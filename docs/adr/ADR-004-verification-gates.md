# ADR-004 — Verification gates, and who writes the tests

- **Status:** Accepted — implementation deferred until the suite is non-trivial
- **Date:** 2026-07-30
- **Area:** code review
- **Related:** ADR-002 (trust boundaries), ADR-005 (merge policy)

## Context

When code generation is cheap, **verification becomes the bottleneck.** The
pipeline is a verification loop wrapped around the agent's own verification loop,
and this ADR decides what the outer loop actually checks.

The problem it has to solve is independence. If the agent writes both the
implementation and the test, the test asserts what the code *does*, not what it
*should* do. A green suite then demonstrates self-consistency, not correctness —
the same structural flaw as an agent reviewing its own work. "The agent added
tests and they pass" is close to meaningless on its own.

So: what blocks a merge, what merely informs, and where does the quality metric
live?

## Findings — what large engineering orgs actually do

Worth establishing, because the intuitive answer (gate on a coverage number) is
not what the organisations with the most experience do.

**Google measures coverage and deliberately does not mandate it.** Their
published guidance offers 60% as acceptable, 75% commendable, 90% exemplary,
while explicitly avoiding top-down mandates — each team picks its own number.
Two points from it outweigh the percentages:

- **"What's not covered is more meaningful than what is covered."** The value is
  a human reading the *uncovered* lines, not the ratio.
- **New code should meet the threshold.** That is patch coverage, reached from
  operational experience rather than theory.
- Returns past ~90% are logarithmic, so chasing 95% is waste.

**Meta has moved past coverage as an objective.** Their current system is
mutation-guided rather than coverage-guided: it targets injected faults, was
deployed across Facebook, Instagram, WhatsApp and wearables, and privacy
engineers accepted 73% of the tests it generated over thousands of mutants. Their
own framing is the decisive line:

> The system often increases coverage as a side effect of targeting faults, but
> **coverage is not the primary objective.**

Coverage is an output there, not a goal. The earlier TestGen-LLM work established
the mechanism both generations share — **assured generation**: the model's output
is a *candidate*, and the harness accepts it only if it compiles, passes
reliably, measurably improves the suite, and breaks nothing. The filter is
mechanical; the LLM is never trusted.

## The argument that decides this ADR

Coverage-as-target is Goodhart's law, which every engineering org learns slowly.
**With an agent the loop is faster and the failure is harder to see.**

Instruct an agent to reach 90% patch coverage and it will — by writing tests that
execute lines and assert nothing of consequence. It has no professional
discomfort about a hollow test, it optimises literally what it was asked for, and
it produces plausible-looking tests at volume, so the gaming survives a skim
review. A human gaming coverage writes five bad tests and feels bad about it; an
agent writes fifty and reports success.

Therefore:

> **The metric belongs in the harness, not in the prompt. The agent proposes, the
> pipeline filters, a human judges relevance.**

This is the shape Meta arrived at from a cost-and-scale direction and Google from
a code-review direction. We adopt it for a third reason: it is the only version
that survives an adversarial or merely over-eager agent.

## Decision

**1. Patch coverage is reported, never blocking.**
Coverage of the *changed lines* is measured and posted on the pull request for a
human to read. It does not fail a build. Rationale: the signal is the gap, and a
blocking number converts a diagnostic into an objective the agent will satisfy
dishonestly. Total-repository coverage is not gated either — it drifts with
unrelated changes, punishes small pull requests against large untested
codebases, and is trivially inflated.

Tooling: `coverage.py` as the engine (the JaCoco analogue), `pytest-cov` to drive
it, `diff-cover` for the changed-lines view.

**2. The blocking gate is fail-on-base.**

> A regression test added by a bug-fix pull request must **fail on the parent
> commit.**

If the test passes against the code *before* the fix, it does not test the fix.
This is the strongest available check because **the pre-fix commit is an oracle
the agent did not write** — independence obtained mechanically rather than by
trusting the author. It cannot be satisfied by a hollow test, which is exactly
what a coverage gate cannot say.

Sketch: identify the test files the pull request changed, check out the base
commit, restore only those files from the head, run only those tests, and require
at least one failure.

**3. Metrics never appear in the issue; assertions do.**
The agent-task template's *Acceptance criteria* field carries the observable
behaviour ("returns 404 with `{"detail": "Not found"}` for a missing id"), never
a target ("reach 90% coverage"). A specification can be satisfied honestly; a
target invites gaming.

**4. Test authorship: the issue states the assertion, the agent writes both the
test and the implementation, and the pipeline proves the independence.**
This obtains most of the independence of a human-written test without a human
writing code, because gate (2) supplies the missing oracle. Revisit for
`agent-autonomous` work specifically — where no human reads the diff at all, a
human-authored test may be the only defensible option (ADR-005).

