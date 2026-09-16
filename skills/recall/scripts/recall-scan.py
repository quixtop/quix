#!/usr/bin/env python3
# (c) Shrix
# author: shrix
#
# recall-scan.py — list or dump PRIOR Claude Code sessions for a project.
#
# Claude Code writes one JSONL transcript per session under
# ~/.claude/projects/<mangled-cwd>/. The overwhelming majority are subagent
# scratch sessions (hook classifiers, chapter markers, gate checks), so this
# filters STRUCTURALLY on real user-prompt count rather than blacklisting
# boilerplate, which stays correct as new agent types appear.
#
# Usage:
#   recall-scan.py                      list recent real sessions for cwd's project
#   recall-scan.py -n 10                list the 10 most recent
#   recall-scan.py -s "cc-xtn"          only sessions whose text contains a term
#   recall-scan.py --all                search every project, not just this one
#   recall-scan.py --show <id-prefix>   dump one session's user prompts
#   recall-scan.py --show <id> --full   also include assistant replies
#   recall-scan.py --show <id> --tail 0 all prompts (default: last 40)
#   recall-scan.py --min-prompts 5      raise the real-session threshold (default 3)
#   recall-scan.py --exclude <id>       omit a session (e.g. the current one)
#
import argparse, atexit, glob, json, os, re, sys, datetime

atexit.register(lambda: sys.stdout.isatty() and print())
TTY = sys.stdout.isatty()
def c(s, code): return f"\033[{code}m{s}\033[0m" if TTY else s
ROOT = os.path.expanduser("~/.claude/projects")

def mangle(path): return re.sub(r"[^A-Za-z0-9]", "-", os.path.realpath(path))

def project_dirs(all_projects):
    if all_projects:
        return sorted(d for d in glob.glob(os.path.join(ROOT, "*")) if os.path.isdir(d))
    d = os.path.join(ROOT, mangle(os.getcwd()))
    if os.path.isdir(d):
        return [d]
    sys.exit(f"no session store for {os.getcwd()}\n  looked in: {d}\n  try --all")

def parse(path):
    """Return (user_prompts, assistant_texts, title, cwd)."""
    ups, asts, title, cwd = [], [], None, None
    try:
        fh = open(path, errors="replace")
    except OSError:
        return ups, asts, title, cwd
    with fh:
        for line in fh:
            try:
                o = json.loads(line)
            except Exception:
                continue
            t = o.get("type")
            cwd = cwd or o.get("cwd")
            if t == "custom-title":
                title = o.get("customTitle") or title
            elif t in ("user", "assistant"):
                body = (o.get("message") or {}).get("content")
                if isinstance(body, list):
                    txt = " ".join(i.get("text", "") for i in body
                                   if isinstance(i, dict) and i.get("type") == "text")
                else:
                    txt = str(body or "")
                txt = txt.strip()
                if not txt:
                    continue
                ts = (o.get("timestamp") or "")[:16].replace("T", " ")
                if t == "user":
                    if txt.startswith("<"):      # hook/system injections
                        continue
                    ups.append((ts, txt))
                else:
                    asts.append((ts, txt))
    return ups, asts, title, cwd

def collect(dirs, min_prompts, term, exclude):
    out = []
    for d in dirs:
        for f in glob.glob(os.path.join(d, "*.jsonl")):
            sid = os.path.basename(f)[:-6]
            if exclude and sid.startswith(exclude):
                continue
            ups, asts, title, cwd = parse(f)
            if len(ups) < min_prompts:
                continue
            if term:
                hay = "\n".join(t for _, t in ups + asts).lower()
                if term.lower() not in hay:
                    continue
            out.append({"id": sid, "file": f, "mtime": os.path.getmtime(f),
                        "n": len(ups), "title": title, "cwd": cwd, "ups": ups})
    out.sort(key=lambda r: r["mtime"], reverse=True)
    return out

def main():
    p = argparse.ArgumentParser(add_help=False,
        description="List or dump prior Claude Code sessions for a project.")
    p.add_argument("-h", "--help", action="help",
                   help="show this help and exit")
    p.add_argument("-n", type=int, default=5, metavar="N",
                   help="how many sessions to list (default 5)")
    p.add_argument("-s", "--search", metavar="TERM",
                   help="only sessions whose text contains TERM (case-insensitive)")
    p.add_argument("--all", action="store_true",
                   help="search every project store, not just the cwd's")
    p.add_argument("--show", metavar="ID",
                   help="dump one session; ID is the short hex from the listing")
    p.add_argument("--full", action="store_true",
                   help="with --show: include assistant replies, not just prompts")
    p.add_argument("--min-prompts", type=int, default=3, metavar="N",
                   help="real-prompt threshold that separates sessions from "
                        "subagent noise (default 3)")
    p.add_argument("--exclude", metavar="ID",
                   help="omit a session, e.g. the current one")
    p.add_argument("--tail", type=int, default=40, metavar="N",
                   help="with --show: last N prompts (0 = all). Default 40.")
    a = p.parse_args()

    if a.show:
        cand = [f for d in project_dirs(True)
                for f in glob.glob(os.path.join(d, a.show + "*.jsonl"))]
        if not cand:
            sys.exit(f"no session matching {a.show!r}")
        if len(cand) > 1:
            sys.exit(f"{a.show!r} is ambiguous ({len(cand)} matches) - use more chars")
        ups, asts, title, cwd = parse(cand[0])
        sid = os.path.basename(cand[0])[:-6]
        print(c(f"{title or '(untitled)'}  [{sid[:8]}]", "1"))
        print(f"{cwd or '?'}   {len(ups)} prompts")
        tagged = ([("USER", t, x) for t, x in ups] +
                  ([("ASST", t, x) for t, x in asts] if a.full else []))
        items = sorted(tagged, key=lambda r: r[1])
        shown = items if a.tail <= 0 else items[-a.tail:]
        if len(shown) < len(items):
            print(c(f"... {len(items) - len(shown)} earlier hidden "
                    f"(--tail {len(items)} for all)", "33"))
        print()
        for who, ts, txt in shown:
            print(f"[{ts}] {who + ': ' if a.full else ''}{txt}\n")
        return

    rows = collect(project_dirs(a.all), a.min_prompts, a.search, a.exclude)

    if not rows:
        print("no prior sessions matched"
              + (f" for {a.search!r}" if a.search else ""))
        return
    print(c(f"{'when':<12} {'id':<9} {'n':>5}  title", "1"))
    for r in rows[:a.n]:
        when = datetime.datetime.fromtimestamp(r["mtime"]).strftime("%m-%d %H:%M")
        head = (r["title"] or r["ups"][0][1][:34].replace("\n", " ")) if r["ups"] else "?"
        print(f"{when:<12} {c(r['id'][:8], '36'):<9} {r['n']:>5}  {head[:38]}")
    if len(rows) > a.n:
        print(f"... {len(rows) - a.n} more (raise -n)")

if __name__ == "__main__":
    main()
