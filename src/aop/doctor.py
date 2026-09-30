"""Readiness checks: is this project actually operable in production?"""
from pathlib import Path

from .config import load_config


def run_checks(root="."):
    root = Path(root)
    checks = []

    def add(name, status, hint=""):
        checks.append({"name": name, "status": status, "hint": hint})

    cfg_path = root / "agentops.yaml"
    cfg = None
    if cfg_path.exists():
        try:
            cfg = load_config(cfg_path)
            add("config", "pass")
        except Exception as exc:
            add("config", "fail", f"cannot parse agentops.yaml: {exc}")
    else:
        add("config", "fail", "run `aop init`")
    if cfg:
        ds = root / cfg.get("dataset", "")
        add("dataset", "pass" if ds.is_file() else "fail", "" if ds.is_file() else f"missing {ds}")
        th = cfg.get("thresholds") or {}
        add("gate thresholds", "pass" if th else "warn", "" if th else "define thresholds to make evals block releases")
        add("evaluator coverage", "pass" if len(cfg.get("evaluators", [])) >= 3 else "warn",
            "use 3+ evaluators (quality, safety, latency/cost)")
    add("baseline", "pass" if (root / ".aop/baseline/results.json").exists() else "warn",
        "save one: cp .aop/results/latest/results.json .aop/baseline/results.json")
    wf = list((root / ".github/workflows").glob("*.y*ml")) if (root / ".github/workflows").exists() else []
    add("CI workflow", "pass" if wf else "warn", "" if wf else "run `aop workflow generate`")
    add("trace store", "pass" if (root / ".aop/traces.db").exists() else "warn",
        "" if (root / ".aop/traces.db").exists() else "route agents through `aop gateway` or `aop demo`")
    return checks
