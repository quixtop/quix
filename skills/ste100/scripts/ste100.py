#!/usr/bin/env python3
# (c) Shrix
# author: shrix
# ste100 — check doc prose against ASD-STE100 Simplified Technical English
# (Issue 9) and render a drawing-sheet HTML view of the result.
#
# Usage:
#   ste100.py scope  [DIR] [--all]                 list the files in scope
#   ste100.py lint   FILE... [--json] [--data F] [--spelling en-US|en-GB] [--strict]
#   ste100.py render [DIR] [--all] [--data F] [--no-history] [--no-hub]
#   ste100.py hub    [DIR]                          rewrite only the docs/arch.html hub
#   ste100.py -h | --help | help
#
# Scope: the arch family (ARCHITECTURE.md, arch.md, docs/arch.md, docs/arch/**,
# per-module arch.md). --all adds the reqs and design families and the root README.
# render reads DIR/docs/arch/ste100.json (created when missing), records today's
# score in its history (one entry per day), and writes DIR/docs/arch/ste100.html
# plus the hub DIR/docs/arch.html, which shows docs/arch/archify.html (archify's
# system picture) and docs/arch/ste100.html in one page. An arch.html that is not
# the hub is never overwritten. Run hub after archify first writes arch/archify.html.
# Exit: 0 ok · 1 --strict and a rule failed · 2 usage or input error.

import atexit
import bisect
import datetime
import html
import json
import os
import re
import sys
from urllib.parse import quote

atexit.register(lambda: sys.stdout.isatty() and print())

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
ISSUE = "ASD-STE100 Issue 9"

# ---------------------------------------------------------------- help + status


def print_help():
    out = []
    with open(os.path.abspath(__file__), encoding="utf-8") as fh:
        for n, line in enumerate(fh):
            if n == 0:
                continue
            if re.match(r"^# \(c\)", line) or re.match(r"^# author:", line):
                continue
            if not line.startswith("#"):
                break
            out.append(re.sub(r"^# ?", "", line.rstrip("\n")))
    print("\n".join(out))


def status(kind, msg):
    glyph = {"ok": "✓", "fail": "✗", "warn": "⚠"}[kind]
    if sys.stdout.isatty():
        colour = {"ok": "32", "fail": "31", "warn": "33"}[kind]
        print("\033[%sm%s %s\033[0m" % (colour, glyph, msg))
    else:
        print("%s %s" % (glyph, msg))


# ---------------------------------------------------------------- word lists

FUNCTION_WORDS = set("""
a an the this these that those some any each every all both either neither no not
and or but nor so yet if then than when while before after until unless because as
since though although whether where which who whom whose what how why
to of in on at by for from with without into onto over under above below between
through during about against among across along around behind beside near off out up
down per via upon within like
i you he she it we they me him her us them my your his its our their mine yours
is are was were be been being am do does did done has have had having
can could will would shall should may might must
also only just more most less least very too much many few other another such same
there here now again still already never always often
one two three four five six seven eight nine ten first second last next
""".split())

IMPERATIVE = set("""
add adjust allow apply approve ask attach avoid back build bump call cancel change
check choose clean clear click close commit compare compile configure confirm connect
copy count create cut define delete deploy describe destroy disable do download drop
edit enable enter examine export extract fetch fill find fix follow force get give go
grant grep hold ignore import include increase decrease install keep kill label leave
let lint list load lock log look make mark measure merge migrate mount move name note
open pass paste pin pipe point print pull push put read rebuild record refer refresh
register reload remove rename render repeat replace report reset resize restart
restore retry return revert review rotate run save scan schedule select send set show
sign skip sort split start stop store submit switch sync tag take tell test think
touch track trigger try turn type unlock unpin update upgrade upload use validate
verify view wait watch wipe write
""".split())

IRREGULAR_PP = set("""
been done gone made taken given written built sent set put kept held found shown known
seen broken chosen driven frozen hidden spoken thrown worn begun drawn fallen forgotten
gotten grown risen shaken stuck struck swept told thought understood won bound brought
bought caught fed felt fought hung laid led left lent lost meant met paid said sold shot
shut slid spent split spread stood taught wound cut hit let quit upset rebuilt rewritten
overridden undone withdrawn run read
""".split())

NON_VERB_ING = set("""
thing things string strings nothing something anything everything during king ring
spring wing sing bring swing sling sting ceiling morning evening pending remaining
existing following corresponding outstanding interesting misleading warning warnings
setting settings heading headings building buildings
""".split())

# -ing words that work as technical nouns in software docs (rule 3.5 allows these)
ING_TECH_NOUNS = set("""
logging routing caching testing scheduling streaming rendering pricing hosting billing
mapping tracing linting polling pooling hashing indexing parsing batching sharding
versioning encoding padding spacing timing tooling onboarding monitoring networking
debugging profiling branding licensing staging hashing throttling queueing queuing
""".split()) | NON_VERB_ING

# Periods that never end a sentence; "no." only before a number, "etc." only before a capital.
ABBREV = set("e.g i.e vs cf viz approx fig mr mrs dr st al inc ltd e g i e".split())
NUMBER_ABBREV = {"no"}
CAPITAL_ABBREV = {"etc"}

UNITS = set("""
ms s sec secs min mins h hr hrs d kb mb gb tb kib mib gib b px pt em rem % ° vw vh
mhz ghz hz kbps mbps gbps k m x
nanosecond nanoseconds microsecond microseconds millisecond milliseconds second seconds
minute minutes hour hours day days week weeks month months year years
bit bits byte bytes kilobyte kilobytes megabyte megabytes gigabyte gigabytes terabyte terabytes
pixel pixels percent degree degrees meter meters metre metres
""".split())

LATIN = [
    (r"\be\.g\.?(?=\W|$)", "for example"),
    (r"\bi\.e\.?(?=\W|$)", "that is"),
    (r"\betc\.?(?=\W|$)", "and so on"),
    (r"\bvs\.?(?=\W|$)", "compared with"),
    (r"\bviz\.(?=\W|$)", "namely"),
    (r"\bcf\.(?=\W|$)", "refer to"),
    (r"\bet al\.(?=\W|$)", "and others"),
]

BRIT_STEMS = (
    "organ|optim|initial|normal|serial|priorit|recogn|real|summar|custom|minim|maxim|"
    "final|author|util|standard|categor|synchron|visual|emphas|apolog|character|memor|"
    "special|sanit|token|parameter|capital|central|general|local|modern|personal"
)
BRIT_RE = re.compile(r"\b(?:%s)is(?:e|ed|es|ing|ation|ations)\b" % BRIT_STEMS, re.I)
BRIT_WORDS = {
    "behaviour": "behavior", "behaviours": "behaviors", "colour": "color",
    "colours": "colors", "favour": "favor", "honour": "honor", "labour": "labor",
    "neighbour": "neighbor", "centre": "center", "centres": "centers", "metre": "meter",
    "analyse": "analyze", "analysed": "analyzed", "catalogue": "catalog",
    "cancelled": "canceled", "cancelling": "canceling", "modelled": "modeled",
    "modelling": "modeling", "labelled": "labeled", "labelling": "labeling",
    "travelled": "traveled", "programme": "program", "grey": "gray",
}

# ---------------------------------------------------------------- scope

SKIP_DIRS = set(
    ".git node_modules vendor dist build .next .archify target __pycache__ .venv venv "
    ".cache coverage .wrangler .turbo".split()
)


def _walk_md(root):
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x not in SKIP_DIRS and not x.startswith("."))
        for f in sorted(files):
            if f.lower().endswith(".md"):
                yield os.path.relpath(os.path.join(d, f), root)


def family_of(rel):
    p = rel.replace(os.sep, "/")
    low = p.lower()
    base = os.path.basename(low)
    if base in ("architecture.md", "arch.md") or low.startswith("docs/arch/"):
        return "arch"
    if (low in ("docs/reqs.md", "requirements.md") or low.startswith("docs/reqs/")
            or low.startswith("docs/requirements/") or re.match(r"reqs-.*\.md$", base)):
        return "reqs"
    if low == "design.md" or low.startswith("docs/design/"):
        return "design"
    if low == "readme.md":
        return "readme"
    return None


def scope(root, everything=False):
    wanted = {"arch"} if not everything else {"arch", "reqs", "design", "readme"}
    out = []
    for rel in _walk_md(root):
        fam = family_of(rel)
        if fam in wanted:
            out.append((rel, fam))
    order = {"arch": 0, "reqs": 1, "design": 2, "readme": 3}
    return sorted(out, key=lambda t: (order[t[1]], t[0]))


# ---------------------------------------------------------------- markdown → blocks

LIST_RE = re.compile(r"^(\s*)([-*+]|\d+[.)])\s+(.*)$")
ITEM_COL_RE = re.compile(r"^(\s*(?:>\s*)*)([-*+]|\d+[.)])(\s+)")   # its end is the item's content column
LEAD_RE = re.compile(r"^\s*(?:>\s*)*")                              # indent plus any blockquote markers
RAW_OPEN_RE = re.compile(r"^<(script|pre|style|textarea)(?=[\s>]|$)", re.I)  # content is never prose
LINKDEF_RE = re.compile(r"""^\[(?!\^)[^\]]+\]:\s*(?:<[^<>\n]*>|\S+)(?:\s+(?:"[^"]*"|'[^']*'|\([^)]*\)))?\s*$""")


