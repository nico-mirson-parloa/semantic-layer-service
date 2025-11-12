"""Sample data fixtures for testing."""

SAMPLE_SEMANTIC_MODELS = {
    "sales_metrics": {
        "name": "sales_metrics",
        "description": "Core sales metrics and KPIs",
        "model": "main.gold.sales_fact",
        "entities": [
            {"name": "order_id", "type": "primary", "expr": "order_id"},
            {"name": "customer_id", "type": "foreign", "expr": "customer_id"},
            {"name": "product_id", "type": "foreign", "expr": "product_id"}
        ],
        "dimensions": [
            {
                "name": "order_date",
                "type": "time", 
                "expr": "order_date",
                "time_granularity": ["day", "week", "month", "quarter", "year"]
            },
            {
                "name": "customer_region",
                "type": "categorical",
                "expr": "customer_region"
            },
            {
                "name": "product_category", 
                "type": "categorical",
                "expr": "product_category"
            }
        ],
        "measures": [
            {
                "name": "revenue",
                "agg": "sum",
                "expr": "order_amount",
                "description": "Total revenue from orders"
            },
            {
                "name": "quantity_sold",
                "agg": "sum", 
                "expr": "quantity",
                "description": "Total quantity sold"
            },
            {
                "name": "order_count",
                "agg": "count",
                "expr": "order_id",
                "description": "Number of orders"
            },
            {
                "name": "unique_customers",
                "agg": "count_distinct",
                "expr": "customer_id",
                "description": "Number of unique customers"
            }
        ],
        "metrics": [
            {
                "name": "total_revenue",
                "type": "simple",
                "measure": "revenue",
                "description": "Total revenue across all orders"
            },
            {
                "name": "average_order_value",
                "type": "ratio",
                "numerator": "revenue", 
                "denominator": "order_count",
                "description": "Average revenue per order"
            },
            {
                "name": "revenue_per_customer",
                "type": "ratio",
                "numerator": "revenue",
                "denominator": "unique_customers", 
                "description": "Average revenue per customer"
            }
        ]
    },
    
    "customer_metrics": {
        "name": "customer_metrics",
        "description": "Customer behavior and engagement metrics",
        "model": "main.gold.customer_fact",
        "entities": [
            {"name": "customer_id", "type": "primary", "expr": "customer_id"}
        ],
        "dimensions": [
            {
                "name": "signup_date",
                "type": "time",
                "expr": "signup_date", 
                "time_granularity": ["day", "week", "month"]
            },
            {
                "name": "customer_tier",
                "type": "categorical",
                "expr": "tier"
            },
            {
                "name": "acquisition_channel",
                "type": "categorical", 
                "expr": "acquisition_channel"
            }
        ],
        "measures": [
            {
                "name": "active_customers",
                "agg": "count_distinct",
                "expr": "customer_id",
                "description": "Number of active customers"
            },
            {
                "name": "total_lifetime_value",
                "agg": "sum",
                "expr": "lifetime_value",
                "description": "Total customer lifetime value"
            }
        ],
        "metrics": [
            {
                "name": "customer_count",
                "type": "simple", 
                "measure": "active_customers",
                "description": "Total number of customers"
            },
            {
                "name": "average_lifetime_value",
                "type": "ratio",
                "numerator": "total_lifetime_value",
                "denominator": "active_customers",
                "description": "Average customer lifetime value"
            }
        ]
    }
}

SAMPLE_TABLE_METADATA = [
    {
        "catalog_name": "main",
        "schema_name": "gold", 
        "table_name": "sales_fact",
        "table_type": "TABLE",
        "data_source_format": "DELTA",
        "columns": [
            {"column_name": "order_id", "data_type": "bigint", "is_nullable": False},
            {"column_name": "customer_id", "data_type": "bigint", "is_nullable": False},
            {"column_name": "product_id", "data_type": "bigint", "is_nullable": False},
            {"column_name": "order_date", "data_type": "date", "is_nullable": False},
            {"column_name": "order_amount", "data_type": "decimal(10,2)", "is_nullable": False},
            {"column_name": "quantity", "data_type": "int", "is_nullable": False},
            {"column_name": "customer_region", "data_type": "string", "is_nullable": True},
            {"column_name": "product_category", "data_type": "string", "is_nullable": True}
        ]
    },
    {
        "catalog_name": "main",
        "schema_name": "gold",
        "table_name": "customer_fact", 
        "table_type": "TABLE",
        "data_source_format": "DELTA",
        "columns": [
            {"column_name": "customer_id", "data_type": "bigint", "is_nullable": False},
            {"column_name": "signup_date", "data_type": "date", "is_nullable": False},
            {"column_name": "tier", "data_type": "string", "is_nullable": False},
            {"column_name": "acquisition_channel", "data_type": "string", "is_nullable": True},
            {"column_name": "lifetime_value", "data_type": "decimal(12,2)", "is_nullable": True}
        ]
    }
]

SAMPLE_QUERY_RESULTS = {
    "revenue_by_date": {
        "columns": ["order_date", "total_revenue", "order_count"],
        "data": [
            ["2024-01-01", 1500.50, 12],
            ["2024-01-02", 2300.75, 18],
            ["2024-01-03", 1850.25, 15],
            ["2024-01-04", 2100.00, 21]
        ],
        "row_count": 4,
        "execution_time": 0.45
    },
    
    "revenue_by_category": {
        "columns": ["product_category", "total_revenue", "avg_order_value"],
        "data": [
            ["Electronics", 15000.50, 125.75],
            ["Books", 8500.25, 45.50], 
            ["Clothing", 12750.00, 85.25],
            ["Home & Garden", 9200.75, 98.50]
        ],
        "row_count": 4,
        "execution_time": 0.32
    }
}

SAMPLE_GENIE_RESPONSES = {
    "successful_query": {
        "statement_id": "stmt-123-456-789",
        "status": {"state": "SUCCEEDED"},
        "result": {
            "data_array": [
                ["SELECT", "SUM(order_amount) as total_revenue", ""],
                ["FROM", "main.gold.sales_fact", ""], 
                ["WHERE", "order_date >= '2024-01-01'", ""],
                ["GROUP BY", "product_category", ""],
                ["ORDER BY", "total_revenue DESC", ""]
            ]
        },
        "manifest": {
            "schema": {
                "columns": [
                    {"name": "query_type", "type_name": "STRING"},
                    {"name": "sql_fragment", "type_name": "STRING"}, 
                    {"name": "condition", "type_name": "STRING"}
                ]
            }
        }
    },
    
    "failed_query": {
        "statement_id": "stmt-999-888-777", 
        "status": {"state": "FAILED"},
        "result": {
            "data_array": []
        },
        "error": {
            "error_code": "INVALID_PARAMETER_VALUE",
            "message": "Table 'invalid_table' not found"
        }
    }
}

SAMPLE_CONVERSATIONS = [
    {
        "id": "conv-abc-123",
        "title": "Sales Analysis Q1 2024", 
        "created_at": "2024-01-15T10:30:00Z",
        "messages": [
            {
                "id": "msg-001",
                "content": "Show me total revenue by product category for Q1 2024",
                "role": "user",
                "timestamp": "2024-01-15T10:30:00Z"
            },
            {
                "id": "msg-002", 
                "content": "Here's the revenue breakdown by category...",
                "role": "assistant",
                "timestamp": "2024-01-15T10:30:15Z",
                "sql": "SELECT product_category, SUM(order_amount) as revenue FROM main.gold.sales_fact WHERE order_date BETWEEN '2024-01-01' AND '2024-03-31' GROUP BY product_category ORDER BY revenue DESC"
            }
        ]
    }
]