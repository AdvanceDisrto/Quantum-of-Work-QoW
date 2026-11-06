"""Experimental non-QR radial optical carrier. Exact registered PNG only."""
import json, math, struct, zlib
from pathlib import Path
from PIL import Image,ImageDraw
from .truthculator import canonical

SIZE=2000
CENTER=1000
SPOKES=120
RINGS=112
FIRST_RADIUS=300
R_STEP=5.8
CAPACITY=(SPOKES*RINGS)//8
def _bitpoints():
    for spoke in range(SPOKES):
        theta=2*math.pi*spoke/SPOKES-math.pi/2
        for ring in range(RINGS):
            radius=FIRST_RADIUS+ring*R_STEP
            yield (int(round(CENTER+radius*math.cos(theta))),
                   int(round(CENTER+radius*math.sin(theta))))
def encode(receipt,output_path):
    content=zlib.compress(canonical(receipt),level=9)
    data=struct.pack(">I",len(content))+content
    if len(data)>CAPACITY:
        raise ValueError("receipt exceeds radial optical capacity")
    bits="".join(f"{byte:08b}" for byte in data)
    img=Image.new("RGB",(SIZE,SIZE),"white")
    d=ImageDraw.Draw(img)
    # Central proof-DAG illustration is display-only, not encoded proof.
    d.ellipse((CENTER-95,CENTER-95,CENTER+95,CENTER+95),outline="#006c84",width=5)
    for name,dx,dy in (("GENE",0,-40),("INPU",-54,0),("VERI",54,0),("OUTP",0,40)):
        d.text((CENTER+dx-15,CENTER+dy-5),name,fill="#061526")
    for i,(x,y) in enumerate(_bitpoints()):
        if i>=len(bits):
            break
        if bits[i]=="1":
            d.ellipse((x-2,y-2,x+2,y+2),fill="#071622")
    img.save(output_path)
    return {"encoded_bytes":len(data),"capacity_bytes":CAPACITY}
def decode(path):
    img=Image.open(path).convert("L")
    if img.size!=(SIZE,SIZE):
        raise ValueError("image must be perspective-rectified to original dimensions")
    pixels=img.load()
    bits=[]
    for x,y in _bitpoints():
        bits.append("1" if pixels[x,y]<128 else "0")
    raw=bytes(int("".join(bits[i:i+8]),2) for i in range(0,len(bits),8))
    n=struct.unpack(">I",raw[:4])[0]
    if n<=0 or n>CAPACITY-4:
        raise ValueError("invalid optical payload length")
    try:
        return json.loads(zlib.decompress(raw[4:4+n]))
    except (ValueError,zlib.error) as exc:
        raise ValueError("optical decoding failed") from exc
