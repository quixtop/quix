# spec — Steps 1–3 in EGM-full and EGM-lite: the think stage
<!-- author: shrix -->

READ at Step 1 in EGM-full and EGM-lite, and § Save point and resume plus
§ Contradictions when Step 0.2 resumes a concept. Lite, post-build mode
and spec-only re-runs do not run this stage. READ `references/questions.md` for the bank and
the drill form. Step numbers are `spec/SKILL.md`'s.

The stage attacks the idea before any spec exists. **The only turns that
ask:** the drill's questions, the concept gate when it stops, at most 2
follow-ups after the idea panel, a contradiction, a lens STOP
(`references/review.md` § Panel), the depth line (`references/questions.md`
§ Depths), an EGM-lite run's ask to switch to EGM-full, and the approach pick when
approaches differ on scope or security.
Everything else — routing the panel's problems, the save point — runs in the
same turn, with no extra confirm.

## Drill

Step 1 forms the vision block silently; it is shown at the concept gate. Step
2 asks ONE question per turn in the drill form, each with a recommended answer
and other options: the required topics first (bank rows 1, 2, 4, 5 and 6 —
scope, success, security, today, constraints), then the bank's priority
order. A question the request, the code or the existing spec's Decided
already answers is not asked: an existing Decided entry stays Decided, an
answer found in the request or the code is an **Assumption** until the gate.

- **In an `EGM-lite` run the drill takes at most 3 turns**, the required
  topics first — the depth is set before the drill, and a depth word in a
  drill reply changes it (`references/questions.md` § Depths).
- **The drill ends** when the required topics are answered, after 6 turns, or
  when the user says "recommended for the rest" on any turn, the first
  included. A follow-up on an answer counts as a turn. The concept gate always
  follows.
- The user's answers are **Decided**; every bank question neither asked nor
  already answered takes its recommended answer as an **Assumption**. "All
  questions" lifts the 6-turn cap and asks the whole bank, one question per
  turn; "All questions" lifts EGM-lite's 3-turn cap too.

## Concept gate

Show the concept: 2–3 sentences covering the request, the goal, who
benefits, the approach in one line, and the scope edge (what it does NOT do),
then Decided as a short list and the Assumptions in two labelled groups:
found in the request or the code — Decided if you confirm at a stop, else
Assumptions until the go; recommended answers — stay Assumptions; the go
approves them.

The gate **stops** (confirm or correct) only when an Assumption found in the
request or the code answers one of the drill's required-topic rows — 1, 2, 4,
5 or 6 (scope, success, security, today, constraints) — naming those rows, or
when § Contradictions applies — at the gate, a found Assumption that
contradicts a Decided entry (a contradiction stop asks § Contradictions'
question, not confirm or correct; when a required row is found too, the same
turn also asks the confirm, and the gate goes on only once both are answered;
an unanswered one is asked again); otherwise it goes on in the same turn to
the idea panel. A correction updates Decided and shows the gate again; at a stop,
a confirm moves the found group into Decided; the recommended group stays
Assumptions until the go. No agent runs before the gate goes on or is
confirmed. The gate decides when found Assumptions move: § Drill's "until the
gate" means until it decides.

## Contradictions

From the concept gate to the Step 6 go, an answer, a found Assumption at the
concept gate or an idea-panel problem that contradicts a Decided entry, without saying it replaces it, stops every
file write for that turn. Ask: "This contradicts Decided <n>: which one
stands?" The answer updates Decided, and the next turn goes on. A gate
correction, a follow-up answer, a go with changes and a walk `change`
(`references/review.md` § Walk at the go) replace Decided by design: they
never trigger this. A correction of a found Assumption after the gate went on
is not a contradiction either (the entry is not Decided): it is Decided when
given; one given at the go is a go with changes. The panel does not re-run for
it.

## Idea panel

After the gate goes on or is confirmed, run in ONE wave each idea lens of
`references/lenses.md` § Idea lenses whose **Runs** line holds for the concept
the gate passed — no cap; a trigger the run is unsure of counts as holding —
then one merger, as `references/review.md` describes: § Agent tools (panel
brief, run-id files, write check), § Panel (STOP and `incomplete`; a STOP
recovery re-runs only lenses that ran), § Merger, § Self-review (it covers the
triggered lenses only) and § Cap and cost. With no optional trigger, the two
always-lenses and the merger run. No lens is stopped early when others report
first. Each skipped lens is named with its one-line reason, in the
planned-spend line and in Review. Each lens gets the concept the gate passed,
`<root>`, its lens block without its **Runs** line and the lenses.md "Every
agent" list.

