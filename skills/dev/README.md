# dev

Run an already-reviewed plan to completion, unattended — per task: test, implement, verify, an isolated review, a commit.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- dev
```

## Usage

Invoke it as `/dev` in Claude Code.

Run an already-reviewed plan to completion, unattended — flat tasks or phases; per task: test → implement → verify → isolated review → commit, with an exit gate at every phase boundary and a compaction-proof ledger. Triggers on /dev, 'dev this plan', or handing over a reviewed plan to run unattended — never on the bare word 'dev' in ordinary talk. OFFER it and get a yes first; never auto-run. Given only a rough idea, it offers /spec first. NOT planning, a single task, or exploratory work.

## Source

`skills/dev` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
