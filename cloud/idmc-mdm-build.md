# Native IDMC and Informatica MDM build specification

**Manual configuration specification, not an importable Informatica export. Not executed in a tenant.** UI names and connector availability depend on entitlement and release. Target: MDM SaaS Customer 360 / Business 360. Do not import this into Multidomain MDM Hub.

1. Create DEV project `Customer360Portfolio`. Configure approved runtime and connections to the source files, Snowflake and Business 360 supported by your tenant. Store credentials in managed connections, never in Git.
2. Define mapping `m_customer_landing`: Source customer snapshot → Expression for trimmed source key and normalized email → Router for mandatory-key checks → Snowflake raw target and reject target. Preserve original values and append `batch_id`, `source`, `ingested_at`.
3. Define `m_order_landing` similarly; preserve integer cents and original currency, reject invalid numeric values rather than silently coercing them. Stage immutable source records first.
4. In Business 360 configure Customer entity fields: source system, source ID, trusted loyalty ID, name, email, region. Configure source systems CRM and SHOP, record provenance and source-key uniqueness.
5. Configure and test matching on validated trusted loyalty ID. Shared email with contradictory trusted IDs must be a stewardship case; this may require a quality/pre-ingress gate and custom configuration rather than a built-in setting. Do not auto-merge on email alone.
6. Configure survivorship with CRM preferred to SHOP. Test null handling, two same-source candidates, corrections and manual overrides. The local demo uses whole-record preference; native field-level trust requires a separate test matrix.
7. Build ingress mapping/job with the supported Business 360 connector and wait for success. Run match/merge using the tenant's documented job orchestration. Review candidate merges and unresolved cases in the steward interface.
8. Egress master records plus source crosswalk using supported connector/jobs. Map the actual MDM master identifier to `golden_id`; populate Snowflake curated staging. Do not assume a fabricated REST endpoint or connector export format.
9. Order taskflow: land source batch → validate manifest → MDM ingress → match/merge completion → egress → validate Snowflake → publish → Fabric copy → gold validation → semantic model refresh. Failure branches stop publication and record run ID, job ID, stage and sanitized error.
10. Export the actual native assets from your tenant after successful tests; scan for connection secrets and private endpoints before adding sanitized exports here.

Acceptance cases: one master for C1/S1; no automatic merge of S3/C4; missing trusted ID is unresolved; all crosswalk keys unique; held customer orders excluded; rerun creates no duplicate master/order rows. Capture native results rather than assuming parity with Python.
