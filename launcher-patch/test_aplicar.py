# -*- coding: utf-8 -*-
"""Testes do aplicador sem tocar em nenhuma instalação real."""
import base64
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
APLICAR = HERE / "aplicar.py"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fixture(tmp: Path):
    original = b"PLAY\0EXTRACT GAME DISC\0QUIT\0"
    changed = original.replace(b"PLAY", b"JOGO")
    (tmp / "renut.exe").write_bytes(original)
    manifest = {
        "release": "test", "version": "0", "input_size": len(original),
        "input_sha256": sha(original), "output_size": len(changed),
        "output_sha256": sha(changed),
    }
    patch = {"schema": "test", "edits": [{
        "offset": 0, "old": base64.b64encode(b"PLAY").decode(),
        "new": base64.b64encode(b"JOGO").decode(), "note": "teste",
    }]}
    (tmp / "manifesto.json").write_text(json.dumps(manifest), encoding="utf-8")
    (tmp / "patch.json").write_text(json.dumps(patch), encoding="utf-8")
    return original, changed


def run(tmp: Path, *args: str, env=None):
    return subprocess.run(
        [sys.executable, "-I", str(APLICAR), *args,
         "--patch", str(tmp / "patch.json"), "--manifesto", str(tmp / "manifesto.json")],
        capture_output=True, text=True, encoding="utf-8", env=env,
    )


def test_apply_and_revert():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        original, changed = fixture(tmp)
        out = tmp / "renut.ptbr.exe"
        r = run(tmp, "aplicar", "--renut", str(tmp / "renut.exe"), "--saida", str(out))
        assert r.returncode == 0, r.stdout + r.stderr
        assert out.read_bytes() == changed
        r = run(tmp, "reverter", "--renut", str(tmp / "renut.exe"), "--saida", str(out))
        assert r.returncode == 0, r.stdout + r.stderr
        assert not out.exists()
        assert (tmp / "renut.exe").read_bytes() == original


def test_engine_apply_and_revert():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        original, changed = fixture(tmp)
        orig = tmp / "orig"
        out = tmp / "out"
        engine = tmp / "engine"
        orig.mkdir()
        out.mkdir()
        engine.mkdir()
        (orig / "renut.exe").write_bytes(original)
        dll = b"Fullscreen\0rest\0"
        (orig / "rexui.dll").write_bytes(dll)
        new_dll = dll.replace(b"Fullscreen", b"TELA CHEIA")
        (engine / "rexui_patch.json").write_text(json.dumps({"edits": [{
            "offset": 0, "old": base64.b64encode(b"Fullscreen").decode(),
            "new": base64.b64encode(b"TELA CHEIA").decode(), "note": "teste",
        }]}), encoding="utf-8")
        (engine / "manifesto.json").write_text(json.dumps({"components": [{
            "file": "rexui.dll", "patch_file": "rexui_patch.json",
            "input_size": len(dll), "input_sha256": sha(dll),
            "output_size": len(new_dll), "output_sha256": sha(new_dll),
        }]}), encoding="utf-8")
        env = __import__("os").environ.copy()
        env["RENUT_ENGINE_DIR"] = str(engine)
        target = out / "renut.ptbr.exe"
        r = run(tmp, "aplicar", "--renut", str(orig / "renut.exe"), "--saida", str(target), env=env)
        assert r.returncode == 0, r.stdout + r.stderr
        assert target.read_bytes() == changed
        assert (out / "rexui.dll").read_bytes() == new_dll
        r = run(tmp, "reverter", "--renut", str(orig / "renut.exe"), "--saida", str(target), env=env)
        assert r.returncode == 0, r.stdout + r.stderr
        assert not target.exists()
        assert not (out / "rexui.dll").exists()
        assert (orig / "rexui.dll").read_bytes() == dll


def test_refuses_wrong_version():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        fixture(tmp)
        (tmp / "renut.exe").write_bytes(b"outra versao")
        out = tmp / "renut.ptbr.exe"
        r = run(tmp, "aplicar", "--renut", str(tmp / "renut.exe"), "--saida", str(out))
        assert r.returncode == 3
        assert not out.exists()
        assert (tmp / "renut.exe").read_bytes() == b"outra versao"