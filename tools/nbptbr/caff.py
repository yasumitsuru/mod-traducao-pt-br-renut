"""Contêiner CAFF "07.08.06.0036" dos arquivos loctext (big-endian).

Somente o subconjunto observado nos 1498 arquivos loctext (14 idiomas x 107):
uma seção (".data") e um símbolo (o asset "aid_loctext_banjox_*").
Qualquer desvio desse subconjunto gera FormatoInvalido em vez de um palpite.

Layout (detalhes em docs/formato-loctext.md):

    0x00  char[20]  "CAFF07.08.06.0036" + 3 bytes 0
    0x14  u32       0x78 (tamanho do cabeçalho fixo)
    0x18  u32       checksum (depende só do cabeçalho fixo; algoritmo desconhecido)
    0x1C  u32       1 (símbolos)        0x20  u32  1 (seções)
    0x24  36 bytes  zero
    0x48  u8[4]     01 01 00 00
    0x4C  u32       tamanho da tabela de nomes de seção (6 = ".data\\0")
    0x50  u32       tamanho da área de informações (alinhado a 4)
    0x54  12 bytes  zero
    0x60  u32       tamanho da área de informações (repetido)
    0x64  20 bytes  zero
    0x78  área de informações (empacotada, sem alinhamento):
          u32 0 | u8 4 | u32 0 | u32 tam_secao | u32 0 x4 | u32 tam_secao
          nomes de seção | u32 tam_nomes_simbolo | u32 0 | nome do símbolo\\0
          u32 0 | u32 1 | u32 0 | u32 tam_secao | u8 1 | u8 4 | zeros até alinhar a 4
    0x78+info  dados da seção (tamanho múltiplo de 16)
"""

from __future__ import annotations

import struct
from dataclasses import dataclass

ASSINATURA = b"CAFF07.08.06.0036\x00\x00\x00"
TAM_CABECALHO = 0x78
ALINHAMENTO_SECAO = 16


class FormatoInvalido(ValueError):
    """O arquivo não segue o subconjunto CAFF documentado."""


def _u32(b: bytes, o: int) -> int:
    return struct.unpack_from(">I", b, o)[0]


def _exigir(cond: bool, msg: str) -> None:
    if not cond:
        raise FormatoInvalido(msg)


def alinhar(valor: int, base: int) -> int:
    return (valor + base - 1) // base * base


@dataclass(frozen=True)
class Caff:
    """Arquivo CAFF com uma seção e um símbolo.

    `cabecalho` guarda os 0x78 bytes fixos exatamente como lidos (inclui o checksum).
    `dados` é o conteúdo da seção .data, já com o preenchimento até múltiplo de 16.
    """

    cabecalho: bytes
    nomes_secao: bytes
    nome_simbolo: bytes  # sem o \0 final, ASCII: "aid_loctext_banjox_x,1220524793,2.33"
    dados: bytes

    @property
    def asset(self) -> str:
        return self.nome_simbolo.decode("ascii").split(",")[0]

    @property
    def tam_info(self) -> int:
        return _u32(self.cabecalho, 0x50)

    @property
    def checksum(self) -> int:
        return _u32(self.cabecalho, 0x18)


def _validar_cabecalho(b: bytes) -> None:
    _exigir(len(b) >= TAM_CABECALHO, "arquivo menor que o cabeçalho CAFF")
    _exigir(b[:20] == ASSINATURA, f"assinatura CAFF inesperada: {b[:20]!r}")
    _exigir(_u32(b, 0x14) == TAM_CABECALHO, "campo 0x14 != 0x78")
    _exigir(_u32(b, 0x1C) == 1 and _u32(b, 0x20) == 1, "esperado 1 símbolo e 1 seção")
    _exigir(b[0x24:0x48] == bytes(0x24), "bytes 0x24..0x47 não são zero")
    _exigir(b[0x48:0x4C] == b"\x01\x01\x00\x00", "bytes 0x48..0x4B != 01 01 00 00")
    _exigir(_u32(b, 0x50) == _u32(b, 0x60), "tamanhos da área de informações divergem")
    _exigir(b[0x54:0x60] == bytes(12) and b[0x64:0x78] == bytes(0x14), "campos reservados não são zero")
    _exigir(_u32(b, 0x50) % 4 == 0, "área de informações não alinhada a 4")


