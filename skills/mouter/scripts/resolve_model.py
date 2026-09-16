#!/usr/bin/env python3
"""Resolve task keys -> {tier, effort} -> concrete model via the active adapter.

Resolution order: request flags > config routing entry > shipped default.
Emits one-line band-violation warnings in both directions (overkill and
underkill), applies adapter pins (e.g. a tier ceiling for security work),
and handles model unavailability by falling back one band at a time.

Stdlib only — parses the constrained YAML subset used in mouter's markdown
files without PyYAML, so the skill works on any machine with python3.

Usage examples:
  resolve_model.py --task unit_tests --task docs_sync
  resolve_model.py --task schema_design --request-tier light   # obeyed + warned
  resolve_model.py --tier mid --effort high                    # direct, no key
  resolve_model.py --table                                     # full routing table
  resolve_model.py --task X --unavailable frontier             # simulate outage
"""
import argparse
import os
import re
import sys
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parent.parent
REFS = SKILL_ROOT / "references"

TIER_ORDER = ["light", "mid", "top", "frontier"]  # ascending weight
EFFORTS = ["low", "medium", "high", "xhigh"]

# Shipped routing defaults — the reference point for band-violation warnings
# and for set_route.py's reset. Mirrors the routing table in references/config.md.
DEFAULTS = {
    "fallback_route":             ("mid", "high"),
    "spec_clarification":         ("top", "high"),
    "feasibility_analysis":       ("top", "high"),
    "epic_to_tickets":            ("top", "high"),
    "architecture_bounded":       ("top", "xhigh"),
    "architecture_greenfield":    ("frontier", "high"),
    "schema_design":              ("top", "xhigh"),
    "second_opinion":             ("top", "high"),
    "feature_well_scoped":        ("mid", "high"),
    "feature_cross_file":         ("top", "high"),
    "refactor_standard":          ("mid", "high"),
    "refactor_long_multifile":    ("frontier", "high"),
    "boilerplate_scaffolding":    ("light", "low"),
    "computer_use_automation":    ("mid", "high"),
    "bugfix_known":               ("mid", "high"),
    "debugging_hard_novel":       ("top", "xhigh"),
    "investigation_long_context": ("frontier", "high"),
    "repro_bisect_logdive":       ("mid", "high"),
    "unit_tests":                 ("mid", "high"),
    "test_gap_analysis":          ("mid", "high"),
    "e2e_integration_design":     ("mid", "high"),
    "edge_case_hunt":             ("mid", "high"),
    "diff_review_routine":        ("mid", "high"),
    "diff_review_high_stakes":    ("top", "xhigh"),
    "security_review":            ("top", "xhigh"),
    "docs_sync":                  ("light", "low"),
    "api_docs_judgment":          ("mid", "high"),
    "pr_description":             ("light", "low"),
    "commit_messages":            ("light", "low"),
    "release_notes":              ("light", "low"),
    "cicd_pipeline_config":       ("mid", "high"),
    "deployment_rollback_plan":   ("top", "xhigh"),
    "dependency_audit":           ("light", "low"),
    "dependency_migration":       ("top", "high"),
    "profiling_analysis":         ("mid", "high"),
    "optimization_subtle":        ("top", "xhigh"),
    "db_migration_backfill":      ("top", "xhigh"),
    "issue_triage":               ("light", "low"),
    "unfamiliar_codebase_dive":   ("frontier", "high"),
}


# ---------- minimal YAML-subset parsing ----------

def strip_comment(line: str) -> str:
    depth = 0
    for i, ch in enumerate(line):
        if ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
        elif ch == "#" and depth == 0:
            return line[:i]
    return line


def parse_value(val: str):
    val = val.strip()
    if val.startswith("{") and val.endswith("}"):
        out = {}
        for part in val[1:-1].split(","):
            if part.strip():
                k, _, v = part.partition(":")
                out[k.strip()] = v.strip()
        return out
    if val.startswith("[") and val.endswith("]"):
        return [p.strip() for p in val[1:-1].split(",") if p.strip()]
    if val in ("true", "false"):
        return val == "true"
    return val


def parse_yaml_subset(text: str) -> dict:
    root, current = {}, None
    for raw in text.splitlines():
        line = strip_comment(raw)
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip())
        key, _, val = line.strip().partition(":")
        key = key.strip()
        if indent == 0:
            if val.strip():
                root[key] = parse_value(val)
                current = None
            else:
                root[key] = {}
                current = root[key]
        elif current is not None:
            current[key] = parse_value(val)
    return root


def yaml_blocks(md_text: str) -> dict:
    merged = {}
    for block in re.findall(r"```yaml\n(.*?)```", md_text, re.S):
        merged.update(parse_yaml_subset(block))
    return merged


def load_config() -> dict:
    path = REFS / "config.md"
    if not path.exists():
        return {}
    return yaml_blocks(path.read_text())


def detect_agent(config: dict, override: str | None) -> str:
    if override:
        return override
    if config.get("agent"):
        return str(config["agent"])
    if os.environ.get("CLAUDECODE") or os.environ.get("CLAUDE_CODE"):
        return "claude"
    if os.environ.get("CODEX_HOME") or os.environ.get("CODEX_SANDBOX"):
        return "codex"
    return "claude"


def load_adapter(agent: str) -> dict:
    path = REFS / f"{agent}.md"
    if not path.exists():
        sys.exit(f"error: no adapter references/{agent}.md — check config.md 'agent' key")
    data = yaml_blocks(path.read_text())
    if "tiers" not in data:
        sys.exit(f"error: adapter references/{agent}.md has no 'tiers' yaml block")
    return data


# ---------- resolution ----------

