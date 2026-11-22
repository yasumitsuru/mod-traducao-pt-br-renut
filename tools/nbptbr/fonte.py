"""Inventário de caracteres da fonte "euro" do jogo (gera data/fonte_euro.json).

* precache_euro.ini (UTF-16BE com BOM): caracteres pré-carregados pela interface.
* euro.sbp: cabeçalho 01 01 22 04, u16 BE com o nº de glyphs em 0x04 e, a partir de 0x06,
  registros de 10 bytes [u16 BE código][u32 BE deslocamento][4 bytes de métricas].
Só a lista de códigos é gravada (nenhum desenho de glyph sai do jogo).
"""

from __future__ import annotations

import struct

from .caff import FormatoInvalido
from .config import Caminhos
from .io_seguro import RAIZ_PROJETO, gravar_json_atomico, ler_binario, ler_json, sha256

ARQ_FONTE = RAIZ_PROJETO / "data" / "fonte_euro.json"

# Caracteres que o PT-BR costuma precisar.
NECESSARIOS_PTBR = "áàâãéêíóôõúüçÁÀÂÃÉÊÍÓÔÕÚÜÇºª«»…–—“”‘’°"


def codigos_precache(dados: bytes) -> set[int]:
    if not dados.startswith(b"\xfe\xff"):
        raise FormatoInvalido("precache_euro.ini sem BOM UTF-16BE")
    texto = dados[2:].decode("utf-16-be")
    return {ord(c) for c in texto if c not in "\r\n"}


def codigos_sbp(dados: bytes) -> set[int]:
    if dados[:4] != b"\x01\x01\x22\x04":
        raise FormatoInvalido(f"cabeçalho de euro.sbp inesperado: {dados[:4].hex()}")
    n = struct.unpack_from(">H", dados, 4)[0]
    out, anterior = set(), -1
    for i in range(n):
        cod, desl = struct.unpack_from(">HI", dados, 6 + 10 * i)
        if cod <= anterior or desl >= len(dados):
            raise FormatoInvalido("tabela de glyphs de euro.sbp fora de ordem ou com deslocamento inválido")
        anterior = cod
        out.add(cod)
    return out


def para_faixas(cods: set[int]) -> list[list[str]]:
    faixas: list[list[int]] = []
    for c in sorted(cods):
        if faixas and faixas[-1][1] == c - 1:
            faixas[-1][1] = c
        else:
            faixas.append([c, c])
    return [[f"{a:04X}", f"{b:04X}"] for a, b in faixas]


def de_faixas(faixas: list[list[str]]) -> set[int]:
    out: set[int] = set()
    for a, b in faixas:
        out.update(range(int(a, 16), int(b, 16) + 1))
    return out


def executar(cam: Caminhos) -> dict:
    ini = ler_binario(cam.precache_euro)
    sbp = ler_binario(cam.fonte_euro)
    pre, gl = codigos_precache(ini), codigos_sbp(sbp)
    doc = {
        "origem": {"precache_euro.ini_sha256": sha256(ini), "euro.sbp_sha256": sha256(sbp)},
        "precache": para_faixas(pre),
        "sbp": para_faixas(gl),
    }
    gravar_json_atomico(ARQ_FONTE, doc)
    return {
        "precache": len(pre),
        "sbp": len(gl),
        "faltando_precache": "".join(c for c in NECESSARIOS_PTBR if ord(c) not in pre),
        "faltando_sbp": "".join(c for c in NECESSARIOS_PTBR if ord(c) not in gl),
        "saida": str(ARQ_FONTE),
    }


class ConjuntoFonte:
    """Consulta de caracteres a partir de data/fonte_euro.json."""

    def __init__(self, precache: set[int], sbp: set[int]):
        self.precache = precache
        self.sbp = sbp

    @classmethod
    def carregar(cls) -> "ConjuntoFonte | None":
        if not ARQ_FONTE.exists():
            return None
        d = ler_json(ARQ_FONTE)
        return cls(de_faixas(d["precache"]), de_faixas(d["sbp"]))
