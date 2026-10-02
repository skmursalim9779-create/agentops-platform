"""Persistent span store with SQLite for local use and PostgreSQL for production."""



import json

import os

import sqlite3

import threading

from pathlib import Path



try:

    import psycopg

except ImportError:

    psycopg = None





SCHEMA = """

CREATE TABLE IF NOT EXISTS spans (

  span_id TEXT PRIMARY KEY,

  trace_id TEXT NOT NULL,

   owner_id TEXT NOT NULL DEFAULT 'public',

  parent_id TEXT,

  name TEXT,

  kind TEXT,

  start_ts REAL,

  end_ts REAL,

  status TEXT DEFAULT 'ok',

  model TEXT,

  tokens_in INTEGER DEFAULT 0,

  tokens_out INTEGER DEFAULT 0,

  cost_usd REAL DEFAULT 0,

  input TEXT,

  output TEXT,

  attrs TEXT,

  error TEXT

);



CREATE INDEX IF NOT EXISTS idx_spans_trace

ON spans(trace_id);



CREATE INDEX IF NOT EXISTS idx_spans_start

ON spans(start_ts);

"""





COLUMNS = [

    "span_id",

    "trace_id",

    "owner_id",

    "parent_id",

    "name",

    "kind",

    "start_ts",

    "end_ts",

    "status",

    "model",

    "tokens_in",

    "tokens_out",

    "cost_usd",

    "input",

    "output",

    "attrs",

    "error",

]





