---
name: spec
author: shrix
description: "(shrix) Transform rough feature ideas into implementation-ready specs through structured requirements gathering, design options, and validation. Use to spec out a feature or plan before building — full multi-section specs, not quick ideation (superpowers:brainstorming) or PRD publishing (to-prd)."
metadata:
  version: "2.0"
  category: planning
---

# Specification Generator

Transform rough feature ideas into comprehensive, implementation-ready specifications through structured brainstorming and requirements refinement.

**Not for**: implementation (use `implement`), bug fixes, or refactoring (use
`refactor`). Directory paths and file examples below are illustrative — adapt
to your project's actual structure.

---

## Quick Reference

| Phase | Purpose | Output |
|-------|---------|--------|
| 1. Vision | Extract core intent | Problem statement, goals |
| 2. Requirements | Gather requirements interactively | Clarified requirements |
| 3. Design | Explore approaches | Recommended approach + ADR |
| 4. Specification | Define details | Complete spec document |
| 5. Validation | Verify completeness | Ready-for-implementation checklist |

---

## Phase 1: Understand the Vision

**Token Budget**: ~1500

### Extract Core Intent

```
🎯 Feature Vision Analysis:

**User's Initial Request**: [Restate what user asked for]

**Interpreted Goal**: [What problem are we solving?]

**Primary User Benefit**: [Why would users want this?]

**High-Level Approach**: [General strategy in 1-2 sentences]
```

### Identify Knowns & Unknowns

```
✅ What We Know:
- [Clear requirement 1]
- [Clear requirement 2]

❓ What Needs Clarification:
- [Ambiguity 1]: [Why this matters]
- [Ambiguity 2]: [Why this matters]
```

---

## Phase 2: Interactive Requirements Gathering

**Token Budget**: ~2000

### Default: Sequential Clarification

Present ONE question at a time with AI-recommended answers:

```
❓ Question 1 of 3: How should users activate this feature?

**Why asking**: Determines UI/UX approach and integration points

**Recommended**: Combination (Button in sidebar + Ctrl+B shortcut)
**Reasoning**: Balances discoverability with power-user efficiency.

**Other Options**:
A) Keyboard shortcut only - Quick but poor discoverability
B) Button only - Discoverable but slower access
C) Context menu - Contextual but hidden

**Your answer** (type "recommended", choose A/B/C, or describe):
```

### Optional: Batch Mode

If user requests "all questions at once":

```
📋 Critical Clarifications (5 questions):

**User Experience**:
1. ❓ How should users activate? **Recommended**: [suggestion]
2. ❓ What workflow steps? **Recommended**: [suggestion]

**Functionality**:
3. ❓ Behavior in edge case X? **Recommended**: [suggestion]

**Data & State**:
4. ❓ Where to store data? **Recommended**: [suggestion]

**Integration**:
5. ❓ How integrate with feature Y? **Recommended**: [suggestion]
```

### Question Priority Order

1. **Scope** - What's included/excluded (CRITICAL)
2. **Security** - Auth, validation, data protection (CRITICAL)
3. **UX** - User interactions, workflows (HIGH)
4. **Data** - Storage, persistence, schema (HIGH)
5. **Performance** - Targets, constraints (MEDIUM)
6. **Integration** - Existing features (MEDIUM)
7. **Edge Cases** - Error scenarios, limits (LOW)

---

## Phase 3: Explore Design Options

**Token Budget**: ~2500

### Brainstorm 2-4 Approaches

For each approach:

```
💡 Approach [N]: [Name]

**Description**: [How it works in 2-3 sentences]

**User Flow**:
1. User does [action]
2. System responds with [behavior]
3. User sees [result]

**Pros**: ✅ [Benefit 1] ✅ [Benefit 2]
**Cons**: ❌ [Drawback 1] ❌ [Drawback 2]

**Complexity**: [Low/Medium/High]
**Effort**: [X-Y hours]
```

### Comparative Analysis

```
📊 Approach Comparison:

| Criterion | Approach 1 | Approach 2 | Approach 3 |
|-----------|------------|------------|------------|
| UX        | ⭐⭐⭐⭐     | ⭐⭐⭐      | ⭐⭐⭐⭐⭐    |
| Complexity| ⭐⭐ (High) | ⭐⭐⭐⭐(Low)| ⭐⭐⭐(Med) |
| Maintenance| ⭐⭐⭐⭐    | ⭐⭐⭐      | ⭐⭐⭐⭐⭐   |

**Recommendation**: Approach [N]
**Reasoning**: [Why best fit for this project]
```

### Architecture Decision Record (ADR)

For significant decisions, use the ADR format to document context, decision, and consequences.

> **See [references/adr-template.md](references/adr-template.md) for the full ADR template and comparative analysis format.**

---

## Phase 4: Detailed Specification

**Token Budget**: ~3000

The detailed specification covers 13 sections: Feature Overview, User Stories, Functional Requirements, Data Model, UI/UX, Technical Architecture, API Contracts, Edge Cases & Errors, Non-Functional Requirements, Testing Strategy, Implementation Roadmap, Risks & Mitigation, and Out of Scope.

