# secscan — fixes

Only when the owner names findings ("fix 2, 5"). Never on your own.

## Order

1. **Leaked keys first.** Tell the owner which key (by place and rule, never the
   value) and where to revoke it. Wait for "revoked". Then the owner removes the
   value from the file (you never open it while it holds the value). Removing a
   key from code or history does not make it safe; revoking does.
2. **A `claude-security` finding**: run its "Suggest patches" job (invoke the
   `claude-security:claude-security` skill naming it, with the owner's ids for
   its findings). It writes patch files, each checked by its own panel; the
   owner applies them. It accepts only a report of the checkout it patches, so
   it scans the live repo first and runs only behind SKILL.md's secrets gate
   (ignored files included). When the gate is shut, or it refuses, the finding
   takes step 3 instead, with the tool's report as evidence.
3. **An engine finding through `/rev`** (it owns the failing-test-first fix):
   - prepend ONE audit entry to the project's `docs/logs/revlogs.md`, in
     `code-audit`'s entry format, so `/rev` reads it as the newest audit entry:

     ```text
     [<DMonYY>/<H.MMa|p>]
     > **<at-risk|needs-attention> — secscan fix hand-off (not an audit baseline), <sha12>, <clean|dirty>, <mode>**
     - **<category>** [Critical|Important|Minor] A1 file:line — <issue>; <two sentences: what breaks and the smallest fix at the last trusted decision point>
     - [Important] A2 file:line — <issue>; <…>
     - **Not checked:** <coverage gaps, each with its command>
     - **Next steps:** /rev A1 A2
     ```

     The timestamp is the moment you write it (e.g. `[24Oct26/2.05p]`). The
     verdict is `at-risk` when any named finding is critical or high, else
     `needs-attention`. Severity words map critical/high → Critical, medium →
     Important, low/info → Minor — on purpose: a high security flaw blocks a
     ship. The entry holds only the findings the owner named, so `/rev` fixes
     every one of them, Minor included. Create `docs/logs/revlogs.md` when missing, with a `# <Project> Review
     Logs` header and a dashed underline below it, as `code-audit` writes it.
   - run `/rev A1 A2 …` with the IDs the owner named, telling it: no secret value
     in any output; a file that held a masked hit is fixed only after the owner
     removed the value (step 1); once it is gone, the file holds no secret and
     `/rev` reads and edits it as any other.
4. **Close-check** after `/rev` lands: `python3 $P <mode> --only <engine> --json`
   on the repo (a mode that includes that engine; never on the mirror, which
   masks and leaves files out). A finding is closed only when that engine's
   coverage says `ran` and the finding is gone — `n/a` or any gap is not a close.
   Report each as closed or still open. A `claude-security` finding is closed by
   that tool's own re-scan.
5. **False positives** on the owner's word: `keyscan:allow` on the line, a
   `.gitleaksignore` fingerprint, or a `docs/security/precedents.md` entry.

Dependency upgrades, Dockerfile and workflow fixes are code changes too: they go
through `/rev` like any other.
