# Architecture Decision Record (ADR) Template

Use this template for significant design decisions during the specification phase. ADRs document the context, decision, and consequences of architectural choices.

---

## Template

```markdown
# ADR-NNN: [Decision Title]

## Status
Proposed | Accepted | Deprecated

## Context
[Forces at play - technical, project constraints]

## Decision
[Approach and rationale]

## Alternatives considered
[Option]
- How: [how it works, one line]
- Pros: [what it gains]
- Cons: [what it costs]
- Why rejected: [what it lacks or costs against the chosen one]

(A decision found in built code: `N/A — not recorded`.)

## Consequences
**Positive**: [Benefits]
**Negative**: [Trade-offs]
```

## When to Write an ADR

- Choosing between 2+ viable architectural approaches
- Adopting a new library, framework, or tool
- Changing an established pattern in the codebase
- Making a trade-off that future developers should understand

When evaluating multiple approaches, pair the ADR with Step 3's comparison
table (SKILL.md § Step 3: Design); its rejected rows are the ADR's
Alternatives considered.
