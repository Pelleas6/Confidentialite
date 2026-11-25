from pathlib import Path
import hashlib
import io
import json
import struct
import zlib

here = Path(__file__).resolve().parent
out = Path("distribution")
out.mkdir(exist_ok=True)
base = b"".join(p.read_bytes() for p in sorted(here.glob("base-*.part")))
manifest = json.loads((here / "manifest.json").read_text())

def restore(delta):
    stream = io.BytesIO(zlib.decompress(delta))
    result = io.BytesIO()
    while kind := stream.read(1):
        if kind == b"L":
            length, = struct.unpack(">I", stream.read(4))
            chunk = stream.read(length)
        elif kind == b"C":
            offset, length = struct.unpack(">II", stream.read(8))
            chunk = base[offset:offset + length]
        else:
            raise ValueError("Unknown record")
        assert len(chunk) == length
        result.write(chunk)
    return result.getvalue()

checks = []
for version, info in sorted(manifest.items()):
    name = f"Sources-{version}.zip"
    data = base if version == "1.7.2" else restore((here / f"{version}.delta").read_bytes())
    digest = hashlib.sha256(data).hexdigest()
    assert digest == info["sha256"] and len(data) == info["size"], name
    (out / name).write_bytes(data)
    checks.append(f"{digest}  {name}")
(out / "SHA256SUMS").write_text("\n".join(checks) + "\n")
