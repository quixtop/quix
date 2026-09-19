# panel

An adversarial panel — agents from different models judge the same question independently. Needs: Codex CLI, jq.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- panel
```

## Requires

- [Codex CLI](https://github.com/openai/codex)
- [jq](https://github.com/jqlang/jq)

## Usage

Invoke it as `/panel` in Claude Code.

Adversarial multi-model panel — N agents from DIFFERENT models independently propose, cross-critique once, and are judged on evidence. Heterogeneity is enforced: same-model panels are refused and redirected to clodex's self-revision, because the research shows they underperform their cost. For code, the judge runs the tests rather than weighing arguments. Triggers on /panel [query], 'run a panel on X', 'get a multi-model review of X'. NOT for delegating work (subcodex) or a two-party dialectic (clodex).

## Source

`skills/panel` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
