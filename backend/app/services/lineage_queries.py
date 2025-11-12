"""
SQL query templates for extracting lineage from Databricks Unity Catalog system tables.

This module contains parameterized SQL query templates for extracting table and column-level
lineage using recursive CTEs (available in Databricks Runtime 17.0+ and DBSQL 2025.20+).

All queries follow Databricks SQL style guide:
- Lowercase keywords and identifiers
- Trailing commas in SELECT lists
- Group by all instead of column lists
- Parameterized with :parameter_name syntax
- 4-space indentation

Example usage:
    query = DOWNSTREAM_LINEAGE_RECURSIVE
    params = {
        "table_name": "catalog.schema.table",
        "days_back": 90,
        "max_depth": 5
    }
    results = spark.sql(query, **params)
"""

from typing import Final

# Downstream lineage recursive CTE
# Finds all tables that derive from the specified source table
# Uses recursive traversal with cycle detection and depth limiting
# Note: MAX RECURSION LEVEL is hardcoded to 100 (cannot be parameterized in Databricks SQL)
# Filter results by min_depth column after query execution to control depth
DOWNSTREAM_LINEAGE_RECURSIVE: Final[str] = """
with recursive lineage_paths (
    source_table,
    target_table,
    source_type,
    target_type,
    depth,
    path,
    statement_id,
    event_time
) max recursion level 100 as (
    -- Base case: direct downstream dependencies
    select
        source_table_full_name as source_table,
        target_table_full_name as target_table,
        source_type,
        target_type,
        1 as depth,
        array(struct(source_table_full_name as source, target_table_full_name as target)) as path,
        statement_id,
        event_time,
    from system.access.table_lineage
    where
        true
        and source_table_full_name = :table_name
        and event_date > current_date() - interval :days_back days
        and target_table_full_name is not null

    union all

    -- Recursive case: traverse downstream
    select
        lineage.source_table_full_name as source_table,
        lineage.target_table_full_name as target_table,
        lineage.source_type,
        lineage.target_type,
        paths.depth + 1 as depth,
        array_append(paths.path, struct(lineage.source_table_full_name as source, lineage.target_table_full_name as target)) as path,
        lineage.statement_id,
        lineage.event_time,
    from system.access.table_lineage as lineage
    inner join lineage_paths as paths
        on lineage.source_table_full_name = paths.target_table
    where
        true
        and lineage.event_date > current_date() - interval :days_back days
        and lineage.target_table_full_name is not null
        and not array_contains(
            paths.path,
            struct(lineage.source_table_full_name as source, lineage.target_table_full_name as target)
        )
),

deduped_lineage as (
    select
        source_table,
        target_table,
        source_type,
        target_type,
        min(depth) as min_depth,
        max(depth) as max_depth,
        count(*) as occurrence_count,
        max(event_time) as last_seen,
        array_agg(distinct statement_id) as statement_ids,
    from lineage_paths
    group by all
)

select *
from deduped_lineage
order by min_depth, source_table, target_table
"""

# Upstream lineage recursive CTE
# Finds all source tables that contribute to the specified target table
# Uses recursive traversal with cycle detection and depth limiting
# Note: MAX RECURSION LEVEL is hardcoded to 100 (cannot be parameterized in Databricks SQL)
# Filter results by min_depth column after query execution to control depth
UPSTREAM_LINEAGE_RECURSIVE: Final[str] = """
with recursive lineage_paths (
    source_table,
    target_table,
    source_type,
    target_type,
    depth,
    path,
    statement_id,
    event_time
) max recursion level 100 as (
    -- Base case: direct upstream dependencies
    select
        source_table_full_name as source_table,
        target_table_full_name as target_table,
        source_type,
        target_type,
        1 as depth,
        array(struct(source_table_full_name as source, target_table_full_name as target)) as path,
        statement_id,
        event_time,
    from system.access.table_lineage
    where
        true
        and target_table_full_name = :table_name
        and event_date > current_date() - interval :days_back days
        and source_table_full_name is not null

    union all

    -- Recursive case: traverse upstream
    select
        lineage.source_table_full_name as source_table,
        lineage.target_table_full_name as target_table,
        lineage.source_type,
        lineage.target_type,
        paths.depth + 1 as depth,
        array_append(paths.path, struct(lineage.source_table_full_name as source, lineage.target_table_full_name as target)) as path,
        lineage.statement_id,
        lineage.event_time,
    from system.access.table_lineage as lineage
    inner join lineage_paths as paths
        on lineage.target_table_full_name = paths.source_table
    where
        true
        and lineage.event_date > current_date() - interval :days_back days
        and lineage.source_table_full_name is not null
        and not array_contains(
            paths.path,
            struct(lineage.source_table_full_name as source, lineage.target_table_full_name as target)
        )
),

deduped_lineage as (
    select
        source_table,
        target_table,
        source_type,
        target_type,
        min(depth) as min_depth,
        max(depth) as max_depth,
        count(*) as occurrence_count,
        max(event_time) as last_seen,
        array_agg(distinct statement_id) as statement_ids,
    from lineage_paths
    group by all
)

select *
from deduped_lineage
order by min_depth desc, source_table, target_table
"""

