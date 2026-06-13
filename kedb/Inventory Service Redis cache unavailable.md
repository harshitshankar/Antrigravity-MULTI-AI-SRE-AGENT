KEDB Entry: KEDB-0030

Problem
Inventory Service Redis cache unavailable.

Symptoms

Product availability checks become slow.

Log entries containing:

RedisConnectionFailureException
Connection refused
Unable to connect to Redis
Inventory API latency increases from 50ms to >1500ms.
Database CPU utilization spikes.
Cache hit ratio drops to nearly 0%.

Root Cause
Redis instance outage, network disruption, or exhausted Redis resources causing cache failures.

Resolution

Immediate Remediation: Fail over to Redis replica or restart Redis pods.
Database Protection: Enable request throttling to reduce database load.
Infrastructure Check: Verify Redis memory utilization and node health.
Code Fix: Implement graceful cache fallback and proper retry policies.
