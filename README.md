# AgentOps Platform

**AI infrastructure and observability platform for LLM gateways, tracing, evaluation, security, and cost controls.**

AgentOps provides an OpenAI-compatible gateway, trace instrumentation, cost tracking, policy enforcement, and CI-gated evaluations for AI agents. It uses a stdlib-first Python approach, runs fully offline with a built-in mock model, and can connect to an OpenAI-compatible provider when you are ready.

> **Live demo:** https://agentops-platform-4d6p.onrender.com

## Project status

- **Tests:** 26/26 passing
- **Local dashboard:** verified
- **Local API E2E:** verified
- **PII redaction:** verified
- **Public Render deployment:** verified
- **Health endpoint:** `/health`
- **Current live provider:** built-in mock provider

> The public demo is intended for demonstration and portfolio use. The current Render deployment uses the mock provider and an ephemeral trace database.

## Architecture

| Layer | What it does | Inspired by |
|---|---|---|
| **Gateway** | OpenAI-compatible proxy: traces every call, prices it, redacts PII, rate-limits, enforces a per-session budget, and detects prompt loops | AgentOps-AI (monitoring, cost) |
| **Tracing** | `@aop.agent`, `@aop.tool`, `@aop.llm`, `@aop.operation` decorators, nested spans, SQLite store, dashboard | AgentOps-AI (span decorators) |
| **Evals** | YAML config, JSONL datasets, 10 evaluators, baseline comparison, threshold gate (exit code 2), `results.json` + `report.md` | Azure/agentops (eval/CI model) |
| **Ops** | `aop doctor` readiness checks, GitHub Actions generator, and trace-to-regression promotion | Azure/agentops (Doctor, workflow, promote-traces) |

The design was studied from two open-source MIT-licensed projects and then re-implemented from scratch. See [`NOTICE.md`](NOTICE.md) and [`docs/RESEARCH.md`](docs/RESEARCH.md).

## Key capabilities

### LLM Gateway

- OpenAI-compatible `POST /v1/chat/completions`
- Request validation
- Configurable request-size limit
- PII redaction
- Session-aware tracing
- Rate limiting
- Prompt loop detection
- Per-session cost budget
- Estimated-cost pre-check before provider execution
- OpenAI-compatible response format
- Trace and cost response headers

### Tracing and observability

Instrument your agent with decorators and nested spans:

```python
import aop

@aop.tool("search")
def search(q):
    ...

@aop.agent("researcher")
def run(prompt):
    with aop.get_tracer().span("llm:gpt-4o-mini", kind="llm") as sp:
        text = call_model(prompt)
        sp.set_usage("gpt-4o-mini", tokens_in, tokens_out)
    return text
```

Async functions are supported. Errors are recorded on the span and re-raised.

The dashboard exposes aggregate trace, token, cost, model, latency, and error information.

## Quick start

```bash
pip install -e .

aop doctor
aop demo
aop traces
aop eval run
aop gateway
```

The default local gateway runs at:

```text
http://127.0.0.1:8787
```

The dashboard is available at `/`.

## Calling the gateway

```bash
curl http://127.0.0.1:8787/v1/chat/completions \
  -H 'content-type: application/json' \
  -H 'x-aop-session: demo1' \
  -H 'x-aop-agent: my-agent' \
  -d '{"model":"gpt-4o-mini","messages":[{"role":"user","content":"What is 6 x 7?"}]}'
```

Responses include the following headers:

```text
x-aop-trace-id
x-aop-cost-usd
```

### Real provider

The gateway can point to an OpenAI-compatible upstream:

```bash
AOP_UPSTREAM_API_KEY=sk-... \
aop gateway \
  --provider openai \
  --upstream https://api.openai.com/v1/chat/completions
```

Do not commit provider API keys or other secrets to the repository.

## API authentication

When `AOP_API_KEY` is configured, the gateway and protected `/api/*` endpoints require the `x-aop-key` header:

```bash
curl http://127.0.0.1:8787/api/stats \
  -H 'x-aop-key: YOUR_AOP_API_KEY'
```

For local development, authentication remains optional when `AOP_API_KEY` is not configured.

## Evals in CI

1. `aop init` creates `agentops.yaml` with target, dataset, evaluator, and threshold configuration.
2. `aop eval run` writes `.aop/results/latest/results.json` and `report.md`.
3. Save a baseline:

```bash
cp .aop/results/latest/results.json .aop/baseline/results.json
```

4. Run against the baseline:

```bash
aop eval run --baseline .aop/baseline/results.json
```

5. `aop workflow` writes a GitHub Actions workflow that runs the evaluation flow on pull requests.

### Targets

Supported target types:

- `python` — `module:function`
- `http` — POST `{"input": ...}`
- `gateway` — OpenAI-style chat completion

### Evaluators

```text
exact_match
contains
regex
json_valid
latency
cost
tool_calls
safety_refusal
no_pii
python
```

The `python` evaluator supports your own function using `function: pkg.mod:fn`.

### Promoting traces

Turn real traces into regression cases:

```bash
aop eval promote-traces
```

Review generated `expected` values before using them as a regression baseline. They are previous model outputs, not independent ground truth.

## Security controls

AgentOps includes multiple protections around LLM requests and agent execution:

```text
PII redaction
API authentication
Request schema validation
Request-size limiting
Rate limiting
Prompt loop detection
Per-session budget enforcement
Pre-request estimated-cost checks
Error/status tracing
```

These controls are designed to reduce accidental data exposure, runaway requests, repeated-agent loops, and uncontrolled model spending.

## Cost tracking

`src/aop/pricing.py` ships **illustrative** per-token prices.

Provider pricing changes over time, so configure your own pricing file before relying on cost figures:

```bash
AOP_PRICING_FILE=pricing.json
```

Example:

```json
{
  "gpt-4o-mini": [0.15, 0.60]
}
```

Values are USD per 1 million tokens in the order:

```text
[input_price, output_price]
```

## Dashboard

Start the gateway:

```bash
aop gateway --host 127.0.0.1 --port 8787
```

Open:

```text
http://127.0.0.1:8787/
```

The dashboard provides:

- trace counts
- span counts
- token totals
- cost totals
- error counts
- per-model statistics
- trace list
- trace detail view

## Tests

Run the full test suite:

```bash
python -m unittest discover -s tests -v
```

Current verification:

```text
26 tests
26 passed
0 failed
0 errors
```

## Repository structure

```text
agentops-platform/
├── .github/
│   └── workflows/
├── datasets/
├── docs/
├── examples/
├── src/
│   └── aop/
│       ├── evals/
│       ├── cli.py
│       ├── config.py
│       ├── dashboard.py
│       ├── doctor.py
│       ├── evals/
│       ├── gateway.py
│       ├── mock_llm.py
│       ├── policies.py
│       ├── pricing.py
│       ├── store.py
│       └── tracing.py
├── tests/
├── agentops.yaml
├── pyproject.toml
├── LICENSE
├── NOTICE.md
└── README.md
```

## Research and design notes

See:

- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- [`docs/RESEARCH.md`](docs/RESEARCH.md)
- [`NOTICE.md`](NOTICE.md)

The repository documents which ideas were studied and which implementation was built from scratch.

## Roadmap

- OpenTelemetry / Foundry export
- Streaming support in the gateway
- LLM-as-judge evaluator
- Multi-tenant API keys
- Postgres trace store
- Red-team dataset packs

## License

MIT. See [`LICENSE`](LICENSE).
