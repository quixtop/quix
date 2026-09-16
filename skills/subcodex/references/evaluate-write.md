# Evaluating a write task result

1. **Verify** — run the verify command IN THE WORKTREE (explicit `--verify`, else
   the inferred project test/build). Capture output to `$SD/verify.log`.
2. **Grade** — Did tests/build pass? Does the diff actually satisfy the task
   intent (not merely compile)? Read `worktree.sh diff`.
3. **Decide:**
   - PASS → `worktree.sh apply` the diff onto the main tree (UNSTAGED, never
     auto-commit). On conflict, resolve — never discard; surface non-trivial
     conflicts to the user.
   - Tests RAN and FAILED → retry up to MAX_RETRIES, re-delegating with the
     failure log as context; then fallback (CC finishes it / surfaces to user).
   - Verify command could not run (missing/errored) → surface this; do NOT claim
     "verified". Distinguish this case from a genuine test failure.
