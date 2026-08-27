#!/usr/bin/env node
/**
 * PostToolUse hint for edits with a coupled follow-up step — the engine.
 *
 * This repository couples files that nothing links mechanically: the settings
 * dataclass to `.env.example` and the README table, the Go JSON tags to the
 * frontend that reads them by name, the two services to each other. None of
 * those couplings is visible from the file being edited, and no gate reports
 * them. This states the coupling at the moment it is created, instead of
 * leaving it to be rediscovered when something breaks in production.
 *
 * The rules themselves live in `../config/pipeline-hints.json` so they can be
 * read and edited without touching this file, and so a second consumer (a hook
 * matching a different tool) can share one table instead of copying it.
 *
 * Input: the hook payload on stdin. Output: JSON carrying `additionalContext`,
 * or nothing when the edited path has no coupled step. Never fails the tool
 * call: any error exits 0 silently, because a missing hint must never block an
 * edit.
 */

import { readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const HERE = dirname(fileURLToPath(import.meta.url));
const CONFIG = join(HERE, "..", "config", "pipeline-hints.json");

try {
  const payload = JSON.parse(readFileSync(0, "utf8"));
  const path = payload?.tool_input?.file_path ?? payload?.tool_response?.filePath ?? "";
  const { rules } = JSON.parse(readFileSync(CONFIG, "utf8"));

  const rule = rules.find(({ pattern }) => new RegExp(pattern).test(path));
  if (rule) {
    process.stdout.write(
      JSON.stringify({
        hookSpecificOutput: {
          hookEventName: "PostToolUse",
          additionalContext: rule.hint,
        },
      }),
    );
  }
} catch {
  // A hint is best-effort: never turn a parsing or config problem into a failed edit.
}
