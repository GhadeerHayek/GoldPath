# Architecture Decision Records

One record per significant choice, written when the choice is made rather than
reconstructed afterwards. The reasoning is the artefact — an ADR that only states
what was decided, without the alternatives and the trade-off, has recorded
nothing useful.

## Relationship to Notion

The [Notion ADR database](https://app.notion.com/p/5b407165ae2f4b77a5a8fb675e3fe3b7)
is the canonical, reviewable home for these — that is where Colin and Rebecca
read them. The copies here exist because a decision about the pipeline should be
readable next to the pipeline, and because they get versioned with the code they
describe: when a workflow changes, the ADR that justified it shows up in the same
diff.

Notion is the source of truth for status. If the two disagree, Notion wins.

## Format

`Status` / `Context` / `Findings` / `Options` / `Decision` / `Consequences` /
`Evidence`.

Two conventions worth keeping:

- **Record options that were rejected, and why.** A decision with no discarded
  alternatives reads as the only thing anyone thought of, which is rarely true
  and impossible to review.
- **Link primary evidence.** Where a decision rests on what a vendor documents,
  link the vendor's own page rather than paraphrasing it. Documentation changes,
  and a claim without a source cannot be re-checked later.

Status values: `Proposed`, `Accepted`, `Superseded by ADR-NNN`, `Rejected`.
A `Proposed` ADR that is blocking should say who it is blocked on.

## Index

| ADR | Title | Status |
|---|---|---|
| 001 | Prove the pipeline on a demo repo vs. build on MindVault directly | Not yet written |
| 002 | Agent execution surface — CI vs. local vs. hybrid | Not yet written |
| [003](ADR-003-model-routing.md) | Model routing for the coding agent | **Proposed** — blocked on Colin |
| 004 | Review strategy — agentic review as advisory vs. blocking | Not yet written |
| 005 | Deployment and credential isolation | Not yet written |
| 006 | Trust gradient — what earns autonomous merge | Not yet written |
| 007 | Migrations and test fidelity | Not yet written |

ADR-003 is written first because it is the one with an external dependency:
it needs an answer from Colin, and the answer changes what Phase 3a is built on.
The others document decisions already taken, so they can be written from the
evidence in this repository at any point.