# Column-level lineage query
# Extracts column-to-column dependencies for a specific table
# Includes transformation information and confidence scores
COLUMN_LINEAGE_QUERY: Final[str] = """
with column_lineage_base as (
    select
        source_table_full_name,
        source_column_name,
        target_table_full_name,
        target_column_name,
        source_type,
        target_type,
        event_time,
        statement_id,
        cast(entity_metadata as string) as entity_metadata,
    from system.access.column_lineage
    where
        true
        and target_table_full_name = :table_name
        and event_date > current_date() - interval :days_back days
),

aggregated_lineage as (
    select
        source_table_full_name,
        source_column_name,
        target_table_full_name,
        target_column_name,
        source_type,
        target_type,
        count(*) as reference_count,
        max(event_time) as last_seen,
        min(event_time) as first_seen,
        array_agg(distinct statement_id) as statement_ids,
        max(entity_metadata) as entity_metadata,
    from column_lineage_base
    group by all
)

select *
from aggregated_lineage
order by target_column_name, source_table_full_name, source_column_name
"""

# Lineage with query history
# Joins lineage with query execution details for richer context
# Includes query text, user, duration, and execution metadata
LINEAGE_WITH_QUERY_HISTORY: Final[str] = """
with lineage_base as (
    select
        source_table_full_name,
        target_table_full_name,
        source_type,
        target_type,
        statement_id,
        event_time,
        event_id,
        cast(entity_metadata as string) as entity_metadata,
    from system.access.table_lineage
    where
        true
        and (
            source_table_full_name = :table_name
            or target_table_full_name = :table_name
        )
        and event_date > current_date() - interval :days_back days
),

query_details as (
    select
        statement_id,
        statement_text,
        executed_by,
        start_time,
        end_time,
        total_task_duration_ms,
        rows_produced,
        execution_status,
        error_message,
        warehouse_id,
        compute_type,
    from system.query.history
    where
        true
        and start_time > current_date() - interval :days_back days
        and statement_type in ('CREATE_TABLE', 'CREATE_VIEW', 'MERGE', 'INSERT')
),

lineage_with_queries as (
    select
        lineage.source_table_full_name,
        lineage.target_table_full_name,
        lineage.source_type,
        lineage.target_type,
        lineage.event_time,
        lineage.event_id,
        lineage.entity_metadata,
        queries.statement_text,
        queries.executed_by,
        queries.start_time as query_start_time,
        queries.end_time as query_end_time,
        queries.total_task_duration_ms,
        queries.rows_produced,
        queries.execution_status,
        queries.error_message,
        queries.warehouse_id,
        queries.compute_type,
    from lineage_base as lineage
    left join query_details as queries
        on lineage.statement_id = queries.statement_id
)

select *
from lineage_with_queries
order by event_time desc
"""

# External table lineage by storage path
# Finds lineage relationships for external tables based on their storage locations
# Useful for tracking data flows across different storage systems
EXTERNAL_TABLE_LINEAGE: Final[str] = """
with external_tables as (
    select
        table_catalog,
        table_schema,
        table_name,
        concat(table_catalog, '.', table_schema, '.', table_name) as full_table_name,
        table_type,
        data_source_format,
        location,
        created,
        last_altered,
    from system.information_schema.tables
    where
        true
        and table_type = 'EXTERNAL'
        and table_catalog = :catalog
        and location is not null
),

matching_external_tables as (
    select
        ext.full_table_name,
        ext.table_type,
        ext.data_source_format,
        ext.location,
        ext.created,
        ext.last_altered,
    from external_tables as ext
    where
        ext.location like concat('%', :storage_path, '%')
),

lineage_relationships as (
    select
        ext.full_table_name as external_table,
        ext.location as storage_path,
        ext.data_source_format,
        lineage.source_table_full_name,
        lineage.target_table_full_name,
        lineage.source_type,
        lineage.target_type,
        lineage.event_time,
        lineage.statement_id,
    from matching_external_tables as ext
    left join system.access.table_lineage as lineage
        on (
            lineage.source_table_full_name = ext.full_table_name
            or lineage.target_table_full_name = ext.full_table_name
        )
        and lineage.event_date > current_date() - interval :days_back days
)

select *
from lineage_relationships
order by external_table, event_time desc
"""

# Simple test query to verify access to system.access.table_lineage
# Use this to debug connectivity and data availability issues
SIMPLE_LINEAGE_TEST: Final[str] = """
select
    source_table_full_name,
    target_table_full_name,
    source_type,
    target_type,
    event_time
from system.access.table_lineage
where
    true
    and (
        source_table_full_name = :table_name
        or target_table_full_name = :table_name
    )
    and event_date > current_date() - interval :days_back days
order by event_time desc
limit 100
"""

# Example parameter dictionaries for each query
# These demonstrate the expected parameter structure for each query template
EXAMPLE_PARAMS: Final[dict[str, dict[str, str | int]]] = {
    "downstream_lineage": {
        "table_name": "catalog.schema.table",
        "days_back": 90,
    },
    "upstream_lineage": {
        "table_name": "catalog.schema.table",
        "days_back": 90,
    },
    "column_lineage": {
        "table_name": "catalog.schema.table",
        "days_back": 90,
    },
    "lineage_with_query_history": {
        "table_name": "catalog.schema.table",
        "days_back": 90,
    },
    "external_table_lineage": {
        "catalog": "catalog_name",
        "storage_path": "s3://bucket/path",
        "days_back": 90,
    },
}
