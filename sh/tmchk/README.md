# tmchk

Time Machine at a glance — each backup disk's snapshots and how fresh the latest one is.

## Install

```bash
curl -fsSL https://quixtop.com/i | sh -s -- tmchk
```

## Usage

```text
tmchk — Time Machine at a glance: each backup disk's snapshots and how fresh the latest is,
plus the launchd job that backs it up: its schedule and its last logged run.

Disks come from Time Machine itself (tmutil destinationinfo), so a mount point like
"mini-tm-ssd 1" still works. A disk that is not plugged in gets no snapshot check and
is named; its job is still checked.
A latest snapshot older than its schedule allows is flagged ⚠; a disk with no age
limit set (see max_age_hours) is listed but not age-checked, and says so.
Under each disk, "job <name>:" shows the schedule launchd holds (what will actually run)
and the last run logged in ~/Library/Logs/tm-jobs.log. Flagged ⚠: a job that is not
loaded, a last run that failed, a run still going after max_run_hours or one that
started and never finished, and a last exit launchd reports as failed (e.g. the job's
script could not start, so nothing was logged).

Usage:
  tmchk                show every Time Machine disk and its job
  tmchk -h | --help | help

Read-only: it lists snapshots and reads launchd and the job log; it never starts, stops
or deletes a backup.
Exit: 0 every connected disk fresh and every job healthy (✓) · 1 something needs a look (⚠)
      or tmchk failed (✗)
```

## Source

`sh/tmchk` in [quixtop/quix](https://github.com/quixtop/quix) · author: shrix

<!-- written by apps publish — edit freely; remove this line to keep your edits -->
