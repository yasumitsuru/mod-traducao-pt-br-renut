"""F3 — validador das traduções (data/traducao) contra o original (data/strings).

Regras (nível):
  ERRO     chave/ID divergente; original mudou desde a extração; códigos de controle faltando ou
           sobrando; ordem dos valores %s/%d trocada; caractere sem glyph na fonte euro;
           caractere de controle ou nulo.
  AVISO    ordem dos demais códigos trocada; caractere fora do pré-cache da fonte; texto visível
           maior que o original além do limiar (+X%); espaços nas pontas diferentes; espaço duplo;
           pontuação espanhola (¿ ¡); termo obrigatório do glossário ausente.
  PENDENTE frase com original não vazio ainda sem tradução.
Estado: PASS quando não há ERRO (pendentes e avisos não reprovam), FAIL caso contrário.
"""

from __future__ import annotations

import csv
import re
from collections import Counter
from dataclasses import dataclass

from . import codigos, protegidos
from .extrair import PASTA_TRADUCAO, carregar_strings, carregar_traducao, hash_texto, nomes_traducao
from .fonte import ConjuntoFonte
from .io_seguro import RAIZ_PROJETO, gravar_json_atomico

ARQ_GLOSSARIO = RAIZ_PROJETO / "data" / "glossario.csv"
ARQ_RELATORIO = RAIZ_PROJETO / "work" / "validacao" / "relatorio.json"


@dataclass(frozen=True)
class TermoGlossario:
    termo_en: str
    termo_es: str
    termo_ptbr: str
    exigir: bool


def carregar_glossario() -> list[TermoGlossario]:
    if not ARQ_GLOSSARIO.exists():
        return []
    with open(ARQ_GLOSSARIO, "r", encoding="utf-8", newline="") as f:
        return [
            TermoGlossario(
                r.get("termo_en", "").strip(),
                r.get("termo_es", "").strip(),
                r.get("termo_ptbr", "").strip(),
                r.get("exigir", "").strip().lower() == "sim",
            )
            for r in csv.DictReader(f)
        ]


def _contem_termo(texto: str, termo: str) -> bool:
    return bool(termo) and re.search(rf"(?<!\w){re.escape(termo)}(?!\w)", texto, re.IGNORECASE) is not None


def validar_frase(
    texto_ref: str,
    texto_ptbr: str,
    fonte: ConjuntoFonte | None = None,
    glossario: list[TermoGlossario] | None = None,
    limiar: float = 0.20,
    texto_es: str | None = None,
) -> list[tuple[str, str, str]]:
    """Valida uma frase traduzida contra o texto que ela substitui no jogo (`texto_ref`).

    `texto_ref` é o inglês (base de loctext\\portuguese); `texto_es`, quando dado, entra só como
    referência adicional de espaço disponível (comprimento) e de termos do glossário.
    Retorna [(nível, regra, mensagem)].
    """
    out: list[tuple[str, str, str]] = []
    if not texto_ptbr:
        if texto_ref:
            out.append(("PENDENTE", "pendente", "sem tradução"))
        return out

    cod_es, cod_pt = codigos.extrair(texto_ref), codigos.extrair(texto_ptbr)
    if Counter(cod_es) != Counter(cod_pt):
        faltam = list((Counter(cod_es) - Counter(cod_pt)).elements())
        sobram = list((Counter(cod_pt) - Counter(cod_es)).elements())
        out.append(("ERRO", "codigos", f"faltam {faltam} sobram {sobram}"))
    else:
        pf_es = [c for c in cod_es if codigos.eh_printf(c)]
        pf_pt = [c for c in cod_pt if codigos.eh_printf(c)]
        if pf_es != pf_pt:
            out.append(("ERRO", "ordem_printf", f"ordem dos valores {pf_es} -> {pf_pt}"))
        elif cod_es != cod_pt:
            out.append(("AVISO", "ordem_codigos", "códigos em ordem diferente do original"))

    visivel = codigos.sem_codigos(texto_ptbr)
    controles = sorted({f"U+{ord(c):04X}" for c in texto_ptbr if ord(c) < 0x20 or ord(c) == 0x7F})
    if controles:
        out.append(("ERRO", "controle", f"caracteres de controle {controles}"))
    if fonte is not None:
        sem_glyph = sorted({c for c in visivel if ord(c) not in fonte.sbp})
        if sem_glyph:
            out.append(("ERRO", "fonte", f"sem glyph na fonte euro: {''.join(sem_glyph)!r}"))
        fora_cache = sorted({c for c in visivel if ord(c) in fonte.sbp and ord(c) not in fonte.precache})
        if fora_cache:
            out.append(("AVISO", "fonte_precache", f"fora do pré-cache (testar no jogo): {''.join(fora_cache)!r}"))

    # espaço disponível: o maior entre o texto substituído e o espanhol (que já cabe na interface)
    vis_ref = max(len(codigos.sem_codigos(texto_ref)), len(codigos.sem_codigos(texto_es or "")))
    if vis_ref and len(visivel) > vis_ref * (1 + limiar):
        pct = round(100 * (len(visivel) / vis_ref - 1))
        out.append(("AVISO", "comprimento", f"+{pct}% ({vis_ref} -> {len(visivel)} caracteres)"))
    if (texto_ref[:1] == " ") != (texto_ptbr[:1] == " ") or (texto_ref[-1:] == " ") != (texto_ptbr[-1:] == " "):
        out.append(("AVISO", "espacos_pontas", "espaço no início/fim diferente do original"))
    if "  " in texto_ptbr and "  " not in texto_ref:
        out.append(("AVISO", "espaco_duplo", "espaço duplo"))
    if any(c in texto_ptbr for c in "¿¡"):
        out.append(("AVISO", "pontuacao_es", "pontuação espanhola (¿ ¡) no texto em português"))
    for t in glossario or []:
        no_original = (_contem_termo(texto_ref, t.termo_en) or _contem_termo(texto_ref, t.termo_es)
                       or (texto_es is not None and _contem_termo(texto_es, t.termo_es)))
        # Termo mantido no original (nome próprio, sigla etc.) não precisa de aviso: quem cuida
        # dos nomes protegidos é a regra específica acima.
        mantido = t.termo_ptbr.lower() in {t.termo_en.lower(), t.termo_es.lower()}
        if t.exigir and t.termo_ptbr and not mantido and no_original and not _contem_termo(texto_ptbr, t.termo_ptbr):
            out.append(("AVISO", "glossario", f"'{t.termo_en or t.termo_es}' deveria virar '{t.termo_ptbr}'"))

    violacoes = protegidos.violacoes(texto_ptbr)
    for nome, variante, _ in violacoes:
        out.append(("ERRO", "nome_protegido", f"'{variante}' deve ficar '{nome}'"))
    if not violacoes:
        for nome in protegidos.ausentes(texto_ref, texto_ptbr):
            out.append(("AVISO", "nome_protegido_ausente", f"o original cita '{nome}' e a tradução não"))
    return out


