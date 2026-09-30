import json
from pathlib import Path


def render_markdown(results):
    s, gate, cmp_ = results["summary"], results["gate"], results.get("comparison")
    out = [f"# AgentOps Eval Report\n", f"**Gate: {'PASS' if gate['passed'] else 'FAIL'}**\n"]
    out += [f"- {f}" for f in gate["failures"]]
    out += ["", "| Metric | Value |", "|---|---|",
            f"| Cases | {s['passed']}/{s['total']} passed ({s['pass_rate']:.1%}) |",
            f"| Avg latency | {s['avg_latency_ms']:.1f} ms |", f"| P95 latency | {s['p95_latency_ms']:.1f} ms |",
            f"| Total cost | ${s['total_cost_usd']:.6f} |", f"| Tokens | {s['total_tokens']} |", ""]
    out += ["## Evaluators", "", "| Evaluator | Pass rate |", "|---|---|"]
    out += [f"| {k} | {v:.1%} |" for k, v in s["by_evaluator"].items()]
    if cmp_:
        d = cmp_["deltas"]
        out += ["", "## Comparison vs Baseline", "",
                f"- Pass rate Δ: {d['pass_rate']:+.1%}", f"- Avg latency Δ: {d['avg_latency_ms']:+.1f} ms",
                f"- Cost Δ: ${d['total_cost_usd']:+.6f}",
                f"- Regressed cases: {', '.join(cmp_['regressed_cases']) or 'none'}",
                f"- Fixed cases: {', '.join(cmp_['fixed_cases']) or 'none'}"]
    failed = [c for c in results["cases"] if not c["passed"]]
    if failed:
        out += ["", "## Failed cases", ""]
        for c in failed:
            bad = "; ".join(f"{k}: {v['detail']}" for k, v in c["checks"].items() if not v["passed"])
            out.append(f"- `{c['id']}` — {bad}")
    return "\n".join(out) + "\n"


def write_outputs(results, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (out / "report.md").write_text(render_markdown(results), encoding="utf-8")
    return out
