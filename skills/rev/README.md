# rev

Review, fix and test until clean — an isolated reviewer sized to the change, a failing test before each fix, two rounds at most.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- rev
```

## Usage

Invoke it as `/rev` in Claude Code.

Review → fix → test until clean, at most two rounds, over a caller's base/range (optionally a path list) or audit findings by ID, else everything since the last push (uncommitted included); with nothing to review it offers /code-audit. An isolated reviewer sized to the change (a tiny diff skips it), a failing test before each fix; round 2 re-reviews only the fix hunks, and only after a Critical or security fix or a fix that adds logic. Triggers on /rev, 'review and clean up what I pushed', 'tighten the recent changes'. NOT one-pass review (/code-review, /simplify) or plan execution (/dev).

## Source

`skills/rev` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
