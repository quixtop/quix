# mouter — Skill Build Prompt

This is the final, consolidated prompt for building the **mouter** (model-router) Claude
Skill via Claude Code + skill-creator. Paste the section below labeled
**"MASTER PROMPT"** directly into Claude Code. The **"Addendum"** section contains a
later refinement (budget profiles / tier remap) — fold it in before building, or hand
both to Claude Code together with "apply the addendum to the master prompt."

---

## MASTER PROMPT

```
Use the skill-creator skill for this task and follow its full loop end to end: capture intent → draft → generate test prompts → run them → show me results for review → iterate → run the description-triggering optimization → validate → package.

GOAL: Create a global, AGENT-PORTABLE Skill named "mouter" (short for model-router). Canonical install location: ~/.agents/skills/mouter/ with a symlink at ~/.claude/skills/mouter (my existing setup — detect if the symlink already exists before creating). Objective: MAXIMIZE OUTPUT QUALITY per usage window on a flat-rate plan (Claude Max today) by keeping every model inside its band of comparative advantage — never above it (quality risk), never below it (wasted distinctive capability). Surplus capacity funds quality-amplifying "extras" in parallel/background subagents so the main chat stays responsive. Every task's tier+effort is user-definable in one config file, the capability toggles ON/OFF to coexist with other skills, and the skill is PORTABLE across agents (Claude Code, Codex, etc.) via per-agent adapter files.

══ 0. PORTABILITY ARCHITECTURE (new, governs everything below) ══
- SKILL.md and references/config.md are 100% AGENT-AGNOSTIC: no Claude model names, no claude.ai/Max specifics, no Claude Code command syntax in either. The Agent Skills format is an open standard (https://agentskills.io) adopted across Claude, OpenAI Codex, Gemini CLI, Cursor, and others — write to the standard, not to Claude.
- Routing is expressed in ABSTRACT TIERS: frontier (bleeding-edge reasoning, highest weight), top (flagship workhorse for hard work), mid (strong everyday implementation), light (fast/cheap volume + parallel workforce).
- Per-agent ADAPTER files in references/ map tiers → concrete models and hold ALL agent-specific mechanics: references/claude.md and references/codex.md (spec below). At runtime the skill detects (or reads from config) which agent it's running under and loads ONLY that adapter — the other costs zero context.
- SKILL.md refers to "the host agent's adapter file" generically; adding support for a new agent later = adding one adapter file, touching nothing else.

══ 1. SPEC COMPLIANCE (validate against https://agentskills.io/specification before packaging) ══
- Directory name and frontmatter `name` both exactly `mouter` (lowercase/numbers/hyphens, ≤64 chars, folder === name field).
- Frontmatter: only `name` and `description`; no angle brackets anywhere in frontmatter.
- `description` ≤1,024 chars, third person, WHAT + WHEN with trigger keywords ("model router" phrasing lives HERE), agent-agnostic wording. Pushy — trigger whenever I: ask which model to use, mention quality/thoroughness/effort levels/getting the most from my plan, start a multi-phase or multi-step dev task, ask to delegate, parallelize, fan out, run in background, or split work across agents, mention subagents/orchestration/routing, or begin any task spanning multiple SDLC phases — even without saying "model routing".
- SKILL.md: H1 title, H2 sections, numbered steps, ≤500 lines (~5k tokens); LOGIC ONLY — zero tunables (all in config.md) and zero agent specifics (all in adapters).
- Canonical resource dirs only: references/, scripts/, assets/. Reference each bundled file with when-to-read guidance. Forward slashes in all paths.
- Subagent definition files live OUTSIDE the skill package (per host-agent convention, e.g. ~/.claude/agents/ for Claude Code) — generated as a documented setup step per the active adapter, never bundled.

══ 1b. RUNTIME & PLATFORM LIMITS (verify live — Claude: https://docs.claude.com and https://code.claude.com/docs; Codex: OpenAI's current docs — at build time) ══
- Startup tax: every skill's name+description loads in EVERY session (~55–235 tokens measured); frontmatter budget ≤100 tokens.
- Activation budget: SKILL.md ≤5,000 tokens. Bundled files cost zero until read — adapters, matrices, playbooks all stay on disk.
- Scripts over prose: script code never enters context, only output. Resolution = scripts/resolve_model.py; config edits = scripts/set_route.py; state = scripts/mouter_state.py.
- Multi-agent burn: each subagent has its own context; heavy fan-out ≈ 7x a standard session — a feature when the window is fresh, a throttle target when low (4b).
- Flat-plan metering (adapter-specific numbers live in the adapter): reason in WINDOW BURN, not dollars; below-band routing is the prime waste since it starves the extras budget.
- Skills don't sync across surfaces; canonical copy lives at ~/.agents/skills/mouter/ and is symlinked per agent (~/.claude/skills/ today). Document how to symlink for a second agent. Verify current upload/zip caps per surface at build time — don't hard-code.
- Effort mechanics vary by agent and version: verify the current per-subagent/per-invocation effort mechanism in each agent's docs at build time; where effort isn't independently settable, degrade gracefully and note it in the routing justification rather than failing.
- Anti-bloat rule: if SKILL.md nears the limit, cut into references/, never raise the limit.

══ 2. CORE PRINCIPLES ══
- BAND-MATCHING: every tier has a floor and ceiling; above the ceiling risks quality (cheap-but-wrong), below the floor wastes distinctive capability at heavy weight. Both are failures; guard both directions.
- QUALITY-EQUIVALENCE: where tiers perform equivalently on a task class (short well-scoped tasks; computer-use), the higher tier is waste, not quality. "Best model for the job" = best DIFFERENTIATED tier.
- USER-DEFINABLE ROUTING: config.md maps every SDLC task key → {tier, effort}. Resolution order: model/tier named in my request > config routing entry > adapter default. Out-of-band request or config entry → comply, state the band violation in one line.
- AUTO-PICK WHEN ON: with state ON, automatically detect task type(s) from the prompt alone and pick tier + effort per config — no prefix needed, no asking me which model, EVER. Explicit invocation is only for forcing, one-shots, and admin.
- AVAILABILITY FALLBACK: scripts/resolve_model.py must handle model-unavailable errors — fall back one band (frontier → top, etc.), announce in one line, continue; never fail a task over a routing choice.
- Main-lane work never de-escalates below band to save capacity unless the throttle forces it — extras drop first.

══ 2b. INVOCATION MODES & ON/OFF STATE ══
STATE GATE (first instruction in SKILL.md): enabled flag in references/state.json (default ON, written at install). On every auto-trigger, check via scripts/mouter_state.py:
- ON → AUTO-ROUTE EVERY QUALIFYING PROMPT per the pipeline below.
- OFF → stand down SILENTLY: no routing, extras, subagents, or mention of mouter — the prompt is handled natively/by other skills. This is what lets mouter coexist with other dev skills.
Explicit invocation ALWAYS works regardless of state. In Claude Code the invocation syntax is /mouter <args> (documented in claude.md); other agents' syntax is documented in their adapter; commands themselves are agent-agnostic:
- (bare) — TOGGLE ON↔OFF, one-line confirmation.
- status — state (ON/OFF) + status card: routing summary (defaults vs. customizations), active/queued extras, pending proposed diffs, window estimate.
- config — print references/config.md in full.
- table — routing table, customizations highlighted.
- set <task_key>=<tier>[,<effort>] — edit config via scripts/set_route.py (validates; warns on band violation but obeys; preserves prose/comments). Works even when OFF.
- reset <task_key>|all — restore shipped defaults.
- refresh — re-verify references/models.md (and the active adapter's model list) against the vendor docs; update "last verified".
- throttle <fresh|low|off> — manually override the window-state heuristic (testing + when I know better).
- <anything else> — treat as a task; force the full pipeline. If OFF, this is a ONE-SHOT: route this task only, global state stays OFF.
AUTO-DETECTION PIPELINE (ON, or one-shot): parse prompt → map to task key(s) (composites decompose: "add feature X with tests and docs" → feature_well_scoped + unit_tests + docs_sync) → resolve tier+effort per key via scripts/resolve_model.py + active adapter → main-lane keys interactive, amplifier keys background. No matching key → config's fallback_route, announced. Ambiguity → closest key, stated, correctable.

══ 3. COMPARATIVE-ADVANTAGE BANDS (agent-agnostic; adapters ground them in concrete models) ══
- FRONTIER: the longest-horizon, hardest reasoning — greenfield system design, long multi-file refactors, huge-context investigation, unfamiliar-codebase dives. Evidence: frontier lead GROWS with task length/complexity and vanishes on short scoped tasks; heaviest window weight. FLOOR: genuinely long-horizon or deeply ambiguous work — anything less is underuse.
- TOP: flagship workhorse — architecture, decomposition, novel debugging, security judgment, high-blast-radius changes, long-context retrieval. Effort: max setting for architecture/security/hard debugging. FLOOR: multi-file scope, ambiguity, or high blast radius.
- MID: near-top quality on well-scoped implementation at a fraction of the weight; standard refactoring, test writing, review drafting, computer-use/automation parity zones (per adapter evidence). Ceiling: architecture, novel debugging, long-horizon multi-file.
- LIGHT: speed + volume; the only tier cheap enough for many-way parallel. Lint, formatting, commit messages, log parsing, triage, doc stubs, bulk mechanical edits, high-volume extras. Ceiling: cross-file reasoning or design judgment — watch for "simple-looking" tasks hiding coupling.
- EFFORT band-matching mirrors the tier rule: max effort on trivial work = waste; low effort on hard work = underuse. Match to blast radius and ambiguity.
- Escalation one-way by default: cheaper tiers escalate UP on any struggle (one background-extra failure → rerun next tier up; cheap-but-wrong is the most expensive outcome); main lane never de-escalates outside throttle mode. Prompt caching / batch execution for non-interactive bulk where the host supports them.

══ 3b. DEFAULT CONFIG — seed references/config.md with the following (THE single user-editable file; prose + fenced yaml blocks; scripts preserve prose on edit): ══

# mouter configuration  (edit freely — scripted edits preserve your notes)

## Active agent
```yaml
agent: claude          # which adapter to load: claude | codex (auto-detected where possible; this is the override)
```

## Routing table  (per-task tier + effort — redefine any line; tiers: frontier | top | mid | light)
```yaml
routing:
  fallback_route:            {tier: mid,      effort: high}   # when no task key matches; announced
  # Requirements & pre-design
  spec_clarification:        {tier: top,      effort: high}
  feasibility_analysis:      {tier: top,      effort: high}
  epic_to_tickets:           {tier: top,      effort: high}
  # Design
  architecture_bounded:      {tier: top,      effort: xhigh}
  architecture_greenfield:   {tier: frontier, effort: high}
  schema_design:             {tier: top,      effort: xhigh}
  second_opinion:            {tier: top,      effort: high}
  # Implementation
  feature_well_scoped:       {tier: mid,      effort: high}
  feature_cross_file:        {tier: top,      effort: high}
  refactor_standard:         {tier: mid,      effort: high}
  refactor_long_multifile:   {tier: frontier, effort: high}   # frontier's biggest documented lead
  boilerplate_scaffolding:   {tier: light,    effort: low}
  computer_use_automation:   {tier: mid,      effort: high}   # documented parity zone
  # Debugging
  bugfix_known:              {tier: mid,      effort: high}
  debugging_hard_novel:      {tier: top,      effort: xhigh}
  investigation_long_context: {tier: frontier, effort: high}
  repro_bisect_logdive:      {tier: mid,      effort: high}
  # Testing
  unit_tests:                {tier: mid,      effort: high}
  test_gap_analysis:         {tier: mid,      effort: high}
  e2e_integration_design:    {tier: mid,      effort: high}
  edge_case_hunt:            {tier: mid,      effort: high}
  # Review
  diff_review_routine:       {tier: mid,      effort: high}
  diff_review_high_stakes:   {tier: top,      effort: xhigh}
  security_review:           {tier: top,      effort: xhigh}  # pinned top, never frontier (see adapter notes)
  # Docs & comms
  docs_sync:                 {tier: light,    effort: low}
  api_docs_judgment:         {tier: mid,      effort: high}
  pr_description:            {tier: light,    effort: low}
  commit_messages:           {tier: light,    effort: low}
  release_notes:             {tier: light,    effort: low}
  # Build, release, ops
  cicd_pipeline_config:      {tier: mid,      effort: high}
  deployment_rollback_plan:  {tier: top,      effort: xhigh}
  dependency_audit:          {tier: light,    effort: low}
  dependency_migration:      {tier: top,      effort: high}
  # Performance & data
  profiling_analysis:        {tier: mid,      effort: high}
  optimization_subtle:       {tier: top,      effort: xhigh}
  db_migration_backfill:     {tier: top,      effort: xhigh}
  # Maintenance
  issue_triage:              {tier: light,    effort: low}
  unfamiliar_codebase_dive:  {tier: frontier, effort: high}
