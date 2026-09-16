#!/usr/bin/env python3
"""Per-session state gate for mouter + the (global) throttle override.

mouter is OFF by default and activated PER SESSION: `/mouter` in a session
opts THAT session in; every other session is ignored. State file shape:

  {"default": false, "sessions": {"<session_id>": true|false}, "throttle": "off"}

The session id is CLAUDE_CODE_SESSION_ID (present in the Bash env when the
skill runs a command) or passed explicitly by the hook (which reads it from
its UserPromptSubmit event) — both are the same id. Throttle stays global.
MOUTER_STATE / MOUTER_RECO env vars relocate the files (tests).

Usage:
  mouter_state.py [get|on|off|toggle]           this session's flag; prints ON/OFF
  mouter_state.py on|off all                    ALL sessions (sets the default,
                                                clears per-session overrides)
  mouter_state.py throttle [get|fresh|low|off]  global throttle override
"""
import json
import os
import sys
from pathlib import Path

STATE = Path(os.environ.get(
    "MOUTER_STATE",
    str(Path(__file__).resolve().parent.parent / "references" / "state.json")))
RECO = Path(os.environ.get("MOUTER_RECO",
                           str(Path.home() / ".claude" / "mouter-reco.json")))
THROTTLE_MODES = ("fresh", "low", "off")


def _load() -> dict:
    try:
        data = json.loads(STATE.read_text())
    except (OSError, ValueError):
        data = {}
    return data if isinstance(data, dict) else {}


def _sid(explicit: str | None = None) -> str:
    return explicit or os.environ.get("CLAUDE_CODE_SESSION_ID", "")


def read(session_id: str | None = None) -> dict:
    """This session's gate: enabled = sessions[sid], else the global default."""
    d = _load()
    sid = _sid(session_id)
    default = bool(d.get("default", False))
    sessions = d.get("sessions", {})
    if not isinstance(sessions, dict):
        sessions = {}
    enabled = bool(sessions.get(sid, default)) if sid else default
    return {"enabled": enabled, "throttle": d.get("throttle", "off")}


def _save(d: dict) -> None:
    d.setdefault("default", False)
    d.setdefault("sessions", {})
    d.setdefault("throttle", "off")
    STATE.write_text(json.dumps(d) + "\n")


def _set_enabled(sid: str, value: bool) -> None:
    d = _load()
    sessions = d.get("sessions", {})
    if not isinstance(sessions, dict):
        sessions = {}
    sessions[sid] = bool(value)
    d["sessions"] = sessions
    _save(d)


def main() -> None:
    args = sys.argv[1:] or ["get"]
    sid = _sid()
    if args[0] == "throttle":
        mode = args[1] if len(args) > 1 else "get"
        if mode in THROTTLE_MODES:
            d = _load()
            d["throttle"] = mode
            _save(d)
        elif mode != "get":
            print("usage: mouter_state.py throttle [get|fresh|low|off]", file=sys.stderr)
            sys.exit(2)
        print(read(sid)["throttle"])
        return
    cmd = args[0]
    scope_all = len(args) > 1 and args[1] == "all"
    if cmd == "get":
        pass
    elif cmd in ("on", "off") and scope_all:      # every session: set the default
        d = _load()                               # + wipe per-session overrides
        d["default"] = (cmd == "on")
        d["sessions"] = {}
        _save(d)
    elif cmd in ("on", "off"):
        _set_enabled(sid, cmd == "on")
    elif cmd == "toggle":
        _set_enabled(sid, not read(sid)["enabled"])
    else:
        print("usage: mouter_state.py [get|on|off|toggle] | on|off all "
              "| throttle [get|fresh|low|off]", file=sys.stderr)
        sys.exit(2)
    st = read(sid)
    if not st["enabled"]:                        # instant mute (clears the reco)
        try:
            RECO.unlink(missing_ok=True)
        except OSError:
            pass
    if scope_all:
        print(("ON" if cmd == "on" else "OFF") + " (all sessions)")
    else:
        print("ON" if st["enabled"] else "OFF")


if __name__ == "__main__":
    main()
