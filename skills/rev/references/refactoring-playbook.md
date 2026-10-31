# Refactoring playbook — the HOW behind `/rev`

Reference material only. `/rev` owns WHEN a refactor happens and the loop
it runs in; this file is the catalogue it reaches for at step 3. It is not a
skill and carries no frontmatter — a second `name:` in the tree would make
`skillsync` see a skill that does not exist.

Code maintenance and architecture consistency (performance optimization is `/tune`'s).

## Modes

| Mode | Purpose |
|------|---------|
| **Performance** | → `/tune` — measured optimization toward a target is tune's |
| **Maintenance** | Dead code, duplicates, organization |
| **Refactoring** | Quality improvements |
| **Architecture** | Pattern consistency |
| **Code Review** | Structured review |

---

## The Golden Rules

1. **Behavior is preserved** - Refactoring doesn't change what the code does, only how
2. **Small steps** - Make tiny changes, and after each run the tests it affects — tier the diff with `~/.agents/skills/_shared/references/test-runs.md`'s table, never the whole suite; inside a `/rev` fix round, the round's one batch is the step
3. **Checkpoint every safe state** - save each green state as a patch OUTSIDE the work tree, new untracked files included (they are often the failing-first tests), and reverts to that:
   `{ git diff --binary BASE; git ls-files -o --exclude-standard -z | xargs -0 -n1 git diff --binary --no-index /dev/null; } > "$TMPDIR/rev-green.patch"`
   (`git diff BASE` alone omits untracked files, and a patch written into the repo becomes one)
4. **Tests are essential** - Without tests, you're not refactoring, you're editing
5. **One thing at a time** - Don't mix refactoring with feature changes

### When NOT to Refactor

- Code that works and won't change again (if it ain't broke...)
- Critical production code without tests (add tests first)
- When you're under a tight deadline
- "Just because" - need a clear purpose

---

## Common Refactoring Operations

| Operation | Description |
|-----------|-------------|
| Extract Method | Turn code fragment into method |
| Extract Class | Move behavior to new class |
| Inline Method | Move method body back to caller |
| Pull Up Method | Move method to superclass |
| Push Down Method | Move method to subclass |
| Rename Method/Variable | Improve clarity |
| Introduce Parameter Object | Group related parameters |
| Replace Conditional with Polymorphism | Use polymorphism instead of switch/if |
| Replace Magic Number with Constant | Named constants |
| Replace Nested Conditional with Guard Clauses | Early returns |

---

## Code Smells & Fixes

**📚 For detailed before/after examples, see: [code-smells.md](code-smells.md)**

### Quick Reference

| # | Smell | Detection | Fix |
|---|-------|-----------|-----|
| 1 | Long Method | > 50 lines | Extract focused functions |
| 2 | Duplicated Code | Similar patterns | Extract common logic |
| 3 | Large Class | God object | Single responsibility |
| 4 | Long Parameter List | > 4 params | Parameter object |
| 5 | Nested Conditionals | Arrow code | Guard clauses |
| 6 | Magic Numbers | Hardcoded values | Named constants |
| 7 | Feature Envy | Uses other object's data | Move to data owner |
| 8 | Dead Code | Unused code | Delete it |
| 9 | Primitive Obsession | Primitives for concepts | Value objects |
| 10 | Inappropriate Intimacy | Deep object access | Ask, don't tell |

---

## Performance Mode — hand off to `/tune`

Measured optimization (speed, memory, bundle size, Core Web Vitals) belongs to
`/tune`: it sets the goal, measures before and after, and keeps only what moves
the number. rev fixes a performance BUG that review finds — an N+1 query, an
O(n²) loop over unbounded input, a blocking call on a hot path — like any other
finding; it never runs an open-ended speed pass.

---

## Maintenance Mode

### Dead Code Detection

```bash
# Find unused functions / dead code (Python) — use a real analyzer, not grep:
# grep can't do this correctly (a definition always matches itself), and PCRE
# grep isn't available on stock macOS anyway.
vulture src/            # or: ruff check --select F401,F811 src/

# Find unused exports (JavaScript/TypeScript)
npx knip                # or: npx ts-prune

# Find unused DEPENDENCIES in package.json (different job than unused exports)
npx depcheck

# Find commented code
grep -r "^[[:space:]]*#.*def \|^[[:space:]]*//" src/
```

### Maintenance Report