```

## Execution
```yaml
execution:
  fanout_cap: 3
  fanout_cap_fresh: 5
  hooks_auto_review: false
```

## Amplifiers
```yaml
amplifiers:
  diff_review: true
  test_gap: true
  edge_case_hunt: true
  security_sweep: true
  docs_sync: true
  lint_sweep: true
  second_opinion: true
  tech_debt_notes: true
```

## Throttle
```yaml
throttle:
  enabled: true
  degradation_order: [reduce_extras, downband_extras, defer_extras, main_lane_low_effort]
  announce_downgrades: true
```

══ 3c. AGENT ADAPTERS (all agent specifics live here and ONLY here) ══
references/claude.md — the Claude Code adapter. Seed with (then VERIFY live against https://docs.claude.com):
- Tier map: frontier → claude-fable-5 (explicit pin — no alias exists; one-line update when Fable N+1 ships); top → opus alias; mid → sonnet alias; light → haiku alias. Aliases auto-track latest defaults.
- Model notes (July 2026, verify): Fable 5 ~95.0% SWE-bench Verified / 80.3% Pro / 29.3% FrontierCode Diamond, 1M+ context, lead grows with length; Opus 4.8 ~88.6%/69.2%, 1M context, strongest long-context retrieval; Sonnet 4.6 ~79.6%, 1M context, near-Opus computer use; Haiku 4.5 ~73.3%, 200K context, fastest. Window-burn weights: top ~5x light, mid ~3x light; frontier ~2x top.
- CLAUDE-SPECIFIC RULE: security_review and anything security-flagged pins to top (Opus), never frontier — Fable's safety classifiers can reroute flagged queries mid-session; Opus is predictable.
- Effort levels: low/high/xhigh semantics per current Claude Code docs; frontier-at-low-effort inversion lane (75.0 vs top-at-xhigh 68.6, SWE-bench Pro) is the throttle fallback.
- Mechanics: /mouter slash-command syntax + $ARGUMENTS; subagent files → ~/.claude/agents/ with model aliases; background execution + hooks syntax; Max metering (5-hour windows + weekly caps shared across claude.ai/Code/Desktop); claude.ai zip upload path. "Last verified" date + refresh instructions.
references/codex.md — the OpenAI Codex adapter. Seed with current rough equivalents, then VERIFY live against OpenAI's docs at build time (do not trust these numbers blindly):
- Tier map (approximate, July 2026): frontier AND top → GPT-5.5 (~$5/$30 per MTok; OpenAI's frontier — note it currently leads Terminal-Bench 2.1); mid → gpt-5.4 (~$2.50/$15) for general work or gpt-5.3-codex (~$1.75/$14) for coding-heavy lanes; light → the current mini/nano tier (verify exact ID + pricing in docs).
- Where frontier and top collapse to one model, note that frontier-tier tasks simply get max reasoning effort instead of a different model.
- Mechanics per current Codex docs: invocation syntax, reasoning-effort parameter semantics, subagent/parallel-execution equivalents (or graceful degradation notes where a Claude feature has no Codex analog), metering model. Include the security-review note only if an analogous classifier-reroute concern exists; otherwise state "no equivalent constraint".
- "Last verified" date + refresh instructions.
Runtime: load ONLY the adapter named by config's `agent` key (auto-detect where the host environment makes it possible; config overrides).

══ 4. QUALITY AMPLIFIERS (each toggleable in config, each band-matched via tiers) ══
After/alongside any substantive main-lane task, queue applicable extras as BACKGROUND runs so the chat stays free: fresh-context independent diff review (top for high-stakes, mid routine — sees only diff + criteria); test-gap analysis + missing tests (mid); edge-case & failure-mode hunt — nulls, races, boundaries, error paths (mid; top if subtle); security sweep on auth/input/secrets/network (top); docs sync + changelog (light); lint/type/static-analysis sweep-and-fix (light); second-opinion critique with one alternative on high-stakes decisions (top); refactor & tech-debt notes to NOTES.md, never auto-applied (mid).
Rules: extras never block the main lane or chat; results return as a concise digest (checked / found / auto-fixed vs. proposed); non-mechanical changes are proposed diffs awaiting approval, never silent. Background extras must not write the same file concurrently — serialize writes to shared targets (NOTES.md, README, changelog) — and operate on the working tree only: NEVER commit, push, or stage.

══ 4a. PARALLEL & BACKGROUND MECHANICS ══
- Background execution for long-running commands (builds, test suites); subagents for concurrent work; main conversation stays interactive.
- Fan-out within config's fanout_cap (fanout_cap_fresh when fresh). Only genuinely independent units parallelize; dependent work serializes.
- Pattern: top/frontier plans and does the differentiated work → band-matched extras fan out in background → top-tier reviewer validates anything high-stakes → digest to me.
- Optional hooks (post-edit/stop per the adapter) auto-trigger review/test-gap extras, controlled by hooks_auto_review.

══ 4b. WINDOW-AWARE THROTTLE ══
- Track burn heuristically (intensity, tier mix, fan-out); manual override via the throttle command. Degradation order per config: (1) fewer concurrent extras, (2) extras down one band where quality-equivalent, (3) defer non-critical extras, (4) last resort: main lane to frontier/top-at-LOW-effort (inversion lane), announced.
- Fresh window + big task = spend generously: raise fan-out, full amplifier suite. Idle capacity is waste — but so is below-band spend; surplus buys MORE extras, never gold-plating trivial work.

══ 5. BUNDLED RESOURCES ══
- references/config.md (per 3b) — the single user-editable, agent-agnostic config.
- references/claude.md, references/codex.md (per 3c) — adapters; only the active one loads.
- references/state.json {"enabled": true} — machine-written only; never merged into config.md.
- references/models.md — agent-agnostic band definitions (floor/ceiling/distinctive strengths per tier) + pointers into the adapters for concrete model data.
- references/sdlc-matrix.md — phase → task-key → tier matrix with rationale, example prompts, amplifiers per phase, band-violation traps both directions. ToC if >300 lines.
- references/amplifiers.md — per-extra playbook: triggers, tier, prompt template, digest format.
- scripts/resolve_model.py — prompt/task-key → {tier, effort} via request > config > default, then tier → concrete model via the active adapter; emits band-violation warnings; handles model-unavailable with one-band fallback.
- scripts/set_route.py — safe config.md edits (validates keys/tiers, preserves prose/comments).
- scripts/mouter_state.py — get/set/toggle enabled flag; single source of truth for the state gate.

══ 6. SUBAGENTS (generated per the ACTIVE adapter as a documented setup step; namespaced to avoid collisions; never overwrite an existing file without asking) ══
- "mouter-grunt" (light) — mechanical work + high-volume extras, parallel-safe.
- "mouter-implementer" (mid) — scoped implementation, automation, mid-weight extras.
- "mouter-architect" (top) — design, decomposition, hard debugging, second opinions.
- "mouter-reviewer" (top) — fresh-context review, security sweeps, high-stakes validation.
Tier references only; the adapter supplies concrete model strings/aliases; config routing overrides per task.

══ 7. RUNTIME BEHAVIOR ══
a. STATE GATE via scripts/mouter_state.py — OFF and not explicit invocation → silent stand-down. Otherwise:
b. Load the active adapter (config's agent key / auto-detect).
c. Classify prompt → task key(s) (composites decompose; no match → fallback_route, announced; ambiguity → closest key, stated).
d. Band-match main lane per config; two-sided one-line audit: overkill ("short + well-scoped → mid is quality-equivalent at a fraction of the weight, freeing extras budget") and underkill ("cross-file architecture on mid is below spec → escalating").
e. Queue enabled amplifiers on their band-matched tiers within the fan-out cap.
f. Resolve every role via scripts/resolve_model.py (request > config > default; adapter maps tier → model; band violations and availability fallbacks stated in one line).
g. Execute: main lane interactive, extras background, chat available throughout.
h. Report: one-line routing justification up front (window-burn framing, what freed/spent capacity buys); consolidated extras digest on completion — findings, auto-fixes, proposed diffs.
i. Throttle per 4b when low — shed extras first, protect main-lane band-matching, announce forced downgrades.

══ 8. TESTING & PACKAGING (per skill-creator's loop; run under Claude Code with the claude adapter active; show me all outputs before finalizing) ══
1. Schema design → top xhigh + second-opinion extra.
2. "Fix these 40 lint errors" → light; verify no top-tier waste.
3. Unit tests for a module → mid + test-gap extra.
4. Security review of an auth flow → top (Opus via adapter), NOT frontier, + security sweep.
5. Long multi-file refactor → frontier main lane + background review/docs/edge-case in parallel.
6. Composite "add feature X with tests, docs, changelog" → multi-key decomposition + fan-out; chat responsive.
7. SHORT well-scoped feature → mid + explicit anti-overkill note.
8. "set architecture_bounded=light" then an architecture prompt → compliance + band-violation warning (anti-underkill).
9. "table" → routing rendered, customizations highlighted.
10. "set debugging_hard_novel=frontier" then a hard-debugging prompt → takes effect with "per your routing table" note; "reset all" → defaults restored.
11. Bare toggle → OFF confirmed; auto-trigger-worthy dev prompt → SILENT stand-down; "mouter fix this race condition" while OFF → one-shot, state stays OFF; "status" → OFF + card; bare toggle → ON; next dev prompt auto-routes with NO model question asked.
12. Hand-edit fanout_cap: 1 → composite fans out one agent; amplifiers.second_opinion: false → schema prompt skips that extra.
13. "throttle low" → extras shed per degradation_order before main-lane quality; announced.
14. Flip config agent: codex → verify resolve_model.py maps tiers via codex.md (dry-run resolution is sufficient — no OpenAI calls needed); flip back.
15. Simulate frontier-model-unavailable → one-band fallback to top, announced, task completes.
Also verify: routing consistency across runs; request-named model beats config; extras propose (never silently apply) non-mechanical changes; no git commit/push/stage from any background agent; SKILL.md and config.md contain zero agent-specific strings (grep for "claude", "opus", "sonnet", "haiku", "fable", "gpt" — all hits must be inside references/claude.md or references/codex.md); "config" prints in full.
EFFICIENCY GATE before packaging: report final token weight of frontmatter, SKILL.md body, and each reference file; confirm frontmatter ≤100 tokens, body ≤5k; confirm the OFF-path is a single script call; refactor into references/ and re-measure if over — never ship over budget.
INSTALL: place at ~/.agents/skills/mouter/, create/verify the symlink at ~/.claude/skills/mouter, then run skill-creator's description-triggering optimization, validate frontmatter/naming against the spec, and package as mouter.skill.
```

