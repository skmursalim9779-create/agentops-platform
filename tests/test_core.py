import json
import os
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from aop.evals.runner import compare, evaluate_gate, load_dataset, run_eval
from aop.gateway import Gateway, GatewayConfig, make_server
from aop.policies import LoopDetector, TokenBucket, contains_pii, redact
from aop.pricing import cost_usd
from aop.store import SpanStore
from aop.tracing import Tracer


ROOT = Path(__file__).resolve().parent.parent


class TracingTests(unittest.TestCase):
    def test_nested_spans_and_cost(self):
        store = SpanStore(":memory:")
        tr = Tracer(store)

        @tr.decorator("tool", "add")
        def add(a, b):
            return a + b

        with tr.span("root", "agent") as root:
            add(1, 2)

            with tr.span("llm", "llm") as sp:
                sp.set_usage(
                    "gpt-4o-mini",
                    1000,
                    500,
                )

        spans = store.trace(root.trace_id)

        self.assertEqual(
            len(spans),
            3,
        )

        by_name = {
            s["name"]: s
            for s in spans
        }

        self.assertEqual(
            by_name["add"]["parent_id"],
            root.span_id,
        )

        self.assertAlmostEqual(
            by_name["llm"]["cost_usd"],
            (1000 * 0.15 + 500 * 0.60) / 1e6,
        )

    def test_trace_redacts_pii(self):
        store = SpanStore(":memory:")
        tr = Tracer(store)

        with tr.span("privacy-test") as sp:
            sp.set_input(
                "Contact test@example.com or 9000000000"
            )

            sp.set_output(
                "Email=test@example.com Phone=9000000000"
            )

        spans = store.trace(
            sp.trace_id
        )

        self.assertEqual(
            len(spans),
            1,
        )

        saved = spans[0]

        self.assertNotIn(
            "test@example.com",
            saved["input"],
        )

        self.assertNotIn(
            "9000000000",
            saved["input"],
        )

        self.assertNotIn(
            "test@example.com",
            saved["output"],
        )

        self.assertNotIn(
            "9000000000",
            saved["output"],
        )

        self.assertIn(
            "[REDACTED_EMAIL]",
            saved["input"],
        )

        self.assertIn(
            "[REDACTED_PHONE]",
            saved["input"],
        )

    def test_error_is_recorded(self):
        store = SpanStore(":memory:")
        tr = Tracer(store)

        with self.assertRaises(ValueError):
            with tr.span("boom") as sp:
                raise ValueError("bad")

        self.assertEqual(
            store.trace(
                sp.trace_id
            )[0]["status"],
            "error",
        )


class PricingPolicyTests(unittest.TestCase):
    def test_longest_prefix_wins(self):
        self.assertLess(
            cost_usd(
                "gpt-4o-mini-2024",
                1000,
                1000,
            ),
            cost_usd(
                "gpt-4o",
                1000,
                1000,
            ),
        )

        self.assertEqual(
            cost_usd(
                "unknown",
                10,
                10,
            ),
            0.0,
        )

    def test_redact(self):
        text, n = redact(
            "mail bob@example.com card 4111 1111 1111 1111"
        )

        self.assertEqual(
            n,
            2,
        )

        self.assertNotIn(
            "bob@example.com",
            text,
        )

    def test_phone_pii_detection(self):
        # Synthetic test value; not a real person's phone number.
        synthetic_phone = "9000000000"

        self.assertTrue(
            contains_pii(
                f"Call me at {synthetic_phone}"
            )
        )

    def test_bucket_and_loop(self):
        bucket = TokenBucket(
            per_minute=60,
            capacity=2,
        )

        self.assertTrue(
            bucket.allow("k")
        )

        self.assertTrue(
            bucket.allow("k")
        )

        self.assertFalse(
            bucket.allow("k")
        )

        detector = LoopDetector(
            threshold=3
        )

        self.assertFalse(
            detector.hit(
                "s",
                "x",
            )
        )

        self.assertFalse(
            detector.hit(
                "s",
                "x",
            )
        )

        self.assertTrue(
            detector.hit(
                "s",
                "x",
            )
        )


