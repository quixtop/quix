# Non-UI Specification Guidance

Spec considerations for backend services, data migrations, infrastructure, and other non-user-facing features.

---

## Backend Service Specs

When the feature has no user interface, replace UI-focused sections with these:

### Instead of UI/UX (Section 4.5), specify:

```
Service Interface:

**Trigger**: [How is this service invoked?]
  - API endpoint: POST /api/service/action
  - Message queue: consumes from `queue-name`
  - Cron schedule: every 15 minutes
  - Event: triggered by `event-name`

**Input Contract**:
  - Source: [Where data comes from]
  - Format: [JSON schema, protobuf, CSV, etc.]
  - Validation: [Required fields, constraints]

**Output Contract**:
  - Destination: [Where results go]
  - Format: [Response shape, event payload]
  - Side effects: [DB writes, notifications, external API calls]

**Observability**:
  - Logs: [What to log at INFO vs ERROR level]
  - Metrics: [Counters, histograms, gauges to emit]
  - Alerts: [Conditions that should page on-call]
```

### Instead of User Stories, specify:

```
Service Story:

When [trigger event occurs]
The system should [processing steps]
Resulting in [expected outcome]
Within [performance constraint]

Failure mode:
When [error condition]
The system should [recovery behavior]
And notify [alerting target]
```

---

## Data Migration Specs

### Key Sections to Add

```
Migration Specification:

**Source**: [Current data format/location]
**Target**: [New data format/location]
**Volume**: [Number of records, total size]
**Window**: [Maximum acceptable downtime or migration duration]

**Strategy**: [Big bang / rolling / dual-write / expand-contract]

**Validation**:
- Pre-migration: Record counts, checksums
- Post-migration: Data integrity checks, sample verification
- Rollback trigger: [Conditions that require rollback]

**Rollback Plan**:
1. [Step to revert schema changes]
2. [Step to restore data from backup]
3. [Step to re-enable old code path]

**Dependencies**:
- [ ] Backup completed before migration starts
- [ ] All consumers updated or backward-compatible
- [ ] Monitoring dashboards configured
```

### Data Migration Risks

| Risk | Mitigation |
|------|-----------|
| Data loss during transform | Backup before migration, validate record counts after |
| Extended downtime | Use rolling migration or dual-write strategy |
| Partial migration failure | Make migration idempotent — safe to re-run |
| Performance degradation | Run during low-traffic window, throttle batch sizes |

---

## Infrastructure Specs

### Key Sections to Add

```
Infrastructure Specification:

**Component**: [What is being added/changed]
**Environment**: [Dev/Staging/Production]

**Resource Requirements**:
- Compute: [CPU, memory, instance type]
- Storage: [Disk size, IOPS, retention]
- Network: [Bandwidth, ports, VPC/subnet]

**Scaling**:
- Strategy: [Horizontal/Vertical/Auto]
- Triggers: [CPU > 80%, queue depth > 1000]
- Limits: [Min 2, Max 10 instances]

**Security**:
- Network access: [Which services can reach this?]
- Secrets: [What credentials are needed, where stored]
- IAM/permissions: [Least-privilege role definition]

**Deployment**:
- Method: [Blue-green / Rolling / Canary]
- Rollback: [How to revert to previous version]
- Health check: [Endpoint and expected response]

**Monitoring**:
- Health endpoint: [GET /health → 200]
- Key metrics: [Request rate, error rate, latency p50/p95/p99]
- Alerts: [PagerDuty/Slack conditions]
```

---

## Checklist: Is Your Non-UI Spec Complete?

- [ ] Trigger mechanism defined (API, queue, cron, event)
- [ ] Input/output contracts with concrete schemas
- [ ] Error handling and retry strategy specified
- [ ] Idempotency requirements documented
- [ ] Performance targets with specific numbers (throughput, latency)
- [ ] Monitoring, logging, and alerting defined
- [ ] Rollback plan with concrete steps
- [ ] Data volume and scaling considerations addressed
