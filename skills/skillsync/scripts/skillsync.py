#!/usr/bin/env python3
# (c) Shrix
# author: shrix
"""
skillsync — Audit & repair the shrix skill naming/identity convention.

A skill is 'mine' iff its SKILL.md frontmatter declares author: shrix. Dir
names are plain and match the command (there is no longer an -x suffix).
Checks every such skill dir in ~/.agents/skills/ (enabled) and
~/.agents/disabled-skills/ (disabled) for:
  1. ~/.claude/skills/<name> symlink → ../../.agents/skills/<name>
  2. SKILL.md frontmatter  name: <name>   (matches the dir name)
  3. SKILL.md frontmatter  author: shrix
  4. SKILL.md frontmatter  description: starts with (shrix)
And, report-only, every reference one shrix skill makes to another (`/name`, or
a path into skills/<name>/) in its SKILL.md, references/ or scripts/: it must
sit inside a bundle, or be a listed mention, in CONVENTIONS.md § Bundles.

Usage:
  skillsync.py [--fix] [--help]
  skillsync.py add <name>   # onboard a skill: fix convention + create symlink

Note: runctl-managed commands are out of scope — use 'runctl list' for those.
"""

import atexit
import os
import re
import sys
from pathlib import Path

atexit.register(lambda: sys.stdout.isatty() and print())   # trailing gap, TTY only


def status(kind: str, msg: str) -> None:
    """The one closing status line of an action: ✓ ok · ✗ fail · ⚠ warn, coloured on a TTY."""
    glyph, colour = {"ok": ("✓", "32"), "fail": ("✗", "31"), "warn": ("⚠", "33")}[kind]
    line = f"{glyph} {msg}"
    print(f"\033[{colour}m{line}\033[0m" if sys.stdout.isatty() else line)


HOME = Path.home()
SKILLS_ENABLED  = HOME / ".agents" / "skills"
SKILLS_DISABLED = HOME / ".agents" / "disabled-skills"
CLAUDE_SKILLS   = HOME / ".claude" / "skills"
CONVENTIONS     = SKILLS_ENABLED / "CONVENTIONS.md"
# Where a skill's runtime text lives; docs/ is design history, never scanned.
SCAN_DIRS       = ("references", "scripts")
TICKED_NAME     = re.compile(r'`([a-z0-9][a-z0-9-]*)`')
VENDORED        = {"node_modules", "vendor", ".venv", "venv", "__pycache__", ".git", "dist", "build"}

# A YAML block-scalar header: `>` or `|`, then an optional indentation indicator
# (1-9) and chomping indicator (+/-) in either order, then an optional comment —
# `>-`, `>2`, `|-2`, `>2+`, `>- # note`.
BLOCK_HEADER = re.compile(r'^[>|]([1-9][+-]?|[+-][1-9]?)?(\s+#.*)?$')

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def plain_name(dirname: str) -> str:
    """The command name IS the dir name now — no -x suffix to strip."""
    return dirname


def parse_frontmatter(skill_md: Path) -> dict:
    """
    Parse YAML frontmatter (between first two '---' lines) from SKILL.md.
    Returns a dict with raw string values (quotes stripped).
    """
    result = {}
    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError:
        return result

    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return result

    block_key, block_lines, block_fold = None, [], True
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if block_key and (line.startswith((" ", "\t")) or not line.strip()):
            block_lines.append(line.strip())             # body of a > or | block scalar
            continue
        if block_key:
            result[block_key] = (" " if block_fold else "\n").join(x for x in block_lines if x)
            block_key, block_lines = None, []
        m = re.match(r'^([\w][\w-]*):\s*(.*)', line)
        if m:
            key = m.group(1)
            val = m.group(2).strip()
            if BLOCK_HEADER.match(val):                  # `description: >-` — value on the next lines
                block_key, block_fold = key, val.startswith(">")
                continue
            # Strip surrounding quotes (double or single) if present
            if len(val) >= 2 and val[0] == val[-1] and val[0] in ('"', "'"):
                val = val[1:-1]
            result[key] = val
    if block_key:
        result[block_key] = (" " if block_fold else "\n").join(x for x in block_lines if x)
    return result


