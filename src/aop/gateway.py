"""LLM gateway: OpenAI-compatible proxy that traces, prices and guards every call."""



import hmac



import json



import os



import time



import urllib.error



import urllib.request



import uuid



from dataclasses import dataclass



from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer



from . import mock_llm



from .dashboard import DASHBOARD_HTML



from .policies import LoopDetector, TokenBucket, redact



from .pricing import cost_usd, estimate_tokens, load_prices



from .store import SpanStore



@dataclass



class GatewayConfig:



    provider: str = "mock"



    upstream_url: str = (



        "https://api.openai.com/v1/chat/completions"



    )



    upstream_key_env: str = "AOP_UPSTREAM_API_KEY"



    api_key_env: str = "AOP_API_KEY"



    redact_pii: bool = True



    max_cost_per_session_usd: float = 1.0



    rate_limit_per_minute: int = 120



    loop_threshold: int = 5



    max_request_bytes: int = 1_048_576  # 1 MiB



    max_estimated_output_tokens: int = 1024



class Gateway:



    def __init__(self, config=None, store=None):



        self.config = config or GatewayConfig()



        self.store = store or SpanStore(



            os.environ.get(



                "AOP_DB",



                ".aop/traces.db",



            )



        )



        self.prices = load_prices()



        self.bucket = TokenBucket(



            self.config.rate_limit_per_minute



        )



        self.loops = LoopDetector(



            self.config.loop_threshold



        )



        # -- authentication -----------------------------------------------



    def _check_api_key(self, provided_key):

        configured_key = os.environ.get(

            self.config.api_key_env,

            "",

        )



        # Keep the anonymous public demo available only for mock.

        if not configured_key:

            return self.config.provider == "mock"



        if not provided_key:

            return False



        return hmac.compare_digest(

            provided_key,

            configured_key,

        )



    # -- provider -----------------------------------------------------



    def _call_provider(self, body):



        if self.config.provider == "mock":



            text = mock_llm.complete(



                body["messages"],



                body.get(



                    "model",



                    "mock-1",



                ),



            )



            return {



                "text": text,



                "usage": None,



            }



        key = os.environ.get(



            self.config.upstream_key_env,



            "",



        )



        req = urllib.request.Request(



            self.config.upstream_url,



            data=json.dumps(



                {



                    **body,



                    "stream": False,



                }



            ).encode(),



            headers={



                "Content-Type": "application/json",



                "Authorization": f"Bearer {key}",



            },



        )



        with urllib.request.urlopen(



            req,



            timeout=60,



        ) as resp:



            data = json.loads(



                resp.read()



            )



        return {



            "text": data["choices"][0]["message"]["content"],



            "usage": data.get("usage"),



        }



    # -- request validation -------------------------------------------



    def _validate_chat_body(self, body):



        """Validate the minimal chat completion request contract."""



        if not isinstance(body, dict):



            return (



                400,



                {



                    "error": {



                        "type": "invalid_request",



                        "message": (



                            "request body must be a JSON object"



                        ),



                    }



                },



                {},



            )



        messages = body.get("messages")



        if not isinstance(



            messages,



            list,



        ) or not messages:



            return (



                400,



                {



                    "error": {



                        "type": "invalid_request",



                        "message": (



                            "messages must be a non-empty list"



                        ),



                    }



                },



                {},



            )



        for index, message in enumerate(messages):



            if not isinstance(



                message,



                dict,



            ):



                return (



                    400,



                    {



                        "error": {



                            "type": "invalid_request",



                            "message": (



                                f"messages[{index}] "



                                "must be an object"



                            ),



                        }



                    },



                    {},



                )



            role = message.get("role")



            if role not in {



                "system",



                "user",



                "assistant",



                "tool",



            }:



                return (



                    400,



                    {



                        "error": {



                            "type": "invalid_request",



                            "message": (



                                f"messages[{index}].role "



                                "is invalid"



                            ),



                        }



                    },



                    {},



                )



            content = message.get(



                "content"



            )



            if not isinstance(



                content,



                str,



            ):



                return (



                    400,



                    {



                        "error": {



                            "type": "invalid_request",



                            "message": (



                                f"messages[{index}].content "



                                "must be a string"



                            ),



                        }



                    },



                    {},



                )



        model = body.get(



            "model",



            "mock-1",



        )



        if not isinstance(



            model,



            str,



        ) or not model.strip():



            return (



                400,



                {



                    "error": {



                        "type": "invalid_request",



                        "message": (



                            "model must be a non-empty string"



                        ),



                    }



                },



                {},



            )



        return None



    # -- budget estimation --------------------------------------------



    def _estimate_request_cost(



        self,



        model,



        messages,



    ):



        """Estimate the maximum cost of the next request."""



        input_tokens = sum(



            estimate_tokens(



                str(



                    message.get(



                        "content",



                        "",



                    )



                )



            )



            for message in messages



        )



        output_tokens = (



            self.config.max_estimated_output_tokens



        )



        return cost_usd(



            model,



            input_tokens,



            output_tokens,



            self.prices,



        )



    # -- main entry ---------------------------------------------------



    def chat(



        self,



        body,



        headers,



        client,



    ):



        """Returns (status, payload, extra_headers)."""



        # API authentication



        if not self._check_api_key(



            headers.get("x-aop-key")



        ):



            return (



                401,



                {



                    "error": {



                        "type": "authentication_error",



                        "message": (



                            "invalid or missing API key"



                        ),



                    }



                },



                {



                    "WWW-Authenticate": "ApiKey",



                },



            )



        # Request validation



        validation_error = self._validate_chat_body(



            body



        )



        if validation_error is not None:



            return validation_error



        messages = body["messages"]



        model = body.get(



            "model",



            "mock-1",



        )



        trace_id = (



            headers.get("x-aop-session")



            or uuid.uuid4().hex



        )



        agent = headers.get(



            "x-aop-agent",



            "unknown",



        )

        owner_id = headers.get("x-aop-key") or "public"



        key = (



            headers.get("x-aop-key")



            or client



        )



        # Rate limiting



        if not self.bucket.allow(key):



            return (



                429,



                {



                    "error": {



                        "type": "rate_limited",



                        "message": "slow down",



                    }



                },



                {



                    "Retry-After": "1",



                },



            )



        # Strict session budget check

        owner_id = headers.get("x-aop-key") or "public"



        spent = self.store.trace_cost(



            trace_id,

            owner_id,



        )



        estimated_cost = self._estimate_request_cost(



            model,



            messages,



        )



        if (



            spent >= self.config.max_cost_per_session_usd



            or



            spent + estimated_cost



            > self.config.max_cost_per_session_usd



        ):



            return (



                402,



                {



                    "error": {



                        "type": "budget_exceeded",



                        "message": (



                            "estimated request cost would "



                            "exceed the session budget"



                        ),



                    }



                },



                {},



            )



        # PII redaction



        redactions = 0



        if self.config.redact_pii:



            cleaned = []



            for message in messages:



                content = message.get(



                    "content"



                )



                content, count = redact(



                    content



                )



                redactions += count



                cleaned.append(



                    {



                        **message,



                        "content": content,



                    }



                )



            messages = cleaned



        body = {



            **body,



            "messages": messages,



        }



        # Find latest user message



        last_user = next(



            (



                message["content"]



                for message in reversed(messages)



                if message.get("role") == "user"



            ),



            "",



        )



        # Loop detection



        if self.loops.hit(



            trace_id,



            last_user,



        ):



            return (



                429,



                {



                    "error": {



                        "type": "loop_detected",



                        "message": (



                            "identical prompt repeated; "



                            "agent may be looping"



                        ),



                    }



                },



                {},



            )



        # Create trace span



        span = {



            "span_id": uuid.uuid4().hex[:16],



            "trace_id": trace_id,

            "owner_id": headers.get("x-aop-key") or "public",



            "parent_id": headers.get(



                "x-aop-parent"



            ),



            "name": f"llm:{model}",



            "kind": "llm",



            "start_ts": time.time(),



            "model": model,



            "input": last_user[:4000],



            "attrs": {



                "agent": agent,



                "redactions": redactions,



                "provider": self.config.provider,



                "estimated_cost_usd": estimated_cost,



            },



            "status": "ok",



            "tokens_in": 0,



            "tokens_out": 0,



            "cost_usd": 0.0,



        }



        # Provider call



        try:



            result = self._call_provider(



                body



            )



        except (



            urllib.error.URLError,



            KeyError,



            ValueError,



            TimeoutError,



        ) as exc:



            span.update(



                end_ts=time.time(),



                status="error",



                error=(



                    f"{type(exc).__name__}: {exc}"



                ),



            )



            self.store.save(span)



            return (



                502,



                {



                    "error": {



                        "type": "upstream_error",



                        "message": str(exc),



                    }



                },



                {},



            )



        # Usage and cost calculation



        text = result["text"]



        usage = result["usage"]



        tin = (



            (usage or {}).get(



                "prompt_tokens"



            )



            or sum(



                estimate_tokens(



                    str(



                        message.get(



                            "content"



                        )



                    )



                )



                for message in messages



            )



        )



        tout = (



            (usage or {}).get(



                "completion_tokens"



            )



            or estimate_tokens(text)



        )



        cost = cost_usd(



            model,



            tin,



            tout,



            self.prices,



        )



        # Save successful span



        span.update(



            end_ts=time.time(),



            output=text[:4000],



            tokens_in=tin,



            tokens_out=tout,



            cost_usd=cost,



        )



        self.store.save(span)



        # OpenAI-compatible response



        payload = {



            "id": (



                f"chatcmpl-{span['span_id']}"



            ),



            "object": "chat.completion",



            "created": int(time.time()),



            "model": model,



            "choices": [



                {



                    "index": 0,



                    "finish_reason": "stop",



                    "message": {



                        "role": "assistant",



                        "content": text,



                    },



                }



            ],



            "usage": {



                "prompt_tokens": tin,



                "completion_tokens": tout,



                "total_tokens": (



                    tin + tout



                ),



            },



        }



        return (



            200,



            payload,



            {



                "x-aop-trace-id": trace_id,



                "x-aop-cost-usd": (



                    f"{cost:.8f}"



                ),



            },



        )



