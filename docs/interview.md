# Interview questions and answers

**Why MDM before reporting?** Source IDs identify source records, not necessarily distinct people. A governed master and crosswalk make identity explicit and auditable.

**Why not merge on email?** Shared addresses, recycled addresses and typos can join unrelated people. This demo requires a trusted ID and holds contradictory email/ID pairs for review.

**Does Python implement Informatica MDM?** No. It tests a small business-rule contract locally. Native matching, governance and stewardship require a licensed MDM tenant and separate acceptance evidence.

**How do you prevent double revenue?** Source-qualified order keys, exact duplicate collapse, conflicting duplicate rejection and a replay ledger. Transactions keep the fact tables and successful ledger entry consistent.

**Why full snapshots?** They make corrections and removals understandable in a small reproducible example. They cost more to process and require completeness checks. CDC is a separate extension with delete and late-event handling.

**Why Snowflake and Fabric together?** This illustrates an enterprise with Snowflake as governed storage and Fabric/Power BI as Microsoft analytics. The trade-off is duplicated storage, transfer cost and more failure boundaries; a single platform can be simpler when requirements permit it.

**Are Delta writes an end-to-end transaction?** No. Each table write is atomic, but publication across several tables/services needs batch isolation and a serving cutover protocol.

**What can you honestly claim now?** A tested local implementation and documented native deployment design. Native tenant operation, performance tuning results and a published report need further execution evidence.
