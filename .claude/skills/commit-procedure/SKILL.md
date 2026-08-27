---
name: commit-procedure
description: The procedure and policy for splitting this repository's working tree into Conventional Commits — survey, group by concern, verify, commit, report. Load it before staging or committing anything here. It is the `committer` agent's working instructions; it does NOT authorize a commit, which only the user can do.
user-invocable: false
allowed-tools: Read, Edit, Bash
---

# Commit procedure

The whole policy for turning this tree into commits. It lives here, as one skill, so the
`committer` agent loads it when it runs instead of carrying it in every context, and so a
rule is stated once — `.claude/agents/committer.md` points at this file rather than
restating it.

It is the operational form of `.github/instructions/commit.instructions.md`, which is the
repository's own commit policy and applies to every agent working here. Where that file and
this one describe the same rule, they must agree; this one adds the phases, the scopes that
actually exist in this tree, and the verification step.

**Loading this skill is not authorization.** The user authorizes commits, per run, by
typing `/commit`. Reading the procedure never creates permission to execute it: without
that authorization, stop here and say so.

## Constraints (ABSOLUTE)

- **No commits without explicit user authorization** — `git commit` only after the user says so
- **No branches, worktrees, pushes** — never create or modify them (`git push` is denied in settings)
- **No `--amend` on prior commits** — only commits from this run
- **No `.git/` edits** — never touch version control internals
- **Never hand-write a trailer** — commits carry no `Co-Authored-By` line
- **Never commit `.env`** or anything under `outputs/`
- Fail on ambiguity — ask rather than guess scope/type if it does not fit Conventional Commits 1.0.0

## Procedure: one `.claude/scripts/commit.sh` call per phase

**Phase 1: Survey** — one full read of the tree

```
.claude/scripts/commit.sh survey
```

Reads: branch, tracked+untracked status, diffstat, full diff vs HEAD, untracked line counts,
and how much of the daily commit budget is already spent. **Never re-run `git status` or
`git diff` separately; never run multiple survey calls.** The survey is one round-trip
precisely so the diff, not shell plumbing, is what occupies your context.

If the survey reports that the hooks are not installed, say so in the final report. Nothing
is checking the message format or the budget on that tree, and the reader should know.

**Phase 2: Group by concern** — see the categories below

- Each commit is one concern, ordered so dependencies come first.
- This tree holds two independent services. A change that touches both is almost always two
  commits, not one — they ship separately and are read separately. The exception is a change
  whose whole point is keeping them aligned; say so in the body when you make it.
- **Check the split against the daily budget before starting.** `.githooks/pre-commit`
  refuses the 61st commit of a day and warns from the 50th, and it counts every commit of
  this run. A twelve-commit split spends twelve. The survey's `daily commit budget` line
  reports what is already spent, so this costs no extra call; if the planned split does not
  fit in what is left, say so and propose a coarser grouping rather than starting one —
  hitting the limit mid-run leaves the tree half committed, which is the one state this
  procedure must never produce.
- When a file mixes concerns, use `Edit` to split it: trim to one concern, `git add`,
  `git commit`, restore with `Edit`.
- Always verify the final state against the original working tree — diff to confirm nothing
  was lost or altered.

**Phase 3: Verify** — before any commits

```
.claude/scripts/commit.sh verify
```

Runs the gates for whichever service the tree touches, skipping the one it does not. A
passing gate prints one line; a failing one prints the tail of its output — the only case
where that output is worth context — plus the path to the whole run on disk. When the tail
is not enough, grep that file. Never re-run a gate just to see more of it.

Exit 0 = proceed. Non-zero = stop, report the failure, do not commit.

Some gates cannot run without their toolchain: Python needs the dependencies installed
(`make install`), the full Python suite needs the Tesseract binary, and Go needs `go` plus
`go mod tidy`, since `go.sum` is not committed. A gate that cannot run reports `skipped` with
the reason. **A skipped gate is not a passing gate** — say which ones were skipped in the
Phase 5 report, so nobody reads the run as more verified than it was.

**Phase 4: Create commits** — one at a time, each message written from its own staged diff

For each commit:

1. `git add <specific files>`
2. If this commit is a user-visible or architectural change, update `CHANGELOG.md`'s
   `[Unreleased]` per the Changelog section below and `git add CHANGELOG.md` into this same
   commit; if it is internal churn, leave the file alone
3. `.claude/scripts/commit.sh staged` — the staged diffstat and the staged diff
4. Write the subject and body from that output, then commit with the form below
5. Before running it, read the subject back against the diffstat. A subject naming a change
   that is not in that output is a false message: stop, do not commit, report it

**The message comes from the staged diff, never from your memory of the work.** Memory
carries what you set out to do; the diff carries what the commit actually contains, and when
the two disagree the diff is right. `.githooks/commit-msg` checks the *shape* of a message
and nothing more — a well-formed subject describing the wrong diff passes it and always will.
This read-back is the only check on whether the message is true.

```
git commit -F - <<'MSG'
<type>(<scope>): <description>

<body>
MSG
```

The heredoc is the form to use: it is the only one that produces a real body, and `-m` pairs
invite a body squeezed onto one line. The git guard strips heredoc bodies before matching
bypass flags, so any message text is safe inside it. No trailer, ever — `commit-msg` rejects
`Co-Authored-By`.

A rejected message costs nothing: the commit did not happen, the index is untouched, and
re-running with a corrected message is a normal step rather than a failed run. Never reach
for `--no-verify` to get past it; the git guard denies that anyway.

