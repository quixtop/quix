---
name: codedoc
author: shrix
description: "(shrix) Generate, verify, update, explain, and changelog code documentation — READMEs, API docs/docstrings, migration guides, release notes. Use when asked to document code, check docs against reality, explain a module, or write release notes."
metadata:
  version: "2.0"
  category: documentation
---

# Documentation Specialist

Generate, verify, and update code documentation.

## Modes

| Mode | Purpose |
|------|---------|
| **Generate** | Create new documentation |
| **Verify** | Check docs match code |
| **Update** | Sync docs with changes |
| **Explain** | Explain code in plain English |
| **Changelog** | Generate release notes |

---

## Quick Reference

| Doc Type | When to Update |
|----------|----------------|
| README | Feature changes, setup changes |
| API docs | Endpoint changes |
| Code comments | Complex logic changes |
| Architecture | Structural changes |
| Changelog | Before releases |

---

## Documentation Tiers

### Tier 1: Always Update
- `README.md` - User-facing features
- `docs/reqs.md` - Requirements
- `docs/status.md` - Implementation status

### Tier 2: When Relevant
- `docs/arch/*.md` - Architecture
- `docs/decisions.md` - Design decisions
- API documentation

### Tier 3: Reference Only
- `docs/refs/*.md` - API reference
- `docs/user/*.md` - User guides

---

## Generate Mode

### README Template

```markdown
# Project Name

Brief description (1-2 sentences).

## Features
- Feature 1: Brief description
- Feature 2: Brief description

## Installation
\`\`\`bash
npm install
\`\`\`

## Quick Start
\`\`\`bash
npm start
\`\`\`

## Configuration
| Variable | Description | Default |
|----------|-------------|---------|
| `API_KEY` | API key | - |

## Development
\`\`\`bash
npm install  # Setup
npm test     # Test
npm run build # Build
\`\`\`

## License
[License type]
```

### Code Documentation

**JavaScript (JSDoc)**:
```javascript
/**
 * Brief description of function.
 *
 * @param {string} param1 - Description
 * @param {Object} options - Configuration
 * @returns {Promise<Result>} Description
 * @throws {Error} When condition occurs
 *
 * @example
 * const result = await fn('value', { flag: true });
 */
```

**Python (docstrings)**:
```python
def function_name(param1: str, options: dict = None) -> Result:
    """Brief description.

    Args:
        param1: Description
        options: Configuration options

    Returns:
        Result object with processed data

    Raises:
        ValueError: When param1 is invalid

    Example:
        >>> result = function_name('value')
    """
```

**Go**:
```go
// FunctionName does brief description.
//
// Parameters:
//   - param1: description
//
// Returns processed result or error.
func FunctionName(param1 string) (Result, error) {
```

---

## Verify Mode

### Documentation Drift Detection

```bash
# Find functions without docs
grep -r "^function\|^const.*=.*=>" src/ --include="*.js" | head -20

# Check doc coverage (find is shell-agnostic — ** globs need zsh/globstar)
find src \( -name '*.js' -o -name '*.py' \) -exec grep -c "@param\|Args:" {} + 2>/dev/null
```

### Verification Checklist

```markdown
## Documentation Verification

### README.md
- [ ] Installation steps work
- [ ] Quick start example runs
- [ ] All features documented
- [ ] Links not broken

### API Documentation
- [ ] All endpoints documented
- [ ] Request/response examples accurate
- [ ] Error codes documented

### Code Comments
- [ ] Public functions documented
- [ ] Complex logic explained
- [ ] Examples provided
```

---

## Update Mode

### Change Detection

```bash
# Find recently modified files
git diff --name-only HEAD~5 | grep -v "test\|spec"

# Check if docs were updated
git diff --name-only HEAD~5 | grep -E "\.md$|docs/"
```

### Update Workflow

1. **Identify changes** — what code changed
2. **Impact assessment** — what docs are affected
3. **Update docs**
4. **Verify accuracy** — test examples

### Update Template

```markdown
## Documentation Update: [Feature]

### Changed Code
- `src/module.js`: [What changed]

### Docs to Update
- [ ] README.md: [Section]
- [ ] docs/api.md: [Endpoint]

### Verification
- [ ] Examples tested
- [ ] Links verified
```

---

## Explain Mode

### Code Explanation Template

```markdown
## What This Code Does

**File**: `src/module.js`
**Purpose**: [High-level purpose]

### How It Works

1. **[Step 1]**: [Explanation]
2. **[Step 2]**: [Explanation]
3. **[Step 3]**: [Explanation]

### Key Concepts

- **[Concept 1]**: [Plain English explanation]
- **[Concept 2]**: [Plain English explanation]

### Example Usage

[Simple example with expected output]
```

---

## Changelog Mode

### Keep a Changelog Format

```markdown
# Changelog

## [Unreleased]

### Added
- New feature description

### Changed
- Modified behavior description

### Fixed
- Bug fix description

### Removed
- Removed feature description

## [1.0.0] - YYYY-MM-DD

### Added
- Initial release features
```

### Commit Analysis

```bash
# Get commits since last tag
git log $(git describe --tags --abbrev=0)..HEAD --oneline

# Group by type
git log --oneline | grep -i "feat\|fix\|chore\|docs"
```

---

## Skill Integration

### Workflow Position

```
implement → test → codedoc
                 ↓
            (deploy)
```

(`implement` is currently disabled — in practice the live upstream neighbors
are `/spec`, `/test`, and `/refactor`.)

### When to Use

| Trigger | Mode |
|---------|------|
| New feature complete | Generate |
| Before PR/merge | Verify |
| Code changes merged | Update |
| Before release | Changelog |
| Onboarding help | Explain |

### Related Skills

| Skill | Relationship |
|-------|--------------|
| `doclint` (disabled) | Cross-doc consistency validation |
| `implement` (disabled) | Docs follow implementation |
| `spec` | Feature specs inform docs |

---

## Best Practices

### What to Document

✅ **Always Document**:
- Public APIs
- Configuration options
- Setup procedures
- Complex algorithms

❌ **Avoid Documenting**:
- Self-explanatory code
- Obvious variable names
- Comments that repeat code

### Good vs Bad

**Good Comment**:
```javascript
// Use exponential backoff to avoid overwhelming server
// Max 5 retries with 2^n second delays
```

**Bad Comment**:
```javascript
// Increment i by 1
i++;
```

---

## Quality Indicators

**Good Documentation**:
✅ All public APIs documented
✅ Examples that run
✅ Up-to-date with code
✅ Covers error scenarios

**Red Flags**:
❌ TODO comments in docs
❌ Broken links
❌ Outdated examples
❌ Missing error documentation

---

## Extended References

| Topic | Reference File |
|-------|---------------|
| Auto-generated vs hand-written docs | `references/doc-generation-guidance.md` |
| Modern changelog workflows | `references/doc-generation-guidance.md` |
| Breaking change documentation | `references/doc-generation-guidance.md` |