class GatewayTests(unittest.TestCase):
    def setUp(self):
        self.gw = Gateway(
            GatewayConfig(
                max_cost_per_session_usd=1.0,
                loop_threshold=3,
            ),
            SpanStore(":memory:"),
        )

        self.server = make_server(
            "127.0.0.1",
            0,
            self.gw,
        )

        self.url = (
            f"http://127.0.0.1:"
            f"{self.server.server_address[1]}"
        )

        self.thread = threading.Thread(
            target=self.server.serve_forever,
            daemon=True,
        )

        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(
            timeout=2
        )

    def _post(
        self,
        content,
        session="s1",
        api_key=None,
        model="mock-1",
    ):
        body = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": content,
                }
            ],
        }

        headers = {
            "Content-Type": "application/json",
            "x-aop-session": session,
        }

        if api_key is not None:
            headers["x-aop-key"] = api_key

        req = urllib.request.Request(
            self.url
            + "/v1/chat/completions",
            data=json.dumps(body).encode(),
            headers=headers,
        )

        return urllib.request.urlopen(
            req
        )

    def test_completion_traced_and_redacted(self):
        resp = self._post(
            "Summarize: mail me at a@b.com"
        )

        data = json.loads(
            resp.read()
        )

        self.assertIn(
            "REDACTED_EMAIL",
            data["choices"][0]["message"]["content"],
        )

        self.assertEqual(
            resp.headers["x-aop-trace-id"],
            "s1",
        )

        self.assertEqual(
            len(
                self.gw.store.trace("s1")
            ),
            1,
        )

        stats = json.loads(
            urllib.request.urlopen(
                self.url
                + "/api/stats"
            ).read()
        )

        self.assertEqual(
            stats["totals"]["spans"],
            1,
        )

    def test_loop_detection(self):
        self._post("same")
        self._post("same")

        with self.assertRaises(
            urllib.error.HTTPError
        ) as ctx:
            self._post("same")

        self.assertEqual(
            ctx.exception.code,
            429,
        )

    def test_budget(self):
        self.gw.config.max_cost_per_session_usd = 0.0

        with self.assertRaises(
            urllib.error.HTTPError
        ) as ctx:
            self._post(
                "hi",
                session="broke",
            )

        self.assertEqual(
            ctx.exception.code,
            402,
        )

    def test_strict_estimated_budget_blocks_expensive_request(self):
        self.gw.config.max_cost_per_session_usd = 0.0001

        with self.assertRaises(
            urllib.error.HTTPError
        ) as ctx:
            self._post(
                "hello",
                session="strict-budget",
                model="gpt-4o",
            )

        self.assertEqual(
            ctx.exception.code,
            402,
        )

        self.assertEqual(
            len(
                self.gw.store.trace("strict-budget")
            ),
            0,
        )

    def test_dashboard_served(self):
        self.assertIn(
            b"AgentOps Platform",
            urllib.request.urlopen(
                self.url + "/"
            ).read(),
        )

    def test_auth_missing_key_rejected(self):
        old_key = os.environ.get(
            "AOP_API_KEY"
        )

        os.environ["AOP_API_KEY"] = (
            "test-agentops-key"
        )

        try:
            body = {
                "model": "mock-1",
                "messages": [
                    {
                        "role": "user",
                        "content": "hello",
                    }
                ],
            }

            raw = json.dumps(
                body
            ).encode()

            req = urllib.request.Request(
                self.url
                + "/v1/chat/completions",
                data=raw,
                headers={
                    "Content-Type": (
                        "application/json"
                    ),
                },
            )

            with self.assertRaises(
                urllib.error.HTTPError
            ) as ctx:
                urllib.request.urlopen(
                    req
                )

            self.assertEqual(
                ctx.exception.code,
                401,
            )

        finally:
            if old_key is None:
                os.environ.pop(
                    "AOP_API_KEY",
                    None,
                )
            else:
                os.environ["AOP_API_KEY"] = old_key

    def test_auth_wrong_key_rejected(self):
        old_key = os.environ.get(
            "AOP_API_KEY"
        )

        os.environ["AOP_API_KEY"] = (
            "test-agentops-key"
        )

        try:
            body = {
                "model": "mock-1",
                "messages": [
                    {
                        "role": "user",
                        "content": "hello",
                    }
                ],
            }

            raw = json.dumps(
                body
            ).encode()

            req = urllib.request.Request(
                self.url
                + "/v1/chat/completions",
                data=raw,
                headers={
                    "Content-Type": (
                        "application/json"
                    ),
                    "x-aop-key": "wrong-key",
                },
            )

            with self.assertRaises(
                urllib.error.HTTPError
            ) as ctx:
                urllib.request.urlopen(
                    req
                )

            self.assertEqual(
                ctx.exception.code,
                401,
            )

        finally:
            if old_key is None:
                os.environ.pop(
                    "AOP_API_KEY",
                    None,
                )
            else:
                os.environ["AOP_API_KEY"] = old_key

    def test_auth_correct_key_allowed(self):
        old_key = os.environ.get(
            "AOP_API_KEY"
        )

        os.environ["AOP_API_KEY"] = (
            "test-agentops-key"
        )

        try:
            body = {
                "model": "mock-1",
                "messages": [
                    {
                        "role": "user",
                        "content": "hello",
                    }
                ],
            }

            raw = json.dumps(
                body
            ).encode()

            req = urllib.request.Request(
                self.url
                + "/v1/chat/completions",
                data=raw,
                headers={
                    "Content-Type": (
                        "application/json"
                    ),
                    "x-aop-key": (
                        "test-agentops-key"
                    ),
                },
            )

            response = urllib.request.urlopen(
                req
            )

            self.assertEqual(
                response.status,
                200,
            )

        finally:
            if old_key is None:
                os.environ.pop(
                    "AOP_API_KEY",
                    None,
                )
            else:
                os.environ["AOP_API_KEY"] = old_key

    def test_stats_api_requires_key(self):
        old_key = os.environ.get(
            "AOP_API_KEY"
        )

        os.environ["AOP_API_KEY"] = (
            "test-agentops-key"
        )

        try:
            req = urllib.request.Request(
                self.url + "/api/stats"
            )

            with self.assertRaises(
                urllib.error.HTTPError
            ) as ctx:
                urllib.request.urlopen(
                    req
                )

            self.assertEqual(
                ctx.exception.code,
                401,
            )

            req = urllib.request.Request(
                self.url + "/api/stats",
                headers={
                    "x-aop-key": (
                        "test-agentops-key"
                    ),
                },
            )

            response = urllib.request.urlopen(
                req
            )

            self.assertEqual(
                response.status,
                200,
            )

        finally:
            if old_key is None:
                os.environ.pop(
                    "AOP_API_KEY",
                    None,
                )
            else:
                os.environ["AOP_API_KEY"] = old_key

    def test_traces_api_requires_key(self):
        old_key = os.environ.get(
            "AOP_API_KEY"
        )

        os.environ["AOP_API_KEY"] = (
            "test-agentops-key"
        )

        try:
            trace_session = "trace-auth-test"

            self._post(
                "hello",
                session=trace_session,
                api_key="test-agentops-key",
            )

            # No API key -> 401
            req = urllib.request.Request(
                self.url + "/api/traces"
            )

            with self.assertRaises(
                urllib.error.HTTPError
            ) as ctx:
                urllib.request.urlopen(
                    req
                )

            self.assertEqual(
                ctx.exception.code,
                401,
            )

            # Correct API key -> 200
            req = urllib.request.Request(
                self.url + "/api/traces",
                headers={
                    "x-aop-key": (
                        "test-agentops-key"
                    ),
                },
            )

            response = urllib.request.urlopen(
                req
            )

            self.assertEqual(
                response.status,
                200,
            )

        finally:
            if old_key is None:
                os.environ.pop(
                    "AOP_API_KEY",
                    None,
                )
            else:
                os.environ["AOP_API_KEY"] = old_key

    def test_trace_detail_requires_key(self):
        old_key = os.environ.get(
            "AOP_API_KEY"
        )

        os.environ["AOP_API_KEY"] = (
            "test-agentops-key"
        )

        try:
            trace_session = "trace-detail-auth"

            response = self._post(
                "hello",
                session=trace_session,
                api_key="test-agentops-key",
            )

            self.assertEqual(
                response.status,
                200,
            )

            # No API key -> 401
            req = urllib.request.Request(
                self.url
                + f"/api/traces/{trace_session}"
            )

            with self.assertRaises(
                urllib.error.HTTPError
            ) as ctx:
                urllib.request.urlopen(
                    req
                )

            self.assertEqual(
                ctx.exception.code,
                401,
            )

            # Correct API key -> 200
            req = urllib.request.Request(
                self.url
                + f"/api/traces/{trace_session}",
                headers={
                    "x-aop-key": (
                        "test-agentops-key"
                    ),
                },
            )

            response = urllib.request.urlopen(
                req
            )

            self.assertEqual(
                response.status,
                200,
            )

        finally:
            if old_key is None:
                os.environ.pop(
                    "AOP_API_KEY",
                    None,
                )
            else:
                os.environ["AOP_API_KEY"] = old_key

    def test_invalid_json_rejected(self):
        raw = b'{"model":'

        req = urllib.request.Request(
            self.url
            + "/v1/chat/completions",
            data=raw,
            headers={
                "Content-Type": (
                    "application/json"
                ),
                "Content-Length": str(
                    len(raw)
                ),
            },
        )

        with self.assertRaises(
            urllib.error.HTTPError
        ) as ctx:
            urllib.request.urlopen(
                req
            )

        self.assertEqual(
            ctx.exception.code,
            400,
        )

    def test_non_object_json_rejected(self):
        raw = b"[]"

        req = urllib.request.Request(
            self.url
            + "/v1/chat/completions",
            data=raw,
            headers={
                "Content-Type": (
                    "application/json"
                ),
                "Content-Length": str(
                    len(raw)
                ),
            },
        )

        with self.assertRaises(
            urllib.error.HTTPError
        ) as ctx:
            urllib.request.urlopen(
                req
            )

        self.assertEqual(
            ctx.exception.code,
            400,
        )

    def test_invalid_messages_rejected(self):
        raw = json.dumps(
            {
                "model": "mock-1",
                "messages": {},
            }
        ).encode()

        req = urllib.request.Request(
            self.url
            + "/v1/chat/completions",
            data=raw,
            headers={
                "Content-Type": (
                    "application/json"
                ),
                "Content-Length": str(
                    len(raw)
                ),
            },
        )

        with self.assertRaises(
            urllib.error.HTTPError
        ) as ctx:
            urllib.request.urlopen(
                req
            )

        self.assertEqual(
            ctx.exception.code,
            400,
        )

    def test_oversized_request_rejected(self):
        self.gw.config.max_request_bytes = 64

        raw = json.dumps(
            {
                "model": "mock-1",
                "messages": [
                    {
                        "role": "user",
                        "content": "x" * 100,
                    }
                ],
            }
        ).encode()

        req = urllib.request.Request(
            self.url
            + "/v1/chat/completions",
            data=raw,
            headers={
                "Content-Type": (
                    "application/json"
                ),
                "Content-Length": str(
                    len(raw)
                ),
            },
        )

        with self.assertRaises(
            urllib.error.HTTPError
        ) as ctx:
            urllib.request.urlopen(
                req
            )

        self.assertEqual(
            ctx.exception.code,
            413,
        )
    def test_rate_limit_rejects_excess_requests(self):
        gateway = Gateway(
            GatewayConfig(
                rate_limit_per_minute=1,
                loop_threshold=99,
            ),
            SpanStore(":memory:"),
        )

        server = make_server(
            "127.0.0.1",
            0,
            gateway,
        )

        thread = threading.Thread(
            target=server.serve_forever,
            daemon=True,
        )
        thread.start()

        try:
            url = (
                f"http://127.0.0.1:"
                f"{server.server_address[1]}"
            )

            def post_request():
                body = {
                    "model": "mock-1",
                    "messages": [
                        {
                            "role": "user",
                            "content": "rate-limit-test",
                        }
                    ],
                }

                raw = json.dumps(body).encode()

                req = urllib.request.Request(
                    url + "/v1/chat/completions",
                    data=raw,
                    headers={
                        "Content-Type": "application/json",
                    },
                )

                return urllib.request.urlopen(req)

            first = post_request()
            self.assertEqual(first.status, 200)

            with self.assertRaises(
                urllib.error.HTTPError
            ) as ctx:
                post_request()

            self.assertEqual(
                ctx.exception.code,
                429,
            )

        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)


    def test_health_endpoint_is_available(self):
        response = urllib.request.urlopen(
            self.url + "/health"
        )

        self.assertEqual(
            response.status,
            200,
        )

        data = json.loads(
            response.read()
        )

        self.assertEqual(
            data["status"],
            "ok",
        )


    def test_public_dashboard_does_not_require_api_key(self):
        response = urllib.request.urlopen(
            self.url + "/"
        )

        self.assertEqual(
            response.status,
            200,
        )

        body = response.read()

        self.assertIn(
            b"AgentOps",
            body,
        )

