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
