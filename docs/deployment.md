# Deployment and validation

## Free local route
Clone the repository, enter the cloned repository directory, run tests and run `python src/pipeline.py`. No pip installation or secrets are needed. CSVs can be imported into Power BI Desktop; using the Desktop demo does not prove Power BI Service or Fabric deployment.

## Licensed native route (pending)
1. Provision isolated DEV environments only after checking entitlements and costs. Choose a Snowflake Azure region compatible with your network/security requirements. Fabric and Snowflake remain separate services and charges.
2. Follow `cloud/idmc-mdm-build.md`. Start with the included synthetic fixture. Record native job IDs and master/crosswalk outputs.
3. Run `cloud/snowflake.sql` in a dedicated schema with an active, small warehouse. Load the approved MDM egress and curated order batch into the stage tables before the validation/publish block. The SQL models snapshot publication, not native MDM execution or CDC.
4. In Fabric create a workspace, Lakehouse and Data Factory pipeline. Add Snowflake connection using an authentication method supported by the connector and tenant. Configure two Copy activities reading the certified dimension and fact, writing Parquet to isolated batch folders. Follow Microsoft's connector-specific staging/storage-integration requirements; the exact configuration depends on source cloud and selected copy path.
5. Attach the Lakehouse to a notebook and adapt/run `cloud/fabric_gold.py`. Explicitly map source column names/types before publication. Wait for both outputs and quality gates before refresh.
6. Create the semantic model and report using `docs/powerbi-demo.md`. Validate SQL totals, Spark totals and report cards against the same batch.
7. Capture run IDs, screenshots and elapsed times honestly. Mark native cloud stages verified only after running them. Record cloud costs with the measured period; no cost or speed benchmark is supplied here.

## Access and cleanup
Use separate least-privilege service identities for ingestion, mastering, publishing and reporting. Never commit tokens, private keys, connection exports or tenant URLs. Curated serving data excludes email and loyalty ID; restrict raw and steward data. RLS in a report is not a substitute for restricting source access.

Suspend unused Snowflake warehouses, stop scheduled jobs and remove lab staging data/resources when finished. Fabric capacity and Power BI sharing requirements depend on the environment; local execution requires neither.

## Recovery exercises
- Change O1 to a negative amount; inspect quarantine and reconcile the reduced certified revenue.
- Give S3 the same trusted ID as C4 and submit a NEW complete snapshot; explain why steward approval is required before using that correction in production.
- Run the same batch twice; then reuse its ID with a changed amount and observe rejection.
- Run the rollback unit test; show that partial writes and their audit entry do not commit.
- Fail the second Fabric write in a lab. Verify downstream refresh is blocked; restore both tables from the previous publication batch.
