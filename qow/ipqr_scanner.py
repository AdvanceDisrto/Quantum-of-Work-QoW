"""Registered PNG optical decoder. Camera capture is experimental and not accepted."""
from .ipqr import encode,decode
from .truthculator import verify_receipt

def add_fiducials(path):
    from PIL import Image,ImageDraw
    img=Image.open(path).convert("RGB")
    draw=ImageDraw.Draw(img)
    for x,y in ((65,65),(1935,65),(1935,1935),(65,1935)):
        draw.rectangle((x-22,y-22,x+22,y+22),fill="#071622")
        draw.rectangle((x-12,y-12,x+12,y+12),fill="white")
        draw.rectangle((x-5,y-5,x+5,y+5),fill="#071622")
    img.save(path)

def scan_physical_ipqr(source,pinned_pubkey=None):
    # Fail closed on arbitrary camera images until a registered-camera
    # distortion and real print test has been independently accepted.
    if isinstance(source,int):
        raise ValueError("physical camera acceptance not implemented")
    receipt=decode(source)
    return {"receipt":receipt,"signature":verify_receipt(receipt,pinned_pubkey),
            "scanner":"registered PNG; no physical camera acceptance"}