**5. Self-verification is necessary but insufficient.**
Give the agent linters, tests and type checks so it catches its own errors before
a human sees them — that is most of the value. But an agent verifying its own
work has the same independence problem as an agent writing its own tests, so the
external gates in this ADR are not redundant with it.

**6. Grade by execution, not resemblance.**
Whether the diff looks like what a human would have written is not a gate. Does
the suite pass, does the new regression test fail on the parent, does anything
existing break. This is the principle SWE-bench uses.

## Agent-readiness certification

A repository's fitness for agentic development is a function of its test suite —
an agent can only self-verify as well as the tests allow. So autonomy should be
**earned by the repository**, not granted by policy. Tiers:

| Tier | Requirement | Status here |
|---|---|---|
| 0 | Tests exist and pass in CI | Met |
| 1 | Patch coverage measured and reported | Deferred — see below |
| 2 | Deterministic: no flakes across N repeated runs | Not started |
| 3 | Fail-on-base verified for bug fixes | Not started |
| 4 | Mutation score above a threshold | Direction, not committed |

A repository's tier caps how much autonomy it may be granted. This inverts the
usual arrangement, where autonomy is a policy decision and test quality is
someone's good intention.

## Mutation testing — the intended direction, not yet a commitment

Mutation testing measures what coverage cannot: whether the tests **detect
faults**, rather than merely execute lines. It has always been the technically
correct answer and has always been dismissed as too expensive — the suite must be
re-run per mutant, and most mutants are trivially killed, so the compute is
largely wasted.

Meta's finding is that LLM-generated mutants change that arithmetic: realistic
mutants mean far less compute wasted on easy kills.

The implication for GoldPath is specific and, as far as this project can tell,
not yet written down anywhere: **we already pay for an LLM.** The tier that a
pre-LLM pipeline could not afford may be affordable precisely because an agentic
pipeline has already absorbed that cost. If so, mutation score — not coverage —
is the right top rung of the certification above.

**This is recorded as a direction and not a decision, deliberately.** The cost
argument is borrowed from Meta's deployment, not measured on our own code. Before
committing, run `mutmut` against a real suite and record the wall-clock time.
Until then a presentation claim about affordability would be repeating someone
else's number as if it were ours.

## Consequences

**Nothing in this ADR is gameable by a hollow test.** The only blocking quality
gate is fail-on-base, which a test that asserts nothing cannot pass.

**A human still has to look at uncovered lines.** Reporting coverage without
gating it means the signal only has value if someone reads it. That is a real
cost, and it is Google's position too.

**Implementation is deferred and the reason is honesty.** The application has one
test against two endpoints. A coverage gate on it today would report ~100% and
measure nothing; a fail-on-base gate has almost nothing to run against. Building
the machinery now would produce a green badge that certifies nothing, which is
worse than an acknowledged gap. Implement when the application grows.

**Fail-on-base does not generalise to new features.** A test for code that does
not exist yet fails to import on the parent commit — a collection error, not an
assertion failure, and not evidence the test is any good. The gate is therefore
blocking for bug fixes and informational for features, which means the task type
has to be declared. That is a dependency on ADR-006 (trigger design).

## Residual risks

1. **Flake detection is unimplemented.** Tier 2 requires N repeated runs, which
   costs CI time that has not been budgeted. A flaky test that passes on the
   attempt that mattered still merges.
2. **Coverage reporting is only as useful as the person reading it.** Non-blocking
   means ignorable.
3. **The mutation cost claim is unverified** on our code, as stated above.
4. **Nothing here evaluates whether the change solves the user's actual problem.**
   Every gate in this ADR checks internal consistency against a stated
   specification. If the specification in the Linear issue is wrong, the pipeline
   will faithfully deliver the wrong thing, green all the way. That is a limit of
   automated verification, not a gap to be closed by another check.

## Evidence

- [Google Testing Blog — Code Coverage Best Practices](https://testing.googleblog.com/2020/08/code-coverage-best-practices.html) — the 60/75/90 guidance, the refusal to mandate, and "what's not covered is more meaningful"
- [Engineering at Meta — LLMs Are the Key to Mutation Testing](https://engineering.fb.com/2025/09/30/security/llms-are-the-key-to-mutation-testing-and-better-compliance/) — the deployment, the 73% acceptance rate, and coverage as a side effect
- [Mutation-Guided LLM-based Test Generation at Meta](https://arxiv.org/pdf/2501.12862) — the method
- [Automated Unit Test Improvement using LLMs at Meta (TestGen-LLM)](https://arxiv.org/abs/2402.09171) — assured generation
- [What It Would Take to Use Mutation Testing in Industry — A Study at Facebook](https://arxiv.org/pdf/2010.13464) — why mutation testing was historically unaffordable
