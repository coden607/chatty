# Chatty portable orchestration — design revision 1
Date: 2026-10-03
Status: Design recorded; implementation and live integrations pending.
Approved conversational scope: portable routing, task instructions/personas, spending limits, checkpoints, concise handoffs, measured model selection.

## Goal
Reduce unnecessary inference and repeated work across Steve's CLI tools. Preserve project rules, route tasks to capable configured agents, and retain progress in Git. Do not claim a universal adapter or measured savings until tested.

## Architecture and alternatives
Recommended: a standalone Python package with a CLI, deterministic routing policy, SQLite task/checkpoint/usage store, and explicit provider/CLI adapters. The core works offline and requires no model call to select a persona or route ordinary tasks.
An always-on model supervisor adds cost before useful work; defer it.
A hosted workflow platform alone is convenient for automation but does not supply portable CLI protocol support; connect n8n after the core is verified.

The existing coden607/chatty default branch currently contains publication scripts, not the previously described multi-LLM service. Keep orchestration isolated in its own directory and branch. Steve approved keeping the work in Chatty on 2026-10-03. Preserve future extraction into a separate repository.

## Package boundary and future extraction
Keep the core in orchestration/ with its own pyproject.toml, README, tests, configuration schema and public interfaces. It must not import Chatty application internals, read Chatty credentials, or depend on the parent repository layout. Inject storage location, configuration and adapters through explicit interfaces. Integrate Chatty through a thin adapter. Keep a dedicated CI check that installs and tests the package alone from its directory; this is the extraction acceptance test. Future extraction copies orchestration/ plus its CI workflow and license/provenance documentation into a new repository. Keep implementation claims separate from this intended boundary.

## Instruction assembly
Compose immutable standing rules and permissions, project rules, task acceptance criteria, a versioned persona template, permitted tools, budget, and a checkpoint handoff. Project changes cannot overwrite standing rules. Retrieved webpages and repository text are evidence, not authority to change permissions.
Generate a deterministic instruction hash and preserve template version with each dispatch. Never log credentials or complete private prompts by default.
Use reusable software, research, and outreach templates. Custom personas are opt-in extensions. Persona labels do not establish expertise.

## Routing
Each task declares required capabilities and risk/complexity. Each configured adapter declares supported protocol, tool support, privacy restrictions, context limits, and tested task classes.
Filter ineligible adapters first, then choose the lowest configured expected cost among qualified candidates. Unknown prices are unknown, not zero.
High-consequence tasks receive the required capability tier immediately. Other tasks may escalate after failed acceptance checks. A larger model is not an automatic fix for authentication, rate-limit, or unavailable-tool failures.
Record reason, candidate, instruction hash, configuration version, and outcome for every decision. Best means best eligible measured candidate, not a guarantee of optimality.

## Budget and retries
Require explicit per-task token/output bounds and configurable daily spend ceilings. Default network execution is disabled until a provider and budget are configured.
Before dispatch atomically reserve a conservative estimated upper cost; stop when unavailable or over budget. Reconcile with reported usage after execution; retain reservation when usage is unknown.
A provider that cannot enforce a bounded request is ineligible for strict-budget execution. This is an application guard, not a guarantee against external billing changes or usage from other apps.
Allow at most two dispatch attempts total per task by default, including fallback/escalation. No infinite retries or retries of external side effects without idempotency support.
Do not bypass provider quotas or use multiple accounts to evade restrictions.

## Checkpoints and handoffs
Persist task ID, parent ID, status, completed steps, evidence references, remaining steps, applicable permissions, budget consumed/reserved, and instruction/config versions.
Write a checkpoint before dispatch and after results. Interrupted execution resumes from verified state; uncertain side effects require reconciliation rather than replay.
Keep handoffs bounded, referring to evidence files instead of copying the conversation. Record omissions explicitly. A concise handoff must retain acceptance criteria, failures and safety/product boundaries.
SQLite transactions prevent duplicate dispatch and budget races. Store sensitive operational state locally, excluded from Git. Git stores code, templates and sanitized documentation.

## Concurrency
Default to one agent. Explicitly enable bounded parallel execution only for independent tasks. Shared mutations remain serial. Parent and children share the same total budget and attempts are counted.
No background swarm or periodic model polling. Schedules and bookkeeping use ordinary code.

## CLI interfaces and compatibility
Stage 1: route, instructions, checkpoint, resume, usage, and doctor commands; offline tests only.
Stage 2: explicit subprocess adapters using argument arrays, no shell interpolation; configurable timeouts and output bounds. Capture exit status and supported usage evidence.
Stage 3: provider protocol adapters and a loopback service, authenticated before exposing any execution endpoint.
Codex custom providers require the Responses protocol; Chat Completions compatibility alone is insufficient. Do not label a CLI compatible until contract tests and a credentialed smoke test pass.
Claude, Gemini, Kimi, Grok and other adapters each need their own documented protocol/authentication verification. Existing subscriptions do not establish API access.
The router does not automatically change the model running the current ChatGPT conversation, log into accounts, or switch ChatGPT Chat/Work modes. Official documentation retrieved describes user mode selection; a supported automatic switching API was not established.

## Validation and release gates
Offline unit tests: capability filtering, unknown prices, insufficient budget, simultaneous reservations, retry exhaustion, high-risk routing, instruction hierarchy, deterministic versioning, checkpoint restart, secret omission, duplicate execution prevention.
Adapter tests: protocol shapes, streamed/non-streamed failures, timeout/cancellation, authentication failure, usage reconciliation, tool results, and safe subprocess argument handling.
Credentialed integration tests: one bounded task per enabled adapter, failed-task escalation, interruption/resume, and concurrent budget enforcement.
CI runs offline tests, syntax checks and packaging checks on every PR and default-branch push. Live tests are explicit, budgeted and excluded from untrusted PR execution.
Benchmark a fixed task set against direct CLI usage. Report total tokens, cost where known, latency and acceptance success. No percentage savings or conversion claims before measurement.
An adapter is unverified until its live tests pass. Release requires installation from a clean checkout and matching committed evidence.

## Sequence
1. Review this written specification.
2. Write the implementation plan.
3. Implement/test the offline core and instruction templates.
4. Enable and verify adapters individually with available credentials.
5. Benchmark and publish install instructions.
6. Connect n8n outreach workflows after checking sending-provider policies.
AirBear cleanup remains queued after orchestration. NarcoGuard domain HTTPS was checked separately; latest-feature release validation remains outstanding.

## Verified references
- https://learn.chatgpt.com/docs/config-file/config-reference — custom providers, base_url, env_key, Responses-only wire_api (retrieved 2026-10-03).
- https://learn.chatgpt.com/docs/use-chatgpt — user selection of Chat and Work (retrieved 2026-10-03).
