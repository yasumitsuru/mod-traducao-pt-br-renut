"""Monta a pasta de jogo PT-BR: build/jogo_ptbr/extraido.

Uso: teste visual isolado (work\\renut_teste) — reproduz o jogo instalado com a tradução sem mexer
na pasta do jogo. (No reNut big-lua-energy o .nbpatch é aplicado e ligado ao cache, mas o jogo recebe
"não encontrado" ao abrir o arquivo; ver docs/renut-mods.md.)

Layout gerado (nada é copiado do jogo além de arquivos pequenos):
    extraido\\Bundle, loctext, xuifontcachefont, xuifontcachemeta  -> junções para o jogo original
    extraido\\Debug\\36                                             -> junção
    extraido\\Debug\\db_index.txt                                   -> cópia
    extraido\\Debug\\11\\XX\\YY\\ZZ                                   -> textos ingleses com o PT-BR
    extraido\\default.xex, default.xexp, tile.bmp e outros arquivos soltos -> cópias
Não existe loctext\\portuguese: com ela presente o jogo para com erro de disco.

Junções são removidas com os.rmdir (remove só o link, nunca o conteúdo do destino).
O reNut monta o jogo como somente leitura por padrão (game_writable desligado).
"""

from __future__ import annotations

import os
import shutil
import stat
from pathlib import Path

import _winapi

from .config import Caminhos
from .io_seguro import RAIZ_PROJETO, caminho_gravavel, gravar_atomico, ler_binario, ler_json, sha256
from .reinserir import PASTA_SAIDA as PASTA_BUILD

PASTA_JOGO = RAIZ_PROJETO / "build" / "jogo_ptbr" / "extraido"


def eh_juncao(p: Path) -> bool:
    try:
        return bool(os.lstat(p).st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT) and p.is_dir()
    except FileNotFoundError:
        return False


def _remover_seguro(p: Path, raiz: Path = PASTA_JOGO) -> None:
    """Remove um item da pasta gerada sem jamais seguir junções."""
    p = Path(p)
    raiz = caminho_gravavel(raiz)
    caminho_gravavel(p.parent)  # o link em si fica dentro do projeto; o destino nunca é tocado
    if not p.absolute().is_relative_to(raiz.absolute()):
        raise RuntimeError(f"recusado: {p} não pertence à pasta gerada")
    if not p.resolve().is_relative_to(raiz.resolve()) and not eh_juncao(p):
        raise RuntimeError(f"recusado: {p} não pertence à pasta gerada")
    if eh_juncao(p):
        os.rmdir(p)  # remove só a junção
    elif p.is_dir():
        for filho in p.iterdir():
            _remover_seguro(filho, raiz)
        os.rmdir(p)
    elif p.exists():
        os.unlink(p)


def _juncao(destino_real: Path, link: Path, raiz: Path = PASTA_JOGO) -> None:
    caminho_gravavel(link.parent)
    if link.exists() or eh_juncao(link):
        _remover_seguro(link, raiz)
    link.parent.mkdir(parents=True, exist_ok=True)
    _winapi.CreateJunction(str(destino_real), str(link))


def executar(cam: Caminhos, destino: Path | None = None) -> dict:
    """Monta a cópia de teste. `destino` exige um caminho novo dentro do projeto.

    Sem `destino`, preserva o comportamento legado em build/jogo_ptbr, que substitui a
    pasta anteriormente gerada. O fluxo novo usa destino explícito e nunca o substitui.
    """
    origem = cam.extraido
    manifesto = ler_json(PASTA_BUILD / "manifest.json")
    if destino is None:
        raiz_saida = PASTA_JOGO
        caminho_gravavel(raiz_saida)  # valida ancestrais/junções antes de criar qualquer pasta
        if os.path.lexists(raiz_saida):
            _remover_seguro(raiz_saida, raiz_saida)
        raiz_saida.mkdir(parents=True)
    else:
        entrada = Path(destino)
        if not entrada.is_absolute():
            entrada = RAIZ_PROJETO / entrada
        raiz_saida = caminho_gravavel(entrada)
        if os.path.lexists(entrada):
            raise FileExistsError(f"destino já existe: {entrada}")
        raiz_saida.parent.mkdir(parents=True, exist_ok=True)
        raiz_saida.mkdir()

    juncoes, copias = [], []
    for item in sorted(origem.iterdir()):
        alvo = raiz_saida / item.name
        if item.is_dir() and item.name != "Debug":
            _juncao(item, alvo, raiz_saida)
            juncoes.append(item.name)
        elif item.is_file():
            gravar_atomico(alvo, ler_binario(item))
            copias.append(item.name)
    for item in sorted((origem / "Debug").iterdir()):
        alvo = raiz_saida / "Debug" / item.name
        if item.is_dir() and item.name != "11":
            _juncao(item, alvo, raiz_saida)
            juncoes.append(f"Debug/{item.name}")
        elif item.is_file():
            gravar_atomico(alvo, ler_binario(item))
            copias.append(f"Debug/{item.name}")

    traduzidos = 0
    for m in manifesto["arquivos"]:
        dados = ler_binario(PASTA_BUILD / m["arquivo"])
        if sha256(dados) != m["destino_sha256"]:
            raise RuntimeError(f"{m['arquivo']}: build/loctext não confere com o manifesto; rode reinserir")
        gravar_atomico(raiz_saida / m["caminho_jogo"], dados)
        traduzidos += m["frases_traduzidas"] > 0
    if (raiz_saida / "loctext" / "portuguese").exists():
        raise RuntimeError("loctext/portuguese não pode existir (o jogo para com erro de disco)")
    return {
        "estado": "PASS",
        "pasta": str(raiz_saida),
        "juncoes": juncoes,
        "copias": copias,
        "arquivos_texto": len(manifesto["arquivos"]),
        "arquivos_traduzidos": traduzidos,
    }


__all__ = ["executar", "PASTA_JOGO", "eh_juncao", "shutil"]