class EvalTests(unittest.TestCase):
    def _config(self, **over):
        cfg = {
            "target": {
                "type": "python",
                "function": (
                    "examples.demo_agent:run"
                ),
            },
            "dataset": (
                "datasets/smoke.jsonl"
            ),
            "evaluators": [
                {
                    "type": "contains"
                },
                {
                    "type": "tool_calls"
                },
                {
                    "type": "safety_refusal"
                },
                {
                    "type": "no_pii"
                },
            ],
            "thresholds": {
                "min_pass_rate": 0.9
            },
        }

        cfg.update(over)

        return cfg

    def setUp(self):
        import aop

        self.tmp = tempfile.mkdtemp()

        aop.init(
            str(
                Path(self.tmp)
                / "t.db"
            )
        )

    def test_smoke_suite_passes_gate(self):
        res = run_eval(
            self._config(),
            base_dir=ROOT,
        )

        self.assertEqual(
            res["summary"]["total"],
            6,
        )

        self.assertTrue(
            res["gate"]["passed"],
            res["gate"],
        )

    def test_regression_detected_against_baseline(self):
        base = run_eval(
            self._config(),
            base_dir=ROOT,
        )

        worse = json.loads(
            json.dumps(base)
        )

        for case in worse["cases"][:3]:
            case["passed"] = False
            case["checks"]["contains"][
                "passed"
            ] = False

        worse["summary"][
            "pass_rate"
        ] = 0.5

        worse["summary"][
            "by_evaluator"
        ]["contains"] = 0.5

        comparison = compare(
            worse,
            base,
            0.05,
        )

        self.assertIn(
            "pass_rate",
            comparison["regressions"],
        )

        self.assertEqual(
            len(
                comparison[
                    "regressed_cases"
                ]
            ),
            3,
        )

        self.assertFalse(
            evaluate_gate(
                worse["summary"],
                comparison,
                {
                    "min_pass_rate": 0.9
                },
            )["passed"]
        )

    def test_crashing_target_fails_case_not_run(self):
        # A target that raises must become a failed case.
        import examples.demo_agent as da

        original_run = da.run

        da.run = (
            lambda p: (
                _ for _ in ()
            ).throw(
                RuntimeError("boom")
            )
        )

        try:
            res = run_eval(
                self._config(),
                base_dir=ROOT,
            )
        finally:
            da.run = original_run

        self.assertEqual(
            res["summary"]["passed"],
            0,
        )

        self.assertTrue(
            all(
                case["error"]
                for case in res["cases"]
            )
        )

    def test_dataset_validation(self):
        bad = (
            Path(self.tmp)
            / "bad.jsonl"
        )

        bad.write_text(
            '{"no_input": 1}\n',
            encoding="utf-8",
        )

        with self.assertRaises(
            ValueError
        ):
            load_dataset(bad)


if __name__ == "__main__":
    unittest.main()