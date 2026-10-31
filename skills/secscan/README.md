# secscan

One security scan for a project — secrets, vulnerable dependencies, misconfigured infrastructure, code flaws, CI and agent skills — merged and verified.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- secscan
```

## Usage

Invoke it as `/secscan` in Claude Code.

Security scan for a project — runs every engine that applies (secrets via keyscan and gitleaks, vulnerable dependencies, misconfigured Docker/Terraform/Kubernetes, licences, code flaws, GitHub Actions, agent skills and MCP) into one merged, verified list with coverage, then calls the best outside tools, both by default: claude-security for the verified code review and patch files, the security-audit skill for its domain guides in depth and agent skills and MCP. Each reads a masked copy of the repo, so nothing reads a leaked key. Bare /secscan checks the whole repo; changes, deps, secrets, code, ci, agents narrow it. Triggers on /secscan, 'security scan', 'is this secure', 'scan for secrets', 'any keys in here', 'check before I push'.

## Source

`skills/secscan` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
