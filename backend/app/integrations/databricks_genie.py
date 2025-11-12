"""
Databricks Genie (AI/BI) API integration for natural language to SQL
"""
from typing import Dict, Any, Optional, List
import httpx
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class DatabricksGenieClient:
    """Client for Databricks Genie API"""
    
    def __init__(self):
        self.host = settings.databricks_host
        self.token = settings.databricks_token
        self.base_url = f"https://{self.host}/api/2.0"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    async def create_genie_space(self, warehouse_id: str) -> str:
        """Create a Genie space for natural language queries"""
        # Extract warehouse ID from HTTP path
        if not warehouse_id and settings.databricks_http_path:
            # Extract from path like /sql/1.0/warehouses/abcd1234
            parts = settings.databricks_http_path.split('/')
            if 'warehouses' in parts:
                idx = parts.index('warehouses')
                if idx + 1 < len(parts):
                    warehouse_id = parts[idx + 1]
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/genie/spaces",
                headers=self.headers,
                json={
                    "warehouse_id": warehouse_id,
                    "name": "Semantic Layer Genie Space"
                }
            )
            response.raise_for_status()
            return response.json()["space_id"]
    
    async def natural_language_to_sql(
        self, 
        query: str, 
        context: Optional[Dict[str, Any]] = None,
        space_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Convert natural language to SQL using Genie
        
        Args:
            query: Natural language query (e.g., "total revenue by month")
            context: Additional context like table names, catalog, schema
            space_id: Genie space ID (will create one if not provided)
        
        Returns:
            Dict with generated SQL and metadata
        """
        try:
            # Use configured space ID first
            if not space_id and settings.databricks_genie_space_id:
                space_id = settings.databricks_genie_space_id
            
            # Create a space if still not available
            if not space_id:
                warehouse_id = self._extract_warehouse_id()
                space_id = await self.create_genie_space(warehouse_id)
            
            # Build the prompt with context
            prompt = self._build_prompt(query, context)
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/genie/spaces/{space_id}/start-conversation",
                    headers=self.headers,
                    json={
                        "content": prompt
                    }
                )
                response.raise_for_status()
                
                result = response.json()
                # Extract conversation ID and message ID from the response
                conversation_id = result.get("conversation_id") or result.get("conversation", {}).get("conversation_id")
                message_id = result.get("message_id")
                
                if not conversation_id:
                    logger.error("No conversation ID in response", response=result)
                    raise ValueError("Failed to get conversation ID from Genie")
                
                logger.info("Started Genie conversation", conversation_id=conversation_id, message_id=message_id, space_id=space_id)
                
                # Get the SQL from the conversation
                sql_response = await self._get_conversation_result(
                    space_id, 
                    conversation_id,
                    message_id
                )
                
                return {
                    "sql": sql_response.get("sql"),
                    "explanation": sql_response.get("explanation"),
                    "confidence": sql_response.get("confidence", 0.8),
                    "conversation_id": conversation_id,
                    "space_id": space_id,
                    "message_id": message_id
                }
                
        except Exception as e:
            logger.error("Failed to generate SQL from natural language", error=str(e))
            raise
    
    async def refine_query(
        self, 
        space_id: str,
        conversation_id: str,
        feedback: str
    ) -> Dict[str, Any]:
        """Refine a query based on user feedback"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/genie/spaces/{space_id}/conversations/{conversation_id}/messages",
                headers=self.headers,
                json={
                    "content": feedback,
                    "message_type": "FEEDBACK"
                }
            )
            response.raise_for_status()
            
            return await self._get_conversation_result(space_id, conversation_id)
    
    async def suggest_metrics(
        self,
        table_name: str,
        catalog: str,
        schema: str
    ) -> List[Dict[str, str]]:
        """Suggest common metrics for a table"""
        prompt = f"""
        Given the table {catalog}.{schema}.{table_name}, suggest 5 common business metrics
        that could be calculated from this table. For each metric provide:
        1. A business-friendly name
        2. A description
        3. The natural language query to calculate it
        """
        
        result = await self.natural_language_to_sql(prompt, {
            "catalog": catalog,
            "schema": schema,
            "table": table_name
        })
        
        # Parse suggestions from the response
        return self._parse_metric_suggestions(result.get("explanation", ""))
    
    def _build_prompt(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """Build a contextualized prompt for Genie"""
        prompt_parts = []
        
        if context:
            if "catalog" in context and "schema" in context:
                prompt_parts.append(
                    f"Using catalog '{context['catalog']}' and schema '{context['schema']}'"
                )
            if "table" in context:
                prompt_parts.append(f"From table '{context['table']}'")
            if "time_grain" in context:
                prompt_parts.append(f"Grouped by {context['time_grain']}")
        
        prompt_parts.append(query)
        
        return ", ".join(prompt_parts)
    
    def _extract_warehouse_id(self) -> str:
        """Extract warehouse ID from HTTP path"""
        if settings.databricks_http_path:
            parts = settings.databricks_http_path.split('/')
            if 'warehouses' in parts:
                idx = parts.index('warehouses')
                if idx + 1 < len(parts):
                    return parts[idx + 1]
        raise ValueError("Could not extract warehouse ID from HTTP path")
    
    async def _get_conversation_result(
        self, 
        space_id: str, 
        conversation_id: str,
        message_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Poll for conversation result and extract SQL from attachments"""
        import asyncio
        
        async with httpx.AsyncClient() as client:
            # Poll for results - Genie processes async
            max_attempts = 30  # 30 seconds max
            for attempt in range(max_attempts):
                try:
                    # If we have a message_id, try to get the specific message
                    if message_id:
                        # Try the specific message endpoint
                        response = await client.get(
                            f"{self.base_url}/genie/spaces/{space_id}/conversations/{conversation_id}/messages/{message_id}",
                            headers=self.headers
                        )
                    else:
                        # Fall back to getting all messages
                        response = await client.get(
                            f"{self.base_url}/genie/spaces/{space_id}/conversations/{conversation_id}/messages",
                            headers=self.headers
                        )
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Handle single message response
                        if message_id and isinstance(data, dict):
                            return self._extract_sql_from_message(data)
                        
                        # Handle multiple messages
                        elif isinstance(data, list) and len(data) > 0:
                            # Get the latest assistant message
                            for message in reversed(data):
                                if message.get("role") == "assistant" or message.get("type") == "RESPONSE":
                                    result = self._extract_sql_from_message(message)
                                    if result.get("sql"):
                                        return result
                
                except Exception as e:
                    logger.warning(f"Poll attempt {attempt + 1} failed: {e}")
                
                # Wait before next poll
                await asyncio.sleep(1)
            
            # If we get here, polling timed out
            return {
                "sql": "",
                "explanation": "Query processing timed out",
                "confidence": 0.0
            }
    
    def _extract_sql_from_message(self, message: Dict[str, Any]) -> Dict[str, Any]:
        """Extract SQL from a Genie message's attachments"""
        sql = ""
        explanation = message.get("content", "")
        
        # Check attachments array for SQL query
        attachments = message.get("attachments", [])
        for attachment in attachments:
            # The SQL is nested: attachment.query.query
            query_obj = attachment.get("query", {})
            if isinstance(query_obj, dict):
                sql = query_obj.get("query", "")
                if query_obj.get("description"):
                    explanation = query_obj.get("description")
                if sql:
                    break
            # Also try direct query field in attachment
            elif isinstance(query_obj, str):
                sql = query_obj
                if sql:
                    break
        
        # Fallback: check for sql_query field (older API format)
        if not sql and message.get("sql_query"):
            sql = message.get("sql_query")
        
        # Fallback: check for query field directly in message
        if not sql and message.get("query"):
            sql = message.get("query")
        
        return {
            "sql": sql,
            "explanation": explanation,
            "confidence": 0.9 if sql else 0.0
        }
    
    def _parse_metric_suggestions(self, explanation: str) -> List[Dict[str, str]]:
        """Parse metric suggestions from Genie response"""
        # This would parse the structured response
        # For now, return example suggestions
        return [
            {
                "name": "Total Revenue",
                "description": "Sum of all order amounts",
                "query": "Calculate total revenue from all orders"
            },
            {
                "name": "Order Count", 
                "description": "Number of orders placed",
                "query": "Count the total number of orders"
            },
            {
                "name": "Average Order Value",
                "description": "Average amount per order",
                "query": "Calculate the average order value"
            }
        ]


# Singleton instance
_genie_client: Optional[DatabricksGenieClient] = None


def get_genie_client() -> DatabricksGenieClient:
    """Get or create Genie client instance"""
    global _genie_client
    if _genie_client is None:
        _genie_client = DatabricksGenieClient()
    return _genie_client
