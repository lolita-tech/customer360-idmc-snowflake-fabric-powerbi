import copy
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from src.pipeline import build, run, export

class Customer360Tests(unittest.TestCase):
    def setUp(self):
        self.data=json.loads(Path("data/sample.json").read_text())
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.db=str(Path(self.tmp.name)/"test.db")
    def run_batch(self,batch="b1",**kw):
        return run(self.data["customers"],self.data["orders"],self.db,batch,**kw)
    def model(self): return build(self.data["customers"],self.data["orders"])
    def test_reconciliation(self):
        r=self.run_batch()
        self.assertEqual((r["golden_customers"],r["accepted_orders"],r["rejected_rows"],r["revenue_cents"]),(2,3,6,20000))
    def test_survivorship(self):
        self.assertIn({"name":"Avery Example","region":"East","survivor_source":"crm"},[{k:v for k,v in r.items() if k!="golden_id"} for r in self.model()["dim_customer"]])
    def test_no_email_only_merge(self):
        self.assertEqual(sum(r["reason"]=="EMAIL_ID_CONFLICT" for r in self.model()["exceptions"]),2)
    def test_missing_trusted_id(self):
        self.assertIn("MISSING_TRUSTED_ID",[r["reason"] for r in self.model()["exceptions"]])
    def test_orphan_rejected(self):
        self.assertEqual(sum(r["reason"]=="UNRESOLVED_CUSTOMER" for r in self.model()["exceptions"]),2)
    def test_currency_rejected(self):
        self.assertEqual(sum(r["reason"]=="UNSUPPORTED_CURRENCY" for r in self.model()["exceptions"]),1)
    def test_replay(self):
        self.run_batch()
        self.assertEqual(self.run_batch()["status"],"replay_skipped")
        with sqlite3.connect(self.db) as c:self.assertEqual(c.execute("SELECT count(*) FROM fact_order").fetchone()[0],3)
    def test_changed_batch_rejected(self):
        self.run_batch();self.data["orders"][0]["amount_cents"]=1
        with self.assertRaises(ValueError): self.run_batch()
    def test_rollback_preserves_previous_snapshot(self):
        self.run_batch();self.data["orders"][0]["amount_cents"]=1
        with self.assertRaises(RuntimeError): self.run_batch("b2",fail_before_commit=True)
        with sqlite3.connect(self.db) as c:
            self.assertEqual(c.execute("SELECT sum(amount_cents) FROM fact_order").fetchone()[0],20000)
            self.assertEqual(c.execute("SELECT count(*) FROM run_audit").fetchone()[0],1)
    def test_conflicting_source_key(self):
        r=copy.deepcopy(self.data["customers"][0]);r["name"]="Conflict"
        self.data["customers"].append(r)
        with self.assertRaises(ValueError):self.model()
    def test_exact_duplicate_deduplicated(self):
        self.data["orders"].append(copy.deepcopy(self.data["orders"][0]))
        self.assertEqual(len(self.model()["fact_order"]),3)
    def test_negative_and_boolean_amount_rejected(self):
        for amount in (-1,True):
            self.data["orders"][0]["amount_cents"]=amount
            self.assertIn("INVALID_AMOUNT",[r["reason"] for r in self.model()["exceptions"]])
    def test_snapshot_removal(self):
        self.run_batch();self.data["orders"]=self.data["orders"][1:]
        self.assertEqual(self.run_batch("b2")["revenue_cents"],10000)
    def test_input_order_does_not_change_identity(self):
        before=self.model();self.data["customers"].reverse();self.data["orders"].reverse()
        self.assertEqual(before,self.model())
    def test_export(self):
        self.run_batch();export(self.db,Path(self.tmp.name)/"exports")
        self.assertTrue((Path(self.tmp.name)/"exports/fact_order.csv").read_text().startswith("source,order_id,golden_id"))

if __name__ == "__main__": unittest.main()
