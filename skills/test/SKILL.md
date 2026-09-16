---
name: test
author: shrix
description: "(shrix) Generate tests and analyze test coverage (Python/JS/Go). Use when asked to write/add tests, find coverage gaps, or add a regression test for a bug — NOT for merely running an existing test suite."
metadata:
  version: "2.0"
  category: testing
---

# Test Generator

Generate tests and analyze coverage for comprehensive testing.

## Modes

| Mode | Purpose |
|------|---------|
| **Generate** | Create tests for provided code |
| **Analyze** | Find coverage gaps and opportunities |
| **Augment** | Add tests to existing suite |

---

## Quick Reference

| Framework | Language | Test File Pattern |
|-----------|----------|-------------------|
| pytest | Python | `test_*.py`, `*_test.py` |
| Jest / Bun / Vitest | JavaScript | `*.test.js`, `*.spec.js` |
| Go testing | Go | `*_test.go` |

---

## Testing Philosophy

### The Testing Pyramid

```
        ┌───────────┐
        │    E2E    │  ← Few, slow, expensive
        │  (10-20%) │
        ├───────────┤
        │Integration│  ← Some, moderate speed
        │  (20-30%) │
        ├───────────┤
        │   Unit    │  ← Many, fast, cheap
        │  (50-70%) │
        └───────────┘
```

**Rule of thumb**: If you're debugging with `console.log`, you're missing a test.

### Core Principles

| Principle | Meaning |
|-----------|---------|
| **F.I.R.S.T** | Fast, Independent, Repeatable, Self-validating, Timely |
| **AAA Pattern** | Arrange → Act → Assert |
| **One assertion focus** | Test one behavior per test |
| **Test behavior, not implementation** | Tests survive refactoring |

### When NOT to Test