def is_shrix_skill(skill_md: Path) -> bool:
    """A skill is 'mine' iff its folder and SKILL.md are real (never links) and
    the SKILL.md frontmatter block is closed and declares author: shrix — the
    same test as allow-own-edits."""
    if skill_md.parent.is_symlink() or skill_md.is_symlink() or not skill_md.is_file():
        return False
    try:
        lines = skill_md.read_text(encoding="utf-8").splitlines()
    except OSError:
        return False
    if not lines or lines[0].strip() != "---" or not any(x.strip() == "---" for x in lines[1:]):
        return False
    return parse_frontmatter(skill_md).get("author", "") == "shrix"


def get_user_skill_dirs():
    """
    Yield (dirname, is_disabled, skill_md_path) for every shrix skill dir in
    ~/.agents/skills/ (enabled) and ~/.agents/disabled-skills/ (disabled).
    Identity is the frontmatter 'author: shrix'; 3rd-party skills (no such
    marker) are skipped. Dir names are plain — no -x suffix.
    """
    for slot, is_disabled in [(SKILLS_ENABLED, False), (SKILLS_DISABLED, True)]:
        if not slot.exists():
            continue
        for entry in sorted(slot.iterdir()):
            if not entry.is_dir():
                continue
            skill_md = entry / "SKILL.md"
            if skill_md.exists() and is_shrix_skill(skill_md):
                yield entry.name, is_disabled, skill_md


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

def check_skill(dirname: str, is_disabled: bool, skill_md: Path) -> list[str]:
    """
    Run the 4-part convention check.
    Returns a list of human-readable issue strings (empty = OK).
    """
    plain  = plain_name(dirname)
    issues = []

    # 1. Symlink — only ENABLED skills carry a ~/.claude/skills/<plain> symlink.
    #    A disabled skill lives in ~/.agents/disabled-skills/ and should have NO
    #    entry under ~/.claude/skills/ (no dangling links), so skip the check.
    if not is_disabled:
        symlink          = CLAUDE_SKILLS / plain
        expected_target  = f"../../.agents/skills/{dirname}"

        if symlink.is_symlink():
            actual = os.readlink(str(symlink))
            if actual != expected_target:
                issues.append(
                    f"symlink target wrong: got '{actual}', want '{expected_target}'"
                )
        elif symlink.exists():
            issues.append("~/.claude/skills/<plain> exists but is not a symlink")
        else:
            issues.append(f"missing symlink: ~/.claude/skills/{plain}")

    # 2-4. Frontmatter
    fm = parse_frontmatter(skill_md)

    fm_name = fm.get("name", "")
    if fm_name != plain:
        issues.append(f"name: '{fm_name}' should be '{plain}'")

    if fm.get("author", "") != "shrix":
        issues.append("missing/wrong author: shrix")

    desc = fm.get("description", "")
    if not desc.startswith("(shrix)"):
        issues.append("description missing '(shrix)' prefix")

    return issues


def find_orphaned_symlinks() -> list[tuple[str, str, str]]:
    """
    Return orphaned symlinks: dangling symlinks in ~/.claude/skills/, each as
    (name, target, reason). Two kinds:
      - target dir exists only in ~/.agents/disabled-skills/ — leftover from a
        disable (the convention keeps NO symlink for disabled skills)
      - target doesn't resolve anywhere — real breakage
    Report-only; --fix never touches these.
    """
    disabled_dirs: set[str] = set()
    if SKILLS_DISABLED.exists():
        for d in SKILLS_DISABLED.iterdir():
            if d.is_dir():
                disabled_dirs.add(d.name)

    orphans = []
    if not CLAUDE_SKILLS.exists():
        return orphans

    for entry in sorted(CLAUDE_SKILLS.iterdir()):
        if entry.is_symlink() and not entry.exists():
            target  = os.readlink(str(entry))
            dirname = target.rstrip("/").split("/")[-1]
            if dirname in disabled_dirs:
                reason = "points at a disabled skill — remove it (disabled skills keep no symlink)"
            else:
                reason = "broken — target does not resolve"
            orphans.append((entry.name, target, reason))

    return orphans


