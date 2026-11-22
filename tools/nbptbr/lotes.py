"""F4 — aplica um lote de tradução (data/lotes/lote-NNN.json) em data/traducao.

Formato do lote (versionado; só texto PT-BR e IDs):
    {
      "lote": "001",
      "descricao": "menus principais ...",
      "traducoes": {"<arquivo>": {"<id>": "texto PT-BR", ...}, ...}
    }
Cada frase aplicada recebe "lote": "<NNN>" para rastreabilidade. IDs inexistentes geram erro e
nada é gravado (todas as checagens acontecem antes da primeira escrita).
"""

from __future__ import annotations

from pathlib import Path

from .extrair import PASTA_TRADUCAO, carregar_traducao
from .io_seguro import gravar_json_atomico, ler_json


class LoteInvalido(ValueError):
    pass


def checar(caminho_lote: str | Path, limiar: float = 0.20) -> dict:
    """Confere um lote sem gravar nada: IDs, códigos, fonte, comprimento e glossário.

    Também conta, nos arquivos do lote, quantas frases com texto ainda ficariam sem tradução.
    """
    from collections import Counter

    from .extrair import carregar_strings
    from .fonte import ConjuntoFonte
    from .validar import carregar_glossario, validar_frase

    lote = ler_json(caminho_lote)
    fonte, glossario = ConjuntoFonte.carregar(), carregar_glossario()
    itens, cont = [], Counter()
    for arquivo, trad in sorted(lote.get("traducoes", {}).items()):
        try:
            orig = {f["id"]: f for f in carregar_strings(arquivo)["frases"]}
            ja = {f["id"] for f in carregar_traducao(arquivo)["frases"] if f.get("texto_ptbr")}
        except FileNotFoundError:
            itens.append(("ERRO", arquivo, "*", "arquivo", "arquivo inexistente"))
            cont["ERRO"] += 1
            continue
        for fid, texto in trad.items():
            cont["frases"] += 1
            o = orig.get(fid)
            if o is None:
                itens.append(("ERRO", arquivo, fid, "id", "id não existe no arquivo"))
                cont["ERRO"] += 1
                continue
            if not isinstance(texto, str) or not texto:
                itens.append(("ERRO", arquivo, fid, "vazio", "texto vazio"))
                cont["ERRO"] += 1
                continue
            ref = o["texto_en"] if o.get("texto_en") is not None else (o.get("texto_es") or "")
            for nivel, regra, msg in validar_frase(ref, texto, fonte, glossario, limiar, texto_es=o.get("texto_es")):
                cont[nivel] += 1
                itens.append((nivel, arquivo, fid, regra, msg))
        faltam = [fid for fid, o in orig.items()
                  if (o.get("texto_en") or o.get("texto_es")) and fid not in trad and fid not in ja]
        cont["faltam"] += len(faltam)
        if faltam:
            itens.append(("INFO", arquivo, ",".join(faltam[:12]), "faltam", f"{len(faltam)} frase(s) do arquivo fora do lote"))
    return {"estado": "PASS" if cont["ERRO"] == 0 else "FAIL", "contagem": dict(cont), "itens": itens}


def aplicar(caminho_lote: str | Path) -> dict:
    lote = ler_json(caminho_lote)
    num = str(lote.get("lote", "")).strip()
    if not num:
        raise LoteInvalido("lote sem número")
    pendentes: dict[str, dict] = {}
    total = 0
    for arquivo, trad in sorted(lote["traducoes"].items()):
        if not (PASTA_TRADUCAO / f"{arquivo}.json").exists():
            raise LoteInvalido(f"arquivo {arquivo} não existe em data/traducao")
        doc = carregar_traducao(arquivo)
        por_id = {f["id"]: f for f in doc["frases"]}
        for fid, texto in trad.items():
            if fid not in por_id:
                raise LoteInvalido(f"{arquivo}: id {fid} não existe")
            if not isinstance(texto, str) or not texto:
                raise LoteInvalido(f"{arquivo}[{fid}]: texto vazio ou inválido")
            por_id[fid]["texto_ptbr"] = texto
            por_id[fid]["lote"] = num
            total += 1
        pendentes[arquivo] = doc
    for arquivo, doc in pendentes.items():
        gravar_json_atomico(PASTA_TRADUCAO / f"{arquivo}.json", doc)
    return {"lote": num, "arquivos": len(pendentes), "frases": total}
