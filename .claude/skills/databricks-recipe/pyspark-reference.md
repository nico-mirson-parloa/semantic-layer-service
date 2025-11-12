# PySpark Patterns Reference

## DataFrame Creation

```python
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, IntegerType

schema = StructType([
    StructField("id", IntegerType(), nullable=False),
    StructField("name", StringType(), nullable=True),
])

df = spark.createDataFrame(data, schema=schema)
```

## Transformations

```python
df_transformed = (
    df
    .withColumn("new_col", F.col("old_col") + 1)
    .filter(F.col("status") == "active")
    .groupBy("category")
    .agg(
        F.count("*").alias("count"),
        F.sum("amount").alias("total_amount"),
    )
)
```

## Window Functions

```python
from pyspark.sql.window import Window

window_spec = Window.partitionBy("user_id").orderBy("timestamp")

df_windowed = df.withColumn(
    "row_num",
    F.row_number().over(window_spec)
)
```

## JSON Handling

```python
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StructField, StringType

json_schema = StructType([
    StructField("field1", StringType()),
    StructField("field2", StringType()),
])

df_parsed = df.withColumn(
    "parsed_json",
    from_json(col("json_string"), json_schema)
)

# Access nested fields
df_with_fields = df_parsed.select(
    "id",
    col("parsed_json.field1").alias("field1"),
    col("parsed_json.field2").alias("field2"),
)
```

## Common Operations

| Operation | Code |
|-----------|------|
| Filter | `df.filter(F.col("x") > 10)` |
| Select | `df.select("col1", "col2")` |
| Rename | `df.withColumnRenamed("old", "new")` |
| Drop | `df.drop("col1", "col2")` |
| Distinct | `df.distinct()` |
| Join | `df1.join(df2, on="key", how="inner")` |
| Union | `df1.union(df2)` |
| Sort | `df.orderBy("col1", F.desc("col2"))` |

## DQX Integration Example

```python
from databricks.labs.dqx import DQX
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.getOrCreate()

# Load data
df = spark.table("schema.table_name")

# Define inline checks
dqx = DQX(spark)
results = dqx.check(
    df,
    [
        ("no_nulls_in_id", "id IS NOT NULL", "critical"),
        ("positive_amounts", "amount > 0", "error"),
        ("valid_dates", "date >= '2020-01-01'", "warning"),
    ]
)

# Or load from YAML
results = dqx.run_checks("quality_checks.yml")

# Handle results
if results.has_critical_failures():
    raise Exception(f"Critical failures: {results.critical_count}")

# Write results
results.write_to_table("data_quality.check_results")

# Get detailed failure info
failures_df = results.get_failures()
failures_df.show()
```

## Error Handling Pattern

```python
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def transform_data(
    input_table: str,
    output_table: str,
    checkpoint_location: str,
) -> Optional[str]:
    """Transform data from input to output table.

    Args:
        input_table: Full path to input table
        output_table: Full path to output table
        checkpoint_location: Path for streaming checkpoint

    Returns:
        Output table name if successful, None otherwise
    """
    try:
        df = spark.table(input_table)

        df_transformed = (
            df
            .withColumn("processed_at", F.current_timestamp())
            .filter(F.col("status") == "active")
        )

        (
            df_transformed
            .write
            .format("delta")
            .mode("overwrite")
            .option("checkpointLocation", checkpoint_location)
            .saveAsTable(output_table)
        )

        logger.info(f"Successfully transformed {input_table} to {output_table}")
        return output_table

    except Exception as e:
        logger.error(f"Failed to transform {input_table}: {str(e)}")
        raise
```
