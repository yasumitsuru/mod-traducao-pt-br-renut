"""F6 — empacota a tradução como mod do reNut.

Modo 0.6.0 (validado na instalação real): o `.nbpatch` ADICIONA a pasta `loctext/englishus` com
`Kind="new"`. O jogo a lê em English (1). É uma pasta nova, então o reNut a monta como cópia mesclada
e evita o defeito `HasChildVanished` que quebrava a substituição de arquivos existentes.

O modo antigo (delta "NBDL" sobre `Debug/11`) continua implementado e testado para histórico:
    Files[{Path, Kind="delta", SourceSha256, SourceSize, TargetSha256, TargetSize, Entry}]
    files/<hash>.nbdl — "NBDL" | u32 LE (não lido) | u64 LE tamanho final | operações 0x01 cópia e
    0x02 literal (varint LEB128).
"""

from __future__ import annotations

import io
import json
import re
import struct
import zipfile

from . import loctext
from .io_seguro import RAIZ_PROJETO, gravar_atomico, gravar_texto_atomico, ler_binario, ler_json, sha256
from .reinserir import PASTA_SAIDA as PASTA_BUILD

ID_MOD = "ptbr_traducao"
PASTA_DIST = RAIZ_PROJETO / "dist" / ID_MOD
DATA_ZIP = (2026, 1, 1, 0, 0, 0)  # data fixa: pacote byte-estável
MAGICO_NBDL = b"NBDL"


class PacoteInvalido(RuntimeError):
    pass


# ---- NBDL ---------------------------------------------------------------------------------
def varint(n: int) -> bytes:
    if n < 0:
        raise ValueError("varint negativo")
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | (0x80 if n else 0))
        if not n:
            return bytes(out)


def _ler_varint(d: bytes, p: int) -> tuple[int, int]:
    n = shift = 0
    while True:
        if p >= len(d):
            raise PacoteInvalido("varint truncado")
        b = d[p]
        p += 1
        n |= (b & 0x7F) << shift
        shift += 7
        if not b & 0x80:
            return n, p


def delta_literal(alvo: bytes) -> bytes:
    """Delta com uma única operação literal (o arquivo inteiro)."""
    if len(alvo) > 0x7FFFFFFF:
        raise PacoteInvalido("arquivo grande demais para NBDL")
    return MAGICO_NBDL + struct.pack("<IQ", 1, len(alvo)) + b"\x02" + varint(len(alvo)) + alvo


def aplicar_delta(origem: bytes, delta: bytes) -> bytes:
    """Reimplementação do decodificador do reNut, usada para conferir o pacote."""
    if len(delta) < 16 or delta[:4] != MAGICO_NBDL:
        raise PacoteInvalido("não é um delta NBDL")
    tam = struct.unpack_from("<Q", delta, 8)[0]
    if tam > 0x7FFFFFFF:
        raise PacoteInvalido("tamanho final grande demais")
    out, p = bytearray(), 16
    while p < len(delta):
        op = delta[p]
        p += 1
        if op == 1:
            desl, p = _ler_varint(delta, p)
            n, p = _ler_varint(delta, p)
            if desl + n > len(origem) or len(out) + n > tam:
                raise PacoteInvalido("delta copy out of range")
            out += origem[desl : desl + n]
        elif op == 2:
            n, p = _ler_varint(delta, p)
            if p + n > len(delta) or len(out) + n > tam:
                raise PacoteInvalido("delta literal out of range")
            out += delta[p : p + n]
            p += n
        else:
            raise PacoteInvalido("bad delta op")
    if len(out) != tam:
        raise PacoteInvalido("delta produced a short file")
    return bytes(out)


# ---- pacote -------------------------------------------------------------------------------
def montar_patch_json(arquivos: list[dict], versao: str) -> dict:
    return {
        "Format": 1,
        "Name": "Traducao PT-BR",
        "Id": ID_MOD,
        "Version": versao,
        "Author": "Projeto de traducao PT-BR (fas)",
        "Category": "Translation",
        "Requires": [],
        "Conflicts": [],
        "Ops": [],
        "Files": arquivos,
        "ExeMods": [],
    }


