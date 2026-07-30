# ADR-002 — Trust boundaries and the credential model

- **Status:** Accepted — implemented and verified in this repository
- **Date:** 2026-07-30
- **Area:** guardrails & security
- **Related:** ADR-001 (agent runtime), ADR-003 (model routing), ADR-004 (verification gates)

## Context

An autonomous coding agent wired into a real delivery pipeline assembles
Willison's **lethal trifecta** by construction: access to private data, exposure
to untrusted content, and a channel to communicate outward. Because an LLM
cannot reliably distinguish instructions from data, any design that leaves all
three legs intact is exploitable, and no amount of prompt hardening fixes it.

Mapped onto GoldPath, the naive pipeline has all three:

| Leg | Where it appears |
|---|---|
| Private data | Repository contents, model API key, GitHub token, VPS SSH key, registry credentials |
| Untrusted content | Linear issue titles and bodies, PR comments, review replies, dependency metadata, anything fetched from the web |
| External communication | `git push`, opening PRs, writing to Linear, and — on a default runner — arbitrary outbound HTTP |

So the design question is never *"are we vulnerable"*. It is **"at each stage,
which leg have we broken?"**

This ADR also fixes the standard for what counts as a guardrail here:

> **A rule in a prompt is a request. A rule in a token scope is a control.**

Only the second kind is recorded as a security property. Everything in the
"implemented" section below is a control.

## Decision

Split the pipeline into three planes, each of which deliberately gives up one
leg of the trifecta.

```
CONTROL PLANE — intent
  Linear issue + `agent-ready` label applied by a write-access human
  Handles untrusted text. Executes nothing. Holds no credentials of consequence.
        │
        │  authorisation crosses here: a label, not a body
        ▼
EXECUTION PLANE — proposal only
  The coding agent. Reads the repo and the issue, writes code, opens a PR.
  Holds: model API key, a scoped GITHUB_TOKEN (contents+PR write).
  Holds NOT: VPS credentials, registry credentials, environment secrets.
  ── breaks the PRIVATE DATA leg ──
        │
        │  deterministic gates cross here; none of them trust the agent
        ▼
POLICY — machines verify, policy merges
  lint · test · image · secrets · sast · deps · privileged-changes · human-approval
        │
        ▼
DELIVERY PLANE — action
  Builds the image, pushes to the registry, deploys to the VPS, writes status back.
  Input is an immutable merged commit SHA. Never reads an issue body or a comment.
  ── breaks the UNTRUSTED CONTENT leg ──
```

**The invariant: agents propose, machines verify, policy merges, only the
delivery plane acts.**

Two independent lines of reasoning arrive at this same boundary, which is the
main reason to have confidence in it:

- **From security:** the trifecta analysis above. Break a different leg in each
  plane and a fully-compromised agent still cannot reach production.
- **From operations:** this is GitOps. Humans and agents change the *declared
  state in Git*; a separate automated process reconciles reality to it.
  Declarative desired state, immutable version-controlled changes, automated
  synchronisation. Spotify arrives at the same split from a configuration-drift
  direction rather than a security one.

## What is implemented and verified

Not aspirational. Each row was tested by making it fail.

