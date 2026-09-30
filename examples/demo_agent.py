"""A tiny agent instrumented with AgentOps Platform: calculator tool + mock LLM."""
import re

import aop
from aop import mock_llm
from aop.policies import redact
from aop.pricing import estimate_tokens

ARITH = re.compile(r"(-?\d+(?:\.\d+)?)\s*([+\-*/x×])\s*(-?\d+(?:\.\d+)?)")
MODEL = "mock-1"


@aop.tool("calculator")
def calculator(a, op, b):
    return mock_llm.calc(a, op, b)


def _llm(prompt):
    prompt, _ = redact(prompt)
    tracer = aop.get_tracer()
    with tracer.span(f"llm:{MODEL}", kind="llm") as sp:
        sp.set_input(prompt)
        text = mock_llm.complete([{"role": "user", "content": prompt}], MODEL)
        sp.set_output(text)
        sp.set_usage(MODEL, estimate_tokens(prompt), estimate_tokens(text))
        return text, sp.data["tokens_in"], sp.data["tokens_out"], sp.data["cost_usd"]


@aop.agent("qa-agent")
def _run(prompt):
    tools = []
    m = ARITH.search(prompt)
    if m:
        value = calculator(*m.groups())
        tools.append("calculator")
        return {"output": f"The answer is {value}.", "tools": tools}
    text, tin, tout, cost = _llm(prompt)
    return {"output": text, "tools": tools, "tokens_in": tin, "tokens_out": tout, "cost_usd": cost}


def run(prompt):
    return _run(prompt)
