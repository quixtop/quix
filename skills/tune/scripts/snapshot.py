#!/usr/bin/env python3
# (c) Shrix
# author: shrix
# snapshot — start copies, pre-apply checks and diff-built reports for /tune.
#
# Usage:
#   snapshot.py snapshot <run-dir> <path>...
#       Copy each path into <run-dir>/before/ under its absolute path, and
#       write <run-dir>/manifest.json. Refuses if before/ already exists (a
#       start copy is taken once, before the first edit) and refuses a root
#       that is itself a symlink (pass its real path instead).
#   snapshot.py check <path>...
#       Validate files before they are applied: YAML frontmatter (Ruby's
#       parser), shrix description rules ((shrix) prefix; length cap =
#       min(1024, skillListingMaxDescChars in ~/.claude/settings.json, else 1536)), a
#       SKILL.md must have frontmatter, `bash -n` / `zsh -n` for shell,
#       compile() for Python, `node --check` for JavaScript (parse only;
#       NODE_OPTIONS is cleared), and JSON parsing. Directories are searched
#       recursively and symlinks are followed (read-only). A file that could
#       not be checked is reported, never counted as valid.
#   snapshot.py diff <run-dir> [--md] [--expect FILE]
#       Compare before/ against the live files: ADDED / MODIFIED / DELETED /
#       UNREADABLE, with byte and ~token changes. --md prints a markdown table.
#       --expect lists the paths the run meant to change (one per line); any
#       other change is marked UNEXPECTED.
#   snapshot.py diff <before-dir> --live <dir> [--md] [--expect FILE]
#       The same comparison for a plain copy of <dir> made some other way.
#   -h | --help | help
#       Print this text.
#
# Exit codes: 0 fine · 1 a check failed, a change was UNEXPECTED or
# UNREADABLE, or a check could not run · 2 usage or input error.
# All three skip node_modules, .git, __pycache__, .next and .trash. snapshot and
# diff also skip the run directory itself, and copy and compare symlinks as
# links, never following them.
import argparse
import atexit
import functools
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
from datetime import datetime
from pathlib import Path

atexit.register(lambda: sys.stdout.isatty() and print())

SKIP = {"node_modules", ".git", "__pycache__", ".next", ".trash"}
RUBY = os.environ.get("SNAPSHOT_RUBY", "/usr/bin/ruby")   # override for tests
EXT_KIND = {".py": "python", ".sh": "bash", ".bash": "bash", ".zsh": "zsh",
            ".js": "node", ".mjs": "node", ".cjs": "node"}
RUBY_YAML = ("require 'yaml'; require 'json'; require 'date'; "
             "puts JSON.generate(YAML.safe_load(STDIN.read, permitted_classes: [Date, Time], aliases: true))")


def usage():
    out = []
    for line in Path(__file__).read_text(encoding="utf-8").splitlines()[1:]:
        if not line.startswith("#"):
            break
        if re.match(r"^# ?(\(c\)|author:)", line):
            continue
        out.append(re.sub(r"^# ?", "", line))
    print("\n".join(out))


@functools.lru_cache(maxsize=None)
def desc_cap():
    """min(1024, skillListingMaxDescChars from ~/.claude/settings.json, else
    1536) — the rule references/profiles.md states. An unusable file or value
    falls back too, with a warning on stderr."""
    v, bad = None, None
    try:
        v = json.loads((Path.home() / ".claude" / "settings.json").read_text(encoding="utf-8"))
        v = v.get("skillListingMaxDescChars")
    except FileNotFoundError:
        pass
    except (OSError, ValueError, AttributeError) as e:
        v, bad = None, f"~/.claude/settings.json unusable: {e}"
    if v is not None and not (type(v) is int and v > 0):
        v, bad = None, f"skillListingMaxDescChars is not a positive integer: {v!r}"
    if bad:
        print(f"⚠ description cap falls back to 1024 — {bad}", file=sys.stderr)
    return min(1024, v or 1536)


def status(kind, msg):
    glyph, colour = {"ok": ("✓", "32"), "fail": ("✗", "31"), "warn": ("⚠", "33")}[kind]
    text = f"{glyph} {msg}"
    print(f"\033[{colour}m{text}\033[0m" if sys.stdout.isatty() else text)


def norm(p):
    """Absolute and normalised ('..' collapsed), without resolving symlinks."""
    return Path(os.path.abspath(os.path.expanduser(str(p))))


def _raise(err):
    raise err


