#!/usr/bin/env python3
"""UserPromptSubmit hook body: prompt -> classify -> write reco file (or clear).

CC pipes the prompt event as JSON on stdin. This classifies it and writes an
ENRICHED reco to MOUTER_RECO (default ~/.claude/mouter-reco.json): tier_idx,
the adapter's alias->tier map, the effort ladder, and the session_id — i.e.
everything the statusline wrapper needs so its per-render compare is a single
cheap jq call (no python in the ~300ms render loop). No match -> the reco is
KEPT so the suggestion persists across follow-ups. Runs only for a session
that was activated with /mouter (per-session gate); other sessions do nothing.
On a fresh classification it also prints an `ideal=` marker + a PRE-FORMATTED
3-line banner to stdout (UserPromptSubmit stdout is injected as model-visible
context) — deterministic here so it can't drift; the rule prints those lines
verbatim when the ideal model differs from the current one.

Kept synchronous and side-effect-only; never backgrounds work (avoids the
hook-stdout EOF hang). Wire in settings.json under UserPromptSubmit.
"""
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from mouter_classify import classify, resolve  # noqa: E402
from resolve_model import (  # noqa: E402
    TIER_ORDER, EFFORTS, load_config, load_adapter, detect_agent, tier_model,
)
from mouter_state import read as read_state  # noqa: E402

RECO = Path(os.environ.get("MOUTER_RECO", str(Path.home() / ".claude" / "mouter-reco.json")))


def _run() -> None:
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    prompt, session_id = raw, ""
    try:
        obj = json.loads(raw)
        if isinstance(obj, dict):
            prompt = str(obj.get("prompt") or "")
            session_id = str(obj.get("session_id") or "")
    except (ValueError, TypeError):
        pass
    # Per-session gate: mouter is OFF unless THIS session was activated with
    # /mouter. A non-activated session does nothing — no write, and no clear
    # (never disturb an activated session's shared reco).
    if read_state(session_id).get("enabled") is False:
        return
    key = classify(prompt)
    if not key:            # unsure -> KEEP the last reco (persistence): follow-up
        return             # prompts ("ok", questions) shouldn't drop the active
                           # task's suggestion. Staleness is the wrapper's TTL;
                           # mute still clears instantly via mouter_state.py.
    config = load_config()
    adapter = load_adapter(detect_agent(config, None))
    reco = resolve(key, config, adapter)
    if not reco:                                   # unknown key/tier -> keep old
        return
    # Enrich so the wrapper's jq needs no adapter/config knowledge of its own.
    # alias_tiers is an ARRAY ordered frontier->light: first-substring-match
    # wins, preserving the old current_tier() iteration semantics.
    reco["tier_idx"] = TIER_ORDER.index(reco["tier"])
    reco["session_id"] = session_id
    reco["alias_tiers"] = [[tier_model(adapter, t), TIER_ORDER.index(t)]
                           for t in reversed(TIER_ORDER)]
    reco["efforts"] = EFFORTS
    reco["ts"] = int(time.time())                  # wrapper TTL anchor
    RECO.parent.mkdir(parents=True, exist_ok=True)
    tmp = RECO.with_suffix(".tmp")                 # atomic: never render a
    tmp.write_text(json.dumps(reco) + "\n")        # half-written reco
    os.replace(tmp, RECO)
    # Response banner: emit an ideal marker + a PRE-FORMATTED 3-line block.
    # Baking it here (deterministic Python) instead of letting the model author
    # ASCII is what stops the format from drifting. The rule prints these 3
    # lines VERBATIM iff the ideal model differs from the current one.
    text = f"{reco['model']} / {reco['effort']}"
    bar = "-" * (len(text) + 2)
    print(f"mouter: ideal={reco['model']}/{reco['effort']} — if it differs from "
          f"your current model, open your reply with the 3 lines below, verbatim:")
    print(bar)
    print(f" {text}")
    print(bar)


def main() -> None:
    # A UserPromptSubmit hook must NEVER crash the turn. Swallow everything —
    # incl. SystemExit from sys.exit-ing helpers like load_adapter, which is
    # not an Exception subclass — and fail silent. A missing chip always beats
    # a traceback on every prompt.
    try:
        _run()
    except (Exception, SystemExit):
        pass                                         # never disturb the reco on
        #                                              crash (may be another
        #                                              session's); TTL self-heals


if __name__ == "__main__":
    main()
