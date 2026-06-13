KEDB Entry: KEDB-0028

Problem
Order Service Kafka consumer lag increasing rapidly.

Symptoms

Customer orders remain in PENDING state for extended periods.

Log entries containing:

Consumer lag exceeded threshold
Commit offset delay detected
Poll timeout exceeded
Kafka metrics show consumer lag > 50,000 messages.
Order processing throughput drops significantly.
Alerts triggered for delayed order fulfillment.

Root Cause
Order Service consumers cannot process messages fast enough due to insufficient consumer replicas, increased order volume, or slow downstream dependencies.

Resolution

Immediate Remediation: Increase Order Service consumer replicas from 3 to 8.
Partition Scaling: Increase Kafka topic partitions if required.
Dependency Check: Verify downstream services (Inventory, Payment) are responding normally.
Code Fix: Optimize message processing logic and eliminate long-running synchronous calls.