def walk(root, exclude=(), strict=False):
    """Every file and symlink under root, never following links (snapshot and
    diff). Skips SKIP names and any directory whose REAL path is excluded.
    strict=True raises on an unreadable directory instead of omitting it."""
    root = Path(root)
    if root.is_symlink() or root.is_file():
        yield root
        return
    excl = {os.path.realpath(e) for e in exclude}
    for dirpath, dirs, files in os.walk(root, onerror=_raise if strict else None):
        keep = []
        for d in dirs:
            p = Path(dirpath, d)
            if d in SKIP or os.path.realpath(p) in excl:
                continue
            if p.is_symlink():
                yield p
            else:
                keep.append(d)
        dirs[:] = keep
        for f in files:
            if f not in SKIP:
                yield Path(dirpath, f)


def signature(p):
    if p.is_symlink():
        return ("link", os.readlink(p))
    if p.is_dir():
        return ("dir", None)
    return ("file", hashlib.sha256(p.read_bytes()).hexdigest(), stat.S_IMODE(p.stat().st_mode))


def size(p):
    try:
        return 0 if p.is_symlink() or not p.is_file() else p.stat().st_size
    except OSError:
        return 0


# ---- snapshot ---------------------------------------------------------------

def cmd_snapshot(a):
    run = norm(a.run)
    before, tmp = run / "before", run / "before.tmp"
    if before.exists():
        status("fail", f"{before} already exists — a start copy is taken once")
        return 2
    roots = [norm(p) for p in a.paths]
    for r in roots:
        if r.is_symlink():
            status("fail", f"{r} is a symlink — pass its real path: {r.resolve()}")
            return 2
        if not r.exists():
            status("fail", f"not found: {r}")
            return 2
    entries = []
    try:
        run.mkdir(parents=True, exist_ok=True)
        if tmp.exists():
            shutil.rmtree(tmp)      # left by an earlier failed attempt of this command
        tmp.mkdir()
        for root in roots:
            for src in walk(root, exclude=[run], strict=True):
                dst = tmp / str(src).lstrip("/")
                dst.parent.mkdir(parents=True, exist_ok=True)
                if src.is_symlink():
                    os.symlink(os.readlink(src), dst)
                else:
                    shutil.copy2(src, dst)
                entries.append({"path": str(src), "bytes": size(src)})
    except OSError as e:
        shutil.rmtree(tmp, ignore_errors=True)
        status("fail", f"start copy aborted, nothing kept: {e}")
        return 1
    if not entries:
        shutil.rmtree(tmp, ignore_errors=True)
        status("warn", f"nothing to copy under {', '.join(map(str, roots))} — no start copy made")
        return 1
    tmp.rename(before)
    (run / "manifest.json").write_text(json.dumps({
        "taken": datetime.now().isoformat(timespec="seconds"),
        "run": str(run), "roots": [str(r) for r in roots], "entries": entries,
    }, indent=1), encoding="utf-8")
    status("ok", f"start copy: {len(entries)} entries from {len(roots)} path(s) → {before}")
    return 0


# ---- diff -------------------------------------------------------------------

def compare(pairs, roots, exclude):
    rows = []
    for live, old in sorted(pairs.items()):
        lp, op = Path(live), Path(old)
        try:
            os.lstat(lp)                # exists() says False on EACCES too
        except FileNotFoundError:
            rows.append(("DELETED", live, size(op), 0))
            continue
        except OSError:
            rows.append(("UNREADABLE", live, size(op), 0))
            continue
        try:
            changed = signature(lp) != signature(op)
        except OSError:
            rows.append(("UNREADABLE", live, size(op), 0))
            continue
        if changed:
            rows.append(("MODIFIED", live, size(op), size(lp)))
    for root in roots:
        for p in walk(root, exclude=exclude):
            if str(p) not in pairs:
                rows.append(("ADDED", str(p), 0, size(p)))
    return sorted(rows, key=lambda r: r[1])


