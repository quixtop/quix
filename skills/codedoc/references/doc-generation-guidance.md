# Documentation Generation & Advanced Workflows

Extended guidance for codedoc covering auto-generation tools, modern changelog management, and breaking change documentation.

---

## Auto-Generated vs Hand-Written Documentation

### When to Use Auto-Generation

| Tool | Language | Best For |
|------|----------|----------|
| **TypeDoc** | TypeScript | Library API reference from TSDoc comments |
| **Rustdoc** | Rust | Crate documentation from `///` comments |
| **pdoc** / **Sphinx** | Python | Module reference from docstrings |
| **Javadoc** | Java | Class/method reference |
| **Godoc** / **pkgsite** | Go | Package documentation from code comments |
| **Swagger/OpenAPI** | Any (REST APIs) | API endpoint reference from spec files |

### Decision Matrix

| Situation | Approach | Why |
|-----------|----------|-----|
| Public library API reference | Auto-generate | Stays in sync with code; readers expect consistent format |
| Internal module docs | Auto-generate if team > 3 | Enforces documentation discipline across contributors |
| Architecture overview | Hand-write | Auto-generators can't capture design intent or trade-offs |
| Getting started guide | Hand-write | Needs narrative flow, curated examples |
| Configuration reference | Auto-generate from schema | Single source of truth for config options |
| Tutorials / How-to guides | Hand-write | Requires pedagogical structure, not API listing |
| REST API docs | Generate from OpenAPI spec | Spec-first ensures docs match implementation |

### Integration Tips

- **Don't duplicate**: If auto-generating API docs, don't also hand-write the same reference. Link to the generated output.
- **CI integration**: Run doc generation in CI to catch broken doc comments before merge.
- **Example**: `typedoc --entryPointStrategy expand ./src --out docs/api`
- **Hybrid approach**: Auto-generate the API reference, hand-write the guides that link into it.

---

## Modern Changelog Workflows

The `git log --oneline | grep` approach works for quick ad-hoc changelogs but breaks down for releases. Consider these approaches for sustained projects:

### Conventional Commits

Standardized commit message format that enables automation:

```
feat: add user avatar upload
fix: resolve auth token refresh race condition
feat(api)!: change pagination response format

BREAKING CHANGE: pagination now returns `{ items, cursor }` instead of `{ data, page }`
```

**Prefixes**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, `build`

**Tooling that reads conventional commits**:
- **standard-version** / **release-please**: Auto-generate CHANGELOG.md + version bumps
- **semantic-release**: Fully automated npm publishing with changelog
- **git-cliff**: Language-agnostic changelog generator from conventional commits

### Changesets (for monorepos)

```bash
npx changeset          # Create a changeset describing your change
npx changeset version  # Bump versions + update changelogs
npx changeset publish  # Publish packages
```

Best for: monorepos with multiple publishable packages (e.g., design systems, SDK collections).

### Release-Please (GitHub-native)

GitHub Action that:
1. Watches for conventional commits on main
2. Opens a "Release PR" that accumulates changes
3. On merge, creates GitHub Release with auto-generated notes

Best for: GitHub-hosted projects wanting zero-config changelog automation.

### When to Use What

| Project Type | Recommended Approach |
|-------------|---------------------|
| Solo / small team, no releases | `git log` + manual CHANGELOG (existing approach) |
| Library with published versions | Conventional commits + release-please or standard-version |
| Monorepo with multiple packages | Changesets |
| Enterprise with compliance needs | Conventional commits + git-cliff (customizable templates) |

---

## Breaking Change Documentation

When a release includes breaking changes, documentation must help users migrate. This applies to libraries, APIs, CLI tools, and configuration formats.

### Deprecation Lifecycle

```
v2.1: Introduce new API + deprecation warning on old API
v2.2: Old API still works, warning in docs and runtime
v3.0: Old API removed, migration guide published
```

**Minimum deprecation period**: One major version or 3-6 months, whichever is longer.

### Migration Guide Template

```markdown
# Migrating from vX to vY

## Breaking Changes

### 1. [Change Title]

**What changed**: [Precise description]
**Why**: [Reason for the change]
**Before (vX)**:
\`\`\`javascript
// Old usage
const result = api.getData({ page: 1, limit: 10 });
// Returns: { data: [...], page: 1, totalPages: 5 }
\`\`\`

**After (vY)**:
\`\`\`javascript
// New usage
const result = api.getData({ cursor: null, limit: 10 });
// Returns: { items: [...], cursor: "abc123", hasMore: true }
\`\`\`

**Migration steps**:
1. Replace `page` parameter with `cursor` (use `null` for first page)
2. Update response handling: `data` -> `items`, `page`/`totalPages` -> `cursor`/`hasMore`
3. If using pagination UI, switch from page numbers to "Load More" pattern

### Automated Migration

If a codemod is available:
\`\`\`bash
npx @yourlib/codemod v2-to-v3
\`\`\`
```

### Breaking Change Checklist

When documenting a breaking change, verify:
- [ ] Change is listed in CHANGELOG under "Breaking Changes" (not just "Changed")
- [ ] Before/after code examples provided
- [ ] Migration steps are numbered and actionable
- [ ] Runtime deprecation warning added in prior version
- [ ] API docs updated to reflect new behavior
- [ ] Error messages reference the migration guide URL
