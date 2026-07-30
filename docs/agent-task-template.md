# Writing an issue an agent can actually finish

This is the contract between a Linear issue and the pipeline. It exists because
of one constraint that shapes everything else:

> **The merge gate is deterministic. If "done" cannot be expressed as something
> CI can check, the agent cannot merge autonomously — and probably should not be
> doing the task at all.**

An agent does not ask a clarifying question at 2am. It fills gaps in the spec
with guesses, and a guess that passes CI is worse than a failure, because it
merges. The template's whole job is to remove the gaps.

Mirror this into Linear as the template for issues labelled `agent-ready`.

---

## The template

```markdown
## Outcome

<!-- What is observably true when this is finished? One or two sentences,
written as a state of the world, not as a task list.

Good:  `GET /notes/{id}` returns 404 with `{"detail": "Not found"}` for an id
       that does not exist, instead of raising a 500.
Bad:   Fix the notes endpoint. -->

## Acceptance criteria

<!-- Each line must be checkable by a machine or by a one-line command. If a
criterion needs judgement to evaluate, it is a design decision and belongs in
an ADR before it reaches an agent. -->

- [ ]
- [ ]

## Tests

<!-- Name the test that proves this. Either an existing test that must still
pass, or a new test the agent must write. "Add tests" is not a specification;
"add a test asserting 404 on a missing id" is.

An agent-ready issue with no test requirement is a red flag: it means nothing
will detect a regression, so the change cannot be verified after merge either. -->

- Test to add or extend:
- Must continue to pass:

## Scope

**In scope:**
<!-- Specific files or modules. Bounded scope is what keeps the diff reviewable
and stops the agent refactoring adjacent code it happens to dislike. -->

**Out of scope:**
<!-- State this even when it feels obvious. "Do not change the response schema"
prevents a whole class of plausible-looking overreach. -->

## Autonomy

<!-- Tick only if EVERY box in the checklist below is true. See "What earns
autonomous merge". -->

- [ ] Eligible for `agent-autonomous`

## Context

<!-- Links: the ADR that constrains this, prior related issues, the failing log
or reproduction. Do not paste credentials, tokens, or production data — the
agent reads this text, and so does anyone who can see the repository. -->
```

---

## What earns autonomous merge

`agent-autonomous` means the PR merges on green with no human in the loop. It
applies only when **all** of these hold:

| Condition | Why |
|---|---|
| No database schema change or migration | A migration that passes CI can still break production. This is the MindVault failure mode — schema built at startup, tests on in-memory SQLite — and it is exactly what a green check fails to catch |
| No new or upgraded dependency | Adds supply-chain surface that no test in the repo evaluates |
| Does not touch the privilege surface | Enforced independently by `privileged-changes`; listing it here keeps the reasoning visible |
| Confined to a single module | Keeps the diff reviewable after the fact, and limits the blast radius of a wrong guess |
| No change to a public API contract | A shape change breaks callers that no test in this repo exercises |
| Success is checkable by an existing or specified test | Without this, "green" means "nothing detected", not "it works" |

Anything else is still a perfectly good agent task — it just gets a human merge.
The label is about who presses merge, not whether the agent may attempt it.

---

## Tasks that are not suitable for an agent

Not "hard" tasks. **Unverifiable** ones:

| Issue | Problem |
|---|---|
| "Improve performance of the notes endpoint" | No measurable finish line. The agent will make a change and assert it is faster |
| "Refactor the database layer" | No observable behaviour change, so nothing can confirm success or detect breakage |
| "Fix the bug users reported" | The specification is in someone's head |
| "Make the error messages friendlier" | Requires product judgement; the agent will invent a house style |
| "Add tests" | Unbounded. The agent will write tests that pass rather than tests that would catch a regression |

The repair is usually the same: state the observable outcome. "Improve
performance" becomes "`GET /notes` responds in under 200ms with 1,000 rows
seeded, asserted by a test."

---

## A note on issue text as untrusted input

The agent reads the issue body. That text is the agent's instructions, which
means **anyone who can file an issue can attempt to instruct the agent.**

Two consequences for how the pipeline is built, both already enforced:

1. **The trigger is the `agent-ready` label, not the issue.** Filing an issue
   starts nothing. A human with write access applying the label is the
   authorisation step, and it is checked rather than assumed.
2. **The agent's output is gated by checks that do not trust it.**
   `privileged-changes` blocks any agent PR that touches CI, review routing, or
   reaches for a credential — regardless of what the issue said.

So a hostile issue is not a privilege-escalation route. It is at worst a wasted
agent run, and only if someone with write access labels it.

Practically, for whoever writes the issue: never paste a secret, token, or
production record into one.
