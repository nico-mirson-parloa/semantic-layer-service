-- Databricks SQL Dashboard: Semantic Layer Monitoring
-- 
-- This file contains SQL queries for creating monitoring dashboards in Databricks SQL.
-- Create a new dashboard and add these queries as visualizations.

-- =============================================================================
-- SYSTEM HEALTH OVERVIEW
-- =============================================================================

-- Query 1: Overall System Status (Last 24 Hours)
-- Visualization: Counter/KPI cards
SELECT 
  COUNT(DISTINCT component) as total_components,
  SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count,
  SUM(CASE WHEN status = 'healthy' THEN 1 ELSE 0 END) as healthy_count,
  AVG(response_time_ms) as avg_response_time_ms,
  MAX(timestamp) as last_check
FROM semantic_layer.monitoring.system_health
WHERE timestamp > current_timestamp() - INTERVAL 24 HOURS;

-- Query 2: System Health Timeline (Last 24 Hours)  
-- Visualization: Line chart (X: time, Y: response_time_ms, Series: component)
SELECT 
  date_trunc('hour', timestamp) as hour,
  component,
  AVG(response_time_ms) as avg_response_time_ms,
  COUNT(*) as check_count,
  SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count
FROM semantic_layer.monitoring.system_health
WHERE timestamp > current_timestamp() - INTERVAL 24 HOURS
GROUP BY date_trunc('hour', timestamp), component
ORDER BY hour DESC;

-- Query 3: Recent Errors (Last 2 Hours)
-- Visualization: Table
SELECT 
  timestamp,
  component,
  error_message,
  details
FROM semantic_layer.monitoring.system_health
WHERE timestamp > current_timestamp() - INTERVAL 2 HOURS
  AND status = 'error'
ORDER BY timestamp DESC
LIMIT 20;

-- =============================================================================
-- VOLUME HEALTH MONITORING  
-- =============================================================================

-- Query 4: Volume Accessibility Status
-- Visualization: Bar chart or table
SELECT 
  SUBSTRING_INDEX(volume_path, '/', -1) as category,
  accessible,
  file_count,
  ROUND(total_size_bytes / 1024 / 1024, 2) as size_mb,
  last_modified,
  MAX(timestamp) as last_checked
FROM semantic_layer.monitoring.volume_health
WHERE timestamp > current_timestamp() - INTERVAL 1 HOUR
GROUP BY volume_path, accessible, file_count, total_size_bytes, last_modified
ORDER BY last_checked DESC;

-- Query 5: Volume File Count Trend (Last 7 Days)
-- Visualization: Line chart (X: date, Y: file_count, Series: volume category)
SELECT 
  date(timestamp) as date,
  SUBSTRING_INDEX(volume_path, '/', -1) as category,
  AVG(file_count) as avg_file_count,
  MAX(file_count) as max_file_count
FROM semantic_layer.monitoring.volume_health
WHERE timestamp > current_timestamp() - INTERVAL 7 DAYS
  AND accessible = true
GROUP BY date(timestamp), SUBSTRING_INDEX(volume_path, '/', -1)
ORDER BY date DESC, category;

-- =============================================================================
-- CACHE PERFORMANCE METRICS
-- =============================================================================

