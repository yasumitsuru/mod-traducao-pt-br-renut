"""Compara dois pacotes `.nbpatch` do mod (ex.: 0.7.0 contra a revisão 0.8.0).

Abre os dois ZIPs, confere o `patch.json` de cada um e, para cada asset de
`loctext/englishus`, lê o loctext e compara frase a frase (pela chave). O resultado diz quais
arquivos mudaram, quais chaves mudaram em cada um e se algo além do texto mudou (chaves,
estrutura). Somente leitura; não grava nada.
"""

from __future__ import annotations

import io
import json
import zipfile
from pathlib import Path

from . import loctext
from .io_seguro import ler_binario, sha256

PREFIXO = "loctext/englishus/"


def _abrir(dados: bytes) -> tuple[dict, dict[str, bytes]]:
    with zipfile.ZipFile(io.BytesIO(dados)) as z:
        pj = json.loads(z.read("patch.json").decode("utf-8"))
        arquivos = {}
        for f in pj["Files"]:
            if not f["Path"].startswith(PREFIXO):
                raise ValueError(f"{f['Path']}: fora de {PREFIXO}")
            arquivos[f["Path"][len(PREFIXO):]] = z.read(f["Entry"])
    return pj, arquivos


def comparar_bytes(antigo: bytes, novo: bytes) -> dict:
    pj_a, arq_a = _abrir(antigo)
    pj_n, arq_n = _abrir(novo)
    mudaram: dict[str, dict] = {}
    estrutura: list[str] = []
    for nome in sorted(set(arq_a) | set(arq_n)):
        if nome not in arq_a or nome not in arq_n:
            estrutura.append(f"{nome}: {'só no novo' if nome in arq_n else 'só no antigo'}")
            continue
        a, n = arq_a[nome], arq_n[nome]
        if a == n:
            continue
        fa = {f.chave: f for f in loctext.ler(a).frases()}
        fn = {f.chave: f for f in loctext.ler(n).frases()}
        if set(fa) != set(fn):
            estrutura.append(f"{nome}: conjunto de chaves diferente")
        chaves = sorted(c for c in set(fa) & set(fn) if fa[c].texto != fn[c].texto)
        ids = {c: fn[c].id for c in chaves}
        mudaram[nome] = {"chaves": chaves, "ids": [ids[c] for c in chaves],
                         "sha_antigo": sha256(a), "sha_novo": sha256(n)}
    return {
        "versao_antiga": pj_a.get("Version"),
        "versao_nova": pj_n.get("Version"),
        "sha_antigo": sha256(antigo),
        "sha_novo": sha256(novo),
        "arquivos_antigo": len(arq_a),
        "arquivos_novo": len(arq_n),
        "arquivos_mudaram": len(mudaram),
        "frases_mudaram": sum(len(v["chaves"]) for v in mudaram.values()),
        "mudancas": mudaram,
        "problemas_estrutura": estrutura,
    }


def comparar(antigo: str | Path, novo: str | Path) -> dict:
    return comparar_bytes(ler_binario(antigo), ler_binario(novo))


def conferir_esperado(resultado: dict, esperado: dict[str, set[str]]) -> list[str]:
    """Confere que as frases que mudaram no pacote são exatamente as esperadas ({arquivo: {id}})."""
    erros = []
    obtido = {nome: set(v["ids"]) for nome, v in resultado["mudancas"].items()}
    for nome in sorted(set(obtido) | set(esperado)):
        a, b = obtido.get(nome, set()), esperado.get(nome, set())
        if a - b:
            erros.append(f"{nome}: mudaram sem estar no catálogo revisado: {sorted(a - b)}")
        if b - a:
            erros.append(f"{nome}: revisadas no catálogo mas iguais no pacote: {sorted(b - a)}")
    erros += resultado["problemas_estrutura"]
    return erros


__all__ = ["comparar", "comparar_bytes", "conferir_esperado"]
