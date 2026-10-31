# start --deep — the Explore brief
<!-- author: shrix -->

Give this to an Explore subagent ("medium" breadth) after the card. Fill
`<root>` and the card's Project line.

> Map the codebase at `<root>` (card: `<Project line>`). Read-only. Return 40
> lines or fewer, under these headings, with one `file:line` per claim:
>
> 0. First read `AI.md` if it exists (Claude Code does not load it), and follow
>    the docs that CLAUDE.md, AGENTS.md or AI.md point to for conventions.
> 1. **Structure** — top-level layout, entry points, where the core logic
>    lives, and how components, services and utils are organised.
> 2. **Stack** — language, framework, database, frontend, test runner, build.
> 3. **Conventions** — naming (files, functions, classes, constants), error
>    handling, logging, test layout; the pattern each follows, as observed.
> 4. **Dev gates** — what rejects a change before merge: tsconfig strictness,
>    target and path aliases, linter and its key rules, formatter, pre-commit
>    hooks, CI checks.
> 5. **Workflow** — setup and env setup, dev and watch, test and coverage,
>    build and deploy commands; the README's and CONTRIBUTING's setup and
>    contribution rules, summarised.
> 6. **External services** — SDKs and API clients by NAME (Auth, Storage,
>    Database, Cache, Payments, Email, Search, CDN, other), each with the
>    env-var NAMES it reads and where its key is obtained (the provider's
>    console or docs) — never the key.
> 7. **Health** — what is done well (clear entry points, consistent naming,
>    configuration kept apart from code, tests) and what needs attention (a
>    flat structure, mixed naming, no clear entry point, missing docs or
>    tests); one line each, only what you saw.
>
> Never open `.env*` (except `.env.example`, names only), `.dev.vars`,
> `*.tfvars`, `*.pem`, `*.key`, `secrets/` or `credentials*`. Never print a
> string literal, a URL or a value — names and `file:line` only. Use `find` or
> `/bin/ls`, never a bare `ls`. Spawn nothing.