def blocks_of(text):
    """Split markdown into prose blocks: (kind, start_line, text).
    kind: para | item | heading. Code, tables, comments, frontmatter, raw HTML
    blocks and link reference definitions are skipped."""
    if text.startswith("﻿"):
        text = text[1:]                  # a UTF-8 byte order mark is not text
    lines = text.split("\n")
    out, buf, kind, start = [], [], None, 0
    i, n = 0, len(lines)

    def flush():
        nonlocal buf, kind
        if buf and kind:
            out.append((kind, start, "\n".join(buf)))
        buf, kind = [], None

    items = []   # open list items, innermost last: (content column, quoted); code sits 4 deeper

    def close_items(line):
        """A block-starting line ends each item it is indented less than, and every
        quoted item when the line is not quoted."""
        exp = line.expandtabs(4)
        lead = LEAD_RE.match(exp).end()
        if not exp[lead:].strip():
            lead = float("inf")          # a bare ">": closes no quoted item, but a deeper plain one
        ind = len(exp) - len(exp.lstrip())
        quoted = exp[ind:ind + 1] == ">"
        # a quoted item's column counts its ">" markers; a plain item's does not
        while items and ((items[-1][1] and not quoted) or (lead if items[-1][1] else ind) < items[-1][0]):
            items.pop()

    if n and lines[0].strip() == "---":
        j = 1
        while j < n and lines[j].strip() != "---":
            j += 1
        i = j + 1 if j < n else 0
    fence = None
    raw_end, raw_indent = None, 0   # an open <script>/<pre>/<style>/<textarea> block: its close tag, indent
    in_comment = False
    in_table = False
    while i < n:
        line = lines[i]
        s = line.strip()
        if in_comment:
            if "-->" in s:
                in_comment = False
            i += 1
            continue
        if raw_end and s and len(line.expandtabs(4)) - len(line.expandtabs(4).lstrip()) < raw_indent:
            raw_end = None                 # the list item that held the block has ended
        if raw_end:
            if raw_end in s.lower():
                raw_end = None
            i += 1
            continue
        if fence:
            if re.match(r"^%s{%d,}\s*$" % (re.escape(fence[0]), len(fence)), s):
                fence = None
            i += 1
            continue
        m = re.match(r"^(```+|~~~+)", s)
        if m:
            flush()
            close_items(line)
            fence = m.group(1)
            i += 1
            continue
        if kind is None and s:
            close_items(line)
        indent = len(line.expandtabs(4)) - len(line.expandtabs(4).lstrip())
        if kind is None and s and indent >= (items[-1][0] if items else 0) + 4:
            i += 1        # an indented code block (also inside a list item): never prose
            continue
        rm = RAW_OPEN_RE.match(s)
        if rm:
            flush()
            end_tag = "</%s>" % rm.group(1).lower()
            raw_end, raw_indent = (None if end_tag in s.lower() else end_tag), (items[-1][0] if items else 0)
            i += 1
            continue
        # HTML comments, found OUTSIDE inline code: `<!--` in backticks is text
        masked_line = re.sub(r"`[^`]*`", lambda mm: " " * len(mm.group(0)), s)
        if "<!--" in masked_line:
            while True:
                a = masked_line.find("<!--")
                if a < 0:
                    break
                b = masked_line.find("-->", a + 4)
                if b < 0:                       # opens a comment that runs past this line
                    s, masked_line, in_comment = s[:a], masked_line[:a], True
                    break
                pad = " " * (b + 3 - a)
                s = s[:a] + pad + s[b + 3:]
                masked_line = masked_line[:a] + pad + masked_line[b + 3:]
            s = s.strip()
            if not s:
                flush()
                i += 1
                continue
        if in_table:
            if s and "|" in s:
                i += 1
                continue
            in_table = False
        if re.match(r"^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$", s):
            if kind == "para" and buf:
                buf.pop()
            flush()
            in_table = True
            i += 1
            continue
        if re.match(r"^(=+|-+)$", s) and kind == "para" and buf:
            title = buf.pop()
            hline = start + len(buf)
            flush()
            out.append(("heading", hline, title))
            i += 1
            continue
        if not s or s.startswith("|") or re.match(r"^(-{3,}|\*{3,}|_{3,})$", s):
            flush()
            i += 1
            continue
        if s.startswith("<") and re.match(r"^</?[a-zA-Z][^>]*>$", s):
            flush()
            i += 1
            continue
        if s.startswith("#"):
            flush()
            close_items(line)
            out.append(("heading", i + 1, s.lstrip("#").strip()))
            i += 1
            continue
        s = re.sub(r"^(>\s*)+", "", s)
        if kind is None and LINKDEF_RE.match(s):
            i += 1        # a link reference definition ([id]: url "title") is a URL, not prose
            continue
        lm = LIST_RE.match(s)
        if lm:
            flush()
            close_items(line)
            mcol = ITEM_COL_RE.match(line.expandtabs(4))
            items.append((len(mcol.group(0)) if mcol else 0, line.lstrip().startswith(">")))
            kind, start, buf = "item", i + 1, [lm.group(3)]
            i += 1
            continue
        if kind is None:
            kind, start = "para", i + 1
        buf.append(s)
        i += 1
    flush()
    return out


# ---------------------------------------------------------------- sentences

# Private-use characters: a placeholder for code / URLs that no doc text can contain
# (mask strips them from the input first) and that no \b or word pattern can match.
PH = "%d"
PH_RE = re.compile("(\\d+)")
TOKEN = "  "  # what a placeholder becomes before the word checks run


def mask(text):
    """Replace inline code and URLs with placeholders; strip links and emphasis."""
    store = []

    def keep(m):
        store.append(m.group(0))
        return PH % (len(store) - 1)

    def link_text(m):
        url = m.group(2)
        hidden = sum(store[int(k)].count("\n") for k in PH_RE.findall(url))   # in a code span
        return m.group(1) + "\n" * (url.count("\n") + hidden)

    t = re.sub("[-]", "", text)
    t = re.sub(r"`[^`]+`", keep, t)
    # links and tags keep the newlines they remove, so line numbers stay right. Linear:
    # no bracket in the link text; the URL is <…>, or allows \-escapes and one
    # level of (…) (wiki "Foo_(bar)").
    t = re.sub(r"!?\[([^\[\]]*)\]\((<[^<>\n]*>|(?:[^()\\]|\\[\s\S])*"
               r"(?:\((?:[^()\\]|\\[\s\S])*\)(?:[^()\\]|\\[\s\S])*)*)\)", link_text, t)
    t = re.sub(r"https?://[^\s)>\]]+", keep, t)
    t = re.sub(r"</?[A-Za-z][A-Za-z0-9-]*(?:\s[^<>\n]*)?/?>",          # HTML tags only, never `< 50 ms … >`
               lambda m: " " + "\n" * m.group(0).count("\n"), t)
    t = re.sub(r"(\*\*|__)", "", t)
    t = re.sub(r"(?<![\w*])\*(?=\S)([^*\n]+?)(?<=\S)\*(?![\w*])", r"\1", t)
    t = re.sub(r"(?<!\w)_(?=\S)([^_\n]+?)(?<=\S)_(?!\w)", r"\1", t)     # _emphasis_, never snake_case
    return t, store


def unmask(t, store):
    return PH_RE.sub(lambda m: store[int(m.group(1))], t)


def shown_text(text):
    """Text as lint prints it (links, emphasis, tags stripped), white space collapsed."""
    return " ".join(unmask(*mask(text)).split())


END_RE = re.compile(r"[.!?][\"'”’)]*(?=\s+|$)")
NEXT_RE = re.compile(r"\s*(\S?)")
ABBREV_CHARS = frozenset("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ.")


def split_sentences(t):
    """Yield (start, end) spans of sentences in masked text, in linear time."""
    spans, start = [], 0
    for m in END_RE.finditer(t):
        end = m.end()  # past any closing quote or bracket, so it stays with its sentence
        nxt = NEXT_RE.match(t, end).group(1)
        if t[m.start()] == ".":
            j = m.start()
            while j > start and t[j - 1] in ABBREV_CHARS:
                j -= 1
            word = t[j:m.start()].lower().rstrip(".")
            if j == start or not t[j - 1].isalnum():   # "1st." is an ordinal, not "st."
                if (word in ABBREV or (word in NUMBER_ABBREV and (nxt.isdigit() or nxt == PH[0]))
                        or (word in CAPITAL_ABBREV and nxt and not nxt.isupper())):
                    continue
        if "a" <= nxt <= "z":  # a lowercase start continues the sentence;
            continue           # anything else (capital, emoji, code, digit) starts one
        spans.append((start, end))
        start = end
    if t[start:].strip():
        spans.append((start, len(t)))
    return [(a, b) for a, b in spans if t[a:b].strip()]


def _parens_as_words(s):
    """Replace each balanced (…) group, nested too, with one word W; an unmatched bracket stays."""
    out, opens = [], []
    for ch in s:
        if ch == "(":
            opens.append(len(out))
        elif ch == ")" and opens:
            del out[opens.pop():]
            out.append(" W ")
            continue
        out.append(ch)
    return "".join(out)


def _quotes_as_words(s):
    """Replace each quoted text with one word W: a " or “ opens it, the next " or ” closes it.
    An opening mark with no closing mark after it stays. One pass, so linear."""
    out, start = [], -1
    for ch in s:
        if start >= 0 and ch in "\"”":
            del out[start:]
            out.append(" W ")
            start = -1
            continue
        if start < 0 and ch in "\"“":
            start = len(out)
        out.append(ch)
    return "".join(out)


def _inside_wrappers(s):
    """The text inside the brackets or quotation marks when the whole sentence sits in
    them, nested and mixed too: "((Run it.))", "(Run it)." and '"(Run it.)"' give "Run it".
    Double quotes pair as word_count pairs them, and also as nested pairs: “…” and a
    straight "…" around curly ones. '…' and ‘…’ count only when each ' or ’ inside is an
    apostrophe (it's). Before any layer is peeled, a stray closer at the sentence edge,
    left by an aside an earlier sentence opened, is skipped: a ) with no ( for it, or a ’
    when no other ' ‘ ’ (apostrophes aside) is in the sentence. So '"Run it.")' gives
    "Run it" too. Any other sentence comes back as is.
    Linear: the pairs are found in one pass, so each layer is checked in O(1)."""
    t = s.strip()
    n = len(t)
    parens, curly, opens, copens, closed = {}, {}, [], [], set()   # closed: each ) that has its (
    closers = [0] * (n + 1)   # closers[i]: " and ” in t[:i]
    straight = [0] * (n + 1)  # straight[i]: " in t[:i]
    loose = [0] * (n + 1)     # loose[i]: ' ‘ ’ in t[:i] that are not apostrophes
    stop = [-1] * n           # stop[i]: the last j <= i where t[j] is not an end mark or a closing quote
    for i, ch in enumerate(t):
        if ch == "(":
            opens.append(i)
        elif ch == ")" and opens:
            parens[opens.pop()] = i
            closed.add(i)
        elif ch == "“":
            copens.append(i)
        elif ch == "”" and copens:
            curly[copens.pop()] = i
        apostrophe = ch in "'’" and 0 < i < n - 1 and t[i - 1].isalnum() and t[i + 1].isalnum()
        closers[i + 1] = closers[i] + (ch in "\"”")
        straight[i + 1] = straight[i] + (ch == '"')
        loose[i + 1] = loose[i] + (ch in "'‘’" and not apostrophe)
        if ch not in ".!?\"'”’":
            stop[i] = i
        elif i:
            stop[i] = stop[i - 1]
    a, b, peeled = 0, n - 1, False   # the sentence is t[a..b], both ends included
    while True:
        while a < b and (t[b] in ".!?" or t[b].isspace()):
            b -= 1
        while a < b and t[a].isspace():
            a += 1
        if a >= b:
            break
        o, c = t[a], t[b]
        if o in "\"“" and c in "\"”" and (closers[b] == closers[a + 1] or curly.get(a) == b
                                          or o == c == '"' and straight[b] == straight[a + 1]):
            pass
        elif o in "'‘" and c in "'’" and loose[b] == loose[a + 1]:
            pass
        else:   # brackets, with any end mark or closing quote after them
            e = max(a, stop[b])
            if o == "(" and parens.get(a) == e:
                b = e
            elif peeled:
                break
            elif (c == ")" and b not in closed) or (c == "’" and loose[b] == loose[a]):   # a stray closer
                b -= 1
                continue
            elif o == ")" or (o == "’" and loose[b + 1] == loose[a + 1]):
                a += 1
                continue
            else:
                break
        a, b, peeled = a + 1, b - 1, True
    return t[a:b + 1] if peeled else s


