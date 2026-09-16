---
name: start
author: shrix
description: "(shrix) Establish comprehensive project context by analyzing codebase patterns, architecture, and conventions. Use when onboarding to a new/unfamiliar codebase or (re)building a mental model of a project."
metadata:
  version: "2.0"
  category: discovery
---

# Project Context Initializer

Establish comprehensive project context by analyzing codebase patterns, structure, and conventions.

## Quick Reference

| Phase | Time | Output |
|-------|------|--------|
| 1. Guidelines | ~2 min | Project rules |
| 2. Structure | ~2 min | File organization |
| 3. Stack | ~2 min | Technologies used |
| 4. Patterns | ~3 min | Coding conventions |
| 5. Workflow | ~2 min | Dev processes |

---

## Phase 1: Locate Project Guidelines

Search for project-specific AI agent guidelines:

| File | Purpose |
|------|---------|
| `CLAUDE.md`, `AGENTS.md`, `AI.md` | AI-specific instructions |
| `.claude/` directory | Agent configuration |
| `README.md` | May contain guidelines |
| `CONTRIBUTING.md` | Development guidelines |

**Action**: Read ALL that exist. Follow ALL referenced documentation.

---

## Phase 2: Project Structure

### Directory Analysis

```bash
# Get top-level structure
ls -la

# Find source directories
ls -la src/ app/ lib/ 2>/dev/null

# Check for docs
ls docs/ doc/ documentation/ 2>/dev/null

# Check for tests
ls tests/ test/ __tests__/ spec/ 2>/dev/null
```

### Key Files to Check

| File | Purpose |
|------|---------|
| `README.md` | Project overview |
| `package.json` / `pyproject.toml` | Dependencies |
| `.env.example` | Environment variables |
| `Makefile` / `justfile` | Common commands |

### Structure Template

```
📁 Project Structure:

Root:
├── src/ or app/     → Source code
├── tests/           → Test files
├── docs/            → Documentation
├── scripts/         → Utility scripts
└── config/          → Configuration

Key Patterns:
- [Pattern 1]
- [Pattern 2]
```

---

## Phase 3: Technology Stack

### Auto-Detection

**JavaScript/TypeScript**:
```bash
cat package.json | grep -A 20 '"dependencies"'
grep -l "react\|vue\|angular\|svelte" package.json
```

**Python**:
```bash
cat requirements.txt pyproject.toml 2>/dev/null | head -30
grep -l "django\|flask\|fastapi" requirements.txt pyproject.toml 2>/dev/null
```

**Go**:
```bash
cat go.mod | head -20
```

### Stack Summary Template

```
🔧 Technology Stack:

Language: [Primary language]
Framework: [Web framework]
Database: [DB technology]
Frontend: [UI framework]
Testing: [Test framework]
Build: [Build tools]
```

---

## Phase 4: Coding Patterns

### Pattern Discovery

```bash
# Find common patterns in source
grep -r "class.*extends\|export default\|module.exports" src/ 2>/dev/null | head -10

# Check naming conventions (find is shell-agnostic — ** globs need zsh/globstar)
find src \( -name '*.js' -o -name '*.py' \) 2>/dev/null | head -20

# Find utility patterns
cat src/utils/*.js src/utils/*.py 2>/dev/null | head -50
```

### Pattern Template

```
📐 Coding Patterns:

Naming:
- Files: [camelCase/snake_case/kebab-case]
- Functions: [camelCase/snake_case]
- Classes: [PascalCase]
- Constants: [UPPER_SNAKE]

Structure:
- Components: [Pattern]
- Services: [Pattern]
- Utils: [Pattern]

Error Handling: [Pattern used]
Logging: [Pattern used]
```

---

## Phase 5: Development Workflow

### Command Discovery

```bash
# NPM scripts
cat package.json | grep -A 30 '"scripts"'

# Makefile targets
grep "^[a-z].*:" Makefile 2>/dev/null

# Common dev commands
cat README.md | grep -A 5 "## Development\|## Getting Started"
```

### Workflow Template

```
🔄 Development Workflow:

Setup:
$ [install command]
$ [env setup]

Development:
$ [dev server command]
$ [watch command]

Testing:
$ [test command]
$ [coverage command]

Build:
$ [build command]
$ [deploy command]
```

---

## Output Format

### Complete Context Summary

```markdown
# Project Context: [Project Name]

## Overview
[1-2 sentence description]

## Structure
[Directory tree]

## Stack
[Technologies]

## Patterns
[Coding conventions]

## Workflow
[Key commands]

## Key Files
- [Entry point]
- [Main config]
- [Core logic location]

## Notes
- [Important convention 1]
- [Important convention 2]
```

---

## Skill Integration

### Post-Discovery Skills

| Next Need | Use Skill |
|-----------|-----------|
| Plan new feature | `spec` |
| Understand a feature/module | `codedoc` (explain mode) |
| Quick changes | `build` (disabled) |
| Code quality | `refactor` |
| Security review | `security` (disabled) |

### Workflow Position

```
start → spec/build → implement → test
  ↓
(context established for all future work)
```

(`build` and `implement` are currently disabled — the live chain is
`/start → /spec → /test → /codedoc`, with `/refactor` for quality passes.)

---

## Quality Indicators

**Well-Structured Project**:
✅ Clear directory organization
✅ Documented entry points
✅ Consistent naming
✅ Test coverage
✅ Configuration separated

**Needs Attention**:
❌ Flat file structure
❌ Mixed naming conventions
❌ No clear entry point
❌ Missing documentation

---

## Project Type Classification

Run this early in Phase 2 to narrow which patterns to search for:

```
Is there a UI? (src/components/, templates/, public/index.html)
├── YES → Is there also a server? (src/server/, api/, routes/)
│   ├── YES → Full-stack application
│   └── NO  → Frontend application (SPA, static site)
└── NO  → Is it importable? (exports in index.*, "main" in package.json)
    ├── YES → Library / Package
    └── NO  → Backend service / CLI tool / Infrastructure
```

**Why classify first?** Each type has different critical files to read, different patterns to search for, and different "done" criteria for onboarding.

---

## Extended Discovery

**📚 For detailed guidance, see: [references/extended-discovery.md](references/extended-discovery.md)**

| Discovery Step | What to Check | Why |
|----------------|---------------|-----|
| **Dev environment** | tsconfig.json, ESLint, Prettier, pre-commit hooks, CI workflows | Know what will reject your code before you write it |
| **External dependencies** | .env.example, API client configs, SDK imports | Map the external services the project relies on — affects local dev setup and blast radius |
