"""Portable PDF attachment and hash-bound model sidecar; no GGUF trailer writes."""
import json,hashlib,base64
from pathlib import Path
from reportlab.pdfgen import canvas
from pypdf import PdfWriter
from .truthculator import canonical,verify_receipt,digest

class UniversalCarrier:
    def __init__(self,receipt,pinned_pubkey):
        if not verify_receipt(receipt,pinned_pubkey)["ok"]:
            raise ValueError("signed receipt failed issuer pin verification")
        self.receipt=receipt
    def embed_in_pdf(self,path):
        from tempfile import NamedTemporaryFile
        with NamedTemporaryFile(suffix=".pdf") as f:
            c=canvas.Canvas(f.name)
            c.setTitle("iNNOVULIS QoW receipt certificate")
            c.drawString(60,740,"iNNOVULIS Quantum of Work / signed receipt")
            c.drawString(60,715,"Claim: "+self.receipt["body"]["claim_id"])
            c.drawString(60,690,"Verdict: "+self.receipt["body"]["verdict"])
            c.drawString(60,665,"Signature verification must use a pinned issuer public key.")
            c.save()
            writer=PdfWriter()
            writer.append(f.name)
            writer.add_attachment(filename="receipt.ipqr.json",data=canonical(self.receipt))
            with open(path,"wb") as out:
                writer.write(out)
    def embed_in_model_weights(self,model_path,sidecar_path):
        model=Path(model_path)
        # Stream the digest; never overwrite model weight bytes.
        h=hashlib.sha256()
        with model.open("rb") as f:
            for block in iter(lambda:f.read(1024*1024),b""):
                h.update(block)
        sidecar={"spec":"qow/model-sidecar/v1","weights_sha256":"sha256:"+h.hexdigest(),
                 "qow_receipt":self.receipt,"does_not_prove":["model is safe","model runtime checks the sidecar"]}
        Path(sidecar_path).write_text(json.dumps(sidecar,sort_keys=True,indent=2))
        return sidecar
    def embed_in_source_code(self,source_path,output_path):
        source=Path(source_path).read_text()
        payload=base64.b64encode(canonical(self.receipt)).decode()
        Path(output_path).write_text(source+"\n# --- QoW SIGNED RECEIPT ---\n# "+payload+"\n")
