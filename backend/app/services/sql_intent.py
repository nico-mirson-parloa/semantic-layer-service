"""
Rule-based NL -> SQL generator for common analytics intents.
This avoids returning demo SQL and works without Genie message reads or model serving.
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List
import re
import structlog

from app.integrations.databricks import get_databricks_connector


logger = structlog.get_logger(__name__)


def _contains(text: str, *needles: str) -> bool:
    t = text.lower()
    return all(n.lower() in t for n in needles)


def _find_table_for_latency_toolcall() -> Optional[Dict[str, Any]]:
    """Search UC for an analytics table that contains latency metrics suitable for grouping by tool.
    Preference order: amp_latency_metrics_validated, amp_conversation_tool_call_metrics, any table with 'latency'.
    """
    connector = get_databricks_connector()
    # Search analytics schema across catalogs
    tables = connector.get_tables(schema="analytics")

    def score(row: Dict[str, Any]) -> int:
        name = (row.get("table_name") or "").lower()
        s = 0
        if name == "amp_latency_metrics_validated":
            s += 100
        if "latency" in name:
            s += 10
        if "tool" in name:
            s += 5
        if name.startswith("amp_"):
            s += 3
        return s

    tables_sorted = sorted(tables, key=score, reverse=True)
    return tables_sorted[0] if tables_sorted else None


def _pick_column(columns: List[Dict[str, Any]], *keywords: str) -> Optional[str]:
    """Pick first column whose name contains any of the keywords (in priority order)."""
    names = [c.get("column_name") or "" for c in columns]
    for kw in keywords:
        for n in names:
            if kw.lower() in n.lower():
                return n
    return None


def generate_sql_from_intent(nl_query: str) -> Optional[str]:
    """Best-effort SQL for a handful of common intents.

    Returns SQL string or None if no rule matched.
    """
    q = nl_query.strip()
    if not q:
        return None

    # Case: latency per tool_call (group latency by tool)
    if _contains(q, "latency", "tool") or _contains(q, "latency", "tool_call"):
        table_row = _find_table_for_latency_toolcall()
        if not table_row:
            return None
        catalog = table_row.get("table_catalog")
        schema = table_row.get("table_schema")
        table = table_row.get("table_name")

        connector = get_databricks_connector()
        cols = connector.get_columns(catalog=catalog, schema=schema, table=table)

        # heuristic choices
        tool_col = _pick_column(cols, "tool_call", "tool", "function", "tool_name") or "tool"
        latency_col = _pick_column(cols, "latency_ms", "latency", "duration_ms", "duration") or "latency_ms"

        sql = f"""
SELECT
  {tool_col} AS tool,
  AVG({latency_col}) AS avg_latency,
  PERCENTILE({latency_col}, 0.5) AS p50_latency,
  PERCENTILE({latency_col}, 0.9) AS p90_latency,
  PERCENTILE({latency_col}, 0.99) AS p99_latency,
  COUNT(*) AS events
FROM {catalog}.{schema}.{table}
GROUP BY {tool_col}
ORDER BY avg_latency DESC
LIMIT 100
""".strip()
        return sql

    # No rule matched
    return None


