# Computer Systems for Data Science — Comprehensive Midterm Study Guide

## CSEE 4121 Spring 2026

---

# Table of Contents

1. Performance Concepts
2. Data Centers
3. Relational Model & SQL Basics
4. Protocol Buffers & API Schema
5. Indexing & Query Optimization
6. Transactions & ACID
7. Concurrency Control & Locking
8. Indexing Data Structures & Bloom Filters
9. Caching
10. Partitioning & Sharding
11. Replication
12. Distributed File Systems
13. Two-Phase Commit (2PC)
14. TCP/IP Networking Model
15. Distributed Systems Architecture

---

# 1. Performance Concepts

## 1.1 Core Metrics

Performance in computer systems is evaluated along several orthogonal dimensions. Understanding these metrics — and how they interact — is the foundation of systems thinking.

**Latency** is the time to complete a single task from start to finish. Think of it as the *length* of a pipe: how long does it take for one unit of work to travel from one end to the other? Latency is measured in time units (nanoseconds, microseconds, milliseconds, seconds). Synonyms you will encounter include *execution time* and *response time*.

- Example: How long until my pizza arrives after I place the order?

**Throughput** is the number of tasks completed per unit time. Think of it as the *width* of the pipe: how many units of work can flow through simultaneously? Throughput is measured in tasks per unit time (requests/second, transactions/second, pizzas/hour).

- Example: How many pizzas is the shop making per hour?

**Bandwidth** is the *theoretical maximum* throughput of a system. It represents the upper bound — throughput can never exceed bandwidth. In practice, throughput is always less than bandwidth due to overhead, contention, and inefficiencies.

- Example: A pizza shop has 5 ovens that each take 10 minutes per pizza. Bandwidth = 30 pizzas/hour. Actual throughput might be 24 pizzas/hour due to prep time and coordination.

**The Latency-Throughput Tradeoff:** These two metrics are orthogonal — improving one does not necessarily improve the other, and they often trade off against each other. Consider two aircraft flying from DC to Paris:

| Plane | DC → Paris | Speed | Passengers | Throughput (passenger-miles/hr) |
|---|---|---|---|---|
| Boeing 747 | 6.5 hrs | 610 mph | 470 | 286,700 |
| Concorde | 3 hrs | 1350 mph | 132 | 178,200 |

The Concorde has *lower latency* (faster per trip), but the 747 has *higher throughput* (moves more passengers per hour). A system can be fast for one request but unable to handle many requests simultaneously, or vice versa. A pizza shop that hand-crafts artisanal pizza has low latency but low throughput. A factory assembly line might have higher latency per pizza but much higher throughput.

**Comparing system performance:** "System X is *n* times faster than Y" means:

- Speedup(X, Y) = Execution Time(Y) / Execution Time(X)

**QPS/CPU (Queries Per Second per CPU):** A measure of *resource efficiency* — how many requests per second can you process per unit of CPU consumption. This metric matters when you are paying for compute resources in the cloud.

**Uptime:** The fraction of time a system is guaranteed to be working correctly. This is a measure of *reliability* and is typically expressed in "nines":

| Nines | Uptime % | Downtime/year |
|---|---|---|
| 2-nines | 99% | ~3.65 days |
| 3-nines | 99.9% | ~8.76 hours |
| 4-nines | 99.99% | ~52.6 minutes |
| 5-nines | 99.999% | ~5.26 minutes |

## 1.2 Amdahl's Law

Amdahl's Law predicts the overall speedup of a system when you improve only *part* of it. It is one of the most important back-of-the-envelope tools in systems design.

**Formula:**

```
Speedup(s) = 1 / ((1 - p) + p/s)
```

Where:
- **p** = fraction of total work that is affected by the improvement
- **s** = speedup factor applied to that fraction
- **(1 - p)** = fraction of work that remains unchanged

**Maximum possible speedup** (even if the improved part takes *zero* time):

```
Max Speedup = 1 / (1 - p)
```

**Example from lecture:** Suppose you build a new database that speeds up aggregate queries by 2x. Sounds great — but only 10% of your queries are aggregate queries.

- p = 0.1, s = 2
- Speedup = 1 / (0.9 + 0.1/2) = 1 / 0.95 = **1.053** (only 5.3% overall improvement!)
- Even with *infinite* speedup on aggregates: 1 / 0.9 = **1.11** (at most 11% improvement)

**The core lesson of Amdahl's Law: optimize the common case.** If only a small fraction of your work benefits from an optimization, the overall system improvement will be small no matter how dramatic the local improvement. Always identify where the *majority* of time is being spent before optimizing.

## 1.3 Latency Numbers Every Programmer Should Know

The time scales in computer systems vary by *millions*. Developing intuition for these orders of magnitude is essential for back-of-the-envelope calculations and for identifying bottlenecks.

| Operation | Latency | Order of Magnitude |
|---|---|---|
| L1 cache reference | 1 ns | nanoseconds |
| L2 cache reference | 4 ns | nanoseconds |
| Main memory access | 100 ns | nanoseconds |
| SSD / flash random read | 20 µs (20,000 ns) | microseconds |
| Read small object within datacenter network | 100 µs (100,000 ns) | microseconds |
| Datacenter network round-trip | 500 µs | microseconds |
| Run a SQL query on a flash database | 1 ms (1,000,000 ns) | milliseconds |
| HDD seek / magnetic disk random read | 4-10 ms (4,000,000 ns) | milliseconds |
| Internet round-trip (same coast) | 30 ms | milliseconds |
| Internet round-trip (cross-country) | 100 ms | milliseconds |

Key takeaways:
- CPUs and memory operate in **nanoseconds**
- Datacenter networks and SSDs operate in **microseconds** (~1000x slower)
- Sending data over the Internet operates in **milliseconds** (~1000x slower still)
- From L1 cache to cross-country Internet is roughly a **100-million-fold** difference

## 1.4 Identifying Performance Bottlenecks

A critical systems skill is identifying *where* the bottleneck is. The lecture walks through a structured approach:

**Step 1:** Identify what systems a request must access and which networks it traverses.

**Step 2:** Start from the most common case with the highest latency.

**Example (from lecture):** An application sees an average latency of 200ms. Where is the bottleneck?

Given that 10% of requests hit CPU cache, 18% hit main memory, and 72% go to the database:

```
Expected latency = 0.10 * cache_latency + 0.18 * memory_latency + 0.72 * database_latency
```

Since the database accounts for 72% of requests and has latency orders of magnitude higher than cache/memory, the database dominates total latency:

```
Total ≈ 0.72 * database_latency
```

**Real-world scenario analysis (from lecture):**
- *Scenario 1:* App makes a single cloud database request → latency is dominated by network + database
- *Scenario 2:* App makes one request, gets user input, then makes another → two round trips
- *Scenario 3:* App makes 20 sequential database accesses for one query → latency = 20 × single access latency. This is why minimizing round trips is critical.

**Disk vs. Flash, Cost vs. Performance:** The lectures emphasize this tradeoff. Flash (SSD) is ~50,000x faster than magnetic disk for random reads but costs more. For latency-sensitive applications, the cost of flash is justified. For bulk storage, magnetic disk is more economical.

---

# 2. Data Centers

## 2.1 Evolution of Data Centers

The physical infrastructure of computing has evolved dramatically:

- **1960s–70s:** A few very large time-shared computers. Computing was centralized and expensive.
- **1980s–90s:** Heterogeneous collections of smaller machines. Decentralized but hard to manage.
- **2000–2020:** Large numbers of *nearly identical* machines, geographically spread around the world. This is the era of cloud computing and hyperscale data centers.
- **2020s+:** The rise of AI-specific datacenters — clusters of datacenters in the same region designed to train massive models. Companies consider datacenter technology a trade secret, especially in the age of AI. Limited public discussion of state-of-the-art from industry leaders.

## 2.2 Physical Structure

A datacenter is organized hierarchically:

**Rack:**
- Typically 19" or 23" wide
- Measured in "U" or "RU" (Rack Units) — each U is 1.75 inches tall
- Typically 42U tall
- Slots hold power distribution, servers, storage, and networking equipment
- Typical server: 2U form factor, 128–192 cores, 256–512 GB RAM
- Typical storage: 30 drives per unit
- Typical network switch: 72 × 100 Gb/s ports

**Row:** 30+ racks arranged in a row

**Datacenter:** Multiple rows, often the size of a football stadium

## 2.3 Network Topology

Data within a datacenter flows through a hierarchy of networking equipment:

1. **Top-of-Rack (ToR) Switch:** Connects all machines within a single rack. Communication within a rack is fastest.
2. **End-of-Row Router:** Aggregates multiple racks in a row. Communication across racks in the same row adds one hop.
3. **Core Router:** Connects the datacenter to the outside world and to other datacenters.

**Key principle:** Higher in the hierarchy → higher aggregate throughput, but also higher latency for cross-communication. **Multipath routing** provides extra capacity and redundancy — there are multiple physical paths between any two points.

## 2.4 Power & Cooling

**Power Usage Effectiveness (PUE):**

```
PUE = Total Facility Power / IT Equipment Power
```

| Era | PUE | Waste |
|---|---|---|
| Inefficient (early) | 1.7–2.0 | 40–50% wasted on cooling/overhead |
| Efficient (modern) | 1.1–1.15 | 10–15% waste |
| Best case (cutting edge) | ~1.04 | Only 4% overhead |

Power is approximately **25% of monthly operating cost** and is often the *limiting factor* in datacenter capacity — you may have physical space for more servers but not enough power to run them.