def word_count(s):
    """Count words the STE way: parenthesised text, quoted text, code, numbers with
    units, and hyphenated words each count as one word (rules 8.5–8.7). A sentence
    wholly in brackets or quotation marks is not an aside: its own words count."""
    t = _quotes_as_words(_parens_as_words(_inside_wrappers(s)))
    t = PH_RE.sub(" W ", t)
    toks = [x for x in re.split(r"\s+", t) if re.search(r"[A-Za-z0-9]", x)]
    n, i = 0, 0
    while i < len(toks):
        n += 1
        if re.match(r"^[\d.,]+$", toks[i]) and i + 1 < len(toks) and toks[i + 1].lower().strip(".,;:") in UNITS:
            i += 1
        i += 1
    return n


def longest(text):
    """Word count of the longest sentence in text: the number a sentence limit applies to."""
    m, _ = mask(text)
    return max((word_count(m[a:b]) for a, b in split_sentences(m)), default=0)


def first_words(s, k=3):
    t = PH_RE.sub(TOKEN, s)
    return [w.lower() for w in re.findall(r"[A-Za-z']+", t)[:k]]


AUX_WORDS = set("is are was were has have had will can could must may might should would does do".split())
# Command words that also work as NOUN MODIFIERS in docs ("Build artifacts…", "Update
# notes…"). Only these can open a noun phrase; a verb like verify/check/confirm/make
# followed by "settings are…" is a command with a clause object.
NOUN_MODIFIERS = set("""
build update log test deploy release cache record report review schedule sync tag track
view watch upload download export import label list lock mark name note print push pull
save scan search set sign sort store switch trigger copy load move pin drop fix run
""".split())
DETERMINERS = set("the a an this these that those each every all your its their our any no both it them".split())


SUBORDINATORS = set("when if before after until unless while because once so then".split())


def _subject_follows(w):
    """True when the words after a command-like first word read as its predicate:
    an auxiliary, or a noun followed by a present-tense verb, before any determiner.
    Only a word that works as a noun modifier can start such a noun phrase.
    None when the first five words do not decide it."""
    if not w or w[0] not in NOUN_MODIFIERS:      # no words (code or a number first): a command
        return False
    for k in range(1, min(len(w), 5)):
        x = w[k]
        if x in DETERMINERS:
            return False                 # "Build THE bundle" — an object follows: a command
        if x in SUBORDINATORS:
            return False                 # "Deploy only WHEN tests pass" — a condition, not a subject
        if x in AUX_WORDS:
            return True
        prev = w[k - 1]
        if k >= 2 and x in IMPERATIVE and prev not in FUNCTION_WORDS and prev not in IMPERATIVE:
            return True                  # "… test jobs RUN …"
    return None


def classify(s):
    """procedural when the sentence (or the clause after a leading condition) starts
    with a command verb; else descriptive."""
    body = re.sub(r"^\s*(?:WARNING|CAUTION|DANGER|NOTICE|NOTE)\s*:\s*", "", s, flags=re.I)
    body = body.lstrip("⚠️👉✋ ").strip()
    clause = body
    w = first_words(clause, 6)
    if not w:
        return "descriptive"
    if w[0] in ("if", "when", "before", "after", "while", "until", "unless", "once") and "," in body:
        clause = body.split(",", 1)[1]
        w = first_words(clause, 6)
        if not w:
            return "descriptive"
    if w[0] in IMPERATIVE:
        # "Build artifacts ARE stored" / "Build and test jobs RUN in CI": the first word
        # is a noun with its own verb after it, not a command. Only the words before
        # the first comma count: "Run tests, check output, and stop." is a command list.
        parts = clause.split(",", 2)
        subject = _subject_follows(first_words(parts[0], 6))
        if subject is None and len(parts) == 3:
            # "Log entries, once written, ARE kept": an aside between two commas, then
            # the subject's verb. A command list has no auxiliary there ("do", "have" start commands).
            after = first_words(parts[2], 1)
            subject = bool(after) and after[0] in AUX_WORDS and after[0] not in ("do", "have")
        return "descriptive" if subject else "procedural"
    if w[0] in ("never", "always", "then", "next", "first", "now") and len(w) > 1 and w[1] in IMPERATIVE:
        return "procedural"
    if w[:2] == ["do", "not"] and len(w) > 2:
        return "procedural"
    return "descriptive"


# ---------------------------------------------------------------- word list + data

def whole_word(body):
    """body as a whole word; unlike \\b, also when it starts or ends with a symbol (C++, .NET)."""
    return r"(?<!\w)(?:%s)(?!\w)" % body


def load_words():
    path = os.path.join(SKILL, "references", "words.tsv")
    rows = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 3:
                continue
            word, pos, use = parts[0].strip(), parts[1].strip(), parts[2].strip()
            flags = 0 if len(parts) > 3 and parts[3].strip() == "cs" else re.I
            if pos == "v" and " " not in word:
                stem = word[:-1] if word.endswith("e") else word
                forms = [word, word + "s", word + "es", stem + "ed", word + "d", stem + "ing"]
                if word.endswith("y"):
                    forms += [word[:-1] + "ies", word[:-1] + "ied"]
                pat = whole_word("|".join(sorted(set(map(re.escape, forms)), key=len, reverse=True)))
            elif pos == "n" and " " not in word:
                pat = whole_word("%ss?" % re.escape(word))
            else:
                pat = whole_word(re.escape(word).replace(r"\ ", r"\s+"))
            rows.append({"word": word, "pos": pos, "use": use, "re": re.compile(pat, flags)})
    return rows


def blank_data(project):
    return {
        "version": 1,
        "meta": {"project": project, "owner": "", "spelling": "en-US"},
        "dictionary": [],
        "anatomy": [],
        "history": [],
    }


def read_data(path, project):
    if not path or not os.path.exists(path):
        return blank_data(project)
    with open(path, encoding="utf-8-sig") as fh:          # -sig: a byte order mark is not JSON
        data = json.load(fh)
    check_data(data, path)
    base = blank_data(project)
    for k, v in base.items():
        data.setdefault(k, v)
    data["meta"] = dict(base["meta"], **data["meta"]) if "meta" in data else base["meta"]
    return data


def check_data(data, path):
    """Validate the shape of docs/arch/ste100.json at the boundary; raise ValueError."""
    def need(ok, what):
        if not ok:
            raise ValueError("%s: %s" % (path, what))

    def is_str(x):
        return isinstance(x, str)

    def is_num(x):                       # a 0–100 score; NaN and inf fail the range
        return isinstance(x, (int, float)) and not isinstance(x, bool) and 0 <= x <= 100

    need(isinstance(data, dict), "the top level must be an object")
    meta = data.get("meta", {})
    need(isinstance(meta, dict), "meta must be an object")
    for k in ("project", "owner", "spelling"):
        need(is_str(meta.get(k, "")), "meta.%s must be a string" % k)
    need(meta.get("spelling", "en-US") in ("en-US", "en-GB"), "meta.spelling must be en-US or en-GB")
    cap = meta.get("findings_per_rule", 0)
    need(isinstance(cap, int) and not isinstance(cap, bool) and cap >= 0,
         "meta.findings_per_rule must be a whole number, 0 or more (0 lists every finding)")
    for key in ("dictionary", "anatomy", "history"):
        need(isinstance(data.get(key, []), list), "%s must be a list" % key)
    for i, r in enumerate(data.get("dictionary", [])):
        need(isinstance(r, dict) and is_str(r.get("word")) and r["word"].strip(),
             "dictionary[%d] needs a word (a string)" % i)
        for k in ("pos", "meaning", "example"):
            need(is_str(r.get(k, "")), "dictionary[%d].%s must be a string" % (i, k))
        need(isinstance(r.get("not", []), list) and all(is_str(x) and x.strip() for x in r.get("not", [])),
             "dictionary[%d].not must be a list of words" % i)
    for i, r in enumerate(data.get("anatomy", [])):
        need(isinstance(r, dict) and is_str(r.get("ste")) and r["ste"].strip(), "anatomy[%d] needs ste (a string)" % i)
        for k in ("file", "original"):
            need(is_str(r.get(k, "")), "anatomy[%d].%s must be a string" % (i, k))
        need(r.get("type", "descriptive") in ("procedural", "descriptive"),
             "anatomy[%d].type must be procedural or descriptive" % i)
        need(isinstance(r.get("line", 0), (int, str)), "anatomy[%d].line must be a number" % i)
        notes = r.get("notes", [])
        need(isinstance(notes, list) and all(isinstance(x, dict) and is_str(x.get("text", "")) and is_str(x.get("note", ""))
                                             and x.get("tone", "ok") in ("ok", "fix", "term", "info") for x in notes),
             "anatomy[%d].notes must be objects with text, note and tone (ok, fix, term or info)" % i)
    for i, h in enumerate(data.get("history", [])):
        need(isinstance(h, dict) and is_str(h.get("date")) and is_num(h.get("score")),
             "history[%d] needs a date (string) and a score (a finite number)" % i)


# ---------------------------------------------------------------- checks

AUX = r"(?:am|is|are|was|were|be|been|being)"
ADV = r"(?:\w+ly\s+|not\s+|already\s+|never\s+|just\s+|also\s+|now\s+)?"


def _is_pp(word):
    w = word.lower()
    if w in IRREGULAR_PP:
        return True
    return w.endswith("ed") and not w.endswith("eed") and w not in ("red", "bed", "shed", "hundred", "embed", "need")


