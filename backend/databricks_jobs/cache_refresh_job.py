"""
Databricks Job: Cache Refresh and Metric Pre-aggregation

This job runs every 15 minutes to:
1. Refresh cached metric results
2. Update pre-aggregated tables
3. Monitor cache performance
4. Send alerts for cache misses

Deploy this as a Databricks Job with:
- Cluster: Single node with Databricks Runtime
- Schedule: Every 15 minutes
- Libraries: databricks-sdk, pyyaml, structlog
"""

import os
import json
import time
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import structlog
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import ExecuteStatementResponse
from pyspark.sql import SparkSession

# Configure logging for Databricks
structlog.configure(
    processors=[structlog.dev.ConsoleRenderer()],
    wrapper_class=structlog.make_filtering_bound_logger(20),  # INFO level
    logger_factory=structlog.PrintLoggerFactory(),
)
logger = structlog.get_logger(__name__)


class MetricCacheManager:
    """Manage metric caching and pre-aggregation in Databricks."""
    
    def __init__(self):
        self.client = WorkspaceClient()
        self.spark = SparkSession.getActiveSession() or SparkSession.builder.getOrCreate()
        self.volume_base_path = "/Volumes/semantic_layer/metrics"
        
        # Ensure cache tables exist
        self._ensure_cache_tables()
        
    def _ensure_cache_tables(self):
        """Ensure the cache tables exist in Unity Catalog."""
        try:
            # Create schema if not exists
            self.spark.sql("""
                CREATE SCHEMA IF NOT EXISTS semantic_layer.cache
                COMMENT 'Semantic layer caching tables'
            """)
            
            # Create query results cache table
            self.spark.sql("""
                CREATE TABLE IF NOT EXISTS semantic_layer.cache.query_results (
                    cache_key STRING,
                    query_sql STRING,
                    result_data STRING,
                    created_at TIMESTAMP,
                    expires_at TIMESTAMP,
                    hit_count BIGINT,
                    last_accessed TIMESTAMP,
                    metric_name STRING,
                    category STRING
                ) USING DELTA
                TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
            """)
            
            # Create cache performance metrics table
            self.spark.sql("""
                CREATE TABLE IF NOT EXISTS semantic_layer.cache.performance_metrics (
                    timestamp TIMESTAMP,
                    metric_name STRING,
                    cache_key STRING,
                    hit BOOLEAN,
                    execution_time_ms BIGINT,
                    result_size_bytes BIGINT,
                    user_email STRING
                ) USING DELTA
                PARTITIONED BY (date(timestamp))
                TBLPROPERTIES ('delta.autoOptimize.optimizeWrite' = 'true')
            """)
            
            logger.info("Cache tables initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize cache tables: {e}")
            raise
    
    def _load_metrics_from_volume(self, category: str = "production_models") -> List[Dict[str, Any]]:
        """Load all metrics from Unity Catalog Volume."""
        try:
            volume_path = f"{self.volume_base_path}/{category}"
            
            # List YAML files in volume
            files = self.client.files.list_directory_contents(directory_path=volume_path)
            metrics = []
            
            for file_info in files:
                if file_info.name.endswith('.yml') or file_info.name.endswith('.yaml'):
                    try:
                        # Download and parse YAML
                        file_content = self.client.files.download(
                            file_path=f"{volume_path}/{file_info.name}"
                        )
                        
                        import yaml
                        metric_data = yaml.safe_load(file_content.contents.decode('utf-8'))
                        metric_data['file_name'] = file_info.name
                        metric_data['category'] = category
                        metrics.append(metric_data)
                        
                    except Exception as e:
                        logger.warning(f"Failed to load metric {file_info.name}: {e}")
            
            logger.info(f"Loaded {len(metrics)} metrics from {category}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to load metrics from volume {category}: {e}")
            return []
    
    def _should_refresh_metric(self, metric: Dict[str, Any]) -> bool:
        """Determine if a metric should be refreshed based on cache config."""
        cache_config = metric.get('cache_config')
        if not cache_config:
            return False
            
        if not cache_config.get('pre_aggregate', False):
            return False
        
        # Check when metric was last refreshed
        metric_name = metric.get('name', 'unknown')
        cache_key = self._generate_cache_key(metric_name, metric.get('definition', {}).get('sql', ''))
        
        try:
            last_refresh = self.spark.sql(f"""
                SELECT MAX(created_at) as last_refresh
                FROM semantic_layer.cache.query_results 
                WHERE cache_key = '{cache_key}'
            """).collect()[0]['last_refresh']
            
            if not last_refresh:
                return True
                
            # Parse refresh frequency (e.g., "15m", "1h", "1d")
            refresh_freq = cache_config.get('refresh_frequency', '15m')
            refresh_interval = self._parse_time_interval(refresh_freq)
            
            return datetime.now() - last_refresh > refresh_interval
            
        except Exception as e:
            logger.warning(f"Failed to check refresh status for {metric_name}: {e}")
            return True
    
    def _parse_time_interval(self, interval_str: str) -> timedelta:
        """Parse time interval string (e.g., '15m', '1h', '2d') to timedelta."""
        import re
        
        match = re.match(r'(\d+)([smhd])', interval_str.lower())
        if not match:
            return timedelta(minutes=15)  # default
        
        value, unit = match.groups()
        value = int(value)
        
        if unit == 's':
            return timedelta(seconds=value)
        elif unit == 'm':
            return timedelta(minutes=value)
        elif unit == 'h':
            return timedelta(hours=value)
        elif unit == 'd':
            return timedelta(days=value)
        
        return timedelta(minutes=15)
    
    def _generate_cache_key(self, metric_name: str, sql: str) -> str:
        """Generate consistent cache key for metric."""
        content = f"{metric_name}:{sql}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _execute_sql_with_retry(self, sql: str, max_retries: int = 3) -> Optional[List[Dict[str, Any]]]:\n        \"\"\"Execute SQL with retry logic.\"\"\"\n        for attempt in range(max_retries):\n            try:\n                result = self.spark.sql(sql)\n                return [row.asDict() for row in result.collect()]\n                \n            except Exception as e:\n                logger.warning(f\"SQL execution attempt {attempt + 1} failed: {e}\")\n                if attempt == max_retries - 1:\n                    raise\n                time.sleep(2 ** attempt)  # exponential backoff\n        \n        return None\n    \n    def refresh_metric_cache(self, metric: Dict[str, Any]) -> bool:\n        \"\"\"Refresh cache for a specific metric.\"\"\"\n        try:\n            metric_name = metric.get('name', 'unknown')\n            definition = metric.get('definition', {})\n            sql = definition.get('sql')\n            \n            if not sql:\n                logger.warning(f\"No SQL found for metric {metric_name}\")\n                return False\n            \n            logger.info(f\"Refreshing cache for metric {metric_name}\")\n            \n            # Execute the metric query\n            start_time = time.time()\n            result_data = self._execute_sql_with_retry(sql)\n            execution_time_ms = int((time.time() - start_time) * 1000)\n            \n            if result_data is None:\n                logger.error(f\"Failed to execute query for metric {metric_name}\")\n                return False\n            \n            # Store in cache\n            cache_key = self._generate_cache_key(metric_name, sql)\n            result_json = json.dumps(result_data)\n            result_size = len(result_json.encode('utf-8'))\n            \n            # Determine TTL from cache config\n            cache_config = metric.get('cache_config', {})\n            ttl = cache_config.get('ttl', '1h')\n            ttl_interval = self._parse_time_interval(ttl)\n            expires_at = datetime.now() + ttl_interval\n            \n            # Insert/update cache entry\n            self.spark.sql(f\"\"\"\n                MERGE INTO semantic_layer.cache.query_results t\n                USING (SELECT \n                    '{cache_key}' as cache_key,\n                    '''{sql.replace(\"'\", \"''\")}''' as query_sql,\n                    '''{result_json.replace(\"'\", \"''\")}''' as result_data,\n                    current_timestamp() as created_at,\n                    timestamp '{expires_at.strftime(\"%Y-%m-%d %H:%M:%S\")}' as expires_at,\n                    CAST(1 as BIGINT) as hit_count,\n                    current_timestamp() as last_accessed,\n                    '{metric_name}' as metric_name,\n                    '{metric.get('category', 'unknown')}' as category\n                ) s\n                ON t.cache_key = s.cache_key\n                WHEN MATCHED THEN UPDATE SET\n                    result_data = s.result_data,\n                    created_at = s.created_at,\n                    expires_at = s.expires_at,\n                    last_accessed = s.last_accessed\n                WHEN NOT MATCHED THEN INSERT *\n            \"\"\")\n            \n            # Log performance metrics\n            self.spark.sql(f\"\"\"\n                INSERT INTO semantic_layer.cache.performance_metrics\n                VALUES (\n                    current_timestamp(),\n                    '{metric_name}',\n                    '{cache_key}',\n                    false,  -- This is a refresh, not a hit\n                    {execution_time_ms},\n                    {result_size},\n                    'system_cache_refresh'\n                )\n            \"\"\")\n            \n            logger.info(\n                f\"Successfully refreshed cache for {metric_name}\",\n                execution_time_ms=execution_time_ms,\n                result_size_bytes=result_size\n            )\n            \n            return True\n            \n        except Exception as e:\n            logger.error(f\"Failed to refresh cache for metric {metric_name}: {e}\")\n            return False\n    \n    def cleanup_expired_cache(self):\n        \"\"\"Remove expired cache entries.\"\"\"\n        try:\n            result = self.spark.sql(\"\"\"\n                DELETE FROM semantic_layer.cache.query_results \n                WHERE expires_at < current_timestamp()\n            \"\"\")\n            \n            logger.info(\"Cleaned up expired cache entries\")\n            \n        except Exception as e:\n            logger.error(f\"Failed to cleanup expired cache: {e}\")\n    \n    def get_cache_stats(self) -> Dict[str, Any]:\n        \"\"\"Get cache performance statistics.\"\"\"\n        try:\n            # Overall cache stats\n            stats = self.spark.sql(\"\"\"\n                SELECT \n                    COUNT(*) as total_entries,\n                    SUM(hit_count) as total_hits,\n                    AVG(hit_count) as avg_hits_per_entry,\n                    COUNT(CASE WHEN expires_at > current_timestamp() THEN 1 END) as active_entries,\n                    SUM(LENGTH(result_data)) as total_cache_size_bytes\n                FROM semantic_layer.cache.query_results\n            \"\"\").collect()[0].asDict()\n            \n            # Recent performance (last hour)\n            recent_perf = self.spark.sql(\"\"\"\n                SELECT \n                    COUNT(*) as total_requests,\n                    SUM(CASE WHEN hit THEN 1 ELSE 0 END) as cache_hits,\n                    AVG(execution_time_ms) as avg_execution_time_ms,\n                    AVG(result_size_bytes) as avg_result_size_bytes\n                FROM semantic_layer.cache.performance_metrics\n                WHERE timestamp > current_timestamp() - INTERVAL 1 HOUR\n            \"\"\").collect()[0].asDict()\n            \n            # Calculate hit rate\n            hit_rate = 0.0\n            if recent_perf['total_requests'] and recent_perf['total_requests'] > 0:\n                hit_rate = recent_perf['cache_hits'] / recent_perf['total_requests']\n            \n            return {\n                'timestamp': datetime.now().isoformat(),\n                'cache_stats': stats,\n                'recent_performance': recent_perf,\n                'hit_rate': hit_rate\n            }\n            \n        except Exception as e:\n            logger.error(f\"Failed to get cache stats: {e}\")\n            return {}\n    \n    def send_slack_alert(self, message: str, severity: str = \"info\"):\n        \"\"\"Send Slack alert (simplified - use webhook URL from environment).\"\"\"\n        try:\n            import requests\n            \n            webhook_url = os.getenv('SLACK_WEBHOOK_URL')\n            if not webhook_url:\n                logger.info(f\"Slack alert (no webhook configured): {message}\")\n                return\n            \n            color_map = {\n                \"info\": \"#36a64f\",\n                \"warning\": \"#ff9500\", \n                \"error\": \"#ff0000\",\n                \"critical\": \"#ff0000\"\n            }\n            \n            payload = {\n                \"attachments\": [{\n                    \"color\": color_map.get(severity, \"#36a64f\"),\n                    \"text\": message,\n                    \"ts\": time.time()\n                }]\n            }\n            \n            response = requests.post(webhook_url, json=payload, timeout=10)\n            response.raise_for_status()\n            \n            logger.info(f\"Sent Slack alert: {message}\")\n            \n        except Exception as e:\n            logger.warning(f\"Failed to send Slack alert: {e}\")\n\n\ndef main():\n    \"\"\"Main job execution.\"\"\"\n    logger.info(\"Starting cache refresh job\")\n    \n    try:\n        cache_manager = MetricCacheManager()\n        \n        # Load metrics that need refreshing\n        all_metrics = []\n        for category in [\"production_models\", \"staging_models\"]:\n            metrics = cache_manager._load_metrics_from_volume(category)\n            all_metrics.extend(metrics)\n        \n        # Filter metrics that need refreshing\n        metrics_to_refresh = [m for m in all_metrics if cache_manager._should_refresh_metric(m)]\n        \n        logger.info(f\"Found {len(metrics_to_refresh)} metrics to refresh\")\n        \n        # Refresh each metric\n        successful_refreshes = 0\n        failed_refreshes = 0\n        \n        for metric in metrics_to_refresh:\n            try:\n                if cache_manager.refresh_metric_cache(metric):\n                    successful_refreshes += 1\n                else:\n                    failed_refreshes += 1\n            except Exception as e:\n                logger.error(f\"Failed to refresh metric {metric.get('name', 'unknown')}: {e}\")\n                failed_refreshes += 1\n        \n        # Cleanup expired cache\n        cache_manager.cleanup_expired_cache()\n        \n        # Get performance stats\n        stats = cache_manager.get_cache_stats()\n        hit_rate = stats.get('hit_rate', 0.0)\n        \n        # Send alerts if needed\n        if hit_rate < 0.7:  # Less than 70% hit rate\n            cache_manager.send_slack_alert(\n                f\"🚨 Cache hit rate dropped to {hit_rate:.1%}. Consider reviewing cache configuration.\",\n                \"warning\"\n            )\n        \n        if failed_refreshes > 0:\n            cache_manager.send_slack_alert(\n                f\"⚠️ {failed_refreshes} metric cache refreshes failed. Check job logs for details.\",\n                \"warning\"\n            )\n        \n        # Success summary\n        summary_msg = f\"✅ Cache refresh completed: {successful_refreshes} successful, {failed_refreshes} failed. Hit rate: {hit_rate:.1%}\"\n        logger.info(summary_msg)\n        \n        if successful_refreshes > 0:\n            cache_manager.send_slack_alert(summary_msg, \"info\")\n        \n        logger.info(\"Cache refresh job completed successfully\")\n        \n    except Exception as e:\n        error_msg = f\"❌ Cache refresh job failed: {str(e)}\"\n        logger.error(error_msg)\n        \n        try:\n            cache_manager = MetricCacheManager()\n            cache_manager.send_slack_alert(error_msg, \"critical\")\n        except:\n            pass  # Don't fail the job if Slack alert fails\n        \n        raise\n\n\nif __name__ == \"__main__\":\n    main()