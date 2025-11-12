# Databricks SQL Reference

## SQL Style Guide

**Indentation:** 4 spaces always

**Keywords:** Lowercase
```sql
select column_name
from table_name
where condition
```

**Trailing commas:** Always
```sql
select
    column_a,
    column_b,
    column_c,  -- Trailing comma
from table_name
```

**Where clause format:**
```sql
-- Multiple conditions: start with true
where
    true
    and condition1
    and condition2

-- Single condition: one line
where condition1
```

**Final CTE pattern:**
```sql
with intermediate as (
    select * from source
),

final_cte as (
    select * from intermediate
)

select *
from final_cte
```

**Nested field access:**
```sql
-- JSON strings: use :
event_data:user_id

-- Structs: use .
struct_column.field_name
```

## Common Databricks SQL Functions

| Function | Purpose | Example |
|----------|---------|---------|
| `cast(x as type)` | Type conversion | `cast(amount as decimal(10,2))` |
| `coalesce(a, b)` | Null handling | `coalesce(value, 0)` |
| `date_trunc('day', ts)` | Truncate timestamp | `date_trunc('day', event_timestamp)` |
| `row_number() over (...)` | Window function | `row_number() over (partition by id order by ts)` |
| `first_value(x) over (...)` | First in window | `first_value(x) over (partition by id order by ts)` |
| `lag(x, 1) over (...)` | Previous value | `lag(x, 1) over (partition by id order by ts)` |
| `array_contains(arr, val)` | Array membership | `array_contains(tags, 'important')` |
| `explode(array)` | Flatten array | `explode(items) as item` |

## Activity Schema Advanced Examples

**Complex temporal joins:**
```sql
with conversation_starts as (
    select
        conversation_id,
        min(event_timestamp) as start_time,
        event_data:channel as channel
    from bronze.amp_all_events_v2
    where event_name = 'conversation_started'
    group by all
),

user_messages as (
    select
        conversation_id,
        event_timestamp,
        event_data:message_text as message
    from bronze.amp_all_events_v2
    where event_name = 'user_message'
),

first_message_per_conversation as (
    select
        um.conversation_id,
        um.message,
        cs.channel,
        um.event_timestamp - cs.start_time as time_to_first_message
    from user_messages as um
    inner join conversation_starts as cs
        on um.conversation_id = cs.conversation_id
    where um.event_timestamp = (
        select min(event_timestamp)
        from user_messages as um2
        where
            true
            and um2.conversation_id = um.conversation_id
            and um2.event_timestamp > cs.start_time
    )
),

final_cte as (
    select *
    from first_message_per_conversation
)

select *
from final_cte
```

**Aggregate between events:**
```sql
with session_starts as (
    select
        conversation_id,
        event_timestamp as session_start
    from bronze.amp_all_events_v2
    where event_name = 'session_start'
),

session_ends as (
    select
        conversation_id,
        event_timestamp as session_end
    from bronze.amp_all_events_v2
    where event_name = 'session_end'
),

events_in_session as (
    select
        e.conversation_id,
        ss.session_start,
        se.session_end,
        count(*) as event_count,
        count(distinct e.event_name) as unique_event_types
    from bronze.amp_all_events_v2 as e
    inner join session_starts as ss
        on e.conversation_id = ss.conversation_id
    inner join session_ends as se
        on e.conversation_id = se.conversation_id
    where
        true
        and e.event_timestamp between ss.session_start and se.session_end
    group by all
),

final_cte as (
    select *
    from events_in_session
)

select *
from final_cte
```
