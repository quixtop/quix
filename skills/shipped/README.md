# shipped

The last n features shipped, as a table, with your own smoke-test state.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- shipped
```

## Usage

Invoke it as `/shipped` in Claude Code.

List the last n features shipped (default 25) as a table from the project's deplog — smoke state, dep time, feature, machine verdict. -v / -u filter verified / unverified; -w opens the smoke-check widget. Read-only. Triggers on /shipped [n], 'what shipped', 'what went out lately', 'features shipped', 'last few features'.

## Source

`skills/shipped` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
