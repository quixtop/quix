#!/usr/bin/env python3
# (c) Shrix
# author: shrix
"""scan.py — secscan's engine runner: every security engine that applies, one merged result.
The code review is not scan.py's: secscan calls claude-security (and security-audit) for it.

Usage: scan.py [full|changes|deps|secrets|code|ci|agents] [--base SHA] [--only ENGINE]
               [--json] [PATH]
       scan.py doctor        engines, versions, data age, what the sandbox blocks
       scan.py update        refresh trivy's databases and semgrep's rule packs (network)
       scan.py report FINDINGS.json OUTDIR   write secscan-<date>.md and .json (-HHMMSS on a same-day rerun)
       scan.py mirror DEST [PATH]   masked copies of the repo's files (or one file or folder) for a reader:
                     files with a hit masked; secret-named, binary, oversized, symlinked, unvouched
                     and control-character-named files left out, and any still matching after masking
       scan.py -h | --help | help

Modes: full (default) every engine over the whole repo · changes what changed since
the last push · deps trivy + hadolint · secrets keyscan · code semgrep + gosec ·
ci zizmor + actionlint · agents skillspector + trivy (dependency files in agent folders).
Engines run all at once (SECSCAN_JOBS workers, default the CPU count), keyscan's runs
started first; a line per engine goes to stderr as it finishes, keyscan's with the places
to revoke. Repeats of one rule inside one skill or file (never secrets) are listed once
under "groups" (the JSON keeps every member; text output prints the group line instead).
Engines see only an allowlisted environment (paths, locale, proxy and CA settings, Go's;
SECSCAN_PASS_ENV adds name prefixes); a symlinked path is never read; trivy's version is
read from its install, so a known-bad release never runs.
Engines run offline, without telemetry, with explicit
config, from an empty folder (keyscan and actionlint from the repo top, gosec from each
Go module);
no output holds a secret value (every text field goes through keyscan --mask, or is
withheld). A missing, blocked, refused, failed or data-less engine is a coverage
gap, never a pass; so is a run in which no engine ran (ci or agents mode on a repo
with no workflow or agent files exits 1 for that reason). skillspector runs with every
proxy set to a closed local port, so its OSV.dev lookup never leaves the machine; its
known-vulnerable-dependency results (SC4) are left to trivy. Inside Claude's sandbox
semgrep, skillspector and trivy's misconfig checks are blocked: run scan.py in a
terminal.
Engine data: $SECSCAN_CACHE, else ${XDG_CACHE_HOME:-~/Library/Caches}/secscan.
Exit: 0 ran, nothing found, no gap · 1 findings or a gap · 2 could not run.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import mmap
import os
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass, field
from pathlib import Path

MODES = ("full", "changes", "deps", "secrets", "code", "ci", "agents")
ENGINES = ("keyscan", "trivy", "semgrep", "zizmor", "actionlint", "skillspector", "hadolint", "gosec")
MODE_ENGINES = {
    "full": ENGINES, "changes": ENGINES, "deps": ("trivy", "hadolint"), "secrets": ("keyscan",),
    "code": ("semgrep", "gosec"), "ci": ("zizmor", "actionlint"), "agents": ("trivy", "skillspector"),
}
INSTALL = {
    "keyscan": "keyscan is secscan's own secret scanner (~/.agents/bin/keyscan, linked into ~/.local/bin)",
    "trivy": "brew install trivy", "semgrep": "brew install semgrep", "zizmor": "brew install zizmor",
    "actionlint": "brew install actionlint", "skillspector": "uv tool install skillspector",
    "hadolint": "brew install hadolint", "gosec": "brew install gosec",
}
KNOWN_BAD = {"trivy": {"0.69.4", "0.69.5", "0.69.6"}}   # compromised releases, March 2026
MUST_KNOW_VERSION = {"trivy"}                           # an unknown version cannot be checked against KNOWN_BAD
TIMEOUT_S = 600            # provisional: no engine run on the fixture took over 60 s; a hang is the case it guards
SEMGREP_PACKS = ("default", "python", "javascript", "typescript", "golang", "java")
RULES_FILE = "rules.yml"   # the packs merged, each rule id once; scan.py update writes it
STALE_DAYS = 7
SEVERITIES = ("info", "low", "medium", "high", "critical")
CONFIDENCES = ("low", "medium", "high")
CONTROL = re.compile("[\x00-\x1f\x7f-\x9f‪-‮⁦-⁩]")
OK_CODES = {"keyscan": {0, 1}, "trivy": {0}, "semgrep": {0, 1}, "zizmor": {0, 10, 11, 12, 13, 14},
            "actionlint": {0, 1}, "skillspector": {0, 1}, "hadolint": {0, 1}, "gosec": {0, 1}}
FINDING_CODES = {"keyscan": {1}, "zizmor": {10, 11, 12, 13, 14}, "actionlint": {1}, "hadolint": {1}, "gosec": {1}}
BLOCKED_SIGNS = ("operation not permitted", "permissionerror", "no trust anchor",
                 "could not find a suitable tls ca", "sandbox")
ENV_KEEP = re.compile(r"PATH|HOME|LANG|LC_\w+|TMPDIR|TERM|TZ|USER|LOGNAME|(?i:https?_proxy|no_proxy|all_proxy)"
                      r"|SSL_CERT_(FILE|DIR)|REQUESTS_CA_BUNDLE|CURL_CA_BUNDLE|NODE_EXTRA_CA_CERTS"
                      r"|GO(PATH|ROOT|MODCACHE|CACHE|ENV|FLAGS|PRIVATE|NOSUMDB|NOPROXY|INSECURE|TOOLCHAIN|PROXY|OS|ARCH)")
# skillspector's OSV.dev lookup goes through httpx, which follows these: a closed local port makes it fail at once
NO_NETWORK = {**{k: "http://127.0.0.1:9" for k in ("HTTPS_PROXY", "https_proxy", "HTTP_PROXY", "http_proxy",
                                                  "ALL_PROXY", "all_proxy")}, "NO_PROXY": "", "no_proxy": ""}
GO_MODULE = {"trivy": b"github.com/aquasecurity/trivy"}   # read from the binary's Go build info, never by running it
NEEDS_HOME = {"gosec"}     # reads Go's module cache under $HOME; every other engine gets an empty HOME, so no user config narrows it
ENUM_KEYS = {"severity", "state", "engine", "category", "confidence", "verdict", "mode"}   # never masked: fixed words
TRUNC = {"title": 200, "evidence": 300, "fix": 300, "reason": 300}                          # applied after masking
TRUNC_OTHER = 2000
SECRET_NAME = re.compile(r"(^|/)\.env($|\.)|\.pem$|\.key$|\.crt$|\.p12$|\.pfx$|credentials\.json$|credentials\.ya?ml$"
                         r"|secrets\.ya?ml$|(^|/)id_rsa$|(^|/)id_ed25519$|(^|/)\.netrc$")    # keyscan's SECRET_NAME
TEMPLATE_NAME = re.compile(r"(^|/)\.env\.(example|sample|template|dist)$")                     # keyscan's TEMPLATE_NAME
MIRROR_MAX = 2_000_000
MANIFESTS = re.compile(r"(^|/)(requirements[^/]*\.txt|pyproject\.toml|poetry\.lock|Pipfile(\.lock)?|package(-lock)?\.json"
                       r"|yarn\.lock|pnpm-lock\.yaml|go\.(mod|sum)|Cargo\.(toml|lock)|Gemfile(\.lock)?|composer\.(json|lock)"
                       r"|pom\.xml|build\.gradle(\.kts)?|[^/]+\.tf|[^/]+\.ya?ml)$")
# the dependency files trivy's vuln scanner reads (a lockfile, not a bare package.json, pyproject.toml, setup.py or Pipfile)
TRIVY_DEPS = re.compile(r"(^|/)(requirements\.txt|poetry\.lock|uv\.lock|Pipfile\.lock|package-lock\.json|yarn\.lock"
                        r"|pnpm-lock\.yaml|go\.(mod|sum)|Cargo\.lock|Gemfile\.lock|composer\.lock|pom\.xml|gradle\.lockfile)$")
# what skillspector's SC4 parses and trivy does not (a requirements.txt aside): its built-in list alone checks these
SC4_ONLY = re.compile(r"(^|/)(package\.json|pyproject\.toml|setup\.py|Pipfile|[^/]*requirements[^/]*\.(txt|in))$")
LOCKED_BY_SIBLING = ("package.json", "pyproject.toml", "Pipfile")   # trivy reads their lockfile when one sits beside them
DOCKER = re.compile(r"(?i)(^|/)(?![^/]*\.(md|txt|rst|html)$)((docker|container)file([.-][^/]*)?|[^/]+\.(docker|container)file)$")
WORKFLOW = re.compile(r"(^|/)\.github/workflows/[^/]+\.ya?ml$")
SUPPRESS_MARKERS = ("keyscan:allow", "secscan:allow", "gitleaks:allow", "trivy:ignore")

CWE_OWASP: dict = {}
for _ids, _cat in (
    ((79, 89, 78, 77, 94, 917, 943, 74, 90, 643), "A05"),
    ((22, 23, 284, 285, 639, 862, 863, 352, 918, 200, 201, 359, 601), "A01"),
    ((798, 259, 287, 306, 307, 384, 522, 521, 620, 640), "A07"),
    ((327, 326, 328, 330, 295, 310, 319, 321, 338, 916), "A04"),
    ((16, 611, 1004, 614, 942, 693, 250), "A02"),
    ((1104, 1395, 1357, 353, 1035), "A03"),
    ((502, 494, 829, 915, 345, 565), "A08"),
    ((778, 117, 223, 532), "A09"),
    ((754, 755, 703, 248, 252, 390), "A10"),
    ((269, 266, 653), "A06"),
):
    for _i in _ids:
        CWE_OWASP[_i] = _cat
CATEGORY_OWASP = {"secret": "A07", "dependency": "A03", "misconfig": "A02", "ci-pin": "A03",
                  "ci-injection": "A05", "injection": "A05", "access": "A01", "crypto": "A04"}
CWE_CATEGORY: dict = {}
for _ids, _cat in (
    ((79, 89, 78, 77, 94, 917, 611, 943, 74, 90, 643, 22, 23, 918), "injection"),
    ((284, 285, 639, 862, 863, 352, 287, 306, 269, 266), "access"),
    ((327, 326, 328, 330, 295, 310, 319, 338, 916), "crypto"),
    ((798, 259, 321, 522), "secret"),
    ((119, 120, 125, 787, 416, 415, 476, 190), "memory"),
):
    for _i in _ids:
        CWE_CATEGORY[_i] = _cat


class EngineOutputError(Exception):
    pass


@dataclass
class Finding:
    sources: list
    rules: list
    category: str
    severity: str
    title: str
    file: str
    line: int | None = None
    commit: str | None = None
    evidence: str = ""
    tags: list = field(default_factory=list)
    fix: str | None = None
    confidence: str = "high"
    verdict: str = "candidate"
    predates_change: bool = False
    group: str = ""          # merge key beyond file + category: a dependency's package
    id: str = ""


@dataclass
class Coverage:
    engine: str
    state: str               # ran | n/a | missing | blocked | refused | failed | no-data
    reason: str = ""
    scope: str = ""
    version: str = ""

    @property
    def gap(self) -> bool:
        return self.state not in ("ran", "n/a")


@dataclass
class Repo:
    top: Path
    scope: Path
    is_git: bool
    files: list
    base: str | None = None
    changed: dict | None = None      # file → set of added/modified lines, or None for a whole new file
    note: str = ""
    links: list = field(default_factory=list)    # paths reached through a symlink: listed, never read


class CannotRun(Exception):
    pass


# ---------- small helpers ----------
def cache_dir() -> Path:
    env = os.environ.get("SECSCAN_CACHE")
    if env:
        return Path(env)
    return Path(os.environ.get("XDG_CACHE_HOME") or Path.home() / "Library" / "Caches") / "secscan"


def engine_bin(name: str) -> str | None:
    env = os.environ.get(f"SECSCAN_{name.upper()}")
    if env is not None:
        return env or None          # set empty: the engine is treated as missing
    return shutil.which(name)


def git(top: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(top), "-c", "core.quotePath=false", *args], capture_output=True, text=True)


def git_bytes(top: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(top), "-c", "core.quotePath=false", *args], capture_output=True)


def rel(top: Path, p: str) -> str:
    """A path as the repo names it: relative to the top, the top's symlinks resolved; outside the repo, absolute."""
    if not p:
        return p
    q = Path(p)
    if not q.is_absolute():
        return os.path.normpath(p)
    for t in (top, top.resolve()):
        try:
            return os.path.normpath(str(q.relative_to(t)))
        except ValueError:
            pass
    try:
        return os.path.normpath(str(Path(os.path.realpath(q.parent)).joinpath(q.name).relative_to(top.resolve())))
    except ValueError:
        return str(q)


