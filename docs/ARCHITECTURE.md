# Architecture

```
 agent code ──(decorators / spans)──┐
                                    ▼
 client ──► Gateway ──► provider    SpanStore (SQLite) ◄── dashboard (/, /api/*)
            │ rate limit  (mock or         ▲
            │ PII redact   OpenAI-compat)  │ aop eval promote-traces
            │ budget/loop                  │
            └── trace + cost ──────────────┘

 agentops.yaml + dataset.jsonl ──► Eval runner ──► target (python|http|gateway)
                                       │ evaluators → summary → baseline compare → gate
                                       ▼
                            results.json + report.md + exit code (0 ok / 1 error / 2 gate fail)
```

Modules: `tracing.py` (spans, contextvars), `store.py`, `pricing.py`, `policies.py`, `gateway.py`, `dashboard.py`,
`evals/{evaluators,runner,report}.py`, `doctor.py`, `workflow.py`, `cli.py`.

Design choices: stdlib HTTP server keeps the gateway dependency-free and testable offline (swap for FastAPI/uvicorn for production concurrency);
one SQLite table keeps traces portable; gate logic is pure functions (`compare`, `evaluate_gate`) so it is unit-tested without I/O.
