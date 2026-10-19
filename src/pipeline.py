"""Synthetic snapshot demo; standard library only, not an Informatica runtime."""
import argparse
import hashlib
import json
import sqlite3
from collections import defaultdict
from pathlib import Path


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def unique(rows, keys):
    result = {}
    for row in rows:
        key = tuple(row[k] for k in keys)
        if key in result and result[key] != row:
            raise ValueError(f"Conflicting source key: {key}")
        result[key] = row
    return list(result.values())


def build(customers, orders):
    # Input is a COMPLETE snapshot, not a change feed. Identity requires a trusted
    # synthetic loyalty ID. Email alone is never sufficient to merge customers.
    customers = unique(customers, ("source", "customer_id"))
    orders = unique(orders, ("source", "order_id"))
    groups, email_ids = defaultdict(list), defaultdict(set)
    rejects = []
    for r in customers:
        if r["source"] not in ("crm", "shop"):
            raise ValueError("Unsupported customer source")
        email = r["email"].strip().lower()
        if r["loyalty_id"]:
            email_ids[email].add(r["loyalty_id"])
    for r in customers:
        email = r["email"].strip().lower()
        reason = None
        if not r["loyalty_id"]:
            reason = "MISSING_TRUSTED_ID"
        elif not email or "@" not in email:
            reason = "INVALID_EMAIL"
        elif len(email_ids[email]) > 1:
            reason = "EMAIL_ID_CONFLICT"
        if reason:
            rejects.append({"entity":"customer", "source":r["source"], "key":r["customer_id"], "reason":reason})
        else:
            groups[r["loyalty_id"]].append(r)
    golden, crosswalk = [], []
    for loyalty_id, rows in sorted(groups.items()):
        # Stable only while trusted ID remains stable. Production uses MDM IDs.
        gid = "G_" + hashlib.sha256(loyalty_id.encode()).hexdigest()[:20]
        winner = sorted(rows, key=lambda r: (0 if r["source"] == "crm" else 1, r["customer_id"]))[0]
        golden.append({"golden_id":gid, "name":winner["name"], "region":winner["region"], "survivor_source":winner["source"]})
        crosswalk.extend({"source":r["source"], "customer_id":r["customer_id"], "golden_id":gid} for r in rows)
    lookup = {(r["source"],r["customer_id"]):r["golden_id"] for r in crosswalk}
    facts = []
    for r in orders:
        gid = lookup.get((r["source"],r["customer_id"]))
        reason = None
        if r["currency"] != "USD":
            reason = "UNSUPPORTED_CURRENCY"
        elif type(r["amount_cents"]) is not int or r["amount_cents"] < 0:
            reason = "INVALID_AMOUNT"
        elif gid is None:
            reason = "UNRESOLVED_CUSTOMER"
        if reason:
            rejects.append({"entity":"order", "source":r["source"], "key":r["order_id"], "reason":reason})
        else:
            facts.append({"source":r["source"], "order_id":r["order_id"], "golden_id":gid, "amount_cents":r["amount_cents"], "currency":r["currency"]})
    return {"dim_customer":golden, "customer_crosswalk":sorted(crosswalk,key=lambda r:(r["source"],r["customer_id"])),
            "fact_order":sorted(facts,key=lambda r:(r["source"],r["order_id"])),
            "exceptions":sorted(rejects,key=lambda r:(r["entity"],r["source"],r["key"]))}

SCHEMA = """
CREATE TABLE IF NOT EXISTS dim_customer(golden_id TEXT PRIMARY KEY, name TEXT, region TEXT, survivor_source TEXT);
CREATE TABLE IF NOT EXISTS customer_crosswalk(source TEXT, customer_id TEXT, golden_id TEXT REFERENCES dim_customer, PRIMARY KEY(source,customer_id));
CREATE TABLE IF NOT EXISTS fact_order(source TEXT, order_id TEXT, golden_id TEXT REFERENCES dim_customer, amount_cents INTEGER CHECK(amount_cents>=0), currency TEXT CHECK(currency='USD'), PRIMARY KEY(source,order_id));
CREATE TABLE IF NOT EXISTS exceptions(entity TEXT, source TEXT, key TEXT, reason TEXT);
CREATE TABLE IF NOT EXISTS run_audit(batch_id TEXT PRIMARY KEY, fingerprint TEXT, accepted_orders INTEGER, rejected_rows INTEGER, revenue_cents INTEGER);
"""


def run(customers, orders, db, batch_id, fail_before_commit=False):
    model = build(customers, orders)
    fingerprint = hashlib.sha256(canonical({"customers": sorted(customers,key=canonical), "orders":sorted(orders,key=canonical)}).encode()).hexdigest()
    con = sqlite3.connect(db)
    try:
        con.execute("PRAGMA foreign_keys=ON")
        con.executescript(SCHEMA)
        con.execute("BEGIN IMMEDIATE")
        old = con.execute("SELECT fingerprint FROM run_audit WHERE batch_id=?", (batch_id,)).fetchone()
        if old:
            if old[0] != fingerprint:
                raise ValueError("Batch ID reused with different content")
            con.rollback()
            return {"status":"replay_skipped", "batch_id":batch_id}
        for table in ("fact_order", "customer_crosswalk", "dim_customer", "exceptions"):
            con.execute(f"DELETE FROM {table}")
        for table, rows in model.items():
            for row in rows:
                con.execute(f"INSERT INTO {table} ({','.join(row)}) VALUES ({','.join('?' for _ in row)})", tuple(row.values()))
        result = {"status":"committed", "batch_id":batch_id, "golden_customers":len(model["dim_customer"]),
                  "accepted_orders":len(model["fact_order"]), "rejected_rows":len(model["exceptions"]),
                  "revenue_cents":sum(r["amount_cents"] for r in model["fact_order"])}
        con.execute("INSERT INTO run_audit VALUES(?,?,?,?,?)",(batch_id,fingerprint,result["accepted_orders"],result["rejected_rows"],result["revenue_cents"]))
        if fail_before_commit:
            raise RuntimeError("Injected failure")
        con.commit()
        return result
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()


def export(db, target):
    import csv
    target = Path(target)
    target.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db) as con:
        # One read transaction provides a consistent snapshot across exported files.
        con.execute("BEGIN")
        for table in ("dim_customer", "customer_crosswalk", "fact_order", "exceptions", "run_audit"):
            cur = con.execute(f"SELECT * FROM {table}")
            with (target / (table + ".csv")).open("w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([c[0] for c in cur.description])
                writer.writerows(cur)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data/sample.json")
    parser.add_argument("--db", default="output/demo.db")
    parser.add_argument("--batch", default="snapshot-001")
    args = parser.parse_args()
    Path(args.db).parent.mkdir(parents=True,exist_ok=True)
    data = json.loads(Path(args.data).read_text())
    print(json.dumps(run(data["customers"],data["orders"],args.db,args.batch),indent=2))
    export(args.db, Path(args.db).parent / "exports")