def tier_idx(tier: str) -> int:
    return TIER_ORDER.index(tier)


def tier_model(adapter: dict, tier: str) -> str:
    entry = adapter["tiers"].get(tier, {})
    return entry.get("model", tier) if isinstance(entry, dict) else str(entry)


def resolve_one(key, config, adapter, args, lines):
    routing = config.get("routing", {})
    notes = []

    # request > config > shipped default > fallback_route
    if args.request_tier:
        tier, effort, source = args.request_tier, args.request_effort, "request"
    elif key in routing:
        entry = routing[key]
        tier, effort = entry.get("tier"), entry.get("effort")
        source = "config"
    elif key in DEFAULTS:
        tier, effort = DEFAULTS[key]
        source = "default"
    else:
        fb = routing.get("fallback_route") or dict(zip(("tier", "effort"), DEFAULTS["fallback_route"]))
        tier, effort = fb.get("tier"), fb.get("effort")
        source = "fallback_route"
        notes.append(f"no routing entry for '{key}' — using fallback_route ({tier}/{effort}), announced")

    if tier not in TIER_ORDER:
        sys.exit(f"error: unknown tier '{tier}' for '{key}' (valid: {'|'.join(TIER_ORDER)})")
    customized = key in DEFAULTS and source == "config" and (tier, effort) != DEFAULTS[key]
    effort = effort or DEFAULTS.get(key, (None, "high"))[1]
    if args.request_effort:
        effort = args.request_effort

    # two-sided band audit vs shipped default
    if key in DEFAULTS and source in ("config", "request"):
        d_tier = DEFAULTS[key][0]
        if tier_idx(tier) < tier_idx(d_tier):
            notes.append(f"band violation (underkill): '{key}' is {d_tier}-band work routed to {tier} — complying per {source}")
        elif tier_idx(tier) > tier_idx(d_tier):
            notes.append(f"band violation (overkill): '{key}' defaults to {d_tier}; {tier} spends extra window for no quality gain — complying per {source}")

    # adapter pins: tier ceilings (e.g. security never above 'top')
    pins = adapter.get("pins", {})
    if key in pins and not args.request_model:
        pin = str(pins[key])
        if tier_idx(tier) > tier_idx(pin):
            notes.append(f"adapter pin: '{key}' capped {tier} -> {pin} (see adapter notes)")
            tier = pin

    # tier -> model, with one-band-down availability fallback
    unavailable = set(args.unavailable or [])
    model = tier_model(adapter, tier)
    fb_tier = tier
    while (model in unavailable or fb_tier in unavailable) and tier_idx(fb_tier) > 0:
        prev = fb_tier
        fb_tier = TIER_ORDER[tier_idx(fb_tier) - 1]
        model = tier_model(adapter, fb_tier)
        notes.append(f"availability fallback: {prev} unavailable -> {fb_tier} ({model}) — continuing")
    tier = fb_tier

    if args.request_model:
        notes.append(f"request-named model '{args.request_model}' overrides tier mapping")
        model = args.request_model

    # adapter effort mapping (graceful degradation where host lacks a level)
    emap = adapter.get("efforts", {})
    host_effort = emap.get(effort, effort)
    if host_effort != effort:
        notes.append(f"effort '{effort}' not independently settable on this host -> '{host_effort}' (noted, not failed)")

    lines.append(f"task={key} tier={tier} effort={host_effort} model={model} source={source}"
                 + (" customized=yes" if customized else ""))
    for n in notes:
        lines.append(f"  note: {n}")


def print_table(config, adapter):
    routing = config.get("routing", {})
    print(f"# routing table — agent={detect_agent(config, None)}  (* = customized vs shipped default)")
    for key in DEFAULTS:
        if key == "fallback_route":
            continue
        entry = routing.get(key, {})
        tier = entry.get("tier", DEFAULTS[key][0])
        effort = entry.get("effort", DEFAULTS[key][1])
        star = " *" if (tier, effort) != DEFAULTS[key] else ""
        print(f"{key:<27} {tier:<9} {effort:<6} -> {tier_model(adapter, tier)}{star}")
    fb = routing.get("fallback_route", {})
    print(f"{'fallback_route':<27} {fb.get('tier', 'mid'):<9} {fb.get('effort', 'high')}")


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--task", action="append", help="task key(s) to resolve")
    p.add_argument("--tier", help="resolve a bare tier directly (no task key)")
    p.add_argument("--effort", help="effort for --tier mode")
    p.add_argument("--agent", help="adapter override (else config.md / env autodetect)")
    p.add_argument("--request-tier", choices=TIER_ORDER, help="user-requested tier (wins over config)")
    p.add_argument("--request-effort", choices=EFFORTS, help="user-requested effort (wins over config)")
    p.add_argument("--request-model", help="user-named concrete model (wins over everything)")
    p.add_argument("--unavailable", action="append", help="model/tier to treat as unavailable (repeatable)")
    p.add_argument("--table", action="store_true", help="print the full routing table")
    args = p.parse_args()

    config = load_config()
    adapter = load_adapter(detect_agent(config, args.agent))

    if args.table:
        print_table(config, adapter)
        return
    if args.tier:
        if args.tier not in TIER_ORDER:
            sys.exit(f"error: unknown tier '{args.tier}'")
        effort = args.effort or "high"
        model = tier_model(adapter, args.tier)
        print(f"tier={args.tier} effort={adapter.get('efforts', {}).get(effort, effort)} model={model}")
        return
    if not args.task:
        p.error("nothing to resolve: pass --task, --tier, or --table")

    lines = []
    for key in args.task:
        resolve_one(key, config, adapter, args, lines)
    print("\n".join(lines))


if __name__ == "__main__":
    main()
