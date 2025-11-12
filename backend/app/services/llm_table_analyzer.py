"""
LLM-based Table Analyzer using Databricks Foundation Models
"""
import json
from typing import List, Dict, Any, Optional
import structlog
import requests
from datetime import datetime

from app.models.catalog import TableSchema, ColumnInfo
from app.models.semantic import (
    SuggestedMetric, SuggestedDimension, AnalysisResult
)
from app.core.config import settings
from app.integrations.databricks import DatabricksConnector

logger = structlog.get_logger()


class LLMTableAnalyzer:
    """Analyzes tables using Databricks Foundation Models (LLMs)"""
    
    def __init__(self):
        """Initialize with Databricks connection"""
        self.connector = DatabricksConnector()
        # Foundation Model endpoint - can be configured
        self.model_endpoint = getattr(
            settings, 
            'databricks_foundation_model_endpoint',
            'databricks-dbrx-instruct'  # Default to DBRX
        )
        
    def analyze_table_with_llm(self, table_schema: TableSchema) -> AnalysisResult:
        """
        Analyze table using LLM to generate intelligent metric and dimension suggestions
        """
        logger.info(f"Analyzing table with LLM: {table_schema.full_name}")
        
        # Build context for LLM
        schema_context = self._build_schema_context(table_schema)
        
        # Create prompt for LLM
        prompt = self._create_analysis_prompt(schema_context, table_schema)
        
        # Call LLM for analysis
        llm_response = self._call_databricks_llm(prompt)
        
        # Parse LLM response into suggestions
        suggestions = self._parse_llm_response(llm_response, table_schema)
        
        return suggestions
    
    def _build_schema_context(self, table_schema: TableSchema) -> str:
        """Build a detailed schema context for the LLM"""
        context_parts = []
        
        # Table information
        context_parts.append(f"Table: {table_schema.full_name}")
        if table_schema.table_comment:
            context_parts.append(f"Description: {table_schema.table_comment}")
        
        # Column information
        context_parts.append("\nColumns:")
        for col in table_schema.columns:
            col_desc = f"- {col.name} ({col.data_type})"
            if col.comment:
                col_desc += f" - {col.comment}"
            if col.nullable:
                col_desc += " (nullable)"
            context_parts.append(col_desc)
        
        return "\n".join(context_parts)
    
    def _create_analysis_prompt(self, schema_context: str, table_schema: TableSchema) -> str:
        """Create a detailed prompt for the LLM"""
        prompt = f"""You are a data analytics expert analyzing a database table to suggest metrics and dimensions for a semantic layer.

{schema_context}

Based on this table schema, provide intelligent suggestions for:

1. METRICS: Business metrics that can be calculated from numeric columns. Consider:
   - Simple aggregations (SUM, AVG, COUNT, MIN, MAX)
   - Derived metrics (ratios, percentages, growth rates)
   - Business-specific metrics based on column names and context
   - Include confidence scores (0.0-1.0) based on how useful each metric would be

2. DIMENSIONS: Categorical attributes for grouping and filtering. Consider:
   - Natural grouping columns (IDs, categories, types)
   - Time dimensions with appropriate granularities
   - Geographic dimensions if applicable
   - Hierarchical relationships between dimensions

3. ADDITIONAL INSIGHTS:
   - Suggest meaningful relationships between metrics and dimensions
   - Identify potential data quality metrics
   - Recommend time-based analysis if date/timestamp columns exist

Return your analysis in the following JSON format:
{{
  "metrics": [
    {{
      "name": "metric_internal_name",
      "display_name": "User Friendly Metric Name",
      "expression": "SQL expression",
      "aggregation": "sum|avg|count|min|max|custom",
      "description": "What this metric measures",
      "business_context": "Why this metric is important",
      "confidence_score": 0.95,
      "category": "revenue|cost|performance|quality|engagement",
      "requires_dimension": ["optional_required_dimensions"],
      "format": "currency|percentage|number|duration"
    }}
  ],
  "dimensions": [
    {{
      "name": "dimension_name",
      "display_name": "User Friendly Name",
      "type": "categorical|time|geographic|hierarchical",
      "description": "What this dimension represents",
      "granularities": ["for time dimensions: day|week|month|quarter|year"],
      "sample_values": ["up to 5 example values if known"]
    }}
  ],
  "insights": {{
    "table_type": "fact|dimension|bridge|aggregate",
    "primary_use_case": "Description of main analytics use case",
    "recommended_analyses": ["List of recommended analysis types"],
    "data_quality_metrics": ["Suggested data quality checks"]
  }}
}}

Table name: {table_schema.table}
Please analyze this table and provide comprehensive suggestions."""
        
        return prompt
    
    def _call_databricks_llm(self, prompt: str) -> str:
        """
        Call Databricks Foundation Model API
        
        This can be done through:
        1. Model Serving Endpoints (preferred)
        2. Databricks SQL AI Functions (ai_query)
        3. External LLM APIs
        """
        # Try different methods in order of preference
        
        # Method 1: Try Model Serving API first (more reliable)
        try:
            logger.info(f"Calling Databricks Model Serving endpoint: {self.model_endpoint}")
            return self._call_model_serving_endpoint(prompt)
        except Exception as e:
            logger.warning(f"Model serving endpoint failed: {e}")
        
        # Method 2: Try SQL AI Functions as fallback
        try:
            if self.model_endpoint.startswith('databricks-'):
                # Use built-in Foundation Models
                query = f"""
                SELECT ai_query(
                    '{self.model_endpoint}',
                    '{prompt.replace("'", "''")}'
                ) as llm_response
                """
            else:
                # Use custom model serving endpoint
                query = f"""
                SELECT ai_query(
                    '{self.model_endpoint}',
                    '{prompt.replace("'", "''")}',
                    'returnType', 'STRING'
                ) as llm_response
                """
            
            results = self.connector.execute_query(query)
            if results and len(results) > 0:
                return results[0]['llm_response']
                
        except Exception as e:
            logger.warning(f"SQL AI function failed: {e}")
        
        # Method 3: Use enhanced pattern-based analysis as fallback
        logger.info("Using enhanced pattern-based analysis")
        return self._get_enhanced_fallback_response(prompt)
    
    def _call_model_serving_endpoint(self, prompt: str) -> str:
        """
        Call a Databricks Model Serving endpoint directly
        """
        try:
            # Get Databricks workspace URL and token
            host = settings.databricks_host
            token = settings.databricks_token
            
            # Construct the endpoint URL
            endpoint_url = f"https://{host}/api/2.0/preview/ml/served-models/{self.model_endpoint}/invocations"
            
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": prompt,
                "max_tokens": 2000,
                "temperature": 0.3  # Matching Databricks chat node temperature
            }
            
            response = requests.post(endpoint_url, json=payload, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                logger.debug(f"Model serving response: {json.dumps(result)[:500]}...")
                
                # Extract the generated text based on various response formats
                if "predictions" in result:
                    # Standard model serving format
                    if isinstance(result["predictions"], list) and len(result["predictions"]) > 0:
                        prediction = result["predictions"][0]
                        if isinstance(prediction, dict) and "generated_text" in prediction:
                            return prediction["generated_text"]
                        elif isinstance(prediction, str):
                            return prediction
                elif "choices" in result:
                    # OpenAI-compatible format
                    if isinstance(result["choices"], list) and len(result["choices"]) > 0:
                        choice = result["choices"][0]
                        if "message" in choice and "content" in choice["message"]:
                            return choice["message"]["content"]
                        elif "text" in choice:
                            return choice["text"]
                elif "generated_text" in result:
                    # Direct text format
                    return result["generated_text"]
                elif "text" in result:
                    # Alternative text format
                    return result["text"]
                elif "output" in result:
                    # Another possible format
                    return result["output"]
                else:
                    # Return the whole result as JSON if format is unknown
                    logger.warning(f"Unknown response format from model serving: {list(result.keys())}")
                    return json.dumps(result)
            else:
                logger.error(f"Model serving endpoint returned {response.status_code}: {response.text}")
                raise Exception(f"Model serving error: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error calling model serving endpoint: {e}")
            raise
    
    def _get_enhanced_fallback_response(self, prompt: str) -> str:
        """
        Provide an enhanced fallback response using advanced pattern analysis
        when LLM is not available
        """
        # Extract table information from prompt
        table_info = {}
        if "Columns:" in prompt:
            columns_section = prompt.split("Columns:")[1].split("\n\n")[0]
            columns = []
            for line in columns_section.strip().split("\n"):
                if line.strip().startswith("-"):
                    parts = line.strip("- ").split(" (")
                    if len(parts) >= 2:
                        col_name = parts[0]
                        col_type = parts[1].split(")")[0]
                        columns.append({"name": col_name, "type": col_type})
            
            # Generate intelligent suggestions based on patterns
            metrics = []
            dimensions = []
            
            for col in columns:
                col_name = col["name"].lower()
                col_type = col["type"].upper()
                
                # Enhanced metric detection
                if any(t in col_type for t in ["INT", "DECIMAL", "DOUBLE", "FLOAT", "NUMERIC"]):
                    # Revenue/Financial metrics
                    if any(fin in col_name for fin in ["revenue", "sales", "amount", "price", "cost", "fee"]):
                        metrics.extend([
                            {
                                "name": f"total_{col['name']}",
                                "display_name": f"Total {col['name'].replace('_', ' ').title()}",
                                "expression": f"SUM({col['name']})",
                                "aggregation": "sum",
                                "description": f"Total {col['name'].replace('_', ' ')} across all records",
                                "business_context": f"Key financial metric tracking total {col['name'].replace('_', ' ')}",
                                "confidence_score": 0.95,
                                "category": "revenue",
                                "format": "currency"
                            },
                            {
                                "name": f"avg_{col['name']}",
                                "display_name": f"Average {col['name'].replace('_', ' ').title()}",
                                "expression": f"AVG({col['name']})",
                                "aggregation": "avg",
                                "description": f"Average {col['name'].replace('_', ' ')} per transaction",
                                "business_context": f"Helps understand typical {col['name'].replace('_', ' ')} values",
                                "confidence_score": 0.85,
                                "category": "revenue",
                                "format": "currency"
                            }
                        ])
                    
                    # Performance metrics
                    elif any(perf in col_name for perf in ["latency", "duration", "time", "delay"]):
                        metrics.extend([
                            {
                                "name": f"avg_{col['name']}",
                                "display_name": f"Average {col['name'].replace('_', ' ').title()}",
                                "expression": f"AVG({col['name']})",
                                "aggregation": "avg",
                                "description": f"Average {col['name'].replace('_', ' ')}",
                                "business_context": "Key performance indicator for system efficiency",
                                "confidence_score": 0.95,
                                "category": "performance",
                                "format": "duration"
                            },
                            {
                                "name": f"p95_{col['name']}",
                                "display_name": f"95th Percentile {col['name'].replace('_', ' ').title()}",
                                "expression": f"PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY {col['name']})",
                                "aggregation": "custom",
                                "description": f"95th percentile of {col['name'].replace('_', ' ')}",
                                "business_context": "Shows performance for 95% of cases, excluding outliers",
                                "confidence_score": 0.90,
                                "category": "performance",
                                "format": "duration"
                            }
                        ])
                    
                    # Count/Quantity metrics
                    elif any(cnt in col_name for cnt in ["count", "quantity", "number", "total"]):
                        metrics.append({
                            "name": f"total_{col['name']}",
                            "display_name": f"Total {col['name'].replace('_', ' ').title()}",
                            "expression": f"SUM({col['name']})",
                            "aggregation": "sum",
                            "description": f"Total {col['name'].replace('_', ' ')}",
                            "business_context": f"Aggregate measure of {col['name'].replace('_', ' ')}",
                            "confidence_score": 0.90,
                            "category": "engagement",
                            "format": "number"
                        })
                
                # Dimension detection
                elif col_type in ["STRING", "VARCHAR", "CHAR", "TEXT"]:
                    dim_type = "categorical"
                    if any(geo in col_name for geo in ["country", "state", "city", "region", "location", "geo"]):
                        dim_type = "geographic"
                    
                    dimensions.append({
                        "name": col['name'],
                        "display_name": col['name'].replace('_', ' ').title(),
                        "type": dim_type,
                        "description": f"Group by {col['name'].replace('_', ' ')}",
                        "sample_values": []
                    })
                
                # Time dimension detection
                elif col_type in ["DATE", "TIMESTAMP", "DATETIME"]:
                    dimensions.append({
                        "name": col['name'],
                        "display_name": col['name'].replace('_', ' ').title(),
                        "type": "time",
                        "description": f"Time-based analysis using {col['name'].replace('_', ' ')}",
                        "granularities": ["day", "week", "month", "quarter", "year"]
                    })
            
            return json.dumps({
                "metrics": metrics[:10],  # Limit to top 10
                "dimensions": dimensions[:10],
                "insights": {
                    "table_type": "fact" if metrics else "dimension",
                    "primary_use_case": "Analytics and reporting",
                    "recommended_analyses": [
                        "Time series analysis" if any(d["type"] == "time" for d in dimensions) else None,
                        "Geographic analysis" if any(d["type"] == "geographic" for d in dimensions) else None,
                        "Performance monitoring" if any(m.get("category") == "performance" for m in metrics) else None,
                        "Financial analysis" if any(m.get("category") == "revenue" for m in metrics) else None
                    ],
                    "data_quality_metrics": [
                        "Null value percentage by column",
                        "Data freshness monitoring",
                        "Outlier detection for numeric columns"
                    ]
                }
            })
        
        return self._get_fallback_response()
    
    def _get_fallback_response(self) -> str:
        """Provide a basic fallback response if all methods fail"""
        return json.dumps({
            "metrics": [],
            "dimensions": [],
            "insights": {
                "table_type": "unknown",
                "primary_use_case": "Table analysis requires LLM or pattern matching",
                "recommended_analyses": [],
                "data_quality_metrics": []
            }
        })
    
    def _parse_llm_response(self, llm_response: str, table_schema: TableSchema) -> AnalysisResult:
        """Parse LLM response into structured suggestions"""
        try:
            # Parse JSON response
            analysis = json.loads(llm_response)
            
            # Convert to model objects
            metrics = []
            for metric_data in analysis.get('metrics', []):
                metrics.append(SuggestedMetric(
                    name=metric_data['name'],
                    display_name=metric_data['display_name'],
                    expression=metric_data['expression'],
                    aggregation=metric_data.get('aggregation'),
                    description=metric_data['description'],
                    metric_type='simple' if metric_data.get('aggregation') else 'derived',
                    confidence_score=metric_data.get('confidence_score', 0.8),
                    category=metric_data.get('category'),
                    format=metric_data.get('format'),
                    requires_time_dimension='time' in metric_data.get('requires_dimension', [])
                ))
            
            dimensions = []
            for dim_data in analysis.get('dimensions', []):
                dimensions.append(SuggestedDimension(
                    name=dim_data['name'],
                    display_name=dim_data['display_name'],
                    type=dim_data['type'],
                    expression=dim_data['name'],  # Default to column name
                    description=dim_data['description'],
                    granularities=dim_data.get('granularities'),
                    sample_values=dim_data.get('sample_values')
                ))
            
            # Build analysis result
            insights = analysis.get('insights', {})
            
            result = AnalysisResult(
                table_analysis={
                    "table_name": table_schema.table,
                    "table_type": insights.get('table_type', 'unknown'),
                    "columns": {
                        col.name: {
                            "data_type": col.data_type,
                            "nullable": col.nullable,
                            "comment": col.comment
                        } for col in table_schema.columns
                    }
                },
                suggested_metrics=metrics,
                suggested_dimensions=dimensions,
                analysis_notes=insights.get('recommended_analyses', []),
                confidence_scores={
                    "overall": 0.90,  # High confidence with LLM analysis
                    "metrics": 0.95,
                    "dimensions": 0.90
                }
            )
            
            result.calculate_statistics()
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            logger.debug(f"LLM Response: {llm_response[:500]}...")
            
            # Fall back to basic analysis
            return self._create_basic_analysis(table_schema)
    
    def _create_basic_analysis(self, table_schema: TableSchema) -> AnalysisResult:
        """Create a basic analysis when LLM fails"""
        # Use the existing pattern-based analyzer as fallback
        from app.services.table_analyzer import TableAnalyzer
        from app.services.metric_suggester import MetricSuggester
        
        analyzer = TableAnalyzer(self.connector)
        analysis = analyzer.analyze_table(table_schema)
        
        # Convert to format for metric suggester
        analyzed_dict = {
            "table_name": analysis.table_name,
            "table_type": analysis.table_type,
            "columns": {}
        }
        
        # Add column info with proper pattern detection
        for col in analysis.columns:
            pattern = "dimension"  # default
            
            if col.name in analysis.numeric_columns:
                if col.name in analysis.id_columns:
                    pattern = "identifier"
                elif any(keyword in col.name.lower() for keyword in ['amount', 'price', 'cost', 'revenue', 'total', 'fee', 'charge']):
                    pattern = "amount"
                elif any(keyword in col.name.lower() for keyword in ['count', 'qty', 'quantity', 'volume', 'number']):
                    pattern = "quantity"
                elif any(keyword in col.name.lower() for keyword in ['rate', 'ratio', 'percent', 'pct', 'share']):
                    pattern = "percentage"
                else:
                    pattern = "metric"
            elif col.name in analysis.temporal_columns:
                pattern = "time"
            elif col.name in analysis.boolean_columns:
                pattern = "boolean"
            elif col.name in analysis.categorical_columns:
                pattern = "dimension"
            
            analyzed_dict["columns"][col.name] = {
                "data_type": col.data_type,
                "pattern": pattern,
                "nullable": col.nullable,
                "comment": col.comment
            }
        
        # Suggest metrics
        suggester = MetricSuggester()
        suggestions = suggester.suggest_metrics(analyzed_dict)
        
        # Generate dimension suggestions
        dimension_suggestions = []
        
        # Add categorical columns as dimensions
        for col_name in analysis.categorical_columns:
            col_info = next((c for c in analysis.columns if c.name == col_name), None)
            if col_info:
                dim_type = "categorical"
                if any(geo in col_name.lower() for geo in ['country', 'state', 'city', 'region', 'location']):
                    dim_type = "geographic"
                
                dimension_suggestions.append(SuggestedDimension(
                    name=col_name,
                    display_name=col_name.replace('_', ' ').title(),
                    type=dim_type,
                    expression=col_name,
                    description=col_info.comment or f"Dimension based on {col_name}"
                ))
        
        # Add time dimensions
        for col_name in analysis.temporal_columns:
            col_info = next((c for c in analysis.columns if c.name == col_name), None)
            if col_info and col_info.data_type in ['DATE', 'TIMESTAMP']:
                dimension_suggestions.append(SuggestedDimension(
                    name=col_name,
                    display_name=col_name.replace('_', ' ').title(),
                    type="time",
                    expression=col_name,
                    description=col_info.comment or f"Time dimension based on {col_name}",
                    granularities=["day", "week", "month", "quarter", "year"] if col_info.data_type == 'DATE' else ["hour", "day", "week", "month", "quarter", "year"]
                ))
        
        # Build response
        result = AnalysisResult(
            table_analysis=analyzed_dict,
            suggested_metrics=suggestions[:10],  # Limit suggestions
            suggested_dimensions=dimension_suggestions[:10],  # Limit dimensions too
            suggested_entities=[],
            suggested_measures=[],
            confidence_scores={
                "overall": 0.85,
                "metrics": 0.90,
                "dimensions": 0.80
            }
        )
        
        result.calculate_statistics()
        return result


class LLMModelRegistry:
    """Registry of available Databricks Foundation Models"""
    
    AVAILABLE_MODELS = {
        'databricks-llama-4-maverick': {
            'name': 'Llama 4 Maverick',
            'context_length': 8192,
            'description': 'Databricks Llama 4 model optimized for chat',
            'endpoint': 'databricks-llama-4-maverick'
        },
        'databricks-dbrx-instruct': {
            'name': 'DBRX Instruct',
            'context_length': 32768,
            'description': 'Databricks DBRX model optimized for instructions',
            'endpoint': 'databricks-dbrx-instruct'
        },
        'databricks-llama-2-70b-chat': {
            'name': 'Llama 2 70B Chat',
            'context_length': 4096,
            'description': 'Meta Llama 2 70B parameter chat model',
            'endpoint': 'databricks-llama-2-70b-chat'
        },
        'databricks-mixtral-8x7b-instruct': {
            'name': 'Mixtral 8x7B Instruct',
            'context_length': 32768,
            'description': 'Mistral AI Mixtral model with MoE architecture',
            'endpoint': 'databricks-mixtral-8x7b-instruct'
        },
        'databricks-mpt-30b-instruct': {
            'name': 'MPT 30B Instruct',
            'context_length': 8192,
            'description': 'MosaicML MPT 30B instruction-tuned model',
            'endpoint': 'databricks-mpt-30b-instruct'
        }
    }
    
    @classmethod
    def get_model_info(cls, model_key: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model"""
        return cls.AVAILABLE_MODELS.get(model_key)
    
    @classmethod
    def list_models(cls) -> List[Dict[str, Any]]:
        """List all available models"""
        return [
            {'key': k, **v} 
            for k, v in cls.AVAILABLE_MODELS.items()
        ]
