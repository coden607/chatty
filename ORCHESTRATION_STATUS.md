# Adaptive orchestration status

The `feat/adaptive-orchestration-router` branch provides a deterministic planning
policy. It is not yet an end-to-end execution integration.

## Verified policy behavior

- Task and project detection select persona, skills, and suggested token budgets.
- Unavailable providers are excluded.
- Candidates must satisfy capability and context requirements; there is no
  fallback that discards these constraints.
- Paid-tier candidates require explicit `allow_paid=True`. Risk classification
  alone does not authorize paid fallback.
- Plans report `execution_verified=False` and whether paid fallback is allowed.

Run `python3 -m unittest test_adaptive_orchestration_router -v` to check the policy.

## Remaining execution work

- Wire the plan into the actual generation entry points. The existing API uses
  Tokenspin/FreeLLMRouter, and CHATTY_MODEL_ROUTER has a separate fallback path.
- Enforce context/output and total workflow budgets before provider requests.
- Use configured, runtime-validated models instead of assuming registry entries
  remain available or free. In particular, FREE_LLM_ROUTER includes xAI entries
  described as paid fallback; its name is not a spending guarantee.
- Carry spending policy through every retry and fallback, including Tokenspin.
- Bound retry counts and agent concurrency; preserve a queue and isolated project
  context. A suggested `parallel_agents` value does not launch agents.
- Record provider-reported usage and configured pricing, and verify savings using
  measured comparable workloads.
- Verify authenticated access and a real provider smoke test on the target
  runtime before deploying. This branch does not change ChatGPT's own billing.

These checks remain release blockers for claiming cost-controlled execution.