def cmd_diff(a):
    target = norm(a.target)
    if a.live:
        before, live = target, norm(a.live)
        if not before.is_dir() or not live.exists():
            status("fail", f"need an existing <before-dir> and --live dir: {before}, {live}")
            return 2
        pairs = {str(live / p.relative_to(before)): str(p) for p in walk(before)}
        roots, exclude = [live], [target]
    else:
        mf = target / "manifest.json"
        if not mf.is_file():
            status("fail", f"no manifest at {mf} — was `snapshot` run for this run dir?")
            return 2
        try:
            manifest = json.loads(mf.read_text(encoding="utf-8"))
            before = target / "before"
            pairs = {e["path"]: str(before / e["path"].lstrip("/")) for e in manifest["entries"]}
            roots, exclude = [Path(r) for r in manifest["roots"]], [target]
        except (OSError, ValueError, KeyError, TypeError, AttributeError) as e:
            status("fail", f"unreadable manifest {mf}: {e}")
            return 2
    expect = None
    if a.expect:
        try:
            expect = {str(norm(l.strip())) for l in open(a.expect, encoding="utf-8") if l.strip()}
        except OSError as e:
            status("fail", f"cannot read --expect file: {e}")
            return 2
    rows = compare(pairs, roots, exclude)
    if expect is not None:
        rows = [(s if p in expect else f"{s}·UNEXPECTED", p, b, n) for s, p, b, n in rows]
    tok = lambda b, n: round((n - b) / 4)
    if a.md:
        print("| state | path | before → after bytes | ~tokens |")
        print("|---|---|---|---|")
        for s, p, b, n in rows:
            print(f"| {s} | `{p}` | {b} → {n} | {tok(b, n):+} |")
    else:
        for s, p, b, n in rows:
            print(f"{s:20} {p}  {b} -> {n}  ({tok(b, n):+} tok)")
    c = {k: sum(1 for r in rows if r[0].startswith(k)) for k in ("ADDED", "MODIFIED", "DELETED", "UNREADABLE")}
    bad = sum(1 for r in rows if "UNEXPECTED" in r[0] or r[0].startswith("UNREADABLE"))
    print(f"{len(rows)} changed ({c['ADDED']} added, {c['MODIFIED']} modified, {c['DELETED']} deleted"
          + (f", {c['UNREADABLE']} unreadable" if c["UNREADABLE"] else "") + "); "
          f"{sum(r[2] for r in rows)} -> {sum(r[3] for r in rows)} bytes"
          + (f"; {sum(1 for r in rows if 'UNEXPECTED' in r[0])} UNEXPECTED" if expect is not None else ""))
    return 1 if bad else 0


# ---- check ------------------------------------------------------------------

def check_walk(root):
    """Files under root for `check`: symlinks FOLLOWED (read-only), cycles cut,
    SKIP names skipped. Yields (path, error) — error set for a dangling link
    or an unreadable directory, so nothing is silently omitted."""
    root = Path(root)
    if root.is_symlink() and not root.exists():
        yield root, "dangling symlink"
        return
    if root.is_file():
        yield root, None
        return
    seen = set()
    errors = []
    for dirpath, dirs, files in os.walk(root, followlinks=True, onerror=errors.append):
        real = os.path.realpath(dirpath)
        if real in seen:
            dirs[:] = []
            continue
        seen.add(real)
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in files:
            if f in SKIP:
                continue
            p = Path(dirpath, f)
            yield p, ("dangling symlink" if p.is_symlink() and not p.exists() else None)
    for e in errors:
        yield Path(e.filename or str(root)), f"unreadable directory: {e.strerror}"


def python_syntax(p, text):
    try:
        compile(text, str(p), "exec")
        return []
    except SyntaxError as e:
        return [f"python syntax: line {e.lineno}: {e.msg}"]


def interpreter(p, shebang):
    """The checker for a file: the shebang wins, the extension is the fallback."""
    if re.search(r"python|uv run", shebang):
        return "python"
    if "zsh" in shebang:
        return "zsh"
    if re.search(r"\b(bash|sh)\b", shebang):
        return "bash"
    if re.search(r"\bnode\b", shebang):
        return "node"
    return EXT_KIND.get(p.suffix)