def check_sentence(s, stype, words, dict_rows, spelling):
    """Return findings for one masked sentence: list of (rule, severity, span, msg, use)."""
    f = []
    t = PH_RE.sub(TOKEN, s)
    n = word_count(s)
    limit = 20 if stype == "procedural" else 25
    if n > limit:
        f.append(("5.1" if stype == "procedural" else "6.3", "fail", "",
                  "%d words in a %s sentence (limit %d)" % (n, stype, limit),
                  "split it into shorter sentences or a vertical list"))

    starts, ends = [], []    # the spans already reported: disjoint, in order

    def take(m):
        a, b = m.span()
        k = bisect.bisect_left(starts, b)     # the spans that start before this one ends
        if k and ends[k - 1] > a:             # the last of them runs into it: an overlap
            return False
        starts.insert(k, a)
        ends.insert(k, b)
        return True

    for m in re.finditer(r"\b(must|can|could|should|will|would|may|might|shall|is to|are to)\s+(?:not\s+)?be\s+(\w+)\b", t, re.I):
        if _is_pp(m.group(2)) and take(m):
            f.append(("3.4", "fail", m.group(0), "complex verb construction with a passive", "use the active voice: who does it"))
    for m in re.finditer(r"\b(has|have|had|having)\s+%s(\w+)\b" % ADV, t, re.I):
        if _is_pp(m.group(2)) and take(m):
            f.append(("3.4", "fail", m.group(0), "perfect tense is not approved", "use the simple past or present"))
    for m in re.finditer(r"\b(?:am|is|are|was|were)\s+being\s+(\w+)\b", t, re.I):
        if _is_pp(m.group(1)) and take(m):
            f.append(("3.2", "fail", m.group(0), "progressive passive is not approved", "use the active voice in the simple present"))
    for m in re.finditer(r"\b%s\s+%s(\w{3,}ing)\b" % (AUX, ADV), t, re.I):
        if m.group(1).lower() not in NON_VERB_ING and take(m):
            f.append(("3.2", "fail", m.group(0), "progressive (-ing) form is not approved", "use the simple present"))
    for m in re.finditer(r"\b%s\s+%s(\w+)\b" % (AUX, ADV), t, re.I):
        if _is_pp(m.group(1)) and take(m):
            sev = "fail" if stype == "procedural" else "check"
            msg = ("passive voice in an instruction" if stype == "procedural"
                   else "passive voice: allowed only when the agent is unknown")
            f.append(("3.6", sev, m.group(0), msg, "name who or what does the action"))
    for m in re.finditer(r"\b(by|before|after|when|while|for|of|in|on|without|from|about|through|upon)\s+(\w{3,}ing)\b", t, re.I):
        if m.group(2).lower() not in ING_TECH_NOUNS and take(m):
            f.append(("3.5", "check", m.group(0), "-ing form used as a verb", "use a clause: 'before you start' not 'before starting'"))
    fw = first_words(s, 1)
    if fw and fw[0].endswith("ing") and fw[0] not in ING_TECH_NOUNS and len(fw[0]) > 4:
        f.append(("3.5", "check", re.findall(r"[A-Za-z']+", t)[0], "sentence starts with an -ing form", "start with the subject or a command"))

    for m in re.finditer(r"\b\w+n['’]t\b|\b(?:it|that|there|what|who|he|she|they|we|you|i|let|here)['’](?:s|re|ve|ll|d|m)\b", t, re.I):
        f.append(("4.2", "fail", m.group(0), "contraction", "write the words in full"))
    if ";" in t:
        f.append(("8.1", "fail", ";", "semicolon is not approved", "use two sentences"))
    for pat, use in LATIN:
        for m in re.finditer(pat, t, re.I):
            f.append(("GR-6", "check", m.group(0), "Latin abbreviation", use))

    for row in words:
        for m in row["re"].finditer(t):
            if row["pos"] == "phrasal":
                f.append(("9.3", "fail", m.group(0), "phrasal verb", row["use"]))
            else:
                f.append(("1.1", "fail", m.group(0), "word not approved in STE", row["use"]))
    for row in dict_rows:
        for syn in row.get("not") or []:
            for m in re.finditer(whole_word(re.escape(syn)), t, re.I):
                f.append(("1.11", "fail", m.group(0), "different name for the same item",
                          str(row.get("word", "")).upper()))
    if spelling != "en-GB":
        for m in BRIT_RE.finditer(t):
            us = re.sub(r"is(e|ed|es|ing|ation|ations)$", r"iz\1", m.group(0), flags=re.I)
            f.append(("1.14", "check", m.group(0), "British spelling", us))
        for m in re.finditer(r"\b(%s)\b" % "|".join(BRIT_WORDS), t, re.I):
            f.append(("1.14", "check", m.group(0), "British spelling", BRIT_WORDS[m.group(0).lower()]))

    cl = noun_cluster(t)
    if cl and len(cl.split()) > 3:
        f.append(("2.1", "check", cl, "possible noun cluster of %d words" % len(cl.split()),
                  "use a preposition to break it up, or define it as a technical name"))

    if stype == "procedural":
        k = instructions(t)
        if k > 1 and not re.search(r"at the same time|simultaneous", t, re.I):
            f.append(("5.2", "fail", "", "%d instructions in one sentence" % k, "write one instruction per sentence"))
    head = re.match(r"^\s*(?:⚠️\s*)?(WARNING|CAUTION|DANGER|NOTICE)\s*:\s*(\S+)", s, re.I)
    if head:
        w = re.sub(r"\W", "", head.group(2)).lower()
        if w not in IMPERATIVE and w not in ("if", "when", "before", "after", "do", "never", "make"):
            f.append(("7.2", "check", head.group(0), "safety instruction does not start with a command or condition",
                      "start with the command, then give the risk"))
    note = re.match(r"^\s*NOTE\s*:\s*(\w+)", s, re.I)
    if note and note.group(1).lower() in IMPERATIVE:
        f.append(("5.5", "check", note.group(0), "a note gives an instruction", "put the instruction in a step"))
    if t.count(",") >= 3 and n >= 15:
        f.append(("4.3", "check", "", "long list inside a sentence", "use a vertical list"))
    return f, n


def noun_cluster(t):
    """The longest run of content words that is not all capitalised (a proper name)."""
    toks = re.findall(r"[A-Za-z][A-Za-z-]*|[^\sA-Za-z]", t)
    best, best_len = (0, 0), 0
    run_start, lower = 0, 0      # where the current run starts · its words not capitalised
    for i, tok in enumerate(toks):
        low = tok.lower()
        is_content = (
            re.match(r"^[A-Za-z][A-Za-z-]*$", tok) is not None
            and low not in FUNCTION_WORDS
            and low not in IMPERATIVE
            and not low.endswith("ly")
            and not (low.endswith("s") and low[:-1] in IMPERATIVE)
            and not (low.endswith("es") and low[:-2] in IMPERATIVE)
            and not _is_pp(low)
            and not (low.endswith("ing") and low not in ING_TECH_NOUNS)
        )
        if is_content:
            if not tok[:1].isupper():
                lower += 1
            if i + 1 - run_start > best_len and lower:
                best, best_len = (run_start, i + 1), i + 1 - run_start
        else:
            run_start, lower = i + 1, 0
    return " ".join(toks[best[0]:best[1]])


def instructions(t):
    count = 0
    body = re.sub(r"^\s*(if|when|before|after|while|until|unless|once)\b[^,]*,", "", t, flags=re.I)
    for clause in re.split(r",\s*(?:and\s+|then\s+)?|\s+and\s+(?:then\s+)?|\s+then\s+", body):
        w = re.findall(r"[A-Za-z']+", clause)
        if w and w[0].lower() in IMPERATIVE:
            count += 1
    return count


# ---------------------------------------------------------------- lint

def lint_files(paths, root, data, fams=None):
    words = load_words()
    dict_rows = [r for r in data.get("dictionary", []) if isinstance(r, dict)]
    spelling = (data.get("meta") or {}).get("spelling", "en-US")
    findings, files, sentences, paragraphs = [], [], [], []
    for rel in paths:
        full = os.path.join(root, rel)
        with open(full, encoding="utf-8", errors="replace") as fh:
            text = fh.read()
        fs = {"path": rel, "family": (fams or {}).get(rel) or family_of(rel) or "file",
              "sentences": 0, "fails": 0, "checks": 0}
        for kind, line, raw in blocks_of(text):
            if kind == "heading":
                continue
            masked, store = mask(raw)
            spans = split_sentences(masked)
            if kind == "para":
                paragraphs.append({"file": rel, "line": line, "count": len(spans),
                                   "text": unmask(masked[spans[0][0]:spans[0][1]], store).strip() if spans else ""})
            pos, nl = 0, 0           # newlines in masked[:pos], counting those a code span hides
            for a, b in spans:
                seg = masked[a:b]
                first = a + len(seg) - len(seg.lstrip())     # the sentence's first character
                chunk = masked[pos:first]
                nl += chunk.count("\n") + sum(store[int(k)].count("\n") for k in PH_RE.findall(chunk))
                pos = first
                s = seg.strip()
                if not re.search(r"[A-Za-z]{2}", PH_RE.sub("", s)):
                    continue
                stype = classify(s)
                sline = line + nl
                found, n = check_sentence(s, stype, words, dict_rows, spelling)
                shown = unmask(s, store)
                rec = {"file": rel, "line": sline, "type": stype, "words": n, "text": shown,
                       "instructions": instructions(PH_RE.sub(TOKEN, s)) if stype == "procedural" else 0,
                       "cluster": len(noun_cluster(PH_RE.sub(TOKEN, s)).split()),
                       "fails": 0, "checks": 0}
                for rule, sev, span, msg, use in found:
                    findings.append({"file": rel, "line": sline, "rule": rule, "severity": sev,
                                     "span": unmask(span, store), "message": msg, "use": use,
                                     "sentence": shown, "type": stype})
                    rec["fails" if sev == "fail" else "checks"] += 1
                sentences.append(rec)
                fs["sentences"] += 1
                fs["fails"] += rec["fails"]
                fs["checks"] += rec["checks"]
        for p in paragraphs:
            if p["file"] == rel and p["count"] > 6:
                findings.append({"file": rel, "line": p["line"], "rule": "6.6", "severity": "fail",
                                 "span": "", "message": "%d sentences in one paragraph (limit 6)" % p["count"],
                                 "use": "split the paragraph by topic", "sentence": p["text"], "type": "descriptive"})
                fs["fails"] += 1
        files.append(fs)
    return summarise(files, sentences, paragraphs, findings, words)


