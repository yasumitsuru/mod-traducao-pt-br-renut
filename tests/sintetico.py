"""Gerador independente de arquivos loctext sintéticos, escrito a partir de docs/formato-loctext.md.

Não usa o serializador de tools/ (para não testar o código contra ele mesmo). Os hashes
usados aqui são arbitrários (CRC32 & 0xFFFF): o leitor não depende do algoritmo real.
"""

from __future__ import annotations

import struct
import zlib

MAGICO_CAFF = b"CAFF07.08.06.0036\x00\x00\x00"


def hash16(nome: str) -> int:
    h = zlib.crc32(nome.encode("ascii")) & 0xFFFF
    return 0x1234 if h == 0xFFFF else h


def _alinhar(v: int, a: int) -> int:
    return (v + a - 1) // a * a


def montar_secao(
    textos: dict[str, str],
    colisoes: list[tuple[str, int, int]] | None = None,
    comentarios: bytes | None = None,
    com_indice: bool = True,
    hashes: dict[str, int] | None = None,
) -> bytes:
    nomes = sorted(textos)
    hs = hashes or {n: hash16(n) for n in nomes}
    assert len(set(hs.values())) == len(nomes)
    indice = {n: i + 1 for i, n in enumerate(nomes)}
    por_hash = sorted(nomes, key=lambda n: hs[n])

    # tabela de frases
    entradas, corpo, u = b"", b"", 0
    for n in por_hash:
        cod = textos[n].encode("utf-16-le") + b"\x00\x00"
        entradas += struct.pack("<HI", hs[n], u)
        u += len(cod) // 2
        corpo += cod
    entradas += struct.pack("<HI", 0xFFFF, u)
    t1_corpo = entradas + corpo + b"\x00\x00"
    t1 = struct.pack("<2I", 8 + len(t1_corpo), len(nomes)) + t1_corpo

    # tabela de chaves
    blob, desl = b"", {}
    for n in nomes:
        desl[n] = len(blob)
        blob += n.encode("ascii") + b"\x00"
    ent2 = b"".join(struct.pack("<HHI", hs[n], indice[n], desl[n]) for n in por_hash)
    t2 = struct.pack("<2I", 8 + len(ent2) + len(blob), len(nomes)) + ent2 + blob

    tX = comentarios or b""
    t3 = b""
    if com_indice:
        lst = b"".join(struct.pack("<H", hs[n]) for n in nomes)
        t3 = struct.pack("<2I", 8 + len(lst), len(nomes)) + lst

    d2 = 0x1C + len(t1)
    dX = d2 + len(t2) if comentarios else 0
    d3 = (d2 + len(t2) + len(tX)) if com_indice else 0
    lsbl = b"LSBL" + struct.pack("<6I", 0x1C, 4, 0x1C, d2, dX, d3) + t1 + t2 + tX + t3

    col = colisoes or []
    bloco = b""
    if col:
        nomes_col = b""
        base = 12 + 8 * len(col)
        ents = b""
        for nome, h_orig, h_sub in col:
            ents += struct.pack(">IHH", base + len(nomes_col), h_orig, h_sub)
            nomes_col += nome.encode("ascii") + b"\x00"
        bloco = ents + nomes_col
    pre = struct.pack(">IIHH", 12 + len(bloco), 12 if col else 0, len(col), 0)
    sec = pre + bloco + lsbl
    return sec + bytes(_alinhar(len(sec), 16) - len(sec))


def montar_caff(nome_simbolo: str, secao: bytes, checksum: int = 0x0BADF00D) -> bytes:
    nome = nome_simbolo.encode("ascii") + b"\x00"
    tam = len(secao)
    info = (
        struct.pack(">IB", 0, 4)
        + struct.pack(">7I", 0, tam, 0, 0, 0, 0, tam)
        + b".data\x00"
        + struct.pack(">II", len(nome), 0)
        + nome
        + struct.pack(">4I2B", 0, 1, 0, tam, 1, 4)
    )
    info += bytes(_alinhar(len(info), 4) - len(info))
    cab = (
        MAGICO_CAFF
        + struct.pack(">IIII", 0x78, checksum, 1, 1)
        + bytes(0x24)
        + b"\x01\x01\x00\x00"
        + struct.pack(">II", 6, len(info))
        + bytes(12)
        + struct.pack(">I", len(info))
        + bytes(0x14)
    )
    assert len(cab) == 0x78
    return cab + info + secao


def montar_arquivo(textos: dict[str, str], nome_asset: str = "aid_loctext_banjox_teste", **kw) -> bytes:
    return montar_caff(f"{nome_asset},1222176485,2.33", montar_secao(textos, **kw))
