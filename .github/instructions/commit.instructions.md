---
applyTo: '**'
---

# Commit Workflow Instructions

> **CRITICAL**: This workflow MUST be followed every time you commit changes.

## Step-by-Step Commit Process

When asked to make commits, follow these steps **in order**:

### Step 1: Review Current State
```bash
git status                    # See all modified/untracked files
git diff -U5                  # Review unstaged changes (5 lines context)
git diff --stat               # Quick summary of changes
```

### Step 2: Analyze and Group Changes
- Read each modified file to understand its purpose
- Group files by functional context (database, api, config, docs, deps)
- Decide if you need one commit or multiple commits

### Step 3: Stage and Commit by Context
For each context group:
```bash
# Stage files for this context
git add <file1> <file2> ...

# Commit with proper format: type(scope): description
git commit -m "type(scope): brief description

Optional body explaining why (not what).
Each paragraph separated by blank line."

# Verify commit was created
git status
```

### Step 4: Verify Clean State
```bash
git status                    # Should show "nothing to commit, working tree clean"
git log --oneline -3          # Verify your commits
```

### Step 5: Repeat Until Clean
- If `git status` shows uncommitted files, return to Step 3
- Continue until working tree is clean

---

## Quick Reference Card

### Commit Format
```
<type>(scope): <description>

[optional body]

[optional footer]
```

### Most Common Types
| Type | Use When | Example |
|------|----------|---------|
| `feat` | Adding new feature | `feat(api): add user login endpoint` |
| `fix` | Fixing a bug | `fix(auth): resolve token expiration issue` |
| `docs` | Documentation only | `docs: update API usage guide` |
| `chore` | Dependencies, tooling | `chore(deps): add express package` |
| `refactor` | Code restructure (no new feature/fix) | `refactor(api): simplify error handling` |
| `improvement` | Enhancement to existing code | `improvement(ui): enhance loading indicators` |

### Common Scopes
- `api` - API routes & controllers
- `database` - MongoDB & models  
- `auth` - Authentication & JWT
- `deps` - Dependencies
- `config` - Configuration files
- `docs` - Documentation

### Rules
**DO**: Use lowercase description with imperative mood ("add" not "added")  
**DO**: Write all commit messages in English only  
**DO**: Keep commits focused on single logical change  
**DO**: Group related files by context  
**DON'T**: Commit `.env` files or secrets  
**DON'T**: Use generic messages like "updates" or "changes"  
**DON'T**: Mix unrelated changes in one commit

---

## Conventional Commits Specification

### Required Format Structure

