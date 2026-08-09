---
name: ask-before-commit-or-push
description: Always ask Alexis before running git commit or git push — including in auto/bypass mode and inside subagents
metadata:
  type: feedback
---

Never run `git commit` or `git push` without asking Alexis first. This holds **even in auto-accept /
bypass-permissions mode**, where the harness would otherwise let the call through unprompted, and it
applies to subagents too — when delegating implementation work, tell the subagent explicitly not to
commit, and make the commit yourself only after Alexis approves.

**Why:** permission mode controls what the harness blocks, not what Alexis wants reviewed. He wants to
see the staged change and the commit message before either becomes part of the branch's history, because
rewriting a commit after the fact is more disruptive than approving one up front. Stated 2026-07-30 after
a bmad-quick-dev implementation subagent committed on its own.

**How to apply:** finish the work, show the diff and the proposed commit message, then wait. Applies to
`git commit --amend` and any commit-creating helper too. Pushing additionally opens or updates a PR, so
it always needs its own explicit approval — see [[no-coauthor-in-commits.md]] for what must never appear
in the message itself.