**Cooling methods (evolution):**
- **Early:** HVAC systems borrowed from shopping malls — inefficient for dense compute
- **Modern:** Outside air cooling, evaporative cooling — much more efficient
- **Cutting edge:** Liquid immersion cooling — servers submerged in non-conductive fluid

**Backup power:** Batteries handle short glitches (seconds to minutes), with diesel generators for longer outages (minutes to hours).

## 2.5 Datacenter Location Factors

Choosing where to build a datacenter involves balancing several factors:

1. **Cheap, plentiful electricity** — hydroelectric, wind, nuclear (e.g., Oregon, Iowa, Nordic countries)
2. **Good network backbone access** — proximity to major Internet exchange points
3. **Inexpensive land** — rural areas preferred
4. **Proximity to users** — speed of light imposes hard latency limits; data sovereignty laws may require data to stay in certain countries
5. **Available labor pool** — less important now with increased automation
6. **Climate** — cooler climates reduce cooling costs

## 2.6 AI Datacenters vs. Traditional

| Aspect | Traditional | AI-Specific |
|---|---|---|
| Compute | CPUs dominate | Thousands of GPUs, low CPU:GPU ratio |
| Memory | Standard DRAM | High Bandwidth Memory (HBM) on-GPU, very expensive |
| Network (within server) | Standard PCIe | NVLink (GPU-to-GPU, much higher bandwidth) |
| Network (across servers) | Standard Ethernet | InfiniBand (lower latency, higher bandwidth) |
| Topology | Same rack/row structure | Same rack/row structure |
| Cooling | Critical | Even more critical (GPUs produce more heat) |

AI training requires moving enormous amounts of data between GPUs. The network bandwidth requirements within an AI datacenter are much higher than traditional web-serving workloads.

## 2.7 Common Failure Modes

For a new datacenter with thousands of machines, expect *per year*:

- **~Thousands** of hard drive failures
- **~1,000** individual machine failures
- **~Dozens** of minor DNS blips
- **~3** router failures
- **~20** rack failures (40–80 machines unavailable for 1–6 hours)
- **~1** PDU (Power Distribution Unit) failure (500–1,000 machines unavailable for ~6 hours)

**The fundamental lesson: reliability must come from software, not hardware.** At scale, hardware *will* fail. The question is not *if* but *when*. Systems must be designed to tolerate failures gracefully through replication, redundancy, and automatic recovery.

---

# 3. Relational Model & SQL Basics

## 3.1 Core Concepts

The relational model, introduced by Edgar Codd in 1970, organizes data into **relations** (tables):

- **Entity / Relation:** A table (e.g., `Students`, `Courses`)
- **Attribute:** A column (e.g., `name`, `cuid`, `gpa`)
- **Tuple:** A row — one complete record
- **Schema:** The structure definition — column names, their data types, and constraints

The power of the relational model comes from its mathematical foundation (relational algebra) and the declarative query language SQL, which lets you specify *what* you want without specifying *how* to compute it.

## 3.2 Data Types

| Type | Description |
|---|---|
| `INT32`, `INT64` | Integers (32 or 64 bit) |
| `FLOAT32`, `FLOAT64` | Floating point numbers |
| `CHAR(n)` | Fixed-length string, padded with spaces to length n |
| `VARCHAR(n)` | Variable-length string, up to n characters |
| `DATE`, `TIMESTAMP` | Date/time values |
| `BOOLEAN` | True/false |

## 3.3 Set vs. Multiset vs. List

| Collection | Ordered? | Duplicates? |
|---|---|---|
| Set | No | No |
| Multiset (Bag) | No | Yes |
| List | Yes | Yes |

**SQL uses multisets** — duplicates are allowed but order is not guaranteed. Why? Because removing duplicates requires expensive sorting or hashing operations. SQL only eliminates duplicates when you explicitly ask for it with `DISTINCT`.

## 3.4 Keys and Constraints

- **Primary Key:** Uniquely identifies each row; cannot be NULL. Every table should have one.
- **Foreign Key:** References the primary key of another table. Enforces referential integrity — you cannot have a foreign key value that doesn't exist in the referenced table.
- **NOT NULL:** Column cannot contain NULL values.
- **UNIQUE:** All values in the column must be distinct.

**Foreign Key Behavior (from lecture):**

When you try to **insert** a tuple with a foreign key value that doesn't exist in the referenced table, the insert is **rejected** — foreign keys are constraints.

When you **delete** a row that is referenced by foreign keys, the DBA has three options:
1. **Disallow** the delete (reject it)
2. **Cascade** — remove all dependent rows
3. **Set NULL** — set the foreign key columns in dependent rows to NULL

```sql
CREATE TABLE Enrolled (
    student_id CHAR(20),
    cid        CHAR(20),
    grade      CHAR(10),
    PRIMARY KEY (student_id, cid),
    FOREIGN KEY (student_id) REFERENCES Students(cuid)
);
```

## 3.5 Data Independence

Two critical forms of independence that make relational databases practical:

- **Logical data independence:** Applications are unaffected by changes to the logical schema (e.g., adding a column, creating a view). Achieved through **views**.
- **Physical data independence:** Applications are unaffected by changes to physical storage (e.g., adding an index, moving to SSD). The query optimizer handles this transparently.

## 3.6 Basic Query Structure

```sql
SELECT columns          -- what to return (projection)
FROM table              -- where to get data
WHERE condition         -- which rows to include (selection/filter)
GROUP BY column         -- how to group rows
HAVING condition        -- filter on groups (after aggregation)
ORDER BY column         -- how to sort results
LIMIT n                 -- how many rows to return
```

**Important SQL details (from lecture):**
- SQL commands are **case insensitive**: `SELECT`, `Select`, `select` are all the same
- **Values are case sensitive**: `'Seattle'` ≠ `'seattle'`
- Use **single quotes** for string constants: `'abc'` (yes), `"abc"` (no)

**Selection** is the operation of filtering a relation's tuples on some condition (the `WHERE` clause).

**Projection** is the operation of producing an output with only a subset of the columns (the `SELECT` clause).

**LIKE — String Pattern Matching:**
```sql
SELECT * FROM Products WHERE PName LIKE '%gizmo%'
```
- `%` = any sequence of characters (including empty)
- `_` = any single character

**DISTINCT — Eliminating Duplicates:**
```sql
SELECT DISTINCT Category FROM Product    -- no duplicates
SELECT Category FROM Product             -- may have duplicates
```

**ORDER BY — Sorting Results:**
```sql
SELECT PName, Price FROM Product
ORDER BY Price, PName    -- ties broken by PName
```
Ordering is ascending by default; use `DESC` for descending.

## 3.7 SQL Semantics: How Queries Execute Logically

Understanding the *logical* execution order is essential for writing correct SQL:

1. **FROM:** Compute the Cartesian product of all tables
2. **WHERE:** Filter rows based on conditions
3. **GROUP BY:** Group remaining rows
4. **HAVING:** Filter groups
5. **SELECT:** Project desired columns
6. **ORDER BY:** Sort
7. **LIMIT:** Truncate

*Note: This is how SQL logically works, not how the database actually executes it.* The query optimizer may reorder operations for efficiency.

## 3.8 Aggregate Functions

```sql
COUNT(*)       -- number of rows
COUNT(column)  -- number of non-NULL values
SUM(column)    -- sum of values
AVG(column)    -- average
MIN(column)    -- minimum
MAX(column)    -- maximum
```

**All aggregate operators ignore NULL, except `COUNT(*)`.**

**WHERE vs. HAVING:**
- `WHERE` filters individual tuples *before* grouping — **cannot** use aggregates
- `HAVING` filters groups *after* aggregation — **can** use aggregates

```sql
-- WRONG: WHERE with aggregate
SELECT dept, AVG(salary) FROM employees WHERE AVG(salary) > 50000

-- CORRECT: HAVING with aggregate
SELECT dept, AVG(salary) FROM employees GROUP BY dept HAVING AVG(salary) > 50000
```

**Grouping and Aggregation step-by-step (from lecture):**

```sql
SELECT product, SUM(price * quantity) AS TotalSales
FROM Purchase
WHERE date > '10/1/2005'
GROUP BY product
```

Execution:
1. Compute FROM and WHERE — get all purchases after 10/1/2005
2. Group by the `product` attribute — create groups of rows with the same product
3. For each group, compute the SELECT clause — product name and sum of (price × quantity)

## 3.9 JOIN Types

**CROSS JOIN (Cartesian Product):**
```sql
SELECT * FROM A, B    -- every row of A paired with every row of B
```
If A has L rows and B has R rows, the result has L × R rows.

**INNER JOIN:**
```sql
SELECT * FROM A INNER JOIN B ON A.key = B.key
-- Equivalent to:
SELECT * FROM A, B WHERE A.key = B.key
```
Returns only rows where both sides have matching values.

**LEFT (OUTER) JOIN:**
```sql
SELECT * FROM A LEFT OUTER JOIN B ON A.key = B.key
```
Returns *all* rows from A. If there's no matching row in B, the B columns are filled with NULL.

**RIGHT (OUTER) JOIN:** Like LEFT JOIN, but keeps all rows from B.

**FULL OUTER JOIN:** Keeps all rows from *both* tables, filling NULLs where there's no match.

**Result size bounds (from lecture):**

| Join Type | Minimum Rows | Maximum Rows |
|---|---|---|
| Inner Join | 0 | L × R |
| Left Outer Join | L | L × R |
| Right Outer Join | R | L × R |
| Full Outer Join | L + R | L × R |

## 3.10 Subqueries

