# JavaScript/TypeScript Test Examples (Jest, Vitest)

Comprehensive Jest/Vitest patterns including mocking, async tests, and describe blocks.

---

## Test Structure

```javascript
const { functionUnderTest } = require('./module');

describe('functionUnderTest', () => {
  describe('happy path', () => {
    it('returns expected result for normal input', () => {
      expect(functionUnderTest('valid')).toBe(expected);
    });
  });

  describe('edge cases', () => {
    it('handles empty input', () => {
      expect(functionUnderTest('')).toBe(default);
    });

    it('handles boundary value', () => {
      expect(functionUnderTest(MAX_VALUE)).toBe(boundary);
    });

    it('handles null/undefined', () => {
      expect(functionUnderTest(null)).toBeUndefined();
    });
  });

  describe('error cases', () => {
    it('throws for invalid input', () => {
      expect(() => functionUnderTest(-1)).toThrow('expected message');
    });
  });

  describe('with mocked dependencies', () => {
    beforeEach(() => {
      jest.mock('./external', () => ({
        service: jest.fn().mockResolvedValue({ data: 'mocked' })
      }));
    });

    it('works with mocked service', async () => {
      const result = await functionUnderTest('input');
      expect(result).toEqual(expectedWithMock);
    });
  });
});
```

## Test Improvement Patterns

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

## Running Tests

```bash
# Run all tests
npm test

# With coverage
npm test -- --coverage

# Watch mode
npm test -- --watch

# Specific file
npm test -- tests/module.test.js
```

## Coverage Analysis

```bash
# Count exports
grep -r "export.*function" src/ --include="*.js" --include="*.ts" | wc -l
grep -r "describe\|it\|test" tests/ --include="*.test.js" | wc -l

# Coverage report
npm test -- --coverage
```

## Detect Project Type

```bash
test -f jest.config.js || grep "jest" package.json
```

---

## Bun Test Runner

Bun includes a built-in test runner (`bun test`) that is Jest-compatible with faster execution. No extra dependencies needed.

### Configuration

```toml
# bunfig.toml (optional — Bun works zero-config)
[test]
preload = ["./tests/setup.ts"]   # Global setup
coverage = true                   # Enable coverage
coverageThreshold = { line = 80 } # Fail if below threshold
```

### Test Structure

```typescript
// math.test.ts — Jest-compatible API, runs with `bun test`
import { describe, it, expect, beforeEach, mock } from 'bun:test';

describe('add', () => {
  it('adds two numbers', () => {
    expect(add(1, 2)).toBe(3);
  });

  it('handles negative numbers', () => {
    expect(add(-1, -2)).toBe(-3);
  });
});
```

### Mocking

```typescript
import { mock, spyOn } from 'bun:test';

// Mock a module
mock.module('./database', () => ({
  getUser: mock(() => ({ id: 1, name: 'Test' })),
}));

// Spy on object methods
const spy = spyOn(console, 'log');
doSomething();
expect(spy).toHaveBeenCalledWith('expected output');
```

### Running Tests

```bash
# Run all tests
bun test

# Specific file
bun test tests/auth.test.ts

# Watch mode
bun test --watch

# With coverage
bun test --coverage

# Filter by test name (-t / --test-name-pattern; Bun has no Mocha-style --grep)
bun test -t "adds two"
```

### Key Differences from Jest

| Feature | Jest | Bun |
|---------|------|-----|
| Import syntax | `jest.fn()` | `mock()` from `bun:test` |
| Module mocking | `jest.mock('./mod')` | `mock.module('./mod', () => ...)` |
| Speed | ~5-15s startup | ~0.1-0.5s startup |
| Config | `jest.config.js` | `bunfig.toml` (optional) |
| Compatibility | Full ecosystem | Jest-compatible API, some edge cases differ |

---

## Snapshot Testing

Snapshot tests capture output and compare against a stored baseline. Useful for catching unintended changes in serialized output.

### When Snapshots Help

- Component render output (React/Vue component trees)
- API response structure validation
- Config file generation
- Error message formatting

### When Snapshots Hurt

- Large snapshots nobody reads during review (rubber-stamped updates)
- Frequently changing output (noisy diffs, constant updates)
- Testing implementation details instead of behavior

### Jest/Vitest Snapshots

```typescript
import { render } from '@testing-library/react';

it('renders user card', () => {
  const { container } = render(<UserCard name="Alice" role="admin" />);
  expect(container).toMatchSnapshot();
});

// Inline snapshots (preferred — visible in test file)
it('formats error message', () => {
  expect(formatError('not_found', 'User')).toMatchInlineSnapshot(
    `"Error: User not found"`
  );
});
```

### Snapshot Update Strategy

```bash
# Update all snapshots (review diff carefully!)
npx jest --updateSnapshot
npx vitest --update

# Bun
bun test --update-snapshots
```

**Rule**: Treat snapshot updates like code changes — review the diff, don't blindly update.