def sev(word, table: dict | None = None) -> str:
    w = str(word or "").strip().lower()
    if table and w in table:
        return table[w]
    return {"critical": "critical", "high": "high", "error": "high", "medium": "medium", "moderate": "medium",
            "warning": "medium", "low": "low", "info": "info", "informational": "info", "note": "info",
            "style": "low", "unknown": "low"}.get(w, "medium")


def text(v) -> str:
    return "" if v is None else str(v)


def cwe_ids(values) -> list:
    out = []
    for v in values or []:
        m = re.search(r"CWE-?(\d+)", text(v))
        if m and int(m.group(1)) not in out:
            out.append(int(m.group(1)))
    return out


def tags_for(cwes: list, category: str, owasp: list | None = None) -> list:
    tags = [f"CWE-{c}" for c in cwes]
    o2025 = [m.group(1) for o in owasp or [] for m in [re.match(r"(A\d\d):2025", text(o))] if m]
    if not o2025:
        o2025 = [CWE_OWASP[c] for c in cwes if c in CWE_OWASP][:1] or ([CATEGORY_OWASP[category]] if category in CATEGORY_OWASP else [])
    tags += [f"OWASP:{o}" for o in dict.fromkeys(o2025)]
    if category == "prompt-injection":
        tags.append("LLM01")
    return tags


def category_for(cwes: list, rule: str, file: str, default: str = "other") -> str:
    if DOCKER.search(file):
        return "misconfig"
    r = rule.lower()
    if WORKFLOW.search(file):
        if any(w in r for w in ("pin", "mutable", "unpinned")):
            return "ci-pin"
        if any(w in r for w in ("inject", "untrusted", "template")):
            return "ci-injection"
        return "misconfig"
    if "sql" in r:
        return "injection"
    for c in cwes:
        if c in CWE_CATEGORY:
            return CWE_CATEGORY[c]
    return default


def first_line(s) -> str:
    """Never cut short here: a value cut in half no longer matches a rule, so text is masked first, truncated after."""
    for line in text(s).splitlines():
        line = re.sub(r"\x1b\[[0-9;]*m", "", line).strip()
        if line:
            return line
    return ""


def printable(s) -> str:
    """For the terminal and markdown: no control characters (C0, C1, bidi overrides), no table-breaking pipes."""
    return CONTROL.sub("?", text(s)).replace("|", "\\|")


# ---------- repo discovery ----------
def plain_file(top: Path, f: str) -> bool:
    """A regular file reached with no symlink on its way, so nothing outside the repo is ever read through it."""
    p = top
    for part in Path(f).parts:
        p = p / part
        if p.is_symlink():
            return False
    return p.is_file()


def discover(path: Path, mode: str, base_arg: str | None) -> Repo:
    if not path.exists():
        raise CannotRun(f"no such path: {path}")
    path = path.resolve()
    start = path if path.is_dir() else path.parent
    top_p = git(start, "rev-parse", "--show-toplevel")
    is_git = top_p.returncode == 0
    top = Path(top_p.stdout.strip()) if is_git else start
    if is_git:
        ls = git_bytes(top, "ls-files", "-z", "-co", "--exclude-standard")
        names = [f for f in ls.stdout.decode("utf-8", "replace").split("\0") if f]
    else:
        names = []
        for d, ds, ns in os.walk(top):
            ds[:] = [x for x in ds if x != ".git"]
            names += [str(Path(d, n).relative_to(top)) for n in ns]
    scope_rel = "" if path in (top, top.resolve()) else rel(top, str(path))
    if scope_rel:
        names = [f for f in names if f == scope_rel or f.startswith(scope_rel.rstrip("/") + "/")]
    files = [f for f in names if plain_file(top, f)]
    plain = set(files)
    links = [f for f in names if f not in plain and os.path.lexists(top / f)]
    repo = Repo(top=top, scope=path, is_git=is_git, files=sorted(files), links=sorted(links))
    if mode == "changes":
        if not is_git:
            repo.note = "changes mode needs git — running full without history"
            return repo
        if base_arg is not None:
            r = git(top, "rev-parse", "--verify", "--quiet", "--end-of-options", f"{base_arg}^{{commit}}")
            if base_arg.startswith("-") or r.returncode != 0:
                raise CannotRun(f"--base: no such commit {base_arg}")
            base = r.stdout.strip()
        else:
            base = resolve_base(top)
        if not base:
            repo.note = "changes mode needs a push target — running full"
            return repo
        repo.base = base
        repo.changed = changed_lines(top, base)
    return repo


