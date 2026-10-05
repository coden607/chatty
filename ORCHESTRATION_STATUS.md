# Adaptive orchestration status

The `feat/adaptive-orchestration-router` branch now enforces the shared routing policy in the three known generation paths: `TOKENSPIN_BRIDGE.py`, `FREE_LLM_ROUTER.py`, and `CHATTY_MODEL_ROUTER.py`.

## Implemented

- Deterministic project/task/risk/complexity classification.
- Quality-floor-first model eligibility followed by configured token-efficiency ranking.
- Context capability checks; an undersized model is never selected as fallback.
- Explicit `allow_paid=True` requirement for paid/known-paid paths.
- Paid policy is preserved across FreeLLMRouter retries.
- Tokenspin is treated as opaque and bypassed by default unless paid fallback is explicitly authorized.
- Output budget is enforced by the Tokenspin bridge before execution.
- Personas, skills, framework choice, verification requirements, and isolated project metadata are emitted in each routing plan.
- Routing plans do not claim runtime provider availability, price, execution verification, or measured savings.

## Validation gates

Focused unit tests cover project/risk classification, context overflow, paid opt-in, provider exclusion, quality-floor rejection, and token-efficiency selection.

Before release, exact-head validation must still prove:
1. Python compile succeeds for all changed Python files.
2. Focused unit tests pass.
3. Retry/fallback integration cannot bypass `allow_paid`.
4. Runtime provider smoke tests are performed only for configured/authenticated providers.
5. Any claimed savings use measured provider usage or comparable workload telemetry, never assumed pricing.

The repository currently has no GitHub Actions workflow attached to this PR head, so absence of CI is not evidence of a pass. Do not claim production readiness until the exact-head validation gates above are executed.
