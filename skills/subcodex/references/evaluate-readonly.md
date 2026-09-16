# Evaluating a read-only task result

1. **sanity-check** — spot-check the analysis's claims against the real code;
   do not trust assertions blindly.
2. **Grade** — relevance and quality for the pipeline step that needs it.
3. **Decide:** PASS → use as pipeline input; FAIL → retry once or discard with a
   short note on why.
