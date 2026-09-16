#!/usr/bin/env python3
"""Classify a free-text prompt -> routing task key -> {tier, effort, model}.

The ambient half of mouter: a UserPromptSubmit hook feeds the user's prompt in,
this prints a compact JSON recommendation the statusline chip renders as a
chip. Deliberately HIGH-PRECISION / LOW-RECALL: it only speaks up on clear
signals and stays SILENT (empty output, exit 0) when unsure — a wrong nudge is
worse than none. Coarse by design; it targets the common, high-signal task
classes, not all 40 keys.

Resolution reuses resolve_model.py's parser/adapter helpers so config
customizations and the active adapter's tier->model map are honored without
duplicating that logic. Pins/availability-fallback are NOT applied here — the
chip is advisory; the real resolve happens when the user's turn runs.

Usage:
  mouter_classify.py "add a --json flag to the report command"   # -> JSON or ""
  echo '{"prompt":"..."}' | mouter_classify.py                   # hook stdin (JSON)
  mouter_classify.py --key-only "write unit tests for utils.py"   # -> key or ""
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from resolve_model import (  # noqa: E402
    DEFAULTS, TIER_ORDER, load_config, load_adapter, detect_agent, tier_model,
)

# mouter's own subcommands — never a routable task.
COMMANDS = {"status", "config", "table", "set", "reset", "refresh",
            "throttle", "toggle", "on", "off", "mouter"}

# Priority-ordered (rule wins on first match). High-stakes / most-specific
# first, cheap lanes next, broad feature/refactor last, so a specific signal
# is never shadowed by a generic one. `breadth` marks rules that escalate a
# tier when the prompt shows multi-file scope (see BREADTH).
BREADTH = re.compile(
    r"\b(across|through(out)?\s+(everything|the\s+\w+base)|every\s+file|"
    r"monorepo|many\s+files?|spans?|whole\s+(codebase|repo|app)|"
    r"legacy|\d+\s*files?|refactor\s+the\s+entire)\b", re.I)

RULES = [
    # key,                        pattern
    ("security_review",
     r"security\s+review|\bsecurity\b|\bvuln(erabilit\w+)?\b|\bexploit\b|"
     r"\binjection\b|\bauthz\b|\bauthn\b|\bCVE\b|secret\s+(leak|exposure)|SSRF"),
    ("epic_to_tickets",
     r"\b(break|decompos\w+|split)\b.*\b(prd|epic|tickets?|tasks?|stories)\b"),
    ("schema_design",
     r"\b(schema|data\s*model)\b.*\b(design|add|new|migrat\w+)|"
     r"\bdesign\b.*\b(schema|data\s*model|database\s+(schema|tables?))\b"),
    ("architecture_greenfield",
     r"\b(design|architect)\b.*\b(system|service|architecture|from\s+scratch|"
     r"greenfield|new\s+(service|system))\b"),
    ("debugging_hard_novel",
     r"\b(intermittent|flaky|deadlock|race\s+condition|heisenbug|"
     r"non-?deterministic)\b|only\s+under\s+load"),
    ("bugfix_known",
     r"\bfix(es|ed|ing)?\b.*\b(bug|error|crash|failure|exception|regression|"
     r"broken)\b|\bbugfix\b"),
    # features before the test/doc lanes: in a composite ("add X with tests
    # and docs") the lead action is the main lane; tests/docs are amplifiers.
    # Verbs use EXPLICIT inflections (not open \w*) so "address"/"fixture"-style
    # words can't false-trigger — a wrong nudge is worse than none.
    ("feature_cross_file",
     r"\b(add(s|ing|ed)?|implement\w*|build(s|ing)?|built|creat(e|es|ing|ed)|"
     r"wir(e|es|ing)\s+up)\b.*\b(feature|endpoint|flow|integration|module|"
     r"subsystem)\b", "breadth"),
    ("feature_well_scoped",
     r"\b(add(s|ing|ed)?|implement\w*|build(s|ing)?|built|creat(e|es|ing|ed)|"
     r"wir(e|es|ing)\s+up)\b.*\b(flag|option|parameter|function|method|"
     r"endpoint|retry|button|field|feature|command)\b"),
    ("unit_tests",
     r"\b(unit\s+tests?|write\s+tests?|add\s+tests?|test\s+coverage|"
     r"missing\s+tests?)\b|\bcoverage\b"),
    ("boilerplate_scaffolding",  # lint/format lane
     r"\b(lint|ruff|eslint|prettier|flake8|black|gofmt|unused\s+imports?|"
     r"dead\s+code|format(ting)?|whitespace|scaffold(ing)?|boilerplate)\b"),
    ("commit_messages", r"\bcommit\s+messages?\b"),
    ("pr_description",
     r"\b(pr|pull\s+request)\s+(description|desc|summary|blurb)\b|"
     r"describe\s+(this|the)\s+(pr|pull\s+request|diff)\b"),
    ("release_notes", r"\b(release\s+notes|changelog)\b"),
    ("docs_sync",  # order-insensitive: "update the docs" or "docs update"
     r"\b(docs?|documentation|readme|docstrings?)\b.*\b(update|sync|refresh|"
     r"writ\w*|fix\w*)\b|\b(updat\w*|sync\w*|refresh\w*|writ\w*)\b.*\b(docs?|"
     r"documentation|readme|docstrings?)\b|\bdocument\s+(this|the|these)\b"),
    ("issue_triage", r"\b(triage|categoriz\w+|label)\b.*\b(issues?|tickets?)\b"),
    ("dependency_audit",
     r"\b(audit|check|review)\b.*\bdependenc\w+\b|\boutdated\s+packages?\b"),
    # refactor: breadth escalates long-multifile vs standard. Verbs stemmed
    # (\w*) so "refactoring"/"restructuring"/"migrating" match.
    ("refactor_long_multifile",
     r"\b(refactor\w*|rip\w*\s+out|rework\w*|restructur\w*|migrat\w*)\b",
     "breadth"),
    ("refactor_standard",
     r"\b(refactor\w*|rework\w*|restructur\w*|clean\s+up|de-?dup\w*|tidy\w*)\b"),
    ("unfamiliar_codebase_dive",
     r"\b(understand|explore|dive\s+into|trace\s+through|investigate|"
     r"walk\s+me\s+through|unfamiliar)\b.*\b(codebase|repo|system|module)\b"),
]

# Precompile once.
_COMPILED = [(k, re.compile(p, re.I), *rest) for k, p, *rest in RULES]


def classify(prompt: str) -> str | None:
    """Return a task key, or None when no confident signal fires."""
    text = prompt.strip()
    if len(text) < 12:                       # trivial / conversational
        return None
    words = text.split()
    # A leading subcommand word is a mouter command ONLY when the prompt is
    # short — else "set up a retry…" / "table the migration" get eaten.
    if words[0].lower() in COMMANDS and (len(words) <= 3
                                         or words[0].lower() == "mouter"):
        return None
    for key, pat, *flags in _COMPILED:
        if pat.search(text):
            if "breadth" in flags and not BREADTH.search(text):
                continue                      # breadth rule needs a scope signal
            return key
    return None


def resolve(key: str, config: dict, adapter: dict) -> dict | None:
    """key -> {tier,effort,model}, or None if it can't resolve to a valid tier.

    Advisory-only: honors config routing + shipped DEFAULTS but does NOT apply
    adapter pins or availability fallback (resolve_model.py owns those for the
    real turn). Returns None on an unknown key or a typo'd tier so a bad chip
    never renders.
    """
    entry = config.get("routing", {}).get(key)
    entry = entry if isinstance(entry, dict) else {}
    default = DEFAULTS.get(key)
    tier = entry.get("tier") or (default[0] if default else None)
    effort = entry.get("effort") or (default[1] if default else "high")
    if tier not in TIER_ORDER:               # unknown key / typo'd tier
        return None
    return {"key": key, "tier": tier, "effort": effort,
            "model": tier_model(adapter, tier)}


def read_prompt(argv_prompt: str | None) -> str:
    if argv_prompt:
        return argv_prompt
    raw = sys.stdin.read() if not sys.stdin.isatty() else ""
    if not raw.strip():
        return ""
    try:                                      # hook feeds JSON on stdin
        obj = json.loads(raw)
        if isinstance(obj, dict):
            return str(obj.get("prompt") or "")
        return raw                            # scalar/array JSON -> treat as text
    except (ValueError, TypeError):
        return raw                            # plain text fallback


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("prompt", nargs="?", help="prompt text (else read stdin)")
    p.add_argument("--key-only", action="store_true", help="print only the key")
    args = p.parse_args()

    key = classify(read_prompt(args.prompt))
    if not key:                               # silent when unsure
        return
    if args.key_only:
        print(key)
        return
    config = load_config()
    adapter = load_adapter(detect_agent(config, None))
    reco = resolve(key, config, adapter)
    if reco:
        print(json.dumps(reco))


if __name__ == "__main__":
    main()