def _zip(entradas: list[tuple[str, bytes]]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_STORED) as z:
        for nome, dados in entradas:
            info = zipfile.ZipInfo(nome, date_time=DATA_ZIP)
            info.compress_type = zipfile.ZIP_STORED
            info.external_attr = 0o644 << 16
            z.writestr(info, dados)
    return buf.getvalue()


def mod_toml(versao: str, n_frases: int) -> str:
    """Somente ASCII: não se sabe se a interface do reNut desenha acentos."""
    return (
        'name = "Traducao PT-BR"\n'
        f'description = "Brazilian Portuguese text loaded from loctext/englishus (English, 1). '
        f'The game files are not modified. {n_frases} translated phrases."\n'
        f'version = "{versao}"\n'
        'author = "Projeto de traducao PT-BR (fas)"\n'
    )


def montar_portugues(gerados: dict[str, bytes], versao: str) -> tuple[bytes, dict]:
    """Monta o .nbpatch que ADICIONA loctext/englishus/<hash> (Kind="new").

    Por que arquivos novos: o reNut 0.1.6 tem um defeito no VFS ao substituir um arquivo que já
    existe (o blob do cache é descartado por HasChildVanished, que procura o nome do cache dentro da
    pasta original). Uma pasta que ainda não existe no jogo é servida inteira a partir da cópia
    mesclada, sem esse caminho de código. O jogo procura GAME:\\loctext\\englishus\\ quando o idioma
    é Inglês (1); como o disco não traz essa pasta, o mod a fornece com os textos em PT-BR.
    """
    if not gerados:
        raise PacoteInvalido("nenhum arquivo para o pacote inglês")
    arquivos, entradas = [], []
    for nome in sorted(gerados):
        novo = gerados[nome]
        if not re.fullmatch(r"11[0-9a-f]{6}", nome):
            raise PacoteInvalido(f"nome de loctext fora do padrão: {nome!r}")
        loctext.ler(novo)  # precisa ser um loctext válido
        caminho = f"loctext/englishus/{nome}"
        entry = f"files/{caminho}"
        entradas.append((entry, novo))
        arquivos.append(
            {
                "Path": caminho,
                "Kind": "new",
                "TargetSha256": sha256(novo),
                "TargetSize": len(novo),
                "Entry": entry,
            }
        )
    pj = montar_patch_json(arquivos, versao)
    texto = json.dumps(pj, ensure_ascii=False, indent=2) + "\n"
    return _zip([("patch.json", texto.encode("utf-8"))] + entradas), pj


def verificar_pacote_portugues(nbpatch: bytes, gerados: dict[str, bytes]) -> int:
    """Simula a aplicação dos arquivos novos e confere caminho, tamanho, SHA-256 e loctext."""
    with zipfile.ZipFile(io.BytesIO(nbpatch)) as z:
        pj = json.loads(z.read("patch.json").decode("utf-8"))
        vistos = set()
        for f in pj["Files"]:
            if f["Kind"] != "new":
                raise PacoteInvalido(f"{f['Path']}: esperado Kind=new")
            prefixo = "loctext/englishus/"
            if not f["Path"].startswith(prefixo):
                raise PacoteInvalido(f"{f['Path']}: fora de loctext/englishus")
            nome = f["Path"][len(prefixo):]
            if nome not in gerados:
                raise PacoteInvalido(f"{f['Path']}: arquivo não gerado")
            if nome in vistos:
                raise PacoteInvalido(f"{f['Path']}: repetido")
            vistos.add(nome)
            dados = z.read(f["Entry"])
            if sha256(dados) != f["TargetSha256"] or len(dados) != f["TargetSize"]:
                raise PacoteInvalido(f"{f['Path']}: entrada não confere")
            if dados != gerados[nome]:
                raise PacoteInvalido(f"{f['Path']}: entrada difere do arquivo gerado")
            loctext.ler(dados)
    if vistos != set(gerados):
        raise PacoteInvalido("o pacote não lista todos os arquivos gerados")
    return len(vistos)