SQL is **compositional** — the output of one query can be the input to another, since both inputs and outputs are multisets. This enables powerful nested queries.

**IN:** Value exists in a result set
```sql
SELECT * FROM employees WHERE dept_id IN (SELECT id FROM departments WHERE location = 'NYC')
```

**EXISTS:** Checks whether the subquery returns any rows
```sql
SELECT * FROM employees e
WHERE EXISTS (SELECT 1 FROM projects p WHERE p.lead = e.id)
```

**ALL:** Comparison must hold against *every* value in the result set
```sql
SELECT name FROM Product
WHERE price > ALL (SELECT price FROM Product WHERE maker = 'Gizmo-Works')
-- Products more expensive than ALL Gizmo-Works products
```

**ANY:** Comparison must hold against *at least one* value
```sql
SELECT * FROM employees WHERE salary > ANY (SELECT salary FROM employees WHERE dept = 'Sales')
```

**Correlated subqueries (from lecture):** A subquery that references columns from the outer query. These can be very powerful but are harder to optimize:

```sql
SELECT DISTINCT x.name, x.maker
FROM Product AS x
WHERE x.price > ALL (
    SELECT y.price FROM Product AS y
    WHERE x.maker = y.maker AND y.year < 1972
)
-- Products more expensive than all products by the same maker before 1972
```

**Aggregates inside nested queries (from lecture):**

```sql
-- Find stations with the highest daily precipitation on any given day
SELECT station_id, day
FROM Precipitation,
     (SELECT day AS maxd, MAX(precipitation) AS maxp
      FROM Precipitation
      GROUP BY day)
WHERE day = maxd AND precipitation = maxp
```

The inner query computes the max precipitation per day. The outer query joins this back to the original table to find which stations achieved the maximum.

---

# 4. Protocol Buffers & API Schema

## 4.1 The Role of API Schema

In real systems, clients don't talk directly to the database. An **API schema** acts as a translation layer between external clients and the internal database:

- Defines request/response formats, endpoints, and parameters
- Can **hide sensitive database details** from external users
- Allows the **database schema to change without breaking the API** (and vice versa)
- Enforces access control and validation

From the lecture, modern APIs at companies like Uber have evolved:
- From REST-like to RPC-like communication
- From request/response to **streaming** paradigms
- Flexible schema doesn't mean *no* schema — it means centralizing the complexity of consistency
- Transport layer matters as much as the data format: "Don't reinvent the wheel"

## 4.2 Data Serialization Formats

When data travels over a network, it must be **serialized** (converted from in-memory representation to bytes) and later **deserialized** (converted back). The format you choose has major performance implications.

| Format | Type | Pros | Cons |
|---|---|---|---|
| JSON | Text | Human-readable, flexible, self-describing | Verbose, slow parsing |
| XML | Text | Structured, can be validated with schemas | Very verbose |
| Protocol Buffers | Binary | Compact, fast, strongly typed | Not human-readable |

## 4.3 Protocol Buffers (Protobuf)

Protobuf is Google's API schema definition language and serialization format. It is the industry standard for high-performance RPC systems.

**Example schema definition:**

```protobuf
edition = "2023";
package tutorial;

message Person {
    string name = 1;
    int32 id = 2;
    string email = 3;

    enum PhoneType {
        PHONE_TYPE_UNSPECIFIED = 0;
        PHONE_TYPE_MOBILE = 1;
        PHONE_TYPE_HOME = 2;
        PHONE_TYPE_WORK = 3;
    }

    message PhoneNumber {
        string number = 1;
        PhoneType type = 2;
    }

    repeated PhoneNumber phones = 4;
}

message AddressBook {
    repeated Person people = 1;
}
```

## 4.4 Why Protobuf is Smaller — A Concrete Comparison

**JSON (105 bytes minified):**
```json
{"name":"Alice Smith","id":12345,"email":"alice@example.com","phones":[{"number":"555-1234","type":1},{"number":"555-5678","type":2}]}
```

**Protobuf (45 bytes):**
```
0a 0b 41 6c 69 63 65 20 53 6d 69 74 68 10 b9 60 1a 11 61 6c 69 63 65 ...
```

That's a **57% reduction** in size. Here's why:

| Aspect | JSON | Protobuf |
|---|---|---|
| Field names | Repeated as full strings ("name", "id", etc.) | Small numeric tags (1, 2, 3...) |
| Integers | ASCII digits (12345 = 5 bytes as text) | Varint encoding (12345 = 2 bytes) |
| Schema required? | No (self-describing) | Yes (need .proto file) |
| Human readable? | Yes | No |
| Delimiters | Quotes, colons, commas, brackets, whitespace | None — binary encoding |

## 4.5 Backward Compatibility

**Never mark fields as `required` in Protobuf.** This is a critical design rule:

- If you **remove** a required field later, old software will reject new data (it expects the field)
- If you **add** a new required field, new software will reject old data (the field is missing)

Instead, use **optional** fields. Optional fields are safely ignored by older versions of the software that don't know about them. This enables **gradual rollout** — you can update servers and clients independently without breaking the system.

## 4.6 Serialization and Deserialization

- **Serialize:** Convert in-memory data structures to a wire format (bytes) for transmission or storage
- **Deserialize:** Convert wire format back to in-memory data structures

The generated code from `protoc` (the Protobuf compiler) handles both directions automatically, with type safety and efficient binary encoding.

---

# 5. Indexing & Query Optimization

## 5.1 What is an Index?

An index is a separate data structure that speeds up lookups on a column. Think of it as the index in the back of a textbook — instead of scanning every page, you look up the topic and jump directly to the relevant page.

**Search Key:** The attribute (or set of attributes) used to look up records. The search key of an index is *not necessarily* the same as the primary key of the table.

An index consists of records (called index entries) of the form:

```
[search-key] → [pointer to record(s)]
```

The index is typically **much smaller** than the original data — often 100x smaller — because it stores only keys and pointers, not the full records.

## 5.2 Creating Indexes

```sql
CREATE INDEX idx_name ON table(column);
CREATE INDEX idx_multi ON table(col1, col2);    -- composite index
```

## 5.3 Index Trade-offs

**Benefits:**
- Lookup: O(log n) or even O(1) instead of O(n) full table scan
- Range queries become much faster
- A **covering index** can answer a query entirely from the index without touching the base table

**Costs:**
- Storage space — the index is an additional data structure
- Slower writes — every INSERT, UPDATE, or DELETE must also update the index
- More indexes = more write overhead

**Where would you store the index?** Usually in memory, since the index must be small (memory capacity is limited). If it doesn't fit in memory, you need multi-level indexing.

## 5.4 Index Evaluation Metrics (from lecture)

When evaluating an index structure, consider:
- **Access types supported:** Point queries? Range queries?
- **Access time** for lookups
- **Insertion time**
- **Update time**
- **Deletion time**
- **Space overhead**

## 5.5 When Indexes Help

- Frequently filtered columns (`WHERE` clause)
- Join columns
- `GROUP BY` columns
- `ORDER BY` columns

## 5.6 When Indexes Don't Help

- Small tables (full scan is fast enough)
- Low-cardinality columns (few distinct values, e.g., boolean or gender)
- Write-heavy tables (update overhead dominates the benefit)
- When the query scans most of the table anyway

## 5.7 Query Planner

The database's **query planner** decides how to execute your query. You can inspect its decisions:

- `EXPLAIN`: Shows the planned execution strategy without running the query
- `EXPLAIN ANALYZE`: Actually runs the query and shows real execution times

**What to look for:**
- **Sequential Scan:** Full table scan — often indicates a missing index
- **Index Scan:** Using an index — usually good
- **Index Only Scan:** All needed data comes from the index itself — best case

## 5.8 Things That Prevent Index Use

Even if an index exists, the query planner may not use it if:

- **Functions applied to indexed columns:** `WHERE EXTRACT(YEAR FROM date) = 2024` — the index is on `date`, not on `EXTRACT(YEAR FROM date)`
- **Implicit type casts:** Comparing an integer column to a string
- **OR conditions:** Sometimes prevents index use
- **Leading wildcards:** `WHERE name LIKE '%smith'` — the index is sorted by the start of the string, so a leading wildcard can't use it. But `LIKE 'smith%'` *can* use the index.

---

# 6. Transactions & ACID

## 6.1 What is a Transaction?

A transaction is a sequence of one or more database operations that forms a **single logical unit of work**. Either all operations in the transaction succeed, or none of them take effect.

```sql
START TRANSACTION;
UPDATE accounts SET balance = balance - 100 WHERE id = 1;
UPDATE accounts SET balance = balance + 100 WHERE id = 2;
COMMIT;
```

If the system crashes between the two UPDATE statements, the transaction guarantees that neither update is applied — you won't lose money into thin air.

## 6.2 ACID Properties

| Property | Meaning | Mechanism |
|---|---|---|
| **Atomicity** | All or nothing — partial failures are completely rolled back | Write-ahead logging |
| **Consistency** | Database moves from one valid state to another; all constraints satisfied | Constraints, triggers |
| **Isolation** | Concurrent transactions don't interfere with each other | Locking, MVCC |
| **Durability** | Once committed, changes survive any subsequent crashes | Write-ahead logging, replication |

**From the lecture, here is how each DBMS technique maps to ACID:**
- **Write-ahead logging** → provides **A** (Atomicity) and **D** (Durability)
- **Serializability** → whether **I** (Isolation) is achieved
- **2-Phase Locking** → helps ensure **C** (Consistency) and **I** (Isolation)
- **Indexing** → faster access (performance, not ACID per se)
- **Bloom filters** → reduce unnecessary access attempts (performance)
- **Caching** → reduce work duplication (performance)

