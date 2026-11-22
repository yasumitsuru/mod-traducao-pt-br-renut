"""Asset de texto dentro da seção .data de um arquivo loctext.

Seção .data (detalhes em docs/formato-loctext.md):

    +0x00  u32 BE  deslocamento do LSBL dentro da seção (12 sem bloco de colisões)
    +0x04  u32 BE  deslocamento do bloco de colisões (0 se não houver; senão 12)
    +0x08  u16 BE  número de entradas do bloco de colisões
    +0x0A  u16 BE  0
    +0x0C  bloco de colisões (opcional): n x [u32 BE desloc_nome][u16 BE hash_original][u16 BE hash_substituto]
                   seguido dos nomes ASCII terminados em \\0 (deslocamentos relativos à seção)
    +lsbl  LSBL (little-endian; pode começar em endereço ímpar)
    zeros até o tamanho da seção (múltiplo de 16)

LSBL (little-endian):

    "LSBL" | u32 0x1C | u32 4 | u32 desl_frases (0x1C) | u32 desl_chaves | u32 desl_comentarios (0=ausente)
           | u32 desl_indice (0=ausente)
    As tabelas são contíguas, nesta ordem: frases, chaves, [comentários], [índice].

    Tabela de frases:  u32 tamanho | u32 n | (n+1) x [u16 hash, u32 desl_em_unidades]
                       (a última entrada é [0xFFFF, total_de_unidades]) | textos UTF-16LE com \\0 | u16 0
    Tabela de chaves:  u32 tamanho | u32 n | n x [u16 hash, u16 indice, u32 desl_nome] | nomes ASCII\\0
    Comentários e índice: preservados byte a byte (não dependem das frases).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, replace

from .caff import ALINHAMENTO_SECAO, FormatoInvalido, alinhar

MAGICO = b"LSBL"
TAM_CAB_LSBL = 0x1C
HASH_TERMINAL = 0xFFFF


def _exigir(cond: bool, msg: str) -> None:
    if not cond:
        raise FormatoInvalido(msg)


@dataclass(frozen=True)
class Chave:
    hash: int
    indice: int  # 1..n, ordem alfabética do nome
    nome: str


@dataclass(frozen=True)
class Colisao:
    nome: str
    hash_original: int
    hash_substituto: int


@dataclass(frozen=True)
class AssetTexto:
    """Conteúdo da seção .data.

    `hashes` e `textos` seguem a ordem da tabela de frases (crescente por hash).
    As demais tabelas são guardadas como bytes crus e reescritas sem alteração.
    """

    bloco_colisoes: bytes  # bytes entre +0x0C e o LSBL (vazio se não houver)
    n_colisoes: int
    hashes: tuple[int, ...]
    textos: tuple[str, ...]
    tabela_chaves: bytes
    tabela_comentarios: bytes | None
    tabela_indice: bytes | None
    lsbl_cab_extra: tuple[int, int] = (TAM_CAB_LSBL, 4)

    # ---- visões derivadas -------------------------------------------------
    def chaves(self) -> list[Chave]:
        """Chaves na ordem da tabela (a mesma ordem de `hashes`)."""
        return _ler_chaves(self.tabela_chaves)

    def colisoes(self) -> list[Colisao]:
        return _ler_colisoes(self.bloco_colisoes, self.n_colisoes)

    def com_textos(self, textos: tuple[str, ...] | list[str]) -> "AssetTexto":
        textos = tuple(textos)
        _exigir(len(textos) == len(self.textos), "quantidade de textos diferente da original")
        for t in textos:
            _exigir("\x00" not in t, "texto não pode conter o caractere nulo")
        return replace(self, textos=textos)


def _ler_chaves(t: bytes) -> list[Chave]:
    tam, n = struct.unpack_from("<2I", t, 0)
    _exigir(tam == len(t), "tamanho da tabela de chaves não confere")
    inicio_nomes = 8 + 8 * n
    nomes = t[inicio_nomes:]
    _exigir(nomes.count(b"\x00") == n and nomes.endswith(b"\x00"), "nomes de chave sem terminador")
    out = []
    for i in range(n):
        h, idx, off = struct.unpack_from("<HHI", t, 8 + 8 * i)
        fim = nomes.index(b"\x00", off)
        out.append(Chave(hash=h, indice=idx, nome=nomes[off:fim].decode("ascii")))
    return out


def _ler_colisoes(bloco: bytes, n: int) -> list[Colisao]:
    out = []
    for i in range(n):
        off, h_orig, h_sub = struct.unpack_from(">IHH", bloco, 8 * i)
        rel = off - 12  # deslocamentos são relativos ao início da seção
        fim = bloco.index(b"\x00", rel)
        out.append(Colisao(nome=bloco[rel:fim].decode("ascii"), hash_original=h_orig, hash_substituto=h_sub))
    return out


def _tabela(lsbl: bytes, desl: int) -> bytes:
    _exigir(desl + 8 <= len(lsbl), "deslocamento de tabela fora do LSBL")
    tam = struct.unpack_from("<I", lsbl, desl)[0]
    _exigir(desl + tam <= len(lsbl), "tabela ultrapassa o LSBL")
    return lsbl[desl : desl + tam]


def ler(secao: bytes) -> AssetTexto:
    """Interpreta a seção .data (com o preenchimento final)."""
    _exigir(len(secao) >= 12, "seção curta demais")
    desl_lsbl, desl_col, n_col, zero = struct.unpack_from(">IIHH", secao, 0)
    _exigir(zero == 0, "preâmbulo: campo reservado != 0")
    if n_col == 0:
        _exigir(desl_col == 0 and desl_lsbl == 12, "preâmbulo sem colisões com deslocamentos inesperados")
    else:
        _exigir(desl_col == 12 and desl_lsbl > 12 + 8 * n_col, "preâmbulo com colisões inválido")
    bloco_col = secao[12:desl_lsbl]
    if n_col:
        _ler_colisoes(bloco_col, n_col)  # valida

    L = desl_lsbl
    _exigir(secao[L : L + 4] == MAGICO, "assinatura LSBL ausente")
    cab = struct.unpack_from("<6I", secao, L + 4)
    tam_cab, quatro, d_frases, d_chaves, d_coment, d_indice = cab
    _exigir(tam_cab == TAM_CAB_LSBL and quatro == 4 and d_frases == TAM_CAB_LSBL, f"cabeçalho LSBL inesperado: {cab}")

    resto = secao[L:]
    t_frases = _tabela(resto, d_frases)
    _exigir(d_frases + len(t_frases) == d_chaves, "tabela de chaves não segue a de frases")
    t_chaves = _tabela(resto, d_chaves)
    fim = d_chaves + len(t_chaves)
    t_coment = None
    if d_coment:
        _exigir(d_coment == fim, "tabela de comentários fora de ordem")
        t_coment = _tabela(resto, d_coment)
        fim = d_coment + len(t_coment)
    t_indice = None
    if d_indice:
        _exigir(d_indice == fim, "tabela de índice fora de ordem")
        t_indice = _tabela(resto, d_indice)
        fim = d_indice + len(t_indice)

    tam_secao_esperado = alinhar(L + fim, ALINHAMENTO_SECAO)
    _exigir(len(secao) == tam_secao_esperado, "tamanho da seção != alinhamento de 16 do conteúdo")
    _exigir(secao[L + fim :] == bytes(len(secao) - L - fim), "preenchimento final da seção não é zero")

    hashes, textos = _ler_frases(t_frases)
    chaves = _ler_chaves(t_chaves)
    _exigir([c.hash for c in chaves] == list(hashes), "hashes das tabelas de frases e de chaves divergem")
    _exigir(sorted(c.indice for c in chaves) == list(range(1, len(chaves) + 1)), "índices de chave inválidos")

    return AssetTexto(
        bloco_colisoes=bloco_col,
        n_colisoes=n_col,
        hashes=hashes,
        textos=textos,
        tabela_chaves=t_chaves,
        tabela_comentarios=t_coment,
        tabela_indice=t_indice,
    )


def _ler_frases(t: bytes) -> tuple[tuple[int, ...], tuple[str, ...]]:
    tam, n = struct.unpack_from("<2I", t, 0)
    entradas = [struct.unpack_from("<HI", t, 8 + 6 * i) for i in range(n + 1)]
    _exigir(entradas[-1][0] == HASH_TERMINAL, "entrada terminal da tabela de frases ausente")
    hashes = tuple(h for h, _ in entradas[:-1])
    _exigir(list(hashes) == sorted(hashes) and len(set(hashes)) == n, "hashes de frase fora de ordem ou repetidos")
    inicio = 8 + 6 * (n + 1)
    total = entradas[-1][1]
    _exigir(tam == inicio + 2 * total + 2, "tamanho da tabela de frases não confere")
    _exigir(t[inicio + 2 * total :] == b"\x00\x00", "final da tabela de frases não é u16 0")
    textos = []
    for i in range(n):
        a, z = entradas[i][1], entradas[i + 1][1]
        _exigir(a < z, "deslocamentos de frase não são crescentes")
        bruto = t[inicio + 2 * a : inicio + 2 * z]
        _exigir(bruto[-2:] == b"\x00\x00", "frase sem terminador nulo")
        texto = bruto[:-2].decode("utf-16-le", "surrogatepass")
        _exigir("\x00" not in texto, "frase com nulo interno")
        textos.append(texto)
    return hashes, tuple(textos)


def _escrever_frases(hashes: tuple[int, ...], textos: tuple[str, ...]) -> bytes:
    n = len(hashes)
    corpo = bytearray()
    entradas = bytearray()
    unidades = 0
    for h, txt in zip(hashes, textos, strict=True):
        cod = txt.encode("utf-16-le", "surrogatepass") + b"\x00\x00"
        entradas += struct.pack("<HI", h, unidades)
        unidades += len(cod) // 2
        corpo += cod
    entradas += struct.pack("<HI", HASH_TERMINAL, unidades)
    tam = 8 + len(entradas) + len(corpo) + 2
    return struct.pack("<2I", tam, n) + bytes(entradas) + bytes(corpo) + b"\x00\x00"


def escrever(a: AssetTexto) -> bytes:
    """Serializa a seção .data, recalculando deslocamentos, tamanhos e preenchimento."""
    t_frases = _escrever_frases(a.hashes, a.textos)
    d_chaves = TAM_CAB_LSBL + len(t_frases)
    fim = d_chaves + len(a.tabela_chaves)
    d_coment = 0
    if a.tabela_comentarios is not None:
        d_coment = fim
        fim += len(a.tabela_comentarios)
    d_indice = 0
    if a.tabela_indice is not None:
        d_indice = fim
        fim += len(a.tabela_indice)
    lsbl = b"".join(
        [
            MAGICO,
            struct.pack("<6I", TAM_CAB_LSBL, 4, TAM_CAB_LSBL, d_chaves, d_coment, d_indice),
            t_frases,
            a.tabela_chaves,
            a.tabela_comentarios or b"",
            a.tabela_indice or b"",
        ]
    )
    desl_lsbl = 12 + len(a.bloco_colisoes)
    desl_col = 12 if a.n_colisoes else 0
    corpo = struct.pack(">IIHH", desl_lsbl, desl_col, a.n_colisoes, 0) + a.bloco_colisoes + lsbl
    return corpo + bytes(alinhar(len(corpo), ALINHAMENTO_SECAO) - len(corpo))
