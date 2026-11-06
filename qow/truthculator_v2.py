"""Multi-parent ancestry and fresh Z3 re-execution, fail-closed."""
from .truthculator import Truthculator,verify_receipt,canonical,digest

class TruthculatorV2(Truthculator):
    def compute(self,claim_id,claim_text,declarations,axioms,hypothesis,parent_hashes=None):
        parents=list(parent_hashes or [])
        known={r["receipt_hash"] for r in self.receipts}
        if len(set(parents))!=len(parents) or any(p not in known for p in parents):
            raise ValueError("duplicate or unavailable DAG parent")
        receipt=super().compute(claim_id,claim_text,declarations,axioms,hypothesis)
        body=receipt["body"]
        body["parent_hashes"]=parents
        body["external_gates"]={k:"NOT_VERIFIED" for k in ("tee","witness_quorum","rfc3161","zk","raft","cloud","physical_camera")}
        body["does_not_prove"].append("parent references imply the child logically depends on their theorems")
        raw=canonical(body)
        receipt["receipt_hash"]=digest(raw)
        receipt["signature"]=self.sk.sign(raw).hex()
        self.receipts[-1]=receipt
        self.last_hash=receipt["receipt_hash"]
        return receipt

def independently_recheck(receipt,pinned_pubkey):
    auth=verify_receipt(receipt,pinned_pubkey)
    if not auth["ok"]:
        return {"ok":False,"reason":"signature/hash invalid"}
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    b=receipt["body"]
    independent=Truthculator(Ed25519PrivateKey.generate(),timeout_ms=5000)
    computed=independent.compute(b["claim_id"],b["claim_text"],b["declarations"],b["axioms"],b["hypothesis"])["body"]
    ok=computed["verdict"]==b["verdict"] and computed["axioms_consistent"]==b["axioms_consistent"]
    return {"ok":ok,"verdict":computed["verdict"],"claimed":b["verdict"],
            "method":"fresh local Z3 re-execution","independent_proof_certificate":False}

def verify_dag(receipts,pinned_pubkey):
    seen=set()
    for r in receipts:
        if not verify_receipt(r,pinned_pubkey)["ok"]:
            return {"ok":False,"reason":"invalid signature/hash"}
        parents=r["body"].get("parent_hashes",[])
        if len(set(parents))!=len(parents) or any(p not in seen for p in parents):
            return {"ok":False,"reason":"unresolved/forward/duplicate parent"}
        seen.add(r["receipt_hash"])
    return {"ok":True,"nodes":len(seen),"does_not_prove":"logical inheritance"}
