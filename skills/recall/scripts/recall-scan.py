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
#   recall-scan.py --latest             the newest real session only, as key: value
#                                       lines (id, when, title, prompts, its last 3
#                                       chapters, its last request — cut to 100
#                                       chars, key-shaped tokens masked); stops
#                                       reading early: 1.5 s where -n 1 takes
#                                       6.8 s (4,170 transcripts, 7Oct26)
#
import argparse, atexit, glob, json, os, re, sys, datetime

atexit.register(lambda: sys.stdout.isatty() and print())
TTY = sys.stdout.isatty()
def c(s, code): return f"\033[{code}m{s}\033[0m" if TTY else s
ROOT = os.path.expanduser("~/.claude/projects")

def mangle(path):
    # as Claude Code names a project's folder (the rule in excptn's record.py): every
    # UTF-16 unit that isn't an ASCII letter or digit becomes "-", so an emoji gives "--"
    return "".join(c if c.isascii() and c.isalnum() else ("--" if ord(c) > 0xFFFF else "-")
                   for c in os.path.realpath(path))

def project_dirs(all_projects):
    if all_projects:
        return sorted(d for d in glob.glob(os.path.join(ROOT, "*")) if os.path.isdir(d))
    m = mangle(os.getcwd())
    d = os.path.join(ROOT, m)
    if os.path.isdir(d):
        return [d]
    if len(m) > 200:  # a name over 200 characters is cut and given a suffix: match the first 200
        cut = sorted(x for x in glob.glob(os.path.join(ROOT, glob.escape(m[:200]) + "*"))
                     if os.path.isdir(x) and len(os.path.basename(x)) > 200)  # a cut name always has its suffix
        if cut:
            return cut
    sys.exit(f"no session store for {os.getcwd()}\n  looked in: {d}\n  try --all")

def parse(path, stop_after=None):
    """Return (user_prompts, assistant_texts, title, cwd). Each prompt or reply
    is (seq, ts, text): seq is its line number in the transcript, the true
    chronological order (ts is only to the minute, so it cannot order ties).
    stop_after: only count prompts, and stop once that many are found; lines
    that cannot be a user entry are not decoded (title and cwd stay unread)."""
    ups, asts, title, cwd = [], [], None, None
    try:
        fh = open(path, errors="replace")
    except OSError:
        return ups, asts, title, cwd
    with fh:
        for seq, line in enumerate(fh):
            if stop_after and '"user"' not in line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            t = o.get("type")
            cwd = cwd or o.get("cwd")
            if t == "custom-title":
                title = o.get("customTitle") or title
            elif t in ("user", "assistant"):
                if t == "user" and (o.get("isMeta") or o.get("isCompactSummary")):
                    continue    # harness-injected: skill/command bodies, image
                                # notes, hook feedback, compaction summaries
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
                    ups.append((seq, ts, txt))
                    if stop_after and len(ups) >= stop_after:
                        break
                else:
                    asts.append((seq, ts, txt))
    return ups, asts, title, cwd

def chapters(path):
    """Titles of the session's mark_chapter calls, in order. Read from the
    tool_use structure, never from the 'Chapter marked' result text, which
    quoted rules also contain."""
    out = []
    try:
        fh = open(path, errors="replace")
    except OSError:
        return out
    with fh:
        for line in fh:
            if "mark_chapter" not in line:
                continue
            try:
                o = json.loads(line)
            except Exception:
                continue
            if o.get("type") != "assistant":
                continue
            for i in (o.get("message") or {}).get("content") or []:
                if (isinstance(i, dict) and i.get("type") == "tool_use"
                        and str(i.get("name", "")).endswith("mark_chapter")):
                    t = (i.get("input") or {}).get("title")
                    if t:
                        out.append(str(t))
    return out

# Masking for the --latest text. (?<![A-Za-z0-9]) instead of \b: \b treats "_"
# as a word character, so it never fires inside DB_PASSWORD or after a prefix_.
# "/" and "." never join a catch-all run, so file paths and URLs stay readable.
_NB = r"(?<![A-Za-z0-9])"
_RUN = r"[A-Za-z0-9+=_-]"
_B64 = r"[A-Za-z0-9/+]"
_KEY = (r"(?:password|passwd|passphrase|pwd|(?<![a-z])pass(?![a-z])|secret|token|"
        r"api[_-]?key|apikey|private[_-]?key|access[_-]?key|credential)")
