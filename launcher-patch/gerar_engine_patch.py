# -*- coding: utf-8 -*-
"""Gera os patches das DLLs do motor que fornecem duas descrições do launcher.

O patch 0.8.0 cobria só o renut.exe. As descrições de TELA CHEIA e de ENTRADA
CONTROLE vêm de rexui.dll e rexhid.dll; este gerador cria patches in-place para
cópias dessas DLLs. Os originais nunca são escritos.

    .venv\\Scripts\\python -I launcher-patch\\gerar_engine_patch.py --renut <pasta> --saida launcher-patch\\engine
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from gerar_patch import PE, align_up  # noqa: E402

ENTRADAS = [
    {
        "id": "help.gfx.fullscreen",
        "file": "rexui.dll",
        "en": "Fullscreen",
        "pt": "TELA CHEIA",
        "source": "rexui.dll",
    },
    {
        "id": "help.input.drivers",
        "file": "rexhid.dll",
        "en": "Input drivers in priority order, comma separated",
        "pt": "Drivers de entrada por prioridade, vírgula",
        "source": "rexhid.dll",
    },
]


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def pe_checksum(data: bytearray, checksum_off: int) -> bytes:
    data[checksum_off:checksum_off + 4] = b"\0\0\0\0"
    total = 0
    for i in range(0, len(data), 2):
        w = data[i] | ((data[i + 1] << 8) if i + 1 < len(data) else 0)
        total += w
        total = (total & 0xFFFF) + (total >> 16)
    total = (total & 0xFFFF) + (total >> 16)
    return struct.pack("<I", total)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--renut", required=True, help="pasta do reNut (somente leitura)")
    ap.add_argument("--saida", default=str(HERE / "engine"))
    args = ap.parse_args()
    renut = Path(args.renut)
    outdir = Path(args.saida)
    outdir.mkdir(parents=True, exist_ok=True)

    fontes_path = HERE / "engine" / "fontes.json"
    fontes = json.loads(fontes_path.read_text(encoding="utf-8")) if fontes_path.is_file() else {}
    components = []
    for e in ENTRADAS:
        path = renut / e["file"]
        data = path.read_bytes()
        sha = sha256(data)
        esperado = fontes.get(e["file"], {}).get("input_sha256")
        if esperado and esperado != sha:
            raise SystemExit(f"{e['file']}: SHA-256 {sha} != esperado {esperado}")
        nb = e["en"].encode("utf-8")
        pb = e["pt"].encode("utf-8")
        if len(pb) > len(nb):
            raise SystemExit(f"{e['id']}: tradução não cabe ({len(nb)} -> {len(pb)})")
        off = data.find(nb + b"\0")
        if off < 0:
            raise SystemExit(f"{e['id']}: literal não encontrado em {e['file']}")
        if data.find(nb + b"\0", off + 1) >= 0:
            raise SystemExit(f"{e['id']}: literal duplicado em {e['file']}")
        new = pb + b" " * (len(nb) - len(pb)) + b"\0"
        out = bytearray(data)
        out[off:off + len(nb) + 1] = new
        pe = PE(data)
        csum = pe_checksum(out, pe.checksum_off)
        old_csum = data[pe.checksum_off:pe.checksum_off + 4]
        out[pe.checksum_off:pe.checksum_off + 4] = csum
        out_sha = sha256(bytes(out))
        patch = {
            "schema": "renut-launcher-engine-patch/1",
            "file": e["file"],
            "input_size": len(data),
            "input_sha256": sha,
            "output_size": len(out),
            "output_sha256": out_sha,
            "entries": [e["id"]],
            "edits": [
                {"offset": off, "old": base64.b64encode(nb + b"\0").decode("ascii"),
                 "new": base64.b64encode(new).decode("ascii"),
                 "note": f"{e['id']}: literal UTF-8"},
                {"offset": pe.checksum_off, "old": base64.b64encode(old_csum).decode("ascii"),
                 "new": base64.b64encode(csum).decode("ascii"), "note": "checksum PE"},
            ],
        }
        patch_path = outdir / (path.stem + "_ptbr.patch")
        patch_path.write_text(json.dumps(patch, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
        components.append({
            "file": e["file"],
            "patch_file": patch_path.name,
            "input_size": len(data),
            "input_sha256": sha,
            "output_size": len(out),
            "output_sha256": out_sha,
            "entries": [e["id"]],
            "edits": len(patch["edits"]),
        })
        fontes[e["file"]] = {"input_size": len(data), "input_sha256": sha}
        print(f"{e['file']}: {e['id']} @ {off:#x}  {len(nb)} -> {len(pb)} bytes  sha {out_sha[:16]}…")
    (HERE / "engine" / "fontes.json").write_text(json.dumps(fontes, ensure_ascii=False, indent=1),
                                                encoding="utf-8", newline="\n")
    manifest = {
        "schema": "renut-launcher-engine/1",
        "release": "big-lua-energy",
        "version": "0.11.21",
        "components": components,
    }
    (outdir / "manifesto.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=1),
                                          encoding="utf-8", newline="\n")
    print(f"manifesto: {outdir / 'manifesto.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())