class SpanStore:

    def __init__(self, path=".aop/traces.db"):

        self._lock = threading.Lock()



        database_url = os.environ.get("DATABASE_URL")



        if database_url and path != ":memory:":

            if psycopg is None:

                raise RuntimeError(

                    "DATABASE_URL is configured but psycopg is not installed"

                )



            self.backend = "postgres"

            self.path = database_url

            self._conn = psycopg.connect(database_url)

            self._init_postgres()



        else:

            self.backend = "sqlite"

            self.path = path



            if path != ":memory:":

                Path(path).parent.mkdir(

                    parents=True,

                    exist_ok=True,

                )



            self._conn = sqlite3.connect(

                path,

                check_same_thread=False,

            )

            self._conn.row_factory = sqlite3.Row

            self._init_sqlite()



    # ------------------------------------------------------------------

    # Database initialization

    # ------------------------------------------------------------------



    def _init_sqlite(self):

        with self._lock:

            self._conn.executescript(SCHEMA)



            columns = {

                row[1]

                for row in self._conn.execute(

                    "PRAGMA table_info(spans)"

                ).fetchall()

            }



            if "owner_id" not in columns:

                self._conn.execute(

                    """

                    ALTER TABLE spans

                    ADD COLUMN owner_id TEXT NOT NULL DEFAULT 'public'

                    """

                )



            self._conn.commit()



    def _init_postgres(self):

        with self._lock:

            cursor = self._conn.cursor()



            try:

                for statement in SCHEMA.split(";"):

                    statement = statement.strip()



                    if statement:

                        cursor.execute(statement)



                cursor.execute(

                    """

                    ALTER TABLE spans

                    ADD COLUMN IF NOT EXISTS owner_id

                    TEXT NOT NULL DEFAULT 'public'

                    """

                )



                self._conn.commit()



            except Exception:

                self._conn.rollback()

                raise



            finally:

                cursor.close()



    # ------------------------------------------------------------------

    # Database helpers

    # ------------------------------------------------------------------



    def _write(self, sql, args=()):

        with self._lock:

            cursor = self._conn.cursor()



            try:

                cursor.execute(sql, args)

                self._conn.commit()



            except Exception:

                self._conn.rollback()

                raise



            finally:

                cursor.close()



    def _rows(self, sql, args=()):

        with self._lock:

            cursor = self._conn.cursor()



            try:

                cursor.execute(sql, args)

                rows = cursor.fetchall()



                if not cursor.description:

                    return []



                columns = [

                    column.name

                    if hasattr(column, "name")

                    else column[0]

                    for column in cursor.description

                ]



                return [

                    dict(zip(columns, row))

                    for row in rows

                ]



            finally:

                cursor.close()



    # ------------------------------------------------------------------

    # Save span

    # ------------------------------------------------------------------



    def save(self, span):

        row = dict(span)

        row.setdefault("owner_id", "public")


        row["attrs"] = json.dumps(

            row.get("attrs") or {},

            default=str,

        )



        values = [

            row.get(column)

            for column in COLUMNS

        ]



        if self.backend == "postgres":

            placeholders = ", ".join(

                ["%s"] * len(COLUMNS)

            )



            updates = ", ".join(

                f"{column}=EXCLUDED.{column}"

                for column in COLUMNS

                if column != "span_id"

            )



            sql = (

                f"INSERT INTO spans "

                f"({','.join(COLUMNS)}) "

                f"VALUES ({placeholders}) "

                f"ON CONFLICT (span_id) DO UPDATE SET "

                f"{updates}"

            )



        else:

            placeholders = ", ".join(

                ["?"] * len(COLUMNS)

            )



            sql = (

                f"INSERT OR REPLACE INTO spans "

                f"({','.join(COLUMNS)}) "

                f"VALUES ({placeholders})"

            )



        self._write(sql, values)



    # ------------------------------------------------------------------

    # Traces

    # ------------------------------------------------------------------



    def traces(self, limit=50, owner_id="public"):

        if self.backend == "postgres":

            sql = """

                SELECT

                    trace_id,

                    MIN(start_ts) AS start_ts,

                    MAX(end_ts) AS end_ts,

                    COUNT(*) AS spans,

                    SUM(tokens_in) AS tokens_in,

                    SUM(tokens_out) AS tokens_out,

                    SUM(cost_usd) AS cost_usd,

                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS errors,

                    MAX(CASE WHEN parent_id IS NULL THEN name END) AS root

                FROM spans

                WHERE owner_id=%s

                GROUP BY trace_id

                ORDER BY MIN(start_ts) DESC

                LIMIT %s

            """

            args = (owner_id, limit)

        else:

            sql = """

                SELECT

                    trace_id,

                    MIN(start_ts) AS start_ts,

                    MAX(end_ts) AS end_ts,

                    COUNT(*) AS spans,

                    SUM(tokens_in) AS tokens_in,

                    SUM(tokens_out) AS tokens_out,

                    SUM(cost_usd) AS cost_usd,

                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) AS errors,

                    MAX(CASE WHEN parent_id IS NULL THEN name END) AS root

                FROM spans

                WHERE owner_id=?

                GROUP BY trace_id

                ORDER BY MIN(start_ts) DESC

                LIMIT ?

            """

            args = (owner_id, limit)

        return self._rows(sql, args)


    # ------------------------------------------------------------------

    # Single trace

    # ------------------------------------------------------------------



    def trace(self, trace_id, owner_id="public"):

        if self.backend == "postgres":

            sql = """

                SELECT *

                FROM spans

                WHERE trace_id=%s

                  AND owner_id=%s

                ORDER BY start_ts

            """

        else:

            sql = """

                SELECT *

                FROM spans

                WHERE trace_id=?

                  AND owner_id=?

                ORDER BY start_ts

            """

        rows = self._rows(sql, (trace_id, owner_id))

        for row in rows:

            attrs = row.get("attrs") or "{}"

            if isinstance(attrs, str):

                row["attrs"] = json.loads(attrs)

            elif attrs is None:

                row["attrs"] = {}

        return rows


    # ------------------------------------------------------------------

    # Trace cost

    # ------------------------------------------------------------------



    def trace_cost(self, trace_id, owner_id="public"):

        if self.backend == "postgres":

            sql = """

                SELECT COALESCE(SUM(cost_usd), 0) AS c

                FROM spans

                WHERE trace_id=%s

                  AND owner_id=%s

            """

        else:

            sql = """

                SELECT COALESCE(SUM(cost_usd), 0) AS c

                FROM spans

                WHERE trace_id=?

                  AND owner_id=?

            """

        rows = self._rows(sql, (trace_id, owner_id))

        return rows[0]["c"]


    # ------------------------------------------------------------------

    # Dashboard statistics

    # ------------------------------------------------------------------



    def stats(self, owner_id="public"):

        if self.backend == "postgres":
            p = "%s"
        else:
            p = "?"

        totals = self._rows(
            f"""
            SELECT
                COUNT(DISTINCT trace_id) AS traces,
                COUNT(*) AS spans,
                COALESCE(SUM(cost_usd), 0) AS cost_usd,
                COALESCE(SUM(tokens_in), 0) AS tokens_in,
                COALESCE(SUM(tokens_out), 0) AS tokens_out,
                COALESCE(SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END), 0) AS errors
            FROM spans
            WHERE owner_id={p}
            """,
            (owner_id,),
        )[0]

        by_model = self._rows(
            f"""
            SELECT
                model,
                COUNT(*) AS calls,
                SUM(tokens_in) AS tokens_in,
                SUM(tokens_out) AS tokens_out,
                SUM(cost_usd) AS cost_usd,
                AVG((end_ts - start_ts) * 1000) AS avg_latency_ms
            FROM spans
            WHERE owner_id={p}
              AND kind='llm'
              AND model IS NOT NULL
            GROUP BY model
            ORDER BY cost_usd DESC
            """,
            (owner_id,),
        )

        by_kind = self._rows(
            f"""
            SELECT
                kind,
                COUNT(*) AS n,
                AVG((end_ts - start_ts) * 1000) AS avg_latency_ms
            FROM spans
            WHERE owner_id={p}
            GROUP BY kind
            """,
            (owner_id,),
        )

        return {
            "totals": totals,
            "by_model": by_model,
            "by_kind": by_kind,
        }


    # ------------------------------------------------------------------

    # Close database

    # ------------------------------------------------------------------



    def close(self):

        with self._lock:

            self._conn.close()