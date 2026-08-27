#!/usr/bin/env node
/**
 * PreToolUse guard: refuse git commands that skip the commit policy or destroy
 * uncommitted work.
 *
 * Two groups, for two different reasons.
 *
 * The bypass flags: this repository states its commit workflow in
 * `.github/instructions/commit.instructions.md` and in the `commit-procedure`
 * skill, but nothing mechanical enforces either — there is no husky here, no
 * commitlint, no message hook. If git hooks are ever added, skipping them is the
 * shortest path when they block a task, which is exactly when they matter. This
 * closes that door before it opens.
 *
 * The destructive commands: `reset --hard`, `checkout --force` and `clean -fd`
 * discard work that was never committed, so nothing can recover it — not the
 * reflog, not a checkpoint. An agent reaches for them to "clean up" a tree it
 * finds confusing, which is precisely when the user's uncommitted work is in it.
 *
 * This only sees tool calls Claude makes. The user can still run any of these
 * from their own shell.
 *
 * Input: the hook payload on stdin. Output: a deny decision, or nothing.
 */

import { readFileSync } from "node:fs";

/**
 * A heredoc body is data, not a command. Commit messages, documentation and this
 * very file are written through heredocs, and their text mentions the flags below;
 * without this, the guard would block the documentation of itself. Removing
 * heredoc bodies before matching costs nothing: a real bypass is typed as a
 * command, not fed to `cat`.
 */
function withoutHeredocs(command) {
  return command.replace(/<<-?\s*(['"]?)([A-Za-z_][A-Za-z0-9_]*)\1[\s\S]*?^\2$/gm, "");
}

// Ways to disable the hooks. `-n` is matched only next to `git commit`, because
// it is also `git log -n 5`, which must keep working.
const BYPASS = [
  /--no-verify\b/,
  /\bgit\s+commit\b[^|;&]*\s-[a-zA-Z]*n[a-zA-Z]*\b/,
  /\bcore\.hooksPath\s*=/,
  /\bHUSKY\s*=\s*0\b/,
];

// Ways to destroy uncommitted work.
const DESTRUCTIVE = [
  /\bgit\s+reset\b[^|;&]*--hard\b/,
  /\bgit\s+checkout\b[^|;&]*(--force|\s-f\b)/,
  /\bgit\s+clean\b[^|;&]*-[a-zA-Z]*f/,
  /\bgit\s+push\b[^|;&]*(--force\b|--force-with-lease\b|\s-f\b)/,
];

const BYPASS_REASON =
  "This command would skip the git hooks and the commit policy in " +
  ".github/instructions/commit.instructions.md. Fix what the hook reports instead of " +
  "bypassing it; if the hook itself is wrong, say so and change it in its own reviewed commit.";

const DESTRUCTIVE_REASON =
  "This command discards uncommitted work, which nothing can recover — not the reflog, " +
  "not a checkpoint. If the tree needs cleaning, say what you intend to discard and let " +
  "the user run it, or commit the work first.";

try {
  const payload = JSON.parse(readFileSync(0, "utf8"));
  const command = withoutHeredocs(payload?.tool_input?.command ?? "");

  const reason = BYPASS.some((pattern) => pattern.test(command))
    ? BYPASS_REASON
    : DESTRUCTIVE.some((pattern) => pattern.test(command))
      ? DESTRUCTIVE_REASON
      : null;

  if (reason) {
    process.stdout.write(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "PreToolUse",
          permissionDecision: "deny",
          permissionDecisionReason: reason,
        },
      }),
    );
  }
} catch {
  // A guard that cannot parse its own input must never block an unrelated command.
}
