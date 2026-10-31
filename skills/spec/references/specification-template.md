# Specification Output Template

Complete template for Step 4 (Generate) of `/spec`. Fill every section, or mark one `N/A — <why>` when it doesn't apply to the feature being specified. Paths, file names and targets in the examples (e.g. the component tree, the coverage target) are illustrative — use the project's own.

---

## Open questions

The first section, after the Status line, so a later session sees what is
still open first.

```
1. [CRITICAL decision not yet made] — **Recommended**: [answer] (provisional)
```
`None` when nothing is open.

## 4.1 Feature Overview

```
Feature: [Name]

**One-Line Summary**: [Concise description]
**Problem Statement**: [What user problem this solves]
**Success Criteria**:
- Measurable outcome 1
- Measurable outcome 2
```

## 4.2 User Stories

```
As a [user type]
I want to [action/capability]
So that [benefit/value]

**Acceptance Criteria**:
- [ ] Given [context], when [action], then [result]
- [ ] Given [context], when [action], then [result]
```

## 4.3 Functional Requirements

```
FR1: [Requirement Name]
- **Priority**: [Critical/High/Medium/Low]
- **Input**: [What goes in]
- **Processing**: [What happens]
- **Output**: [What comes out]
- **Constraints**: [Limitations, validations]
```

## 4.4 Data Model

```
Data Entities:

Entity: [Name]
{
  field1: type,  // Description, validation
  field2: type,  // Description, validation
}

**Storage**: [localStorage / DB / in-memory]
**Lifecycle**: [How long data persists]
**Migration** (when stored data changes): every up() has a matching down();
tested on a production-sized copy of the data before the real run
```

## 4.5 UI/UX Specification

```
Visual Design:
- **Location**: [Where in UI]
- **Layout**: [Element arrangement]
- **Styling**: [Colors, sizes - reference existing]

**Interactions**:
1. [Interaction]: Trigger -> Response -> States
```

## 4.6 Technical Architecture

```
Component Structure:

Frontend:
├── components/FeatureComponent.js
├── utils/featureHelpers.js
└── constants/featureConstants.js

Backend:
├── api/feature_endpoints.py
├── services/feature_service.py
└── models/feature_models.py
```

## Alternatives considered

One block per approach Step 3 rejected, so the "why not X" outlives the chat:

```
[Approach name]
- How: [how it works, one line]
- Pros: [what it gains]
- Cons: [what it costs]
- Why rejected: [what it lacks or costs against the chosen one]
```

## 4.7 API Contracts

```http
POST /api/feature/action
Content-Type: application/json

Request: { "param1": "value" }

Response (Success): { "status": "success", "data": {...} }
Response (Error): { "status": "error", "message": "..." }
```

**Versioning** (when an existing endpoint changes shape): how the version is
carried (path `/v2/…` or a header), and how the old one is retired — kept for
how long, then `410 Gone` with a pointer to the new one.

## 4.8 Edge Cases & Errors

```
Edge Case: [Scenario]
- **When**: [Conditions]
- **Expected**: [Behavior]
- **Implementation**: [How to handle]

| Error | Cause | User Message | Recovery |
|-------|-------|--------------|----------|
| [Type]| [Why] | "[Message]"  | [Action] |
```

## 4.9 Non-Functional Requirements

```
Performance: [Response time, throughput targets]
Security: [Auth, validation, data protection]
Accessibility: [Keyboard nav, screen reader, WCAG]
Compatibility: [Browser versions]
Scalability: [User load, data volume targets]
```

## 4.10 Testing Strategy

Strategy only — the test tasks themselves live in the plan.

```
Testing (80%+ coverage target):

**Levels**: unit (core functions, error handling, edge cases) ·
integration (component boundaries, feature interactions) · manual scenarios
(happy path, an edge case, error recovery)
**What is hard to test, and how**: [e.g. timing, external services]
**Acceptance**: the feature-level success criteria, each as a plan task
```

## 4.11 Implementation Roadmap

A one-line pointer — the tasks, their "Done when" checks and the estimates
live in the plan, once:

```
Roadmap: see docs/plan/<feature>.md
```

## 4.12 Risks & Mitigation

```
Risks:

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| [Risk] | Med | High | [Strategy] |

**Rollback Plan**:
1. [Disable step]
2. [Revert step]

**Feature flag / kill switch** (for a risky rollout): [flag name · default off ·
who turns it on, and how it is turned off without a deploy]
```

## 4.13 Out of Scope

```
Explicitly Excluded:
- [Feature]: Reason, future consideration: [Yes/No]
```
