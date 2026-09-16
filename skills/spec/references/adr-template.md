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

## Consequences
**Positive**: [Benefits]
**Negative**: [Trade-offs]
```

## When to Write an ADR

- Choosing between 2+ viable architectural approaches
- Adopting a new library, framework, or tool
- Changing an established pattern in the codebase
- Making a trade-off that future developers should understand

## Comparative Analysis Format

Use this alongside the ADR when evaluating multiple approaches:

```
Approach Comparison:

| Criterion   | Approach 1  | Approach 2  | Approach 3  |
|-------------|-------------|-------------|-------------|
| UX          | ****        | ***         | *****       |
| Complexity  | ** (High)   | ****(Low)   | ***(Med)    |
| Maintenance | ****        | ***         | *****       |

**Recommendation**: Approach [N]
**Reasoning**: [Why best fit for this project]
```
