#!/usr/bin/env python3
"""Logic gates for the ambient mouter scripts. Run: python3 -B test_classify.py

Three sections, all must pass (pass/fail is on the classified KEY):
  1. positive key accuracy  — labeled fixtures classify to the right key
  2. decoy silence          — questions/decoys/commands classify to None
  3. hook robustness        — mouter_hook never crashes on malformed stdin
Chip-compare cases live in test_deploy.sh — they test the PRODUCTION bash/jq
path in the statusline wrapper, not a python re-implementation.
Not pytest — a fast standalone check.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from mouter_classify import classify  # noqa: E402

ROOT = HERE.parent
EVALS = json.loads((ROOT / "docs" / "evals.json").read_text())["evals"]

# 1. Expected primary key per fixture id (8, 9 are skill-behavior -> skip).
EXPECT = {
    1: "schema_design", 2: "boilerplate_scaffolding", 3: "unit_tests",
    4: "security_review", 5: "refactor_long_multifile",
    6: "feature_well_scoped", 7: "feature_well_scoped",
}

# 2. Must stay silent — questions, decoys (the "effort"/"route" traps), commands,
#    and the reviewer's proven verb-stem false positives.
DECOYS = [
    "explain effort estimation techniques in scrum",
    "what's the pricing difference between opus and sonnet",
    "did anthropic ship a fable 5.1 yet",
    "what does the walrus operator actually do in python",
    "address the retry option in the client module",     # add\w* trap
    "add a test fixture that reproduces the crash",       # fix\w* trap
    "route53 keeps serving stale records for staging",    # route trap
    "mouter status",
    "throttle low",
]


def section(title):
    print(f"\n=== {title} ===")


def main() -> None:
    fails = 0

    section("1. positive key accuracy")
    for e in EVALS:
        exp = EXPECT.get(e["id"])
        if not exp:
            continue
        got = classify(e["prompt"])
        ok = got == exp
        fails += not ok
        print(f"  [{e['id']}] {exp:<24} got={str(got):<24} {'PASS' if ok else 'FAIL'}")

    section("2. decoy silence")
    for d in DECOYS:
        got = classify(d)
        ok = got is None
        fails += not ok
        print(f"  {'PASS' if ok else 'FAIL'}  got={str(got):<20} :: {d[:44]}")

    section("3. hook robustness (never crash on bad stdin)")
    with tempfile.TemporaryDirectory() as td:
        env = {**os.environ, "MOUTER_RECO": str(Path(td) / "reco.json")}
        cases = ["", "not json at all", "123", "[1,2,3]", '"hi"',
                 '{"noprompt": 1}', '{"prompt": null}',
                 '{"prompt": "add a --json flag to the report command"}']
        for raw in cases:
            r = subprocess.run([sys.executable, "-B", str(HERE / "mouter_hook.py")],
                               input=raw, text=True, capture_output=True, env=env)
            ok = r.returncode == 0 and "Traceback" not in r.stderr
            fails += not ok
            label = (raw[:34] + "…") if len(raw) > 34 else raw
            print(f"  {'PASS' if ok else 'FAIL'}  exit={r.returncode} :: {label!r}")

    print(f"\n{'ALL PASS' if not fails else str(fails) + ' FAIL'}")
    sys.exit(0 if not fails else 1)


if __name__ == "__main__":
    main()
