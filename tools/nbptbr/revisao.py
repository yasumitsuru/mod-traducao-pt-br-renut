"""Propostas de revisão (0.8.0) -> lotes de correção.

Cada frente de revisão entrega um JSON de propostas (em `work/revisao/propostas/`, fora do git,
porque cita o original). Este módulo confere as propostas contra o catálogo atual e o validador e
gera o lote versionado (`data/lotes/lote-NNN-*.json`) que o `aplicar-lote` grava em data/traducao.

Formato das propostas:
    {
      "grupo": "G1", "revisor": "...", "arquivos": ["11b5ef5f", ...], "entradas_revisadas": 123,
      "alteracoes": [{"arquivo", "id", "chave", "pt_anterior", "pt_proposto", "motivo", "categoria",
                      "tipo", "personagem", "mundo", "gravidade", "evidencia"}],
      "mantidas_com_achado": [{"arquivo", "id", "regra", "justificativa"}],
      "pendencias": [{"arquivo", "id", "questao", "alternativas", "impacto"}],
      "tempo_de_leitura": [{"arquivo", "id", "nota"}],
      "glossario": [{"termo_en", "atual", "proposto", "motivo", "ocorrencias"}],
      "observacoes": "..."
    }
"""

from __future__ import annotations

from pathlib import Path

from .extrair import carregar_strings, carregar_traducao
from .fonte import ConjuntoFonte
from .io_seguro import ler_json
from .validar import carregar_glossario, validar_frase

GRAVIDADES = ("CRITICAL", "HIGH", "MEDIUM", "LOW")
TIPOS = ("traducao", "gramatica", "contexto", "personagem", "terminologia", "pontuacao", "tecnico",
         "ingles_remanescente", "estilo", "comprimento")
CAMPOS_ALTERACAO = ("arquivo", "id", "pt_anterior", "pt_proposto", "motivo", "categoria", "tipo",
                    "gravidade", "evidencia")


def carregar(caminho: str | Path) -> dict:
    dados = ler_json(caminho)
    if not isinstance(dados, dict) or not isinstance(dados.get("alteracoes"), list):
        raise ValueError(f"{caminho}: propostas sem a lista 'alteracoes'")
    return dados


def checar(propostas: dict, fonte: ConjuntoFonte | None = None, glossario=None) -> dict:
    """Confere cada alteração: campos, ID, texto anterior igual ao catálogo e validador sem ERRO."""
    fonte = fonte if fonte is not None else ConjuntoFonte.carregar()
    glossario = glossario if glossario is not None else carregar_glossario()
    problemas: list[dict] = []
    avisos: list[dict] = []
    vistos: set[tuple[str, str]] = set()
    cache: dict[str, tuple[dict, dict]] = {}
    for n, alt in enumerate(propostas["alteracoes"]):
        rotulo = f"#{n} {alt.get('arquivo')}[{alt.get('id')}]"
        faltam = [c for c in CAMPOS_ALTERACAO if not alt.get(c)]
        if faltam:
            problemas.append({"onde": rotulo, "problema": f"campos ausentes: {faltam}"})
            continue
        if alt["gravidade"] not in GRAVIDADES:
            problemas.append({"onde": rotulo, "problema": f"gravidade inválida {alt['gravidade']!r}"})
        if alt["tipo"] not in TIPOS:
            avisos.append({"onde": rotulo, "aviso": f"tipo fora da lista {alt['tipo']!r}"})
        chave = (alt["arquivo"], alt["id"])
        if chave in vistos:
            problemas.append({"onde": rotulo, "problema": "entrada repetida nas propostas"})
            continue
        vistos.add(chave)
        if alt["arquivo"] not in cache:
            try:
                s = carregar_strings(alt["arquivo"])
                t = carregar_traducao(alt["arquivo"])
            except FileNotFoundError:
                problemas.append({"onde": rotulo, "problema": "arquivo inexistente"})
                continue
            cache[alt["arquivo"]] = ({f["id"]: f for f in s["frases"]}, {f["id"]: f for f in t["frases"]})
        orig, trad = cache[alt["arquivo"]]
        if alt["id"] not in orig or alt["id"] not in trad:
            problemas.append({"onde": rotulo, "problema": "id inexistente"})
            continue
        atual = trad[alt["id"]].get("texto_ptbr", "")
        if alt["pt_anterior"] != atual:
            problemas.append({"onde": rotulo, "problema": "pt_anterior difere do catálogo atual"})
            continue
        if alt["pt_proposto"] == atual:
            problemas.append({"onde": rotulo, "problema": "proposta igual ao texto atual"})
            continue
        o = orig[alt["id"]]
        ref = o["texto_en"] if o.get("texto_en") is not None else (o.get("texto_es") or "")
        for nivel, regra, msg in validar_frase(ref, alt["pt_proposto"], fonte, glossario, 0.20, texto_es=o.get("texto_es")):
            if nivel == "ERRO":
                problemas.append({"onde": rotulo, "problema": f"validador: {regra}: {msg}"})
            elif regra in {"comprimento", "glossario", "nome_protegido_ausente", "espaco_duplo", "espacos_pontas",
                           "ordem_codigos", "fonte_precache"}:
                avisos.append({"onde": rotulo, "aviso": f"{regra}: {msg}"})
    return {
        "estado": "PASS" if not problemas else "FAIL",
        "alteracoes": len(propostas["alteracoes"]),
        "problemas": problemas,
        "avisos": avisos,
    }


def lote(alteracoes: list[dict], numero: str, descricao: str) -> dict:
    """Monta o lote versionado (só IDs e PT-BR)."""
    traducoes: dict[str, dict[str, str]] = {}
    for alt in sorted(alteracoes, key=lambda a: (a["arquivo"], a["id"])):
        traducoes.setdefault(alt["arquivo"], {})[alt["id"]] = alt["pt_proposto"]
    return {"lote": numero, "descricao": descricao, "traducoes": traducoes}


__all__ = ["GRAVIDADES", "TIPOS", "carregar", "checar", "lote"]
