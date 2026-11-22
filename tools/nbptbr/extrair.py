"""F2 — exporta as frases para JSON.

Saídas:
  data/strings/<arquivo>.json   (FORA do git) extração completa: id, chave, texto_en, texto_es,
                                texto_ptbr (copiado de data/traducao), códigos de controle.
  data/traducao/<arquivo>.json  (versionado) fonte da verdade da tradução: id, chave, hash_es e
                                texto_ptbr. Traduções existentes são preservadas.
  data/indice_arquivos.json     (versionado) contagem de frases por arquivo, sem texto do jogo.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from . import codigos, loctext
from .config import IDIOMA_ALVO, Caminhos
from .io_seguro import RAIZ_PROJETO, gravar_json_atomico, ler_binario, ler_json, sha256

PASTA_STRINGS = RAIZ_PROJETO / "data" / "strings"
PASTA_TRADUCAO = RAIZ_PROJETO / "data" / "traducao"
ARQ_INDICE = RAIZ_PROJETO / "data" / "indice_arquivos.json"


def hash_texto(texto: str) -> str:
    """Impressão digital curta do texto original (versionável no lugar do texto)."""
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:16]


def _traducao_existente(nome: str) -> dict[str, dict]:
    arq = PASTA_TRADUCAO / f"{nome}.json"
    if not arq.exists():
        return {}
    return {f["id"]: f for f in ler_json(arq)["frases"]}


def extrair_arquivo(cam: Caminhos, nome: str) -> tuple[dict, dict, dict]:
    dados_es = ler_binario(cam.pasta_idioma(IDIOMA_ALVO) / nome)
    es = loctext.ler(dados_es)
    en_path = cam.arquivo_ingles(nome)
    en_frases: dict[str, str] = {}
    en_lista = []
    sha_en = None
    if en_path.is_file():
        dados_en = ler_binario(en_path)
        sha_en = sha256(dados_en)
        en_lista = loctext.ler(dados_en).frases()
        en_frases = {f.chave: f.texto for f in en_lista}

    existentes = _traducao_existente(nome)
    frases_strings, frases_trad = [], []
    chaves_es = {f.chave for f in es.frases()}
    # Frases do espanhol, mais as que só existem no inglês (72 linhas dos créditos): o arquivo final
    # (loctext\portuguese) é montado sobre o inglês, então todas as chaves dele podem ser traduzidas.
    entradas = [(f.id, f.chave, f.texto) for f in es.frases()]
    entradas += [(f.id, f.chave, None) for f in en_lista if f.chave not in chaves_es]
    for fid, chave, texto_es in entradas:
        ant = existentes.get(fid)
        h = hash_texto(texto_es) if texto_es is not None else None
        mesmo = bool(ant) and ant.get("chave") == chave
        ptbr = ant["texto_ptbr"] if mesmo else ""
        item_trad = {"id": fid, "chave": chave, "hash_es": h, "texto_ptbr": ptbr}
        if texto_es is None:
            item_trad["so_ingles"] = True
        if mesmo and ptbr:
            if ant.get("hash_es") != h or ant.get("origem_mudou"):
                item_trad["origem_mudou"] = True
                item_trad["hash_es"] = ant.get("hash_es")  # mantém o hash da versão traduzida
            if ant.get("lote"):
                item_trad["lote"] = ant["lote"]
        frases_trad.append(item_trad)
        ref = en_frases.get(chave) if en_frases.get(chave) is not None else (texto_es or "")
        frases_strings.append(
            {
                "id": fid,
                "chave": chave,
                "texto_en": en_frases.get(chave),
                "texto_es": texto_es,
                "texto_ptbr": ptbr,
                "codigos": codigos.extrair(ref),
            }
        )

    base = {"arquivo": nome, "asset": es.nome_asset}
    doc_strings = dict(
        base,
        sha256_es=sha256(dados_es),
        sha256_en=sha_en,
        total=len(frases_strings),
        frases=frases_strings,
    )
    doc_trad = dict(base, frases=frases_trad)
    resumo = dict(
        base,
        frases=len(frases_strings),
        vazias=sum(1 for f in frases_strings if not (f["texto_en"] or f["texto_es"])),
        es_vazia_en_com_texto=sum(1 for f in frases_strings if f["texto_es"] == "" and f["texto_en"]),
        sem_ingles=sum(1 for f in frases_strings if f["texto_en"] is None),
        so_ingles=sum(1 for f in frases_strings if f["texto_es"] is None),
        traduzidas=sum(1 for f in frases_trad if f["texto_ptbr"]),
    )
    return doc_strings, doc_trad, resumo


def executar(cam: Caminhos) -> dict:
    nomes = sorted(p.name for p in cam.pasta_idioma(IDIOMA_ALVO).iterdir() if p.is_file())
    por_arquivo = []
    for nome in nomes:
        doc_strings, doc_trad, resumo = extrair_arquivo(cam, nome)
        # valida invariantes antes de gravar
        assert len(doc_strings["frases"]) == len(doc_trad["frases"]) == resumo["frases"]
        assert len({f["id"] for f in doc_trad["frases"]}) == resumo["frases"], "ids repetidos"
        gravar_json_atomico(PASTA_STRINGS / f"{nome}.json", doc_strings)
        gravar_json_atomico(PASTA_TRADUCAO / f"{nome}.json", doc_trad)
        por_arquivo.append(resumo)
    total = {
        "idioma_base": IDIOMA_ALVO,
        "arquivos": len(por_arquivo),
        "frases": sum(r["frases"] for r in por_arquivo),
        "vazias": sum(r["vazias"] for r in por_arquivo),
        "es_vazia_en_com_texto": sum(r["es_vazia_en_com_texto"] for r in por_arquivo),
        "com_ingles": sum(r["frases"] - r["sem_ingles"] for r in por_arquivo),
        "so_ingles": sum(r["so_ingles"] for r in por_arquivo),
        "traduzidas": sum(r["traduzidas"] for r in por_arquivo),
        "por_arquivo": por_arquivo,
    }
    gravar_json_atomico(ARQ_INDICE, total)
    return total


def carregar_strings(nome: str) -> dict:
    arq = PASTA_STRINGS / f"{nome}.json"
    if not arq.exists():
        raise FileNotFoundError(f"{arq} não existe; rode: python -I tools/ptbr.py extrair")
    return ler_json(arq)


def carregar_traducao(nome: str) -> dict:
    return ler_json(PASTA_TRADUCAO / f"{nome}.json")


def nomes_traducao() -> list[str]:
    return sorted(p.stem for p in PASTA_TRADUCAO.glob("*.json"))


__all__ = ["executar", "hash_texto", "carregar_strings", "carregar_traducao", "nomes_traducao", "Path"]
