import json

from aop.gateway import Gateway, GatewayConfig


def make_gateway(monkeypatch):
    api_keys = {
        "user-a-secret": "user-a",
        "user-b-secret": "user-b",
    }

    monkeypatch.setenv(
        "AOP_API_KEYS",
        json.dumps(api_keys),
    )

    monkeypatch.delenv(
        "AOP_API_KEY",
        raising=False,
    )

    config = GatewayConfig(
        provider="mock",
    )

    return Gateway(config)


def test_api_key_resolves_owner(monkeypatch):
    gw = make_gateway(monkeypatch)

    owner_id = gw._get_owner_id(
        {
            "Authorization": "Bearer user-a-secret",
        }
    )

    assert owner_id == "user-a"


def test_different_users_are_isolated(monkeypatch):
    gw = make_gateway(monkeypatch)

    gw.store.save(
        {
            "trace_id": "trace-a",
            "owner_id": "user-a",
            "model": "mock",
            "input_tokens": 1,
            "output_tokens": 1,
            "total_tokens": 2,
        }
    )

    gw.store.save(
        {
            "trace_id": "trace-b",
            "owner_id": "user-b",
            "model": "mock",
            "input_tokens": 1,
            "output_tokens": 1,
            "total_tokens": 2,
        }
    )

    assert gw.store.trace(
        "trace-a",
        "user-a",
    ) is not None

    assert gw.store.trace(
        "trace-b",
        "user-a",
    ) == []

    assert gw.store.trace(
        "trace-b",
        "user-b",
    ) is not None


def test_user_header_cannot_spoof_owner(monkeypatch):
    gw = make_gateway(monkeypatch)

    owner_id = gw._get_owner_id(
        {
            "Authorization": "Bearer user-a-secret",
            "X-AOP-User-ID": "user-b",
        }
    )

    assert owner_id == "user-a"


def test_wrong_api_key_is_rejected(monkeypatch):
    gw = make_gateway(monkeypatch)

    assert gw._check_api_key(
        "wrong-secret"
    ) is False

