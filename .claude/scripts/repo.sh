#!/usr/bin/env bash
#
# Command bundles for the `new-repo` skill.
#
# Same reason as commit.sh: each subcommand is one shell round-trip that would
# otherwise be several tool calls, and bundling them guarantees every run asks
# the same questions in the same way. These questions have one right answer and
# no room for improvisation — whose account is this, and does anyone but its
# owner appear on the repository — so they are written down once, here.
#
# Usage: .claude/scripts/repo.sh <whoami|remote <owner/name>>

set -uo pipefail

cd "$(git rev-parse --show-toplevel)" || exit 1

# Who must never appear as an author, a co-author or a collaborator. Matched
# case-insensitively against names, emails and logins.
AGENTS='claude|codex|anthropic|openai|copilot|cursor|devin|gemini'

# The account gh will act as, next to the identity this repository signs with.
# They are printed together because the check is whether they are the same
# person, and a mismatch is the one thing that must stop a run: creating a
# repository under an account the user does not own is not undoable by editing.
whoami_() {
  echo "== gh account =="
  gh api user --jq '"login: " + .login, "name:  " + (.name // "—"), "email: " + (.email // "— (private)")' 2>/dev/null ||
    { echo "gh is not authenticated. Run: gh auth login"; return 1; }
  echo
  echo "== token =="
  gh auth status 2>&1 | grep -E "Token scopes|Logged in"
  echo
  echo "== this repository signs as =="
  echo "name:  $(git config user.name)"
  echo "email: $(git config user.email)"
}

# The remote side: who can reach the repository, and who has been asked to.
remote_() {
  local repo="${1:?usage: repo.sh remote <owner/name>}"
  echo "== collaborators =="
  gh api "repos/$repo/collaborators" --jq '.[] | .login + " (" + .role_name + ")"'
  echo
  echo "== pending invitations =="
  gh api "repos/$repo/invitations" --jq 'if length == 0 then "none" else .[] | .invitee.login end'
  echo
  echo "== contributors (what the repository page shows) =="
  # anon=1 also lists authors whose email resolves to no account, which is the
  # only way an agent could appear here without ever being invited.
  gh api "repos/$repo/contributors?anon=1&per_page=100" \
    --jq 'if length == 0 then "none yet (nothing pushed)" else .[] | (.login // (.name + " <" + .email + ">")) end'
  echo
  echo "== agent identities among them =="
  {
    gh api "repos/$repo/collaborators" --jq '.[].login'
    gh api "repos/$repo/invitations" --jq '.[].invitee.login'
    gh api "repos/$repo/contributors?anon=1&per_page=100" --jq '.[] | (.login // .name)'
  } | grep -iE "$AGENTS" || echo "none"
  echo
  echo "note: installed GitHub Apps cannot be listed with this token (403 on"
  echo "/user/installations). Check them at https://github.com/$repo/settings/installations"
}

case "${1:-}" in
  whoami) whoami_ ;;
  remote) remote_ "${2:-}" ;;
  *)
    echo "usage: $0 <whoami|remote <owner/name>>" >&2
    exit 64
    ;;
esac
