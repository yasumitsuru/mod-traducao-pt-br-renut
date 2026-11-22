"""Entrada e saída seguras.

Regras do projeto:
  * Pastas externas (jogo, ISO, reNut, mods) são SOMENTE LEITURA: só abrimos com "rb".
  * Toda escrita acontece dentro da raiz do projeto, de forma atômica
    (arquivo temporário na mesma pasta + os.replace).
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

# tools/nbptbr/io_seguro.py -> raiz do projeto
RAIZ_PROJETO = Path(__file__).resolve().parents[2]


class EscritaForaDaRaiz(PermissionError):
    """Tentativa de gravar fora da raiz do projeto."""


def caminho_gravavel(destino: str | os.PathLike[str]) -> Path:
    """Resolve `destino` e garante que ele fica dentro da raiz do projeto."""
    p = Path(destino)
    if not p.is_absolute():
        p = RAIZ_PROJETO / p
    p = p.resolve()
    if not p.is_relative_to(RAIZ_PROJETO):
        raise EscritaForaDaRaiz(f"escrita recusada fora da raiz do projeto: {p}")
    return p


def ler_binario(origem: str | os.PathLike[str]) -> bytes:
    """Lê um arquivo inteiro em modo somente leitura ("rb")."""
    with open(origem, "rb") as f:
        return f.read()


def sha256(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def gravar_atomico(destino: str | os.PathLike[str], dados: bytes) -> Path:
    """Grava bytes atomicamente dentro da raiz do projeto."""
    p = caminho_gravavel(destino)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{p.name}.", suffix=".tmp", dir=p.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(dados)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, p)
    except BaseException:
        try:
            os.unlink(tmp)
        except FileNotFoundError:
            pass
        raise
    return p


def gravar_texto_atomico(destino: str | os.PathLike[str], texto: str) -> Path:
    """Grava texto UTF-8 com quebras de linha "\\n" (sem conversão para CRLF)."""
    return gravar_atomico(destino, texto.replace("\r\n", "\n").encode("utf-8"))


def json_estavel(obj: Any) -> str:
    """JSON byte-estável: UTF-8 legível, indentado, com quebra de linha final."""
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def gravar_json_atomico(destino: str | os.PathLike[str], obj: Any) -> Path:
    return gravar_texto_atomico(destino, json_estavel(obj))


def ler_json(origem: str | os.PathLike[str]) -> Any:
    with open(origem, "rb") as f:
        return json.loads(f.read().decode("utf-8"))
