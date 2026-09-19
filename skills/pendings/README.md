# pendings

End-of-session sweep for anything the assistant raised that you never answered.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- pendings
```

## Usage

Invoke it as `/pendings` in Claude Code.

End-of-session sweep of the CURRENT conversation for anything the user may have missed — unanswered questions, undecided choices, pending/deferred work, unclaimed offers, warnings flagged in passing, manual checks still owed. Read-only; reads the raw transcript when compacted. Use before wrapping up or /handoff, or on 'did I miss anything?' / 'what's still open?'.

## Source

`skills/pendings` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
