# spec — the panel lenses and roles
<!-- author: shrix -->

READ when a panel runs: the idea panel (`references/think.md` § Idea panel)
uses § Idea lenses, the review panel (`references/review.md` § Panel) uses
§ Review roles. Each agent gets ONE block from here word for word — an idea lens without its
**Runs** line, which only the dispatcher reads — plus the "Every agent" list
below.

**Every agent:**

- **Goal check first.** State in one line what the feature is for and why. If
  the material does not let you do that, write only `result: stopped`,
  `STOP: goal unclear` and what is missing — run nothing else.
- **No taste findings.** Wording and style preferences are not findings; an
  agent told to find gaps always finds some.
- **Every finding in this one pass.** Nothing is held back for a later round.
- **`incomplete`, never clean**, when a file you needed could not be read:
  name it under `unread`.
- **One severity scale**: Critical (the feature fails or harms) · Important
  (a real gap the build would hit) · Minor (worth fixing, not blocking), each
  with file:line where there is one.
- **Report form** — the goal line, `result: findings | incomplete | stopped`,
  `unread: [paths]`, then each finding as severity · file:line · the problem ·
  why it matters · a suggested fix. A panel agent writes it to its own file
  and returns only the path and the `result:` line; one that cannot write its
  file returns the report itself. A reviewer returns the report itself.
  Minor findings: a panel agent writes each Minor finding on one line,
  `Minor · file:line · problem`; Critical and Important keep the full form.
  A reviewer keeps the full form for every finding.

## Idea lenses

The idea panel sees the concept the gate passed (the summary, Decided, Assumptions)
and the code under `<root>`. It attacks the idea, not a document.

### Scope and reuse
**Question**: Which parts of this idea are not needed for the stated goal, and what already in the codebase does part of it?
**Test**: A newcomer could name the simplest version that meets the goal, and the existing code it reuses, on the first try.
**Hard rule**: Search the code under `<root>` and name what can be reused, or say the search found nothing; every part you call unneeded names the goal it does not serve.
**Reads**: the concept, the reqs and tasks families, the code (search, then read the hits).
**Runs**: Always.

### Cost and limits
**Question**: What will this cost to run and where does it hit a limit — time, tokens, money, rate limits, size caps, quotas?
**Test**: A newcomer could state the run cost and the first limit it hits, with numbers, on the first try.
**Hard rule**: Every cost or limit carries a number or names the measurement that would give one.
**Reads**: the concept, the code paths it touches, configs that set limits.
**Runs**: When it calls agents, APIs or the network, or meets a size, rate or token limit.

### Ease of use
**Question**: Where will the person using this get stuck, confused or slowed down?
**Test**: A newcomer could do the main task the first time, without help, on the first try.
**Hard rule**: Every finding names the step where the user gets stuck and what they would expect instead.
**Reads**: the concept, the design family, the existing user-facing flow it changes.
**Runs**: When it changes a flow a person uses: a command, a prompt, a page.

### Migration and rollback
**Question**: What happens to existing data, users and callers when this ships, and how is it undone?
**Test**: A newcomer could ship it and roll it back without losing data, on the first try.
**Hard rule**: Every change to stored data or a public interface names its consumers and its rollback, or is a finding.
**Reads**: the concept, the data model and stored files, the callers of any interface it changes.
**Runs**: When stored data or a public interface changes.

### Monitoring
**Question**: When this fails in use, how will anyone know, and how fast?
**Test**: A newcomer could tell from the logs or the output that it failed, and why, on the first try.
**Hard rule**: Every failure path you name says what signal shows it, or that none does.
**Reads**: the concept, the code's error paths and logs, the existing reporting.
**Runs**: When it runs unattended: hooks, background jobs, scheduled runs.

### Upkeep
**Question**: What will this cost to keep working over the next year — moving parts, dependencies, files that must stay in step?
**Test**: A newcomer could change it six months from now without breaking something elsewhere, on the first try.
**Hard rule**: Every finding names the thing that must stay in step and what drifts if it does not.
**Reads**: the concept, the files it adds or couples, dependency lists.
**Runs**: When it adds files or dependencies, or files that must stay in step.

### Pre-mortem
**Question**: It is 3 months later and this feature failed or was removed: what are the most likely reasons?
**Test**: A newcomer could name the top three ways this fails, each with an early warning sign, on the first try.
**Hard rule**: At most five reasons, each specific to this feature and its codebase, never a generic project risk; each reason's early sign goes under "why it matters".
**Reads**: the concept, Decided and Assumptions, the code it touches.
**Runs**: Always.

## Review roles

The review panel sees the written set: the spec with every added section, the
companions and the plan, and the code under `<root>`. Each role also gets its
`references/review.md` § Checks rows; the block below says how to apply them.

### Fit
**Question**: Does the set build what was decided, inside the stated scope, without contradicting the project's existing decisions?
**Test**: A newcomer could say what the feature does and does not do, and which existing decision it relies on, on the first try.
**Hard rule**: Search the code under `<root>` for something that already does part of it; every contradiction cites both places, and a change recorded in Decided is intended, never a finding.
**Reads**: the spec (Decided, Assumptions, Open questions and To file included), the companions and the plan; the capture docs (reqs, arch, design, tasks) and the ADRs; the code for reuse.

### Fresh reader
**Question**: Can someone who never saw the discussion understand and build from this set?
**Test**: A newcomer could explain every term, follow every example and check every acceptance criterion, on the first try.
**Hard rule**: Every finding quotes the unclear line and says what a reader would have to guess; a requirement with no example where a reader needs one is a finding.
**Reads**: the spec, the companions and the plan, as a first-time reader who never saw the discussion.

### Design critic
**Question**: Is this the right design, and does it handle what goes wrong?
**Test**: A newcomer could say why this approach beat each rejected one, and what happens on every error path, on the first try.
**Hard rule**: In a Step 5 run of an EGM-full spec, no Alternatives entry is an Important finding; every vague requirement ("make it better"), undefined data item or missing error path is a finding.
**Reads**: Alternatives, the approach in Decided or Assumptions, 4.3, 4.4, 4.8, 4.9, 4.12, the companions.

### Build readiness
**Question**: Could `/dev` build this plan task by task without making a decision the plan left open?
**Test**: A newcomer could run each task, see it pass its Done when, and leave the build green, on the first try.
**Hard rule**: Every requirement maps to a plan task and every task to a check; every file has a one-line reason; every phase ends with the build and its tests green; in a partly-built run, `as-built` requirements need no plan task.
**Reads**: the plan, every spec requirement and success criterion, To file, the companions, the Status line of every file.

### Claims against the code
**Question**: Is every claim the set makes about the existing code, tools and dependencies true?
**Test**: A newcomer could open each named file, function, flag and test helper and find it as described, on the first try.
**Hard rule**: Check each claim in the code under `<root>`, test helpers and mocks included; every unverified dependency without a spike task, and every integration point the code needs that the set does not name, is a finding; each false claim cites the claim and the code.
**Reads**: the spec, the companions and the plan, for their claims; the code under `<root>`, the test folders, the integration points the set names.