## 6.3 Write-Ahead Logging (WAL)

The WAL protocol is one of the most important techniques in database systems:

1. **Before** modifying data on disk, write a description of the change to a **sequential log**
2. The log must be flushed to stable storage **before** the actual data page is modified
3. On crash recovery:
   - **Redo:** Replay committed transactions whose data changes may not have reached disk
   - **Undo:** Roll back uncommitted transactions whose partial changes may have reached disk

Why is the log faster than updating the database directly? Because log writes are **sequential** (append-only), while database updates are **random** (scattered across different pages). Sequential I/O is dramatically faster than random I/O on both HDDs and SSDs.

## 6.4 OLTP vs. OLAP

| Characteristic | OLTP | OLAP |
|---|---|---|
| Stands for | Online Transaction Processing | Online Analytical Processing |
| Operations | Read/write, real-time updates | Read-only, batch writes |
| Query size | Small, targeted (one row or a few rows) | Large, scanning/aggregating millions of rows |
| Concurrency | Many concurrent users (thousands) | Fewer, longer-running queries |
| Latency requirement | Low (milliseconds) | Higher (seconds to minutes acceptable) |
| Examples | MySQL, Postgres, Redis | BigQuery, Snowflake, Redshift |
| Use cases | Banking, gaming, user settings | Business reports, analytics, dashboards |

## 6.5 Isolation Anomalies

When transactions run concurrently without proper isolation, several anomalies can occur. The lecture categorizes these by conflict type:

| Anomaly | Conflict Type | Description | Example |
|---|---|---|---|
| **Dirty Read** | Write-Read (WR) | Reading data written by an uncommitted transaction | T1 writes X, T2 reads X, T1 aborts — T2 has read a value that never existed |
| **Lost Update** | Write-Write (WW) | Two concurrent writes, one is silently overwritten | T1 and T2 both read X=10, both write X=X+1, result is 11 instead of 12 |
| **Unrepeatable Read** | Read-Write (RW) | Same row returns different values within one transaction | T1 reads X=0, T2 updates X=1 and commits, T1 reads X again and gets 1 |
| **Phantom Read** | Read-Write (RW) | Set of rows changes between two identical queries | T1 counts rows matching a condition, T2 inserts a new matching row, T1 counts again and gets a different number |

## 6.6 Isolation Levels

| Level | Dirty Reads | Lost Updates | Unrepeatable Reads | Phantom Reads |
|---|---|---|---|---|
| Read Uncommitted | Possible | Possible | Possible | Possible |
| Read Committed | Prevented | Possible | Possible | Possible |
| Repeatable Read | Prevented | Prevented | Prevented | Possible |
| Serializable | Prevented | Prevented | Prevented | Prevented |

- **Most databases default to Read Committed** for performance reasons
- From the lecture: "Serializability is unfortunately rare! Some databases claim to be serializable, but actually are not!"
- **Read Committed** is the most common isolation level in SQL OLTP databases

## 6.7 Serializability

A schedule is **serializable** if its effect is equivalent to *some* serial execution of the same transactions. This is the gold standard for correctness.

**Conflict Serializability:** Two operations *conflict* if they:
1. Belong to different transactions
2. Access the same data item
3. At least one is a write

Conflict types: **Read-Write (RW)**, **Write-Read (WR)**, **Write-Write (WW)**.

**Testing for conflict serializability (from lecture):**

1. **Find all conflicts** — identify pairs of operations from different transactions that access the same item where at least one is a write
2. **Build a conflict graph (precedence graph):** Nodes are transactions. Draw an edge from Ti to Tj if Ti has an operation that conflicts with and precedes an operation in Tj
3. **Check for cycles:** If the graph is **acyclic**, the schedule is conflict serializable. If it has a cycle, it is **not** conflict serializable

**Example with 5 transactions (from lecture):** Given schedule S1 with transactions T1–T5, after building the conflict graph and finding it acyclic, we can derive an equivalent serial schedule by topological sort.

**Strict Serializability (from lecture):** Even stronger than conflict serializability. It adds the constraint: if transaction Y starts after transaction X commits (X and Y are not concurrent), then X must appear before Y in the equivalent serial order. **2PL produces strictly serializable schedules.**

---

# 7. Concurrency Control & Locking

## 7.1 Why Concurrency?

Real systems handle enormous concurrent load — Visa processes **60,000+ transactions per second**. Making unrelated transactions wait for each other would destroy performance. The goal is to *interleave* transactions for performance while maintaining correctness (serializability).

## 7.2 Lock Types

| | None Held | S (Shared) Held | X (Exclusive) Held |
|---|---|---|---|
| **Request S** | Grant | Grant | Wait |
| **Request X** | Grant | Wait | Wait |

- **Shared (S) Lock:** For reading. Multiple transactions can hold S locks on the same item simultaneously — readers don't block readers.
- **Exclusive (X) Lock:** For writing. Only one transaction can hold an X lock. It blocks all other lock requests (both S and X).

## 7.3 Two-Phase Locking (2PL)

**Rule:** A transaction cannot acquire any new locks after it has released any lock.

This creates two distinct phases:
1. **Growing phase:** The transaction acquires locks as needed. No locks are released.
2. **Shrinking phase:** The transaction releases locks. No new locks can be acquired.

**2PL guarantees conflict serializability** — but only if the transaction completes (it may deadlock).

## 7.4 Strict 2PL

**Rule:** Hold ALL locks until COMMIT or ABORT. Release everything at the end.

This is stricter than basic 2PL — the shrinking phase happens all at once at commit time.

**Benefits of Strict 2PL over basic 2PL:**
- Prevents **cascading aborts** — if T1 releases a lock early and T2 reads the value, then T1 aborts, T2 must also abort (cascade). Strict 2PL avoids this.
- Simpler recovery
- Produces **strictly serializable** schedules (from lecture)

**Most databases use Strict 2PL** because of its simplicity and strong guarantees.

## 7.5 Deadlocks

A **deadlock** occurs when there is a cycle of transactions, each waiting for a lock held by the next transaction in the cycle.

**Example:**
- T1 holds lock on A, wants lock on B
- T2 holds lock on B, wants lock on A
- Neither can proceed — circular wait!

**Detection:** Build a **waits-for graph** where nodes are transactions and edges point from waiting to holding transactions. A **cycle** in this graph means deadlock.

**Important (from lecture):** The waits-for graph is **different** from the conflict graph used for serializability testing! The waits-for graph tracks runtime lock waiting, while the conflict graph tracks operation ordering.

**Resolution:** When a deadlock is detected, abort one transaction (typically the youngest or the one with the least work done) and restart it.

## 7.6 Deadlock Prevention Strategies

**Conservative 2PL (C2PL):**
- Acquire **ALL** locks before the transaction begins
- If you cannot obtain all locks, release everything and try again
- **Guarantees no deadlocks** but can degrade performance (transactions may wait unnecessarily)

**Wait-Die (Non-Preemptive):**
- Transactions are assigned priorities based on start time (older = higher priority)
- If Tx (higher priority) wants a lock held by Ty (lower priority): **Tx waits**
- If Tx (lower priority) wants a lock held by Ty (higher priority): **Tx aborts (dies)**
- Shape of waits-for graph: only older transactions wait for younger ones → no cycles possible

**Wound-Wait (Preemptive):**
- Same priority scheme (older = higher priority)
- If Tx (higher priority) wants a lock held by Ty (lower priority): **Ty is aborted (wounded)**
- If Tx (lower priority) wants a lock held by Ty (higher priority): **Tx waits**
- Shape of waits-for graph: only younger transactions wait for older ones → no cycles possible

In both schemes, aborted transactions restart with the **same timestamp** (priority), ensuring they eventually complete (starvation-free).

## 7.7 Detailed 2PL Execution Example (from lecture)

The lecture walks through a full example with 5 transactions executing under strict 2PL:

Given operation arrival order: w1(A), r2(A), w1(B), w3(C), r2(C), r4(B), w2(D), w4(E), r5(D), w5(E)

Step-by-step execution:
1. T1 gets X(A), executes w1(A)
2. T2 requests S(A) — T1 holds X(A), so T2 **waits**
3. T1 gets X(B), executes w1(B)
4. T3 gets X(C), executes w3(C), T3 commits, unlocks C
5. T1 commits, unlocks A, B — T2 is unblocked
6. T2 gets S(A), reads r2(A); gets S(C), reads r2(C); gets X(D), writes w2(D); commits
7. T4 gets S(B), reads r4(B); gets X(E), writes w4(E); commits
8. T5 gets S(D), reads r5(D); gets X(E), writes w5(E); commits

The waits-for graph at step 2 has T2 → T1, but no cycle, so no deadlock.

---

# 8. Indexing Data Structures & Bloom Filters

## 8.1 B-Tree / B+ Tree

The B+ tree is the **most common index structure** in databases.

**Properties:**
- **Balanced tree:** All leaves are at the same depth
- **High fan-out:** Each node has many children (hundreds to thousands), not just 2
- **Lookup time:** O(log n) — but with a very large base, so the tree is typically only 3–4 levels deep
- **Supports range queries efficiently:** Leaf nodes are linked, so after finding the start of a range, you can scan sequentially
- Since each node fits in one disk block/page, each level requires one I/O operation

## 8.2 Dense vs. Sparse Indexes

| Type | Description | When to Use |
|---|---|---|
| **Dense** | An index entry for *every* search key value | Required for secondary indexes |
| **Sparse** | An index entry for only *some* search key values | Only works when data is physically sorted by the search key |

