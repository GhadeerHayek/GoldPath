## What changed

<!-- One or two sentences. What does this PR do, and what problem does it solve? -->

## Why

<!-- The reasoning, not the diff. If this implements a decision recorded in an
ADR, link it. If it *is* a decision, say so — it probably needs one. -->

Linear issue:

## Risk

<!-- Delete the lines that do not apply. -->

- [ ] Touches the database schema (needs an Alembic migration — `metadata.create_all` is not how this project builds schema)
- [ ] Touches CI, deployment, or agent configuration
- [ ] Adds or changes a dependency
- [ ] Changes what credentials a workflow can reach

## How this was verified

<!-- "CI is green" is not verification on its own — CI passing means nothing
broke, not that the new thing works. Say what you actually exercised. -->

---

<!-- For agent-authored PRs: the checks on this PR are the gate, not the
review comment. A PR merges automatically only if the linked issue carries the
`agent-autonomous` label; everything else waits for a human. -->