SECRET = [
    # NAME=v, NAME: v, "name": "v", NAME := v, 'name' => 'v'; the keyword may sit
    # inside a longer name (DB_PASSWORD, DB_PASS, SECRET_KEY, secretKey). Values
    # that are ALL digits, and 1–3 character values, stay (max_tokens: 4096);
    # digits followed by more characters do not (password=1234!abcd).
    (re.compile(r"(?i)(" + _KEY + r"[A-Za-z0-9_]{0,40}[\"']?\s*(?::=|=>|[:=])\s*[\"']?)"
                r"(?![0-9]+(?:[\s\"',;}]|$))[^\s\"',;}]{4,}"), r"\1[masked]"),
    # --password v, --token v, --api-key v
    (re.compile(r"(?i)(--?(?:password|passwd|pass|pwd|token|secret|api[_-]?key)\s+)(?!-)\S+"),
     r"\1[masked]"),
    # "the DB_PASSWORD is …", "my api key is: …"
    (re.compile(r"(?i)(?<![A-Za-z])(" + _KEY + r"|api key|private key|access key)"
                r"(\s+(?:is|was):?\s+)\S+"), r"\1\2[masked]"),
    # Authorization: Bearer v / Token v — a value holding a digit
    (re.compile(r"(?i)\b(bearer|token)(\s+)(?=\S*\d)[A-Za-z0-9._~+/=-]{10,}"), r"\1\2[masked]"),
    # Authorization: Basic <base64> — mixed case, a digit or + / = (never a plain word)
    (re.compile(r"(?i)\b(basic)(\s+)(?=[A-Za-z0-9+/]{8,}={0,2}(?![^\s]))"
                r"(?-i:(?=\S*[0-9+/=]|\S*[A-Z]\S*[a-z]|\S*[a-z]\S*[A-Z]))[A-Za-z0-9+/]+={0,2}"),
     r"\1\2[masked]"),
    # curl -u user:pass, -uuser:pass, --user user:pass (an all-digit uid:gid stays)
    (re.compile(r"((?:-u\s*|--user[\s=]+)[^\s:]+:)(?![0-9]+(?:[\s,;]|$))\S+"), r"\1[masked]"),
    # mysql -pSECRET (glued): a digit or capital inside, so -print and -pthread stay
    (re.compile(r"(?<!\S)-p(?=\S*[0-9A-Z])\S{6,}"), "-p[masked]"),
    (re.compile(r"://[^/\s:@]*:[^@\s/]+@"), "://[masked]@"),              # user:pass@, empty user too
    # provider prefixes, each at its real minimum length
    (re.compile(_NB + r"(?:sk|pk|rk)[-_][A-Za-z0-9_-]{16,}"), "[masked]"),
    (re.compile(_NB + r"(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{20,}"
                r"|glpat-[A-Za-z0-9_-]{20,}|xox[abpr]-[A-Za-z0-9-]{10,}|npm_[A-Za-z0-9]{30,}"
                r"|hf_[A-Za-z0-9]{30,}|whsec_[A-Za-z0-9+/=]{20,}|shpat_[a-f0-9]{32}"
                r"|AIza[A-Za-z0-9_-]{30,})"), "[masked]"),
    (re.compile(_NB + r"AKIA[0-9A-Z]{16}(?![A-Za-z0-9])"), "[masked]"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}"), "[masked]"),
    # catch-alls: 32+ alphanumerics (a full git SHA too — harmless to hide);
    # 20+ characters mixing upper, lower and digits; 20+ lowercase
    # alphanumerics holding 4+ digits; an exactly-40 base64 run with mixed case
    # and digits (AWS secret keys, which carry "/" and "+")
    (re.compile(_NB + r"[A-Za-z0-9]{32,}(?![A-Za-z0-9])"), "[masked]"),
    (re.compile(r"(?<!" + _RUN + r")(?=" + _RUN + r"*[A-Z])(?=" + _RUN + r"*[a-z])(?=" + _RUN +
                r"*[0-9])" + _RUN + r"{20,}"), "[masked]"),
    (re.compile(_NB + r"(?=(?:[a-z]*[0-9]){4})(?=[0-9]*[a-z])[a-z0-9]{20,}(?![A-Za-z0-9])"),
     "[masked]"),
    (re.compile(r"(?<!" + _B64 + r")(?=" + _B64 + r"{40}(?!" + _B64 + r"))(?=" + _B64 +
                r"*[A-Z])(?=" + _B64 + r"*[a-z])(?=" + _B64 + r"*[0-9])" + _B64 + r"{40}"),
     "[masked]"),
]

