"""Fourteen executable QoW review-branch acceptance tests."""
import copy,tempfile,unittest
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from qow.truthculator import pubkey_hex,verify_receipt
from qow.truthculator_v2 import TruthculatorV2,verify_dag
from qow.independent_verifier import independent_check
from qow.pop_aggregator import aggregate
from qow.ipqr import encode,decode
from qow.ipqr_scanner import add_fiducials,scan_physical_ipqr
from qow.universal_carrier import UniversalCarrier

class QoWTests(unittest.TestCase):
    def setUp(self):
        self.sk=Ed25519PrivateKey.generate()
        self.pub=pubkey_hex(self.sk)
        self.tc=TruthculatorV2(self.sk,"test")
        self.decl="(declare-const x Int)"
    def mint(self,axioms=None,hyp="(> x 0)",parents=None):
        return self.tc.compute("A","test",self.decl,
            axioms if axioms is not None else ["(> x 5)"],hyp,parents)
    def test_proven(self):
        self.assertEqual(self.mint()["body"]["verdict"],"PROVEN_TRUE")
    def test_refuted(self):
        self.assertEqual(self.mint(["(= x 0)"])["body"]["verdict"],"REFUTED_FALSE")
    def test_underdetermined(self):
        self.assertEqual(self.mint(["(>= x 0)"],"(> x 0)")["body"]["verdict"],"NOT_ENTAILED")
    def test_inconsistent(self):
        self.assertEqual(self.mint(["(> x 5)","(< x 0)"])["body"]["verdict"],"INCONSISTENT_AXIOMS")
    def test_independent(self):
        self.assertTrue(independent_check(self.mint(),self.pub)["ok"])
    def test_tamper(self):
        r=self.mint()
        r["body"]["verdict"]="PROVEN_TRUE_TAMPER"
        self.assertFalse(verify_receipt(r,self.pub)["ok"])
    def test_pin(self):
        self.assertFalse(verify_receipt(self.mint(),"00"*32)["ok"])
    def test_dag(self):
        a=self.mint();b=self.mint()
        c=self.mint(parents=[a["receipt_hash"],b["receipt_hash"]])
        self.assertTrue(verify_dag([a,b,c],self.pub)["ok"])
    def test_missing_parent(self):
        with self.assertRaises(ValueError):
            self.mint(parents=["sha256:"+"a"*64])
    def test_merkle(self):
        self.assertEqual(aggregate([self.mint()],self.pub)["leaf_count"],1)
    def test_merkle_rejects_tamper(self):
        r=self.mint()
        r["signature"]="00"
        with self.assertRaises(ValueError):
            aggregate([r],self.pub)
    def test_optical(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"test.png"
            r=self.mint()
            encode(r,p)
            add_fiducials(p)
            self.assertEqual(decode(p),r)
            self.assertTrue(scan_physical_ipqr(p,self.pub)["signature"]["ok"])
    def test_pdf_attachment(self):
        from pypdf import PdfReader
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"receipt.pdf"
            UniversalCarrier(self.mint(),self.pub).embed_in_pdf(p)
            self.assertTrue(PdfReader(p).attachments)
    def test_model_sidecar(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"model.gguf";p.write_bytes(b"abc")
            sidecar=Path(d)/"model.gguf.ipqr.json"
            UniversalCarrier(self.mint(),self.pub).embed_in_model_weights(p,sidecar)
            self.assertEqual(p.read_bytes(),b"abc")
            self.assertTrue(sidecar.exists())
if __name__=="__main__":
    unittest.main()