def check_file(p):
    """(verdict, notes): 'ok' | 'fail' | 'skip' (could not be checked), or
    (None, []) when nothing applies to this file."""
    try:
        head = p.read_bytes()[:256]
    except OSError as e:
        return "fail", [f"unreadable: {e.strerror}"]
    shebang = head.split(b"\n", 1)[0].decode("utf-8", "replace") if head.startswith(b"#!") else ""
    kind = interpreter(p, shebang)
    is_skill = p.name == "SKILL.md"
    if not (p.suffix in (".md", ".json") or shebang or kind):
        return None, []
    try:
        text = p.read_text(encoding="utf-8").replace("\r\n", "\n").lstrip("\ufeff")
    except UnicodeDecodeError:
        return "fail", ["not valid UTF-8"]
    fails, skips, ran = [], [], False
    if p.suffix == ".md" and text.startswith("---\n"):
        ran = True
        end = text.find("\n---", 3)
        if end < 0:
            fails.append("frontmatter opened with --- but never closed")
        elif not os.path.exists(RUBY):
            skips.append("YAML not checked: no Ruby at " + RUBY)
        else:
            r = subprocess.run([RUBY, "-E", "UTF-8:UTF-8", "-e", RUBY_YAML],
                               input=text[4:end], capture_output=True, text=True)
            if r.returncode:
                lines = r.stderr.strip().splitlines() or ["parse error"]
                msg = next((l for l in lines if "SyntaxError" in l or "Error)" in l), lines[0])
                fails.append("invalid YAML frontmatter: " + msg.split(": ", 1)[-1][:90])
            else:
                meta = json.loads(r.stdout)
                if not isinstance(meta, dict):
                    fails.append("frontmatter is empty or not a key: value mapping")
                elif meta.get("author") == "shrix" and "description" in meta:
                    d = str(meta["description"])
                    if not d.startswith("(shrix)"):
                        fails.append("description lacks the (shrix) prefix")
                    if len(d) > desc_cap():
                        fails.append(f"description is {len(d)} chars (cap {desc_cap()})")
    elif is_skill:
        ran = True
        fails.append("SKILL.md has no frontmatter (must start with ---)")
    if kind == "python":
        ran = True
        fails += python_syntax(p, text)
    elif kind in ("bash", "zsh"):
        ran = True
        r = subprocess.run([kind, "-n", str(p)], capture_output=True, text=True)
        if r.returncode:
            fails.append(f"{kind} -n: " + (r.stderr.strip().splitlines() or ["syntax error"])[0][:90])
    elif kind == "node":
        node = shutil.which("node")
        if not node:
            skips.append("JavaScript not checked: no node on PATH")
        else:
            ran = True
            env = {k: v for k, v in os.environ.items() if k != "NODE_OPTIONS"}   # parse only, never preload
            r = subprocess.run([node, "--check", str(p)], capture_output=True, text=True, env=env)
            if r.returncode:
                lines = r.stderr.strip().splitlines() or ["syntax error"]
                msg = next((l for l in lines if re.match(r"\w*Error\b", l)), lines[0])
                fails.append("node --check: " + msg[:90])
    elif shebang:
        skips.append("no checker for interpreter: " + shebang[2:].strip()[:40])
    if p.suffix == ".json":
        ran = True
        try:
            json.loads(text)
        except ValueError as e:
            fails.append(f"invalid JSON: {e}")
    if not (ran or fails or skips):
        return None, []             # e.g. plain markdown: nothing to check
    return ("fail" if fails else "skip" if skips else "ok"), fails + skips


def cmd_check(a):
    tally = {"ok": 0, "fail": 0, "skip": 0}
    for raw in a.paths:
        root = norm(raw)
        if not (root.exists() or root.is_symlink()):
            tally["fail"] += 1
            print(f"FAIL  {root}: not found")
            continue
        for p, err in check_walk(root):
            if err:
                tally["fail"] += 1
                print(f"FAIL  {p}: {err}")
                continue
            verdict, notes = check_file(p)
            if verdict is None:
                continue
            tally[verdict] += 1
            for n in notes:
                print(f"{'FAIL' if verdict == 'fail' else 'SKIP'}  {p}: {n}")
    total = sum(tally.values())
    if total == 0:
        status("warn", "nothing checkable found")
        return 1
    if tally["fail"]:
        status("fail", f"{tally['fail']} of {total} files failed"
               + (f"; {tally['skip']} could not be checked" if tally["skip"] else ""))
        return 1
    if tally["skip"]:
        status("warn", f"{tally['ok']} valid, {tally['skip']} could NOT be checked — not a pass")
        return 1
    status("ok", f"{total} files checked, all valid")
    return 0


# ---- main -------------------------------------------------------------------

def _usage_error(msg):
    raise SystemExit(f"usage error: {msg}")


def main(argv):
    if not argv or argv == ["help"] or "-h" in argv or "--help" in argv:
        usage()
        return 0
    p = argparse.ArgumentParser(add_help=False, prog="snapshot.py")
    p.error = _usage_error
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot", add_help=False)
    s.add_argument("run")
    s.add_argument("paths", nargs="+")
    c = sub.add_parser("check", add_help=False)
    c.add_argument("paths", nargs="+")
    d = sub.add_parser("diff", add_help=False)
    d.add_argument("target")
    d.add_argument("--live")
    d.add_argument("--md", action="store_true")
    d.add_argument("--expect")
    for sp in (s, c, d):
        sp.error = _usage_error
    try:
        a = p.parse_args(argv)
    except SystemExit as e:
        if isinstance(e.code, str):
            print(e.code, file=sys.stderr)
            usage()
        return 2
    return {"snapshot": cmd_snapshot, "check": cmd_check, "diff": cmd_diff}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
