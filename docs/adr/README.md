# Architecture Decision Records

One record per significant choice, written when the choice is made rather than
reconstructed afterwards. The reasoning is the artefact — an ADR that only states
what was decided, without the alternatives and the trade-off, has recorded
nothing useful.

## Relationship to Notion

The [Notion ADR database](https://app.notion.com/p/5b407165ae2f4b77a5a8fb675e3fe3b7)
is where Colin and Rebecca read these. The copies here exist because a decision
about the pipeline should be readable next to the pipeline, and because they get
versioned with the code they describe: when a workflow changes, the ADR that
justified it shows up in the same diff.

**Numbering is owned by this directory, and mirrored into Notion.** Notion's `ID`
column is an auto-increment and cannot be set, so it will not necessarily match —
the canonical number lives in the page **Title** (`ADR-002 — …`). Creating the
Notion rows in numeric order keeps the two aligned as a matter of convenience,
not correctness. If the Title and the auto ID disagree, the Title wins.

## Format

`Status` / `Context` / `Decision` / `Consequences` / `Residual risks` / `Evidence`,
with `Findings` and `Options` where a decision rested on investigation.

Three conventions worth keeping:

- **Record options that were rejected, and why.** A decision with no discarded
  alternatives reads as the only thing anyone thought of, which is rarely true
  and impossible to review.
- **Link primary evidence.** Where a decision rests on what a vendor documents,
  link the vendor's own page rather than paraphrasing. Documentation changes, and
  a claim without a source cannot be re-checked later.
- **Name residual risks.** An ADR that lists no remaining exposure is either
  trivial or dishonest. Naming a gap is stronger than hiding it.

Status values: `Proposed`, `Accepted`, `Superseded by ADR-NNN`, `Rejected`.
A `Proposed` ADR that is blocking should say who it is blocked on.

## Index

| ADR | Title | Area | Status |
|---|---|---|---|
| 001 | Agent runtime — stateless YAML-defined runner | tooling | Not yet written |
| [002](ADR-002-trust-boundaries.md) | Trust boundaries and the credential model | guardrails & security | **Accepted** — implemented and verified |
| [003](ADR-003-model-routing.md) | Model routing for the coding agent | model routing | **Proposed** — blocked on Colin |
| 004 | Verification gates — what must pass, and why self-verification is insufficient | code review | Not yet written |
| 005 | Merge policy and the trust gradient — what earns autonomous merge | process | Not yet written |
| 006 | Trigger design — how an issue becomes an agent run | process | Not yet written |
| 007 | Deployment and migration safety | deployment | Not yet written |

Two notes on the order things were written in.

**ADR-003 came first** because it carries an external dependency: it needs an
answer from Colin, and that answer changes what Phase 3a is built on. Blocking
questions get written before settled ones.

**ADR-002 is `Accepted` rather than `Proposed`** because every control it
describes is already implemented in `.github/workflows/policy.yml` and
`guardrails.yml` and was verified by making it fail, rather than by reading it.
The remaining ADRs document decisions that are largely already taken, so they can
be written from the evidence in this repository at any point.
