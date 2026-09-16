#!/usr/bin/env python3
"""Safe scripted edits to references/config.md's routing table.

Edits only the value part of a routing line, preserving all prose, section
headers, alignment, and trailing comments. Validates keys/tiers/efforts;
warns on band violations but obeys (the user's config is authoritative).

Usage:
  set_route.py set <task_key>=<tier>[,<effort>]
  set_route.py reset <task_key>|all
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resolve_model import DEFAULTS, TIER_ORDER, EFFORTS  # noqa: E402

CONFIG = Path(__file__).resolve().parent.parent / "references" / "config.md"


def format_route(tier: str, effort: str) -> str:
    # matches the shipped alignment: {tier: mid,      effort: high}
    return "{tier: " + f"{tier + ',':<9}" + f" effort: {effort}}}"


def rewrite(key: str, tier: str, effort: str, text: str) -> str:
    pattern = re.compile(
        r"^(\s+" + re.escape(key) + r":\s*)\{[^}]*\}(.*)$", re.M)
    if not pattern.search(text):
        sys.exit(f"error: task key '{key}' not found in config.md routing table")
    return pattern.sub(lambda m: m.group(1) + format_route(tier, effort) + m.group(2), text)


def warn_band(key: str, tier: str) -> None:
    if key not in DEFAULTS or key == "fallback_route":
        return
    d_tier = DEFAULTS[key][0]
    di, ti = TIER_ORDER.index(d_tier), TIER_ORDER.index(tier)
    if ti < di:
        print(f"warning: band violation (underkill) — '{key}' is {d_tier}-band work; "
              f"routing to {tier} risks cheap-but-wrong output. Obeying.")
    elif ti > di:
        print(f"warning: band violation (overkill) — '{key}' defaults to {d_tier}; "
              f"{tier} spends extra window for no quality gain. Obeying.")


def cmd_set(spec: str) -> None:
    key, _, val = spec.partition("=")
    key, val = key.strip(), val.strip()
    if not val:
        sys.exit("usage: set_route.py set <task_key>=<tier>[,<effort>]")
    tier, _, effort = val.partition(",")
    tier, effort = tier.strip(), effort.strip()
    if key not in DEFAULTS:
        sys.exit(f"error: unknown task key '{key}' (see resolve_model.py --table)")
    if tier not in TIER_ORDER:
        sys.exit(f"error: unknown tier '{tier}' (valid: {'|'.join(TIER_ORDER)})")
    effort = effort or DEFAULTS[key][1]
    if effort not in EFFORTS:
        sys.exit(f"error: unknown effort '{effort}' (valid: {'|'.join(EFFORTS)})")
    warn_band(key, tier)
    CONFIG.write_text(rewrite(key, tier, effort, CONFIG.read_text()))
    print(f"set {key} = {{tier: {tier}, effort: {effort}}}")


def cmd_reset(target: str) -> None:
    text = CONFIG.read_text()
    keys = [k for k in DEFAULTS] if target == "all" else [target]
    for key in keys:
        if key not in DEFAULTS:
            sys.exit(f"error: unknown task key '{key}'")
        tier, effort = DEFAULTS[key]
        text = rewrite(key, tier, effort, text)
    CONFIG.write_text(text)
    print(f"reset {'all routing entries' if target == 'all' else target} to shipped defaults")


def main() -> None:
    if len(sys.argv) < 3 or sys.argv[1] not in ("set", "reset"):
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    if sys.argv[1] == "set":
        cmd_set(sys.argv[2])
    else:
        cmd_reset(sys.argv[2])


if __name__ == "__main__":
    main()
