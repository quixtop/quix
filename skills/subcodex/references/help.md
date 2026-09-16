# /subcodex — delegate tasks to background Codex worker(s)

Usage:
  /subcodex <task>                      one read-only task, in place
  /subcodex --write <task>              write task in an isolated worktree
  /subcodex --verify "<cmd>" --write <task>   write task; CC runs <cmd> to verify
  /subcodex <task1> ; <task2> ; ...     batch: one Codex job per task

Flags:
  --write              write-capable Codex in a git worktree (default: read-only)
  --verify "<cmd>"     verification command for the eval step (default: inferred)
  --effort LEVEL       low|medium|high|xhigh (default: matched to Claude's model)
  --model <m>          override Codex model
  --wait               block until done instead of background+notify

Notes:
  - --write requires a git repo (worktree isolation). Non-git → read-only or
    explicit in-place-with-warning.
  - Integration never auto-commits to main; changes land unstaged for review.
  - Disambiguation: subcodex DELEGATES a task; clodex DEBATES a question.
