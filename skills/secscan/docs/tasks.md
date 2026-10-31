# secscan — tasks

## Build
- Hand-off runs still owed: "Scan changes" and "Suggest patches" behind the gate — both work only on the repository the session is open in, so they need a session opened in a throwaway git repo (the gate itself is verified: shut on the seeded twin, open on the clean twin); a `/secscan` request carrying the owner's own cost acknowledgment, so `claude-security` starts unattended.
- keyscan `-H`: a key in UTF-16 or UTF-32 text in history is not decoded (paths mode and the `-s` gate decode it).
- The shared secret-pattern lists (`~/.claude/hooks/secret-patterns.sh`, push, pushlog) do not catch private-key headers with a digit (`SSH2 ENCRYPTED PRIVATE KEY`); keyscan's own extra pattern does. The hook list is guard-layer: owner's call.

## Owed elsewhere
- `~/.agents/skills/picsynth/docs/plan/picsynth-music-google.md:29` still says `secscan -s` — the picsynth session updates it to `keyscan -s`.

## Later
- Container image scanning (trivy image).
- SARIF output.
- osv-scanner reachability and guarddog malicious-package checks in deep mode.
- Swap gitleaks for Betterleaks once v2 is stable (gitleaks is security-patch-only).
- A GitHub Action that runs `/secscan changes` on pull requests.
- skillspector on large skills: archify alone takes 46 s, the floor of a full `~/.agents` run.
- `.mcp.json` at a repo root makes the whole repo an agent folder for skillspector (wider than needed).
