# Dashboard build and demonstration

No PBIX, screenshot or cloud report is claimed as completed. This is the build checklist for a real report.

1. Run the local demo. In Power BI Desktop choose Get data → Text/CSV and import `dim_customer`, `fact_order`, `exceptions`, `run_audit` from `output/exports`.
2. Set keys to text, amount_cents to whole number, region/source to text. Create `dim_customer[golden_id]` 1 → many `fact_order[golden_id]`, single-direction filtering.
3. Keep exceptions and run_audit disconnected in this small demo. Add measures from `cloud/measures.dax` separately.
4. Build overview cards: Revenue USD = 200.00, Order Count = 3, Customers With Orders = 2, Average Order Value USD = 66.67 (formatted to 2 decimals).
5. Add revenue by region: East 125.00, West 75.00. Add detail table with source, order ID and amount. Order IDs alone are not globally unique.
6. Create an operations page: 3 rejected customers and 3 rejected orders, exception reason table and batch audit. Do not label disconnected exceptions as region-filtered metrics.
7. For Fabric replace CSV sources with validated gold tables through the Lakehouse SQL endpoint and an Import model for the first native demo. Do not write Delta tables through the SQL endpoint.
8. If adding RLS, create a separate user-to-region security design and test authorized/unauthorized users in the Service. Static sample filters are not evidence of deployed security.

Record a 3-minute video: 30s business scenario, 45s architecture, 45s passing tests and replay, 45s report reconciliation, 15s cloud status. Screenshot only real terminal/report output; remove tenant identifiers and secrets. Add verified screenshots under evidence/ after building the report.
