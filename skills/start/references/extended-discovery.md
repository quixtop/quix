# Extended Discovery

Additional discovery steps for developer tooling and external service dependencies.

---

## Developer Environment Discovery

After Phase 3 (Stack), check developer tooling that affects how code is written:

```bash
# TypeScript config — strictness, paths, target
cat tsconfig.json 2>/dev/null | head -30

# Linting — rules that will reject your code
cat .eslintrc* eslint.config.* 2>/dev/null | head -20

# Formatting — auto-format settings
cat .prettierrc* prettier.config.* .editorconfig 2>/dev/null | head -15

# Pre-commit hooks — what runs before commit
cat .husky/pre-commit .pre-commit-config.yaml lefthook.yml 2>/dev/null

# CI pipeline — what runs in CI that must pass
ls .github/workflows/ .gitlab-ci.yml .circleci/ Jenkinsfile 2>/dev/null
cat .github/workflows/*.yml 2>/dev/null | head -40
```

### Key Things to Note

| Config | What to Look For | Impact on Your Code |
|--------|-----------------|---------------------|
| `tsconfig.json` | `"strict": true` | Must handle null/undefined explicitly |
| `tsconfig.json` | `"paths"` aliases | Use `@/utils` instead of `../../utils` |
| `.eslintrc` | Import ordering rules | Imports must follow specific order |
| `.eslintrc` | Naming convention rules | Variable/function naming is enforced |
| `.prettierrc` | Formatting config | Code auto-formatted on save/commit |
| `.husky/pre-commit` | Pre-commit hooks | Tests/lint run before every commit |
| CI workflows | Required checks | All these must pass for PR to merge |

### Dev Environment Summary Template

```
Developer Tooling:

TypeScript: [strict/loose] — Target: [ES2020/ESNext]
Linter: [ESLint/Biome/none] — Key rules: [import order, naming]
Formatter: [Prettier/Biome/none] — Config: [tabs/spaces, width]
Pre-commit: [Husky/lefthook/none] — Runs: [lint, test, type-check]
CI: [GitHub Actions/GitLab CI/none] — Checks: [build, test, lint]
```

---

## External Dependency Discovery

Map the external services the project communicates with:

### Finding External Services

```bash
# Find environment variables referencing external services
grep -r "API_URL\|API_KEY\|_HOST\|_ENDPOINT\|_SECRET" .env.example .env.local 2>/dev/null

# Find HTTP client usage pointing to external APIs
grep -r "https://\|baseURL\|apiClient\|axios.create" src/ --include='*.js' --include='*.ts' --include='*.py' | grep -v node_modules | head -15

# Find SDK imports (cloud providers, payment, auth, etc.)
grep -r "import.*aws-sdk\|import.*@google\|import.*stripe\|import.*firebase\|import.*@auth0" src/ --include='*.js' --include='*.ts' | head -10

# Python SDK imports
grep -r "import boto3\|import google\|import stripe\|import firebase" src/ --include="*.py" | head -10
```

### External Dependency Map Template

```
External Dependencies:

├── Auth:     [Auth0 / Firebase Auth / Cognito / custom JWT]
├── Storage:  [S3 / GCS / Azure Blob / local filesystem]
├── Database: [PostgreSQL / MongoDB / DynamoDB / Supabase]
├── Cache:    [Redis / Memcached / none]
├── Payments: [Stripe / PayPal / none]
├── Email:    [SendGrid / SES / Resend / none]
├── Search:   [Elasticsearch / Algolia / none]
├── CDN:      [CloudFront / Cloudflare / none]
└── Other:    [List any other external services]

Environment Variables Required:
- SERVICE_API_KEY: [which service, how to obtain]
- DATABASE_URL: [connection string format]
- [etc.]
```

### Why Map External Dependencies

- **Blast radius**: An outage in any external service affects your application
- **Local development**: Know which services need mocks/stubs for local dev
- **Cost awareness**: Understand which services have usage-based pricing
- **Security surface**: Each external service is a potential attack vector
- **Onboarding**: New developers need API keys/credentials for each service