-- Query 6: Cache Performance Summary (Last 24 Hours)
-- Visualization: KPI cards
SELECT 
  COUNT(*) as total_requests,
  SUM(CASE WHEN hit THEN 1 ELSE 0 END) as cache_hits,
  ROUND(SUM(CASE WHEN hit THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as hit_rate_percent,
  AVG(execution_time_ms) as avg_execution_time_ms,
  AVG(result_size_bytes / 1024) as avg_result_size_kb,
  COUNT(DISTINCT metric_name) as unique_metrics_accessed
FROM semantic_layer.cache.performance_metrics
WHERE timestamp > current_timestamp() - INTERVAL 24 HOURS;

-- Query 7: Cache Hit Rate Trend (Last 7 Days)
-- Visualization: Line chart (X: date, Y: hit_rate_percent)
SELECT 
  date_trunc('hour', timestamp) as hour,
  COUNT(*) as total_requests,
  SUM(CASE WHEN hit THEN 1 ELSE 0 END) as cache_hits,
  ROUND(SUM(CASE WHEN hit THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as hit_rate_percent,
  AVG(execution_time_ms) as avg_execution_time_ms
FROM semantic_layer.cache.performance_metrics
WHERE timestamp > current_timestamp() - INTERVAL 7 DAYS
GROUP BY date_trunc('hour', timestamp)
ORDER BY hour DESC;

-- Query 8: Top Cached Metrics (Current Active Cache)
-- Visualization: Bar chart (X: metric_name, Y: hit_count)
SELECT 
  metric_name,
  category,
  hit_count,
  ROUND(LENGTH(result_data) / 1024, 2) as cache_size_kb,
  created_at,
  expires_at,
  CASE 
    WHEN expires_at > current_timestamp() THEN 'Active'
    ELSE 'Expired'
  END as status
FROM semantic_layer.cache.query_results
ORDER BY hit_count DESC
LIMIT 20;

-- Query 9: Cache Miss Analysis (Last 24 Hours)
-- Visualization: Table showing metrics with low hit rates
SELECT 
  metric_name,
  COUNT(*) as total_requests,
  SUM(CASE WHEN hit THEN 1 ELSE 0 END) as hits,
  ROUND(SUM(CASE WHEN hit THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as hit_rate_percent,
  AVG(execution_time_ms) as avg_execution_time_ms,
  MAX(timestamp) as last_accessed
FROM semantic_layer.cache.performance_metrics
WHERE timestamp > current_timestamp() - INTERVAL 24 HOURS
GROUP BY metric_name
HAVING COUNT(*) >= 5  -- Only show metrics with at least 5 requests
ORDER BY hit_rate_percent ASC, total_requests DESC
LIMIT 15;

-- =============================================================================
-- METRIC USAGE ANALYTICS
-- =============================================================================

-- Query 10: Most Popular Metrics (Last 7 Days)
-- Visualization: Bar chart (X: metric_name, Y: request_count)
SELECT 
  metric_name,
  COUNT(*) as request_count,
  COUNT(DISTINCT user_email) as unique_users,
  AVG(execution_time_ms) as avg_execution_time_ms,
  MAX(timestamp) as last_accessed
FROM semantic_layer.cache.performance_metrics
WHERE timestamp > current_timestamp() - INTERVAL 7 DAYS
GROUP BY metric_name
ORDER BY request_count DESC
LIMIT 20;

-- Query 11: User Activity (Last 7 Days)
-- Visualization: Bar chart (X: user, Y: query_count)
SELECT 
  COALESCE(user_email, 'system') as user,
  COUNT(*) as query_count,
  COUNT(DISTINCT metric_name) as unique_metrics,
  AVG(execution_time_ms) as avg_execution_time_ms,
  MAX(timestamp) as last_activity
FROM semantic_layer.cache.performance_metrics
WHERE timestamp > current_timestamp() - INTERVAL 7 DAYS
  AND user_email != 'system_cache_refresh'
GROUP BY user_email
ORDER BY query_count DESC
LIMIT 15;

-- Query 12: Daily Usage Pattern (Last 30 Days)
-- Visualization: Line chart (X: date, Y: query_count)
SELECT 
  date(timestamp) as date,
  COUNT(*) as total_queries,
  COUNT(DISTINCT metric_name) as unique_metrics,
  COUNT(DISTINCT user_email) as active_users,
  AVG(execution_time_ms) as avg_execution_time_ms
FROM semantic_layer.cache.performance_metrics
WHERE timestamp > current_timestamp() - INTERVAL 30 DAYS
  AND user_email != 'system_cache_refresh'
GROUP BY date(timestamp)
ORDER BY date DESC;

-- =============================================================================
-- PERFORMANCE MONITORING
-- =============================================================================

-- Query 13: Slowest Queries (Last 24 Hours)  
-- Visualization: Table
SELECT 
  metric_name,
  user_email,
  execution_time_ms,
  result_size_bytes,
  timestamp,
  hit as was_cache_hit
FROM semantic_layer.cache.performance_metrics
WHERE timestamp > current_timestamp() - INTERVAL 24 HOURS
  AND execution_time_ms > 1000  -- Slower than 1 second
ORDER BY execution_time_ms DESC
LIMIT 20;

-- Query 14: Performance Trend by Hour (Last 7 Days)
-- Visualization: Line chart (X: hour_of_day, Y: avg_execution_time_ms)
SELECT 
  EXTRACT(hour from timestamp) as hour_of_day,
  AVG(execution_time_ms) as avg_execution_time_ms,
  COUNT(*) as request_count,
  ROUND(AVG(result_size_bytes / 1024), 2) as avg_result_size_kb
FROM semantic_layer.cache.performance_metrics
WHERE timestamp > current_timestamp() - INTERVAL 7 DAYS
GROUP BY EXTRACT(hour from timestamp)
ORDER BY hour_of_day;

-- =============================================================================
-- MONITORING METRICS SUMMARY
-- =============================================================================

-- Query 15: Performance KPIs Summary (Real-time)
-- Visualization: Counter cards for dashboard header
WITH recent_performance AS (
  SELECT 
    COUNT(*) as requests_last_hour,
    AVG(execution_time_ms) as avg_response_time,
    ROUND(SUM(CASE WHEN hit THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as cache_hit_rate
  FROM semantic_layer.cache.performance_metrics
  WHERE timestamp > current_timestamp() - INTERVAL 1 HOUR
),
system_status AS (
  SELECT 
    COUNT(DISTINCT component) as components_monitored,
    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as components_with_errors
  FROM semantic_layer.monitoring.system_health
  WHERE timestamp > current_timestamp() - INTERVAL 15 MINUTES
),
volume_status AS (
  SELECT 
    COUNT(DISTINCT volume_path) as total_volumes,
    SUM(CASE WHEN accessible THEN 0 ELSE 1 END) as inaccessible_volumes,
    SUM(file_count) as total_files
  FROM semantic_layer.monitoring.volume_health
  WHERE timestamp > current_timestamp() - INTERVAL 15 MINUTES
)
SELECT 
  rp.requests_last_hour,
  rp.avg_response_time,
  rp.cache_hit_rate,
  ss.components_monitored,
  ss.components_with_errors,
  vs.total_volumes,
  vs.inaccessible_volumes,
  vs.total_files,
  CASE 
    WHEN ss.components_with_errors > 0 OR vs.inaccessible_volumes > 0 THEN 'Warning'
    ELSE 'Healthy'
  END as overall_status
FROM recent_performance rp
CROSS JOIN system_status ss  
CROSS JOIN volume_status vs;

-- =============================================================================
-- ALERTING QUERIES (for scheduled alerts)
-- =============================================================================

-- Query 16: Critical Issues (for alerting)
-- Run this query every 5 minutes to identify issues requiring immediate attention
SELECT 
  'volume_inaccessible' as alert_type,
  CONCAT('Volume ', SUBSTRING_INDEX(volume_path, '/', -1), ' is not accessible') as message,
  'critical' as severity,
  timestamp
FROM semantic_layer.monitoring.volume_health
WHERE timestamp > current_timestamp() - INTERVAL 10 MINUTES
  AND accessible = false

UNION ALL

SELECT 
  'low_cache_hit_rate' as alert_type,
  CONCAT('Cache hit rate dropped to ', ROUND(hit_rate * 100, 1), '%') as message,
  'warning' as severity,
  current_timestamp() as timestamp
FROM (
  SELECT 
    SUM(CASE WHEN hit THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as hit_rate
  FROM semantic_layer.cache.performance_metrics
  WHERE timestamp > current_timestamp() - INTERVAL 1 HOUR
) cache_perf
WHERE hit_rate < 0.7

UNION ALL

SELECT 
  'high_error_rate' as alert_type,
  CONCAT('High error rate detected for component: ', component) as message,
  'error' as severity,
  MAX(timestamp) as timestamp
FROM semantic_layer.monitoring.system_health
WHERE timestamp > current_timestamp() - INTERVAL 15 MINUTES
  AND status = 'error'
GROUP BY component
HAVING COUNT(*) >= 3;  -- 3 or more errors in 15 minutes