def _p90(vals):
    if not vals:
        return 0
    v = sorted(vals)
    return v[min(len(v) - 1, int(round(0.9 * (len(v) - 1))))]


def summarise(files, sentences, paragraphs, findings, words):
    def stat(kind, limit):
        vals = [s["words"] for s in sentences if s["type"] == kind]
        worst = max((s for s in sentences if s["type"] == kind), key=lambda s: s["words"], default=None)
        return {"count": len(vals), "max": max(vals) if vals else 0, "p90": _p90(vals), "limit": limit,
                "over": sum(1 for x in vals if x > limit),
                "worst": {k: worst[k] for k in ("file", "line", "text", "words")} if worst else None}

    def example(pred):
        for s in sentences:
            if pred(s):
                return {"text": s["text"], "file": s["file"], "line": s["line"]}
        return None

    def form(rule, needle):
        hits = [x for x in findings if x["rule"] == rule and needle in x["message"]]
        ex = {"text": hits[0]["sentence"], "file": hits[0]["file"], "line": hits[0]["line"], "span": hits[0]["span"]} if hits else None
        return {"count": len(hits), "example": ex}

    fut = [s for s in sentences if re.search(r"\bwill\s+(?!be\b)\w+", s["text"], re.I)]
    forms = {
        "imperative": {"count": sum(1 for s in sentences if s["type"] == "procedural"),
                       "example": example(lambda s: s["type"] == "procedural")},
        "future": {"count": len(fut), "example": ({"text": fut[0]["text"], "file": fut[0]["file"], "line": fut[0]["line"]} if fut else None)},
        "progressive": form("3.2", "progressive"),
        "perfect": form("3.4", "perfect"),
        "passive": form("3.6", "passive"),
        "modal_be": form("3.4", "complex"),
        "ing": form("3.5", "-ing"),
    }
    wl = {}
    for x in findings:
        if x["rule"] in ("1.1", "9.3"):
            key = x["span"].lower()
            e = wl.setdefault(key, {"word": key, "use": x["use"], "rule": x["rule"], "count": 0,
                                    "example": {"text": x["sentence"], "file": x["file"], "line": x["line"]}})
            e["count"] += 1
    practice = {}
    for x in findings:
        practice[x["rule"]] = practice.get(x["rule"], 0) + 1
    total = len(sentences)
    clean = sum(1 for s in sentences if s["fails"] == 0)
    fails = sum(1 for x in findings if x["severity"] == "fail")
    checks = len(findings) - fails
    return {
        "issue": ISSUE,
        "files": files,
        "sentences": total,
        "procedural": stat("procedural", 20),
        "descriptive": stat("descriptive", 25),
        "paragraph": {"max": max((p["count"] for p in paragraphs), default=0), "p90": _p90([p["count"] for p in paragraphs]),
                      "limit": 6, "over": sum(1 for p in paragraphs if p["count"] > 6)},
        "cluster": {"max": max((s["cluster"] for s in sentences), default=0), "p90": _p90([s["cluster"] for s in sentences]),
                    "limit": 3, "over": sum(1 for s in sentences if s["cluster"] > 3)},
        "instructions": {"max": max((s["instructions"] for s in sentences), default=0), "limit": 1,
                         "over": sum(1 for s in sentences if s["instructions"] > 1)},
        "forms": forms,
        "words": sorted(wl.values(), key=lambda e: (-e["count"], e["word"])),
        "rules": practice,
        "score": round(100.0 * clean / total) if total else 100,
        "fails": fails,
        "checks": checks,
        "findings": findings,
    }


# ---------------------------------------------------------------- render: helpers

def esc(x):
    return html.escape("" if x is None else str(x), quote=True)


def mark_spans(text, marks):
    """Escape text and wrap the first case-insensitive hit of each mark span."""
    spans = []
    low = text.lower()
    for mk in marks:
        sp = (mk.get("span") or "").strip()
        if not sp:
            continue
        i = low.find(sp.lower())
        while i != -1 and any(i < b and a < i + len(sp) for a, b, _ in spans):
            i = low.find(sp.lower(), i + 1)
        if i != -1:
            spans.append((i, i + len(sp), mk))
    spans.sort(key=lambda t: t[0])
    out, pos = [], 0
    for a, b, mk in spans:
        out.append(esc(text[pos:a]))
        tone = mk.get("tone", "bad")
        tip = mk.get("tip", "")
        attr = ' tabindex="0" data-tip="%s"' % esc(tip) if tip else ""
        out.append('<mark class="%s"%s>%s</mark>' % (esc(tone), attr, esc(text[a:b])))
        pos = b
    out.append(esc(text[pos:]))
    return "".join(out)


def code_spans(text):
    """Escape text, rendering `code` as <code>."""
    parts = re.split(r"(`[^`]+`)", text)
    return "".join('<code>%s</code>' % esc(p[1:-1]) if p.startswith("`") and p.endswith("`") and len(p) > 1
                   else esc(p) for p in parts)