**Why must secondary indexes be dense?** A secondary index points to records that are *not* physically sorted by that column. If you have a sparse secondary index, you can't interpolate between entries — you'd have to scan potentially the entire table between two index entries. With a primary (clustering) index, the data is sorted, so you can jump to the approximate location and scan forward.

**From the lecture — Sparse Index Lookup:**
To find a record with search key K in a sparse index:
1. Find the index entry with the largest key value ≤ K
2. Follow the pointer to the data file
3. Scan sequentially from that point

## 8.3 Multilevel Indexes (from lecture)

When an index is too large to fit in memory, accessing it from disk becomes expensive.

**Solution:** Treat the index as a sequential file and build a **sparse index on top of it:**
- **Inner index:** The original (base) index file, stored on disk
- **Outer index:** A sparse index over the inner index, small enough to fit in memory

If even the outer index is too large, add yet another level. This is the idea behind B+ trees — they are essentially multilevel indexes.

**All levels** must be updated on insertion or deletion, which adds write overhead.

## 8.4 Index Updates (from lecture)

**Insertion into a dense index:**
- Look up the search key value
- If it doesn't exist in the index, insert a new entry
- May require creating space (shifting entries, overflow blocks)

**Insertion into a sparse index:**
- No change needed unless a new block is created
- If a new block is created, insert the first search key value of that block into the index

## 8.5 Pointer Size Calculation (from lecture)

**How big does a pointer need to be?** Consider a database with 1GB of data:
- 1GB = 2^30 bytes
- A pointer needs 30 bits to address any byte in 1GB
- General rule: pointer size = ceil(log2(data size in bytes)) bits

**Example:** A database with 2TB of flash storage and entries averaging 50 bytes:
- Total entries: 2TB / 50B = ~40 billion keys
- Pointer needs to distinguish among 40 billion keys → minimum ~36 bits ≈ 5 bytes
- Index size ≈ 40 billion × 5 bytes = **200 GB** — doesn't fit in 64 GB of memory!
- Therefore, you need multi-level indexing or bloom filters

## 8.6 Bloom Filters

A **Bloom filter** is a space-efficient probabilistic data structure for fast set membership testing.

**The Motivation:** When an index doesn't fit in memory, even checking whether a key *exists* requires expensive disk reads. A Bloom filter sits in memory and can quickly tell you "definitely not in the set" or "maybe in the set."

**Structure:**
- An array of **m bits**, all initialized to 0
- **k independent hash functions** h1, h2, ..., hk, each mapping an input to a position in [1, m]

**Operations:**

*Insert(x):* Compute h1(x), h2(x), ..., hk(x). Set all those bit positions to 1.

*Lookup(x):* Compute h1(x), h2(x), ..., hk(x). Check all those positions:
- If **any position is 0** → x is **definitely NOT** in the set (**no false negatives**). You saved a disk read!
- If **all positions are 1** → x is **probably** in the set (**false positives are possible**)

**Concrete example (from lecture):**
```
m = 10, k = 2
Bloom filter: [0, 1, 0, 0, 1, 0, 1, 1, 0, 0]

Is "cat" in DB?  h1("cat")=2, h2("cat")=8 → positions 2 and 8 are both 1 → Maybe!
Is "dog" in DB?  h1("dog")=1, h2("dog")=8 → position 1 is 0 → Definitely NOT!

Add "dog":       Set positions 1 and 8 to 1.
```

**Properties:**
- **Space-efficient:** Uses only bits, not full items
- **False positives possible:** Two different items can hash to the same positions
- **No false negatives:** If any bit is 0, the item is certainly not in the set
- **Cannot delete items:** Clearing a bit would affect other items that hash to the same position
- **Cannot be "undone"**

**Optimal number of hash functions:**
```
k_optimal = (m/n) * ln(2)
```
where n is the number of items inserted.

**False positive probability:**
```
FP rate ≈ (1 - e^(-kn/m))^k
```

**Space vs. Speed Tradeoff (from lecture):**

A larger Bloom filter means fewer false positives (fewer unnecessary disk reads → lower latency, higher throughput). But a larger Bloom filter takes more memory, leaving less room for caching index entries in memory.

**Example calculation from lecture:** Database with 2GB memory, 100GB flash, 1 billion entries:

| Configuration | BF Size | FP Rate | Cache Hit Rate | Avg Latency |
|---|---|---|---|---|
| Option 1 | 600 MB | 9% | 90% (1.4GB cache) | 9.49 µs |
| Option 2 | 1.1 GB | 1% | 70% (0.9GB cache) | 12.64 µs |

Option 1 wins despite higher false positives because it leaves more memory for caching!

**Other issues with Bloom filters (from lecture):**
- Can get "depleted" over time as more items are added
- Need to estimate the number of unique entries in advance
- Do not support deletes (workaround: counting Bloom filters, cuckoo filters)
- Active research area: learned Bloom filters, elastic Bloom filters

---

# 9. Caching

## 9.1 Why Cache?

Many systems use caches to reduce work and transport duplication:
- Databases cache frequently accessed keys in memory
- Computers use memory as a cache for disk
- CDNs cache content near users
- File systems have a page cache
- **Dedicated cache servers** (key-value caches) like **Memcached**, **Redis**, and **Amazon ElastiCache** store data entirely in memory and sit between the application and the database

## 9.2 Cache Concepts

- **Cache hit:** Data found in cache → fast (e.g., 100 µs)
- **Cache miss:** Data not in cache, must fetch from source → slow (e.g., 5 ms)
- **Hit ratio:** hits / total requests

**Example (from lecture):**
- Cache hit latency: 100 µs, database latency: 5 ms
- At 98% hit rate: 0.98 × 100 + 0.02 × 5000 = **198 µs**
- At 99% hit rate: 0.99 × 100 + 0.01 × 5000 = **149 µs**
- A **1% improvement** in hit rate improves latency by **25%!**

## 9.3 Three Fundamental Cache Problems

1. **Assignment:** Where do you put the data in the cache? How do you organize it for fast reads?
2. **Consistency:** What happens when the underlying data is updated or deleted?
3. **Eviction:** When the cache is full, what do you remove to make room?

## 9.4 Standard Eviction Model (from lecture)

- Cache has fixed size C (measured in items)
- Each item has the same size (1 unit)
- Each item has a unique key
- Cache is full
- On a **hit**: read directly from cache
- On a **miss**: fetch from database, **evict** one item to make room, insert the new item

## 9.5 Eviction Policies

### FIFO (First In, First Out)

Evict the item that was inserted into the cache *earliest*.

- **Implementation:** Simple queue (linked list). New items go to the tail; evict from the head.
- **Idea:** The oldest item is likely the least relevant.
- **Advantage:** Extremely simple to implement.
- **Disadvantage:** An old item might still be very popular. FIFO ignores access patterns entirely.
- **Generally suffers from low hit rates.**

*Example from lecture (cache size 4, accesses: 1,2,3,4,1,2,5,1,2,3,4,5):*
Hits on 1 and 2 (already in cache), then misses as items are evicted in insertion order. **Total misses: 10.**

### LRU (Least Recently Used)

Evict the item that was *accessed least recently*.

- **Key difference from FIFO:** A cache hit moves the item to the front (most recent). FIFO does not.
- **Idea:** Recently accessed items are likely to be accessed again (temporal locality).
- **Advantage:** Works well for most real-world workloads. The default eviction policy in many systems.
- **Disadvantage:** Expensive to implement perfectly — need to update a list on every read, not just on misses.

*Same example: Total misses: 8. Better than FIFO.*

**LRU Approximations (from lecture):**
- **Sampled LRU:** Instead of maintaining a full ranking, just record each item's last access timestamp. At eviction time, sample N random items and evict the oldest. With N ≥ 50–100, this closely approximates true LRU.
- **CLOCK algorithm:** Maintain 1 bit per item (reference bit). Set to 1 on access. A "clock hand" sweeps through, resetting bits to 0. Evict the first item with bit = 0. Originally used for OS memory page caching.

### LFU (Least Frequently Used)

Evict the item accessed the *fewest total times*.

- **Key difference from LRU:** Tracks *count* of accesses (frequency), not *recency* of access.
- **Idea:** Items accessed many times in the past will likely be accessed again.
- **Advantage:** Works well for workloads with a stable set of popular items.
- **Disadvantage:** Does not adapt well when popularity shifts. New items that become popular will have low counts and get evicted. To fully implement, you also need to track frequencies of *evicted* items.

*Same example: Total misses: 7. Better than LRU for this workload.*

### LRU/LFU Hybrids (from lecture)

- **Segmented LRU:** First insertion goes to the *middle* of the cache (not the head). Subsequent accesses promote to the top. This penalizes items accessed recently but only once, combining benefits of both recency and frequency.

### OPT / Belady's Algorithm (Optimal)

Evict the item that won't be accessed for the **longest time in the future**.

- **Provably optimal** — no other policy can achieve a better hit rate.
- **Completely impractical** — requires knowledge of the future!
- **Useful as a benchmark:** Compare your policy's hit rate to OPT to see how much room for improvement exists.
- Some recent research uses OPT to train machine learning eviction policies.

*Same example: Total misses: 6 (optimal).*

### Summary of Policies

| Policy | Description | Pros | Cons |
|---|---|---|---|
| FIFO | First in, first out | Simple | Ignores access patterns |
| LRU | Least recently used | Good for temporal locality | Tracking overhead |
| LFU | Least frequently used | Good for stable popularity | Doesn't adapt to changes |
| OPT | Evict furthest future use | Optimal (theoretical) | Requires future knowledge |

