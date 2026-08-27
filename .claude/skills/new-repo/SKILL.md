---
name: new-repo
description: Create a private GitHub repository under the user's own account, with a 350-character English description, and prove the user is its only participant. User-invocable only — typing /new-repo is the authorization to create it, for that run alone.
argument-hint: "[repository name]"
allowed-tools: Bash, Read
user-invocable: true
disable-model-invocation: true
---

# /new-repo

Creates one private repository on GitHub and proves, before reporting success, that the
account it belongs to is the user's and that no one else — no agent, no service, no
second person — can reach it.

Creating a repository is outward-facing and only half-undoable: the name is claimed, and
the token here has no `delete_repo` scope, so nothing in this session can take it back.
That is why the skill is user-invocable only. **Typing `/new-repo` is the authorization,
and it covers that invocation alone.**

## Constraints (ABSOLUTE)

- **Private, always.** `--private`, never `--public`. A repository created public has
  already been public, whatever happens next.
- **Never push.** `git push` is denied by `.claude/settings.json` and pushing is the
  user's, so `gh repo create` runs without `--push` and without `--source`. This skill
  creates an empty repository; the user pushes into it.
- **Never add a collaborator**, and never accept or send an invitation.
- **One repository per invocation.** If the name is taken, stop and report — never
  retry under a modified name.
- **Stop on any identity mismatch.** Creating a repository under the wrong account is
  not fixed by editing.

## Phase 1: Confirm the account is the user's

```
.claude/scripts/repo.sh whoami
```

Prints the account `gh` will act as, its token scopes, and the identity this repository
signs commits with. Read them against each other:

- The `gh` login and the git identity must be the same person. A GitHub login is often
  capitalised differently from the git `user.name`, so compare the **email**, which is the
  field that actually matches. A login that merely looks similar is not a match.
- If `gh` reports a different person, or is not authenticated, **stop**. Do not create
  anything. Report what the account is and let the user decide.
- The token needs the `repo` scope. Without it creation fails after the name is typed,
  which is a confusing failure; check first.

## Phase 2: Write the description

GitHub caps a repository description at **350 characters** and this project uses that
whole budget: it is the only prose GitHub shows next to the name, and a private
repository has no README preview to lean on.

- **English**, like all documentation here. Spanish is user-facing UI only.
- Derive it from `README.md` and `CLAUDE.md` — what the project is, what it does with a
  document, what the two services are. Never from memory of the conversation.
- One or two sentences. Plain prose, no bullet characters, no emoji, no trailing period
  padding to reach the count.
- Count it before using it, because 351 characters is rejected by the API and the error
  does not say by how much:

```
printf '%s' "<description>" | wc -m
```

Aim between 330 and 350. Under 300 is leaving the field half empty; over 350 fails.

## Phase 3: Create it

```
gh repo create <name> --private -d "<description>"
```

Nothing else. No `--push`, no `--source`, no `--add-readme` — an empty repository is
what the user pushes their existing history into, and a README commit created here would
be a commit the user did not write.

If the command fails because the name exists, stop and report it. The user picks the
next name; you do not.

## Phase 4: Prove sole participation

```
.claude/scripts/repo.sh remote <owner>/<name>
```

Reads collaborators and pending invitations, and flags any identity matching a coding
agent. Required outcome: **the user is the only collaborator, there are no pending
invitations, and no agent identity appears.** Anything else is a finding, reported
before you report success.

Two limits to state plainly rather than paper over:

- **Installed GitHub Apps cannot be listed with this token** — `/user/installations`
  answers 403 for an OAuth token. The script prints the settings URL; the user checks it
  in the browser. Do not claim an app audit you did not perform.
- **Access and authorship are separate questions, and the script asks both.** A
  collaborator is invited; a contributor is derived from the commits. GitHub can only
  credit an author or a `Co-Authored-By` co-author whose email resolves to an account, so
  a trailer naming an agent's no-reply address stays text inside the message and never
  becomes a contributor entry. Report what the API returns, not what the trailers say, and
  do not offer to rewrite history to remove them. Commits made under this repository's
  procedure carry no trailer at all — `.githooks/commit-msg` rejects one.

## Phase 5: Report

State, in this order: the account the repository was created under and how you confirmed
it was the user's, the repository URL and that it is private, the character count of the
description, the collaborator and invitation result, and the app-installation check you
could not run. Then the push command the user runs themselves:

```
git remote add <remote-name> git@github.com:<owner>/<name>.git
git push -u <remote-name> main
```

Never run either one.