def excerpt(text, span="", width=90):
    """Shorten text to about width characters, kept centred on span."""
    if len(text) <= width:
        return text
    i = text.lower().find(span.lower()) if span else -1
    if i < 0:
        return text[:width - 1].rstrip() + "…"
    start = max(0, i - (width - len(span)) // 2)
    end = min(len(text), start + width)
    start = max(0, end - width)
    return ("…" if start > 0 else "") + text[start:end].strip() + ("…" if end < len(text) else "")


def tone_of(score):
    return "ok" if score >= 90 else ("warn" if score >= 70 else "bad")


def panel(sid, letter, title, tag, body, cls=""):
    pid = "s%d-%s" % (sid, letter.lower())
    return ('<section class="panel %s" aria-labelledby="%s">'
            '<header><span class="letter">%s</span><h3 id="%s">%s</h3><span class="tag">%s</span></header>'
            '<div class="body">%s</div></section>') % (esc(cls), pid, esc(letter), pid, esc(title), esc(tag), body)


# ---------------------------------------------------------------- render: panels

def r_tree(d):
    items = []
    for br in d.get("branches", []):
        lis = []
        for it in br.get("items", []):
            st = it.get("status", "none")
            # sub is plain text (escaped); counts carries numbers the renderer colours itself
            sub = esc(it.get("sub", ""))
            if it.get("counts"):
                c = it["counts"]
                sub = ('<span class="num">%d</span> sentences · <span class="num %s">%d fail</span> · '
                       '<span class="num warn">%d check</span>') % (
                    int(c["sentences"]), "ok" if not c["fails"] else "bad", int(c["fails"]), int(c["checks"]))
            lis.append('<li class="st-%s"><span class="k">%s</span><span class="lbl">%s</span>%s</li>' % (
                esc(st), esc(it.get("k", "")), code_spans(it.get("label", "")),
                '<span class="sub">%s</span>' % sub if sub else ""))
        items.append('<div class="branch"><div class="bhead">%s</div><ul>%s</ul></div>' % (esc(br.get("title", "")), "".join(lis)))
    root = d.get("root", {})
    return ('<div class="tree"><div class="root"><b>%s</b><span>%s</span></div><div class="branches">%s</div></div>'
            '<p class="foot">%s</p>') % (esc(root.get("title", "")), esc(root.get("sub", "")), "".join(items), esc(d.get("note", "")))


def ruler(words, limit):
    axis = max(limit + 10, words + 2)
    pct = 100.0 * words / axis
    lim = 100.0 * limit / axis
    tone = "ok" if words <= limit else "bad"
    return ('<div class="wruler" role="img" aria-label="%d words, limit %d">'
            '<div class="wtrack"><div class="wfill %s" style="width:%.1f%%"></div>'
            '<div class="wlimit" style="left:%.1f%%"></div></div>'
            '<div class="wlabel"><span class="num %s">longest sentence: %d words</span><span class="num">limit %d</span></div></div>') % (
        words, limit, tone, pct, lim, tone, words, limit)


def r_anatomy(d):
    out = []
    if d.get("original"):
        o = d["original"]
        out.append('<p class="orig-label">%s</p>' % esc(o.get("label", "")))
        if o.get("text"):
            out.append('<p class="orig">%s</p>' % mark_spans(o["text"], o.get("marks", [])))
    for i, ex in enumerate(d.get("items", []), 1):
        spans = ex.get("spans", [])
        notes = "".join('<li class="t-%s"><b>%d</b> %s</li>' % (esc(sp.get("tone", "ok")), k, esc(sp.get("note", "")))
                        for k, sp in enumerate(spans, 1))
        ste = ex.get("ste", "")
        marks = [{"span": sp.get("text", ""), "tone": "ann t-" + sp.get("tone", "ok"), "tip": "%d · %s" % (k, sp.get("note", ""))}
                 for k, sp in enumerate(spans, 1)]
        orig = ""
        if ex.get("original"):
            orig = '<p class="orig">%s</p>' % mark_spans(ex["original"], ex.get("orig_marks", []))
        loc = '<span class="path">%s</span>' % esc(ex["loc"]) if ex.get("loc") else ""
        stale = '<span class="stale">source changed — refresh this example</span>' if ex.get("stale") else ""
        out.append('<div class="anat"><p class="ahead"><b>%d</b> %s %s %s</p>%s'
                   '<p class="ste">%s</p>%s<ol class="notes">%s</ol></div>' % (
                       i, esc(ex.get("heading", "")), loc, stale, orig, mark_spans(ste, marks),
                       ruler(int(ex.get("words", longest(ste))), int(ex.get("limit", 25))), notes))
    if d.get("foot"):
        out.append('<p class="foot">%s</p>' % esc(d["foot"]))
    return "".join(out)


def r_forms(d):
    counted = any(r.get("count") is not None for r in d.get("rows", []))
    rows = []
    for r in d.get("rows", []):
        st = r.get("status", "ok")
        label = "Approved" if st == "ok" else "Not approved"
        cnt = r.get("count")
        found = '<td data-label="Found" class="num">%s</td>' % ("–" if cnt is None else esc(cnt)) if counted else ""
        rows.append('<tr><td data-label="Form">%s</td><td data-label="Example" class="mono">%s</td>'
                    '%s<td data-label="Status" class="st-%s">%s %s</td></tr>' % (
                        esc(r.get("form", "")), mark_spans(r.get("example", ""), r.get("marks", [])),
                        found, esc(st), "✓" if st == "ok" else "✕", label))
    head = "<th>Found</th>" if counted else ""
    return ('<div class="tw"><table class="grid forms"><thead><tr><th>Form</th><th>Example</th>%s<th>Status</th></tr></thead>'
            '<tbody>%s</tbody></table></div><p class="foot">%s</p>') % (head, "".join(rows), esc(d.get("note", "")))


def r_dict(d):
    rows = []
    for r in d.get("rows", []):
        st = r.get("status", "ok")
        label = {"ok": "Approved", "term": "Technical name", "bad": "Not approved"}.get(st, st)
        word = r.get("word", "")
        word = word.upper() if st in ("ok", "term") else word.lower()
        rows.append('<tr><td data-label="Word" class="mono w-%s">%s <span class="pos">(%s)</span></td>'
                    '<td data-label="Status" class="st-%s">%s %s</td>'
                    '<td data-label="Meaning or alternative" class="%s">%s</td>'
                    '<td data-label="Approved example" class="good">%s</td><td data-label="Not approved" class="badtxt">%s</td>'
                    '<td data-label="Found" class="num">%s</td></tr>' % (
                        esc(st), esc(word), esc(r.get("pos", "")), esc(st),
                        "✕" if st == "bad" else "✓", esc(label),
                        "alt" if st == "bad" else "", esc(r.get("meaning", "")),
                        esc(r.get("good", "")), esc(r.get("bad", "") or "–"),
                        "–" if r.get("count") is None else esc(r["count"])))
    return ('<div class="tw"><table class="grid dict"><thead><tr><th>Word (part of speech)</th><th>Status</th>'
            '<th>Meaning or alternative</th><th>Approved example</th><th>Not approved</th><th>Found</th></tr></thead>'
            '<tbody>%s</tbody></table></div><p class="foot">%s</p>') % ("".join(rows), esc(d.get("note", "")))


def r_limits(d):
    bars = []
    for b in d.get("bars", []):
        axis = max(float(b.get("axis", 1)), 1.0)
        lim = float(b["limit"])
        val = b.get("value")
        p90 = b.get("p90")
        fill = ""
        if val is not None:
            tone = "ok" if val <= lim else "bad"
            fill = '<div class="bfill %s" style="width:%.1f%%"></div>' % (tone, min(100.0, 100.0 * val / axis))
        elif b.get("fill_limit"):
            fill = '<div class="bfill lim" style="width:%.1f%%"></div>' % min(100.0, 100.0 * lim / axis)
        p90m = '<div class="bp90" style="left:%.1f%%" title="p90 %s"></div>' % (min(100.0, 100.0 * p90 / axis), esc(p90)) if p90 is not None else ""
        ticks = "".join('<span style="left:%.1f%%">%s</span>' % (100.0 * t / axis, t) for t in sorted({0, int(lim), int(axis)}))
        val_txt = ""
        if val is not None:
            val_txt = '<span class="num %s">max %s</span>' % ("ok" if val <= lim else "bad", esc(val))
            if p90 is not None:
                val_txt += ' <span class="num muted">p90 %s</span>' % esc(p90)
        bars.append('<div class="bar"><div class="bhd"><span>%s</span><span>%s <span class="num lim">limit %s %s</span></span></div>'
                    '<div class="btrack">%s%s<div class="blimit" style="left:%.1f%%"></div></div><div class="bticks">%s</div></div>' % (
                        esc(b.get("label", "")), val_txt, esc(b["limit"]), esc(b.get("unit", "")), fill, p90m,
                        100.0 * lim / axis, ticks))
    pr = []
    for p in d.get("practices", []):
        st = p.get("status", "none")
        cnt = p.get("count")
        pr.append('<li class="st-%s"><span>%s</span>%s</li>' % (esc(st), esc(p.get("text", "")),
                                                             '<span class="num">%s</span>' % esc(cnt) if cnt is not None else ""))
    return '<div class="bars">%s</div><ul class="practices">%s</ul>' % ("".join(bars), "".join(pr))


def r_trend(d):
    pts = d.get("points", [])
    score = d.get("score")
    head = ""
    if score is not None:
        delta = ""
        if len(pts) > 1:
            dv = pts[-1]["score"] - pts[-2]["score"]
            delta = '<span class="num %s">%+d since %s</span>' % ("ok" if dv >= 0 else "bad", dv, esc(pts[-2]["date"]))
        head = '<div class="big"><span class="num %s">%d%%</span><span>sentences that pass every rule</span>%s</div>' % (
            tone_of(score), score, delta)
    if len(pts) < 2:
        return head + '<p class="foot">The trend line starts after the second run.</p>'
    w, h, pad = 300.0, 110.0, 14.0
    xs = [pad + i * (w - 2 * pad) / (len(pts) - 1) for i in range(len(pts))]
    ys = [h - pad - (p["score"] / 100.0) * (h - 2 * pad) for p in pts]
    poly = " ".join("%.1f,%.1f" % (x, y) for x, y in zip(xs, ys))
    dots = "".join('<circle cx="%.1f" cy="%.1f" r="3"><title>%s: %d%%</title></circle>' % (x, y, esc(p["date"]), p["score"])
                   for x, y, p in zip(xs, ys, pts))
    grid = "".join('<line x1="%.0f" x2="%.0f" y1="%.1f" y2="%.1f"/><text x="2" y="%.1f">%d</text>' % (
        pad, w - pad, h - pad - v / 100.0 * (h - 2 * pad), h - pad - v / 100.0 * (h - 2 * pad),
        h - pad - v / 100.0 * (h - 2 * pad) + 3, v) for v in (0, 50, 100))
    labels = '<text x="%.1f" y="%.1f" class="xl">%s</text><text x="%.1f" y="%.1f" class="xl end">%s</text>' % (
        xs[0], h - 1, esc(pts[0]["date"]), xs[-1], h - 1, esc(pts[-1]["date"]))
    return head + ('<svg class="trend" viewBox="0 0 300 110" role="img" aria-label="Score per run">'
                   '<g class="g">%s</g><polyline points="%s"/>%s%s</svg>') % (grid, poly, dots, labels)


def r_timeline(d):
    pts = "".join('<li><b class="num">%s</b><span>%s</span></li>' % (esc(p.get("year", "")), esc(p.get("text", "")))
                  for p in d.get("points", []))
    return '<ol class="timeline">%s</ol><p class="foot">%s</p>' % (pts, esc(d.get("note", "")))


def r_title(d):
    cells = "".join('<div class="cell"><span class="clabel">%s</span><span class="cval %s">%s</span></div>' % (
        esc(c.get("label", "")), "t-" + esc(c["tone"]) if c.get("tone") else "", esc(c.get("value", "")))
        for c in d.get("cells", []))
    return ('<section class="titleblock" aria-label="Title block"><div class="cell wide"><span class="clabel">Title</span>'
            '<span class="ttl">%s</span></div>%s</section>') % (esc(d.get("title", "")), cells)


def render_sheet(sheet, num):
    p = sheet["panels"]
    trend = r_trend(p["F"]) if p["F"].get("kind") == "trend" else r_timeline(p["F"])
    ruler_top = "".join("<span>%d</span>" % i for i in range(1, 9))
    side = "".join("<span>%s</span>" % c for c in "ABCD")
    return ('<article class="sheet" id="sheet-%d" aria-label="%s">'
            '<div class="rul top" aria-hidden="true">%s</div><div class="rul left" aria-hidden="true">%s</div>'
            '<div class="inner">%s%s%s%s%s<div class="stack">%s%s</div></div>'
            '<div class="rul right" aria-hidden="true">%s</div><div class="rul bottom" aria-hidden="true">%s</div>'
            '</article>') % (
        num, esc(sheet["title"]["title"]), ruler_top, side,
        panel(num, "A", p["A"]["title"], p["A"]["tag"], r_tree(p["A"]), "pa"),
        panel(num, "B", p["B"]["title"], p["B"]["tag"], r_anatomy(p["B"]), "pb"),
        panel(num, "C", p["C"]["title"], p["C"]["tag"], r_forms(p["C"]), "pc"),
        panel(num, "D", p["D"]["title"], p["D"]["tag"], r_dict(p["D"]), "pd"),
        panel(num, "E", p["E"]["title"], p["E"]["tag"], r_limits(p["E"]), "pe"),
        panel(num, "F", p["F"]["title"], p["F"]["tag"], trend, "pf"),
        r_title(sheet["title"]), side, ruler_top)


def rule_key(r):
    return ([int(n) if n.isdigit() else 99 for n in re.split(r"[.-]", r.replace("GR", "99"))], r)


def r_findings(res, out_dir, root, cap=0):
    """The findings table. cap > 0 lists at most cap findings per rule, fails before
    checks, shown in document order; the counts above the table always cover every finding."""
    shown, hidden, keep = {}, {}, set()
    for sev in ("fail", "check"):
        for i, x in enumerate(res["findings"]):
            if x["severity"] == sev and not (cap and shown.get(x["rule"], 0) >= cap):
                shown[x["rule"]] = shown.get(x["rule"], 0) + 1
                keep.add(i)
    rows = []
    for i, x in enumerate(res["findings"]):
        if i not in keep:
            hidden[x["rule"]] = hidden.get(x["rule"], 0) + 1
            continue
        href = quote(os.path.relpath(os.path.join(root, x["file"]), out_dir).replace(os.sep, "/"))
        tip = "rule %s · %s" % (x["rule"], x["message"])
        rows.append('<tr data-sev="%s" data-rule="%s"><td data-label="Where" class="path"><a href="%s">%s:%d</a></td>'
                    '<td data-label="Rule" class="rule">%s</td><td data-label="Level"><span class="chip %s">%s</span></td>'
                    '<td data-label="Sentence">%s<div class="msg">%s</div></td><td data-label="Use instead" class="good">%s</td></tr>' % (
                        esc(x["severity"]), esc(x["rule"]), esc(href), esc(x["file"]), x["line"], esc(x["rule"]),
                        "bad" if x["severity"] == "fail" else "warn", "fail" if x["severity"] == "fail" else "check",
                        mark_spans(x["sentence"], [{"span": x["span"], "tone": "bad" if x["severity"] == "fail" else "warn", "tip": tip}]),
                        esc(x["message"]), esc(x["use"])))
    rules = sorted({x["rule"] for x in res["findings"]}, key=rule_key)
    totals = {}
    for x in res["findings"]:
        totals[x["rule"]] = totals.get(x["rule"], 0) + 1
    opts = "".join('<option value="%s">%s (%d%s)</option>' % (
        esc(r), esc(r), totals[r], ", %d listed" % shown.get(r, 0) if r in hidden else "") for r in rules)
    note = ""
    if hidden:
        note = ('<p class="capnote">Listing up to <span class="num">%d</span> findings per rule, fails first: '
                '<span class="num">%d</span> more are not listed (%s). '
                'Run <code>ste100.py lint &lt;files&gt;</code> for every finding.</p>') % (
            cap, sum(hidden.values()), esc(", ".join("%s: %d" % (r, hidden[r]) for r in sorted(hidden, key=rule_key))))
    return ('<section class="findings" id="findings" aria-label="All findings"><h2>All findings '
            '<span class="num">%d</span> <span class="chip bad">%d fail</span> <span class="chip warn">%d check</span></h2>'
            '<div class="filters" role="group" aria-label="Filter findings">'
            '<button type="button" data-f="all" aria-pressed="true">All</button>'
            '<button type="button" data-f="fail" aria-pressed="false">Fail</button>'
            '<button type="button" data-f="check" aria-pressed="false">Check</button>'
            '<label>Rule <select id="rulef"><option value="">all</option>%s</select></label></div>%s'
            '<div class="tw"><table class="grid flist"><thead><tr><th>Where</th><th>Rule</th><th>Level</th><th>Sentence</th>'
            '<th>Use instead</th></tr></thead><tbody>%s</tbody></table></div></section>') % (
        len(res["findings"]), res["fails"], res["checks"], opts, note, "".join(rows))


def page(title, sheets_html, findings_html, nav):
    with open(os.path.join(SKILL, "assets", "sheet.css"), encoding="utf-8") as fh:
        css = fh.read()
    with open(os.path.join(SKILL, "assets", "sheet.js"), encoding="utf-8") as fh:
        js = fh.read()
    legend = "".join('<span class="lg %s">%s</span>' % (c, esc(t)) for c, t in (
        ("ok", "approved / within limit"), ("bad", "not approved / over limit"), ("warn", "check"),
        ("term", "technical name"), ("metric", "measured value"), ("rule", "rule"), ("path", "file")))
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta name="generator" content="ste100 (shrix)"><title>%s</title><style>%s</style></head><body>'
            '<header class="top"><div class="tt"><h1>%s</h1><p>%s</p></div><nav aria-label="Sheets">%s'
            '<button type="button" id="theme" aria-label="Switch colour theme">Theme: auto</button></nav></header>'
            '<div class="legend" aria-label="Colour key">%s</div><main>%s%s</main><script>%s</script></body></html>') % (
        esc(title), css, esc(title), esc(ISSUE + " · generated by /ste100 — do not edit by hand"), nav, legend,
        sheets_html, findings_html, js)


