# ADR-003 — Model routing for the coding agent

- **Status:** Proposed — needs a decision from Colin
- **Date:** 2026-07-30
- **Supersedes:** nothing
- **Related:** ADR-002 (agent execution surface)

## Context

The project brief specifies the build-phase toolchain directly:

> For the build phase you'll run it against **KimiCoding-2.7** (and/or **GLM-5.2**) via OpenRouter (Anthropic-compatible endpoint) to keep experimentation cheap; once the pipeline works, we'll switch you to a live Claude subscription for hardening and the demo.

We decided in ADR-002 to run the agent **fully inside GitHub Actions**, via
`anthropics/claude-code-action`. That makes the model-routing question load-bearing:
the agent's provider configuration is baked into a workflow that other things
depend on, so getting it wrong is a rewrite rather than an edit.

Before building on the brief's assumption, I checked whether the mechanism
actually exists and is supported. Half of it does. The other half is documented
as unsupported by both vendors.

## Findings

### 1. The mechanism is real and documented

OpenRouter exposes what it calls the **Anthropic Skin** — a genuine Anthropic
Messages API endpoint, not merely the OpenAI-shaped `/chat/completions` one.
Claude Code talks to it natively, with no translation proxy. OpenRouter states
that "thinking blocks, native tool use, streaming, and multi-turn context all
work as they do against Anthropic directly."

The configuration is specific, and one line of it is a trap:

```bash
export ANTHROPIC_BASE_URL="https://openrouter.ai/api"   # not /api/v1 — the client appends /v1/messages
export ANTHROPIC_AUTH_TOKEN="$OPENROUTER_API_KEY"
export ANTHROPIC_API_KEY=""                              # empty string, NOT unset
```

`ANTHROPIC_API_KEY` unset and `ANTHROPIC_API_KEY=""` behave differently: unset
lets a previously saved credential win, empty yields to `ANTHROPIC_AUTH_TOKEN`.

Note also that `claude-code-action` has **no documented input** for a custom
base URL — its authentication inputs are `anthropic_api_key`,
`claude_code_oauth_token`, `use_bedrock`, `use_vertex`, and the workload-identity
set. The available hook is the action's `settings` input, which passes an `env`
object through to the Claude Code process. That works, but it is not a
first-class configuration path.

### 2. The model choice in the brief is documented as unsupported

Both vendors say the same thing from their own side:

- **OpenRouter:** "Claude Code is built around Anthropic request semantics, and
  the integration is only guaranteed to work with the Anthropic first-party
  provider."
- **Anthropic:** Anthropic "doesn't support routing Claude Code to non-Claude
  models through any gateway."

KimiCoding-2.7 and GLM-5.2 are not Anthropic models. The exact combination the
brief prescribes — Claude Code, via OpenRouter, against non-Anthropic models —
is the combination both parties decline to support.

### 3. Why this is worse than a normal unsupported-config risk

The failure mode is quiet. Claude Code depends on tool use and thinking blocks
for essentially everything it does; a model that handles those imperfectly does
not error, it just gets worse at the job. Symptoms would be an agent that
sometimes fails to call a tool, or loses context mid-task.

Those symptoms are indistinguishable from "the agent workflow is badly designed"
or "the prompt is weak." The likely cost is not an outage — it is **days spent
debugging our own pipeline for a fault that lives in the routing layer.** That
is a bad failure to accept silently during the make-or-break phase.

## Options

| Option | Supported | Cost | Note |
|---|---|---|---|
| A. OpenRouter + Anthropic models | Yes | Roughly list price plus OpenRouter's margin | **No cost saving.** Not a middle ground — it is Anthropic with an extra hop and an extra vendor in the trust chain |
| B. OpenRouter + Kimi/GLM | **No** | Cheapest | What the brief specifies |
| C. Direct Anthropic key | Yes | Anthropic list price | Needs Colin; the brief defers this to Phase 4 |

Option A is worth naming explicitly because it looks like a compromise and
isn't. If we are paying Anthropic prices anyway, the gateway buys us nothing
here and adds a dependency.

## Decision (proposed)

**1. Put the provider behind a seam, unconditionally.** All agent invocation
goes through a single composite action at `.github/actions/run-agent/`. No
workflow references a model or provider directly. Switching provider — for the
Phase 4 hardening swap, or as a mid-project escape — becomes a one-file change
instead of an edit across every workflow that runs the agent.

This is cheap and correct regardless of how the rest of this ADR resolves, so it
is not contingent on Colin's answer.

**2. Timebox a spike of Option B with an explicit pass/fail criterion**, rather
than either adopting or rejecting it on documentation alone. The criterion is
about tool use specifically, because that is where the unsupported surface bites:

> Given a seeded Linear issue of realistic scope, the agent must complete the
> full loop — read the repo, edit the right files, run the tests, open a PR
> whose checks pass — **three times out of three**, with no run in which it
> stalls, skips a tool call, or loses the task mid-way.

Two out of three is a fail, not a pass. An intermittently reliable agent is the
expensive case, because it invites us to keep debugging instead of switching.

**3. On failure, escalate to Option C immediately** rather than iterating on
prompts. The seam from (1) makes that a small change.

**4. Do not defer the Anthropic-key conversation to Phase 4.** The brief assumed
the cheap path works. It may not. Raising it now costs one message; raising it
mid-Phase-3a costs the critical path.

## Consequences

**If the spike passes:** we get the brief's cost profile for the build phase and
carry a known unsupported dependency, mitigated by the seam and by having tested
the specific capability that would break.

**If it fails:** we lose roughly half a day and need an Anthropic key sooner
than planned. The pipeline is unaffected — the deterministic spine (CI, security
scanning, build, deploy, Linear sync) has no model dependency at all, so it can
be finished and demonstrated while the agent question resolves.

**Either way** we avoid the worst outcome: building the agent workflow around an
assumption, then misreading a routing failure as a design failure.

**Cost of the seam:** one extra indirection when reading the workflows. Small,
and it pays for itself at the Phase 4 swap even if nothing goes wrong.

## Open question for Colin

The brief specifies Kimi/GLM via OpenRouter for the build phase. Both OpenRouter
and Anthropic document that combination as unsupported.

Do you want me to (a) spike it against the criterion above and report, or
(b) skip it and go straight to an Anthropic key? I default to (a) unless you say
otherwise — but it is your call, since (b) has a budget implication and (a) has
a schedule one.

## Evidence

- [OpenRouter × Claude Code setup guide](https://openrouter.ai/blog/tutorials/claude-code-openrouter/) — Anthropic Skin, exact env vars, the first-party-provider caveat
- [OpenRouter API reference](https://openrouter.ai/docs/api-reference/overview) — the OpenAI-compatible endpoint, for contrast
- [Claude Code — other LLM gateways](https://code.claude.com/docs/en/llm-gateway) — Anthropic's position on non-Claude models through a gateway
- `claude-code-action` [setup](https://github.com/anthropics/claude-code-action/blob/main/docs/setup.md) and [configuration](https://github.com/anthropics/claude-code-action/blob/main/docs/configuration.md) docs — authentication inputs, and the `settings` env hook
