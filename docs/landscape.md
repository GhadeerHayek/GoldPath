# Agentic tooling landscape — Phase 1 report

- **Date:** 2026-07-30
- **Phase 1 exit deliverable.** Companion to the source-by-source notes in
  Notion (*Ghadeer's Research → Reading Notes*), which this synthesises.

## What question this answers

Most published comparisons of coding agents answer *"which one writes the best
code?"* That is not GoldPath's question, and answering it would not help.

The reframe that matters comes out of the golden-path reading. There are **two
different golden paths** hiding in "a golden path for agentic development":

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

Derived from the architecture in ADR-002, not from feature lists:

| Criterion | Why it decides things |
|---|---|
| **Headless invocation** | If it cannot run unattended in a CI job, it cannot be the golden path. Everything else is moot. |
| **Credential scoping** | The agent must hold a model key and a narrow repo token, and nothing else. A tool that assumes broad ambient credentials cannot sit in the execution plane. |
| **Statelessness** | No memory between runs means everything the agent needs lives in the repo — `CLAUDE.md`, tests, conventions. Costly, but it makes agent behaviour a **reviewable artefact in a PR** rather than invisible session state. |
| **Where the code executes** | For a privacy company this is a first-order question, not an implementation detail. |
| **Provider flexibility** | Determines whether the model is a swappable input or a lock-in. See ADR-003. |
| **Verification affordances** | An agent is only as good as its ability to check its own work — linters, tests, screenshots. The pipeline is a verification loop wrapped around the agent's own. |

## The tools

### Claude Code — selected

Terminal-native, supports headless invocation, has a first-party GitHub Action,
speaks MCP. Runs inside a CI job with a scoped token, which satisfies the first
three criteria at once.

The property that matters most is that **the harness is the product and the model
is an input.** Claude Code's own documentation treats the model endpoint as
configurable, which is what makes ADR-003's provider seam possible at all — and
which is the practical form of the harness-versus-model distinction Colin named
as a core learning objective.

### OpenAI Codex — not selected, for a structural reason

Runs in two modes: a local CLI, and a **cloud agent in an OpenAI-managed
sandbox** where long tasks execute autonomously. That cloud mode is genuinely
the most advanced autonomy on offer, and it is also why it is wrong here: the
code leaves our infrastructure and executes somewhere we do not control or audit.

For a privacy and security company, that is a boundary question rather than a
performance one. It also inverts our trust model — the value of the three-plane
design is that we decide what the execution plane can reach. A managed sandbox
makes that the vendor's decision.

Worth revisiting only if the sandbox's isolation and data handling can be
audited against LibertiTec's requirements. Not a Phase 1 blocker.

### OpenCode — the lock-in hedge

MIT-licensed, provider-agnostic, bring-your-own-key, not owned by any of the
vendors consolidating this space. Strongest on avoiding lock-in and controlling
data exposure; weakest on first-party CI integration, which is precisely what we
depend on.

**Its value to us is as a documented fallback rather than a current choice.** If
ADR-003 resolves badly — if the provider question turns into a vendor
constraint we cannot live with — OpenCode is the architecture that survives it,
because provider-agnosticism is its premise rather than a configuration option.
Naming it now costs nothing and makes the eventual argument cheaper.

### Conductor — solves a different problem

This is the report's most useful negative finding, because the brief lists
Conductor as the stretch goal for multi-agent orchestration.

Conductor is a **macOS desktop application** that runs several agents in parallel,
each in its own git worktree, with a dashboard and a diff-first review pane. It
is well-designed for what it does: one human supervising many agents
interactively, where the bottleneck is that you cannot watch six agents at once.

**That is not our problem.** GoldPath's bottleneck is an unattended agent inside
a pipeline with nobody watching at all. A macOS desktop app cannot be the CI
orchestration mechanism — not as a limitation to work around, but because it is
built for the opposite situation.

So if multi-agent orchestration in CI is wanted later, Conductor is not the
route. The routes are GitHub Actions matrix jobs, or Claude Code's own subagents
running inside a single job. Worth recording so the stretch goal is not attempted
by installing the wrong tool.

### MCP — read as attack surface, not as convenience

The vendor framing for MCP is developer velocity: one standard, no bespoke
integration per client. For a security-conscious pipeline the operative fact is
the inverse:

> **Every MCP server attached to an agent is new tool surface — a new injection
> vector and a new exfiltration channel.**

Three specifics that the convenience framing omits:

- **Tool-description poisoning.** Server-supplied tool descriptions enter the
  model's context *as instructions*. A compromised server can influence agent
  behaviour without ever being called.
- **Local (stdio) versus remote (HTTP) servers** have materially different trust
  and authentication models.
- **Tool definitions consume context budget**, so more servers is not free even
  setting security aside.

The practical question is therefore *which servers does the agent get inside CI,
and with what token scopes?* **Current answer: Linear only, scoped to reading
issues and writing comments and status — never workspace administration.** Every
additional server widens the execution plane and needs a note against ADR-002.

## What this implies for GoldPath

1. **Claude Code plus GitHub Actions is the blessed stack**, with Semgrep,
   gitleaks, pip-audit and Docker around it. Not SDKs and vector databases —
   that would be the first golden path, not ours.
2. **Guardrails and telemetry belong in the scaffold**, not bolted on per
   project. Already true of `policy.yml` and `guardrails.yml`.
3. **Verification is the thesis.** When code generation is cheap, verification
   becomes the bottleneck. Self-verification is necessary but insufficient — an
   agent checking its own work has the same independence problem as an agent
   writing its own tests. Hence external gates (ADR-004).
4. **Grade by execution, not resemblance.** The honest measure of an agent
   solving an issue is functional: does the suite pass, does the new regression
   test actually fail on the pre-fix commit, does nothing existing break. This is
   the same principle SWE-bench uses, and the ancestor of ADR-004's gate design.
5. **Two ideas worth building that are not in the brief:**
   - **Agent-readiness certification.** A repo's fitness for agentic development
     is a function of its test suite — an agent can only self-verify as well as
     the tests allow. A tiered certification (fast suite? coverage reporting?
     deterministic tests?) makes autonomy *earned* rather than granted, and would
     be an original contribution to the reference architecture.
   - **Golden State via evals.** Track success rate and token cost per pipeline
     run over time, so drift is visible. Spotify's Golden State idea applied to
     agent output.
6. **Framing for the final presentation:** this is a **platform engineering**
   artefact, not a DevOps initiative. DevOps is the culture; platform engineering
   is the practice that makes it scale without burning developers out. That
   vocabulary will land better with Colin and Rebecca.

## Honest gaps

**Source quality is uneven.** The golden-path, security and MCP sections rest on
primary sources — Spotify Engineering, Willison, the MCP specification, Anthropic
and Google engineering posts. The **tool comparison in this report does not**: it
rests on secondary comparison articles, some of which carry stale model-version
claims. Treat the Codex, OpenCode and Conductor assessments as *directional*.

**No hands-on evaluation was done.** Claude Code is the only tool here actually
exercised. A fair comparison would run the same seeded issue through each — which
is exactly what ADR-003's 3-of-3 criterion is designed to measure, and could be
reused as a tool bake-off later.

**Five primary sources remain unread**, in priority order:

1. **Claude Code best practices** — `CLAUDE.md`, permission modes, hooks,
   headless invocation, subagents. The most directly applicable unread item;
   headless mode is what makes the CI-runner design possible at all.
2. **Anthropic — effective harnesses for long-running agents** — the harness
   versus model distinction named as a core learning objective.
3. **Meta — TestGen-LLM** ([arXiv 2402.09171](https://arxiv.org/abs/2402.09171)) —
   assured generation: accept generated tests only if they compile, pass, and
   measurably increase coverage. Read before building ADR-004's most important gate.
4. **METR** — the 2025 study and 2026 follow-up. The honest counter-evidence;
   citing it makes the final presentation credible rather than credulous.
5. **SWE-bench explained** — how the field grades coding agents, and why
   execution-based evaluation is the right frame.

Items 1 and 3 are on the critical path for Phase 3a. Items 4 and 5 are for the
presentation.

## Sources

Primary sources are catalogued per-item in Notion (*Reading Notes*). The
tool-comparison material specific to this report:

- [Claude Code vs Codex vs OpenCode (2026)](https://medium.com/@unicodeveloper/claude-code-vs-codex-vs-opencode-which-ai-coding-agent-is-actually-the-best-in-2026-baa9f6fd5374) — secondary
- [Top CLI coding agents 2026](https://pinggy.io/blog/top_cli_based_ai_coding_agents/) — secondary
- [Conductor by Melty Labs in practice](https://madewithlove.com/blog/conductor-running-multiple-ai-coding-agents-in-parallel/) — secondary
- [Open-source agent orchestrators](https://www.augmentcode.com/tools/open-source-agent-orchestrators) — secondary
- [MCP introduction](https://modelcontextprotocol.io/docs/getting-started/intro) — primary
