"""F5 — reinserção: gera os textos ingleses (Debug\\11\\XX\\YY\\ZZ) com o PT-BR.

Por que o inglês (verificado no jogo em 2026-11-19, docs/renut-mods.md): com o idioma Português (9)
no menu do reNut o jogo procura GAME:\\loctext\\portuguese\\; sem essa pasta ele passa a usar o inglês
(Debug\\11). Com a pasta presente, o jogo lê o arquivo e para com erro de disco (não há Português
interno). Logo, escolher Português mostra os textos de Debug\\11, que passam a levar o PT-BR.

Para cada um dos 107 arquivos:
  1. lê o arquivo INGLÊS (Debug\\11\\XX\\YY\\ZZ, conjunto completo de chaves) em modo somente leitura;
  2. aplica, por chave, as frases com texto_ptbr de data/traducao (as demais ficam em inglês);
  3. confere que o texto espanhol de referência não mudou desde a tradução (hash_es);
  4. grava build/loctext/english/<arquivo>, relê e compara frase a frase (aceite da F5).
Recusa reinserir se o validador acusar ERRO.
"""

from __future__ import annotations

from . import loctext, validar
from .config import IDIOMA_ALVO, Caminhos
from .extrair import carregar_traducao, hash_texto
from .io_seguro import RAIZ_PROJETO, gravar_atomico, gravar_json_atomico, ler_binario, sha256

PASTA_SAIDA = RAIZ_PROJETO / "build" / "loctext" / "english"


def caminho_ingles(nome: str) -> str:
    """Caminho do texto inglês na pasta do jogo: Debug/11/XX/YY/ZZ."""
    return f"Debug/{nome[0:2]}/{nome[2:4]}/{nome[4:6]}/{nome[6:8]}"


class ReinsercaoRecusada(RuntimeError):
    pass


def reinserir_bytes(base: bytes, traducao: dict, textos_es: dict[str, str] | None = None) -> tuple[bytes, int]:
    """Aplica a tradução (por chave) sobre o arquivo base.

    `textos_es` ({chave: texto espanhol}) é a referência do hash_es; sem ela, o próprio texto da base é
    usado (caso em que a base é o espanhol).
    """
    arq = loctext.ler(base)
    chaves_base = {f.chave: f for f in arq.frases()}
    novos: dict[str, str] = {}
    for t in traducao["frases"]:
        if not t.get("texto_ptbr"):
            continue
        if t["chave"] not in chaves_base:
            continue  # chave só existe no espanhol (11 frases dos créditos)
        if textos_es is None:
            ref, conferir = chaves_base[t["chave"]].texto, True
        else:
            ref, conferir = textos_es.get(t["chave"]), True
            if ref is None:
                conferir = False  # sem texto espanhol: a base inglesa é a única referência
        if conferir and t.get("hash_es") != hash_texto(ref):
            raise ReinsercaoRecusada(f"{traducao['arquivo']}[{t['id']}]: original mudou desde a tradução")
        novos[t["chave"]] = t["texto_ptbr"]
    saida = loctext.escrever(arq.com_textos_por_chave(novos))
    esperado = {f.chave: novos.get(f.chave, f.texto) for f in arq.frases()}
    obtido = {f.chave: f.texto for f in loctext.ler(saida).frases()}
    if obtido != esperado:
        raise ReinsercaoRecusada(f"{traducao['arquivo']}: arquivo gerado não confere com o JSON")
    return saida, len(novos)


def executar(cam: Caminhos) -> dict:
    rel = validar.executar(so_traduzidas=True)
    if rel["estado"] != "PASS":
        raise ReinsercaoRecusada(f"validador com {rel['erros']} erro(s); rode: python -I tools/ptbr.py validar")
    nomes = sorted(p.name for p in cam.pasta_idioma(IDIOMA_ALVO).iterdir() if p.is_file())
    manifesto, total_subst, com_trad, frases_total = [], 0, 0, 0
    for nome in nomes:
        base = ler_binario(cam.arquivo_ingles(nome))
        es = {f.chave: f.texto for f in loctext.ler(ler_binario(cam.pasta_idioma(IDIOMA_ALVO) / nome)).frases()}
        saida, n = reinserir_bytes(base, carregar_traducao(nome), es)
        total_subst += n
        com_trad += n > 0
        frases_total += len(loctext.ler(saida).asset.textos)
        gravar_atomico(PASTA_SAIDA / nome, saida)
        manifesto.append(
            {
                "arquivo": nome,
                "caminho_jogo": caminho_ingles(nome),
                "frases_traduzidas": n,
                "origem_sha256": sha256(base),
                "origem_tamanho": len(base),
                "destino_sha256": sha256(saida),
                "destino_tamanho": len(saida),
            }
        )
    gravar_json_atomico(PASTA_SAIDA / "manifest.json", {"destino": "Debug/11 (inglês)", "arquivos": manifesto})
    return {
        "estado": "PASS",
        "arquivos": len(nomes),
        "com_traducao": com_trad,
        "substituidas": total_subst,
        "frases_no_jogo": frases_total,
        "saida": str(PASTA_SAIDA),
    }