# ---------------------------------------------------------------- render: sheet 1 model

def project_model(res, data, root, today):
    meta = data["meta"]
    fam_title = {"arch": "Architecture", "reqs": "Requirements", "design": "Design", "readme": "README", "file": "Files"}
    branches = {}
    for f in res["files"]:
        st = "ok" if f["fails"] == 0 else "bad"
        branches.setdefault(f["family"], []).append({"k": "", "label": "`%s`" % f["path"], "status": st,
                                                     "counts": {k: f[k] for k in ("sentences", "fails", "checks")}})
    A = {"title": "Document structure", "tag": "docs in scope",
         "root": {"title": meta.get("project") or os.path.basename(os.path.abspath(root)), "sub": "STE100 check of the written docs"},
         "branches": [{"title": fam_title.get(k, k), "items": v} for k, v in branches.items()],
         "note": "Code blocks, tables and backticked names are technical names and are not checked."}

    words = load_words()
    dict_rows = [r for r in data.get("dictionary", []) if isinstance(r, dict)]
    items = []
    for ex in data.get("anatomy", [])[:3]:
        if not isinstance(ex, dict) or not ex.get("ste"):
            continue
        orig = ex.get("original", "")
        stale = False
        if orig and ex.get("file"):
            path = os.path.join(root, ex["file"])
            try:
                with open(path, encoding="utf-8", errors="replace") as fh:
                    raw = fh.read()
                # current when found verbatim in the doc, or as lint prints it
                want = shown_text(orig)
                stale = (re.sub(r"\s+", " ", orig).strip() not in re.sub(r"\s+", " ", raw)
                         and not (want and any(want in shown_text(t) for k, _, t in blocks_of(raw) if k != "heading")))
            except OSError:
                stale = True
        om = []
        if orig:
            mo, _ = mask(orig)
            fo, _ = check_sentence(mo, ex.get("type", "descriptive"), words, dict_rows, meta.get("spelling", "en-US"))
            om = [{"span": s, "tone": "bad" if sev == "fail" else "warn", "tip": "rule %s · %s → %s" % (r, m, u)}
                  for r, sev, s, m, u in fo if s]
        stype = ex.get("type", "descriptive")
        items.append({"heading": "%s sentence" % stype.capitalize(), "loc": "%s:%s" % (ex.get("file", ""), ex.get("line", "")) if ex.get("file") else "",
                      "original": orig, "orig_marks": om, "ste": ex["ste"], "words": longest(ex["ste"]),
                      "limit": 20 if stype == "procedural" else 25, "spans": ex.get("notes", []), "stale": stale})
    if not items:
        worst = sorted({(x["file"], x["line"], x["sentence"], x["type"]) for x in res["findings"] if x["severity"] == "fail"},
                       key=lambda t: (-len(t[2]), t[0], t[1]))[:2]
        for fpath, line, sent, stype in worst:
            marks = [{"span": x["span"], "tone": "bad", "tip": "rule %s · %s → %s" % (x["rule"], x["message"], x["use"])}
                     for x in res["findings"] if x["file"] == fpath and x["line"] == line and x["sentence"] == sent and x["span"]]
            items.append({"heading": "Needs a rewrite", "loc": "%s:%d" % (fpath, line), "original": sent, "orig_marks": marks,
                          "ste": "", "words": longest(sent), "limit": 20 if stype == "procedural" else 25,
                          "spans": []})
    label = "Original text, not STE: words to replace are in red. STE rewrite below each."
    B = {"title": "Anatomy of STE sentences", "tag": "from these docs",
         "original": {"label": label, "text": "", "marks": []} if items else None,
         "items": items,
         "foot": "Run /ste100 to add worked rewrites for the worst sentences." if not data.get("anatomy") else "Procedural limit 20 words · descriptive limit 25 words · max 6 sentences per paragraph."}

    fm = res["forms"]

    def ex_text(e):
        return excerpt(e["text"], e.get("span", ""), 80) if e else ""

    def ex_marks(e):
        return [{"span": e.get("span", ""), "tone": "bad", "tip": "%s:%s" % (e.get("file"), e.get("line"))}] if e and e.get("span") else []

    C = {"title": "Verb forms", "tag": "measured in these docs", "rows": [
        {"form": "Command (imperative)", "example": ex_text(fm["imperative"]["example"]) or "Run the tests.", "status": "ok", "count": fm["imperative"]["count"]},
        {"form": "Simple future", "example": ex_text(fm["future"]["example"]) or "The worker will retry once.", "status": "ok", "count": fm["future"]["count"]},
        {"form": "Simple present / past", "example": "The worker sends the reply.", "status": "ok"},
        {"form": "Progressive (-ing)", "example": ex_text(fm["progressive"]["example"]) or "The worker is sending the reply.", "status": "bad", "count": fm["progressive"]["count"], "marks": ex_marks(fm["progressive"]["example"])},
        {"form": "Perfect", "example": ex_text(fm["perfect"]["example"]) or "The worker has sent the reply.", "status": "bad", "count": fm["perfect"]["count"], "marks": ex_marks(fm["perfect"]["example"])},
        {"form": "Passive", "example": ex_text(fm["passive"]["example"]) or "The reply is sent by the worker.", "status": "bad", "count": fm["passive"]["count"], "marks": ex_marks(fm["passive"]["example"])},
        {"form": "Modal + be + participle", "example": ex_text(fm["modal_be"]["example"]) or "The cache must be cleared.", "status": "bad", "count": fm["modal_be"]["count"], "marks": ex_marks(fm["modal_be"]["example"])},
        {"form": "-ing as a verb", "example": ex_text(fm["ing"]["example"]) or "Before deploying, run the tests.", "status": "bad", "count": fm["ing"]["count"], "marks": ex_marks(fm["ing"]["example"])},
    ], "note": "Passive voice is a check (not a fail) in descriptive text: STE allows it when the agent is unknown."}

    drows = []
    for r in dict_rows:
        drows.append({"word": r.get("word", ""), "pos": r.get("pos", "n"), "status": "term",
                      "meaning": r.get("meaning", ""), "good": r.get("example", ""),
                      "bad": ", ".join(r.get("not") or []), "count": None})
    for w in res["words"][:12]:
        drows.append({"word": w["word"], "pos": "phrasal v" if w["rule"] == "9.3" else "", "status": "bad",
                      "meaning": w["use"].upper(), "good": "", "bad": excerpt(w["example"]["text"], w["word"], 90), "count": w["count"]})
    D = {"title": "Dictionary entries", "tag": "project terms + words to replace", "rows": drows,
         "note": "Technical names (UPPERCASE, purple) come from docs/arch/ste100.json: one name, one meaning. "
                 "Red rows are words found in the docs, with the approved word to use."}

    pr, de, pa, cl, ins = res["procedural"], res["descriptive"], res["paragraph"], res["cluster"], res["instructions"]
    rules = res["rules"]

    def pstat(n):
        return "ok" if n == 0 else "bad"
    E = {"title": "Writing rule limits", "tag": "measured max · p90", "bars": [
        {"label": "Procedural sentence", "value": pr["max"] if pr["count"] else None, "p90": pr["p90"] if pr["count"] else None, "limit": 20, "axis": max(30, pr["max"] + 2), "unit": "words"},
        {"label": "Descriptive sentence", "value": de["max"] if de["count"] else None, "p90": de["p90"] if de["count"] else None, "limit": 25, "axis": max(30, de["max"] + 2), "unit": "words"},
        {"label": "Descriptive paragraph", "value": pa["max"], "p90": pa["p90"], "limit": 6, "axis": max(10, pa["max"] + 1), "unit": "sentences"},
        {"label": "Noun cluster", "value": cl["max"], "p90": cl["p90"], "limit": 3, "axis": max(5, cl["max"] + 1), "unit": "words"},
        {"label": "Instructions in each sentence", "value": ins["max"], "limit": 1, "axis": max(3, ins["max"] + 1), "unit": ""},
    ], "practices": [
        {"text": "No semicolons (8.1)", "count": rules.get("8.1", 0), "status": pstat(rules.get("8.1", 0))},
        {"text": "No contractions (4.2)", "count": rules.get("4.2", 0), "status": pstat(rules.get("4.2", 0))},
        {"text": "No phrasal verbs (9.3)", "count": rules.get("9.3", 0), "status": pstat(rules.get("9.3", 0))},
        {"text": "Same name for the same item (1.11)", "count": rules.get("1.11", 0), "status": pstat(rules.get("1.11", 0))},
        {"text": "No Latin abbreviations (GR-6)", "count": rules.get("GR-6", 0), "status": "ok" if not rules.get("GR-6") else "warn"},
        {"text": "American spelling (1.14)", "count": rules.get("1.14", 0), "status": "ok" if not rules.get("1.14") else "warn"},
        {"text": "Vertical lists for long lists (4.3)", "count": rules.get("4.3", 0), "status": "ok" if not rules.get("4.3") else "warn"},
    ]}

    hist = [h for h in data.get("history", []) if isinstance(h, dict) and "score" in h]
    F = {"kind": "trend", "title": "Compliance trend", "tag": "score per run", "points": hist[-12:], "score": res["score"]}

    T = {"title": "%s: Simplified Technical English" % (meta.get("project") or os.path.basename(os.path.abspath(root))), "cells": [
        {"label": "Specification", "value": ISSUE},
        {"label": "Owner", "value": meta.get("owner") or "–"},
        {"label": "Scope", "value": "%d files · %d sentences" % (len(res["files"]), res["sentences"])},
        {"label": "Score", "value": "%d%% pass" % res["score"], "tone": tone_of(res["score"])},
        {"label": "Findings", "value": "%d fail · %d check" % (res["fails"], res["checks"]), "tone": "bad" if res["fails"] else "ok"},
        {"label": "Date", "value": today},
        {"label": "Source", "value": "asd-ste100.org"},
        {"label": "Sheet", "value": "1 of 2"},
    ]}
    return {"title": T, "panels": {"A": A, "B": B, "C": C, "D": D, "E": E, "F": F}}


