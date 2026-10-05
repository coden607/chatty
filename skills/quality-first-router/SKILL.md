---
name: quality-first-router
description: Route coding work to the lowest-cost model appropriate to the task while preserving engineering quality through risk-aware escalation and objective verification.
---

# Quality-First Coding Router

Use this skill before selecting a model or spawning additional coding agents.

## Objective

Minimize tokens and model cost without lowering the engineering acceptance standard.

Do **not** interpret this as "cheapest model that passes tests." Tests are evidence, not proof of optimal code.

## 1. Classify the task

Assign the highest applicable risk tier.

### Tier 0 — Mechanical
Examples: formatting, comments/docs, renames, generated boilerplate, trivial config edits.

Use the cheapest available capable model.

### Tier 1 — Routine implementation
Examples: localized CRUD, small UI changes, straightforward tests, isolated bug fixes with a known cause.

Start with a low-cost capable model. Escalate only if verification fails, uncertainty remains material, or the change expands beyond the original scope.

### Tier 2 — Reasoning-sensitive
Examples: multi-file refactors, unfamiliar debugging, concurrency, nontrivial data flow, public API changes, cross-service behavior.

Use a stronger reasoning model or escalate before implementation when the cheap model cannot produce a clear plan with bounded risk.

### Tier 3 — Critical
Examples: authentication/authorization, secrets, payments, destructive migrations, safety-critical logic, cryptography, security boundaries, performance-critical architecture, release infrastructure.

Use a premium/high-reasoning model from the start. Do not economize by starting with a weak model.

## 2. Minimize context

Load only:
- task requirements;
- repository instructions;
- directly relevant files/symbols;
- failing diagnostics/tests;
- the current diff when reviewing.

Do not preload unrelated conversation history, entire repositories, every skill, or every MCP description.

Prefer retrieval on demand.

## 3. One implementer by default

Use one model/agent for the first implementation.

Do not automatically:
- run a swarm;
- ask multiple models for the same solution;
- have a premium model restate successful low-risk work.

Add another agent/model only when it has a distinct job that materially reduces risk.

## 4. Verify against the task's real quality dimensions

Always run the repository's applicable baseline checks.

Possible evidence:
- tests;
- typecheck/compile;
- lint/format;
- static analysis;
- security checks;
- changed-scope regression tests;
- browser/e2e checks;
- benchmark/profiling for performance-sensitive work;
- migration validation for schema/data changes.

A green test suite does not establish optimal architecture, efficiency, maintainability, or security. For those dimensions, require the relevant evidence or stronger review.

## 5. Escalate intelligently

Escalate when any of these are true:
- required checks fail and the first model cannot repair them cheaply;
- the root cause remains uncertain;
- the task crosses into a higher risk tier;
- implementation requires architectural tradeoffs;
- performance/security correctness lacks objective evidence;
- repeated attempts are consuming more budget than escalation would;
- confidence is insufficient for the consequence of failure.

When escalating, pass a compact handoff:
- original requirement;
- relevant constraints;
- current diff;
- failed checks and exact errors;
- unresolved decisions.

Do not replay the full transcript unless it is genuinely required.

## 6. Stop when sufficient evidence exists

If the implementation satisfies the requirement and the risk-appropriate checks pass, stop.

Do not spend tokens on redundant model reviews solely to seek stylistic agreement.

For Tier 2/3 work, require the risk-appropriate review/evidence even if basic tests pass.

## 7. Paid fallback is explicit

Never silently route to a paid provider or paid fallback when policy/configuration requires approval.

If no allowed model can safely complete the task:
1. stop;
2. report the blocker and evidence;
3. request explicit permission for the paid/stronger fallback when required.

## 8. Measure savings without gaming quality

Record per workflow when available:
- selected model/provider;
- task tier;
- input/output tokens;
- retries;
- escalations and reason;
- verification performed;
- pass/fail outcome;
- estimated cost;
- baseline comparison.

Optimize for:
1. accepted quality;
2. fewer unnecessary tokens;
3. lower cost;
4. lower latency.

Never claim savings from unsupported pricing/provider data. Label estimates and unknowns.

## 9. Model selection remains configuration

This skill does not hard-code which vendor/model is "cheap" or "best."

The router must use current configured capability, availability, price, privacy, and paid-fallback policy. If those facts are unverified, treat them as unknown rather than inventing coverage.

## Decision shorthand

- T0: cheapest capable -> verify -> stop.
- T1: low-cost capable -> verify -> escalate only on evidence.
- T2: stronger reasoning or justified escalation -> expanded verification.
- T3: premium/high-reasoning immediately -> critical-domain verification/review.