def masked(text, limit=100):
    """One line, key-shaped tokens masked, cut to limit chars; a lone
    surrogate (it cannot be printed) becomes '?'."""
    # cut before masking: only the head is ever shown, and a huge prompt must
    # not reach the regexes whole (a repeated keyword is quadratic in rule 1)
    s = " ".join(text[:limit * 8].split()).encode("utf-8", "replace").decode("utf-8")
    for rx, rep in SECRET:
        s = rx.sub(rep, s)
    return s if len(s) <= limit else s[:limit - 1] + "…"

def latest(dirs, min_prompts, exclude):
    """The newest real session: newest file first, each read only until it
    proves real, so scratch transcripts cost a few lines each."""
    stamped = []
    for f in (f for d in dirs for f in glob.glob(os.path.join(d, "*.jsonl"))):
        try:
            stamped.append((os.path.getmtime(f), f))
        except OSError:                 # a dangling link, or deleted mid-run
            continue
    stamped.sort(reverse=True)
    for mtime, f in stamped:
        sid = os.path.basename(f)[:-6]
        if exclude and sid.startswith(exclude):
            continue
        if len(parse(f, stop_after=min_prompts)[0]) < min_prompts:
            continue
        ups, _, title, _ = parse(f)
        return {"id": sid, "mtime": mtime, "n": len(ups),
                "title": title, "chapters": chapters(f)[-3:],
                "ask": ups[-1][2] if ups else ""}
    return None

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
                hay = "\n".join(t for _, _, t in ups + asts).lower()
                if term.lower() not in hay:
                    continue
            out.append({"id": sid, "file": f, "mtime": os.path.getmtime(f),
                        "n": len(ups), "title": title, "cwd": cwd, "ups": ups})
    out.sort(key=lambda r: r["mtime"], reverse=True)
    return out

def main():
    # a lone surrogate in any transcript text prints as "?" in every mode, never a crash
    sys.stdout.reconfigure(errors="replace")
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
    p.add_argument("--latest", action="store_true",
                   help="only the newest real session, as key: value lines, "
                        "its text masked and cut; stops reading early")
    a = p.parse_args()
    if a.latest and (a.show or a.search):
        p.error("--latest cannot be combined with --show or -s")

    if a.latest:
        r = latest(project_dirs(a.all), a.min_prompts, a.exclude)
        if not r:
            print("no prior sessions matched")
            return
        print(f"id: {r['id']}")
        print("when: " + datetime.datetime.fromtimestamp(r["mtime"]).strftime("%m-%d %H:%M"))
        print(f"title: {masked(r['title'] or '(untitled)', 60)}")
        print(f"prompts: {r['n']}")
        for t in r["chapters"]:
            print(f"chapter: {masked(t, 40)}")
        print(f"ask: {masked(r['ask'])}")
        return

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
        tagged = ([("USER", n, t, x) for n, t, x in ups] +
                  ([("ASST", n, t, x) for n, t, x in asts] if a.full else []))
        items = sorted(tagged, key=lambda r: r[1])
        # --tail counts PROMPTS: start at the Nth-last prompt, keeping the
        # replies that follow it
        if 0 < a.tail < len(ups):
            start = ups[-a.tail][0]
            items = [r for r in items if r[1] >= start]
            print(c(f"... {len(ups) - a.tail} earlier prompt(s) hidden "
                    f"(--tail 0 for all)", "33"))
        print()
        for who, _, ts, txt in items:
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
        head = (r["title"] or r["ups"][0][2][:34].replace("\n", " ")) if r["ups"] else "?"
        print(f"{when:<12} {c(r['id'][:8], '36'):<9} {r['n']:>5}  {head[:38]}")
    if len(rows) > a.n:
        print(f"... {len(rows) - a.n} more (raise -n)")

if __name__ == "__main__":
    main()
