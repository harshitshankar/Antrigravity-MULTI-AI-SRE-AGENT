# KEDB Entry: KEDB-0027

## Problem
HikariPool connection pool exhaustion.

## Symptoms
- HTTP 500 errors returned to clients on database-dependent endpoints.
- Log entries containing:
  - `HikariPool exhausted`
  - `Connection is not available, request timed out`
  - `Database timeout after 30000ms`
- Metrics show database connection wait times spikes (e.g., >10000ms).
- Active database connections equal to maximum pool size (e.g., 100/100).

## Root Cause
Connection pool size is set too low for peak traffic, or application code is failing to close database connections properly, causing a connection leak.

## Resolution
1. **Immediate Remediation**: Increase the maximum pool size configuration temporarily (e.g., set `spring.datasource.hikari.maximum-pool-size` to `150`).
2. **Leak Detection**: Enable leak detection threshold in the connection pool config (e.g., `leak-detection-threshold=2000ms`).
3. **Scale Database**: Scale read replicas if the database CPU is also high.
4. **Code Fix**: Audit recent code commits for database connection leaks (e.g., unclosed transactions).
