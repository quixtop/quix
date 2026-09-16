# mouter — help

Ambient model-routing **suggestions**. For each task, mouter shows the ideal
model + effort as a statusline chip (CLI) and a banner atop the reply
(Desktop-local). It is suggestion-only — it never changes your model/effort;
you do. The harness forbids programmatic switching anyway.

mouter is **per-session**: OFF by default, active only where you turn it on.

## Gate — the controls
```
/mouter          toggle THIS session ON <-> OFF (off by default; confirms)
/mouter status   current state + where task classes route right now
/mouter off all  turn OFF across ALL sessions at once  (on all = the reverse)
/mouter help     this card
```
Each session is independent; other sessions are unaffected by your toggle.
When a session goes OFF, the hook clears the reco, so its chip/banner vanish.

## Reading the chip   ▶ model·effort
```
dim ▶      ideal MATCHES your current setting — right-sized, nothing to do
normal ▶   ideal does NOT match — you could switch
(nothing)  aligned, no recent task, muted, or current model unknown
```

## Acting on it (optional — always your call)
```
Ctrl+P -> native picker: up/down model · left/right effort · Enter=save · s=session only
or:  /model <name>   /effort <level>
```
Switching mid-task applies from your NEXT turn (a turn runs on one model).

## Tuning (advanced)
```
/mouter table              routing table (task class -> tier/effort)
/mouter set K=tier[,eff]   re-route one task class (e.g. set unit_tests=top)
/mouter reset K|all        restore shipped defaults
/mouter throttle f|l|off   window-burn override (fresh raises the extras cap)
/mouter config             print the full editable config
```

Full architecture, data flow, teardown: `~/.agents/skills/mouter/README.md`.
