-- DEV starter, not executed on Snowflake. Run in a dedicated empty lab schema.
-- Existing active warehouse and a role allowed to create a schema are prerequisites.
CREATE SCHEMA IF NOT EXISTS CUSTOMER360_LAB;
USE SCHEMA CUSTOMER360_LAB;
ALTER SESSION SET ERROR_ON_NONDETERMINISTIC_MERGE = TRUE;
CREATE TABLE IF NOT EXISTS DIM_CUSTOMER_STAGE (
  golden_id VARCHAR, name VARCHAR, region VARCHAR, survivor_source VARCHAR
);
CREATE TABLE IF NOT EXISTS FACT_ORDER_STAGE (
  source VARCHAR, order_id VARCHAR, golden_id VARCHAR,
  amount_cents NUMBER(18,0), currency VARCHAR
);
CREATE TABLE IF NOT EXISTS DIM_CUSTOMER LIKE DIM_CUSTOMER_STAGE;
CREATE TABLE IF NOT EXISTS FACT_ORDER LIKE FACT_ORDER_STAGE;
-- Populate staging from one complete validated publication batch. For the local
-- demonstration, upload dim_customer.csv and fact_order.csv using Snowsight.
-- Check loader column mapping, header skipping and rejection report first.

-- Gate the full snapshot replacement. DISTINCT collapses exact duplicate rows;
-- conflicting keys still fail. This anonymous block performs no external I/O.
EXECUTE IMMEDIATE $$
DECLARE
  bad_rows INTEGER;
  invalid_batch EXCEPTION (-20001, 'Customer360 staging validation failed');
BEGIN
  SELECT COUNT(*) INTO :bad_rows FROM (
    SELECT golden_id FROM (SELECT DISTINCT * FROM DIM_CUSTOMER_STAGE)
    GROUP BY golden_id HAVING COUNT(*) > 1
    UNION ALL
    SELECT order_id FROM (SELECT DISTINCT * FROM FACT_ORDER_STAGE)
    GROUP BY source, order_id HAVING COUNT(*) > 1
  );
  IF (bad_rows > 0) THEN RAISE invalid_batch; END IF;
  SELECT COUNT(*) INTO :bad_rows FROM FACT_ORDER_STAGE f
  WHERE f.source IS NULL OR f.order_id IS NULL OR f.golden_id IS NULL
     OR f.currency IS NULL OR f.currency <> 'USD'
     OR f.amount_cents IS NULL OR f.amount_cents < 0
     OR NOT EXISTS (SELECT 1 FROM DIM_CUSTOMER_STAGE d WHERE d.golden_id=f.golden_id);
  IF (bad_rows > 0) THEN RAISE invalid_batch; END IF;
  SELECT COUNT(*) INTO :bad_rows FROM DIM_CUSTOMER_STAGE
  WHERE golden_id IS NULL OR region IS NULL;
  IF (bad_rows > 0) THEN RAISE invalid_batch; END IF;
  BEGIN TRANSACTION;
  DELETE FROM FACT_ORDER;
  DELETE FROM DIM_CUSTOMER;
  INSERT INTO DIM_CUSTOMER SELECT DISTINCT * FROM DIM_CUSTOMER_STAGE;
  INSERT INTO FACT_ORDER SELECT DISTINCT * FROM FACT_ORDER_STAGE;
  COMMIT;
EXCEPTION
  WHEN OTHER THEN
    ROLLBACK;
    RAISE;
END;
$$;
SELECT COUNT(*) AS accepted_orders, SUM(amount_cents) AS revenue_cents FROM FACT_ORDER;
-- Expected fixture: 3 orders, 20000 cents. Never sum mixed currencies.
-- Production: stage per batch, validate completeness/counts before this block,
-- use a single writer, add a publication manifest and customer-crosswalk table.
