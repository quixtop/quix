# clodex help block

Used by: SKILL.md when the user invokes clodex without a query (e.g., `/clodex`,
`/clodex --help`, "how do I use clodex"). Read this file and show its contents
verbatim to the user, formatted as below.

---

```text
═══ clodex — Claude+Codex multi-round dialectic ═══

USAGE
  /clodex <query>                                 run with defaults (3 rounds, effort matched, revise ON)
  /clodex --rounds N <query>                      N = 3..5
  /clodex --effort L <query>                      L = low|medium|high|xhigh
  /clodex --no-revise <query>                     skip Step 2.6 self-revision (saves 30s–2min)
  /clodex --rounds N --effort L <query>           combine flags
  /clodex --help                                  show this help

  Natural language (any message containing "clodex"):
    "have clodex weigh in on X"
    "review the auth code over clodex"
    "clodex this design with 5 rounds"
    "use clodex on the typer vs click question"
  Claude infers the query + flags and confirms before launching.

FLAGS
  --effort     Codex reasoning depth.   Range: low|medium|high|xhigh
               Default: auto-matched to Claude (Opus→high, Sonnet→medium, Haiku→low)
               Explicit flag overrides the matched default
               ('minimal' is rejected — warned and bumped to 'low'; it returns
               HTTP 400 with Codex's tool config)
  --rounds     Total round count.    Default: 3.     Range: 3..5  (clamped)
               N=3 → ~6–17 min  N=4 → ~11–28 min  N=5 → ~16–38 min wall-clock
               (estimates with revise ON; subtract ~30s–2min with --no-revise)
  --no-revise  Skip Step 2.6 self-revision (default is ON — each side rewrites
               its own R1 using the critique it received, before synthesis judges).
               Use when wall-clock matters more than answer quality on contested
               questions.

EXAMPLES
  /clodex Should I use Pydantic v2 or attrs for this data model?
  /clodex --rounds 5 Architectural review: Kafka or NATS for our event bus?
  /clodex --effort xhigh Compare these two database schemas for migration safety
  "have clodex weigh in on whether we should migrate from Express to Fastify"
  "review the code over clodex (running 4 rounds)"

WHEN TO USE
  Hard architectural questions, library/framework choices, design tradeoffs,
  debugging strategies — anything where a 5–35 min adversarial second opinion
  is worth the wall-clock cost.

WHEN NOT TO USE
  Simple factual questions or syntax lookups — single-model is faster and cheaper.
  If "common attribution" in your last few runs was consistently >70%, the
  questions you're asking probably don't need clodex.

OUTPUT FORMAT
  Final synthesized answer with [decision: who won] annotations + decision log +
  a STATS block (see references/stats-format.md for exact rules):
    ═══ STATS ═══
      Attribution: Claude (25.0%)  |  Codex (37.5%)  |  Agreed (37.5%)
      Time taken:  Claude (98s)    |  Codex (214s)

  Plus `codex resume <session-id>` commands so you can attach to either Codex
  session interactively in another terminal.

DETAILS
  Full docs:   ~/.agents/skills/clodex/README.md
  Skill spec:  ~/.agents/skills/clodex/SKILL.md
  State dirs:  /tmp/clodex-state/<timestamp>/   (preserved as audit breadcrumbs)
```
