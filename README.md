# AgentOps Platform

**AI infrastructure and observability platform for LLM gateways, tracing, evaluation, security, and cost controls.**

AgentOps provides an OpenAI-compatible gateway, trace instrumentation, cost tracking, policy enforcement, and CI-gated evaluations for AI agents.

It is built with a stdlib-first Python approach, runs fully offline with a built-in mock model, and can connect to any OpenAI-compatible provider when ready.

> **Live Demo:** https://agentops-platform-4d6p.onrender.com

---

## Project Status

- **Tests:** 26/26 passing
- **Local Dashboard:** Verified
- **Local API E2E:** Verified
- **PII Redaction:** Verified
- **Public Render Deployment:** Verified
- **Health Endpoint:** `/health`
- **Current Live Provider:** Built-in mock provider

The public deployment is currently intended for demonstration and portfolio use. It uses the built-in mock provider and an ephemeral trace database.

---

## Architecture

| Layer | What it does | Inspired by |
|---|---|---|
| **Gateway** | OpenAI-compatible proxy that traces calls, estimates/prices usage, redacts PII, rate-limits requests, enforces per-session budgets, and detects prompt loops | AgentOps-AI |
| **Tracing** | `@aop.agent`, `@aop.tool`, `@aop.llm`, `@aop.operation` decorators, nested spans, SQLite storage, and dashboard | AgentOps-AI |
| **Evals** | YAML configuration, JSONL datasets, 10 evaluators, baseline comparison, threshold gates, `results.json`, and `report.md` | Azure/agentops |
| **Ops** | `aop doctor`, GitHub Actions workflow generation, and trace-to-regression promotion | Azure/agentops |

The design was studied from two open-source MIT-licensed projects and then re-implemented from scratch.

See [`NOTICE.md`](NOTICE.md) and [`docs/RESEARCH.md`](docs/RESEARCH.md).

---

## Key Features

### LLM Gateway

- OpenAI-compatible `POST /v1/chat/completions`
- Request schema validation
- Configurable request-size limit
- PII redaction
- Session-aware tracing
- Rate limiting
- Prompt loop detection
- Per-session cost budgets
- Pre-request estimated-cost protection
- OpenAI-compatible responses
- Trace and cost response headers

### Tracing & Observability

- Agent instrumentation
- Tool instrumentation
- LLM instrumentation
- Operation instrumentation
- Nested spans
- SQLite trace storage
- Trace-level cost tracking
- Token usage tracking
- Model statistics
- Error tracking
- Web dashboard

### Evaluation

- YAML-based evaluation configuration
- JSONL datasets
- Multiple built-in evaluators
- Baseline comparison
- Regression detection
- Threshold-based quality gates
- CI integration
- Markdown and JSON reports

### Security & Controls

- PII redaction
- API authentication
- Request validation
- Request-size limiting
- Rate limiting
- Prompt loop detection
- Session budget enforcement
- Estimated-cost pre-checks
- Error/status tracing

---

## Quick Start

Clone the repository and install it:

```bash
git clone https://github.com/skmursalim9779-create/agentops-platform.git
cd agentops-platform
pip install -e .
