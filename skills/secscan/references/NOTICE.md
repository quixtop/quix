# Notices

secscan's method is written in its own words. It draws ideas from these works;
where wording or structure was adapted, the licence below applies to that part.

- **Cloudflare security-audit skill** — https://github.com/cloudflare/security-audit-skill
  MIT License, Copyright (c) 2025-2026 Cloudflare, Inc.
  Adapted ideas: severity anchors, verdicts
  (confirmed / needs-validation / rejected), coverage of every surface. The skill
  itself stays installed; secscan calls it on every default run.

  > Permission is hereby granted, free of charge, to any person obtaining a copy
  > of this software and associated documentation files (the "Software"), to deal
  > in the Software without restriction, including without limitation the rights
  > to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
  > copies of the Software, and to permit persons to whom the Software is
  > furnished to do so, subject to the following conditions:
  >
  > The above copyright notice and this permission notice shall be included in all
  > copies or substantial portions of the Software.
  >
  > THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  > IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  > FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  > AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  > LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  > OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  > SOFTWARE.

- **Anthropic claude-code-security-review** — https://github.com/anthropics/claude-code-security-review
  MIT License, Copyright (c) 2025 Anthropic. Adapted ideas: false-positive
  tests and project precedents. (Same MIT
  terms as above.)

- **Ideas only, re-expressed, no text copied**: the claude-security plugin
  (proprietary), Trail of Bits skills (CC BY-SA 4.0).

- **OWASP** Top 10:2025, ASVS 5.0, Top 10 for LLM Applications 2025 and Top 10
  for Agentic Applications: © the OWASP Foundation, CC BY-SA 4.0
  (https://creativecommons.org/licenses/by-sa/4.0/). `report.md` cites their
  identifiers with the short category names, unchanged; SKILL.md asks
  `security-audit` for ASVS requirement ids and adds them to `claude-security`'s
  findings; no other OWASP text is used.

- **CWE** identifiers: CWE™ is a trademark of The MITRE Corporation; used under
  the CWE terms of use (https://cwe.mitre.org/about/termsofuse.html).
