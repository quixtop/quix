#!/usr/bin/env python3
"""todo backend: personal todo list manager.

Default file: ~/md/todo.md. Configurable via the `path` subcommand; the active
path is persisted in ~/.agents/skills/todo/config.

Usage:
  todo.py                              # list
  todo.py add <text>[, <text>...]      # append one or more items
  todo.py remove <num>[, <num>...]     # remove pending OR done items
  todo.py completed <num>[, <num>...]  # mark pending items as done
  todo.py uncheck <num>[, <num>...]    # flip done items back to pending
  todo.py clear                        # wipe all done items
  todo.py path                         # show current path
  todo.py path <new>                   # set path (persistent)
  todo.py path reset                   # restore default
  todo.py help                         # show full help

Items are numbered CONTINUOUSLY: pending 1..P first, then done P+1..P+D.
All operations that take numbers (remove, completed, uncheck) use this
unified numbering. `remove N` works on any item; `completed N` errors if
N refers to an already-done item; `uncheck N` errors if N is still pending.

Any non-empty prefix of a subcommand works. Collision note: `c` resolves
to `completed` (checked first) to preserve muscle memory; `cl` or longer
is required to reach `clear` via prefix matching. Other canonicals have
unique first letters (a/r/p/h/u). Single-char alias: `x` → `clear`
(so `-x` is the short option for clear, since `clear`'s own letter `c`
collides with `completed`).

Flag syntax (POSIX/GNU-aligned):
  `-X`   — single dash + exactly one char (POSIX short option), e.g. `-a`
  `--X+` — double dash + one or more chars (GNU long option), e.g. `--add`
Both are stripped to their canonical form before prefix matching, so `-a`,
`--a`, and `--add` all resolve to `add`. Malformed forms like `-add`
(single dash + multi-char, looks like POSIX option clustering) and `---foo`
(excess dashes) are rejected with a usage error — this aligns with shell
muscle memory. Examples:
  /todo -a item1       → add item1
  /todo --add item1    → add item1
  /todo -r 3           → remove 3
  /todo -c 4           → completed 4
  /todo -p path1       → path path1
  /todo -h             → help

Batches are comma-separated. Numbers are resolved against the CURRENT display
order (pending 1..P first, then done P+1..P+D) before any mutation, so
`remove 2, 4` always targets what was #2 and #4 when you ran the command.
Batches are all-or-nothing: if any number is invalid or out of range, nothing
is mutated. Duplicate numbers are silently deduped.

Ranges: use `N-M` (inclusive, ascending) anywhere a number is valid, and mix
with singletons: `-c 1-5`, `-c 1-3, 7`, `-r 2-4, 8-10`. The echo line compresses
contiguous runs in the parsed result, so `-c 1, 2, 3, 5` echoes as `completed
1-3, 5`. Invalid ranges (e.g. `5-1`, `1-`, `1-5-7`, `1-abc`) reject with a
usage error; batches remain all-or-nothing.

Limitation: because `,` is the batch separator, you cannot add an item whose
text contains a comma — `add Hello, world` creates two items, not one.

Output: bare `/todo` shows just the list. Mutation commands echo the resolved
full-form invocation on a `›` line above the list. Errors are a single ❌ line
with no echo.
"""

import os
import re
import sys

DEFAULT_TODO_PATH = os.path.expanduser("~/md/todo.md")
CONFIG_PATH = os.path.expanduser("~/.agents/skills/todo/config")
ITEM_RE = re.compile(r"^- \[( |x)\] (.+)$")