## 9.6 Cache Consistency

When the underlying data changes, the cache must be kept consistent:

- **Write-through:** Update cache and database together (synchronous). Simple but slow.
- **Write-back:** Update cache now, database later (asynchronous). Faster but risks data loss on crash.
- **Invalidation:** Remove the entry from cache on update. Next read will fetch fresh data.

## 9.7 Real-World Complications (from lecture)

- The standard model assumes all items are the same size. In reality, items have different sizes — a big item might cause eviction of many small items.
- No one-size-fits-all policy works for every workload. The right policy depends on your access patterns.

---

# 10. Partitioning & Sharding

## 10.1 Why Partition?

When data grows beyond what a single machine can hold or serve:
- **Capacity:** Single machine can't hold all data
- **Performance:** Spread load across multiple servers
- **Parallelism:** Enable parallel query processing

**Horizontal partitioning** divides *rows* (tuples) among nodes: each node gets a subset of the rows but all columns. **Vertical partitioning** divides *columns* among nodes. This course focuses on **horizontal partitioning**.

## 10.2 Partitioning Schemes

### Round-Robin

Tuple *i* goes to server `i mod n`.

**Evaluation:**
- **Scan:** Excellent — all nodes have nearly equal data, work is perfectly balanced
- **Point queries:** Bad — must query *all* nodes since placement is based on insertion order, not key values
- **Range queries:** Bad — all nodes must be queried
- **Advantages:** Very simple to implement; requires only an insertion counter
- **Disadvantage:** All multi-tuple queries must touch all nodes

### Hash Partitioning

Choose one or more attributes as the partitioning key. Apply hash function: `hash(key) mod n` → send to that node.

**Evaluation:**
- **Scan:** Good — assuming a good hash function and keys that form a key, tuples are evenly distributed (slightly less even than round-robin: uniform random ≠ round-robin)
- **Point queries:** Excellent — you can immediately compute which node stores a given key
- **Range queries:** Bad — hash destroys ordering, so range queries must touch all nodes
- **Advantage over round-robin:** Point lookups are trivial; no insertion counter needed
- **Major problem:** Changing `n` (adding/removing servers) requires **massive data redistribution** — most keys will hash to different nodes

### Range Partitioning

Choose a partitioning attribute and a **partitioning vector** [v0, v1, ..., vn-2]:
- Keys < v0 → node 0
- Keys in [vi, vi+1) → node i+1
- Keys ≥ vn-2 → node n-1

Example with vector [5, 11]: key 2 → node 0, key 8 → node 1, key 20 → node 2.

**Evaluation:**
- **Scan:** Good — all nodes participate
- **Point queries:** Good — can immediately determine the correct node
- **Range queries:** Excellent — only the nodes covering the range need to be accessed, leaving others free for other queries
- **Good for transactions** — if transactions access similar key ranges, they naturally colocate
- **Disadvantages:**
  - Requires a **centralized service** (database proxy / registry) to store the partition vector
  - **Skew** is more likely — popular key ranges cause hot spots
  - **Execution skew** — if many blocks are fetched from a single range partition, potential parallelism is wasted

## 10.3 Handling Small Relations (from lecture)

- **Small relations** that fit in a few disk blocks shouldn't be partitioned — assign to a single node, or replicate everywhere
- **Medium relations:** Choose how many nodes based on relation size
- **Large relations:** Partition across all available nodes

## 10.4 Types of Skew (from lecture)

**Data-distribution skew:** Some nodes have many tuples, others have few.
- **Attribute-value skew:** Some partitioning attribute values appear in many tuples (e.g., a very popular product ID). All tuples with the same value end up in the same partition.
- **Partition skew:** Imbalance even without attribute-value skew, from a badly chosen range-partition vector.
- Can be mitigated with balanced range-partition vectors (but rebalancing is expensive).
- Hash partitioning is less susceptible to partition skew but not immune to attribute-value skew.

**Execution skew:** Access patterns are skewed — some tuples are much more "popular" than others (e.g., active student CUIDs accessed far more than graduated students). This can happen with any partitioning method.

**Solutions:** Periodic rebalancing, caching hot data, splitting hot partitions.

## 10.5 Routing of Queries (from lecture)

For range partitioning, the partition table is typically stored at a **master node**. Two designs:

1. **All queries go through master:** Master forwards to the appropriate data node. Disadvantage: master is a bottleneck, and must be contacted for every query.
2. **Master tells clients the mapping:** Clients cache the partition map and talk directly to data nodes. Advantage: faster (skip master for routine queries). Disadvantage: what happens if a node dies and the client has stale mapping info?

Systems using a master node: Hadoop File System, Google File System, BigTable, HBase.

## 10.6 Consistent Hashing

Consistent hashing solves the **redistribution problem** of standard hash partitioning.

**Concept:** Imagine a ring (circle) representing the hash space from 0 to 1. Both servers and keys are hashed onto positions on this ring. Each key is assigned to the next server clockwise from its position.

**Adding a node:** Only the new node's immediate clockwise neighbor transfers some of its data to the new node. All other nodes are unaffected.

**Removing a node:** Only the removed node's clockwise neighbor absorbs its data.

**Benefits:**
- **No single point of failure** — no master needed, fully peer-to-peer
- **Minimal data movement** on topology changes — only O(1/n) of keys need to move when adding/removing a node, versus nearly all keys with `hash mod n`
- **Scalable** — adding servers is cheap

**Disadvantages:**
- Typically requires more communication/coordination among nodes
- Can have uneven load distribution without virtual nodes

**Used by:** Cassandra, DynamoDB, Akamai CDN

---

# 11. Replication

## 11.1 Why Replicate?

- **Durability:** Survive hardware failures — if one copy is lost, others remain
- **Availability:** System stays up even if some nodes fail
- **Performance:** Read from the nearest replica; reduce latency for geographically distributed users

## 11.2 Replication Factor

Data is typically replicated to **3 nodes**. Why 3?

- **1 copy:** Single point of failure
- **2 copies:** No majority possible — if the copies disagree, you can't determine which is correct
- **3 copies:** Smallest odd number that allows a **majority vote** (2 out of 3 can agree)

The unit of replication is typically a **partition (tablet)**, which may be smaller than a full table.

## 11.3 Master-Replica (Primary-Copy) Architecture

- **Master / Leader:** Accepts all writes and replicates them to followers
- **Replicas / Followers:** Receive replicated writes and serve read requests

**On master failure:** An **election** process selects a new master from the replicas. Other nodes must learn who the new master is.

## 11.4 Replication Locations (from lecture)

**Within a datacenter:**
- Protects against disk and server failures
- Reduces latency if a local copy is available
- Replication within or across racks

**Across datacenters:**
- Protects against datacenter-level failures (power outage, fire, earthquake, government seizure, network partition)
- Provides lower latency for end users if a copy is in a nearby datacenter
- **Much higher latency** for replication (cross-country or cross-continent)

## 11.5 Consistency Challenges

Replicas may have **temporarily different values** after a write. The system must decide how to handle this:

**Two replication modes (from lecture):**
- **Synchronous replication:** Write is not committed until all replicas confirm. Guarantees strong consistency but adds latency (must wait for slowest replica).
- **Asynchronous replication:** Write is committed at one datacenter, then propagated to others. Lower latency but carries a small risk of data loss if the primary fails before replication completes.

The fundamental tradeoff: **consistency vs. availability vs. latency.** You cannot have all three simultaneously (this is related to the CAP theorem, though the course focuses on practical tradeoffs rather than the theorem itself).

## 11.6 Protocols to Update Replicas (from lecture)

1. **Two-Phase Commit (2PC):** Assumes all replicas are available. Covered in detail in Section 13.
2. **Consensus protocols (Paxos, Raft):** A set of replicas agree on what updates to perform and in what order. Can work even without a designated master, and tolerate failures of minority nodes.

---

# 12. Distributed File Systems

## 12.1 What is a File System?

A file system provides the logical concept of **files** identified by paths, supporting operations: read, write, create, delete. It abstracts away the details of where data is physically stored on disk.

## 12.2 Distributed File Systems

A **distributed file system** spans multiple machines, providing a single unified namespace while using partitioning and replication under the hood.

**Examples (from lecture):** Hadoop File System (HDFS), Google File System (GFS), CODA, Google Colossus.

**Basic architecture:**
- **Master:** Responsible for metadata (file names, directory structure, block locations)
- **Chunk/Data servers:** Responsible for reading and writing large chunks of data
- **Chunks replicated** on 3 machines; master manages replicas
- GFS/HDFS replication is typically within a single datacenter

## 12.3 HDFS (Hadoop Distributed File System)

HDFS is modeled after the Google File System (GFS).

**Architecture:**
- **NameNode (master):**
  - Maps filename → list of Block IDs
  - Maps each Block ID → list of DataNodes containing replicas
  - Returns block IDs and their locations to clients
- **DataNode:**
  - Maps Block ID → physical location on disk
  - Sends actual data back to clients
- **Client:**
  - Sends filename to NameNode
  - Gets back block locations
  - Reads data **directly from DataNodes** (NameNode is not on the critical read/write path)

**Design principles:**
- **Single namespace** for entire cluster (single directory structure)
- **Write-once-read-many** access model — clients can only append to existing files (not ACID!)
- Files broken into **blocks** (typically 64 MB each)
- Each block **replicated** on multiple DataNodes (typically 3)

