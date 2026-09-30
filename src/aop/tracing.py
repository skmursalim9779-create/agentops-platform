"""Tracing: nested spans via contextvars, decorators for agents/tools/LLM calls."""

import contextvars
import functools
import inspect
import os
import time
import uuid
from contextlib import contextmanager

from .policies import redact
from .pricing import cost_usd, load_prices
from .store import SpanStore


_current = contextvars.ContextVar(
    "aop_current_span",
    default=None,
)

MAX_TEXT = 4000


def _clip(value):
    """
    Convert a value to text, redact PII, and limit its size
    before storing it in a trace.
    """
    if value is None:
        return None

    text = value if isinstance(value, str) else repr(value)

    # Remove sensitive information before trace persistence.
    text, _ = redact(text)

    if len(text) <= MAX_TEXT:
        return text

    return text[:MAX_TEXT] + "...[truncated]"


class Span:
    def __init__(
        self,
        tracer,
        name,
        kind,
        trace_id,
        parent_id,
        attrs,
    ):
        self.tracer = tracer

        self.data = {
            "span_id": uuid.uuid4().hex[:16],
            "trace_id": trace_id,
            "parent_id": parent_id,
            "name": name,
            "kind": kind,
            "start_ts": time.time(),
            "end_ts": None,
            "status": "ok",
            "model": None,
            "tokens_in": 0,
            "tokens_out": 0,
            "cost_usd": 0.0,
            "input": None,
            "output": None,
            "attrs": dict(attrs),
            "error": None,
        }

    @property
    def trace_id(self):
        return self.data["trace_id"]

    @property
    def span_id(self):
        return self.data["span_id"]

    def set(self, **attrs):
        self.data["attrs"].update(attrs)

    def set_input(self, value):
        self.data["input"] = _clip(value)

    def set_output(self, value):
        self.data["output"] = _clip(value)

    def set_usage(
        self,
        model,
        tokens_in,
        tokens_out,
        cost=None,
    ):
        self.data["model"] = model
        self.data["tokens_in"] = int(tokens_in)
        self.data["tokens_out"] = int(tokens_out)

        self.data["cost_usd"] = (
            cost
            if cost is not None
            else cost_usd(
                model,
                tokens_in,
                tokens_out,
                self.tracer.prices,
            )
        )


class Tracer:
    def __init__(self, store=None):
        self.store = store or SpanStore(
            os.environ.get(
                "AOP_DB",
                ".aop/traces.db",
            )
        )

        self.prices = load_prices()

    @contextmanager
    def span(
        self,
        name,
        kind="operation",
        trace_id=None,
        parent_id=None,
        **attrs,
    ):
        parent = _current.get()

        if parent is not None:
            trace_id = trace_id or parent.trace_id
            parent_id = parent_id or parent.span_id

        span = Span(
            self,
            name,
            kind,
            trace_id or uuid.uuid4().hex,
            parent_id,
            attrs,
        )

        token = _current.set(span)

        try:
            yield span

        except Exception as exc:
            span.data["status"] = "error"

            # Prevent sensitive data from entering stored error text.
            span.data["error"] = _clip(
                f"{type(exc).__name__}: {exc}"
            )

            raise

        finally:
            _current.reset(token)
            span.data["end_ts"] = time.time()
            self.store.save(span.data)

    def decorator(self, kind, name=None):
        def wrap(fn):
            label = name or fn.__name__

            if inspect.iscoroutinefunction(fn):

                @functools.wraps(fn)
                async def awrapper(*args, **kwargs):
                    with self.span(label, kind) as sp:
                        sp.set_input(
                            {
                                "args": args,
                                "kwargs": kwargs,
                            }
                        )

                        result = await fn(
                            *args,
                            **kwargs,
                        )

                        sp.set_output(result)

                        return result

                return awrapper

            @functools.wraps(fn)
            def wrapper(*args, **kwargs):
                with self.span(label, kind) as sp:
                    sp.set_input(
                        {
                            "args": args,
                            "kwargs": kwargs,
                        }
                    )

                    result = fn(
                        *args,
                        **kwargs,
                    )

                    sp.set_output(result)

                    return result

            return wrapper

        return wrap


_default = None


def init(db_path=None):
    global _default

    _default = Tracer(
        SpanStore(
            db_path
            or os.environ.get(
                "AOP_DB",
                ".aop/traces.db",
            )
        )
    )

    return _default


def get_tracer():
    global _default

    if _default is None:
        _default = Tracer()

    return _default