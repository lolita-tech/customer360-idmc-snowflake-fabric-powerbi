# Architecture and contracts

The local demo evaluates business rules; the cloud path needs native implementation and acceptance testing.

## Responsibilities
| Component | Responsibility | Durable output |
|---|---|---|
| IDMC CDI | Read source snapshots, standardize formats, route failures, orchestrate tasks | Raw rows with source and batch metadata |
| Informatica MDM SaaS | Manage Customer entity, source records, match/merge, survivorship and stewardship | Vendor-generated master ID, source crosswalk and unresolved records |
| Snowflake | Reconcile orders against the approved crosswalk; publish governed batches | Customer dimension, order fact, exceptions and manifest |
| Fabric Data Factory | Copy one completed publication batch | Isolated Lakehouse staging files |
| Fabric Spark | Validate keys, relationships and totals; materialize Delta tables | Gold tables |
| Power BI | Model one-to-many relationships and expose revenue/quality KPIs | Semantic model and dashboard |

Local contracts: customer source key = `(source, customer_id)`; order key = `(source, order_id)`; money = nonnegative integer cents; only USD; trusted loyalty ID identifies one person for this exercise. Production identities use MDM IDs, not email hashes. The demo's synthetic hashed ID is not anonymization, encryption or an enterprise identity strategy.

Email is only a conflict signal. Shared emails with different trusted IDs are withheld. Missing IDs are unresolved. CRM takes precedence over shop for the entire surviving record. Within the same source, lexicographic source key breaks ties deterministically; it is not recency-based survivorship. Production needs field-specific trust, timestamps, steward decisions and unmerge history.

## Safe batch publication
1. IDMC lands a complete immutable batch with manifest (expected files, row counts and currency totals).
2. Wait for MDM ingress and matching completion, then export masters AND crosswalk for that batch. Never join on name/email.
3. Validate staging; reject duplicate keys or conflicting payloads. Reconcile raw accepted/rejected orders per currency.
4. Publish all Snowflake tables under one batch ID and mark the manifest COMPLETE only after a successful transaction.
5. Fabric copies that exact batch to an isolated path and revalidates counts/sums. Record source batch and run IDs.
6. Refresh the Power BI Import model only after all gold tables are ready. The starter overwrites individual Delta tables; it is NOT an atomic multi-table publish. In production retain versioned batches and switch a serving manifest/view or use an orchestrated cutover.

## Trade-offs and open risks
The local snapshot replacement handles removals but reprocesses all rows. At scale use CDC with persisted watermarks, delete semantics, late-arriving handling and retry-safe stage/commit gates. Never advance watermarks on an incomplete batch. SQL UNIQUE/PRIMARY KEY declarations on standard Snowflake tables are not sufficient enforcement; explicit validation is required. Keep stewardship data restricted and send operational alerts with run IDs, not PII.

Failure drill: inject a failure before local commit and verify prior facts AND run ledger remain unchanged. Native systems require separate recovery tests because there is no distributed transaction across IDMC, MDM, Snowflake, Fabric and Power BI.