**📚 For the full specification template with all 13 section templates, see: [references/specification-template.md](references/specification-template.md)**

---

## Phase 5: Validation

**Token Budget**: ~1500

### Quality Checklist

```
✅ Specification Quality:

**Completeness**:
- [ ] All functional requirements defined
- [ ] All data entities specified
- [ ] All UI interactions described
- [ ] All error scenarios covered

**Clarity**:
- [ ] Requirements unambiguous
- [ ] Technical terms explained
- [ ] Examples provided

**Feasibility**:
- [ ] Implementation realistic
- [ ] Estimates reasonable
- [ ] Risks identified

**Actionability**:
- [ ] Developer can implement from spec
- [ ] Clear acceptance criteria
- [ ] Testing approach defined
```

### Final Package

```
📦 Specification Complete

**Defined**: ✅ Overview ✅ Requirements ✅ Data ✅ UI ✅ Architecture ✅ Tests ✅ Roadmap

**Next Steps**:
1. Review specification
2. Confirm alignment with vision
3. If `implement` is enabled, invoke it to begin; otherwise hand the spec to
   your normal implementation flow (it's currently disabled)

**Estimated Effort**: [X-Y hours]
**Complexity**: [Simple/Medium/Complex]
```

---

## Skill Integration

### Workflow Chain

```
spec  →  implement  →  test  →  codedoc
(Define)   (Build)       (Verify)   (Document)

       ↘ build (Spec + Implement combined)

                      ↓
                  refactor
                  (Optimize)
```

### Related Skills

| Skill | Relationship |
|-------|--------------|
| `checklist` (disabled) | Validate requirements quality |
| `implement` (disabled) | Implement the specification |
| `build` (disabled) | Rapid spec + implement combined |

(All three are currently in `disabled-skills/` — the live downstream neighbors
are `/test`, `/refactor`, and `/codedoc`.)

### Information Sources

**From Codebase**:
```bash
# Find similar features
grep -r "similar_keyword" src/ app/

# Check available utilities
ls -la src/utils/ app/utils/

# Find established patterns
grep -r "pattern_to_follow" --include="*.js" --include="*.py"
```

**From Project Docs**:
- Architecture patterns (docs/arch/)
- Existing features (docs/reqs.md)
- Code standards (project rules file)
- Past decisions (docs/proj/decisions.md)

---

## Usage Examples

```
/spec users want to organize their chats
/spec add ability to share chats with teammates
/spec implement voice input for messages
```

Natural language:
```
spec I want users to customize AI responses
spec thinking about adding plugins
```

---

## Key Principles

| Principle | Application |
|-----------|-------------|
| **Design Thinking** | Start with user needs, not technical solutions |
| **KISS** | Simplest solution that solves the problem |
| **Pattern Awareness** | Reuse established codebase patterns |
| **Risk Awareness** | Identify issues early, plan mitigations |
| **Actionable Output** | Spec is implementable as-is |

---

## Quality Indicators

**Good Spec Has**:
✅ Clear problem statement
✅ Detailed requirements with priorities
✅ Complete data model
✅ Thorough edge case analysis
✅ Realistic roadmap
✅ Testing strategy

**Red Flags**:
❌ Vague requirements ("make it better")
❌ Undefined data structures
❌ No error handling
❌ Missing integration points
❌ Unrealistic estimates

---

## Pre-Written Discovery Questions

Common questions to accelerate Phase 2. Pick the most relevant for the feature:

| # | Category | Question | Why It Matters |
|---|----------|----------|----------------|
| 1 | Scope | What's the simplest version that delivers value? | Prevents scope creep |
| 2 | Users | Who are the primary users? (roles, technical level) | Shapes UX and error messaging |
| 3 | Scale | What's the expected data volume? (records, requests/sec) | Drives architecture decisions |
| 4 | Offline | Should this work offline or with poor connectivity? | Determines caching/sync strategy |
| 5 | Integration | What existing systems does this connect to? | Surfaces API contracts early |
| 6 | Auth | Who should NOT have access to this? | Defines security boundaries |
| 7 | Lifecycle | What happens to old data when this ships? | Exposes migration needs |
| 8 | Failure | What's the worst thing that happens if this breaks? | Calibrates error handling investment |
| 9 | Timing | Are there deadlines or external dependencies? | Affects scope and phasing |
| 10 | Success | How will we measure if this worked? | Defines acceptance criteria |

---

## Non-UI Spec Guidance

**📚 For backend services, data migrations, and infrastructure specs, see: [references/non-ui-specs.md](references/non-ui-specs.md)**

Use when the feature has no user interface — replaces UI/UX sections with service interface contracts, migration strategies, and infrastructure requirements.

---

## Checklist Handoff

After Phase 5 validation, if `checklist` is enabled, invoke it to verify the
specification is implementation-ready (it's currently disabled — in that case do
the completeness check yourself against the Phase 5 criteria):

```
checklist review the specification at [path/to/spec.md]
```

Validates completeness, surfaces gaps, produces a go/no-go before implementation handoff.
