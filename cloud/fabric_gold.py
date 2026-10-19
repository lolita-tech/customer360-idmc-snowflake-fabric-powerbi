# Fabric notebook starter: attach a Lakehouse before executing.
# NOT locally executed: requires the Fabric Spark runtime.
# Copy Snowflake DIM_CUSTOMER and FACT_ORDER into Files/customer360/<batch>/
# as Parquet folders named dim_customer and fact_order. Use an immutable batch.
from pyspark.sql import functions as F
batch_id = "snapshot-001"  # Parameterize from the orchestration run.
base = f"Files/customer360/{batch_id}"
dim = spark.read.parquet(f"{base}/dim_customer").toDF("golden_id", "name", "region", "survivor_source")
fact = spark.read.parquet(f"{base}/fact_order").toDF("source", "order_id", "golden_id", "amount_cents", "currency")
# Configure Copy column order to match the contracts above; use explicit column
# mapping when adapting the starter to another source schema.
assert dim.filter(F.col("golden_id").isNull()).count() == 0
assert dim.groupBy("golden_id").count().filter("count > 1").count() == 0
assert fact.groupBy("source", "order_id").count().filter("count > 1").count() == 0
assert fact.filter("source IS NULL OR order_id IS NULL OR golden_id IS NULL OR amount_cents IS NULL OR amount_cents < 0 OR currency IS NULL OR currency <> 'USD'").count() == 0
assert fact.join(dim.select("golden_id"), "golden_id", "left_anti").count() == 0
# Fixture-specific gates: replace with trusted batch manifest values for new data.
assert fact.count() == 3
assert fact.agg(F.sum("amount_cents")).first()[0] == 20000
# These writes are individually atomic; the pair is NOT a single transaction.
# Block downstream refresh until both writes and validation finish successfully.
dim.write.format("delta").mode("overwrite").saveAsTable("dim_customer")
fact.write.format("delta").mode("overwrite").saveAsTable("fact_order")