The run routes every problem itself, highest severity first, and shows at most
5 with their routes (the rest in Review):

- a follow-up question — at most 2 extra turns, outside the 6-turn cap;
- § Contradictions — the problem contradicts Decided (its question is one of
  the 2 follow-ups; past the 2 follow-ups, an **Open question** for the go);
- an **Assumption** — the problem's fix is taken as the default;
- a **4.13 Out of Scope** entry — the part it names is cut;
- a **4.12 Risk** — kept, with its early sign as the mitigation trigger.

The concept gate shows again only when a follow-up changed Decided. It then
stops, by § Concept gate's rule, only on found Assumptions it has not shown
before; whether it goes on or is confirmed, it continues to § Approach pick,
and the panel does not re-run.

Any reply from the wave up to the Step 6 go — one after `/spec think` stopped
and the go itself included — that names skipped lenses runs them as ONE extra
wave plus a merger, with its own planned-spend line. A reply that also answers
or corrects is applied first, and the extra wave gets the updated concept.
Before Step 4 starts, its problems are routed as the first wave's, and a saved
concept is updated in place; after it, they are routed as the first wave's into
the spec — a follow-up or a contradiction becoming an Open question for the go,
none into Decided — and applied as ONE go-with-changes round (SKILL.md Step 6),
and the go is asked again. Until the go, while a lens is skipped and no extra
wave has run, every asking turn and the save point end with `skipped lenses:
<lens>, … — name any to run them`. The extra wave shares the first wave's 2
follow-ups and its one STOP recovery; a lens of it that STOPs once the
recovery is used is `incomplete`. Its planned-spend line and its Review cost
line start `idea panel, extra wave:`. After Step 4, the spec's 4.1, Decided
and Assumptions stand in for the concept. The extra wave's lenses count
against the panel's 7 lens slots; its merger comes on top and is recorded, as
a STOP recovery's does. The panel runs no other second time.

In an `EGM-lite` run, only Scope and reuse and Pre-mortem and the merger run,
whatever the **Runs** lines say. The other lenses are not skipped: no
skipped-lenses tail and no extra wave. Naming one asks `<lens> runs only in
EGM-full — switch to EGM-full?`; a yes makes the run EGM-full: the named lenses run as
§ Idea panel's extra wave, then the review panel at Step 5. Its problems are
routed as above, with at most 1 follow-up.

Before each wave, print the planned-spend line (`references/review.md` § Cap
and cost). Record in Review the panel's cost line and every other record
review.md names (incomplete lenses, a STOP recovery, the write check), plus
every problem not shown.

## Approach pick

Step 3's approaches (SKILL.md § Step 3): when they differ in scope or
security, the user picks, and the pick is **Decided**; otherwise — cost or
user flow included — the recommended one is an **Assumption**, with the
difference named beside it. Each rejected approach goes into
Alternatives considered, in the form of `references/specification-template.md`.

## Save point and resume

For a NEW feature in EGM-full (EGM-lite too), the turn that ends Step 3 also writes
`<root>/docs/spec/<feature>.md` with `Status: draft — concept`, holding: Open
questions, 4.1 Feature Overview, Decided, Assumptions, Alternatives
considered, the ADR drafts (under To file), the routed problems, and a Review
section with the idea panel's records; it opens its Review section with the
`depth:` line (`references/review.md` § Cap and cost). A re-run of an existing spec writes
nothing here: Step 4 overwrites it as today, and `references/rerun.md` covers
the recovery. `/spec think` stops here and prints how to resume: `/spec
<feature>`.

- **Resume** (Step 0.2): nothing the concept answers is asked again; the run
  goes on in the mode the user gives (`/spec lite <feature>` resumes in lite
  mode). With no word it takes the concept's recorded depth (a concept with
  none is EGM-full) and prints `depth: <d> (from the concept — reply lite |
  EGM-lite | EGM-full to change)`; § Contradictions applies against the concept's Decided until the
  go. A reply after `/spec think` stopped that names skipped lenses runs § Idea
  panel's extra wave on the saved concept; a resume itself does not ask, and the
  go presents any lens still skipped.
- **Step 4 after a save point** — a resume or a plain run going on — keeps the
  concept's Open questions, Decided, Assumptions, Alternatives considered, ADR
  drafts and Review lines as they are, moves each routed problem to the place
  it was routed to (Assumptions, 4.12 Risks, 4.13 Out of Scope), and writes
  every other section.
