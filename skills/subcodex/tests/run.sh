#!/usr/bin/env bash
# Run every test_*.sh in this dir; exit nonzero if any fail.
set -uo pipefail
cd "$(dirname "$0")"
fails=0
for t in test_*.sh; do
  echo "== $t =="
  bash "$t" || fails=$((fails+1))
done
[ "$fails" -eq 0 ] && echo "SUITE PASS" || { echo "SUITE: $fails file(s) failed"; exit 1; }