def get_todo_path():
    """Return the currently configured todo file path (absolute)."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            configured = f.readline().strip()
        if configured:
            return os.path.expanduser(configured)
    return DEFAULT_TODO_PATH


def set_config_path(abs_path):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        f.write(abs_path + "\n")


def clear_config_path():
    if os.path.exists(CONFIG_PATH):
        os.remove(CONFIG_PATH)


def display_path(path):
    """Normalize $HOME → ~ for readability."""
    home = os.path.expanduser("~")
    if path == home:
        return "~"
    if path.startswith(home + os.sep):
        return "~" + path[len(home):]
    return path


def read_lines():
    path = get_todo_path()
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return f.read().splitlines()


def write_lines(lines):
    path = get_todo_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))
    os.replace(tmp, path)  # atomic — a crash mid-write can't corrupt the todo file


def parse_items(lines):
    """Return list of (line_index, done:bool, text:str) for every todo line."""
    items = []
    for i, line in enumerate(lines):
        m = ITEM_RE.match(line)
        if m:
            items.append((i, m.group(1) == "x", m.group(2)))
    return items


def _load_partitioned():
    """Read file, parse items, and split into pending/done.
    Returns (lines, pending, done, num_pending, total) — the shared setup used
    by cmd_rem, cmd_completed, and cmd_uncheck. Centralizes "how do we partition
    items" so the three commands only differ in their validation + mutation logic.
    """
    lines = read_lines()
    items = parse_items(lines)
    pending = [it for it in items if not it[1]]
    done = [it for it in items if it[1]]
    return lines, pending, done, len(pending), len(items)


def render(items):
    total = len(items)
    done = sum(1 for it in items if it[1])
    if total == 0:
        return "**ToDo** (0 items) — empty"

    out = [f"**ToDo** ({total} items, {done} done)"]
    n = 0
    # pending first, numbered 1..num_pending
    for _, is_done, text in items:
        if not is_done:
            n += 1
            out.append(f"{n}. {text}")
    # completed below, continuous numbering, ✅ right-aligned column
    # (longest done text gets 1 space before ✅; shorter ones padded to match)
    done_texts = [text for _, is_done, text in items if is_done]
    if done_texts:
        max_len = max(len(t) for t in done_texts)
        for _, is_done, text in items:
            if is_done:
                n += 1
                pad = " " * (max_len - len(text) + 1)
                out.append(f"{n}. {text}{pad}✅")
    return "\n".join(out)


def echo(resolved):
    """Print a one-line echo showing the resolved full-form command."""
    print(f"› {resolved}")


def cmd_list():
    print(render(parse_items(read_lines())))


def split_csv(args):
    """Join argv tail with spaces, split on commas, strip, drop empties."""
    joined = " ".join(args)
    return [s.strip() for s in joined.split(",") if s.strip()]


def parse_num_list(args):
    """Parse a comma-separated list of numbers and/or ranges. Returns the
    deduped list (insertion order preserved) or None on error. On error, the
    appropriate message is printed before returning.

    Accepted elements:
      42        — single number
      3-7       — inclusive range, ascending (3 ≤ 7)
      5-5       — single-num range, equivalent to `5`
    Rejected:
      5-1       — descending range (rejected rather than silently flipped)
      1-        — incomplete
      -5        — empty first part
      1-5-7     — too many dashes
      1-abc     — non-numeric component
    """
    parts = split_csv(args)
    if not parts:
        usage()
        return None
    nums = []
    seen = set()
    for p in parts:
        if "-" in p:
            # range: exactly two components, both valid ints, ascending
            range_parts = p.split("-")
            if len(range_parts) != 2 or not range_parts[0] or not range_parts[1]:
                print(f"❌ Invalid range `{p}`")
                return None
            try:
                start = int(range_parts[0])
                end = int(range_parts[1])
            except ValueError:
                print(f"❌ `{p}` is not a valid range")
                return None
            if start > end:
                print(f"❌ Invalid range `{p}` (start > end)")
                return None
            if end - start + 1 > 10000:
                print(f"❌ Range `{p}` too large (max 10000 per range)")
                return None
            for n in range(start, end + 1):
                if n not in seen:
                    seen.add(n)
                    nums.append(n)
        else:
            try:
                n = int(p)
            except ValueError:
                print(f"❌ `{p}` is not a number")
                return None
            if n not in seen:
                seen.add(n)
                nums.append(n)
    return nums


def format_num_list(nums):
    """Run-length compress a list of ints, preserving insertion order.
    Contiguous runs (consecutive ascending) collapse to range notation.

    [1,2,3,4,5]       → '1-5'
    [1,2,3,5,7,8,9]   → '1-3, 5, 7-9'
    [1,3,5]           → '1, 3, 5'
    [5,1,2,3]         → '5, 1-3'   (insertion order preserved)
    [3,3]             → '3'        (dedup happens upstream, this is just robust)
    """
    if not nums:
        return ""
    parts = []
    start = nums[0]
    end = nums[0]
    for n in nums[1:]:
        if n == end + 1:
            end = n
        else:
            parts.append(f"{start}-{end}" if end > start else str(start))
            start = end = n
    parts.append(f"{start}-{end}" if end > start else str(start))
    return ", ".join(parts)


def cmd_add(args):
    texts = split_csv(args)
    if not texts:
        usage()
        return
    lines = read_lines()
    for text in texts:
        lines.append(f"- [ ] {text}")
    write_lines(lines)
    echo(f"add {', '.join(texts)}")
    print(render(parse_items(lines)))


def cmd_rem(args):
    nums = parse_num_list(args)
    if nums is None:
        return
    lines, pending, done, _, total = _load_partitioned()
    display_order = pending + done  # matches render() display sequence
    # validate all before mutating (all-or-nothing)
    for n in nums:
        if n < 1 or n > total:
            print(f"❌ No item #{n} (list has {total} items)")
            return
    # resolve all target line indices upfront, then rebuild without them
    target_line_idxs = {display_order[n - 1][0] for n in nums}
    lines = [line for i, line in enumerate(lines) if i not in target_line_idxs]
    write_lines(lines)
    echo(f"remove {format_num_list(nums)}")
    print(render(parse_items(lines)))


def cmd_completed(args):
    nums = parse_num_list(args)
    if nums is None:
        return
    lines, pending, _, num_pending, total = _load_partitioned()
    # validate all before mutating (all-or-nothing)
    for n in nums:
        if n < 1 or n > total:
            print(f"❌ No item #{n} (list has {total} items)")
            return
        if n > num_pending:
            print(f"❌ Item #{n} is already completed")
            return
    target_line_idxs = {pending[n - 1][0] for n in nums}
    for idx in target_line_idxs:
        lines[idx] = lines[idx].replace("- [ ]", "- [x]", 1)
    write_lines(lines)
    echo(f"completed {format_num_list(nums)}")
    print(render(parse_items(lines)))


def cmd_uncheck(args):
    nums = parse_num_list(args)
    if nums is None:
        return
    lines, _, done, num_pending, total = _load_partitioned()
    # validate all before mutating (all-or-nothing)
    for n in nums:
        if n < 1 or n > total:
            print(f"❌ No item #{n} (list has {total} items)")
            return
        if n <= num_pending:
            print(f"❌ Item #{n} is still pending")
            return
    # done index: n in [num_pending+1, total] → done[n - num_pending - 1]
    target_line_idxs = {done[n - num_pending - 1][0] for n in nums}
    for idx in target_line_idxs:
        lines[idx] = lines[idx].replace("- [x]", "- [ ]", 1)
    write_lines(lines)
    echo(f"uncheck {format_num_list(nums)}")
    print(render(parse_items(lines)))


def cmd_clear(args):
    # `clear` takes no args; any extra args → usage error
    if args:
        usage()
        return
    lines = read_lines()
    items = parse_items(lines)
    done_line_idxs = {it[0] for it in items if it[1]}
    lines = [line for i, line in enumerate(lines) if i not in done_line_idxs]
    write_lines(lines)
    echo("clear")
    print(render(parse_items(lines)))


def show_path_line():
    current = get_todo_path()
    suffix = " (default)" if current == DEFAULT_TODO_PATH else ""
    print(f"📍 {display_path(current)}{suffix}")


def cmd_path(args):
    # bare `path` → just show current, no echo, no list
    if not args:
        show_path_line()
        return
    arg = " ".join(args).strip()
    if arg == "reset":
        clear_config_path()
        echo("path reset")
        show_path_line()
        print(render(parse_items(read_lines())))
        return
    # set: expand ~, resolve to absolute
    new_path = os.path.abspath(os.path.expanduser(arg))
    set_config_path(new_path)
    echo(f"path {arg}")
    show_path_line()
    print(render(parse_items(read_lines())))


def cmd_help():
    current = get_todo_path()
    suffix = " (default)" if current == DEFAULT_TODO_PATH else ""
    print("""**/todo** — personal todo manager