def resolve_base(top: Path) -> str | None:
    """Where the unpushed work starts: the merge-base with the push target, else with origin's default branch."""
    branch = git(top, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
    targets = ["@{push}", f"origin/{branch}", git(top, "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD").stdout.strip()]
    for ref in [t for t in targets if t]:
        r = git(top, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
        if r.returncode == 0:
            mb = git(top, "merge-base", "HEAD", r.stdout.strip())
            if mb.returncode == 0:
                return mb.stdout.strip()
    return None


_GIT_ESC = {b"n": b"\n", b"t": b"\t", b"r": b"\r", b"\\": b"\\", b'"': b'"', b"a": b"\a", b"b": b"\b", b"f": b"\f", b"v": b"\v"}


def unquote_git(p: bytes) -> str:
    """A name as git printed it (C-quoted when it holds a quote, a backslash or a control character), as it is on disk."""
    if len(p) >= 2 and p[:1] == b'"' and p[-1:] == b'"':
        p = re.sub(rb'\\([0-7]{3}|.)', lambda m: bytes([int(m.group(1), 8)]) if len(m.group(1)) == 3
                   else _GIT_ESC.get(m.group(1), m.group(1)), p[1:-1])
    return p.decode("utf-8", "replace")


def changed_lines(top: Path, base: str) -> dict:
    """file → the lines the working tree added or modified since base; None for a whole new file.

    Read as bytes, as text whatever .gitattributes says (binary, -diff), names unquoted, renames followed. Only a
    header's own lines are read as names: a `+++ ` line counts only between `diff --git` and the first `@@`."""
    out: dict = {}
    names = git_bytes(top, "diff", "--name-only", "-z", "--no-relative", "-M", "--diff-filter=d", base)
    if names.returncode != 0:
        raise CannotRun(f"git diff against {base[:12]} failed: {first_line(names.stderr.decode('utf-8', 'replace'))}")
    for n in names.stdout.decode("utf-8", "replace").split("\0"):
        if n:
            out[n] = set()
    d = git_bytes(top, "diff", "-U0", "--text", "--no-textconv", "--no-color", "--no-ext-diff", "--no-relative", "-M",
                  "--src-prefix=a/", "--dst-prefix=b/", base)
    if d.returncode != 0:
        raise CannotRun(f"git diff against {base[:12]} failed: {first_line(d.stderr.decode('utf-8', 'replace'))}")
    cur, in_header = None, False
    for line in d.stdout.split(b"\n"):
        if line.startswith(b"diff --git "):
            cur, in_header = None, True
        elif in_header and line.startswith(b"+++ "):
            p = unquote_git(line[4:].rstrip(b"\t"))
            cur = None if p == "/dev/null" else (p[2:] if p.startswith("b/") else p)
            if cur is not None:
                out.setdefault(cur, set())
        elif line.startswith(b"@@ "):
            in_header = False
            m = re.match(rb"@@ -\S+ \+(\d+)(?:,(\d+))? @@", line)
            if m and cur is not None:
                s, n = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
                out[cur].update(range(s, s + n))
    for f in git_bytes(top, "ls-files", "-z", "-o", "--exclude-standard").stdout.decode("utf-8", "replace").split("\0"):
        if f:
            out[f] = None
    return out


# ---------- the engines ----------
def agent_dirs(repo: Repo, files: list) -> list:
    """Folders skillspector reads: each skill, each .claude folder, each folder holding .mcp.json."""
    dirs = {str(Path(f).parent) for f in files if Path(f).name == "SKILL.md"}
    for f in files:
        parts = Path(f).parts
        if ".claude" in parts:
            dirs.add(str(Path(*parts[:parts.index(".claude") + 1])))
        if Path(f).name == ".mcp.json":
            dirs.add(str(Path(f).parent))
    return sorted(dirs)


def touched_agent_dirs(repo: Repo, touched: list, every: list | None = None) -> list:
    """The agent folders (`every`, else agent_dirs over the whole repo) holding any of the touched files — a changed
    skill script is a changed skill."""
    return [d for d in (agent_dirs(repo, repo.files) if every is None else every) if any(under(f, d) for f in touched)]


def go_modules(files: list) -> list:
    return sorted({str(Path(f).parent) for f in files if Path(f).name == "go.mod"})


def under(f: str, d: str) -> bool:
    return d in (".", "") or f == d or f.startswith(d + "/")


def agent_manifest_dirs(repo: Repo, touched: list) -> list:
    """The agent folders holding a dependency file trivy reads: what trivy reports on in agents mode."""
    return [d for d in touched_agent_dirs(repo, touched) if any(TRIVY_DEPS.search(f) and under(f, d) for f in repo.files)]


def applies(name: str, repo: Repo, mode: str) -> tuple:
    files = repo.files
    ch = repo.changed
    touched = files if ch is None else [f for f in files if f in ch]
    if name == "keyscan":
        return True, ""
    if name == "trivy" and mode == "agents":
        dirs = agent_manifest_dirs(repo, touched)
        return bool(dirs), "" if dirs else "no dependency file trivy reads in an agent folder"
    if name == "trivy":
        hits = [f for f in touched if MANIFESTS.search(f) or DOCKER.search(f)]
        return (bool(hits) or ch is None), ("" if hits or ch is None else "no manifest, lockfile or config changed")
    if name == "semgrep":
        return bool(touched), "" if touched else "no file to scan"
    if name in ("zizmor", "actionlint"):
        wf = [f for f in touched if WORKFLOW.search(f)]
        return bool(wf), "" if wf else "no GitHub Actions workflow" + (" changed" if ch is not None else "")
    if name == "hadolint":
        df = [f for f in touched if DOCKER.search(f)]
        return bool(df), "" if df else "no Dockerfile" + (" changed" if ch is not None else "")
    if name == "gosec":
        mods = go_modules(files)
        go = bool(mods) and (ch is None or any(f.endswith(".go") or Path(f).name in ("go.mod", "go.sum") for f in touched))
        return go, "" if go else "no Go module" + (" change" if ch is not None and mods else "")
    if name == "skillspector":
        ag = touched_agent_dirs(repo, touched)
        return bool(ag), "" if ag else "no agent skill, .claude folder or .mcp.json"
    return False, "unknown engine"


def semgrep_configs() -> list:
    d = cache_dir() / "semgrep"
    if (d / RULES_FILE).is_file():
        return [str(d / RULES_FILE)]
    return [str(d / f"{p}.yml") for p in SEMGREP_PACKS if (d / f"{p}.yml").is_file()]


def split_rules(text_: str) -> list | None:
    """A registry pack's rules as (id, block) in order; None unless the layout is the registry's own: 'rules:',
    then items starting '- ' at column 0 whose other lines are indented or blank, each with exactly one
    top-level 'id:' (first, as '- id: X', or later, as '  id: X')."""
    lines = text_.splitlines(keepends=True)
    if not lines or lines[0].rstrip("\n") != "rules:":
        return None
    items: list = []
    for ln in lines[1:]:
        if ln.startswith("- "):
            items.append(ln)
        elif items and (ln.startswith(" ") or not ln.strip()):
            items[-1] += ln
        else:
            return None
    out = []
    for block in items:
        ids = re.findall(r"""^(?:- |  )id: (?:"([^"\s]+)"|'([^'\s]+)'|([^"'\s]+))[ \t]*$""", block, re.M)
        ids = [a or b or c for a, b, c in ids]
        if len(ids) != 1:
            return None
        out.append((ids[0], block if block.endswith("\n") else block + "\n"))
    return out


def build_rules(d: Path) -> tuple | None:
    """RULES_FILE from the cached packs, each rule id once (the first pack holding it wins), so semgrep loads and
    runs every rule once: (rules, duplicates dropped). None, with any older merge removed, when a pack's layout is
    not the expected one — semgrep then reads the packs themselves."""
    dest = d / RULES_FILE
    seen, blocks, dups = set(), [], 0
    for pack in SEMGREP_PACKS:
        f = d / f"{pack}.yml"
        if not f.is_file():
            continue
        rules = split_rules(f.read_text(encoding="utf-8", errors="replace"))
        if rules is None:
            dest.unlink(missing_ok=True)
            return None
        for rid, block in rules:
            if rid in seen:
                dups += 1
                continue
            seen.add(rid)
            blocks.append(block)
    if not blocks:
        dest.unlink(missing_ok=True)
        return None
    tmp = dest.with_suffix(".part")
    tmp.write_text("rules:\n" + "".join(blocks), encoding="utf-8")
    tmp.replace(dest)
    return len(blocks), dups


def runs_for(name: str, repo: Repo, mode: str) -> list:
    """Each engine's invocations: (argv after the binary, cwd or None for an empty folder, extra env)."""
    top = repo.top
    ch = repo.changed
    touched = repo.files if ch is None else [f for f in repo.files if f in ch]
    absf = [str(top / f) for f in touched]
    scope = str(repo.scope)
    if name == "keyscan":
        if ch is None:
            r = [(["--json", scope], top, {})]
            if repo.is_git:
                r.append((["--json", "-H"], top, {}))
            return r
        r = [(["--json", "-s"], top, {}), (["--json", "-H", "--range", f"{repo.base}..HEAD"], top, {})]
        if absf:
            r.append((["--json", "--", *absf], top, {}))
        return r
    if name == "trivy":
        # agents mode: one vuln run over the scope; run_engines keeps only what lies in the agent folders
        scanners = "vuln" if mode == "agents" else "vuln,misconfig,license"
        return [(["fs", "--scanners", scanners, "--format", "json", "--cache-dir", str(cache_dir() / "trivy"),
                  "--skip-db-update", "--skip-java-db-update", "--skip-check-update", "--offline-scan",
                  "--disable-telemetry", "--skip-version-check", "--ignorefile", "", "-q", "--", scope], None, {})]
    if name == "semgrep":
        cfg = [a for c in semgrep_configs() for a in ("--config", c)]
        targets = [scope] if ch is None else absf
        return [(["scan", "--json", "--metrics", "off", "--disable-nosem", *cfg, "--", *targets], None,
                 {"SEMGREP_SEND_METRICS": "off", "SEMGREP_ENABLE_VERSION_CHECK": "0"})]
    if name in ("zizmor", "actionlint"):
        wf = [str(top / f) for f in touched if WORKFLOW.search(f)]
        if name == "zizmor":
            return [(["--offline", "--no-config", "--no-ignores", "--format", "json", *wf], None, {})]
        return [(["-format", "{{json .}}", "-config-file", os.devnull, *wf], top, {})]
    if name == "hadolint":
        df = [str(top / f) for f in touched if DOCKER.search(f)]
        return [(["-f", "json", "--disable-ignore-pragma", *df], None, {})]
    if name == "gosec":
        return [(["-fmt", "json", "-quiet", "-nosec", "./..."], top / m,
                 {"GOFLAGS": "-mod=readonly", "GOPROXY": "off", "GOTOOLCHAIN": "local"}) for m in go_modules(repo.files)]
    if name == "skillspector":
        return [(["scan", "--no-llm", "--format", "json", "--output", "{OUT}", str(top / d)], None, NO_NETWORK)
                for d in touched_agent_dirs(repo, touched)]
    return []


def engine_env(extra: dict, home: str | None = None) -> dict:
    """Only the variables an engine needs to run (ENV_KEEP: paths, locale, proxy and CA settings, Go's toolchain) —
    never the caller's credentials or an engine setting that could narrow a scan — plus secscan's own.
    SECSCAN_PASS_ENV adds name prefixes, comma-separated."""
    passes = tuple(p for p in os.environ.get("SECSCAN_PASS_ENV", "").split(",") if p)
    env = {k: v for k, v in os.environ.items() if ENV_KEEP.fullmatch(k) or (passes and k.startswith(passes))}
    env.update(extra)
    if home:
        env["HOME"] = home
        env["XDG_CONFIG_HOME"] = os.path.join(home, ".config")
    return env


def static_version(name: str, binary: str) -> str:
    """The version a binary declares without running it: its Homebrew Cellar path, else its Go build info."""
    real = os.path.realpath(binary)
    m = re.search(rf"/Cellar/{re.escape(name)}/v?(\d+\.\d+\.\d+)[^/]*/", real)
    if m:
        return m.group(1)
    mod = GO_MODULE.get(name)
    if not mod:
        return ""
    try:
        with open(real, "rb") as fh, mmap.mmap(fh.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            m = re.search(rb"\nmod\t" + re.escape(mod) + rb"\tv(\d+\.\d+\.\d+)\t", mm)   # "(devel)" builds: no match
            return m.group(1).decode() if m else ""      # read while the map is open
    except (OSError, ValueError):
        return ""


def version_of(name: str, binary: str) -> str:
    """An engine's version. One with known-bad releases is only ever read statically: a version that cannot be read
    without running the binary is "" (refused by MUST_KNOW_VERSION), so a compromised build never runs."""
    if name == "keyscan":
        return ""
    if name in KNOWN_BAD:
        return static_version(name, binary)
    flag = {"actionlint": "-version", "gosec": "-version"}.get(name, "--version")
    home = tempfile.mkdtemp(prefix="secscan-home-")
    try:
        r = subprocess.run([binary, flag], capture_output=True, text=True, timeout=30, cwd=home,
                           env=engine_env({"SEMGREP_SEND_METRICS": "off", "SEMGREP_ENABLE_VERSION_CHECK": "0"}, home))
    except (OSError, subprocess.TimeoutExpired):
        return ""
    finally:
        shutil.rmtree(home, ignore_errors=True)
    if r.returncode != 0:                  # a crash's traceback holds other version numbers
        return ""
    m = re.search(r"(\d+\.\d+\.\d+)", r.stdout + r.stderr)
    return m.group(1) if m else ""


def run_one(binary: str, argv: list, cwd: Path | None, env_extra: dict, timeout: int, own_home: bool = True) -> tuple:
    """Run an engine in its own process group, from an empty folder unless it needs the repo, with an empty HOME
    unless it needs the real one; kill it on timeout."""
    tmp = tempfile.mkdtemp(prefix="secscan-")
    home = tempfile.mkdtemp(prefix="secscan-home-")
    out_file = os.path.join(tmp, "out.json")
    uses_out = "{OUT}" in argv             # the engine writes its report to a file, not stdout
    argv = [out_file if a == "{OUT}" else a for a in argv]
    env = engine_env(env_extra, home if own_home else None)
    p = None
    try:
        with _LIVE_LOCK:
            if _STOPPING.is_set():
                return None, b"", "stopped"
            p = subprocess.Popen([binary, *argv], cwd=str(cwd) if cwd else tmp, env=env, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, start_new_session=True)
            _LIVE.add(p)
        try:
            out, err = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            kill_group(p)
            return None, b"", f"timed out after {timeout} s"
        if uses_out:
            out = Path(out_file).read_bytes() if Path(out_file).is_file() else b""
        return p.returncode, out, err.decode("utf-8", "replace")
    except OSError as e:
        return None, b"", str(e)
    except BaseException:                  # Ctrl-C: the engine's whole group goes with us
        if p is not None:
            kill_group(p)
        raise
    finally:
        if p is not None:
            with _LIVE_LOCK:
                _LIVE.discard(p)
        shutil.rmtree(tmp, ignore_errors=True)
        shutil.rmtree(home, ignore_errors=True)


_LIVE: set = set()             # engine processes running now, so an interrupt can stop every one of them
_LIVE_LOCK = threading.Lock()
_STOPPING = threading.Event()


def kill_group(p: subprocess.Popen) -> None:
    try:
        os.killpg(p.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        pass
    p.wait()


def stop_all() -> None:
    """Ctrl-C: no engine starts after this, and every running engine's process group is killed."""
    with _LIVE_LOCK:
        _STOPPING.set()
        live = list(_LIVE)
    for p in live:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass


def gate(name: str, ver: str) -> Coverage | None:
    """Why an installed engine must not run: a bad or unknown release, no data."""
    if ver in KNOWN_BAD.get(name, set()):
        return Coverage(name, "refused", f"{name} {ver} is a compromised release — upgrade it", version=ver)
    if name in MUST_KNOW_VERSION and not ver:
        return Coverage(name, "refused", f"{name}'s version cannot be read without running it, so it cannot be checked "
                                         f"against known-bad releases — install it with Homebrew (or `go install …@v<version>`)")
    if name == "semgrep" and not semgrep_configs():
        return Coverage(name, "no-data", "no rule packs cached — run scan.py update", version=ver)
    if name == "trivy" and not (cache_dir() / "trivy" / "db").is_dir():
        return Coverage(name, "no-data", "no vulnerability database — run scan.py update", version=ver)
    return None


def finish(name: str, results: list, repo: Repo, ver: str, cmd_hint: str) -> tuple:
    """One engine's runs, in their order, to its coverage and findings; the first failing run decides a gap."""
    state, reason, got_all = "ran", "", []
    for rc, out, err in results:
        if rc is None:
            state, reason = "failed", err
            break
        if rc not in OK_CODES[name]:
            blocked = any(s in err.lower() for s in BLOCKED_SIGNS)
            state = "blocked" if blocked else "failed"
            reason = f"blocked by the sandbox — run in a terminal: {cmd_hint}" if blocked else (first_line(err) or f"exit {rc}")
            break
        if rc in FINDING_CODES.get(name, set()) and not out.strip():
            state, reason = "failed", f"exit {rc} means findings, but it wrote none — {first_line(err) or 'no output'}"
            break
        try:
            got, errors = PARSERS[name](out, repo)
        except Exception as e:          # odd output from one engine is that engine's gap, never the scan's crash
            got, errors = [], [f"could not read its output ({type(e).__name__})"]
        if errors:
            state, reason = "failed", "; ".join(errors[:3])
            break
        got_all += got
    if state == "ran" and name == "keyscan":
        reason = keyscan_unread(results)
    if state == "ran" and name == "skillspector":
        scanned = touched_agent_dirs(repo, repo.files if repo.changed is None else [f for f in repo.files if f in repo.changed])
        locked = {str(Path(f).parent) for f in repo.files if TRIVY_DEPS.search(f)}
        only = [f for f in repo.files if SC4_ONLY.search(f) and not TRIVY_DEPS.search(f) and "node_modules/" not in f
                and any(under(f, d) for d in scanned)
                and not (Path(f).name in LOCKED_BY_SIBLING and str(Path(f).parent) in locked)]
        if only:
            reason = (f"{', '.join(only[:5])}{f' and {len(only) - 5} more' if len(only) > 5 else ''}: dependencies checked "
                      f"against skillspector's built-in list only (OSV.dev is cut off, and trivy does not read these files)")
    cov = Coverage(name, state, reason, scope=rel(repo.top, str(repo.scope)) or ".", version=ver)
    return cov, (got_all if state == "ran" else [])


def keyscan_unread(results: list) -> str:
    """What keyscan's runs counted but could not read — binary files, nested repositories — as a coverage reason."""
    unread = nested = 0
    for _, out, _ in results:
        objs, _ = jlines(out)
        s = objs[-1].get("summary") if objs and isinstance(objs[-1], dict) else None
        if isinstance(s, dict):
            unread = max(unread, s.get("not_read") if isinstance(s.get("not_read"), int) else 0)
            nested = max(nested, s.get("nested") if isinstance(s.get("nested"), int) else 0)
    parts = ([f"{unread} binary file{'s' if unread != 1 else ''} not read"] if unread else []) + \
            ([f"{nested} nested repositor{'ies' if nested != 1 else 'y'} not scanned"] if nested else [])
    return "; ".join(parts)


def run_engines(repo: Repo, mode: str, only: str | None = None, cmd_hint: str = "",
                progress=None) -> tuple:
    """Every engine that applies, all at once: version checks in parallel, then every run of every engine in one
    pool (SECSCAN_JOBS workers, default the CPU count). Coverage keeps the mode's engine order; progress(coverage,
    findings, seconds) is called for each engine as it finishes, or at once when it cannot run; keyscan's runs are
    queued first, and its line comes when all of them, history included, are done."""
    timeout = int(os.environ.get("SECSCAN_TIMEOUT", TIMEOUT_S))
    jobs = os.environ.get("SECSCAN_JOBS") or str(os.cpu_count() or 1)
    if not (jobs.isascii() and jobs.isdigit()) or int(jobs) < 1:
        raise CannotRun(f"SECSCAN_JOBS must be a whole number of workers, not {jobs!r}")
    plan_mode = mode if (mode != "changes" or repo.changed is not None) else "full"
    names = [n for n in MODE_ENGINES[plan_mode] if not only or n == only]
    cov: dict = {}
    found: dict = {}
    bins: dict = {}
    t0 = time.monotonic()

    def tell(n):
        if progress:
            progress(cov[n], found.get(n, []), time.monotonic() - t0)

    for name in names:
        ok, why = applies(name, repo, mode)
        if not ok:
            cov[name] = Coverage(name, "n/a", why)
            continue
        binary = engine_bin(name)
        if not binary:
            cov[name] = Coverage(name, "missing", f"not installed — {INSTALL[name]}")
            continue
        bins[name] = binary
    for name in cov:
        tell(name)
    pool = ThreadPoolExecutor(max_workers=int(jobs))
    try:
        vers = dict(zip(bins, pool.map(lambda n: version_of(n, bins[n]), bins)))
        runs: dict = {}
        for name in bins:
            g = gate(name, vers[name])
            if g:
                cov[name] = g
                tell(name)
            else:
                runs[name] = runs_for(name, repo, mode)
        results = {n: [None] * len(r) for n, r in runs.items()}
        left = {n: len(r) for n, r in runs.items()}
        futures = {pool.submit(run_one, bins[n], argv, cwd, env, timeout, n not in NEEDS_HOME): (n, i)
                   for n in runs for i, (argv, cwd, env) in enumerate(runs[n])}

        def done(n):
            cov[n], found[n] = finish(n, results[n], repo, vers[n], cmd_hint)
            if n == "trivy" and plan_mode == "agents":
                dirs = agent_manifest_dirs(repo, repo.files)     # agents mode has no changed set
                found[n] = [f for f in found[n] if any(under(f.file, d) for d in dirs)]
            tell(n)

        for n in [n for n in runs if not runs[n]]:
            done(n)
        for fut in as_completed(futures):
            n, i = futures[fut]
            results[n][i] = fut.result()
            left[n] -= 1
            if left[n] == 0:
                done(n)
    except BaseException:
        stop_all()
        pool.shutdown(wait=False, cancel_futures=True)
        raise
    pool.shutdown()
    if "skillspector" in found and cov.get("trivy") and cov["trivy"].state == "ran":
        # SC4, known-vulnerable dependencies: trivy's fuller offline database covers the files it read
        found["skillspector"] = [f for f in found["skillspector"] if not (f.rules == ["SC4"] and TRIVY_DEPS.search(f.file))]
    return [f for n in names for f in found.get(n, [])], [cov[n] for n in names]


# ---------- parsers: engine output → Finding; never a code snippet ----------
def jlines(out: bytes) -> tuple:
    objs, errors = [], []
    for raw in out.decode("utf-8", "replace").splitlines():
        if raw.strip():
            try:
                objs.append(json.loads(raw))
            except ValueError:
                errors.append("an output line was not JSON")
    return objs, errors


def jdoc(out: bytes, kind: type, empty_ok: bool = False):
    s = out.decode("utf-8", "replace").strip()
    if not s:
        return (kind() if empty_ok else None), ([] if empty_ok else ["empty output"])
    try:
        d = json.loads(s)
    except ValueError:
        return None, ["output was not JSON"]
    if not isinstance(d, kind):
        return None, [f"output was JSON but not a {kind.__name__}"]
    return d, []


def parse_keyscan(out: bytes, repo: Repo) -> tuple:
    objs, errors = jlines(out)
    found = []
    if not objs or "summary" not in objs[-1]:
        errors.append("no summary line")
    for o in objs:
        if not isinstance(o, dict) or "summary" in o:
            continue
        if "note" in o:
            note, place = text(o.get("note")), text(o.get("place"))
            if note.startswith("secret-named file"):
                committed = "committed" in text(o.get("reason")) or "committed" in note
                commit, path = (place.split(" ", 1) + [""])[:2] if committed else (None, place)
                found.append(Finding(["keyscan"], ["secret-named-file"], "secret", "high",
                                     "a secret-named file is in the repo" + (" history" if committed else ""),
                                     rel(repo.top, path), commit=commit, evidence=note, tags=["CWE-538", "OWASP:A02"],
                                     fix="remove the file from git (and from history if it was pushed); keep it out with .gitignore"))
            else:
                errors.append(f"{note}: {place}")
            continue
        rules = [text(r) for r in o.get("rules") or []] or ["keyscan"]
        found.append(Finding(["keyscan"], rules, "secret", "high", "hard-coded secret: " + ", ".join(rules),
                             rel(repo.top, text(o.get("file"))), line=o.get("line") if isinstance(o.get("line"), int) else None,
                             commit=o.get("commit") or None, evidence=f"{text(o.get('preview')) or '?'}… matched {', '.join(rules)}",
                             tags=["CWE-798", "OWASP:A07"],
                             fix="revoke the key at its provider first, then remove it (and from history if it was pushed)"))
    return found, errors


def _vkey(v: str) -> tuple:
    return tuple(int(x) if x.isdigit() else 0 for x in re.split(r"[.\-+]", v or "0"))


def parse_trivy(out: bytes, repo: Repo) -> tuple:
    doc, errors = jdoc(out, dict)
    if doc is None:
        return [], errors
    found = []
    scope = repo.scope if repo.scope.is_dir() else repo.scope.parent
    for res in doc.get("Results") or []:
        if not isinstance(res, dict):
            continue
        tgt = text(res.get("Target"))
        target = rel(repo.top, str(scope / tgt)) if (scope / tgt).exists() else (rel(repo.top, tgt) if (repo.top / tgt).exists() else tgt)
        by_pkg: dict = {}
        for v in res.get("Vulnerabilities") or []:
            by_pkg.setdefault((text(v.get("PkgName")), text(v.get("InstalledVersion"))), []).append(v)
        for (pkg, ver), vs in by_pkg.items():
            top_sev = max((sev(v.get("Severity")) for v in vs), key=SEVERITIES.index)
            fixed = sorted({text(v.get("FixedVersion")).split(",")[0].strip() for v in vs if v.get("FixedVersion")}, key=_vkey)
            ids = [text(v.get("VulnerabilityID")) or "unnamed" for v in vs]
            cwes = cwe_ids([c for v in vs for c in v.get("CweIDs") or []])
            found.append(Finding(["trivy"], ids, "dependency", top_sev,
                                 f"{pkg} {ver}: {len(vs)} known vulnerabilit{'y' if len(vs) == 1 else 'ies'}", target,
                                 evidence=", ".join(ids), tags=tags_for(cwes[:2], "dependency"), group=pkg,
                                 fix=f"upgrade {pkg} to {fixed[-1]} or later" if fixed else "no fixed version yet — replace or isolate it"))
        for m in res.get("Misconfigurations") or []:
            if m.get("Status") != "FAIL":
                continue
            line = (m.get("CauseMetadata") or {}).get("StartLine")
            found.append(Finding(["trivy"], [text(m.get("ID") or m.get("AVDID")) or "misconfig"], "misconfig", sev(m.get("Severity")),
                                 text(m.get("Title")) or "misconfiguration", target, line=line if isinstance(line, int) and line > 0 else None,
                                 evidence=text(m.get("Message")), tags=tags_for([], "misconfig"), fix=text(m.get("Resolution")) or None))
        for lic in res.get("Licenses") or []:
            if sev(lic.get("Severity")) in ("high", "critical"):
                pkg = text(lic.get("PkgName"))
                lfile = text(lic.get("FilePath")) or (target if (repo.top / target).exists() else "")
                found.append(Finding(["trivy"], [text(lic.get("Name")) or "licence"], "other", sev(lic.get("Severity")),
                                     f"licence {text(lic.get('Name'))} ({text(lic.get('Category'))}) in {pkg or target}",
                                     rel(repo.top, lfile) if lfile else "(dependency tree)", evidence=f"{pkg}: {text(lic.get('Name'))}",
                                     group=f"lic:{pkg}", fix="check the licence against how the code is shipped"))
    return found, errors


def parse_semgrep(out: bytes, repo: Repo) -> tuple:
    doc, errors = jdoc(out, dict)
    if doc is None:
        return [], errors
    errors += [first_line(e.get("message")) or "semgrep error" for e in doc.get("errors") or []
               if isinstance(e, dict) and text(e.get("level", "error")).lower() == "error"]
    found = []
    for r in doc.get("results") or []:
        ex = r.get("extra") or {}
        meta = ex.get("metadata") or {}
        cwes = cwe_ids(meta.get("cwe") if isinstance(meta.get("cwe"), list) else [meta.get("cwe")])
        rule = text(r.get("check_id") or "semgrep").split(".")[-1]
        f = rel(repo.top, text(r.get("path")))
        cat = category_for(cwes, rule, f)
        if cat == "other" and "secret" in " ".join(text(x) for x in meta.get("vulnerability_class") or []).lower():
            cat = "secret"
        conf = {"high": "high", "medium": "medium", "low": "low"}.get(text(meta.get("confidence")).lower(), "medium")
        msg = first_line(ex.get("message")) or rule
        line = (r.get("start") or {}).get("line")
        found.append(Finding(["semgrep"], [rule], cat, sev(ex.get("severity")), msg, f,
                             line=line if isinstance(line, int) else None, evidence=msg,
                             tags=tags_for(cwes, cat, meta.get("owasp") if isinstance(meta.get("owasp"), list) else []),
                             fix=None,          # semgrep's fix is the matched source rewritten: a code snippet, never shown
                             confidence=conf))
    return found, errors


def parse_zizmor(out: bytes, repo: Repo) -> tuple:
    doc, errors = jdoc(out, list, empty_ok=True)
    if doc is None:
        return [], errors
    found = []
    for z in doc:
        if not isinstance(z, dict):
            continue
        locs = z.get("locations") or []
        prim = next((l for l in locs if (l.get("symbolic") or {}).get("kind") == "Primary"), locs[0] if locs else {})
        key = ((prim.get("symbolic") or {}).get("key") or {}).get("Local") or {}
        path = text(key.get("verbatim_path") or key.get("given_path"))
        row = (((prim.get("concrete") or {}).get("location") or {}).get("start_point") or {}).get("row")
        ident = text(z.get("ident")) or "zizmor"
        f = rel(repo.top, path)
        cat = category_for([], ident, f)
        det = z.get("determinations") or {}
        found.append(Finding(["zizmor"], [ident], cat, sev(det.get("severity")), text(z.get("desc")) or ident, f,
                             line=(row + 1) if isinstance(row, int) else None, evidence=text(z.get("desc")),
                             tags=tags_for([], cat), fix=text(z.get("url")) or None,
                             confidence=sev(det.get("confidence"), {"high": "high", "medium": "medium", "low": "low"})))
    return found, errors


def parse_actionlint(out: bytes, repo: Repo) -> tuple:
    doc, errors = jdoc(out, list, empty_ok=True)
    if doc is None:
        return [], errors
    found = []
    for a in doc:
        if not isinstance(a, dict):
            continue
        fp = text(a.get("filepath"))
        f = rel(repo.top, fp if os.path.isabs(fp) else str((repo.top / fp).resolve()))
        msg = first_line(a.get("message"))
        cat = category_for([], "untrusted" if "untrusted" in msg else text(a.get("kind")) or "actionlint", f)
        found.append(Finding(["actionlint"], [text(a.get("kind")) or "actionlint"], cat, "medium", msg or "workflow error", f,
                             line=a.get("line") if isinstance(a.get("line"), int) else None, evidence=msg, tags=tags_for([], cat)))
    return found, errors


def parse_hadolint(out: bytes, repo: Repo) -> tuple:
    doc, errors = jdoc(out, list, empty_ok=True)
    if doc is None:
        return [], errors
    return [Finding(["hadolint"], [text(h.get("code")) or "hadolint"], "misconfig",
                    sev(h.get("level"), {"error": "high", "warning": "medium", "info": "low", "style": "low"}),
                    text(h.get("message")), rel(repo.top, text(h.get("file"))),
                    line=h.get("line") if isinstance(h.get("line"), int) else None,
                    evidence=text(h.get("message")), tags=tags_for([], "misconfig"))
            for h in doc if isinstance(h, dict)], errors


def parse_gosec(out: bytes, repo: Repo) -> tuple:
    doc, errors = jdoc(out, dict, empty_ok=True)
    if doc is None:
        return [], errors
    if doc.get("Golang errors"):
        errors.append(f"could not load {len(doc['Golang errors'])} Go package(s) (offline, no module cache?)")
    found = []
    for i in doc.get("Issues") or []:
        cw = i.get("cwe") or {}
        cwes = cwe_ids([f"CWE-{cw.get('id')}"] if cw.get("id") else [])
        f = rel(repo.top, text(i.get("file")))
        cat = category_for(cwes, text(i.get("rule_id")), f)
        ln = text(i.get("line")).split("-")[0]
        found.append(Finding(["gosec"], [text(i.get("rule_id")) or "gosec"], cat, sev(i.get("severity")), text(i.get("details")), f,
                             line=int(ln) if ln.isdigit() else None, evidence=text(i.get("details")), tags=tags_for(cwes, cat),
                             confidence=sev(i.get("confidence"), {"high": "high", "medium": "medium", "low": "low"})))
    return found, errors


def parse_skillspector(out: bytes, repo: Repo) -> tuple:
    doc, errors = jdoc(out, dict)
    if doc is None:
        return [], errors
    src = Path(text((doc.get("skill") or {}).get("source")) or repo.top)
    found = []
    for i in doc.get("issues") or []:
        loc = i.get("location") or {}
        f = rel(repo.top, str(src / text(loc.get("file") or "SKILL.md")))
        if text(i.get("id")) == "SC4" and text(i.get("finding")) == "SC4 fallback active":
            continue    # its "OSV.dev unreachable" notice: expected, secscan cuts the lookup off (run_engines drops SC4 trivy covers)
        try:
            conf = float(i.get("confidence") or 0)
        except (TypeError, ValueError):
            conf = 0.0
        ln = loc.get("start_line")
        found.append(Finding(["skillspector"], [text(i.get("id")) or "skillspector"], "prompt-injection", sev(i.get("severity")),
                             f"{text(i.get('category')) or 'agent risk'}: {text(i.get('pattern'))}".strip(": "), f,
                             line=ln if isinstance(ln, int) else None, evidence=text(i.get("finding")),
                             tags=tags_for([], "prompt-injection") + ["ASI01"], fix=text(i.get("remediation")) or None,
                             confidence="high" if conf >= 0.8 else "medium"))
    return found, errors


PARSERS = {"keyscan": parse_keyscan, "trivy": parse_trivy, "semgrep": parse_semgrep, "zizmor": parse_zizmor,
           "actionlint": parse_actionlint, "hadolint": parse_hadolint, "gosec": parse_gosec,
           "skillspector": parse_skillspector}


# ---------- merge, ids, values, the changes filter, suppressions ----------
def finding_id(f: Finding) -> str:
    key = f"{f.category}|{f.file}|{f.commit or ''}|{f.line if f.line is not None else f.group}|{f.rules[0] if f.rules else ''}"
    return hashlib.sha256(key.encode()).hexdigest()[:12]


def _cwe(f: Finding) -> str:
    return next((t for t in f.tags if t.startswith("CWE-")), "")


def _preview(f: Finding) -> str:
    return f.evidence.split("…", 1)[0] if "…" in f.evidence else ""


def _joins(f: Finding, m: dict) -> bool:
    """Does f share a root cause with the cluster m (same file, category, package and commit already)?
    A secret: only on the same line. Else within 3 lines of the cluster's first: on a member's line (engines tag
    one flaw with unrelated CWEs, so the line decides); nearby, from another engine with a compatible CWE, or from
    the same engine with the same CWE."""
    if f.line is None or m["first"] is None:
        return f.line is None and m["first"] is None
    if f.line - m["first"] > 3:
        return False
    cwe = _cwe(f)
    compatible = not cwe or not m["cwes"] or cwe in m["cwes"]
    if f.line in m["lines"]:
        return True
    if f.category == "secret":
        return False
    if set(f.sources).isdisjoint(m["sources"]):
        return compatible
    return bool(cwe) and cwe in m["cwes"]


def merge(findings: list) -> list:
    """One finding per root cause (see _joins); a finding is compared with every open cluster of its place."""
    for f in findings:
        f.id = finding_id(f)
    # a secret still in the file is one root cause with the commit that added it — on the very same line only
    present = {(f.file, tuple(f.rules), _preview(f), f.line) for f in findings if f.category == "secret" and not f.commit}
    for f in findings:
        if f.category == "secret" and f.commit and (f.file, tuple(f.rules), _preview(f), f.line) in present:
            f.evidence = (f.evidence + "; also in history").lstrip("; ")
            f.commit = None
    findings = sorted(findings, key=lambda f: (f.file, f.category, f.group, f.commit or "", f.line or 0))
    out: list = []
    meta: list = []                 # per cluster: first line, member lines, CWEs, sources, best fix severity
    open_by_place: dict = {}        # (file, category, group, commit) → indices of its clusters
    for f in findings:
        place = (f.file, f.category, f.group, f.commit)
        hit = next((i for i in open_by_place.get(place, []) if _joins(f, meta[i])), None)
        if hit is not None:
            last, m = out[hit], meta[hit]
            if SEVERITIES.index(f.severity) > SEVERITIES.index(last.severity):
                last.severity, last.title, last.id = f.severity, f.title, f.id
            if f.fix and SEVERITIES.index(f.severity) >= m["fix_sev"]:
                last.fix, m["fix_sev"] = f.fix, SEVERITIES.index(f.severity)
            last.sources = list(dict.fromkeys(last.sources + f.sources))
            last.rules = list(dict.fromkeys(last.rules + f.rules))
            last.tags = list(dict.fromkeys(last.tags + f.tags))
            if f.evidence and f.evidence not in last.evidence:
                last.evidence = (last.evidence + "; " + f.evidence) if last.evidence else f.evidence
            last.confidence = max(last.confidence, f.confidence, key=lambda c: CONFIDENCES.index(c) if c in CONFIDENCES else -1)
            m["lines"].add(f.line)
            m["sources"].update(f.sources)
            if _cwe(f):
                m["cwes"].add(_cwe(f))
        else:
            open_by_place.setdefault(place, []).append(len(out))
            out.append(f)
            meta.append({"first": f.line, "lines": {f.line}, "cwes": {_cwe(f)} - {""}, "sources": set(f.sources),
                         "fix_sev": SEVERITIES.index(f.severity) if f.fix else -1})
    return sorted(out, key=lambda f: (-SEVERITIES.index(f.severity), f.file, f.line or 0))


def group_findings(findings: list, units: list) -> list:
    """Findings repeating one rule inside one skill (or one file outside any skill) as one entry each, worst first,
    so a reviewer reads the group, not every member; members are named by id and by their 1-based number in
    findings (numbers survive masking). A lone finding is not grouped; secrets never are — each is its own key to
    revoke — and neither are history hits."""
    units = sorted(units, key=len, reverse=True)

    def unit_of(f: Finding) -> str:
        return next((u for u in units if u in (".", "") or f.file == u or f.file.startswith(u + "/")), f.file)

    by_key: dict = {}
    for n, f in enumerate(findings, 1):
        if not f.commit and f.category != "secret":
            by_key.setdefault((f.sources[0] if f.sources else "", f.rules[0] if f.rules else "", f.category, unit_of(f)), []).append((n, f))
    groups = []
    for (engine, rule, _, unit), members in by_key.items():
        if len(members) < 2:
            continue
        worst = max((f for _, f in members), key=lambda f: SEVERITIES.index(f.severity))
        groups.append({"engine": engine, "rule": rule, "unit": unit, "count": len(members), "severity": worst.severity,
                       "title": worst.title, "ids": [f.id for _, f in members], "members": [n for n, _ in members]})
    return sorted(groups, key=lambda g: (-SEVERITIES.index(g["severity"]), -g["count"], g["unit"], g["rule"]))


def progress_line(c: Coverage, found: list, secs: float) -> str:
    """One stderr line per engine: as it finishes, or at once when it cannot run. keyscan's names the present-tree
    places to revoke first (masked); history hits are only counted, never placed."""
    line = f"▸ {c.engine} {c.state} at {secs:.1f} s" + (f", {len(found)} raw hit(s)" if c.state == "ran" else "")
    if c.engine != "keyscan" or not found:
        return line
    places = sorted({printable(f"{f.file}:{f.line}" if f.line else f.file) for f in found if not f.commit})
    history = len({(f.commit, f.file, f.line) for f in found if f.commit})
    tail = (f" — revoke first: {', '.join(places[:10])}" + (f" +{len(places) - 10} more" if len(places) > 10 else "")
            if places else " — revoke first") + (f"; {history} history hit(s)" if history else "")
    masked = mask_texts([line + tail])
    return masked[0] if masked else line + " — revoke first (places withheld: keyscan --mask unavailable)"


def mask_texts(texts: list):
    """Every text through keyscan --mask, one line each: what a rule matches is replaced. None when it cannot run.

    A private-key BEGIN line with no END masks every later line too: it fails safe (more withheld, nothing shown)."""
    if not texts:
        return []
    k = engine_bin("keyscan")
    if not k:
        return None
    flat = [re.sub(r"[\r\n\x0b\x0c\x1c-\x1e\x85  ]", " ", text(t)) for t in texts]
    with tempfile.TemporaryDirectory(prefix="secscan-mask-") as d:
        p = Path(d) / "texts.txt"
        p.write_bytes(("\n".join(flat) + "\n").encode("utf-8"))
        r = mask_file(k, p, Path(d))
        if r is None:
            return None
        lines = r.decode("utf-8", "replace").split("\n")
        if len(lines) != len(flat) + 1 or lines[-1] != "":
            return None
        return lines[:-1]


def mask_file(keyscan: str, path: Path, cwd: Path) -> bytes | None:
    """keyscan --mask on one file, with the allowlisted environment and a time limit; None when it fails — and when it
    warns (gitleaks missing: only keyscan's own patterns masked), since a partial mask must not pass as a full one."""
    try:
        r = subprocess.run([keyscan, "--mask", str(path)], capture_output=True, cwd=str(cwd), env=engine_env({}, str(cwd)),
                           timeout=int(os.environ.get("SECSCAN_TIMEOUT", TIMEOUT_S)))
    except (OSError, subprocess.TimeoutExpired):
        return None
    return r.stdout if r.returncode == 0 and not r.stderr.strip() else None


def mask_doc(doc: dict) -> dict:
    """Every string a reader sees through keyscan --mask, then cut to length; withheld when masking cannot run.
    Only the fixed words under ENUM_KEYS and dict keys are left as they are."""
    slots = []

    def walk(o, key=None):
        if isinstance(o, dict):
            for k in o:
                if isinstance(o[k], str):
                    fixed_word = k in ENUM_KEYS and re.fullmatch(r"[a-z/-]{1,20}", o[k])
                    if o[k] and not fixed_word:
                        slots.append((o, k, k))
                else:
                    walk(o[k], k)
        elif isinstance(o, list):
            for i, v in enumerate(o):
                if isinstance(v, str):
                    if v and key not in ("sources",):
                        slots.append((o, i, key))
                else:
                    walk(v, key)

    walk(doc)
    masked = mask_texts([o[k] for o, k, _ in slots])
    for n, (o, k, name) in enumerate(slots):
        if masked is None:
            o[k] = "(withheld: keyscan --mask unavailable)"
            continue
        limit = TRUNC.get(name, TRUNC_OTHER)
        v = masked[n]
        o[k] = v if len(v) <= limit else v[:limit - 1] + "…"
    return doc


def settle(findings: list, repo: Repo) -> tuple:
    """The changes filter on every raw hit first, then the merge: a new hit is never hidden inside an older one."""
    keep, old = split_predates(findings, repo)
    return merge(keep), old


def split_predates(findings: list, repo: Repo) -> tuple:
    if repo.changed is None:
        return findings, 0
    keep, old = [], 0
    for f in findings:
        if f.commit:                       # a history hit comes from base..HEAD: it goes out with the push
            keep.append(f)
            continue
        if f.file not in repo.changed:
            old += 1
            continue
        lines = repo.changed[f.file]
        if lines is None or f.line is None or f.line in lines:
            keep.append(f)
        else:
            old += 1
    return keep, old


def _read(p: Path) -> str:
    try:
        if p.stat().st_size > 2_000_000:
            return ""
        b = p.read_bytes()
    except OSError:
        return ""
    return "" if b"\0" in b[:4096] else b.decode("utf-8", "replace")


def find_suppressions(repo: Repo) -> list:
    out = []
    for f in repo.files:
        p = repo.top / f
        if Path(f).name in (".semgrepignore", ".gitleaksignore"):
            for n, line in enumerate(_read(p).splitlines(), 1):
                if line.strip() and not line.lstrip().startswith("#"):
                    out.append({"file": f, "line": n, "marker": f"{Path(f).name}:{line.strip()}"})
            continue
        for n, line in enumerate(_read(p).splitlines(), 1):
            for m in SUPPRESS_MARKERS:
                if m in line:
                    out.append({"file": f, "line": n, "marker": m})
    return out


def folder_coverage(repo: Repo, coverage: list, mode: str = "full") -> list:
    ran = [c.engine for c in coverage if c.state == "ran"]
    ch = repo.changed
    tops = sorted({f.split("/", 1)[0] if "/" in f else "." for f in repo.files})
    every = agent_dirs(repo, repo.files)
    trivy_dirs = agent_manifest_dirs(repo, repo.files) if mode == "agents" else None
    out = []
    for t in tops:
        files = [f for f in repo.files if (f.split("/", 1)[0] if "/" in f else ".") == t]
        if ch is not None:
            files = [f for f in files if f in ch]
        engines = [e for e in ran if (e in ("keyscan", "semgrep") and files)
                   or (e == "trivy" and files and (trivy_dirs is None or any(under(f, d) for f in files for d in trivy_dirs)))
                   or (e in ("zizmor", "actionlint") and any(WORKFLOW.search(f) for f in files))
                   or (e == "hadolint" and any(DOCKER.search(f) for f in files))
                   or (e == "gosec" and any(f.endswith(".go") for f in files))
                   or (e == "skillspector" and touched_agent_dirs(repo, files, every))]
        out.append({"folder": t, "engines": engines,
                    "skipped_reason": None if engines else ("unchanged" if ch is not None and not files else "no engine ran over it")})
    return out


# ---------- data: update and age ----------
def read_stamp() -> dict:
    try:
        s = json.loads((cache_dir() / "stamp.json").read_text())
        return s if isinstance(s, dict) else {}
    except (OSError, ValueError):
        return {}


def data_age_days() -> dict:
    s = read_stamp()
    now = dt.datetime.now(dt.timezone.utc)
    out = {}
    for k in ("trivy", "semgrep"):
        try:
            out[k] = (now - dt.datetime.fromisoformat(s[k])).days
        except (KeyError, ValueError, TypeError):
            out[k] = None
    return out


def in_sandbox() -> bool:
    try:
        with open("/etc/ssl/cert.pem", "rb"):
            return False
    except PermissionError:
        return True
    except OSError:
        return False


def update(script: str) -> int:
    if in_sandbox():
        print(f"⚠ scan.py update needs the network — run in a terminal:\n  python3 {shlex.quote(script)} update", file=sys.stderr)
        return 2
    c = cache_dir()
    (c / "trivy").mkdir(parents=True, exist_ok=True)
    (c / "semgrep").mkdir(parents=True, exist_ok=True)
    stamp = read_stamp()
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    ok = True
    trivy = engine_bin("trivy")
    ver = version_of("trivy", trivy) if trivy else ""
    if not trivy:
        ok = False
        print(f"✗ trivy: missing — {INSTALL['trivy']}")
    elif not ver or ver in KNOWN_BAD["trivy"]:
        ok = False
        print(f"✗ trivy {ver or '(unknown version)'}: refused — upgrade it before it touches the network")
    else:
        base = [trivy, "fs", "--cache-dir", str(c / "trivy"), "--disable-telemetry", "--skip-version-check", "-q"]
        empty = tempfile.mkdtemp(prefix="secscan-upd-")
        tok = True
        for extra in (["--download-db-only"], ["--download-java-db-only"], ["--scanners", "misconfig", "--format", "json"]):
            r = subprocess.run([*base, *extra, empty], capture_output=True, text=True, env=engine_env({}))
            tok &= r.returncode == 0
            print(("✓" if r.returncode == 0 else "✗") + f" trivy {' '.join(extra)}" + ("" if r.returncode == 0 else f": {first_line(r.stderr)}"))
        shutil.rmtree(empty, ignore_errors=True)
        ok &= tok
        if tok:
            stamp["trivy"] = now
    sok = True
    for pack in SEMGREP_PACKS:
        dest = c / "semgrep" / f"{pack}.yml"
        try:
            with urllib.request.urlopen(f"https://semgrep.dev/c/p/{pack}", timeout=60) as resp:
                data = resp.read()
            tmp = dest.with_suffix(".part")
            tmp.write_bytes(data)
            tmp.replace(dest)
            print(f"✓ semgrep p/{pack}")
        except OSError as e:
            sok = False
            print(f"✗ semgrep p/{pack}: {e}")
    try:
        built, why = build_rules(c / "semgrep"), ""
    except OSError as e:
        built, why = None, str(e)
        for stale in (RULES_FILE, Path(RULES_FILE).with_suffix(".part").name):
            try:
                (c / "semgrep" / stale).unlink(missing_ok=True)
            except OSError:
                why += f"; could not remove {stale}"
    if not built and not why:
        why = "no pack cached" if not semgrep_configs() else "unexpected layout"
    print(f"✓ semgrep {RULES_FILE}: {built[0]} rules, {built[1]} duplicate(s) dropped" if built
          else f"⚠ semgrep packs not merged ({why}) — semgrep reads each pack")
    ok &= sok
    if sok:
        stamp["semgrep"] = now
    (c / "stamp.json").write_text(json.dumps(stamp))
    print(("✓ engine data refreshed" if ok else "⚠ engine data partly refreshed") + f" — {c}")
    return 0 if ok else 1


def doctor() -> int:
    print(f"cache: {cache_dir()}  ages (days): {data_age_days()}")
    if in_sandbox():
        print("⚠ inside a sandbox: semgrep, skillspector and trivy's misconfig checks will be blocked — run scan.py in a terminal")
    bad = 0
    for name in ENGINES:
        b = engine_bin(name)
        if not b:
            bad += 1
            print(f"  ✗ {name:<12} missing — {INSTALL[name]}")
            continue
        v = version_of(name, b)
        refused = v in KNOWN_BAD.get(name, set()) or (name in MUST_KNOW_VERSION and not v)
        bad += refused
        print(f"  {'✗' if refused else '✓'} {name:<12} {v or '?':<9} {b}" + ("  REFUSED: compromised or unknown release" if refused else ""))
    print("✓ all engines ready" if not bad else f"⚠ {bad} engine(s) missing or refused")
    return 0 if not bad else 1


# ---------- report ----------
def render(doc: dict) -> str:
    fs = doc.get("findings") or []
    cov = doc.get("coverage") or []
    gaps = [c for c in cov if c.get("state") not in ("ran", "n/a")]
    head = [printable(doc.get("mode", "full"))] + ([printable(doc["profile"])] if doc.get("profile") else [])
    lines = [f"# secscan report — {' '.join(head)} · {printable(doc.get('revision', '?'))} · {dt.date.today().isoformat()}", "",
             f"**{len(fs)} finding(s)**, {len(gaps)} coverage gap(s)."
             + ("" if fs else " No findings in what ran — the gaps below were not checked." if gaps
                else " Zero findings — see coverage below."),
             "", "Places and 4-character previews only; no secret value is in this report.", ""]
    groups = doc.get("groups") or []
    number = {f["id"]: n for n, f in enumerate(fs, 1) if isinstance(f.get("id"), str)}
    ids_usable = len(number) == len(fs)        # withheld ids all read the same, so they cannot tell findings apart
    members = []                               # per group: finding numbers in THIS doc (the review may reorder or drop)
    for g in groups:
        ids, stored = g.get("ids"), g.get("members")
        if ids_usable:
            members.append([number[i] for i in (ids if isinstance(ids, list) else []) if isinstance(i, str) and i in number])
        else:
            members.append([m for m in (stored if isinstance(stored, list) else []) if isinstance(m, int)])
    if groups:
        lines += ["## Repeated findings", "", "One rule repeating inside one skill or file; every member is listed below too.", "",
                  "| count | worst | rule | where | title | findings |", "|---|---|---|---|---|---|"]
        lines += [f"| {printable(text(g.get('count')))}× | {printable(g.get('severity'))} | {printable(g.get('engine'))} "
                  f"{printable(g.get('rule'))} | `{printable(g.get('unit'))}` | {printable(g.get('title'))} | "
                  f"{', '.join('#' + str(m) for m in ms) or '—'} |" for g, ms in zip(groups, members)]
        lines.append("")
    if fs:
        lines += ["| # | severity | place | title | confidence | tags |", "|---|---|---|---|---|---|"]
        for n, f in enumerate(fs, 1):
            place = f"{f.get('commit') + ' ' if f.get('commit') else ''}{f.get('file')}{':' + str(f['line']) if f.get('line') else ''}"
            lines.append(f"| {n} | {printable(f.get('severity'))} | `{printable(place)}` | {printable(f.get('title'))} | "
                         f"{printable(f.get('confidence'))} | {printable(' '.join(text(t) for t in f.get('tags') or []))} |")
        lines.append("")
        for n, f in enumerate(fs, 1):
            lines += [f"### {n}. {printable(f.get('title'))}"]
            if f.get("claim"):
                lines.append(f"- claim: {printable(f['claim'])}")
            lines += [f"- evidence: {printable(f.get('evidence')) or '—'}",
                      f"- sources: {printable(', '.join(text(s) for s in f.get('sources') or []))}",
                      f"- fix: {printable(f.get('fix')) or '—'}", ""]
    for key, head in (("needs_validation", "Needs validation"), ("hardening", "Hardening notes")):
        if doc.get(key):
            lines += [f"## {head}", *[f"- {printable(x)}" for x in doc[key]], ""]
    rejected = [r for r in doc.get("rejected") or [] if isinstance(r, dict)]
    if rejected:
        lines += [f"## Rejected candidates ({len(rejected)})",
                  *[f"- `{printable(r.get('place'))}` — {printable(r.get('reason'))}" for r in rejected], ""]
    tools = [t for t in doc.get("tools") or [] if isinstance(t, dict)]     # what secscan called; never re-scored here
    if tools:
        lines += ["## Called tools",
                  *[f"- {printable(t.get('tool'))}" + (f" — {printable(t['job'])}" if t.get("job") else "")
                    + (f" · report `{printable(t['report'])}`" if t.get("report") else "")
                    + f": {printable(t.get('summary')) or '—'}" for t in tools], ""]
    lines += ["## Suppressions honoured",
              *([f"- `{printable(s.get('file'))}:{s.get('line')}` {printable(s.get('marker'))}" for s in doc["suppressions"]]
                if doc.get("suppressions") else ["- none"]), ""]
    lines += ["## Coverage", *[f"- {printable(c.get('engine'))}: {printable(c.get('state'))}"
                                f"{' — ' + printable(c['reason']) if c.get('reason') else ''}" for c in cov]]
    lines += [f"- folder `{printable(x.get('folder'))}`: {printable(', '.join(text(e) for e in x.get('engines') or [])) or printable(x.get('skipped_reason'))}"
              for x in doc.get("folders") or []]
    if isinstance(doc.get("versions"), dict) and doc["versions"]:
        lines.append("- versions: " + printable(", ".join(f"{k} {v}" for k, v in doc["versions"].items())))
    if doc.get("predates_change"):
        lines.append(f"- {printable(doc['predates_change'])} older hit(s) predate the change")
    lines.append("- residual risk: a secret in a format no rule knows stays unmasked in the mirror the called tools read, "
                 "and in the live checkout that Scan changes and Suggest patches read")
    return "\n".join(lines) + "\n"


def report(src: str, outdir: str) -> int:
    try:
        doc = json.loads(Path(src).read_text())
        if not isinstance(doc, dict):
            raise ValueError("not an object")
    except (OSError, ValueError) as e:
        return fail(f"cannot read {src}: {e}")
    for key in ("findings", "groups", "coverage", "suppressions", "folders", "rejected", "tools"):  # odd input dropped, never a crash
        v = doc.get(key)
        doc[key] = [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []
    for key in ("needs_validation", "hardening"):
        v = doc.get(key)
        doc[key] = [text(x) for x in v] if isinstance(v, list) else ([text(v)] if v else [])
    for f in doc["findings"]:
        if not isinstance(f.get("line"), int):
            f["line"] = int(f["line"]) if text(f.get("line")).isdigit() else None
    doc = mask_doc(doc)
    out = Path(outdir)
    out.mkdir(parents=True, exist_ok=True)
    stem = f"secscan-{dt.date.today().isoformat()}"
    if (out / f"{stem}.md").exists():
        stem += dt.datetime.now().strftime("-%H%M%S")
    (out / f"{stem}.md").write_text(render(doc))
    (out / f"{stem}.json").write_text(json.dumps(doc, indent=1))
    print(f"✓ report written — {out / (stem + '.md')}")
    return 0


# ---------- the masked mirror: what a reviewer reads instead of the repo ----------
def keyscan_places(keyscan: str, target: Path, cwd: Path, top: Path) -> tuple | None:
    """keyscan --strict --json over target: (files with a hit, files noted secret-named, files it could not vouch for),
    each relative to top; None when the scan itself could not run or gave no summary."""
    rc, out, err = run_one(keyscan, ["--strict", "--json", str(target)], cwd, {}, int(os.environ.get("SECSCAN_TIMEOUT", TIMEOUT_S)))
    objs, errors = jlines(out)
    if rc not in (0, 1) or errors or not objs or "summary" not in objs[-1]:
        return None
    hits, named, unsure = set(), set(), set()
    for o in objs[:-1]:
        if not isinstance(o, dict):
            return None
        if "note" in o:
            place = text(o.get("place"))
            (named if text(o.get("note")).startswith("secret-named file") else unsure).add(rel(top, place.split(": ", 1)[0]))
        else:
            hits.add(rel(top, text(o.get("file"))))
    return hits, named, unsure


def mirror(dest_arg: str, path: Path) -> int:
    """Copies of the repo's files a reader may open: a file with any keyscan hit goes through keyscan --mask; a
    secret-named, binary, oversized, symlinked or unvouched file is left out. The copy is scanned again, and a file
    still matching is removed. .secscan-mirror.json lists what was masked and what was skipped (names only)."""
    k = engine_bin("keyscan")
    if not k:
        return fail(f"mirror needs keyscan — {INSTALL['keyscan']}")
    repo = discover(path, "full", None)
    dest = Path(dest_arg).resolve()          # resolved, so the re-check below compares like with like (/tmp → /private/tmp)
    for t in {repo.top, repo.top.resolve()}:
        if dest == t or t in dest.parents or dest.resolve() == t or t in dest.resolve().parents:
            return fail(f"the mirror must be outside the repo: {dest}")
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        return fail(f"{dest} is not an empty folder")
    places = keyscan_places(k, repo.scope, repo.top, repo.top)
    if places is None:
        return fail("keyscan could not scan the repo, so nothing is mirrored")
    hits, named, unsure = places
    dest.mkdir(parents=True, exist_ok=True)
    masked, skipped, copied = [], [{"file": f, "why": "symlink"} for f in repo.links], 0
    with tempfile.TemporaryDirectory(prefix="secscan-mirror-") as work:
        for f in repo.files:
            p = repo.top / f
            why = ("symlink" if p.is_symlink()
                   else "control character in its name" if CONTROL.search(f)        # keyscan's places cannot name it
                   else "secret-named" if f in named or (SECRET_NAME.search(f) and not TEMPLATE_NAME.search(f))
                   else "keyscan could not vouch for it" if f in unsure
                   else "too large" if p.stat().st_size > MIRROR_MAX else "")
            body = b""
            if not why:
                try:
                    body = p.read_bytes()
                except OSError:
                    why = "unreadable"
            if not why and b"\0" in body[:8192]:
                why = "binary"
            if not why and f in hits:
                body = mask_file(k, p, Path(work))
                why = "" if body is not None else "masking failed"
            if why:
                skipped.append({"file": f, "why": why})
                continue
            q = dest / f
            q.parent.mkdir(parents=True, exist_ok=True)
            q.write_bytes(body)
            copied += 1
            if f in hits:
                masked.append(f)
        again = keyscan_places(k, dest, Path(work), dest)
    if again is None:
        shutil.rmtree(dest, ignore_errors=True)
        return fail("keyscan could not re-check the mirror, so it was removed")
    for f in sorted(again[0] | again[1] | again[2]):
        q = dest / f
        if q.is_file() and dest in q.resolve().parents:
            q.unlink()
            copied -= 1
            skipped.append({"file": f, "why": "still matched after masking"})
            if f in masked:
                masked.remove(f)
    names = mask_texts([printable(x) for x in masked] + [printable(s["file"]) for s in skipped])
    if names is None:
        names = ["(withheld: keyscan --mask unavailable)"] * (len(masked) + len(skipped))
    masked = names[:len(masked)]
    for s, n in zip(skipped, names[len(masked):]):
        s["file"] = n
    (dest / ".secscan-mirror.json").write_text(json.dumps({"masked": masked, "skipped": skipped}, indent=1))
    print(f"✓ mirror written — {dest}: {copied} file(s), {len(masked)} masked, {len(skipped)} left out")
    return 0


# ---------- main ----------
def fail(msg: str) -> int:
    print(f"✗ could not scan: {msg}", file=sys.stderr)
    return 2


def revision(repo: Repo) -> str:
    if not repo.is_git:
        return "not-git"
    h = git(repo.top, "rev-parse", "--short=12", "HEAD").stdout.strip() or "no-commit"
    dirty = git(repo.top, "status", "--porcelain").stdout.strip()
    return h + ("-dirty" if dirty else "")


def scan(mode: str, path: Path, base: str | None, only: str | None, as_json: bool, cmd_hint: str) -> int:
    repo = discover(path, mode, base)
    def show(c: Coverage, fs: list, secs: float) -> None:
        line = progress_line(c, fs, secs)
        try:
            print(line, file=sys.stderr, flush=True)
        except (OSError, ValueError):       # a closed stderr never stops the scan
            pass

    findings, coverage = run_engines(repo, mode, only, cmd_hint, progress=show)
    findings, old = settle(findings, repo)
    doc = {"revision": revision(repo), "mode": mode if not repo.note else "full", "base": repo.base, "note": repo.note,
           "findings": [{k: v for k, v in asdict(f).items() if k != "group"} for f in findings],
           "groups": group_findings(findings, agent_dirs(repo, repo.files)),
           "coverage": [asdict(c) for c in coverage], "folders": folder_coverage(repo, coverage, mode),
           "suppressions": find_suppressions(repo), "predates_change": old,
           "data_age_days": data_age_days(), "versions": {c.engine: c.version for c in coverage if c.version}}
    doc = mask_doc(doc)
    gaps = [c for c in coverage if c.gap]
    none_ran = not any(c.state == "ran" for c in coverage)
    if as_json:
        print(json.dumps(doc))
    else:
        if repo.note:
            print(f"⚠ {printable(repo.note)}")
        grouped = {n for g in doc["groups"] for n in g["members"]}
        for g in doc["groups"]:
            print(f"{g['count']:>3}× {g['severity']:<8} {printable(g['unit'])}  {printable(g['title'])}  [{g['engine']} {printable(g['rule'])}]"
                  f"  #{', #'.join(map(str, g['members']))}")
        for n, f in enumerate(doc["findings"], 1):
            if n in grouped:
                continue
            place = f"{f['commit'] + ' ' if f.get('commit') else ''}{f['file']}{':' + str(f['line']) if f.get('line') else ''}"
            print(f"{n:>3}. {f['severity']:<8} {printable(place)}  {printable(f['title'])}  [{', '.join(f['sources'])}]")
        for c in doc["coverage"]:
            if c["state"] != "ran" or c.get("reason"):
                print(f"  {'·' if c['state'] == 'n/a' else '⚠'} {c['engine']}: {c['state']}{' — ' + printable(c['reason']) if c.get('reason') else ''}")
        for k, d in doc["data_age_days"].items():
            if d is not None and d > STALE_DAYS:
                print(f"  ⚠ {k} data {d} days old — run scan.py update")
    status = f"{len(findings)} finding(s), {len(gaps)} coverage gap(s)" + (f", {old} older hit(s) predating the change" if old else "")
    if none_ran:
        status += " — no engine ran, nothing was checked"
    bad = bool(findings or gaps or none_ran)
    print(("✗ " if bad else "✓ ") + status, file=sys.stderr if as_json else sys.stdout)
    return 1 if bad else 0


def main(argv: list) -> int:
    script = os.path.abspath(argv[0])
    args = argv[1:]
    t = os.environ.get("SECSCAN_TIMEOUT")
    if t is not None and not (t.isascii() and t.isdigit() and int(t) > 0):
        return fail(f"SECSCAN_TIMEOUT must be a whole number of seconds, not {t!r}")
    if args and args[0] in ("-h", "--help", "help"):
        print(__doc__.strip())
        return 0
    if args and args[0] == "doctor":
        return doctor()
    if args and args[0] == "update":
        return update(script)
    if args and args[0] == "report":
        if len(args) != 3:
            return fail("report needs FINDINGS.json OUTDIR")
        return report(args[1], args[2])
    if args and args[0] == "mirror":
        if len(args) not in (2, 3):
            return fail("mirror needs DEST [PATH]")
        try:
            return mirror(args[1], Path(args[2]) if len(args) == 3 else Path.cwd())
        except CannotRun as e:
            return fail(str(e))
    mode, path, base, only, as_json = "full", None, None, None, False
    i = 0
    while i < len(args):
        a = args[i]
        if a in MODES:
            mode = a
        elif a == "--base" and i + 1 < len(args):
            base, i = args[i + 1], i + 1
        elif a == "--only" and i + 1 < len(args):
            only, i = args[i + 1], i + 1
            if only not in ENGINES:
                return fail(f"unknown engine {only} — one of {', '.join(ENGINES)}")
        elif a == "--json":
            as_json = True
        elif a.startswith("-"):
            return fail(f"unknown option {a} (scan.py -h)")
        elif path is None:
            path = Path(a)
        else:
            return fail("one path at most")
        i += 1
    if base is not None and mode != "changes":
        return fail("--base goes with changes mode")
    if only and only not in MODE_ENGINES[mode]:
        return fail(f"--only {only} is not part of {mode} mode — engines: {', '.join(MODE_ENGINES[mode])}")
    hint = shlex.join(["python3", script, *args])
    try:
        return scan(mode, path or Path.cwd(), base, only, as_json, hint)
    except CannotRun as e:
        return fail(str(e))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