def executar(cam, versao: str = "0.1.0") -> dict:
    manifesto = ler_json(PASTA_BUILD / "manifest.json")
    gerados, frases = {}, 0
    for item in manifesto["arquivos"]:
        nome = item["arquivo"]
        original = ler_binario(cam.extraido / item["caminho_jogo"])
        if sha256(original) != item["origem_sha256"]:
            raise PacoteInvalido(f"{item['caminho_jogo']}: o original mudou desde a reinserção; rode reinserir de novo")
        novo = ler_binario(PASTA_BUILD / nome)
        if sha256(novo) != item["destino_sha256"] or len(novo) != item["destino_tamanho"]:
            raise PacoteInvalido(f"{nome}: o arquivo gerado não confere com o manifesto; rode reinserir de novo")
        loctext.ler(novo)
        gerados[nome] = novo
        frases += item["frases_traduzidas"]
    if (cam.extraido / "loctext" / "englishus").exists():
        raise PacoteInvalido(
            "loctext/englishus já existe na pasta do jogo; o mod não pode ser Kind=new sobre uma pasta existente"
        )
    nbpatch, pj = montar_portugues(gerados, versao)
    n = verificar_pacote_portugues(nbpatch, gerados)
    gravar_atomico(PASTA_DIST / f"{ID_MOD}.nbpatch", nbpatch)
    gravar_texto_atomico(PASTA_DIST / "mod.toml", mod_toml(versao, frases))
    return {"estado": "PASS", "arquivos": n, "frases": frases, "tamanho": len(nbpatch),
            "sha256": sha256(nbpatch), "saida": str(PASTA_DIST),
            "modo": "loctext/englishus (Kind=new)"}


def montar(originais: dict[str, bytes], gerados: dict[str, bytes], versao: str) -> tuple[bytes, dict]:
    """Monta o .nbpatch a partir de {caminho_jogo: bytes}. Só arquivos diferentes entram."""
    arquivos, entradas = [], []
    for caminho in sorted(gerados):
        orig, novo = originais[caminho], gerados[caminho]
        if orig == novo:
            continue
        loctext.ler(novo)  # o arquivo gerado precisa ser um loctext válido
        entry = f"files/{caminho}.nbdl"
        delta = delta_literal(novo)
        if aplicar_delta(orig, delta) != novo:
            raise PacoteInvalido(f"{caminho}: delta não reproduz o arquivo")
        entradas.append((entry, delta))
        arquivos.append(
            {
                "Path": caminho,
                "Kind": "delta",
                "SourceSha256": sha256(orig),
                "SourceSize": len(orig),
                "TargetSha256": sha256(novo),
                "TargetSize": len(novo),
                "Entry": entry,
            }
        )
    if not arquivos:
        raise PacoteInvalido("nenhum arquivo traduzido para empacotar")
    pj = montar_patch_json(arquivos, versao)
    texto = json.dumps(pj, ensure_ascii=False, indent=2) + "\n"
    return _zip([("patch.json", texto.encode("utf-8"))] + entradas), pj


def verificar_pacote(nbpatch: bytes, originais: dict[str, bytes]) -> int:
    """Simula a aplicação: confere SHA-256 de origem e destino de cada arquivo."""
    with zipfile.ZipFile(io.BytesIO(nbpatch)) as z:
        pj = json.loads(z.read("patch.json").decode("utf-8"))
        for f in pj["Files"]:
            orig = originais[f["Path"]]
            if sha256(orig) != f["SourceSha256"] or len(orig) != f["SourceSize"]:
                raise PacoteInvalido(f"{f['Path']}: origem não confere")
            novo = aplicar_delta(orig, z.read(f["Entry"]))
            if sha256(novo) != f["TargetSha256"] or len(novo) != f["TargetSize"]:
                raise PacoteInvalido(f"{f['Path']}: resultado não confere")
            loctext.ler(novo)
    return len(pj["Files"])
