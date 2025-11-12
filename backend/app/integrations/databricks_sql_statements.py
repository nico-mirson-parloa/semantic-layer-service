"""
Databricks SQL Statements API client
Follows the documented flow: POST statement -> poll GET until SUCCEEDED -> return data/columns
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
import httpx
import asyncio
import structlog

from app.core.config import settings


logger = structlog.get_logger(__name__)


class DatabricksStatementsClient:
    def __init__(self) -> None:
        self.host = settings.databricks_host
        self.token = settings.databricks_token
        self.warehouse_id = settings.warehouse_id
        if not all([self.host, self.token, self.warehouse_id]):
            raise ValueError("Missing Databricks configuration (host/token/warehouse_id)")
        self.base_url = f"https://{self.host}/api/2.0/sql/statements"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        }

    async def run_sql_and_get_results(
        self, sql: str, catalog: Optional[str] = None, schema: Optional[str] = None, timeout_s: int = 120
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "statement": sql,
            "warehouse_id": self.warehouse_id,
            "format": "json",
        }
        if catalog:
            payload["catalog"] = catalog
        if schema:
            payload["schema"] = schema

        async with httpx.AsyncClient(timeout=30.0) as client:
            post_res = await client.post(self.base_url, headers=self.headers, json=payload)
            post_res.raise_for_status()
            body = post_res.json()
            statement_id = body.get("statement_id")
            if not statement_id:
                raise RuntimeError("Databricks did not return a statement_id")

        # Poll
        start = asyncio.get_event_loop().time()
        delay = 0.5
        while True:
            if (asyncio.get_event_loop().time() - start) > timeout_s:
                raise TimeoutError("Databricks SQL statement timed out")
            await asyncio.sleep(delay)
            delay = min(delay * 2, 4.0)
            status_body = await self._get_statement(statement_id)
            status = status_body.get("status")
            if status == "SUCCEEDED":
                # Parse data
                resp = status_body.get("statement_response", {})
                result = resp.get("result", {})
                data_array: List[List[Any]] = result.get("data_array", [])
                manifest = resp.get("manifest", {})
                columns = manifest.get("schema", {}).get("columns", [])
                return {
                    "statement_id": statement_id,
                    "status": status,
                    "row_count": status_body.get("row_count", len(data_array)),
                    "columns": columns,
                    "data": data_array,
                    "manifest": manifest,
                }
            if status in ("FAILED", "CANCELED"):
                raise RuntimeError(f"Databricks SQL statement {status}: {status_body}")

    async def _get_statement(self, statement_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/{statement_id}"
        async with httpx.AsyncClient(timeout=30.0) as client:
            res = await client.get(url, headers=self.headers)
            res.raise_for_status()
            return res.json()


_statements_client: Optional[DatabricksStatementsClient] = None


def get_statements_client() -> DatabricksStatementsClient:
    global _statements_client
    if _statements_client is None:
        _statements_client = DatabricksStatementsClient()
    return _statements_client


