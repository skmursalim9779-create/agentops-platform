# AgentOps Platform

Gateway + tracing + cost tracking + **CI-gated evals** for AI agents. Stdlib-first Python; runs fully offline with a built-in mock model, and points at any OpenAI-compatible provider when you are ready.

Design studied from two open-source (MIT) projects, then re-implemented from scratch. See `NOTICE.md` and `docs/RESEARCH.md`.

| Layer | What it does | Inspired by |
|---|---|---|
| **Gateway** | OpenAI-compatible proxy: traces every call, prices it, redacts PII, rate-limits, enforces a per-session budget, detects prompt loops | AgentOps-AI (monitoring, cost) |
| **Tracing** | `@aop.agent`, `@aop.tool`, `@aop.llm`, `@aop.operation` decorators, nested spans, SQLite store, dashboard | AgentOps-AI (span decorators) |
| **Evals** | YAML config, JSONL datasets, 10 evaluators, baseline comparison, threshold gate (exit code 2), `results.json` + `report.md` | Azure/agentops (eval/CI model) |
| **Ops** | `aop doctor` readiness checks, GitHub Actions generator, trace-to-regression promotion | Azure/agentops (Doctor, workflow, promote-traces) |

## Quick start

```bash
pip install -e .
aop demo                 # seed traces from the demo agent
aop traces               # list traces
aop eval run             # run the smoke suite; exit 0 = gate passed, 2 = gate failed
aop gateway              # http://127.0.0.1:8787  (dashboard at /)
```

Call the gateway like OpenAI:

```bash
curl localhost:8787/v1/chat/completions -H 'content-type: application/json' \
  -H 'x-aop-session: demo1' -H 'x-aop-agent: my-agent' \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"What is 6 x 7?"}]}'
```
Responses carry `x-aop-trace-id` and `x-aop-cost-usd`. For a real provider:
`AOP_UPSTREAM_API_KEY=sk-... aop gateway --provider openai --upstream https://api.openai.com/v1/chat/completions`

## Instrument your own agent

```python
import aop

@aop.tool("search")
def search(q): ...

@aop.agent("researcher")
def run(prompt):
    with aop.get_tracer().span("llm:gpt-4o-mini", kind="llm") as sp:
        text = call_model(prompt)
        sp.set_usage("gpt-4o-mini", tokens_in, tokens_out)   # cost is computed for you
    return text
```
Async functions are supported. Errors are recorded on the span and re-raised.

## Evals in CI

1. `aop init` creates `agentops.yaml` (target, dataset, evaluators, thresholds).
2. `aop eval run` writes `.aop/results/latest/results.json` and `report.md`.
3. Save a baseline: `cp .aop/results/latest/results.json .aop/baseline/results.json`
4. `aop eval run --baseline .aop/baseline/results.json` adds per-metric deltas and fails the gate on regressions beyond `max_regression`.
5. `aop workflow` writes a GitHub Actions workflow that does all of the above on every PR.

**Targets:** `python` (`module:function`), `http` (POST `{"input": ...}`), `gateway` (OpenAI-style).
**Evaluators:** `exact_match`, `contains`, `regex`, `json_valid`, `latency`, `cost`, `tool_calls`, `safety_refusal`, `no_pii`, and `python` for your own (`function: pkg.mod:fn`).

Turn real production traces into regression cases: `aop eval promote-traces` (review the `expected` values, they are the model's past answers, not ground truth).

## Prices
`src/aop/pricing.py` ships **illustrative** per-token prices. Provider pricing changes, so set `AOP_PRICING_FILE` to a JSON file like `{"gpt-4o-mini": [0.15, 0.60]}` (USD per 1M tokens, input/output) before trusting cost numbers.

## Tests
```bash
python -m unittest discover -s tests
```

## Roadmap
Foundry / OpenTelemetry export, streaming support in the gateway, LLM-as-judge evaluator, multi-tenant API keys, Postgres store, red-team dataset packs.
