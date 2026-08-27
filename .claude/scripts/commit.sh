#!/usr/bin/env bash
#
# Command bundles for the `committer` agent.
#
# Each subcommand is one shell round-trip that would otherwise be several tool
# calls, each re-paying for its own invocation and its own output. Bundling them
# here keeps the agent's context on the diff itself instead of on shell plumbing,
# and guarantees every run inspects the tree the same way.
#
# Usage: .claude/scripts/commit.sh <survey|staged|verify|report [n]>

set -uo pipefail

cd "$(git rev-parse --show-toplevel)" || exit 1

survey() {
  echo "== branch =="
  git rev-parse --abbrev-ref HEAD
  echo
  echo "== status (tracked + untracked) =="
  git status --short --untracked-files=all
  echo
  echo "== diffstat vs HEAD =="
  git diff --stat HEAD
  echo
  echo "== full diff vs HEAD (staged and unstaged, tracked files) =="
  git diff HEAD
  echo
  echo "== untracked files (paths only — read the ones you need) =="
  git ls-files --others --exclude-standard | while read -r f; do
    printf '%6s lines  %s\n' "$(wc -l <"$f" 2>/dev/null || echo '?')" "$f"
  done
  echo
  # The daily budget belongs to the same read as the tree: .githooks/pre-commit
  # refuses the 61st commit of a day, and a split that does not fit in what is
  # left must be re-planned before the first commit, not discovered halfway.
  echo "== daily commit budget =="
  printf 'spent today: %s of 60\n' "$(git log --branches --since=midnight --oneline | wc -l | tr -d ' ')"
  if [ "$(git config --get core.hooksPath)" != ".githooks" ]; then
    echo "note: hooks are NOT installed (run: make hooks) — the budget and the"
    echo "      message format are unenforced for this tree."
  fi
}

# What is about to be committed, as one read. The message is written from this and
# nothing else: the survey shows the whole tree, but a commit contains only its index,
# and a message derived from the tree describes work the commit does not carry.
staged() {
  echo "== staged diffstat =="
  git diff --cached --stat
  echo
  echo "== staged diff =="
  git diff --cached
}

# A passing gate has nothing to say, so it says one line: its output is only worth
# context when it fails, and then it is worth more of it than a passing run ever was.
run_gate() {
  local label=$1 out status log
  shift
  out=$("$@" 2>&1)
  status=$?
  if [ "$status" -eq 0 ]; then
    printf '%s passed\n' "$label"
  else
    # The tail is what fits in context; the whole run is kept on disk so a failure
    # that needs more can be grepped instead of re-run.
    log=$(mktemp -t commit-gate)
    printf '%s\n' "$out" >"$log"
    printf '%s FAILED (exit %s)\n' "$label" "$status"
    printf 'full output: %s\n\n' "$log"
    printf '%s\n' "$out" | tail -80
  fi
  return "$status"
}

# A gate whose toolchain is absent must not read as a passing gate. It reports why
# it could not run, and the caller is required to carry that into the final report.
skip_gate() {
  printf '%s SKIPPED — %s\n' "$1" "$2"
}

have() { command -v "$1" >/dev/null 2>&1; }

# Whether the tree touches a service at all. Gates for an untouched service are
# noise: they cost a toolchain check and prove nothing about this run's changes.
touches() {
  git status --porcelain --untracked-files=all | grep -qE "^.{3}$1"
}

python_gates() {
  local failed=0

  if have ruff; then
    run_gate "ruff" ruff check src/ tests/ || failed=1
  elif python3 -c "import ruff" 2>/dev/null; then
    run_gate "ruff" python3 -m ruff check src/ tests/ || failed=1
  else
    skip_gate "ruff" "not installed (make install)"
  fi

  if have black; then
    run_gate "black" black --check src/ tests/ || failed=1
  elif python3 -c "import black" 2>/dev/null; then
    run_gate "black" python3 -m black --check src/ tests/ || failed=1
  else
    skip_gate "black" "not installed (make install)"
  fi

  if python3 -c "import pytest" 2>/dev/null; then
    run_gate "pytest" python3 -m pytest tests/ -q || failed=1
    have tesseract || echo "  note: tesseract absent — the OCR tests skipped themselves"
  else
    skip_gate "pytest" "not installed (make install)"
  fi

  return "$failed"
}

go_gates() {
  local failed=0

  if ! have go; then
    skip_gate "go vet" "go toolchain not installed"
    skip_gate "go test" "go toolchain not installed"
    return 0
  fi

  if [ ! -f ocr-go/go.sum ]; then
    skip_gate "go vet" "ocr-go/go.sum missing (cd ocr-go && go mod tidy)"
    skip_gate "go test" "ocr-go/go.sum missing (cd ocr-go && go mod tidy)"
    return 0
  fi

  run_gate "go vet" env -C ocr-go go vet ./... || failed=1
  run_gate "go test" env -C ocr-go go test -race ./... || failed=1

  return "$failed"
}

verify() {
  local failed=0 ran=0

  if touches "(src/ocr/|tests/|pyproject.toml|requirements)"; then
    ran=1
    python_gates || failed=1
  else
    echo "python gates skipped — tree does not touch the Python service"
  fi

  echo

  if touches "ocr-go/"; then
    ran=1
    go_gates || failed=1
  else
    echo "go gates skipped — tree does not touch the Go service"
  fi

  if [ "$ran" -eq 0 ]; then
    echo
    echo "No code gates apply to this tree (docs or config only)."
  fi

  return "$failed"
}

report() {
  echo "== status after committing =="
  git status --short
  echo
  echo "== new history =="
  git log --oneline -"${1:-10}"
}

case "${1:-}" in
  survey) survey ;;
  staged) staged ;;
  verify) verify ;;
  report) report "${2:-10}" ;;
  *)
    echo "usage: $0 <survey|staged|verify|report [n]>" >&2
    exit 64
    ;;
esac