def ler(b: bytes) -> Caff:
    """Interpreta um arquivo CAFF (bytes completos)."""
    _validar_cabecalho(b)
    tam_nomes_secao = _u32(b, 0x4C)
    tam_info = _u32(b, 0x50)
    inicio_dados = TAM_CABECALHO + tam_info
    _exigir(inicio_dados <= len(b), "área de informações ultrapassa o arquivo")

    p = TAM_CABECALHO
    _exigir(_u32(b, p) == 0, "info+0x00 != 0")
    p += 4
    _exigir(b[p] == 4, "info+0x04 (alinhamento da seção) != 4")
    p += 1
    secao = struct.unpack_from(">7I", b, p)
    p += 28
    tam_secao = secao[1]
    _exigir(secao[0] == 0 and secao[2:6] == (0, 0, 0, 0), "entrada de seção com campos inesperados")
    _exigir(secao[6] == tam_secao, "tamanhos da seção divergem")
    nomes_secao = b[p : p + tam_nomes_secao]
    _exigir(nomes_secao == b".data\x00", f"nome de seção inesperado: {nomes_secao!r}")
    p += tam_nomes_secao
    tam_nomes_simbolo = _u32(b, p)
    _exigir(_u32(b, p + 4) == 0, "campo após o tamanho dos nomes de símbolo != 0")
    p += 8
    nomes_simbolo = b[p : p + tam_nomes_simbolo]
    _exigir(
        len(nomes_simbolo) == tam_nomes_simbolo and nomes_simbolo.endswith(b"\x00") and nomes_simbolo.count(b"\x00") == 1,
        "tabela de nomes de símbolo inválida",
    )
    p += tam_nomes_simbolo
    simbolo = struct.unpack_from(">4I2B", b, p)
    _exigir(simbolo == (0, 1, 0, tam_secao, 1, 4), f"entrada de símbolo inesperada: {simbolo}")
    p += 18
    _exigir(alinhar(p - TAM_CABECALHO, 4) == tam_info, "tamanho da área de informações não confere")
    _exigir(b[p:inicio_dados] == bytes(inicio_dados - p), "preenchimento da área de informações não é zero")
    _exigir(inicio_dados + tam_secao == len(b), "tamanho do arquivo != cabeçalho + info + seção")
    _exigir(tam_secao % ALINHAMENTO_SECAO == 0, "seção não é múltipla de 16")
    return Caff(
        cabecalho=b[:TAM_CABECALHO],
        nomes_secao=nomes_secao,
        nome_simbolo=nomes_simbolo[:-1],
        dados=b[inicio_dados:],
    )


def _area_info(c: Caff) -> bytes:
    tam_secao = len(c.dados)
    nome = c.nome_simbolo + b"\x00"
    partes = [
        struct.pack(">IB", 0, 4),
        struct.pack(">7I", 0, tam_secao, 0, 0, 0, 0, tam_secao),
        c.nomes_secao,
        struct.pack(">II", len(nome), 0),
        nome,
        struct.pack(">4I2B", 0, 1, 0, tam_secao, 1, 4),
    ]
    info = b"".join(partes)
    return info + bytes(alinhar(len(info), 4) - len(info))


def escrever(c: Caff) -> bytes:
    """Serializa o CAFF. Recalcula os tamanhos da seção; o cabeçalho fixo é mantido.

    O checksum em 0x18 depende apenas do cabeçalho fixo (verificado nos 1498 arquivos):
    como a tradução não muda o nome do asset, a área de informações mantém o tamanho e o
    cabeçalho (com o checksum) continua válido. Se o tamanho mudar, recusamos.
    """
    _exigir(len(c.dados) % ALINHAMENTO_SECAO == 0, "dados da seção devem ser múltiplos de 16")
    info = _area_info(c)
    _exigir(
        len(info) == _u32(c.cabecalho, 0x50),
        "a área de informações mudou de tamanho; o checksum do cabeçalho não pode ser recalculado",
    )
    _validar_cabecalho(c.cabecalho)
    return c.cabecalho + info + c.dados