| Control | Mechanism | Verified by |
|---|---|---|
| Authorisation is a label, not text | Agent triggers on `agent-ready` applied by a write-access human, checked against the API — never on `issues: [opened]` or comment bodies | Permission derivation tested against a stranger account |
| Privilege surface is closed to bots | `privileged-changes` blocks bot-authored PRs touching workflows, actions, CODEOWNERS, scanner config, or the image | Run against a real PR diff with the author forced to `agent[bot]` — blocked |
| Agents cannot reach for credentials | Same job fails any bot PR whose *added* lines reference a secret or known credential env var | Diff reading `os.environ["VPS_SSH_KEY"]` and POSTing it — blocked; ordinary endpoint — allowed |
| Nothing merges unreviewed by a machine | Ruleset on `main`: 8 required checks, `bypass_actors: []` | Direct push as **admin** rejected: *"Changes must be made through a pull request"* |
| Bot work needs a human | `human-approval` requires an approving review from a write-access human when the author is a bot; auto-passes for humans, since GitHub forbids self-approval and a flat rule would deadlock a single-maintainer repo | Human path passes in CI; bot path forced and blocked |
| Scanners actually block | `guardrails.yml` asserts gitleaks, Semgrep, and pip-audit each exit non-zero on synthesized bad input | All three fail correctly; input generated at runtime so nothing bad is ever committed |
| No injection via workflow context | All event data passed through `env:`, never interpolated into a `run:` body; `pull_request_target` used nowhere | Reviewed; documented inline in `policy.yml` |
| Least privilege by default | Workflows default to `permissions: contents: read`; jobs opt in explicitly | — |

Two subtleties worth recording because they look fine and are not:

**On a public repository, `collaborators/{user}/permission` returns `read` for
every GitHub user.** It does not 404 for a stranger. An authorisation check
written as `!= "none"`, or as "did the API call succeed", is bypassable by any
account on GitHub. Both checks allowlist `admin`/`maintain`/`write` explicitly,
and exclude `triage`, which can label but not push.

**A required status check whose workflow is absent from the default branch
blocks every pull request permanently.** Land the workflow, then require it.

## Repository visibility, and what changes when it moves

GoldPath is **public** today, for a mundane reason: branch protection and
rulesets are not available on a free personal *private* repository, and rulesets
are load-bearing here. That is expected to change — either when GitHub Pro
arrives via the Student Developer Pack, or when this work moves into the
`Thinking-of-U` organisation. So visibility is a temporary condition, and the
design should not depend on it.

### What being public actually costs, in plain terms

- **Everything is readable by anyone, forever — including git history.** A secret
  that is ever committed is compromised the moment it lands. Deleting it in a
  later commit does not undo that: anyone could already have cloned or cached the
  repository, and the old object stays reachable. **Rotation is the only remedy**,
  which is why push protection and the `secrets` job exist rather than a
  "remember not to commit keys" convention.
- **Workflow logs are public.** Anything CI prints, the world can read. This is
  the reason gitleaks runs with `--redact`: an unredacted finding would broadcast
  the credential to everyone while reporting that it leaked.
- **Strangers can fork and open pull requests**, which runs CI. They cannot do
  harm — pull requests from forks get a read-only token, and `privileged-changes`
  blocks any non-trusted author from the privilege surface — but they can consume
  Actions minutes. Nuisance, not exposure.
- **Weaknesses are visible before they are fixed.** Anyone can read the pipeline
  and look for a gap. This cuts both ways: it is also why the design has to be
  sound rather than merely obscure.
- **The permission endpoint returns `read` for every GitHub user**, as noted
  above, so authorisation cannot be inferred from a successful lookup.

### What changes on a private repository (GitHub Pro)

| | Effect |
|---|---|
| Rulesets and branch protection | **Available** — this is the reason to move |
| Fork pull requests from strangers | **Gone** |
| Workflow logs | **No longer public** |
| Permission endpoint | Stops returning `read` for strangers, so the authorisation check becomes *stricter on its own* |
| Secret scanning and push protection | **Lost** — see below |

That last row is the one that surprises people. **Secret scanning and push
protection are free for public repositories and paid everywhere else** — private
and internal repositories need a GitHub Secret Protection licence. So making the
repository private *removes* a security control rather than adding one.

The mitigation already exists and is not an accident: **the `secrets` job runs
gitleaks in CI over full history regardless of visibility or licensing.** GitHub's
native scanning is a second layer, not the layer. Losing it degrades
defence-in-depth without opening a hole.

### What changes on moving into the organisation

- **Rulesets and secrets need Colin.** Write access is not enough to configure
  either, so the migration is not self-service.
- **Secret Protection availability depends on the organisation's plan** rather
  than on us.
