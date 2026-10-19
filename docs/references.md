# Primary implementation references

Reviewed for this design on 2026-10-19. Follow your tenant/version documentation for changing connector capabilities and entitlements.

- [Fabric Snowflake connector](https://learn.microsoft.com/en-us/fabric/data-factory/connector-snowflake-overview)
- [Fabric Copy configuration and staging requirements](https://learn.microsoft.com/en-us/fabric/data-factory/connector-snowflake-copy-activity)
- [Fabric Snowflake connection and authentication](https://learn.microsoft.com/en-us/fabric/data-factory/connector-snowflake)
- [Snowflake MERGE and duplicate-source behavior](https://docs.snowflake.com/en/sql-reference/sql/merge)
- [Informatica Business 360 Connector mappings](https://docs.informatica.com/integration-cloud/cloud-data-integration-connectors/current-version/business-360-connector/mappings-with-business-360-connector-overview.html)
- [Business 360 FEP task and object types](https://docs.informatica.com/integration-cloud/cloud-data-integration-connectors/current-version/business-360-fep-connector/business-360-fep-connector/business-360-fep-connector-task-and-object-types.html)
- [Informatica Snowflake SQL ELT function syntax](https://docs.informatica.com/integration-cloud/data-integration-free-and-paygo/current-version/snowflake-data-cloud-connector/part-3--sql-elt-with-snowflake-data-cloud-connector/mappings-in-sql-elt-mode-for-snowflake-data-cloud/functions-in-mappings-in-sql-elt-mode.html)

The architecture is a portfolio design, not a vendor-endorsed reference architecture. The tests verify local Python/SQLite behavior only.