**NameNode as single point of failure:**
- All queries go through NameNode first for metadata
- Tradeoff: simplicity vs. fault tolerance
- **Mitigations:** Standby NameNode (hot backup), write-ahead logging of metadata, consensus protocols to protect against NameNode failure
- Directory information kept in memory to avoid expensive disk reads → memory size limits the number of files

## 12.4 Limitations of HDFS (from lecture)

1. **Central master bottleneck:** NameNode keeps everything in memory → memory limits number of files
2. **Per-file overhead:** Not suitable for storing very large numbers of small objects
3. **No in-place updates:** Ideal for write-once, append-only data (e.g., logs, data warehouse imports)
4. **Often used as the storage foundation** for higher-level systems: BigQuery/BigTable uses GFS/Colossus; HBase/Spark uses HDFS

## 12.5 Distributed File Systems vs. Databases (from lecture)

| Aspect | Distributed File System | Database |
|---|---|---|
| Schema | Limited/flexible (Parquet, ORC, JSON) | Full relational model |
| Transactions | None or limited | Full ACID support |
| Abstraction level | Lowest layer (like a file system) | Higher-level (SQL, indexes, optimizer) |
| Typical stack | KV store built on top, then relational DB on top of KV store | Self-contained |

## 12.6 Geographically Distributed Storage (from lecture)

Modern storage systems support geographic distribution for:
- **Fault tolerance** (survive datacenter failures)
- **Latency** (serve from datacenter closest to user)
- **Governmental regulations** (data sovereignty)

Latency of cross-datacenter replication is much higher than within a datacenter. Systems choose between:
- **Synchronous replication:** Wait for remote replicas before committing. Safer but higher latency.
- **Asynchronous replication:** Commit locally, propagate later. Lower latency but small risk of data loss.

---

# 13. Two-Phase Commit (2PC)

## 13.1 The Problem

A distributed transaction spans multiple servers. We must ensure **atomicity**: the transaction either commits at ALL servers or aborts at ALL servers. A partial commit — committed at some servers but aborted at others — would leave the database in an inconsistent state.

## 13.2 System Model

**Fail-stop assumption:** Servers either work correctly or stop completely. They do not send incorrect or malicious messages. This is reasonable when all nodes are within the same organization. (In contrast, **Byzantine fault tolerance** — used in blockchains — assumes nodes can behave arbitrarily.)

**Roles:**
- **Transaction Coordinator (TC):** Any server can be a coordinator. Initiates and coordinates the commit protocol.
- **Transaction Manager (TM):** One per node. Manages the local transaction log and executes operations locally.

## 13.3 Protocol Phases

### Phase 1: Prepare

1. Coordinator writes `<prepare T>` to its own log and flushes to stable storage
2. Coordinator sends **PREPARE** message to all participating servers
3. Each participant:
   - Tries to prepare locally (e.g., acquire locks using conservative 2PL, execute the transaction)
   - If it **can** commit: writes `<ready T>` to its log, **flushes all records for T to stable storage** (executes but does not commit), sends **READY (YES)** to coordinator
   - If it **cannot** commit: writes `<no T>` to its log, sends **ABORT (NO)** to coordinator

### Phase 2: Commit/Abort

1. Coordinator collects all votes:
   - **ALL yes** → writes `<commit T>` to log, flushes to stable storage, sends **COMMIT** to all participants
   - **ANY no** → writes `<abort T>` to log, sends **ABORT** to all participants
2. Once the decision record is in stable storage, the transaction is definitively committed or aborted
3. Each participant writes the decision (COMMIT or ABORT) to its own log:
   - If committed: flush commit record, apply changes permanently
   - If aborted: undo the transaction using local logs (WAL)
4. Participants send acknowledgments to coordinator

## 13.4 Failure Handling

**Participant crash before voting:**
- Coordinator times out waiting for the vote
- Since no READY was sent, coordinator **aborts** the transaction

**Participant crash after voting YES:**
- On recovery, the participant checks its log and finds `<ready T>` but no decision
- Must **ask the coordinator** for the decision (commit or abort?)
- The coordinator's log has the definitive answer

**Coordinator crash after collecting votes (the blocking problem):**
- Participants that voted YES are now **stuck** — they don't know whether the coordinator decided to commit or abort
- They cannot unilaterally commit (another participant might have voted NO) or abort (the coordinator might have committed)
- They must **wait** for the coordinator to recover — this is the **blocking problem** of 2PC

**Handling coordinator failure (from lecture — detailed rules):**
1. If any active server has `<commit T>` in its log → T must be committed
2. If any active server has `<abort T>` in its log → T must be aborted
3. If some active server does NOT have `<ready T>` → the coordinator could not have committed → abort T
4. If all active servers have `<ready T>` but no decision record → **must wait** for coordinator recovery

## 13.5 Network Partition Handling (from lecture)

- If coordinator and all participants are in the same partition → no effect
- If split across partitions:
  - Servers not with the coordinator treat it as a coordinator failure
  - Servers with the coordinator treat the others as participant failures
  - No harm done — but servers may still **block** waiting for the coordinator's decision

## 13.6 Recovery and Concurrency Control (from lecture)

**In-doubt transactions** have `<ready T>` in their log but no decision (commit or abort). Recovery for these can be slow because the server must contact the coordinator.

**Optimization:** Write lock information to the log: `<ready T, L>` where L is the list of locks held by T. On recovery:
- Reacquire all locks from the log
- Resume normal transaction processing concurrently
- In-doubt transactions will be resolved when the coordinator is contacted
- But any new transaction waiting for those locks must wait until the in-doubt transaction is resolved

## 13.7 Avoiding the Blocking Problem (from lecture)

The blocking problem is a serious concern — any participant or coordinator failure can block all other nodes.

**Solution: Distributed Consensus (Paxos, Raft)**

- Involve **multiple nodes** in the decision process
- As long as a **majority** of nodes remain alive and can communicate, the protocol makes progress
- Even if some nodes fail, the remaining majority can "learn" the decision
- No blocking as long as majority survives

**How consensus integrates with 2PC:**
1. After getting responses from 2PC participants, coordinator sends its decision to a set of consensus participants
2. If coordinator fails before informing all: elect a new coordinator, which follows 2PC recovery protocol
3. As long as a majority of consensus participants are accessible, the decision can be found without blocking

**Three-Phase Commit (3PC):** An extension of 2PC that avoids blocking under certain assumptions, using ideas similar to distributed consensus.

## 13.8 Summary of 2PC (from lecture)

- Each server can be both a coordinator and a transaction manager
- Coordinators first prepare, then commit if all managers are ready
- If the coordinator fails right after all managers respond ready but before committing → must wait for recovery
- This blocking problem is solved by consensus protocols that replicate coordinator state across multiple nodes

---

# 14. TCP/IP Networking Model

## 14.1 The 5-Layer Model

The TCP/IP model organizes network communication into 5 layers, each with a specific responsibility. Data flows down the stack on the sender side (encapsulation) and up the stack on the receiver side (decapsulation).

| Layer | Name | Function | Key Protocols / Examples |
|---|---|---|---|
| 5 | Application | Software communication | HTTP, HTTPS, FTP, SMTP, SSH, DNS |
| 4 | Transport | App-to-app delivery, reliability | TCP, UDP, QUIC |
| 3 | Network | Global routing | IPv4, IPv6, BGP |
| 2 | Data Link | Local delivery | Ethernet, MAC, ARP, DHCP |
| 1 | Physical | Bits to physical signals | Fiber, copper, WiFi, 5G, satellite, microwave |

**Mnemonic (bottom → top):** **P**eople **D**on't **N**eed **T**o **A**sk

## 14.2 Layer 1: Physical

Converts bits to physical signals and transmits them over a medium. The medium determines speed, range, and latency.

- **Fiber optic:** High bandwidth, low latency, long range. Light travels through glass.
- **Copper wire:** Lower bandwidth, shorter range. Used for Ethernet.
- **WiFi / 5G:** Wireless, convenient but lower reliability.
- **Microwave:** Travels faster than fiber (air vs. glass) — used by high-frequency trading firms.
- **Satellite (GEO):** ~600 ms latency (physics — distance to geostationary orbit). **Starlink (LEO):** 20–40 ms — viable for applications.

**Key concept:** Layer 1 is **protocol-agnostic** — it just moves signals. A broken cable or weak signal kills everything above it regardless of software quality. Ethernet spans L1 (signaling) and L2 (framing).

## 14.3 Layer 2: Data Link

Organizes bits into **frames** and handles local network delivery.

**Ethernet Frame Structure:**
```
| Preamble (8B) | Dst MAC (6B) | Src MAC (6B) | Type (2B) | Payload (46-1500B) | FCS (4B) |
```

**MAC Address:** 48-bit hardware identifier (e.g., `3C:22:FB:4A:9E:01`). Burned in at manufacture. **Local only** — invisible beyond the router. Switches use MAC tables; routers do not.

**Key protocols:**
- **ARP (Address Resolution Protocol):** Maps IP addresses → MAC addresses. Bridges L2 and L3.
- **DHCP (Dynamic Host Configuration Protocol):** Automatically assigns IP addresses to new devices joining a network.

**Switch:** A Layer 2 device that forwards frames based on MAC address within a local network.

## 14.4 Layer 3: Network

Routes **packets** across multiple networks using **IP addresses**. Makes the global Internet possible.

**IP Addresses:**
- **IPv4:** 32-bit addresses (~4.3 billion). Exhausted — extended via NAT (Network Address Translation), which lets many devices share one public IP.
- **IPv6:** 128-bit addresses (340 undecillion). Eliminates need for NAT. Dominant on mobile networks.

