# dep

Ship recent changes wherever they run — gate, review, deploy, prove, log — in one command.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- dep
```

## Usage

Invoke it as `/dep` in Claude Code.

Ship recent dev changes wherever they run — restart a service, build a client bundle, publish to a host — via a change-gated five-step pipeline ending in a shipped-table report + interactive smoke-check widget + deplog entry; resolves each repo's targets once. Triggers on the bareword `dep` (also `dep <target>`, `dep server`/`srv`/`s`, `dep ext`/`extn`/`e`, `dep both`/`all`, `dep <target> force`) and on `deploy`/`go live`.

## Source

`skills/dep` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
