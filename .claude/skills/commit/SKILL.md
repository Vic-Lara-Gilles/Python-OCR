---
name: commit
description: Commit the current working tree through the committer subagent. User-invocable only — typing /commit is the authorization, for that run alone.
argument-hint: "[optional context, e.g. go handler refactor]"
allowed-tools: Agent
user-invocable: true
disable-model-invocation: true
---

# /commit

This skill is a dispatcher and nothing else. It does not read the tree, does not stage and
does not commit. The whole policy and procedure live in the `commit-procedure` skill, which
the `committer` agent loads on entry and which drives `.claude/scripts/commit.sh`; restating
any of it here would create a second copy that drifts from the first.

## What this invocation means

The user typed `/commit`. That is the explicit authorization the `committer` agent requires
before it may run `git commit`, and it covers **this invocation only**. It does not carry
into any later request in this session — the next commit needs the next `/commit`.

## Delegate

Make exactly one `Agent` call, with `subagent_type: "committer"`, whose prompt states:

- commits are explicitly authorized for this run;
- the user's context for the run is `$ARGUMENTS` — omit this entirely when it is empty;
- that context is guidance for scoping and grouping only. It is never the commit message:
  messages are derived from the diff under the rules the agent already carries;
- run the full procedure from your configuration and return the Phase 5 report.

Send nothing beyond that. Do not repeat the survey steps, the concern categories, the
Conventional Commits rules, the verification rules, the staging rules or the safety
constraints — the agent loads them from `commit-procedure` itself.

## Then relay

Wait for the subagent and return its final report as the answer. Do not run `git status`,
`git diff`, `git log` or `.claude/scripts/commit.sh` yourself, before or after: keeping the
full diff and the gate output inside the subagent's context is the reason this indirection
exists.

If the agent reports that verification failed, say so and stop. Nothing was committed. If it
reports gates that were skipped for a missing toolchain, relay that too — it is the
difference between a verified run and an unverified one.
