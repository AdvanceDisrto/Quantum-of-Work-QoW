"""SMT-backed, signed receipts. No claim of real-world or hardware truth."""
from __future__ import annotations
import hashlib, json, time, uuid
from datetime import datetime, timezone
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization
import z3

def canonical(obj):
    # Deterministic JSON subset; not RFC 8785 JCS.
    return json.dumps(obj,sort_keys=True,separators=(",",":"),ensure_ascii=False,allow_nan=False).encode("utf-8")
def digest(data):
    return "sha256:"+hashlib.sha256(data).hexdigest()
def pubkey_hex(sk):
    return sk.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw).hex()

def verify_receipt(receipt, pinned_pubkey):
    try:
        body=receipt["body"]
        if body["spec"]!="ipqr/truthculator-receipt/v2":
            raise ValueError("wrong schema")
        if not isinstance(pinned_pubkey,str) or body["issuer_pubkey_hex"]!=pinned_pubkey:
            raise ValueError("public-key pin required / mismatch")
        msg=canonical(body)
        if receipt["receipt_hash"]!=digest(msg):
            raise ValueError("receipt hash mismatch")
        Ed25519PublicKey.from_public_bytes(bytes.fromhex(pinned_pubkey)).verify(bytes.fromhex(receipt["signature"]),msg)
        return {"ok":True,"verdict":body["verdict"],"cryptographic_integrity_only":True}
    except (KeyError,ValueError,TypeError,z3.Z3Exception) as ex:
        return {"ok":False,"errors":[str(ex)]}
    except Exception as ex:
        return {"ok":False,"errors":[type(ex).__name__]}

def _check(declarations, assertions, timeout_ms):
    solver=z3.Solver()
    solver.set("timeout",timeout_ms)
    script=declarations+"\n"+"\n".join("(assert "+a+")" for a in assertions)
    if len(script.encode("utf-8"))>256000:
        raise ValueError("SMT-LIB script exceeds 256 KiB")
    solver.from_string(script)
    result=solver.check()
    return (str(result),str(solver.model()) if result==z3.sat else None,
            solver.reason_unknown() if result==z3.unknown else None)

class Truthculator:
    def __init__(self,private_key:Ed25519PrivateKey,machine_id="qow-local",timeout_ms=5000):
        self.sk=private_key
        self.pubkey=pubkey_hex(private_key)
        self.machine_id=machine_id
        self.timeout_ms=timeout_ms
        self.receipts=[]
        self.last_hash=None
    def compute(self,claim_id,claim_text,declarations,axioms,hypothesis):
        start=time.perf_counter()
        verdict="INSUFFICIENT_EVIDENCE"
        reason="missing formal framework"
        counterexample=None
        consistent=None
        if axioms and hypothesis:
            if not isinstance(axioms,list) or not isinstance(declarations,str) or not isinstance(hypothesis,str):
                raise ValueError("invalid SMT inputs")
            if any(not isinstance(a,str) or not a.strip() for a in axioms):
                raise ValueError("empty or invalid axiom")
            base,_,why=_check(declarations,axioms,self.timeout_ms)
            consistent=base=="sat" if base!="unknown" else None
            if base=="unsat":
                verdict,reason="INCONSISTENT_AXIOMS","axioms inconsistent; entailment disabled"
            elif base=="unknown":
                verdict,reason="UNKNOWN","axiom consistency undecided: "+str(why)
            else:
                neg,model,why=_check(declarations,axioms+["(not "+hypothesis+")"],self.timeout_ms)
                if neg=="unsat":
                    verdict,reason="PROVEN_TRUE","axioms entail hypothesis"
                elif neg=="unknown":
                    verdict,reason="UNKNOWN","counterexample search undecided: "+str(why)
                else:
                    pos,_,why=_check(declarations,axioms+[hypothesis],self.timeout_ms)
                    if pos=="unsat":
                        verdict,reason="REFUTED_FALSE","axioms entail the negated hypothesis"
                    elif pos=="sat":
                        verdict,reason="NOT_ENTAILED","both hypothesis and negation possible"
                    else:
                        verdict,reason="UNKNOWN","hypothesis check undecided: "+str(why)
                    counterexample=model
        body={
            "spec":"ipqr/truthculator-receipt/v2",
            "receipt_id":"urn:qow:"+str(uuid.uuid4()),
            "machine_id":self.machine_id,
            "claim_id":claim_id,
            "claim_text":claim_text,
            "logic":"SMT-LIB2",
            "declarations":declarations,
            "axioms":axioms,
            "hypothesis":hypothesis,
            "solver":{"name":"Z3","version":z3.get_version_string(),"implementation":"z3-solver python"},
            "verdict":verdict,
            "verdict_reason":reason,
            "axioms_consistent":consistent,
            "counterexample":counterexample,
            "elapsed_ms":round((time.perf_counter()-start)*1000,3),
            "issued_at_utc":datetime.now(timezone.utc).isoformat().replace("+00:00","Z"),
            "previous_receipt_hash":self.last_hash,
            "issuer_pubkey_hex":self.pubkey,
            "evidence_tier":"A: local solver result; not independent proof certificate",
            "does_not_prove":[
                "truth-in-the-physical-world",
                "text claim faithfully represents SMT hypothesis",
                "signer ran honest software",
                "offline signature check re-ran Z3",
                "independent trusted time, witness quorum, TEE, ZK or physical test"]
        }
        raw=canonical(body)
        receipt={"body":body,"receipt_hash":digest(raw),"signature":self.sk.sign(raw).hex()}
        self.receipts.append(receipt)
        self.last_hash=receipt["receipt_hash"]
        return receipt