**Key devices and protocols:**
- **Router:** Layer 3 device that forwards packets based on IP address. Each router makes a **local best-hop decision** — no router has a complete map of the Internet.
- **BGP (Border Gateway Protocol):** Connects autonomous systems (ISPs, large networks). BGP's trust model is its greatest vulnerability — route hijacking is a known attack.
- **DHCP:** Automatically configures new devices with an IP address, subnet mask, gateway, and DNS server.

**Key concept:** IP addresses are logical and hierarchical — they encode location. This is unlike MAC addresses, which are flat and hardware-specific.

## 14.5 Layer 4: Transport

Provides **end-to-end delivery** between applications. **Port numbers** (0–65535) identify which application/process on a machine should receive the data. Data units at this layer are called **segments**.

### TCP vs. UDP

| Feature | TCP | UDP |
|---|---|---|
| Connection | Required (3-way handshake) | None (connectionless) |
| Reliability | Guaranteed delivery | Best-effort |
| Ordering | Preserved | Not guaranteed |
| Duplicate detection | Yes | No |
| Speed | Slower (overhead) | Faster |
| Use cases | HTTP, SSH, FTP, email | DNS, video streaming, games |

**TCP guarantees** (achieved via sequence numbers, acknowledgments, and retransmission):
1. Delivery confirmation — sender knows data arrived
2. No duplicates — each segment processed exactly once
3. Correct ordering — segments reassembled in order

### QUIC (from lecture)

QUIC (RFC 9000 / HTTP/3) is the modern evolution:
- Runs over **UDP** but reimplements TCP-like reliability
- Integrates **TLS 1.3** encryption (0-RTT connection setup vs. TCP+TLS's 3+ round trips)
- **No head-of-line blocking** — one lost packet doesn't block other streams
- Survives **WiFi → 5G handoff** without dropping connections
- Used by Google, YouTube, and Meta for a major fraction of traffic

## 14.6 Layer 5: Application

Where developers work. Protocols define the language two applications speak over the network.

| Protocol | Port | Description |
|---|---|---|
| **HTTP/HTTPS** | 80 / 443 | Web traffic. HTTPS = HTTP + TLS encryption. |
| **DNS** | 53 (UDP) | Hostname → IP resolution. Hierarchical: root → TLD → authoritative. |
| **SMTP** | 25 / 587 | Email sending. Plaintext by default (1980s!). STARTTLS adds encryption. |
| **SSH** | 22 | Encrypted remote terminal. Replaced Telnet. Supports key-based auth and tunneling. |
| **FTP/SFTP** | 21 / 22 | File transfer. FTP is plaintext (1971). SFTP (over SSH) is encrypted. |

**Key concept:** Many application protocols were designed in the 1980s without security assumptions — plaintext protocols and BGP hijacking remain live threats today. DoH (DNS over HTTPS) and DoT (DNS over TLS) encrypt DNS queries.

## 14.7 Diagnosing Network Problems (from lecture)

The TCP/IP model is a **mental framework for diagnosing failures:** Is this a physical issue (cable broken)? A routing issue (BGP misconfiguration)? An application protocol issue (HTTP error)?

**Layer-based thinking is how professionals isolate problems fast.** The Facebook outage of October 2021 was a BGP (Layer 3) issue — their authoritative DNS servers became unreachable because BGP routes were withdrawn.

---

# 15. Distributed Systems Architecture

## 15.1 The 8-Layer Stack (from Global to Local)

The lecture uses **Petflix** (a fictional Netflix-like streaming service for cat videos) to walk through all 8 layers of a global-scale distributed system. The scenario: Fatima, a graduate student in Karachi, presses play on "Mittens Goes to the Vet" at 10pm on a Friday. Petflix has 200M subscribers and 15M concurrent streams.

| Layer | Name | Function |
|---|---|---|
| 1 | DNS Routing | Route users to nearest healthy datacenter |
| 2 | API Gateway | Authenticate, route requests, circuit breaker |
| 3 | Microservices | Parallel fan-out to multiple services |
| 4 | Data & Caching | Cache hits vs. database queries |
| 5 | CDN | Video served from ISP-local boxes |
| 6 | Pods & Replication | Leader election, consensus |
| 7 | VMs & Containers | Isolation and orchestration |
| 8 | Cores & Threads | Thread scheduling, parallelism |

## 15.2 Layer 1: DNS Routing

When Fatima's phone asks "What is the IP address of `play.petflix.com`?", the request flows through the DNS hierarchy:

1. **Fatima's phone** → ISP DNS Resolver → Root Nameserver → .com Nameserver → **Petflix Authoritative DNS**
2. Petflix's DNS intelligence:
   - Sees the resolver's IP (identifies Karachi)
   - Checks datacenter health and load
   - Returns IP of the **nearest healthy region** (Karachi → Singapore)

**DNS Failover & Load Balancing:**
- If Singapore goes down: health checks detect failure in seconds, DNS stops returning Singapore's IP, next lookup routes to Hong Kong or Tokyo
- **Geographic load balancing:** Smart DNS sometimes routes users to a slightly farther region to avoid overloading a hot datacenter (e.g., Singapore absorbs all of South and Southeast Asia)

**The TTL Problem:**
- DNS answers are **cached** by resolvers
- A cached IP may point to a dead datacenter
- **Solution:** Keep TTLs short (30 seconds) — more DNS traffic but faster failover

## 15.3 Layer 2: API Gateway

The API gateway is the **single entry point** for all backend services.

**Service Registry:** Each service instance registers on startup and sends periodic **heartbeats** to stay registered. If heartbeats stop, the instance is deregistered.

**Load Balancing:** Routes incoming requests to healthy service instances, distributing load evenly.

**Circuit Breaker Pattern:**
- **CLOSED state:** Traffic flows normally to the service
- **OPEN state:** When error rate exceeds a threshold (e.g., >50% failures) → stop sending traffic, return fallback responses immediately
- **HALF-OPEN state:** After a cooldown period, send a single test request. If it succeeds, close the circuit (resume normal traffic). If it fails, keep the circuit open.

This prevents cascading failures — a failing downstream service won't drag down the entire system.

## 15.4 Layer 3-4: Microservices, Data & Caching

Fatima's play request fans out to multiple microservices in parallel: authentication, entitlement checking, video metadata, recommendations, etc.

**Caching layer:**
- **In-memory (Memcached):** Extremely fast, but expensive per byte
- **On disk (Cassandra):** May serve as another cache layer or as "origin" storage

## 15.5 Consistency Spectrum

| Level | Behavior | Use Case |
|---|---|---|
| **Eventual** | Write returns before replication completes; replicas catch up eventually | Analytics, view counts |
| **Session** | User sees their own writes; others may see stale data briefly | Watch lists, user profiles |
| **Strong** | Write synchronously replicates everywhere before returning | Billing, payments |

The right consistency level depends on the data. View counts can tolerate eventual consistency (who cares if the count is off by a few?). But billing must be strongly consistent (you can't charge someone twice or miss a charge).

## 15.6 Layer 5: CDN (Content Delivery Network)

- **Serving boxes installed inside ISPs worldwide** — as close to users as physically possible
- **Pre-loaded overnight** with popular content (the most-watched cat videos)
- **Cache miss:** Fetch from origin datacenter
- **Win-win:** Lower latency for users, reduced bandwidth costs for both ISP and content provider

**Adaptive Bitrate Streaming:**
- Video encoded at **multiple quality levels** (480p, 720p, 1080p, 4K)
- Player monitors available bandwidth and **switches quality at chunk boundaries** (e.g., every 2–4 seconds of video)
- **Per-title encoding:** Static scenes (a sleeping cat) need lower bitrate than action scenes (a cat chase) at the same perceived quality

## 15.7 Layer 6: Pods & Replication

Leader election and consensus protocols keep the system running when individual nodes fail. This connects back to the replication (Section 11) and 2PC/consensus (Section 13) concepts.

## 15.8 Layer 7: VMs & Containers

| Aspect | VM (Virtual Machine) | Container |
|---|---|---|
| Isolation | Own OS kernel (hypervisor) | Shared host kernel |
| Overhead | Higher (full OS per VM) | Lower (just the process + dependencies) |
| Security | Stronger (hypervisor boundary) | Weaker (kernel bug affects all containers) |
| Startup | Slower (boot an OS) | Faster (start a process) |

**Kubernetes** orchestrates containers — it handles scheduling (which machine runs which container), scaling (spin up more copies under load), healing (restart failed containers), and deployment (rolling updates).

## 15.9 Layer 8: Cores & Threads

**Concurrency vs. Parallelism:**
- **Concurrency:** Managing multiple tasks logically — they may interleave on a single core
- **Parallelism:** Actually executing multiple tasks at the same physical instant on multiple cores

Example: Petflix may have 1,000 concurrent streams being served, but only 16 running *truly in parallel* on a 16-core machine. The OS scheduler rapidly switches between the other 984 streams, giving the illusion of simultaneity.

## 15.10 Thundering Herd & Retry Storms (from lecture)

**Thundering herd:** A sudden burst of incoming requests that defies usual traffic patterns (e.g., a viral video, a major event, or recovery from an outage where all cached data expires simultaneously).

**Retry storm:** When a service starts failing, clients retry their requests. This *increases* the load on the already struggling service, causing a cascading failure. Mitigation strategies include:
- **Exponential backoff:** Wait longer between each retry
- **Jitter:** Add randomness to retry timing so clients don't all retry simultaneously
- **Circuit breakers:** Stop retrying entirely after a threshold

---

*Good luck on the exam!*
