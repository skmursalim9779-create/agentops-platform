"""AgentOps Platform: gateway, tracing, cost tracking and evals for AI agents."""
from .tracing import Tracer, get_tracer, init

__version__ = "0.1.0"


def agent(name=None):
    return get_tracer().decorator("agent", name)


def tool(name=None):
    return get_tracer().decorator("tool", name)


def operation(name=None):
    return get_tracer().decorator("operation", name)


def llm(name=None):
    return get_tracer().decorator("llm", name)


__all__ = ["Tracer", "get_tracer", "init", "agent", "tool", "operation", "llm", "__version__"]