def parse_bundles(path: Path):
    """
    Read CONVENTIONS.md § Bundles: a `| bundle | skills |` table and a
    `| skill | mentions |` table, names in backticks. Returns (bundles,
    mentions) — a list of name sets and {skill: names it may mention} — or
    None when the file or the section is absent.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    start = next((i for i, l in enumerate(lines) if re.match(r'^#{2,3} Bundles\b', l)), None)
    if start is None:
        return None
    level = len(lines[start]) - len(lines[start].lstrip("#"))
    bundles, mentions, table, fenced = [], {}, None, False
    for line in lines[start + 1:]:
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced                           # a `# line` in a code block is no heading
            continue
        if fenced:
            continue
        heading = re.match(r'^(#+) ', line)
        if heading and len(heading.group(1)) <= level:
            break
        if not line.startswith("|"):
            table = None
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or set(cells[0]) <= set("-: "):
            continue                                      # short row or the |---| line
        head = cells[0].lower()
        if head in ("bundle", "skill"):
            table = "bundles" if head == "bundle" else "mentions"
            continue
        if table == "bundles":
            bundles.append(set(TICKED_NAME.findall(cells[1])))
        elif table == "mentions":
            owner = TICKED_NAME.findall(cells[0])
            if owner:
                mentions.setdefault(owner[0], set()).update(TICKED_NAME.findall(cells[1]))
    return bundles, mentions


def skill_text_files(skill_dir: Path):
    """SKILL.md plus every real file under references/ and scripts/ — symlinks
    (runctl's links to ~/.local/bin) and docs/ are not the skill's own text."""
    yield skill_dir / "SKILL.md"
    for sub in SCAN_DIRS:
        root = skill_dir / sub
        if root.is_symlink() or not root.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            dirnames[:] = [d for d in dirnames if d not in VENDORED]   # third-party code is not the skill's
            for name in sorted(filenames):
                p = Path(dirpath) / name
                if not p.is_symlink() and p.is_file():
                    yield p


def references_between(skills) -> dict:
    """{skill: other ENABLED shrix skills it names — as a `/name` command (after a
    space, a backtick, `(`, `[` or `*`, never inside a path, a quote or a
    template), as the `name` skill, as a path into skills/<name>, as a
    relative ../<name> path, or as "skills" / "<name>" path parts}. A
    `../<name>` that resolves inside the skill itself is reported too — a
    false alarm in the safe direction, since the check is report-only."""
    names = sorted({d for d, off, _ in skills if not off}, key=len, reverse=True)
    if not names:
        return {}
    alt = "|".join(re.escape(n) for n in names)
    patterns = [
        re.compile(r'(?:^|(?<=[\s`(\[*]))/(' + alt + r')(?![\w/-]|\.\w)', re.M),
        re.compile(r'`(' + alt + r')` skill\b'),
        re.compile(r'(?:\.agents|\.claude)/skills/(' + alt + r')(?![\w-]|\.\w)'),
        re.compile(r'(?:^|(?<=[\s`(\["\'/]))\.\./(' + alt + r')(?![\w.-])', re.M),
        re.compile(r'"skills"\s*/\s*"(' + alt + r')"'),
    ]
    found = {}
    for dirname, is_disabled, skill_md in skills:
        if is_disabled:
            continue
        refs = set()
        for f in skill_text_files(skill_md.parent):
            try:
                text = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            for pattern in patterns:
                refs.update(m.group(1) for m in pattern.finditer(text))
        refs.discard(dirname)
        found[dirname] = refs
    return found


def check_bundles(skills):
    """(outside, unknown) — references outside every bundle and not a listed
    mention, and § Bundles names that are no shrix skill; None if no § Bundles."""
    parsed = parse_bundles(CONVENTIONS)
    if parsed is None:
        return None
    bundles, mentions = parsed
    known = {d for d, _, _ in skills}
    listed = {n for b in bundles for n in b} | set(mentions) | {n for v in mentions.values() for n in v}
    outside = []
    for src, refs in sorted(references_between(skills).items()):
        for dst in sorted(refs):
            if any(src in b and dst in b for b in bundles) or dst in mentions.get(src, ()):
                continue
            outside.append((src, dst))
    return outside, sorted(listed - known)


# ---------------------------------------------------------------------------
# Fix
# ---------------------------------------------------------------------------

def fix_skill(dirname: str, skill_md: Path, issues: list[str]) -> bool:
    """Repair the issues reported for a single NEEDS-FIX skill.
    Returns False when any repair could not land (collision, read/write error)."""
    plain = plain_name(dirname)
    landed = True

    # --- 1. Symlink ----------------------------------------------------------
    if any("symlink" in i or "missing symlink" in i for i in issues):
        symlink         = CLAUDE_SKILLS / plain
        expected_target = f"../../.agents/skills/{dirname}"
        if symlink.is_symlink():
            symlink.unlink()
        if not symlink.exists():
            symlink.symlink_to(expected_target)
            print(f"    [symlink] created ~/.claude/skills/{plain} -> {expected_target}")
        else:
            print(f"    [symlink] COLLISION: ~/.claude/skills/{plain} is a real skill dir "
                  f"(another installed skill owns this name) — not touching it. "
                  f"Rename one of the two, then re-run --fix.")
            landed = False

    # --- 2-4. Frontmatter ----------------------------------------------------
    fm_issues = [i for i in issues if "symlink" not in i and "missing symlink" not in i]
    if not fm_issues:
        return landed

    try:
        text = skill_md.read_text(encoding="utf-8")
    except OSError as e:
        print(f"    [error] cannot read {skill_md}: {e}")
        return False

    lines = text.splitlines(keepends=True)

    # Locate frontmatter block
    if not lines or lines[0].strip() != "---":
        print(f"    [skip] {skill_md.name} has no frontmatter — cannot repair")
        return False

    fm_end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            fm_end = i
            break

    if fm_end is None:
        print(f"    [skip] {skill_md.name} frontmatter not closed — cannot repair")
        return False

    fm_lines = list(lines[1:fm_end])

    # Fix name:
    if any("name:" in i for i in fm_issues):
        new_fm = []
        fixed  = False
        for l in fm_lines:
            if re.match(r'^name:\s*', l):
                new_fm.append(f"name: {plain}\n")
                fixed = True
            else:
                new_fm.append(l)
        if not fixed:
            new_fm.insert(0, f"name: {plain}\n")
        fm_lines = new_fm
        print(f"    [name] set name: {plain}")

    # Fix author:
    if any("author" in i for i in fm_issues):
        new_fm     = []
        found_auth = False
        for l in fm_lines:
            if re.match(r'^author:\s*', l):
                new_fm.append("author: shrix\n")
                found_auth = True
            else:
                new_fm.append(l)
        if not found_auth:
            # Insert after name: line
            inserted = False
            newer    = []
            for l in new_fm:
                newer.append(l)
                if re.match(r'^name:\s*', l) and not inserted:
                    newer.append("author: shrix\n")
                    inserted = True
            if not inserted:
                newer.insert(0, "author: shrix\n")
            new_fm = newer
        fm_lines = new_fm
        print("    [author] added author: shrix")

    # Fix description: (shrix) prefix
    if any("description" in i for i in fm_issues):
        new_fm       = []
        fixed_desc   = False
        in_block     = False
        empty_block  = False
        for l in fm_lines:
            if in_block and l.strip() and not l[:1].isspace():
                # the block ended with no text line — nothing to prefix; say so
                print("    [desc] the description block is empty — add its text by hand")
                landed = False
                empty_block = True
                in_block = False                 # this line is the next key: handle it below
            if in_block:
                # `description: >-` — prefix the block's first text line, keep its indent
                if l.strip():
                    if not l.strip().startswith("(shrix)"):
                        l = re.sub(r'^(\s+)', r'\1(shrix) ', l, count=1)
                    in_block = False
                new_fm.append(l)
                continue
            m = re.match(r'^(description:\s*)(.*)', l, re.DOTALL)
            if m and BLOCK_HEADER.match(m.group(2).strip()):
                new_fm.append(l)
                in_block = fixed_desc = True
                continue
            if m:
                prefix, rest = m.group(1), m.group(2).rstrip("\n")
                # Strip surrounding quotes if present
                quoted = rest.startswith('"') and rest.endswith('"')
                inner  = rest[1:-1] if quoted else rest
                if not inner.startswith("(shrix)"):
                    inner = f"(shrix) {inner}"
                new_val = f'"{inner}"' if quoted else inner
                new_fm.append(f"{prefix}{new_val}\n")
                fixed_desc = True
            else:
                new_fm.append(l)
        if in_block:                             # the block was the last frontmatter line
            print("    [desc] the description block is empty — add its text by hand")
            landed = False
            empty_block = True
        if not fixed_desc:
            # No description field found — add a minimal one after author
            inserted = False
            newer    = []
            for l in new_fm:
                newer.append(l)
                if re.match(r'^author:\s*', l) and not inserted:
                    newer.append("description: (shrix) \n")
                    inserted = True
            if not inserted:
                newer.append("description: (shrix) \n")
            new_fm = newer
        fm_lines = new_fm
        if not empty_block:
            print("    [desc] added (shrix) prefix to description")

    # Reconstruct and write
    new_text = "".join(["---\n"] + fm_lines + [lines[fm_end]] + lines[fm_end + 1:])
    try:
        skill_md.write_text(new_text, encoding="utf-8")
    except OSError as e:
        print(f"    [error] cannot write {skill_md}: {e}")
        return False
    return landed


# ---------------------------------------------------------------------------
# Add subcommand
# ---------------------------------------------------------------------------

def add_skill(name: str) -> int:
    """
    Onboard a single skill: make it convention-compliant and create/repair its
    ~/.claude/skills/<plain> symlink.  Reuses check_skill + fix_skill — no
    logic is duplicated.
    """
    # Accept a bare name OR a full/relative path to the dir — reduce to the
    # final path component. Dir names are plain now; tolerate a stray trailing
    # -x from old muscle memory.
    name    = name.rstrip("/").split("/")[-1]
    dirname = name[:-2] if name.endswith("-x") else name
    skill_md = SKILLS_ENABLED / dirname / "SKILL.md"

    # Guard: skill must exist in the enabled tree
    if not skill_md.exists():
        disabled_md = SKILLS_DISABLED / dirname / "SKILL.md"
        if disabled_md.exists():
            status("fail", f"'{dirname}' is disabled — move it first: "
                           f"mv ~/.agents/disabled-skills/{dirname} ~/.agents/skills/ · "
                           f"then skillsync.py add {name}")
            return 1
        status("fail", f"no skill dir with SKILL.md at ~/.agents/skills/{dirname}/")
        return 1

    plain  = plain_name(dirname)
    issues = check_skill(dirname, False, skill_md)

    print(f"Adding skill: {dirname}")

    if not issues:
        # Everything is already correct — report each check as compliant
        print("  [symlink] already linked")
        print("  [name]    already correct")
        print("  [author]  already set")
        print("  [desc]    already prefixed")
        print()
        status("warn", f"/{plain} already compliant — nothing changed")
        return 0

    # If symlink is already correct, note it (fix_skill won't print anything for it)
    if not any("symlink" in i or "missing symlink" in i for i in issues):
        expected_target = f"../../.agents/skills/{dirname}"
        print(f"  [symlink] already linked  (~/.claude/skills/{plain} -> {expected_target})")

    # Delegate all repairs to the existing fix routine (DRY)
    if not fix_skill(dirname, skill_md, issues):
        print()
        status("fail", f"/{plain} not fully onboarded — see the lines above")
        return 1

    print()
    status("ok", f"onboarded → /{plain}")
    return 0


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    args     = sys.argv[1:]
    fix_mode = "--fix" in args

    if "--help" in args or "-h" in args:
        print(__doc__)
        return 0

    # ---- add <name> subcommand ----------------------------------------------
    if args and args[0] == "add":
        if len(args) < 2:
            status("fail", "usage: skillsync.py add <name>  (the plain skill name, e.g. foo)")
            return 1
        return add_skill(args[1])

    # ---- Collect and audit all shrix skills ---------------------------------
    ok_skills       = []   # (dirname, plain)
    needs_fix       = []   # (dirname, plain, issues, skill_md)
    disabled_skills = []   # (dirname, plain, issues)
    all_skills      = list(get_user_skill_dirs())

    for dirname, is_disabled, skill_md in all_skills:
        plain  = plain_name(dirname)
        issues = check_skill(dirname, is_disabled, skill_md)

        if is_disabled:
            disabled_skills.append((dirname, plain, issues))
        elif issues:
            needs_fix.append((dirname, plain, issues, skill_md))
        else:
            ok_skills.append((dirname, plain))

    orphans = find_orphaned_symlinks()

    # ---- Report -------------------------------------------------------------
    if ok_skills:
        print(f"\nOK ({len(ok_skills)}):")
        for dirname, plain in ok_skills:
            print(f"  {dirname}")

    if needs_fix:
        print(f"\nNEEDS-FIX ({len(needs_fix)}):")
        for dirname, plain, issues, _ in needs_fix:
            print(f"  {dirname}")
            for issue in issues:
                print(f"    - {issue}")

    if disabled_skills:
        print(f"\nDISABLED ({len(disabled_skills)}) [info]:")
        for dirname, plain, issues in disabled_skills:
            if issues:
                print(f"  {dirname}  [issues: {len(issues)}]")
                for issue in issues:
                    print(f"    - {issue}")
            else:
                print(f"  {dirname}")

    if orphans:
        print(f"\nWARN — Orphaned symlinks ({len(orphans)}):")
        for name, target, reason in orphans:
            print(f"  ~/.claude/skills/{name}  ->  {target}   [{reason}]")

    bundle_check = check_bundles(all_skills)
    if bundle_check is None:
        print("\nWARN — no § Bundles in CONVENTIONS.md — bundle check skipped")
    else:
        outside, unknown = bundle_check
        if outside:
            print(f"\nWARN — references outside a bundle ({len(outside)}) — put the pair in one bundle "
                  "in CONVENTIONS.md § Bundles, or list it as a mention:")
            for src, dst in outside:
                print(f"  {src} → /{dst}")
        if unknown:
            print(f"\nWARN — named in CONVENTIONS.md § Bundles but not a shrix skill: {', '.join(unknown)}")

    if not ok_skills and not needs_fix and not disabled_skills:
        print("\n(no shrix skills found)")

    # ---- Fix ----------------------------------------------------------------
    if fix_mode:
        if not needs_fix:
            print()
            status("warn", "nothing to fix — all enabled skills are OK")
        else:
            print(f"\n--- FIX MODE ({len(needs_fix)} skill(s)) ---")
            failed = []
            for dirname, plain, issues, skill_md in needs_fix:
                print(f"  Fixing {plain} ({dirname})...")
                if not fix_skill(dirname, skill_md, issues):
                    failed.append(plain)
            print()
            if failed:
                status("fail", f"{len(failed)} skill(s) could not be fully fixed: {', '.join(failed)}")
                return 1
            status("ok", f"fixed {len(needs_fix)} skill(s) — re-run without --fix to verify")

    return 0


if __name__ == "__main__":
    sys.exit(main())
