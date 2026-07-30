# Security Policy

## Scope

GoldPath is a **demo application**. It exists to prove out an agentic delivery
pipeline — Linear issue to agent to PR to CI to production — and carries no
real user data. The application code is deliberately thin; the pipeline around
it is the artefact under test.

Treat anything deployed from this repository as disposable.

## Reporting a vulnerability

Open a [private security advisory](https://github.com/GhadeerHayek/GoldPath/security/advisories/new).
Please do not open a public issue for anything exploitable.

## What is enforced automatically

Every pull request into `main` must pass:

| Check | Catches |
|---|---|
| `secrets` | Credentials anywhere in commit history (gitleaks, full clone depth) |
| `sast` | Insecure code patterns (Semgrep `p/python`, `p/security-audit`) |
| `deps` | Known CVEs and package-integrity mismatches in the locked dependency tree (pip-audit, `--require-hashes`) |
| `lint` / `test` / `image` | Correctness, and that the container builds and boots |

Dependabot tracks Python packages, workflow actions, and the container base
image, with a cooldown so a freshly published (and possibly compromised)
release is not adopted the day it lands.

Third-party GitHub Actions are pinned to commit SHAs rather than tags. A tag
is mutable; a SHA is not.

## Credential isolation

This is the part worth reading, because it is the design constraint the whole
pipeline is built around.

- **Agents never hold deployment credentials.** The workflow that runs the
  coding agent can write branches, pull requests, and issue comments. It
  cannot reach the VPS. Compromising the agent yields a pull request, which
  still has to pass every check above.
- **Only the deploy job holds them.** VPS credentials live in a protected
  GitHub Environment referenced by exactly one workflow.
- **Deploys do not run as root.** A dedicated unix account with an SSH key
  restricted to a single command performs the release.

If you find a path that crosses one of those boundaries, that is a
vulnerability in the pipeline even if the application is unaffected — please
report it.
