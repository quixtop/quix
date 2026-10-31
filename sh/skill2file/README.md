# skill2file

Pack an installed skill into one markdown file that installs itself — share a skill without a git repo. Needs: Python 3, proj-env.sh.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- skill2file
```

## Requires

- [Python 3](https://www.python.org)
- [proj-env.sh](https://github.com/quixtop/quix/blob/main/sh/proj-env.sh/README.md) — sourced at start

## Usage

```text
skill2file — pack an installed skill into ONE shareable markdown file.

  skill2file <skill-name> [-o bundle.md]   write the bundle
  skill2file <skill-name> --list           show what would be packed

For sharing a skill with a friend or team WITHOUT a git repo: you send one
.md file, they say "install this <file>" and their agent does the rest. The
bundle carries its own install procedure, so nothing is needed on their side.

READ-ONLY on the source skill: it never edits, moves or deletes anything.
The only file written is the one you name with -o.

Things that are easy to get wrong, and how this handles them:
  fences      skill files CONTAIN fenced blocks, so the wrapper fence is
              MEASURED from the payload, never assumed.
  paths       targets are ~/.claude/skills/<name>/ — the universal location.
              The ~/.agents + symlink layout is a local convention and is not
              imposed on the recipient.
  modes       preserved exactly. A script invoked as `bash x.sh` is not +x by
              convention, and forcing it would deviate from the source.
  binaries    refused, not mangled: a .pyc or an image cannot survive a text
              fence, and a silently corrupt file is worse than a refusal.
  author:     rewritten as "(shared copy)" so the recipient's skillsync does
              not adopt it as theirs to maintain.
  trust       nothing is fetched at install time; every byte is in the file,
              because the recipient's only real defence is reading it.
```

## Source

`sh/skill2file` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