- **`gitleaks-action` would demand a licence key** for an org-owned repository.
  Already the reason this pipeline uses the MIT binary with a verified checksum
  instead — a choice made for portability that now also survives the visibility
  change.

### The design consequence

Every control that carries weight here is **visibility-independent**: gitleaks
runs in CI either way, the permission check allowlists privileged levels rather
than testing whether a lookup succeeded, and the ruleset is ours regardless of
who owns the repository. That is deliberate, and it is what makes the eventual
move to Pro or to the organisation a settings change rather than a redesign.

## Trust tiers

Authorship is the boundary, and it has three levels rather than two:

| Tier | Privilege surface | Credential refs | Merge |
|---|---|---|---|
| Write-access human | Permitted | Permitted | No approval required (self-approval impossible) |
| Dependabot | Version pins only — blocked from CODEOWNERS, scanner config, its own schedule | Blocked | Human approval required |
| Coding agent / any other bot | Blocked entirely | Blocked | Human approval required; `agent-autonomous` may waive it for low-risk labelled work (ADR-005) |

Dependabot is a distinct tier because its *input* is a package registry, not an
issue body a stranger can write. Blocking it outright disconnected the
CVE early-warning system from the base image and the action pins — the two
ecosystems most likely to carry one. The exemption is narrowed, not a pass.

## Consequences

**The agent's blast radius is a pull request.** A fully prompt-injected agent
can write bad code and open a PR. It cannot merge it, cannot reach the VPS,
cannot read a deployment secret, and cannot edit the checks that stop it.

**The delivery plane never parses attacker-influenced text.** Its only input is
a merged commit SHA that already passed every gate. This is why an injected
issue body cannot become a deploy-time exploit.

**Cost: the agent cannot fix its own tooling.** If a workflow needs changing, a
human authors it. Accepted deliberately — an agent that can edit the workflows
can edit the workflows that gate it.

**Cost: strict status checks serialise merges.** Each merge makes open PRs stale
and they must update before merging. This prevents the two-PRs-pass-separately-
break-together failure, at the price of throughput.

## Residual risks

Naming these is stronger than hiding them.

1. **Network egress is not controlled.** The largest remaining gap. The agent
   job has unrestricted outbound HTTP, so a fully-injected agent can exfiltrate
   repository contents and its own model key even though it cannot reach
   production. The trifecta's third leg is intact in the execution plane. A
   runner-hardening step or an allowlist proxy is the fix; it is not in v1.
2. **Docker group membership on the VPS is effectively root** on that host. Deferred
   to the deployment phase, to be resolved in the deployment ADR — either accept
   it with justification, or replace it with a single-command `sudoers` rule.
3. **The agentic reviewer is persuadable.** It reads the same attacker-influenced
   text the agent did. It is defence in depth and is never a required check.
4. **Secret-scanning validity checks are unavailable** — they need paid GitHub
   Secret Protection. So we learn that a credential leaked, but not whether it
   is still live. Raised with Colin. Note the visibility interaction above: the
   base scanning we *do* have is free only because the repository is public, and
   going private without a licence removes it.
5. **A compromised agent can create branch and PR noise** with its scoped token.
   Annoying, not dangerous; nothing merges without passing policy.

## Evidence

- [The Lethal Trifecta for AI Agents](https://simonwillison.net/2025/Jun/16/the-lethal-trifecta/) — the three-leg framing, and why prompt-level guardrails are not a control
- [Design Patterns for Securing LLM Agents against Prompt Injections](https://simonwillison.net/2025/Jun/13/prompt-injection-design-patterns/) — security as a deliberate capability sacrifice
- [How Spotify Manages Infrastructure with GitOps](https://thenewstack.io/platformcon-how-spotify-manages-infrastructure-with-gitops/) — the independent operations-side argument for the same boundary
- This repository: `.github/workflows/policy.yml`, `guardrails.yml`, and ruleset `19966324`