**Phase 5: Report** — final status

```
.claude/scripts/commit.sh report [n]
```

State: resulting commits (hash + subject), which gates passed, which were skipped and why,
and that the whole tree was verified rather than each staged index.

## Message format

**Conventional Commits 1.0.0:** `<type>[optional scope]: <description>`

- **Type:** `feat`, `fix`, `perf`, `refactor`, `docs`, `test`, `chore`, `ci`, `style`,
  `improvement`. Pick the one that describes the change; a concern name is not a type.
- **Scope:** the concern from the list below, in parentheses — `chore(docker)`, never
  `docker:`. `docs` is the one word that is both a type and a concern.
- **Description:** imperative mood, lowercase, short enough to survive a narrow log column.
  "add" not "added".
- **Body:** prose — one sentence of why, and whatever more the change needs. Say what changed
  and why, never how: `git show <hash>` should explain the commit without anyone opening the
  diff.

Wrap the body by hand as you write it, at 72 columns. Git reflows nothing, so the line breaks
you type are the ones every reader gets.

Read an existing body with `git show --quiet <hash>`; `git log --oneline` prints subjects only.

**Language:** always English, even for commits touching the Spanish UI strings in
`src/ocr/app.py`. Spanish is user-facing only; commit messages are not. Never translate on
the way past.

Example body: "Shares one detection parser between extraction and annotation so the two
cannot drift."

## Concern categories (commit by concern, not by file)

- **engine:** `src/ocr/engine.py`, `src/ocr/config.py` — the Python OCR core
- **app:** `src/ocr/app.py`, `src/ocr/cli.py` — the Streamlit UI and entry point
- **go:** `ocr-go/cmd/`, `ocr-go/internal/`, `ocr-go/web/` — the Go service
- **tests:** `tests/`, `ocr-go/**/*_test.go`
- **docker:** `Dockerfile`, `docker-compose*.yml`, `.dockerignore`, and their `ocr-go/` counterparts
- **config:** `pyproject.toml`, `requirements*.txt`, `Makefile`, `go.mod`, `.env.example`, `.gitignore`, `.githooks/`
- **ci:** `.github/workflows/`
- **docs:** `README.md`, `CLAUDE.md`, `docs/`, `.github/instructions/`, new `.md` files
- **agent-config:** the `.claude/` directory

**Order:** dependencies before dependents — a new engine helper before the UI that calls it,
an engine fix before the tests that cover it, a config change before the code that reads it.

## Changelog

`CHANGELOG.md` is a curated, high-level record (Keep a Changelog + SemVer). Keep its
`[Unreleased]` section in step with the tree as you commit — it is maintained here, at
commit time, because that is the moment a change lands and its worth is known.

- **When** a commit is a user-visible or architectural change — a `feat`, a behaviour `fix`,
  a removal, a security fix, a change to the response shape or to an environment variable —
  add or update one line under the matching `[Unreleased]` group (Added / Changed /
  Deprecated / Removed / Fixed / Security).
- **When** a commit is internal churn with no user-visible or architectural effect — most
  `chore`, `test`, `style`, `refactor`, `ci` and `docs` — leave `CHANGELOG.md` untouched. A
  changelog that logs every commit is `git log` with extra steps; its value is that it omits.
- **Where** the entry rides in the *same commit* as the change it describes, staged alongside
  that concern's files. It is part of the change, not a separate `docs` concern, and never
  its own commit — this is the one deliberate exception to "commit by concern". Staging it
  together keeps `[Unreleased]` in lockstep with the code and spends no extra commit from
  the daily budget.
- **What** an entry says: what changed and why it matters to someone using or operating the
  project, in one line, in English. Not the file names, not the type, not the diff. "Batch
  previews cut extracted text by bytes, producing invalid UTF-8 for accented characters"
  earns its place; "refactor preview helper" does not belong in the file at all.
- **A change that spans both services** gets one entry describing the behaviour, even though
  it is two commits. The reader cares that the behaviour changed, not that this repository
  ships it twice.
- **Never** add a version heading or a date as part of a normal run. Cutting a release —
  moving `[Unreleased]` under a `## [x.y.z] - YYYY-MM-DD` heading, updating `version` in
  `pyproject.toml` and `__version__` in `src/ocr/__init__.py`, and adding the compare link
  at the foot of the file — is a separate, user-authorized step.

## When a file mixes two concerns

1. Use `Edit` to remove one concern, leaving the other
2. Stage and commit that concern
3. Use `Edit` to restore the removed text for the second concern's commit
4. Always diff the final state against the original to confirm nothing was lost or altered

## Verification requirement

- **Before any commits:** `commit.sh verify` must exit 0.
- **The pre-commit hook does not do this for you.** `.githooks/pre-commit` runs on every
  commit, but it holds only the fast per-commit invariants: the daily budget, the files that
  must never be committed, and a size ceiling. It deliberately does *not* run lint or tests —
  they are slow enough to discourage small commits, and a run that splits one file across two
  concerns would have them fire against a half-trimmed tree. Full-tree verification is yours,
  once per run.
- **When the change touches a Dockerfile or compose file:** the gates do not build images.
  Say so in the report rather than implying the build was proven.
- Verification runs once per run, on the **working tree** — not on each staged index. State
  that plainly in the report, because a reader may otherwise assume every commit was tested
  in isolation, and none of them were.
- If verify fails: **stop, report the failure, do not commit.**
