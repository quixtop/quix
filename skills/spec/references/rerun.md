# spec — re-runs: spec-only mode and dropping a re-run
<!-- author: shrix -->

READ when Step 0.2 finds a re-run whose build has started (spec-only mode), and
when the user drops a re-run at Step 6. Step numbers are `spec/SKILL.md`'s.

## Spec only

   - **Spec only** is for changes that need no build work — wording,
     clarifications, decisions already built, and dropping a planned
     decision. Anything that needs build work goes to the follow-up feature
     instead. In this mode Step 4.3 is skipped and the plan stays read-only
     through every later step; the reviewer is told about the mode, and a
     finding that needs build work becomes an Open question pointing to the
     follow-up. To file holds only the entries this re-run changed, each
     tagged by checking the code under `<root>` — `as-built` when the code
     already does it, else `not built yet` — so Step 7 replaces as-built
     entries in place and marks only the not-built ones `(planned)`; the tags
     guide the filing, stay in the spec's To file, and never appear in the
     capture docs. No `Build` task. A
     dropped planned decision is filed as dropped, and Step 8 names the
     plan tasks the user must remove before resuming `/dev`. Step 7
     leaves the plan's Status alone, and Step 8 offers no new build.

## Dropping a re-run (Step 6, Drop it)

On a re-run, Step 4 has
  overwritten the approved version: list the exact files Steps 4–6 changed or
  created (never a glob; in spec-only mode the plan is not among them), and
  tell the user how to get the approved version back — `/rewind` to before
  Step 4 restores this session's edits, and for each file
  `git -C <root> log -1 -- <path>` shows whether a committed copy exists to
  `git -C <root> restore -- <path>` from. Files the re-run newly created are
  named for the user to remove. Never restore or remove anything yourself.
