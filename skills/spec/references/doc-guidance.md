# spec — changelogs, generated API docs and breaking changes
<!-- author: shrix -->

READ for `/spec changelog`, or when a project's API reference is generated.

## Generated vs hand-written

| doc | approach |
|---|---|
| library or REST API reference | generate it (TypeDoc, pdoc/Sphinx, Rustdoc, godoc, OpenAPI) and link to the output; never hand-write the same reference |
| architecture, getting started, tutorials | hand-write: generators cannot carry intent or trade-offs |
| configuration reference | generate from the schema where one exists |

## Changelog tooling

| project | approach |
|---|---|
| no releases | `git log` + a hand-kept CHANGELOG |
| published library | conventional commits (`feat:`, `fix:`, `feat!:` + `BREAKING CHANGE:`) with release-please, standard-version or git-cliff |
| monorepo with several packages | changesets (`npx changeset`, `changeset version`, `changeset publish`) |

## Breaking changes

- Listed under **Breaking Changes** in the CHANGELOG, not under Changed.
- A migration guide per breaking change: what changed, why, before/after
  examples, numbered migration steps, and the codemod when one exists.
- Deprecate first where possible: warn in one version, remove in the next
  major; error messages point at the migration guide.