All commits MUST follow the [Conventional Commits v1.0.0](https://www.conventionalcommits.org/) specification.

```
<type>[optional scope]: <description>

[optional body]

[optional footer]
```

**Key Requirements (RFC 2119):**
- Commits MUST be prefixed with a type (noun: `feat`, `fix`, etc.)
- Type MUST be followed by OPTIONAL scope and REQUIRED colon and space
- Description MUST immediately follow the type/scope prefix
- Description should be a short summary in imperative mood (e.g., "add feature" not "added feature")
- Body MAY be provided after one blank line following description
- Footer MAY be provided after one blank line following body
- Footer MUST contain meta-information (pull requests, reviewers, breaking changes)

### Commit Types & Semantic Versioning

| Type | Description | SemVer Impact | Required Use |
|------|-------------|---------------|--------------|
| **feat** | New feature | MINOR (1.0.0 → 1.1.0) | MUST use for new features |
| **fix** | Bug fix | PATCH (1.0.0 → 1.0.1) | MUST use for bug fixes |
| **docs** | Documentation only | None | Documentation changes |
| **style** | Code formatting, whitespace | None | No code logic changes |
| **refactor** | Code restructuring | None | No feature/bug changes |
| **perf** | Performance improvement | PATCH | Performance optimization |
| **test** | Add/update tests | None | Test-related changes |
| **chore** | Build, deps, tooling | None | Maintenance tasks |
| **ci** | CI/CD configuration | None | Pipeline changes |
| **improvement** | Enhancement (non-feat) | None | Improve existing code |

**BREAKING CHANGE:**
- Can be part of ANY commit type
- MUST include `BREAKING CHANGE:` in footer (or use `!` in type/scope prefix)
- If `!` is used before `:`, the `BREAKING CHANGE:` footer MAY be omitted
- MUST consist of uppercase text BREAKING CHANGE, followed by colon, space, and description
- `BREAKING-CHANGE` MUST be synonymous with `BREAKING CHANGE` when used as a footer token
- Results in MAJOR version bump (1.0.0 → 2.0.0)

### Scope Guidelines

Scope MAY be provided to add contextual information. MUST be a noun in parentheses.

**Backend Scopes:**
- `auth` - Authentication & JWT
- `database` - MongoDB & models
- `email` - Email notifications
- `api` - API routes & controllers
- `validation` - Input validation
- `middleware` - Express middleware

**Frontend Scopes:**
- `auth` - Auth pages & flows
- `components` - React components
- `pages` - Page components
- `context` - Global state management
- `hooks` - Custom React hooks
- `styles` - CSS & Tailwind
- `config` - Configuration files

**General Scopes:**
- `docs` - Documentation
- `deps` - Dependencies
- `config` - Configuration

### Commit Examples

**Simple commit with no body:**
```
docs: correct spelling of CHANGELOG
```

**Commit with scope:**
```
feat(lang): add polish language
```

**Feature with description and body:**
```
feat(api): add user profile endpoint

Implements GET /api/users/:id endpoint with authentication.
Returns user data excluding password field.

Closes #45
```

**Fix with issue reference:**
```
fix: correct minor typos in code

see the issue for details on the typos fixed

fixes issue #12
```

**Breaking change in footer:**
```
feat: allow provided config object to extend other configs

BREAKING CHANGE: `extends` key in config file is now used for extending other config files
```

**Breaking change with ! notation:**
```
chore!: drop Node 6 from testing matrix

BREAKING CHANGE: dropping Node 6 which hits end of life in April
```

**API structure change:**
```
feat(api)!: change user response structure

BREAKING CHANGE: user endpoints now return wrapped in 'data' object

Before: { _id: "...", name: "..." }
After: { data: { _id: "...", name: "..." } }
```

**Improvement (non-breaking enhancement):**
```
improvement(ui): enhance loading state indicators

Added skeleton loaders for data-fetching components.
Improves perceived performance and user experience.
```

### Conventional Commits Specification Rules

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT", "RECOMMENDED", "MAY", and "OPTIONAL" in this specification are to be interpreted as described in [RFC 2119](https://www.ietf.org/rfc/rfc2119.txt).

1. Commits MUST be prefixed with a type, which consists of a noun, `feat`, `fix`, etc., followed by a REQUIRED colon and space.
2. The type `feat` MUST be used when a commit adds a new feature to your application or library.
3. The type `fix` MUST be used when a commit represents a bug fix for your application.
4. A scope MAY be provided after a type. A scope MUST consist of a noun describing a section of the codebase surrounded by parenthesis, e.g., `fix(parser):`.
5. A description MUST immediately follow the colon and space after the type/scope prefix. The description is a short summary of the code changes, e.g., _fix: array parsing issue when multiple spaces were contained in string._
6. A longer commit body MAY be provided after the short description, providing additional contextual information about the code changes. The body MUST begin one blank line after the description.
7. A commit body is free-form and MAY consist of any number of newline separated paragraphs.
8. One or more footers MAY be provided one blank line after the body. Each footer MUST consist of a word token, followed by either a `:<space>` or `<space>#` separator, followed by a string value (this is inspired by the [git trailer convention](https://git-scm.com/docs/git-interpret-trailers)).
9. A footer's token MUST use `-` in place of whitespace characters, e.g., `Acked-by` (this helps differentiate the footer section from a multi-paragraph body). An exception is made for `BREAKING CHANGE`, which MAY also be used as a token.
10. A footer's value MAY contain spaces and newlines, and parsing MUST terminate when the next valid footer token/separator pair is observed.
11. Breaking changes MUST be indicated in the type/scope prefix of a commit, or as an entry in the footer.
12. If included as a footer, a breaking change MUST consist of the uppercase text BREAKING CHANGE, followed by a colon, space, and description, e.g., _BREAKING CHANGE: environment variables now take precedence over config files._
13. If included in the type/scope prefix, breaking changes MUST be indicated by a `!` immediately before the `:`. If `!` is used, `BREAKING CHANGE:` MAY be omitted from the footer section, and the commit description SHALL be used to describe the breaking change.
14. Types other than `feat` and `fix` MAY be used in your commit messages, e.g., _docs: updated ref docs._
15. The units of information that make up Conventional Commits MUST NOT be treated as case sensitive by implementors, with the exception of BREAKING CHANGE which MUST be uppercase.
16. BREAKING-CHANGE MUST be synonymous with BREAKING CHANGE, when used as a token in a footer.

### Why Use Conventional Commits?

- Automatically generate CHANGELOGs
- Automatically determine semantic version bumps
- Communicate nature of changes to team and stakeholders
- Trigger build and publish processes
- Make it easier for contributors to explore structured commit history
- Enable automated tooling and workflows

### FAQ & Best Practices

**Q: How to handle initial development phase?**  
A: Proceed as if you've released the product. Users (even fellow developers) need to know what's fixed or broken.

**Q: What if commit fits multiple types?**  
A: Make multiple commits. Conventional Commits drives organized commits and PRs.

**Q: Wrong commit type used?**  
A: Before merge: use `git rebase -i` to edit. After release: depends on your workflow.

**Q: Does this slow development?**  
A: It discourages disorganized development. Helps move fast long-term across projects with varied contributors.

**Q: Do all contributors need to follow this?**  
A: No. With squash-based workflows, maintainers can clean up commit messages during merge.

**Q: Uppercase or lowercase types?**  
A: Any casing works, but be consistent throughout the project.

### Naming Conventions

| Element | Pattern | Example |
|---------|---------|---------|
| Database Models | PascalCase | `Usuario.js`, `Registrado.js` |
| Controllers | camelCase + "Controllers" | `usuarioControllers.js` |
| Routes | camelCase + "Routes" | `usuarioRoutes.js` |
| React Components | PascalCase | `Header.jsx`, `Listado.jsx` |
| Hooks | camelCase + "use" prefix | `useAuth.jsx`, `useRegistrados.jsx` |
| CSS Classes | kebab-case | `.form-container`, `.btn-primary` |
| Environment variables | UPPER_SNAKE_CASE | `MONGO_URI`, `JWT_SECRET` |

### Before Committing

1. **Review changes with Git commands**:
   - `git status` - Check which files are modified, staged, or untracked
   - `git diff` - See unstaged changes with 3 lines of context (default)
   - `git diff -U5` - See unstaged changes with 5 lines of context (recommended for better clarity)
   - `git diff --staged` - Review changes that will be committed
   - `git diff --staged -U5` - Review staged changes with more context
   - `git diff --stat` - Show summary of changed files with additions/deletions count
   - `git diff <file>` - View changes for a specific file only
   - `git log --oneline -10` - Check recent 10 commits for context and patterns
   - `git log --oneline --graph -10` - View commit history with branch visualization
   - `git show` - View the last commit details with diff
   - `git show --stat` - View last commit summary without full diff
2. **Group changes by context**:
   - Review each modified file to understand its purpose and scope
   - Determine if changes belong to a single context or multiple contexts
   - Consider creating separate commits for different scopes (e.g., database, api, docs)
3. Code passes linting rules
4. All tests pass (if applicable)
5. No `.env` files or secrets committed
6. No commented-out code unless documented
7. Changes align with project architecture
8. Commit message follows Conventional Commits format

### Commit Message Checklist

Before committing, ensure:

 - [ ] **Review Git context**:
  - [ ] Run `git status` to see modified files
  - [ ] Run `git diff` or `git diff -U5` to understand unstaged changes with adequate context
  - [ ] Run `git diff --staged` or `git diff --staged -U5` to verify what will be committed
  - [ ] Run `git diff --stat` for a quick summary of changed files
  - [ ] Check `git log --oneline -10` for recent commit patterns and history
  - [ ] Use `git diff <file>` to focus on specific file changes
- [ ] Type is valid: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, or `improvement`
- [ ] Type MUST be followed by colon and space (e.g., `feat: ` not `feat:`)
- [ ] Scope is relevant and follows noun format in parentheses (if used)
- [ ] Description is clear, concise, and uses imperative mood ("add" not "added")
- [ ] Description starts with lowercase (e.g., `feat: add feature` not `feat: Add feature`)
- [ ] Body explains "why" not "what" (when needed)
- [ ] Body and footer are separated from description and each other by blank lines
- [ ] Breaking changes use `BREAKING CHANGE:` in body or footer (uppercase required)
- [ ] Breaking changes MAY use `!` notation: `feat!:` or `feat(scope)!:`
- [ ] Related issues are referenced (e.g., `Closes #123`, `Fixes #45`)
- [ ] No `.env` files, secrets, or debug code included
- [ ] Commit is focused on single logical change
 - [ ] Commit message is written in English

### Semantic Versioning Mapping (SemVer)

Commits automatically determine version bumps:

- `fix` commits → **PATCH** release (1.0.0 → 1.0.1)
- `feat` commits → **MINOR** release (1.0.0 → 1.1.0)
- `BREAKING CHANGE` → **MAJOR** release (1.0.0 → 2.0.0)
- Other types → No version impact (unless BREAKING CHANGE included)

## Best Practices

1. **Small, Focused Commits**: One feature or fix per commit
2. **Descriptive Messages**: Help future developers understand changes
3. **No Debug Code**: Remove console.logs before committing
4. **Test Coverage**: Add tests for new features and critical fixes
5. **Documentation**: Update README or docs when adding new features
6. **Code Review**: Request reviews before merging to main

### Organizing Commits by Context

When you have multiple modified files, create separate commits grouped by their functional context:

**Workflow:**
1. Run `git status` to see all modified and untracked files
2. If files are already staged, unstage them: `git reset HEAD .`
3. Review each file's changes with `git diff <file>` or `git diff -U5 <file>` for more context
4. Group files by their scope/context (database, api, config, docs, etc.)
5. Stage and commit each group separately with appropriate type and scope

**Example Workflow:**
```bash
# Check current status
git status

# Review changes with context (use -U5 for 5 lines of context instead of default 3)
git diff --stat          # Quick summary
git diff -U5             # Detailed diff with more context

# Unstage all if needed
git reset HEAD .

# Review specific file changes
git diff -U5 backend/controllers/veterinarioController.js

# Commit by context
git add .gitignore && git commit -m "chore: update .gitignore"
git add backend/config/db.js && git commit -m "fix(database): improve connection handling"
git add backend/index.js && git commit -m "improvement(api): add error handling"
git add backend/models/ && git commit -m "feat(database): add Veterinario model"
git add backend/routes/ && git commit -m "feat(api): add veterinario routes"
git add docs/ && git commit -m "docs: add project documentation"

# Verify commits
git log --oneline -6
git log --oneline --graph -10  # With branch visualization
```

**When to use single vs. multiple commits:**
- **Single commit**: All changes belong to the same scope and feature (e.g., only updating API endpoints)
- **Multiple commits**: Changes span different scopes/concerns (e.g., database models + API routes + documentation)

**Context grouping guidelines:**
| Files Changed | Suggested Grouping | Commit Type |
|---------------|-------------------|-------------|
| `.gitignore`, `.env.example` | Configuration/tooling | `chore` or `chore(config)` |
| `backend/config/db.js` | Database configuration | `fix(database)` or `feat(database)` |
| `backend/models/*.js` | Data models | `feat(database)` |
| `backend/routes/*.js` | API endpoints | `feat(api)` |
| `backend/controllers/*.js` | Request handlers | `feat(api)` or `refactor(api)` |
| `backend/middleware/*.js` | Middleware | `feat(middleware)` |
| `docs/*`, `README.md` | Documentation | `docs` |
| `frontend/src/components/*.jsx` | UI components | `feat(components)` |
| `frontend/src/pages/*.jsx` | Pages | `feat(pages)` |
| `package.json` | Dependencies | `chore(deps)` |

## Common Pitfalls to Avoid

**Generic messages** - "fix stuff", "updates", "changes"  
**Multiple unrelated changes** - One commit doing too many things  
**Committing sensitive data** - `.env` files, API keys, secrets  
**Not specifying breaking changes** - Missing `BREAKING CHANGE:` notation  
**Wrong commit type** - Using `chore` instead of `feat` for new features  
**Incorrect format** - Missing colon, wrong spacing, capitalized description  
**Debug code** - Console.logs, commented code without documentation  
**Case sensitivity errors** - `breaking change:` instead of `BREAKING CHANGE:`  

**Clear, specific messages** - Describe what changed and why  
**Logical, atomic commits** - One feature/fix per commit  
**Conventional format** - Follow `type(scope): description` exactly  
**Explicit breaking changes** - Use both `!` and `BREAKING CHANGE:` for visibility  
**Correct type classification** - `feat` for features, `fix` for bugs  
**Imperative mood** - "add feature" not "added feature"  
**Lowercase description** - `feat: add feature` not `feat: Add Feature`  

## Tools & Automation

**Recommended Tools:**
- `commitlint` - Lint commit messages
- `husky` - Git hooks for pre-commit validation
- `standard-version` - Automated versioning and CHANGELOG generation
- `semantic-release` - Fully automated package releases

**Example commitlint config** (`.commitlintrc.json`):
```json
{
  "extends": ["@commitlint/config-conventional"],
  "rules": {
    "type-enum": [2, "always", [
      "feat", "fix", "docs", "style", "refactor",
      "perf", "test", "chore", "ci", "improvement"
    ]]
  }
}
```

## Resources

- [Conventional Commits Specification](https://www.conventionalcommits.org/)
- [Semantic Versioning](https://semver.org/)
- [Express.js Best Practices](https://expressjs.com/)
- [React Best Practices](https://react.dev/)