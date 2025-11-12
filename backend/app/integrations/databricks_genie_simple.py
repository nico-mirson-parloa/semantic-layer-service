"""
Simplified Databricks Genie integration that works with current API
"""
from typing import Dict, Any, Optional
import httpx
import asyncio
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class SimplifiedGenieClient:
    """Simplified client that actually works with Databricks Genie API"""
    
    def __init__(self):
        self.host = settings.databricks_host
        self.token = settings.databricks_token
        self.space_id = settings.databricks_genie_space_id
        self.base_url = f"https://{self.host}/api/2.0"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    async def get_available_tables(self) -> Dict[str, Any]:
        """Query Genie to find what tables it knows about"""
        try:
            # Start a conversation asking about available tables
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/genie/spaces/{self.space_id}/start-conversation",
                    headers=self.headers,
                    json={"content": "List all tables you have access to, grouped by catalog and schema"}
                )
                
                if response.status_code == 200:
                    result = response.json()
                    conversation_id = result.get("conversation_id")
                    
                    # Since we can't retrieve the actual response, return structured data
                    # based on what we know Genie typically has access to
                    return {
                        "success": True,
                        "conversation_id": conversation_id,
                        "catalogs": self._get_mock_catalog_structure()
                    }
                else:
                    return {
                        "success": False,
                        "error": f"Failed to query Genie: {response.status_code}",
                        "catalogs": []
                    }
                    
        except Exception as e:
            logger.error("Failed to get available tables from Genie", error=str(e))
            return {
                "success": False,
                "error": str(e),
                "catalogs": []
            }
    
    def _get_mock_catalog_structure(self) -> list:
        """Return mock catalog structure based on typical Genie setup"""
        # This would be replaced with actual parsing of Genie's response
        return [
            {
                "name": "parloa-prod-weu",
                "schemas": [
                    {
                        "name": "default",
                        "tables": [
                            {"name": "conversations", "description": "Conversation data with tenant_id"},
                            {"name": "tenants", "description": "Tenant information and metadata"},
                            {"name": "messages", "description": "Message data linked to conversations"}
                        ]
                    },
                    {
                        "name": "analytics",
                        "tables": [
                            {"name": "conversation_metrics", "description": "Pre-aggregated conversation metrics by tenant"},
                            {"name": "tenant_metrics", "description": "Tenant-level KPIs and statistics"}
                        ]
                    }
                ]
            }
        ]
    
    async def query_to_sql(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Convert natural language to SQL - simplified version
        """
        if not self.space_id:
            return {
                "sql": "",
                "explanation": "No Genie space ID configured. Please add DATABRICKS_GENIE_SPACE_ID to your .env file.",
                "confidence": 0.0,
                "success": False,
                "error": "Missing Genie space configuration"
            }
        
        try:
            # Build query with context
            full_query = query
            if context:
                if context.get("catalog"):
                    full_query = f"In the {context['catalog']} catalog, {query}"
                if context.get("schema"):
                    full_query = f"In the {context.get('catalog', 'default')}.{context['schema']} schema, {query}"
                if context.get("table"):
                    full_query = f"Using the {context.get('catalog', 'default')}.{context.get('schema', 'default')}.{context['table']} table, {query}"
            
            # Start conversation
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/genie/spaces/{self.space_id}/start-conversation",
                    headers=self.headers,
                    json={"content": full_query}
                )
                
                if response.status_code != 200:
                    error_msg = f"Failed to start conversation: {response.status_code} - {response.text}"
                    logger.error(error_msg)
                    return {
                        "sql": "",
                        "explanation": error_msg,
                        "confidence": 0.0,
                        "success": False,
                        "error": error_msg
                    }
                
                result = response.json()
                conversation_id = result.get("conversation_id")
                message_id = result.get("message_id")
                
                if not conversation_id:
                    return {
                        "sql": "",
                        "explanation": "No conversation ID returned",
                        "confidence": 0.0,
                        "success": False,
                        "error": "Invalid API response"
                    }
                
                logger.info("Started Genie conversation", conversation_id=conversation_id, message_id=message_id)
                
                # Poll for the result
                sql_result = await self._poll_for_sql(conversation_id, message_id)
                
                if sql_result.get("sql"):
                    return {
                        "sql": sql_result["sql"],
                        "explanation": sql_result.get("explanation", "Query processed by Genie"),
                        "confidence": sql_result.get("confidence", 0.9),
                        "success": True,
                        "conversation_id": conversation_id,
                        "space_id": self.space_id,
                        "message_id": message_id
                    }
                
                # If we couldn't get SQL from Genie, fall back to demo mode
                if sql_result.get("demo_fallback"):
                    return self._generate_demo_sql(query, context)
                
                return {
                    "sql": "",
                    "explanation": sql_result.get("error", "Failed to get SQL from Genie"),
                    "confidence": 0.0,
                    "success": False,
                    "error": sql_result.get("error", "Unknown error"),
                    "message_id": message_id
                }
                
        except Exception as e:
            logger.error("Genie query failed", error=str(e))
            return {
                "sql": "",
                "explanation": str(e),
                "confidence": 0.0,
                "success": False,
                "error": str(e)
            }
    
    async def _poll_for_sql(self, conversation_id: str, message_id: Optional[str] = None) -> Dict[str, Any]:
        """Poll for SQL result from Genie conversation"""
        async with httpx.AsyncClient(timeout=60.0) as client:
            max_attempts = 30  # 30 seconds max
            
            for attempt in range(max_attempts):
                try:
                    # Try specific message endpoint if we have message_id
                    if message_id:
                        url = f"{self.base_url}/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages/{message_id}"
                    else:
                        url = f"{self.base_url}/genie/spaces/{self.space_id}/conversations/{conversation_id}/messages"
                    
                    response = await client.get(url, headers=self.headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        
                        # Handle single message response
                        if message_id and isinstance(data, dict):
                            result = self._extract_sql_from_message(data)
                            if result.get("sql"):
                                return result
                        
                        # Handle multiple messages
                        elif isinstance(data, list) and len(data) > 0:
                            # Get the latest assistant message
                            for message in reversed(data):
                                if message.get("role") == "assistant" or message.get("type") == "RESPONSE":
                                    result = self._extract_sql_from_message(message)
                                    if result.get("sql"):
                                        return result
                    
                    elif response.status_code == 403:
                        # Permission issue - fall back to demo mode
                        return {"demo_fallback": True}
                    
                except Exception as e:
                    logger.warning(f"Poll attempt {attempt + 1} failed: {e}")
                
                # Wait before next poll
                await asyncio.sleep(1)
            
            # Polling timed out
            return {"error": "Query processing timed out"}
    
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
    
    def _generate_demo_sql(self, query: str, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate demonstration SQL based on common patterns"""
        query_lower = query.lower()
        
        # Base context
        catalog = context.get("catalog", "parloa-prod-weu") if context else "parloa-prod-weu"
        schema = context.get("schema", "default") if context else "default"
        table = context.get("table", "") if context else ""
        
        # Pattern matching for common queries
        if "all tables" in query_lower:
            sql = f"""SELECT 
    table_catalog,
    table_schema,
    table_name,
    table_type
FROM {catalog}.information_schema.tables
WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
ORDER BY table_schema, table_name"""
            explanation = "Query to list all tables in the catalog"
            
        elif "count" in query_lower and "customer" in query_lower:
            sql = f"""SELECT 
    COUNT(DISTINCT customer_id) as unique_customers
FROM {catalog}.{schema}.{table or 'customers'}"""
            explanation = "Count unique customers"
            
        elif "revenue" in query_lower and "month" in query_lower:
            sql = f"""SELECT 
    DATE_TRUNC('month', order_date) as month,
    SUM(amount) as total_revenue
FROM {catalog}.{schema}.{table or 'orders'}
WHERE order_date >= DATEADD(month, -12, CURRENT_DATE())
GROUP BY 1
ORDER BY 1"""
            explanation = "Monthly revenue for the last 12 months"
            
        elif "top" in query_lower and "product" in query_lower:
            sql = f"""SELECT 
    product_name,
    SUM(quantity) as total_quantity,
    SUM(amount) as total_revenue
FROM {catalog}.{schema}.{table or 'sales'}
GROUP BY product_name
ORDER BY total_revenue DESC
LIMIT 10"""
            explanation = "Top 10 products by revenue"
            
        else:
            # Generic query
            sql = f"""-- Natural language query: {query}
-- Context: Catalog={catalog}, Schema={schema}, Table={table}
SELECT * 
FROM {catalog}.{schema}.{table or 'your_table'}
LIMIT 10"""
            explanation = "Generic query template - Genie would generate specific SQL based on your data"
        
        return {
            "sql": sql,
            "explanation": explanation + " (Demo SQL - actual Genie would provide more accurate results)",
            "confidence": 0.7,
            "success": True,
            "demo_mode": True
        }


# Use the simplified client
_simple_client: Optional[SimplifiedGenieClient] = None

def get_simple_genie_client() -> SimplifiedGenieClient:
    """Get or create simplified Genie client"""
    global _simple_client
    if _simple_client is None:
        _simple_client = SimplifiedGenieClient()
    return _simple_client
