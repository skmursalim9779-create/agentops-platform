# Research notes

Sources: the two repository READMEs (fetched Sep 2026). Source trees were NOT reviewed line by line, so treat implementation details below as README-level.

## AgentOps-AI/agentops (~5.8k stars, MIT)
- Python SDK + a self-hostable app (`app/`) for agent observability. `agentops.init(key)` auto-instruments LLM calls.
- Span decorators: `@session`, `@agent`, `@operation`/`@task`, `@workflow`; capture inputs/outputs, exceptions, async, generators.
- Strengths: broad framework integrations (CrewAI, AG2/AutoGen, LangChain, LlamaIndex, OpenAI Agents SDK, LiteLLM, Anthropic, Mistral, Cohere...), session replay, cost analytics.
- Its own roadmap still lists as unfinished: CI/CD integration checks, regression testing, loop/recursive-thought detection, token/context overflow flags, agent scorecards, evaluation playground.

## Azure/agentops (AgentOps Accelerator, MIT)
- CLI-first: `agentops init`, `eval run [--baseline]`, `doctor [--evidence-pack]`, `workflow generate`, `eval promote-traces`, `cockpit`.
- Config in `agentops.yaml`; outputs `results.json` (versioned schema) + `report.md` (PR-friendly); release evidence pack.
- Baseline comparison with per-metric deltas; CI/CD gate generation; local "Cockpit" command center.
- Strongly Foundry/Azure-oriented (Foundry agents, App Insights), so less useful as-is for other stacks.

## Gap analysis, and what this project does about it
| Gap | Where it shows | This project |
|---|---|---|
| Observability without release gating | AgentOps-AI roadmap | Evals with thresholds and exit codes, generated CI workflow |
| Evals tied to one cloud | Azure/agentops | Provider-neutral targets (python/http/gateway) |
| Loop / budget protection missing | AgentOps-AI roadmap | Gateway loop detector + per-session budget |
| No PII guard at the call boundary | both | Gateway redaction + `no_pii` evaluator |
| Traces and evals live apart | both | `promote-traces` closes the loop: production traces become regression cases |
| Needs cloud account to try | both | Offline mock model, SQLite, stdlib gateway |
