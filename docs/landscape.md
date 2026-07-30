# Agentic tooling landscape — Phase 1 report

- **Date:** 2026-07-30 (revised)
- **Phase 1 exit deliverable.** Companion to the source-by-source notes in
  Notion (*Ghadeer's Research → Reading Notes*).

## What the reading actually yielded

An honest accounting first, because the yield was uneven — and the pattern in
*which* reading paid off is more useful than the reading itself.

**High yield — reading that changed a decision.**

- **Golden paths and platform engineering (Spotify).** Produced the single most
  useful idea in this report: that there are **two different golden paths** in
  "agentic development", and GoldPath is the second one. That reframe redefined
  the selection question below, and it came out of reading rather than building.
- **The lethal trifecta (Willison).** The most load-bearing reading in the
  project. It became ADR-002 more or less wholesale — the three-plane
  architecture is a direct application of *at each stage, which leg have we
  broken?*
- **MCP.** Inverted from the vendor framing. Read as convenience it is a velocity
  story; read for a security-conscious pipeline, every server is new injection
  and exfiltration surface. That inversion is now a constraint on which servers
  the agent gets.
- **Harnesses for long-running agents, and Meta's TestGen-LLM.** Together they
  established verification as the thesis and the test suite as the limiting
  factor. Both feed ADR-004.

**Yield that was not obvious at the time.**

- **Claude Code best practices, and the introductory Claude material.** Two days
  that felt like practical how-to rather than architecture — and that judgement
  was wrong. The *mechanisms* are architectural even though the guides are not:
  `CLAUDE.md` is what makes a stateless runner viable, hooks are the only Claude
  Code feature that is a control rather than a request, skills are the correct
  home for agent instructions that must stay out of the diff, and subagents are
  one of the two routes to multi-agent work in CI. **ADR-001 exists entirely
  because of this reading.** The lesson is that a practical guide can carry an
  architectural decision, and it will not announce itself as one.

**Low yield.**

- **SWE-bench.** Evaluation methodology for grading models — out of scope for a
  pipeline. One principle survived into ADR-004: grade by execution, not by
  whether the diff resembles a reference.
- **Google, AI in Software Engineering.** Era-specific. Its metrics belong to the
  code-completion period (character counts, acceptance rates) and do not transfer
  to an agent solving a whole issue. Its one transferable point — that context
  construction is the lever rather than model size — had already been reached
  from the Claude Code side.

**Unread: METR.** The counter-evidence on whether AI assistance actually speeds
experienced developers up. Deliberately dropped from Phase 1 rather than carried
as a pending task: it has presentational value and no implementation value, so it
belongs to the Phase 4 argument or to nobody.

**The process lesson, which is the most transferable part.** Front-loading a
reading list produced notes that fed nothing, and the yield above is concentrated
in the sources that happened to meet a concrete problem. Reading *while* building
— asking questions against something real — was consistently higher-yield per
hour than surveying the field first. The practical skills picked up by building
(FastAPI, why Ruff rather than flake8, writing tests under pytest) turned out to
be worth more than several of the industry sources, and they are recorded in
*The stack we chose* below rather than left as tacit knowledge.

## What question this report answers

The reframe above does the work here. There are two golden paths hiding in
"a golden path for agentic development":

1. **A golden path for building agents** — for teams assembling an agent from
   parts. Their questions are orchestration frameworks, memory implementations,
   which tools to expose, how to break hallucination loops from inside the loop.
2. **A golden path for agents building software** — for teams who already have a
   finished agent and need to put it to work safely on a real codebase.

**GoldPath is the second.** We were handed an agent and asked to build the
factory it works in. So the selection question is not about code quality:

> **Which agent can be driven non-interactively, inside a CI job, with scoped
> credentials and no persistent state — and reviewed afterwards from its diff
> alone?**

Almost no published comparison answers that, because almost nobody is asking it
yet. Building with agents is currently in its own *rumour-driven development*
era — no blessed stack, no scaffolding, teams copying each other's setups and
hoping — which is precisely the fragmentation problem golden paths were invented
for.

## Selection criteria

Derived from the trust-boundary architecture in ADR-002, not from feature lists:

| Criterion | Why it decides things |
|---|---|
| **Headless invocation** | If it cannot run unattended in a CI job, it cannot be the golden path. Everything else is moot. |
| **Credential scoping** | The agent holds a model key and a narrow repo token, and nothing else. A tool assuming broad ambient credentials cannot sit in the execution plane. |
| **Statelessness** | No memory between runs means everything the agent needs lives in the repo. Costly, but it makes agent behaviour a reviewable artefact rather than invisible session state. |
| **Where the code executes** | For a privacy company this is a first-order question, not an implementation detail. |
| **Provider flexibility** | Determines whether the model is a swappable input or a lock-in. See ADR-003. |
| **Verification affordances** | An agent is only as good as its ability to check its own work. The pipeline is a verification loop wrapped around the agent's own. |

## The tools

### Claude Code — selected

Terminal-native, supports headless invocation, has a first-party GitHub Action,
speaks MCP. Runs inside a CI job with a scoped token, satisfying the first three
criteria at once.

The property that matters most is that **the harness is the product and the model
is an input** — Claude Code treats the model endpoint as configurable, which is
what makes ADR-003's provider seam possible at all.

Its four context mechanisms — `CLAUDE.md`, hooks, skills, subagents — are not
surveyed here, because they turned out to be decisions rather than features.
**See ADR-001.**

### OpenAI Codex — not selected, for a structural reason

Runs in two modes: a local CLI, and a **cloud agent in a vendor-managed sandbox**
where long tasks execute autonomously. That cloud mode is the most advanced
autonomy on offer, and it is also why it is wrong here: the code leaves our
infrastructure and executes somewhere we do not control or audit.

For a privacy and security company that is a boundary question rather than a
performance one. It also inverts our trust model — the value of the three-plane
design is that *we* decide what the execution plane can reach; a managed sandbox
makes that the vendor's decision.

### OpenCode — the lock-in hedge

MIT-licensed, provider-agnostic, bring-your-own-key, not owned by any of the
vendors consolidating this space. Strongest on avoiding lock-in and controlling
data exposure; weakest on first-party CI integration, which is what we depend on.

**Its value is as a documented fallback rather than a current choice.** If ADR-003
resolves badly, OpenCode is the architecture that survives it, because
provider-agnosticism is its premise rather than a configuration option.

### Conductor — solves a different problem

The most useful negative finding here, because the brief lists Conductor as the
stretch goal for multi-agent orchestration.

Conductor is a **macOS desktop application** running several agents in parallel,
each in its own git worktree, with a dashboard and a diff-first review pane. It is
well designed for one human supervising many agents interactively, where the
bottleneck is that you cannot watch six agents at once.

**That is not our problem.** GoldPath's bottleneck is an unattended agent with
nobody watching at all. A desktop app cannot be the CI orchestration mechanism —
not as a limitation to work around, but because it is built for the opposite
situation. If multi-agent work in CI is wanted later, the routes are Actions
matrix jobs or Claude Code subagents (ADR-001).

### MCP — read as attack surface, not convenience

> **Every MCP server attached to an agent is new tool surface — a new injection
> vector and a new exfiltration channel.**

Three specifics the convenience framing omits: **tool-description poisoning**
(server-supplied descriptions enter the model's context *as instructions*, so a
compromised server shapes behaviour without ever being called), the materially
different trust models of local versus remote servers, and context budget cost.

**Current answer: Linear only**, scoped to reading issues and writing comments and
status — never workspace administration.

## The stack we chose, and why

Not agent tooling, but decisions embedded in the repository that would otherwise
sit there unexplained. These were learned by building rather than reading, and
they are the most directly transferable part of Phase 1 — MindVault gets these
along with the pipeline.

### Ruff, replacing flake8 (and black, and isort)

The repository's original CI installed `flake8` and never invoked it, while Ruff
arrived incidentally through `requirements.txt`. Consolidating on Ruff was the
obvious call: one binary covers linting *and* formatting, replacing what would
otherwise be flake8 plus black plus isort plus pyupgrade, at roughly two orders of
magnitude more speed, with a single configuration block in `pyproject.toml`.

One non-obvious decision is worth recording. Ruff **omits line-length (`E501`) by
default when a formatter is in use**, reasoning that the formatter handles line
length. We re-enable it with `extend-select = ["E501"]` because the formatter will
not break a long string literal or a URL — so `E501` still catches exactly the
cases the formatter cannot fix.

Lint and format run as separate CI steps, because `ruff check` and `ruff format
--check` fail for different reasons and should be distinguishable in the log.

### uv, replacing pip and pip-tools

The most consequential tooling decision, because it is what makes CI reproducible
at all.

The repository previously had **two dependency systems that could not see each
other**: `pyproject.toml` declared only a Ruff dev group, so `uv.lock` pinned
exactly one of the fifty packages CI actually installed — the rest came from a
`requirements.txt` that CI installed instead. Nothing that ran was pinned by the
lockfile the repository carried.

Consolidating on `pyproject.toml` plus `uv.lock` gives one tool for resolve, lock,
install and run. Three properties earn its place:

- **`uv sync --locked` fails if the lockfile is stale** relative to
  `pyproject.toml`. `--frozen` installs an out-of-date lockfile silently. This is
  the check that keeps the lockfile honest, and the distinction between those two
  flags is the whole reason for using it.
- **The lockfile carries hashes**, so `pip-audit --require-hashes` verifies
  package integrity as well as checking CVEs.
- **The Docker build resolves from the same lockfile**, so the deployed image
  cannot drift from what the tests ran against.

### pytest

The existing test is written unittest-style (`class DemoTest(unittest.TestCase)`)
and runs under pytest, which executes both styles — so no migration was needed and
none was done.

Going forward the preference is plain test functions with fixtures rather than
`setUp` inheritance, because fixtures compose and base classes do not. pytest is
also what `pytest-cov` and `diff-cover` plug into, which makes it a prerequisite
for the verification work in ADR-004 rather than a matter of taste.

### FastAPI — given, not chosen

Comes from the brief: it is MindVault's stack, and the demo application mirrors it
so the pipeline transfers. Recorded here so it is clear this was not a decision we
made.

### Docker — multi-stage, non-root

A build stage resolves dependencies from the lockfile; the runtime stage carries
only the virtualenv and the application, leaving uv, pip caches and build tooling
out of the shipped image. It runs as uid 10001 rather than root, on port 8000
rather than 80 — binding a privileged port would have meant running as root for no
benefit, since Traefik terminates TLS anyway.

## What this implies for GoldPath

1. **Claude Code plus GitHub Actions is the blessed stack**, with Semgrep,
   gitleaks, pip-audit and Docker around it. Not SDKs and vector databases — that
   would be the first golden path, not ours.
2. **Guardrails and telemetry belong in the scaffold**, not bolted on per project.
3. **Verification is the thesis.** Self-verification is necessary but insufficient
   — an agent checking its own work has the same independence problem as an agent
   writing its own tests. Hence the external gates in ADR-004.
4. **Grade by execution, not resemblance.**
5. **Framing for the final presentation:** this is a **platform engineering**
   artefact, not a DevOps initiative. DevOps is the culture; platform engineering
   is the practice that makes it scale.

Two ideas worth building that are not in the brief:

- **Agent-readiness certification** — a repo's fitness for agentic development as
  a function of its test suite, making autonomy *earned* rather than granted. Now
  recorded in ADR-004.
- **Golden State via evals** — success rate and token cost per pipeline run over
  time, so drift is visible.

## Honest gaps

**Source quality is uneven.** The golden-path, security and MCP sections rest on
primary sources. The **tool comparison does not** — it rests on secondary
comparison articles, some carrying stale model-version claims. Treat the Codex,
OpenCode and Conductor assessments as *directional*.

**No hands-on evaluation was done.** Claude Code is the only tool actually
exercised. A fair comparison would run the same seeded issue through each — which
is what ADR-003's 3-of-3 criterion measures, and could be reused as a bake-off.

**METR is unread and dropped**, as above — deliberately, not by omission. If the
final presentation makes a claim about developer productivity, this is the gap
that would need closing first.
