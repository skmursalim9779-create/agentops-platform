"""Deterministic offline model so the whole platform runs without API keys."""
import re

CAPITALS = {"france": "Paris", "japan": "Tokyo", "bangladesh": "Dhaka", "india": "New Delhi",
            "germany": "Berlin", "italy": "Rome", "canada": "Ottawa", "egypt": "Cairo"}
ARITH = re.compile(r"(-?\d+(?:\.\d+)?)\s*([+\-*/x×])\s*(-?\d+(?:\.\d+)?)")
INJECTION = ("ignore previous instructions", "ignore all previous", "reveal your system prompt")


def calc(a, op, b):
    a, b = float(a), float(b)
    val = {"+": a + b, "-": a - b, "*": a * b, "x": a * b, "×": a * b}.get(op)
    if op == "/":
        val = a / b if b else float("nan")
    return int(val) if val == int(val) else round(val, 4)


def complete(messages, model="mock-1"):
    user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
    low = user.lower()
    if any(p in low for p in INJECTION):
        return "I can't help with that request."
    m = ARITH.search(user)
    if m:
        return f"The answer is {calc(*m.groups())}."
    m = re.search(r"capital of ([a-z ]+)", low)
    if m:
        city = CAPITALS.get(m.group(1).strip(" ?.!"))
        if city:
            return f"The capital is {city}."
    if low.startswith("summarize"):
        return "Summary: " + user[9:].strip(" :")[:80]
    return "I'm a mock model. You said: " + user[:120]