```markdown
## Code Maintenance Report

### Dead Code Found

| Type | Location | Safe to Remove? |
|------|----------|-----------------|
| Function | src/utils.js:45 | ✅ No references |
| Variable | src/config.js:12 | ⚠️ Check tests |

### Duplicate Patterns

| Pattern | Locations | Action |
|---------|-----------|--------|
| Error handling | 5 files | Extract to utility |
| Fetch wrapper | 3 files | Create shared service |

**🚨 NEVER delete without confirmation - LIST ALL FINDINGS FIRST**
```

---

## Architecture Mode

### Pattern Consistency Check

```bash
# Find different patterns for same thing
grep -r "fetch\|axios\|got\|request" src/ --include="*.js" | grep -v node_modules

# Check error handling patterns
grep -r "try\|catch\|throw" src/ --include="*.js" | head -20

# Check logging patterns
grep -r "console\.\|logger\.\|log\(" src/ --include="*.js" | head -20
```

### Architecture Report

```markdown
## Architecture Consistency Report

### Pattern Inventory

| Pattern | Expected | Found | Consistent? |
|---------|----------|-------|-------------|
| HTTP client | axios | axios, fetch | ❌ Mixed |
| Error handling | try/catch | varies | ⚠️ Inconsistent |
| Logging | logger.* | console.* | ❌ Wrong pattern |

### Recommendations

1. **Standardize HTTP**: Use axios everywhere
2. **Error handling**: Create shared error handler
3. **Logging**: Replace console.* with logger.*
```

---

## Design Patterns for Refactoring

**📚 For pattern examples with code, see: [design-patterns.md](design-patterns.md)**

### When to Apply Patterns

| Problem | Pattern | Use When |
|---------|---------|----------|
| Multiple conditionals | Strategy | Algorithm varies by type |
| Sequential validation | Chain of Responsibility | Multiple handlers, one succeeds |
| Object creation logic | Factory | Complex instantiation |
| Missing objects | Null Object | Avoid null checks |

---

## Code Review Mode

> ⚠️ SUPERSEDED as a process: `/rev` owns reviewing (its SKILL.md, loop
> step 1). Never self-review against the template below — it survives only as
> a REPORT SHAPE for presenting findings once they exist.

### Review Template

```markdown
## Code Review: [PR/Feature Name]

### Summary
[Brief description of changes]

### Strengths
- ✅ [Positive aspect 1]
- ✅ [Positive aspect 2]

### Issues

**Critical**:
1. [Issue]: [Location] - [Why it matters]

**Important**:
2. [Issue]: [Location] - [Recommendation]

**Minor**:
3. [Issue]: [Location] - [Suggestion]

### Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing done

### Verdict
[ ] ✅ Approve
[ ] ⚠️ Approve with comments
[ ] ❌ Request changes
```

---

## Refactoring Checklist

### Code Quality
- [ ] Functions are small (< 50 lines)
- [ ] Functions do one thing
- [ ] No duplicated code
- [ ] Descriptive names (variables, functions, classes)
- [ ] No magic numbers/strings
- [ ] Dead code removed

### Structure
- [ ] Related code is together
- [ ] Clear module boundaries
- [ ] Dependencies flow in one direction
- [ ] No circular dependencies

### Type Safety
- [ ] Types defined for all public APIs
- [ ] No `any` types without justification
- [ ] Nullable types explicitly marked

### Testing
- [ ] Refactored code is tested
- [ ] Tests cover edge cases
- [ ] The affected tests pass (`test-runs.md`)

---

## Quality Indicators

**Good Code**:
✅ Functions < 50 lines
✅ Nesting depth < 4
✅ No magic numbers
✅ Consistent patterns
✅ No dead code

**Red Flags**:
❌ Functions > 100 lines
❌ Duplicate code blocks
❌ Mixed patterns
❌ Commented-out code
❌ Hardcoded values

---

## Additional References

| Guide | When to Use |
|-------|-------------|
| **[async-migration.md](async-migration.md)** | Migrating callback → Promise → async/await (step-by-step with pitfalls) |
| `/tune` (its `ui performance` profile) | Bundle size, code splitting, lazy loading, Core Web Vitals — measured optimization is tune's |

---

## Test-Driven Refactoring Mini-Workflow

Every atomic refactoring change should follow this exact cycle:

```
1. RUN THE AFFECTED TESTS → establish green baseline (in /rev: its pre-flight baseline)
2. MAKE ONE CHANGE → smallest possible refactor step
3. RUN THE AFFECTED TESTS → verify still green
   - Green? → CHECKPOINT (Golden Rule 3) → go to step 2
   - Red? → REVERT the change → rethink approach → go to step 1
4. BEFORE CLOSING → performance unchanged or improved
```

**Why run tests BEFORE the change?** If tests are already failing, you need to know that before you start — otherwise you can't tell if your refactoring broke something or it was already broken.