---

## Addendum — Budget Profiles & Tier Remap

Add this after building the master prompt (or fold it in before building). It adds
a way to shift entire tiers at once — e.g. demote `frontier` to `top` globally when
Fable is suspended, unavailable, or you want to conserve window burn — without
editing every task key by hand, and without ever putting a concrete model name in
`config.md` (portability rule stays intact: `frontier → top` resolves to whatever
`top` means in the active adapter, e.g. Opus on Claude).

```
Add a "Profiles" block to references/config.md, positioned after the Routing table
and before Execution:

## Profiles  (preset tier remaps; switch with the `profile <name>` command; per-task
## `set` entries always override the active profile for that task)
```yaml
profiles:
  active: normal
  normal: {}                                   # no remap — routing table as-is
  saver:  {frontier: top}                      # e.g. Fable unavailable/suspended, or conserving window burn
  scrape: {frontier: mid, top: mid}             # heavy conservation — judgment work funnels to mid
```

Wire it in as follows:
- Add a `profile <name>` command to section 2b's command list (agent-agnostic; same
  invocation style as `set`/`reset`). `profile` alone (no name) shows the active
  profile and lists available ones.
- scripts/resolve_model.py applies remaps AFTER per-task resolution and BEFORE the
  adapter's tier→model mapping: task key → tier (from routing table or request) →
  remap via the active profile (if the tier appears as a key in the profile's remap
  map) → adapter resolves the remapped tier to a concrete model.
- `/mouter status` displays the active profile alongside window state.
- Test: with profile=saver active, a task normally routed to frontier resolves to
  top instead, with a one-line note ("frontier→top per active profile 'saver'");
  switching back to profile=normal restores frontier routing without touching any
  per-task customization made via `set`.
```

---

### Quick reference — what routes where by default (Claude adapter)

| mouter tier | Claude model | Pinned via |
|---|---|---|
| frontier | Fable 5 | explicit ID `claude-fable-5` (no alias exists) |
| top | Opus 4.8 | `opus` alias (auto-tracks latest) |
| mid | Sonnet 4.6 | `sonnet` alias |
| light | Haiku 4.5 | `haiku` alias |

Window-burn weights (relative to light): frontier ≈ 10x, top ≈ 5x, mid ≈ 3x, light = 1x.

Special rule: `security_review` is hard-pinned to `top`, never `frontier` — Fable's
safety classifiers can reroute security-flagged queries mid-session; Opus behaves
predictably there.

https://claude.ai/share/0fe23b2f-e4a4-45ef-9a90-bade82fd63fc
