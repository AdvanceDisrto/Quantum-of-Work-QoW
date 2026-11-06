"""Generate signed QoW DAG, independently re-check and optically recover it."""
import json
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from qow.truthculator import pubkey_hex
from qow.truthculator_v2 import TruthculatorV2,verify_dag
from qow.independent_verifier import independent_check
from qow.pop_aggregator import aggregate
from qow.ipqr import encode
from qow.ipqr_scanner import add_fiducials,scan_physical_ipqr
from qow.universal_carrier import UniversalCarrier

def run(out="artifacts"):
    folder=Path(out)
    folder.mkdir(exist_ok=True,parents=True)
    sk=Ed25519PrivateKey.generate()
    pin=pubkey_hex(sk)
    tc=TruthculatorV2(sk,"qow-review-node")
    decl="(declare-const x Int)"
    a=tc.compute("MATH_A","x>5 entails x>0",decl,["(> x 5)"],"(> x 0)")
    b=tc.compute("MATH_B","x>10 entails x>5",decl,["(> x 10)"],"(> x 5)")
    c=tc.compute("MATH_C","x>15 entails x>0",decl,["(> x 15)"],"(> x 0)",[a["receipt_hash"],b["receipt_hash"]])
    receipts=[a,b,c]
    assert verify_dag(receipts,pin)["ok"]
    assert all(independent_check(r,pin)["ok"] for r in receipts)
    merkle=aggregate(receipts,pin)
    png=folder/"qow_ipqr.png"
    encode(c,png)
    add_fiducials(png)
    scanned=scan_physical_ipqr(png,pin)
    assert scanned["signature"]["ok"] and scanned["receipt"]==c
    carrier=UniversalCarrier(c,pin)
    carrier.embed_in_pdf(folder/"certificate.pdf")
    dummy=folder/"demo_weights.not_real.gguf"
    dummy.write_bytes(b"DEMO_NOT_REAL_MODEL_WEIGHTS")
    carrier.embed_in_model_weights(dummy,folder/"demo_weights.ipqr.json")
    (folder/"receipts.json").write_text(json.dumps(receipts,indent=2))
    report={"status":"ACCEPT_LOCAL_QOW_ADAPTER","receipt_count":3,"parent_count":2,
        "merkle":merkle,"independent_z3_recheck":True,"optical_signature_verified":True,
        "physical_camera":"NOT_VERIFIED","external_attestation":"NOT_IMPLEMENTED",
        "pop_production_schema":"NOT_CLAIMED_COMPATIBLE"}
    (folder/"smoke_report.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
    return report
if __name__=="__main__":
    run()