HUB_MARK = '<meta name="generator" content="ste100 hub">'


# The layout under docs/: the hub arch.html shows the two pages in docs/arch/.
PIC = "arch/archify.html"   # archify's system picture (archify writes it)
SHEET = "arch/ste100.html"  # this skill's sheet
DATA = "arch/ste100.json"   # this skill's source: dictionary, rewrites, history


def hub_html(project, has_pic):
    with open(os.path.join(SKILL, "assets", "hub.html"), encoding="utf-8") as fh:
        t = fh.read()
    pic = ('<iframe class="f-pic" src="%s" title="System picture (archify)"></iframe>' % PIC if has_pic else
           '<p class="f-pic missing">No %s yet: run archify to draw the system picture.</p>' % PIC)
    values = {"__TITLE__": esc("%s — architecture" % project), "__PROJECT__": esc(project),
              "__PIC_OFF__": "" if has_pic else "off", "__BOTH_OFF__": "" if has_pic else "off",
              "__DEFAULT__": "pic" if has_pic else "ste", "__PIC_FRAME__": pic,
              "__HAS_PIC__": "true" if has_pic else "false", "__PIC_SRC__": PIC, "__SHEET_SRC__": SHEET}
    # one pass, so a value that happens to contain a placeholder is never expanded again
    return re.sub(r"__[A-Z_]+__", lambda m: values.get(m.group(0), m.group(0)), t)


def hub_plan(docs, project):
    """Return (path, text, note): the hub to write, or (None, None, why not)."""
    hub = os.path.join(docs, "arch.html")
    if os.path.exists(hub):
        with open(hub, encoding="utf-8", errors="replace") as fh:
            if HUB_MARK not in fh.read(4096):
                return None, None, "arch.html left alone: it is not the ste100 hub (move an archify page to docs/%s)" % PIC
    return hub, hub_html(project, os.path.exists(os.path.join(docs, PIC))), ""


def write_all(writes):
    """Write every file to a .tmp first, then move them all into place; never leave a .tmp."""
    tmps = []
    try:
        for path, text in writes:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmps.append(path + ".tmp")
            with open(tmps[-1], "w", encoding="utf-8") as fh:
                fh.write(text)
        for (path, _), tmp in zip(writes, tmps):
            os.replace(tmp, path)
    finally:
        for tmp in tmps:
            if os.path.exists(tmp):
                os.remove(tmp)


def load_overview():
    with open(os.path.join(SKILL, "references", "overview.json"), encoding="utf-8") as fh:
        return json.load(fh)


# ---------------------------------------------------------------- commands

def cmd_scope(args):
    root = args.get("dir") or "."
    for rel, fam in scope(root, args.get("all")):
        print("%s\t%s" % (fam, rel))
    return 0


def cmd_lint(args):
    root = os.getcwd()
    data = read_data(args.get("data"), os.path.basename(root))
    if args.get("spelling"):
        data["meta"]["spelling"] = args["spelling"]
    res = lint_files(args["files"], root, data)
    if args.get("json"):
        print(json.dumps(res, indent=1, ensure_ascii=False))
    else:
        for x in res["findings"]:
            print("%s:%d\t%s\t%s\t%s\t→ %s" % (x["file"], x["line"], x["severity"], x["rule"],
                                              x["message"] + (" [%s]" % x["span"] if x["span"] else ""), x["use"]))
        print("score %d%% · %d sentences · %d fail · %d check" % (res["score"], res["sentences"], res["fails"], res["checks"]))
    return 1 if args.get("strict") and res["fails"] else 0


def cmd_render(args):
    root = os.path.abspath(args.get("dir") or ".")
    docs = os.path.join(root, "docs")
    data_path = args.get("data") or os.path.join(docs, DATA)
    out = os.path.join(docs, SHEET)
    files = scope(root, args.get("all"))
    if not files:
        status("warn", "no docs in scope under %s — nothing rendered (try --all)" % root)
        return 0
    data = read_data(data_path, os.path.basename(root))
    res = lint_files([f for f, _ in files], root, data, dict(files))
    today = datetime.date.today().isoformat()
    if not args.get("no_history"):
        entry = {"date": today, "score": res["score"], "sentences": res["sentences"], "fails": res["fails"], "checks": res["checks"]}
        data["history"] = [h for h in data["history"] if h["date"] != today] + [entry]
        data["history"] = data["history"][-60:]
    s1 = project_model(res, data, root, today)
    s2 = load_overview()
    nav = ('<a href="#sheet-1">Sheet 1 · project</a><a href="#sheet-2">Sheet 2 · STE overview</a>'
           '<a href="#findings">Findings</a>')
    doc = page(s1["title"]["title"], render_sheet(s1, 1) + render_sheet(s2, 2), r_findings(res, os.path.dirname(out), root, data["meta"].get("findings_per_rule", 0)), nav)
    writes = [(out, doc)]
    note = ""
    if not args.get("no_hub"):
        hub, text, note = hub_plan(docs, data["meta"].get("project") or os.path.basename(root))
        if hub:
            writes.append((hub, text))
    writes.append((data_path, json.dumps(data, indent=2, ensure_ascii=False) + "\n"))
    write_all(writes)
    rel = os.path.relpath(out)
    shown = os.path.relpath(os.path.join(docs, "arch.html")) if len(writes) == 3 else rel
    kind = "ok" if res["fails"] == 0 and not note else "warn"
    status(kind, "%s written — score %d%%, %d fail, %d check in %d files%s — open %s" % (
        rel, res["score"], res["fails"], res["checks"], len(files), (" · " + note) if note else "", shown))
    return 0


def cmd_hub(args):
    root = os.path.abspath(args.get("dir") or ".")
    docs = os.path.join(root, "docs")
    if not os.path.exists(os.path.join(docs, SHEET)):
        status("warn", "no docs/%s yet — run render first; hub not written" % SHEET)
        return 0
    data = read_data(os.path.join(docs, DATA), os.path.basename(root))
    hub, text, note = hub_plan(docs, data["meta"].get("project") or os.path.basename(root))
    if not hub:
        status("warn", note)
        return 0
    write_all([(hub, text)])
    has_pic = os.path.exists(os.path.join(docs, PIC))
    status("ok", "%s written — %s" % (os.path.relpath(hub), "shows %s and %s" % (PIC, SHEET) if has_pic
                                      else "no %s yet, so it shows the STE sheet only" % PIC))
    return 0


def parse(argv):
    if not argv or argv[0] in ("-h", "--help", "help"):
        return None
    cmd, rest = argv[0], argv[1:]
    a = {"cmd": cmd, "files": []}
    i = 0
    while i < len(rest):
        x = rest[i]
        if x in ("-h", "--help"):
            return None
        if x == "--all":
            a["all"] = True
        elif x == "--json":
            a["json"] = True
        elif x == "--strict":
            a["strict"] = True
        elif x == "--no-history":
            a["no_history"] = True
        elif x == "--no-hub":
            a["no_hub"] = True
        elif x in ("--data", "--spelling"):
            if i + 1 >= len(rest):
                raise SystemExit("ste100: %s needs a value" % x)
            a[x[2:]] = rest[i + 1]
            i += 1
        elif x.startswith("-"):
            raise SystemExit("ste100: unknown option %s" % x)
        elif cmd in ("scope", "render", "hub") and "dir" not in a:
            a["dir"] = x
        else:
            a["files"].append(x)
        i += 1
    if a.get("spelling") not in (None, "en-US", "en-GB"):
        raise SystemExit("ste100: --spelling is en-US or en-GB")
    return a


ACTIONS = ("render", "hub")  # commands that change files: they end with one ✓/⚠/✗ line


def main(argv):
    try:
        a = parse(argv)
    except SystemExit as e:
        if argv and argv[0] in ACTIONS:
            status("fail", str(e))
        else:
            print(e, file=sys.stderr)
        return 2
    if a is None:
        print_help()
        return 0
    cmds = {"scope": cmd_scope, "lint": cmd_lint, "render": cmd_render, "hub": cmd_hub}
    if a["cmd"] not in cmds:
        print("ste100: unknown command %s (scope, lint, render, hub)" % a["cmd"], file=sys.stderr)
        return 2
    if a["cmd"] == "lint" and not a["files"]:
        print("ste100: lint needs at least one file", file=sys.stderr)
        return 2
    try:
        return cmds[a["cmd"]](a)
    except Exception as e:  # the CLI boundary: any failure becomes one ✗ line or one error line, exit 2
        if a["cmd"] in ACTIONS:
            status("fail", "%s failed: %s" % (a["cmd"], e))
        else:
            print("ste100: %s" % e, file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