Commands:
  /todo                                 show list
  /todo add <text>[, <text>...]         add item(s)
  /todo remove <num>[, <num>...]        remove pending OR done items
  /todo completed <num>[, <num>...]     mark pending item(s) done
  /todo uncheck <num>[, <num>...]       flip done item(s) back to pending
  /todo clear                           wipe all done items
  /todo path                            show current file path
  /todo path <new-path>                 set file path (persistent)
  /todo path reset                      restore default (~/md/todo.md)
  /todo -h | --help                     show this help

Numbering: items are numbered CONTINUOUSLY — pending first (1..P), then
done (P+1..P+D). All number-taking commands use this unified scheme.
Done items render with ✅ right-aligned in a column based on the longest
done item, so the checkmarks form a straight vertical line.

Shorthand: any non-empty prefix works —
  a / ad / add
  r / re / rem / remo / remov / remove
  c / co / ... / completed           ← `c` stays mapped to completed
  cl / cle / clea / clear             ← `clear` via prefix starts at `cl`
  p / pa / pat / path
  u / un / unc / ... / uncheck

Flag syntax (POSIX/GNU-aligned):
  -X     single dash + one char       e.g. -a, -r, -c, -p, -h, -u, -x
  --XYZ  double dash + multi-char     e.g. --add, --remove, --clear
