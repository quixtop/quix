# spec — requirements

Spec: `docs/spec/think-and-review.md` (the approved design; where it and this
file differ, this file and the skill files are current).

## Before the spec is written
- In full mode, /spec runs a question drill (light offered on turn 1, taken only on an explicit yes), a concept gate, an idea panel of the triggered lenses (Scope and reuse and Pre-mortem always, the other five on their **Runs** line, no cap; each skipped lens named with its reason; the user's first reply after the wave, before Step 4, naming skipped lenses runs them as one extra wave) with one merger, and an approach pick before it writes the spec. Light mode, post-build mode and spec-only re-runs skip this stage and keep one batch.
- The only turns that ask in the think stage are the drill's questions, the concept gate when an inference answers a required-topic row (1, 2, 4, 5, 6) or a contradiction applies, at most 2 follow-ups, a contradiction, a lens STOP and the approach pick when approaches differ on scope or security; routing the panel's problems and the save point need no extra confirm. Spec: `docs/spec/think-lenient.md`.
- From the concept gate to the go, an answer or an idea-panel problem that contradicts Decided, without saying it replaces it, stops file writes for that turn and asks which one stands.
- Every full-mode run of a new feature saves the concept at the end of Step 3 as `draft — concept`; `/spec think` stops there; a later `/spec` (exact match) resumes at Step 4 without asking again, and Step 4 keeps what the concept holds. `think` runs full mode only, never offers light, and never writes to a feature that already has a spec or built code.
- The mode-word rule covers `think` and `review` as it covers `update` and `verify`.

## The spec and the plan
- Every spec and every ADR carries Alternatives considered (`N/A — one viable approach` in light mode, `N/A — not recorded` for a decision found in built code); Open questions is the first section.
- Every plan names a reason for each file and ends each phase green.
- SKILL.md stays at most 24,000 bytes.

## Review
- Full-mode Step 5 is a panel of 5 role reviewers with one merger, each role handed its rows of one Checks table; light mode, post-build mode and spec-only re-runs keep one reviewer with the whole table. An agent that cannot state the goal stops; one that could not read a file reports `incomplete`. Round 2 reviews only the fix hunks and never re-flags a closed finding.
- The panels and review rounds of Steps 1–5 plan at most 15 dispatches; one STOP recovery per panel, the merger of an extra idea-panel wave (its lenses count against the 7 lens slots), each go-with-changes reviewer and a fresh review count after a no-go come on top and are recorded. Each panel, round and single review records its agents (merger included), tokens and minutes in the spec's Review section. The idea lenses run on `sonnet`; the review roles, the merger and every reviewer run on the session model. Before each panel, one line names its planned agents and tokens (the idea panel's also its skipped lenses); a light run that switches to full names the added cost in its one-line notice. Neither waits for an answer.
- Every review dispatch is told to write only its own scratchpad file (reviewers write nothing) and never to read secret files; a content fingerprint of `<root>` (`checks.sh fp`) is compared before and after each wave. A panel agent returns only its file path and result; one that cannot write returns its report, and the merger takes it inline.
- At the go, "walk" takes the findings still open or fixed without a re-review, then the logged Minor ones, one per turn (`keep` · `change <how>` · `to tasks` · `stop`); the changes are applied as ONE go-with-changes round, and the go is asked again. A plain go is unchanged. Spec: `docs/spec/go-walkthrough.md`.
- A light run takes a local schema or stored-data change and writes its data and migration section, with rollback, inside the spec; one reviewer checks that every change to stored data or a public interface names its consumers and its rollback, and a Critical fix there gets round 2. Only auth, secrets, user data (accounts, personal data, content others see) or data that leaves the machine switches a light run to full. Spec: `docs/spec/review-cut.md`.
- `/spec review <file>` reviews existing docs with the panel and changes nothing; it skips the plan-only checks without a plan, and the spec-structure checks for a doc that is not a /spec spec.

## Docs against the code
- `/spec verify` also lists undocumented interfaces (exported, else top-level non-underscore; any doc naming it, a README included, or its docstring counts; tests and fixtures excluded) and four drift types — both block a clean pass. A scoped run blocks only on interfaces the range added or changed; older gaps, link nudges, the complex-logic note and `(planned)` entries listed as owed never block.
- `/spec update` gives each interface its scope added a doc, its docstring at least.

## Related: /rev
- /rev's close suggests /spec when the base range on the final tree passes 100 changed lines of core files (not tests, docs or config) or 3+ core files, and no spec or plan names a changed core file by its path.
