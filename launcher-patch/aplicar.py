# -*- coding: utf-8 -*-
"""Aplicador do patch PT-BR do launcher do reNut.

O renut.exe original nunca é alterado: o patch é aplicado a uma cópia
(`renut.ptbr.exe`) ao lado dele, e o SHA-256 de entrada e de saída é conferido.

    python -I aplicar.py status   --renut <pasta ou renut.exe>
    python -I aplicar.py aplicar  --renut <pasta ou renut.exe> [--saida <arquivo>]
    python -I aplicar.py reverter --renut <pasta ou renut.exe> [--saida <arquivo>]
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(os.environ.get("RENUT_ENGINE_DIR", str(HERE / "engine")))


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def find_exe(renut: str) -> Path:
    p = Path(renut)
    if p.is_dir():
        p = p / "renut.exe"
    return p


def engine_manifest():
    path = ENGINE / "manifesto.json"
    if not path.is_file():
        return None
    return load_json(path)


def same_dir(a: Path, b: Path) -> bool:
    try:
        return a.resolve() == b.resolve()
    except OSError:
        return False


def apply_engine(renut_dir: Path, out_dir: Path) -> int:
    manifest = engine_manifest()
    if not manifest:
        return 0
    if same_dir(renut_dir, out_dir):
        print("AVISO: as DLLs do motor não são alteradas na instalação original.")
        print("       Escolha uma pasta separada para a cópia traduzida.")
        return 0
    changed = 0
    for comp in manifest["components"]:
        name = comp["file"]
        src = renut_dir / name
        dest = out_dir / name
        if not dest.exists():
            shutil.copyfile(src, dest)
        data = dest.read_bytes()
        if hashlib.sha256(data).hexdigest() == comp["output_sha256"]:
            continue
        if len(data) != comp["input_size"] or hashlib.sha256(data).hexdigest() != comp["input_sha256"]:
            print(f"AVISO: {name} não é a versão suportada; o arquivo ficou como estava.")
            continue
        patch = load_json(ENGINE / comp["patch_file"])
        out = bytearray(data)
        for e in patch["edits"]:
            off = int(e["offset"])
            old = base64.b64decode(e["old"])
            new = base64.b64decode(e["new"])
            if len(old) != len(new) or bytes(out[off:off + len(old)]) != old:
                print(f"AVISO: edição inválida em {name} ({e.get('note','')}).")
                break
            out[off:off + len(new)] = new
        else:
            sha = hashlib.sha256(bytes(out)).hexdigest()
            if len(out) != comp["output_size"] or sha != comp["output_sha256"]:
                print(f"AVISO: o resultado de {name} não confere com o manifesto.")
                continue
            tmp = dest.with_suffix(dest.suffix + ".tmp")
            tmp.write_bytes(bytes(out))
            if sha256_file(tmp) != comp["output_sha256"]:
                tmp.unlink(missing_ok=True)
                print(f"AVISO: falha ao gravar {name}.")
                continue
            os.replace(tmp, dest)
            changed += 1
    (out_dir / "ptbr_launcher_engine.json").write_text(
        json.dumps([{"file": c["file"], "output_sha256": c["output_sha256"]} for c in manifest["components"]],
                   ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    return changed


def revert_engine(out_dir: Path) -> int:
    manifest = engine_manifest()
    if not manifest:
        return 0
    removed = 0
    for comp in manifest["components"]:
        dest = out_dir / comp["file"]
        if dest.exists() and sha256_file(dest) == comp["output_sha256"]:
            dest.unlink()
            removed += 1
    (out_dir / "ptbr_launcher_engine.json").unlink(missing_ok=True)
    return removed


def status(exe: Path, manifest: dict) -> int:
    if not exe.is_file():
        print(f"ERRO: renut.exe não encontrado em {exe}")
        return 2
    sha = sha256_file(exe)
    ok = sha == manifest["input_sha256"]
    print(f"Executável: {exe}")
    print(f"Tamanho: {exe.stat().st_size} bytes")
    print(f"SHA-256: {sha}")
    print(f"Versão suportada: {manifest['release']} ({manifest['version']})")
    print("Compatível: " + ("SIM" if ok else "NÃO — o patch será recusado"))
    return 0 if ok else 3


def copy_runtime_files(src_dir: Path, dst_dir: Path) -> None:
    """Copia DLLs e configs para uma pasta de destino separada."""
    if src_dir.resolve() == dst_dir.resolve():
        return
    dst_dir.mkdir(parents=True, exist_ok=True)
    keep_names = {
        "renut.toml", "renut.cfg", "launcher.cfg", "version.txt",
        "rexcrashreporter.exe", "sentry-crash.exe",
    }
    for entry in src_dir.iterdir():
        name = entry.name.lower()
        if entry.is_file() and (name.endswith(".dll") or name in keep_names):
            dest = dst_dir / entry.name
            if not dest.exists():
                shutil.copy2(entry, dest)


def apply_patch(exe: Path, manifest: dict, patch: dict, out: Path) -> int:
    if not exe.is_file():
        print(f"ERRO: renut.exe não encontrado em {exe}")
        return 2
    inp = exe.read_bytes()
    sha = hashlib.sha256(inp).hexdigest()
    if sha != manifest["input_sha256"]:
        print("ERRO: versão incompatível. Nada foi gravado.")
        print(f"  esperado: {manifest['input_sha256']}")
        print(f"  encontrado: {sha}")
        return 3
    if out.exists():
        print(f"ERRO: o destino já existe: {out}\nApague ou renomeie antes de aplicar.")
        return 4
    copy_runtime_files(exe.parent, out.parent)
    data = bytearray(inp)
    for e in patch["edits"]:
        off = int(e["offset"])
        old = base64.b64decode(e["old"])
        new = base64.b64decode(e["new"])
        if old:
            if off + len(old) > len(data) or bytes(data[off:off + len(old)]) != old:
                print(f"ERRO: bytes originais não conferem em {off:#x} ({e.get('note','')})")
                return 5
            data[off:off + len(old)] = new
        else:
            if off != len(data):
                print(f"ERRO: anexo em posição inesperada: {off:#x} != {len(data):#x}")
                return 5
            data += new
    out_sha = hashlib.sha256(bytes(data)).hexdigest()
    if len(data) != manifest["output_size"] or out_sha != manifest["output_sha256"]:
        print("ERRO: o resultado não confere com o manifesto. Nada foi gravado.")
        print(f"  esperado: {manifest['output_sha256']} ({manifest['output_size']} bytes)")
        print(f"  obtido:   {out_sha} ({len(data)} bytes)")
        return 6
    tmp = out.with_suffix(out.suffix + ".tmp")
    tmp.write_bytes(bytes(data))
    if sha256_file(tmp) != manifest["output_sha256"]:
        tmp.unlink(missing_ok=True)
        print("ERRO: falha ao gravar a cópia verificada.")
        return 6
    os.replace(tmp, out)
    print("Patch aplicado com sucesso.")
    print(f"  original preservado: {exe}")
    print(f"  cópia traduzida:     {out}")
    print(f"  SHA-256 da cópia:    {out_sha}")
    n = apply_engine(exe.parent, out.parent)
    if n:
        print(f"  DLLs do motor:       {n} arquivo(s) traduzido(s) na cópia")
    return 0


def revert(exe: Path, manifest: dict, out: Path) -> int:
    if not exe.is_file():
        print(f"ERRO: renut.exe não encontrado em {exe}")
        return 2
    sha = sha256_file(exe)
    if sha != manifest["input_sha256"]:
        print("AVISO: o renut.exe atual não é o original suportado; nada foi apagado.")
        return 3
    if not out.exists():
        print("Nada a reverter: a cópia traduzida não existe. O original está intacto.")
        print(f"SHA-256 do original: {sha}")
        return 0
    if sha256_file(out) != manifest["output_sha256"]:
        print(f"AVISO: {out.name} não é a cópia gerada por este patch; nada foi apagado.")
        return 7
    out.unlink()
    n = revert_engine(out.parent)
    print("Cópia traduzida removida. O renut.exe original permanece intacto.")
    if n:
        print(f"DLLs do motor removidas da cópia: {n}")
    print(f"SHA-256 do original: {sha}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("acao", choices=["status", "aplicar", "reverter"])
    ap.add_argument("--renut", required=True, help="pasta do reNut ou caminho do renut.exe")
    ap.add_argument("--saida", default=None)
    ap.add_argument("--patch", default=str(HERE / "renut_launcher_ptbr.patch"))
    ap.add_argument("--manifesto", default=str(HERE / "manifesto.json"))
    args = ap.parse_args()
    manifest = load_json(Path(args.manifesto))
    patch = load_json(Path(args.patch))
    exe = find_exe(args.renut)
    out = Path(args.saida) if args.saida else exe.with_name("renut.ptbr.exe")
    if args.acao == "status":
        return status(exe, manifest)
    if args.acao == "aplicar":
        return apply_patch(exe, manifest, patch, out)
    return revert(exe, manifest, out)


if __name__ == "__main__":
    sys.exit(main())