def executar(arquivo: str | None = None, limiar: float = 0.20, so_traduzidas: bool = False) -> dict:
    fonte = ConjuntoFonte.carregar()
    glossario = carregar_glossario()
    nomes = [arquivo] if arquivo else nomes_traducao()
    if not nomes:
        raise FileNotFoundError(f"nenhuma tradução em {PASTA_TRADUCAO}; rode: python -I tools/ptbr.py extrair")
    itens, cont = [], Counter()
    for nome in nomes:
        trad, orig = carregar_traducao(nome), carregar_strings(nome)
        por_id = {f["id"]: f for f in orig["frases"]}
        ids_trad = [f["id"] for f in trad["frases"]]
        if sorted(ids_trad) != sorted(por_id) or len(set(ids_trad)) != len(ids_trad):
            itens.append({"arquivo": nome, "id": "*", "chave": "*", "nivel": "ERRO", "regra": "ids",
                          "mensagem": "IDs da tradução não batem com a extração"})
            cont["ERRO"] += 1
        for t in trad["frases"]:
            cont["total"] += 1
            o = por_id.get(t["id"])
            if o is None:
                continue
            res: list[tuple[str, str, str]] = []
            if o["chave"] != t["chave"]:
                res.append(("ERRO", "chave", f"chave {t['chave']} != {o['chave']}"))
            ref = o["texto_en"] if o.get("texto_en") is not None else (o.get("texto_es") or "")
            hash_atual = hash_texto(o["texto_es"]) if o.get("texto_es") is not None else None
            if t.get("texto_ptbr") and (t.get("hash_es") != hash_atual or t.get("origem_mudou")):
                res.append(("ERRO", "origem_mudou", "o texto original mudou desde a tradução; revisar"))
            res += validar_frase(ref, t.get("texto_ptbr", ""), fonte, glossario, limiar, texto_es=o.get("texto_es"))
            if t.get("texto_ptbr"):
                cont["traduzidas"] += 1
            elif not ref:
                cont["vazias"] += 1
            for nivel, regra, msg in res:
                if nivel == "PENDENTE" and so_traduzidas:
                    continue
                cont[nivel] += 1
                cont[f"regra:{regra}"] += 1
                if nivel != "PENDENTE":
                    itens.append({"arquivo": nome, "id": t["id"], "chave": t["chave"], "nivel": nivel,
                                  "regra": regra, "mensagem": msg})
    rel = {
        "estado": "PASS" if cont["ERRO"] == 0 else "FAIL",
        "arquivos": len(nomes),
        "frases": cont["total"],
        "traduzidas": cont["traduzidas"],
        "vazias_no_original": cont["vazias"],
        "pendentes": cont["PENDENTE"],
        "erros": cont["ERRO"],
        "avisos": cont["AVISO"],
        "por_regra": {k[6:]: v for k, v in sorted(cont.items()) if k.startswith("regra:")},
        "checagem_fonte": "executada" if fonte else "NOT_RUN (rode: python -I tools/ptbr.py fonte)",
        "limiar_comprimento": limiar,
        "itens": itens,
    }
    gravar_json_atomico(ARQ_RELATORIO, rel)
    return rel


def formatar_resumo(rel: dict, detalhes: bool = False) -> str:
    linhas = [
        f"Validação: {rel['estado']}  arquivos={rel['arquivos']} frases={rel['frases']} "
        f"traduzidas={rel['traduzidas']} pendentes={rel['pendentes']} vazias_no_original={rel['vazias_no_original']}",
        f"erros={rel['erros']} avisos={rel['avisos']} fonte={rel['checagem_fonte']} limiar=+{round(rel['limiar_comprimento']*100)}%",
    ]
    if rel["por_regra"]:
        linhas.append("por regra: " + ", ".join(f"{k}={v}" for k, v in rel["por_regra"].items()))
    mostrar = rel["itens"] if detalhes else [i for i in rel["itens"] if i["nivel"] == "ERRO"][:30]
    for i in mostrar:
        linhas.append(f"  {i['nivel']:6s} {i['arquivo']}[{i['id']}] {i['chave']}: {i['regra']} — {i['mensagem']}")
    linhas.append(f"Relatório completo: {ARQ_RELATORIO}")
    return "\n".join(linhas)
