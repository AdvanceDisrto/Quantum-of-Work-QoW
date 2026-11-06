"""LOCAL QoW Merkle adapter. NOT PoP's domain-separated production Merkle scheme."""
from .truthculator import verify_receipt,digest
def aggregate(receipts,pinned_pubkey):
    if not receipts:
        raise ValueError("empty Merkle set is not an accepted QoW aggregate")
    for r in receipts:
        if not verify_receipt(r,pinned_pubkey)["ok"]:
            raise ValueError("invalid signed receipt")
    layer=[bytes.fromhex(r["receipt_hash"].split(":",1)[1]) for r in receipts]
    while len(layer)>1:
        if len(layer)%2:
            layer.append(layer[-1])
        layer=[bytes.fromhex(digest(b"qow-node-v1:"+layer[i]+layer[i+1])[7:]) for i in range(0,len(layer),2)]
    return {"spec":"qow/merkle-commitment/v1","root":"sha256:"+layer[0].hex(),
            "leaf_count":len(receipts),"does_not_prove":"compatibility with PoP production Merkle"}
