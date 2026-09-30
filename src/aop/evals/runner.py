"""Eval runner: dataset -> target -> evaluators -> summary -> baseline comparison -> gate."""
import importlib
import json
import sys
import time
import urllib.request
from pathlib import Path

from .evaluators import REGISTRY

SCHEMA_VERSION = 1


def load_dataset(path):
    rows = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            row = json.loads(line)
        except ValueError as exc:
            raise ValueError(f"{path}:{n}: invalid JSON ({exc})")
        if "input" not in row:
            raise ValueError(f"{path}:{n}: missing 'input'")
        row.setdefault("id", f"case-{n}")
        rows.append(row)
    return rows


# -- targets --------------------------------------------------------------
def _normalise(raw):
    if isinstance(raw, str):
        raw = {"output": raw}
    return {"output": raw.get("output", ""), "tools": raw.get("tools", []),
            "tokens_in": raw.get("tokens_in", 0), "tokens_out": raw.get("tokens_out", 0),
            "cost_usd": raw.get("cost_usd", 0.0)}


def make_target(cfg):
    kind = cfg.get("type", "python")
    if kind == "python":
        sys.path.insert(0, str(Path.cwd()))
        mod, _, fn = cfg["function"].partition(":")
        func = getattr(importlib.import_module(mod), fn)
        return lambda case: _normalise(func(case["input"]))
    if kind == "http":
        def call(case):
            req = urllib.request.Request(cfg["url"], data=json.dumps({"input": case["input"]}).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=cfg.get("timeout", 60)) as r:
                body = r.read().decode()
            try:
                return _normalise(json.loads(body))
            except ValueError:
                return _normalise(body)
        return call
    if kind == "gateway":
        def call(case):
            payload = {"model": cfg.get("model", "mock-1"),
                       "messages": [{"role": "user", "content": case["input"]}]}
            req = urllib.request.Request(cfg["url"], data=json.dumps(payload).encode(),
                                         headers={"Content-Type": "application/json",
                                                  "x-aop-agent": cfg.get("agent", "eval")})
            with urllib.request.urlopen(req, timeout=cfg.get("timeout", 60)) as r:
                data = json.loads(r.read())
            u = data.get("usage", {})
            return {"output": data["choices"][0]["message"]["content"], "tools": [],
                    "tokens_in": u.get("prompt_tokens", 0), "tokens_out": u.get("completion_tokens", 0),
                    "cost_usd": float(r.headers.get("x-aop-cost-usd", 0))}
        return call
    raise ValueError(f"unknown target type: {kind}")


# -- run ------------------------------------------------------------------
def _p95(values):
    if not values:
        return 0.0
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(0.95 * (len(ordered) - 1))))]


def run_eval(config, baseline=None, base_dir="."):
    dataset = load_dataset(Path(base_dir) / config["dataset"])
    target = make_target(config["target"])
    evaluators = config.get("evaluators") or [{"type": "contains"}]
    cases = []
    for case in dataset:
        started = time.perf_counter()
        error = None
        try:
            result = target(case)
        except Exception as exc:  # a crashing target is a failed case, not a crashed run
            result = _normalise("")
            error = f"{type(exc).__name__}: {exc}"
        result["latency_ms"] = (time.perf_counter() - started) * 1000
        checks = {}
        for ev in evaluators:
            name = ev.get("name") or ev["type"]
            if error:
                checks[name] = {"passed": False, "detail": error}
                continue
            params = {k: v for k, v in ev.items() if k not in ("type", "name")}
            passed, detail = REGISTRY[ev["type"]](case, result, params)
            checks[name] = {"passed": bool(passed), "detail": detail}
        cases.append({"id": case["id"], "input": case["input"], "expected": case.get("expected"),
                      "tags": case.get("tags", []), "output": result["output"], "tools": result["tools"],
                      "latency_ms": round(result["latency_ms"], 2), "tokens_in": result["tokens_in"],
                      "tokens_out": result["tokens_out"], "cost_usd": result["cost_usd"], "error": error,
                      "checks": checks, "passed": all(c["passed"] for c in checks.values())})

    n = len(cases)
    names = list(cases[0]["checks"]) if cases else []
    summary = {
        "total": n, "passed": sum(c["passed"] for c in cases),
        "pass_rate": (sum(c["passed"] for c in cases) / n) if n else 0.0,
        "by_evaluator": {nm: sum(c["checks"][nm]["passed"] for c in cases) / n for nm in names} if n else {},
        "avg_latency_ms": sum(c["latency_ms"] for c in cases) / n if n else 0.0,
        "p95_latency_ms": _p95([c["latency_ms"] for c in cases]),
        "total_cost_usd": sum(c["cost_usd"] for c in cases),
        "total_tokens": sum(c["tokens_in"] + c["tokens_out"] for c in cases),
    }
    results = {"schema_version": SCHEMA_VERSION, "summary": summary, "cases": cases}
    thresholds = config.get("thresholds", {})
    results["comparison"] = compare(results, baseline, thresholds.get("max_regression", 0.05)) if baseline else None
    results["gate"] = evaluate_gate(summary, results["comparison"], thresholds)
    return results


def compare(current, baseline, tolerance):
    cs, bs = current["summary"], baseline["summary"]
    deltas = {"pass_rate": cs["pass_rate"] - bs["pass_rate"],
              "avg_latency_ms": cs["avg_latency_ms"] - bs["avg_latency_ms"],
              "total_cost_usd": cs["total_cost_usd"] - bs["total_cost_usd"]}
    per_eval = {k: v - bs["by_evaluator"].get(k, v) for k, v in cs["by_evaluator"].items()}
    old = {c["id"]: c["passed"] for c in baseline["cases"]}
    regressed = [c["id"] for c in current["cases"] if old.get(c["id"]) and not c["passed"]]
    fixed = [c["id"] for c in current["cases"] if old.get(c["id"]) is False and c["passed"]]
    regressions = [k for k, d in per_eval.items() if d < -tolerance]
    if deltas["pass_rate"] < -tolerance:
        regressions.append("pass_rate")
    return {"deltas": deltas, "per_evaluator": per_eval, "regressed_cases": regressed,
            "fixed_cases": fixed, "regressions": regressions, "tolerance": tolerance}


def evaluate_gate(summary, comparison, thresholds):
    failures = []
    if "min_pass_rate" in thresholds and summary["pass_rate"] < thresholds["min_pass_rate"]:
        failures.append(f"pass_rate {summary['pass_rate']:.2%} < {thresholds['min_pass_rate']:.2%}")
    for name, minimum in (thresholds.get("evaluators") or {}).items():
        got = summary["by_evaluator"].get(name)
        if got is not None and got < minimum:
            failures.append(f"evaluator '{name}' {got:.2%} < {minimum:.2%}")
    if "max_p95_latency_ms" in thresholds and summary["p95_latency_ms"] > thresholds["max_p95_latency_ms"]:
        failures.append(f"p95 latency {summary['p95_latency_ms']:.0f}ms > {thresholds['max_p95_latency_ms']}ms")
    if "max_total_cost_usd" in thresholds and summary["total_cost_usd"] > thresholds["max_total_cost_usd"]:
        failures.append(f"cost ${summary['total_cost_usd']:.4f} > ${thresholds['max_total_cost_usd']}")
    if comparison and comparison["regressions"]:
        failures.append("regression vs baseline: " + ", ".join(comparison["regressions"]))
    return {"passed": not failures, "failures": failures}