Don't waste time testing:
- Trivial getters/setters (no logic)
- Framework internals (React's useState, Express routing)
- Third-party library behavior
- One-time migration scripts
- Generated code (protobuf, GraphQL types)

### Test-Driven Debugging

```
Bug reported → Write failing test first → Fix bug → Test passes → Never regresses
```

**Every bug is a missing test.** Before fixing, write the test that would have caught it.

---

## Generate Mode

### Test Structure Template

For each function/method:

```
1. Happy path - Normal expected usage
2. Edge cases - Boundary values, empty inputs
3. Error cases - Invalid inputs, exceptions
4. Mocks - External dependencies isolated
```

Language-specific test patterns with full examples for each framework:

- **📚 [references/python-examples.md](references/python-examples.md)** — pytest patterns, fixtures, mocking, coverage commands
- **📚 [references/javascript-examples.md](references/javascript-examples.md)** — Jest/Vitest patterns, describe blocks, async mocking
- **📚 [references/go-examples.md](references/go-examples.md)** — Table-driven tests, standard testing package

---

## Analyze Mode

### Step 1: Detect Project Type

```bash
# Python
test -f pytest.ini || test -f pyproject.toml

# JavaScript
test -f jest.config.js || grep "jest" package.json

# Go
ls *_test.go 2>/dev/null

# Rust
test -f Cargo.toml
```

### Step 2: Identify Untested Code

**Python**:
```bash
# Count functions
grep -r "^def " src/ --include="*.py" | wc -l
grep -r "^def test_" tests/ --include="*.py" | wc -l
```

**JavaScript**:
```bash
# Count exports
grep -r "export.*function" src/ --include="*.js" --include="*.ts" | wc -l
grep -r "describe\|it\|test" tests/ --include="*.test.js" | wc -l
```

### Step 3: Coverage Report

```bash
# Python
pytest --cov=src --cov-report=term-missing

# JavaScript
npm test -- --coverage

# Go
go test -cover ./...
```

### Step 4: Gap Analysis Report

```markdown
# Test Coverage Analysis

## Summary
- Production functions: X
- Test functions: Y
- Coverage ratio: Z%

## Untested Functions

| File | Function | Priority |
|------|----------|----------|
| src/auth.py | validate_token | HIGH |
| src/data.py | parse_input | HIGH |
| src/utils.py | format_date | LOW |

## Recommended Test Order
1. [Critical path function] - Used by N other functions
2. [Security function] - Handles authentication
3. [Data function] - Parses user input
```

---

## Critical Path Analysis

### High-Priority Testing Gaps

| Category | Why Critical | Action |
|----------|--------------|--------|
| Auth functions | Security boundary | Test immediately |
| Data validation | User input handling | Test all paths |
| API endpoints | External interface | Full coverage |
| Error handlers | Failure modes | Test edge cases |

### Risk-Based Prioritization

```
Priority 1 (CRITICAL):
- Authentication/authorization
- Payment/billing logic
- Data validation at boundaries

Priority 2 (HIGH):
- Core business logic
- API endpoints
- Database operations

Priority 3 (MEDIUM):
- Utility functions
- Formatting/display logic
- Configuration handling

Priority 4 (LOW):
- Constants/enums
- Simple getters/setters
- Logging functions
```

---

## Augment Mode

### Adding Tests to Existing Suite

1. **Identify gaps** using coverage report
2. **Check existing patterns** in test files
3. **Follow naming conventions** from existing tests
4. **Add missing scenarios**:
   - Untested branches
   - Error conditions
   - Edge cases

### Test Improvement Patterns

```javascript
// Before: Only happy path
it('returns data', () => {
  expect(fetch()).toBe(data);
});

// After: Comprehensive coverage
describe('fetch', () => {
  it('returns data for valid request', () => {...});
  it('handles empty response', () => {...});
  it('retries on timeout', () => {...});
  it('throws on auth failure', () => {...});
  it('handles network error', () => {...});
});
```

---

## Skill Integration

### Workflow Position

```
spec → implement → test → codedoc
              ↓
          security
```

(`implement` and `security` are currently disabled — the live neighbors are
`/spec`, `/refactor`, and `/codedoc`.)

### When to Use

| Trigger | Mode |
|---------|------|
| New code written | Generate |
| Before PR/merge | Analyze |
| Coverage dropping | Augment |
| Bug found | Add regression test |

### Related Skills

| Skill | Relationship |
|-------|--------------|
| `implement` (disabled) | Tests follow implementation |
| `refactor` | Verify behavior preserved |
| `security` (disabled) | Security test cases |

---

## Running Tests

Language-specific run/coverage commands are included in each reference file:
- [references/python-examples.md](references/python-examples.md) — pytest commands
- [references/javascript-examples.md](references/javascript-examples.md) — npm test / Jest commands
- [references/go-examples.md](references/go-examples.md) — go test commands

---

## Quality Indicators

**Good Test Suite**:
✅ 80%+ code coverage
✅ Tests for all public functions
✅ Edge cases covered
✅ Error scenarios tested
✅ Fast execution (<30s)
✅ No flaky tests

**Red Flags**:
❌ Coverage below 50%
❌ Only happy path tests
❌ No error case tests
❌ Tests depend on order
❌ Tests modify shared state
❌ Slow tests (>5min)

---

## Bun Test Runner

Built-in, Jest-compatible test runner with ~0.1s startup (vs Jest's ~5-15s). Zero dependencies.

```typescript
import { describe, it, expect } from 'bun:test';

describe('auth', () => {
  it('validates token', () => {
    expect(validateToken('valid-token')).toBe(true);
  });
});
```

Run: `bun test`, `bun test --coverage`, `bun test --watch`, `bun test -t "auth"` (Bun filters by test name with `-t`/`--test-name-pattern`, not Mocha's `--grep`)

> See [references/javascript-examples.md](references/javascript-examples.md) for Bun mocking, config, and differences from Jest.

---

## Snapshot Testing

Captures serialized output and compares against a stored baseline.

- **Helps**: Component render output, API response structures, config generation
- **Hurts**: Large snapshots nobody reviews, frequently changing output, implementation detail testing

```typescript
// Inline snapshot (preferred — visible in test file)
it('formats error', () => {
  expect(formatError('not_found')).toMatchInlineSnapshot(`"Error: not found"`);
});
```

**Rule**: Treat snapshot updates like code changes — review the diff, never blindly update.

> See [references/javascript-examples.md](references/javascript-examples.md) for full snapshot patterns and update strategies.

---

## Contract Testing

Verifies that services agree on API contracts without running all services simultaneously. The consumer defines expected request/response pairs; the provider verifies it can fulfill them. Breaking changes are caught before deployment.

**When to use**: Multiple teams own different services, API changes risk breaking consumers, deployment independence required.

| Tool | Ecosystem | Approach |
|------|-----------|----------|
| **Pact** | JS, Python, Go, JVM, .NET | Consumer-driven, Pact Broker for sharing |
| **Spring Cloud Contract** | JVM (Spring Boot) | Provider-driven, Groovy/YAML DSL |

> See [references/contract-testing.md](references/contract-testing.md) for Pact consumer/provider examples (JS + Python), Spring Cloud Contract, and decision guidance.

---

## Testing Real-Time Features

Patterns for testing WebSockets, SSE, async generators, and streaming responses.

| Feature | Key Challenge | Testing Approach |
|---------|---------------|-----------------|
| WebSocket | Bidirectional, connection lifecycle | Spin up server on port 0, test message flow, verify cleanup |
| SSE | Unidirectional stream, reconnection | Read stream with fetch reader, collect N events, cancel |
| Async generators | Yield/return semantics | Mock data source, collect all yielded values |
| Streaming HTTP | Chunked transfer, backpressure | Parse NDJSON lines from response body reader |

> See [references/realtime-testing.md](references/realtime-testing.md) for concrete examples in Node.js and Python.