Multi-char forms with a single dash (e.g. `-add`, `-rem`) are rejected
because POSIX reads them as option clustering. Special: `-x` is the
dedicated short option for `clear` (because `clear`'s natural letter `c`
collides with `completed`). Examples:
  /todo -a item1
  /todo -r 3               (works on pending OR done — continuous nums)
  /todo -c 4               (pending only; errors if item is already done)
  /todo -u 5               (done only; errors if item is still pending)
  /todo -x                 (wipe all done items)
  /todo -h

Batching: separate items or numbers with `,` — e.g.
  /todo add Buy milk, Call mom, Write skill
  /todo remove 2, 4
  /todo completed 1, 3
All-or-nothing: if any item in the batch is invalid, nothing is mutated.

Ranges: for remove/completed/uncheck, use `N-M` (inclusive, ascending)
anywhere a number is valid, mixed freely with singletons. E.g.
  /todo -c 1-5           (completes items 1 through 5)
  /todo -r 2-7           (removes items 2 through 7 — pending+done mixed)
  /todo -u 5-7           (flips done items 5-7 back to pending)
Invalid ranges (`5-1`, `1-`, `1-abc`, etc.) are rejected. The echo line
compresses contiguous runs, so `-c 1, 2, 3` echoes as `completed 1-3`.

Notes:
  • Pending and done items share one number space; `remove N` works on any.
  • `completed N` errors if N is already done; `uncheck N` errors if N is still pending.
  • `add Hello, world` creates TWO items (comma is the batch separator).
""")
    print(f"📍 {display_path(current)}{suffix}")


def usage():
    print("❌ Usage: see `/todo -h`")


def normalize_sub(raw):
    """Strip leading dashes per POSIX/GNU conventions, or return None if malformed.
    Then apply single-char aliases for canonicals that don't start with their own letter.

    Accepted forms:
      '-X'    → 'X'      (POSIX short option: one dash + exactly one char)
      '--XYZ' → 'XYZ'    (GNU long option: two dashes + one or more chars)
    Rejected forms (return None):
      '-XYZ'  (one dash + multi-char looks like POSIX clustering; not supported)
      '---X'  (three or more leading dashes; malformed)
      '-'     (dash only)
      '--'    (double dash only)
    Non-dash input passes through unchanged.

    Single-char aliases (applied after dash stripping, before prefix matching):
      'x' → 'clear'  (clear's canonical `c` collides with completed; `x` is its
                      dedicated short option. Works as `-x`, `--x`, or bare `x`.)
    """
    if not raw.startswith("-"):
        sub = raw
    elif raw.startswith("---"):
        return None
    elif raw.startswith("--"):
        sub = raw[2:] or None
        if sub is None:
            return None
    else:
        # single dash: accept only if exactly one char follows
        rest = raw[1:]
        if len(rest) != 1:
            return None
        sub = rest
    # Single-char aliases for canonicals with no unique prefix
    ALIASES = {"x": "clear"}
    return ALIASES.get(sub, sub)


def main(argv):
    if len(argv) == 1:
        cmd_list()
        return
    if argv[1] in ("-h", "--help"):
        cmd_help()
        return
    sub = normalize_sub(argv[1])
    if not sub:  # catches None (malformed dash form) and empty string
        usage()
        return
    rest = argv[2:]
    # Shorthand: any non-empty prefix of add/remove/completed/clear/path/uncheck.
    # Six canonicals, five unique first letters: a/r/c/p/u (c is shared —
    # completed is checked before clear so `c` → completed for muscle memory;
    # `cl`+ reaches clear via prefix matching, and `-x` reaches it via alias).
    if "add".startswith(sub):
        if not rest:
            usage()
            return
        cmd_add(rest)
    elif "remove".startswith(sub):
        if not rest:
            usage()
            return
        cmd_rem(rest)
    elif "completed".startswith(sub):
        # Note: `c` matches here (completed is checked before clear), so `-c`
        # preserves existing muscle memory. `cl`/`clear` routes to cmd_clear.
        if not rest:
            usage()
            return
        cmd_completed(rest)
    elif "clear".startswith(sub):
        cmd_clear(rest)  # takes no args; bare `clear` wipes all done items
    elif "path".startswith(sub):
        cmd_path(rest)  # bare `path` is valid (show current)
    elif "uncheck".startswith(sub):
        if not rest:
            usage()
            return
        cmd_uncheck(rest)
    else:
        usage()


if __name__ == "__main__":
    main(sys.argv)
