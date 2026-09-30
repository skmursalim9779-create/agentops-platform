"""SQLite span store. One table, thread-safe, no external dependencies."""
import json
import sqlite3
import threading
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS spans (
  span_id TEXT PRIMARY KEY, trace_id TEXT NOT NULL, parent_id TEXT,
  name TEXT, kind TEXT, start_ts REAL, end_ts REAL, status TEXT DEFAULT 'ok',
  model TEXT, tokens_in INTEGER DEFAULT 0, tokens_out INTEGER DEFAULT 0,
  cost_usd REAL DEFAULT 0, input TEXT, output TEXT, attrs TEXT, error TEXT
);
CREATE INDEX IF NOT EXISTS idx_spans_trace ON spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_spans_start ON spans(start_ts);
"""

COLUMNS = ["span_id", "trace_id", "parent_id", "name", "kind", "start_ts", "end_ts", "status",
           "model", "tokens_in", "tokens_out", "cost_usd", "input", "output", "attrs", "error"]


class SpanStore:
    def __init__(self, path=".aop/traces.db"):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.executescript(SCHEMA)

    def save(self, span):
        row = dict(span)
        row["attrs"] = json.dumps(row.get("attrs") or {}, default=str)
        values = [row.get(c) for c in COLUMNS]
        with self._lock:
            self._conn.execute(
                f"INSERT OR REPLACE INTO spans ({','.join(COLUMNS)}) VALUES ({','.join('?' * len(COLUMNS))})",
                values,
            )
            self._conn.commit()

    def _rows(self, sql, args=()):
        with self._lock:
            return [dict(r) for r in self._conn.execute(sql, args).fetchall()]

    def traces(self, limit=50):
        return self._rows(
            """SELECT trace_id, MIN(start_ts) AS start_ts, MAX(end_ts) AS end_ts,
                      COUNT(*) AS spans, SUM(tokens_in) AS tokens_in, SUM(tokens_out) AS tokens_out,
                      SUM(cost_usd) AS cost_usd, SUM(status='error') AS errors,
                      MAX(CASE WHEN parent_id IS NULL THEN name END) AS root
               FROM spans GROUP BY trace_id ORDER BY MIN(start_ts) DESC LIMIT ?""",
            (limit,),
        )

    def trace(self, trace_id):
        rows = self._rows("SELECT * FROM spans WHERE trace_id=? ORDER BY start_ts", (trace_id,))
        for r in rows:
            r["attrs"] = json.loads(r["attrs"] or "{}")
        return rows

    def trace_cost(self, trace_id):
        rows = self._rows("SELECT COALESCE(SUM(cost_usd),0) AS c FROM spans WHERE trace_id=?", (trace_id,))
        return rows[0]["c"]

    def stats(self):
        total = self._rows(
            """SELECT COUNT(DISTINCT trace_id) AS traces, COUNT(*) AS spans,
                      COALESCE(SUM(cost_usd),0) AS cost_usd, COALESCE(SUM(tokens_in),0) AS tokens_in,
                      COALESCE(SUM(tokens_out),0) AS tokens_out, COALESCE(SUM(status='error'),0) AS errors
               FROM spans""")[0]
        by_model = self._rows(
            """SELECT model, COUNT(*) AS calls, SUM(tokens_in) AS tokens_in, SUM(tokens_out) AS tokens_out,
                      SUM(cost_usd) AS cost_usd, AVG((end_ts-start_ts)*1000) AS avg_latency_ms
               FROM spans WHERE kind='llm' AND model IS NOT NULL GROUP BY model ORDER BY cost_usd DESC""")
        by_kind = self._rows(
            """SELECT kind, COUNT(*) AS n, AVG((end_ts-start_ts)*1000) AS avg_latency_ms
               FROM spans GROUP BY kind""")
        return {"totals": total, "by_model": by_model, "by_kind": by_kind}

    def close(self):
        with self._lock:
            self._conn.close()
