---
name: refactor
author: shrix
description: "(shrix) Refactoring, performance optimization, code maintenance, architecture consistency, and structured code review. Use when code is slow, has smells/duplication/dead code, needs pattern consistency, or before a PR review."
metadata:
  version: "2.2"
  category: maintenance
---

# Code Refactoring Specialist

Performance optimization, code maintenance, and architecture consistency.

## Modes

| Mode | Purpose |
|------|---------|
| **Performance** | Speed, memory, efficiency |
| **Maintenance** | Dead code, duplicates, organization |
| **Refactoring** | Quality improvements |
| **Architecture** | Pattern consistency |
| **Code Review** | Structured review |

---

## The Golden Rules

1. **Behavior is preserved** - Refactoring doesn't change what the code does, only how
2. **Small steps** - Make tiny changes, test after each
3. **Version control is your friend** - Commit before and after each safe state
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

**📚 For detailed before/after examples, see: [references/code-smells.md](references/code-smells.md)**

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

## Performance Mode

### Analysis Approach

```markdown
## Performance Analysis

**Target**: [File/Function]

### Metrics

| Metric | Current | Target |
|--------|---------|--------|
| Response time | Xms | <Yms |
| Memory usage | X MB | <Y MB |
| Bundle size | X KB | <Y KB |

### Bottlenecks Found

1. **[Location]**: [Issue]
   - Impact: [High/Medium/Low]
   - Fix: [Recommendation]
```

### Performance Fix Example

```javascript
// Before: O(n²)
for (let i = 0; i < arr.length; i++) {
  for (let j = 0; j < arr.length; j++) {
    // ...
  }
}

// After: O(n)
const map = new Map(arr.map(x => [x.id, x]));
for (let i = 0; i < arr.length; i++) {
  const item = map.get(arr[i].id);
}
```

### Web Performance (Core Web Vitals)

Thresholds live in `references/frontend-performance.md` (single source of truth —
it has the current metric set: LCP < 2.5s, INP < 200ms, CLS < 0.1, plus
supporting metrics). Note: FID was replaced by INP as a Core Web Vital in
March 2024 — don't quote FID targets.

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

**📚 For pattern examples with code, see: [references/design-patterns.md](references/design-patterns.md)**

### When to Apply Patterns

| Problem | Pattern | Use When |
|---------|---------|----------|
| Multiple conditionals | Strategy | Algorithm varies by type |
| Sequential validation | Chain of Responsibility | Multiple handlers, one succeeds |
| Object creation logic | Factory | Complex instantiation |
| Missing objects | Null Object | Avoid null checks |

---

## Safe Refactoring Process

```
1. PREPARE
   - Ensure tests exist (write them if missing)
   - Commit current state
   - Create feature branch

2. IDENTIFY
   - Find the code smell to address
   - Understand what the code does
   - Plan the refactoring

3. REFACTOR (small steps)
   - Make one small change
   - Run tests
   - Commit if tests pass
   - Repeat

4. VERIFY
   - All tests pass
   - Manual testing if needed
   - Performance unchanged or improved

5. CLEAN UP
   - Update comments
   - Update documentation
   - Final commit
```

---

## Code Review Mode

### Review Template

```markdown
## Code Review: [PR/Feature Name]

### Summary
[Brief description of changes]

### Strengths
- ✅ [Positive aspect 1]
- ✅ [Positive aspect 2]

### Issues

**Critical** (Must Fix):
1. [Issue]: [Location] - [Why it matters]

**Suggested** (Should Fix):
2. [Issue]: [Location] - [Recommendation]

**Nitpicks** (Consider):
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
- [ ] All tests pass

---

## Skill Integration

### Workflow Position

```
implement → test → refactor
                ↓
            security
```

(`implement` and `security` are currently disabled — the live neighbors are
`/test`, `/spec`, and `/codedoc`.)

### When to Use

| Trigger | Mode |
|---------|------|
| Slow performance | Performance |
| Code smell | Maintenance |
| Before major feature | Architecture |
| PR review | Code Review |
| Technical debt | Refactoring |

### Related Skills

| Skill | Relationship |
|-------|--------------|
| `test` | Verify behavior preserved |
| `security` (disabled) | Security improvements |
| `deps` (disabled) | Import optimization |

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
| **[references/async-migration.md](references/async-migration.md)** | Migrating callback → Promise → async/await (step-by-step with pitfalls) |
| **[references/frontend-performance.md](references/frontend-performance.md)** | Bundle size, tree-shaking, code splitting, lazy loading, Core Web Vitals optimization |

---

## Test-Driven Refactoring Mini-Workflow

Every atomic refactoring change should follow this exact cycle:

```
1. RUN TESTS → establish green baseline
2. MAKE ONE CHANGE → smallest possible refactor step
3. RUN TESTS → verify still green
   - Green? → COMMIT → go to step 2
   - Red? → REVERT the change → rethink approach → go to step 1
```

**Why run tests BEFORE the change?** If tests are already failing, you need to know that before you start — otherwise you can't tell if your refactoring broke something or it was already broken.