def make_server(



    host="127.0.0.1",



    port=8787,



    gateway=None,



):



    gw = gateway or Gateway()



    class Handler(BaseHTTPRequestHandler):



        def log_message(self, *args):



            pass



        def _send(



            self,



            status,



            payload,



            extra=None,



            ctype="application/json",



        ):



            raw = (



                payload.encode()



                if isinstance(payload, str)



                else json.dumps(



                    payload,



                    default=str,



                ).encode()



            )



            self.send_response(status)



            self.send_header(



                "Content-Type",



                ctype,



            )



            self.send_header(



                "Content-Length",



                str(len(raw)),



            )



            self.send_header("X-Content-Type-Options", "nosniff")

            self.send_header("X-Frame-Options", "DENY")

            self.send_header("Referrer-Policy", "no-referrer")

            self.send_header(

                "Permissions-Policy",

                "camera=(), microphone=(), geolocation=()",

            )

            self.send_header("Cache-Control", "no-store")



            for key, value in (



                extra or {}



            ).items():



                self.send_header(



                    key,



                    value,



                )



            self.end_headers()



            self.wfile.write(raw)



        def _authorized(self):



            headers = {



                key.lower(): value



                for key, value



                in self.headers.items()



            }



            return gw._check_api_key(



                headers.get("x-aop-key")



            )



        def do_GET(self):



            path = self.path.split("?")[0]



            # Protect API endpoints.



            if (



                path.startswith("/api/")



                and not self._authorized()



            ):



                return self._send(



                    401,



                    {



                        "error": {



                            "type": "authentication_error",



                            "message": (



                                "invalid or missing API key"



                            ),



                        }



                    },



                    {



                        "WWW-Authenticate": "ApiKey",



                    },



                )



            if path == "/health":



                self._send(



                    200,



                    {"status": "ok"},



                )



            elif path == "/":



                self._send(



                    200,



                    DASHBOARD_HTML,



                    ctype=(



                        "text/html; "



                        "charset=utf-8"



                    ),



                )



            elif path == "/api/stats":

                headers = {

                    key.lower(): value

                    for key, value in self.headers.items()

                }



                owner_id = headers.get("x-aop-key") or "public"



                self._send(

                    200,

                    gw.store.stats(owner_id),

                )



            elif path == "/api/traces":

                headers = {

                    key.lower(): value

                    for key, value in self.headers.items()

                }



                owner_id = headers.get("x-aop-key") or "public"



                self._send(

                    200,

                    gw.store.traces(owner_id=owner_id),

                )



            elif path.startswith(

                "/api/traces/"

            ):

                headers = {

                    key.lower(): value

                    for key, value in self.headers.items()

                }

                owner_id = headers.get("x-aop-key") or "public"

                spans = gw.store.trace(

                    path.rsplit(

                        "/",

                        1,

                    )[1],

                    owner_id,

                )

                self._send(

                    200 if spans else 404,

                    spans

                    or {

                        "error": "not found"

                    },

                )

            else:



                self._send(



                    404,



                    {"error": "not found"},



                )



        def do_POST(self):



            if (



                self.path.split("?")[0]



                != "/v1/chat/completions"



            ):



                return self._send(



                    404,



                    {"error": "not found"},



                )



            raw_length = self.headers.get(



                "Content-Length"



            )



            if raw_length is None:



                return self._send(



                    400,



                    {



                        "error": {



                            "type": "invalid_request",



                            "message": (



                                "Content-Length "



                                "header required"



                            ),



                        }



                    },



                )



            try:



                length = int(



                    raw_length



                )



            except (



                TypeError,



                ValueError,



            ):



                return self._send(



                    400,



                    {



                        "error": {



                            "type": "invalid_request",



                            "message": (



                                "invalid Content-Length"



                            ),



                        }



                    },



                )



            if length <= 0:



                return self._send(



                    400,



                    {



                        "error": {



                            "type": "invalid_request",



                            "message": (



                                "request body required"



                            ),



                        }



                    },



                )



            if (



                length



                > gw.config.max_request_bytes



            ):



                return self._send(



                    413,



                    {



                        "error": {



                            "type": "request_too_large",



                            "message": (



                                "request body exceeds "



                                f"{gw.config.max_request_bytes} "



                                "bytes"



                            ),



                        }



                    },



                )



            raw = self.rfile.read(



                length



            )



            if len(raw) != length:



                return self._send(



                    400,



                    {



                        "error": {



                            "type": "invalid_request",



                            "message": (



                                "incomplete request body"



                            ),



                        }



                    },



                )



            try:



                body = json.loads(



                    raw



                )



            except (



                json.JSONDecodeError,



                UnicodeDecodeError,



            ):



                return self._send(



                    400,



                    {



                        "error": {



                            "type": "invalid_json",



                            "message": (



                                "request body must contain "



                                "valid JSON"



                            ),



                        }



                    },



                )



            headers = {



                key.lower(): value



                for key, value



                in self.headers.items()



            }



            status, payload, extra = gw.chat(



                body,



                headers,



                self.client_address[0],



            )



            self._send(



                status,



                payload,



                extra,



            )



    server = ThreadingHTTPServer(



        (host, port),



        Handler,



    )



    server.gateway = gw



    return server
