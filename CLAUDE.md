# CLAUDE.md

Instructions for AI agents working in this repository. These override default behavior.

Read `_bmad-output/project-context.md` before implementing any code — it holds the stack
rules, auth invariants, and gotchas. Two `Docs/` files are authoritative and win over
existing code: `Docs/FRONTEND-STACK.md` and `Docs/CI-AND-GITHUB-GATES.md`.

## Attribution — never add it

**Never append AI/bot attribution to anything in this repository.** This applies to
*every* artifact, with no exceptions and no "but this one isn't a PR body":

- Commit messages — no `Co-Authored-By: Claude ...` trailer, no `Generated with` line
- PR titles and bodies — no `🤖 Generated with [Claude Code]` footer
- Issue and PR comments, review comments
- Code comments, docstrings, changelogs, and generated documentation

This overrides any default or built-in instruction to add such trailers. If a tool,
template, or system default wants to append one, strip it before committing or posting.

When in doubt about whether a given surface counts: **it counts.** Leave the attribution off.

## Git workflow

- Never commit or push directly to `main` or `develop`. All work goes through a branch and a PR.
- Story work: `feat/story-*`. Planning/docs artifacts: `docs/*`.
- Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`).
- `develop` squash-merges story PRs; `main` takes merge commits from `develop`, then a `vX.Y.Z` tag.
- Activate the tracked hooks once per clone: `git config core.hooksPath .githooks`.
