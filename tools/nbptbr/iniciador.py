"""Pacote do iniciador: leva a saída da F5 para app/ptbr_copy_package e app/src.

O iniciador (app/) monta uma cópia isolada do jogo e grava nela os textos ingleses (Debug/11) que já
têm PT-BR. Esta etapa:
  1. lê build/loctext/english/manifest.json (gerado por `reinserir`);
  2. escolhe só os arquivos com frases traduzidas e confere, antes de gravar qualquer coisa, que cada
     um tem o SHA-256 e o tamanho do manifesto, um caminho Debug/11/XX/YY/ZZ válido e é um loctext
     legível; com `nbpatch`, confere também que o .nbpatch lista exatamente os mesmos arquivos;
  3. copia os arquivos para app/ptbr_copy_package/files/<caminho>, grava o manifest.json do pacote
     (lido por aplicar-copia.ps1) e app/src/traducoes_geradas.rs (lista embutida com include_bytes!).

Tudo é gravado dentro da raiz do projeto, de forma atômica e byte-estável. Arquivos em files/ que
não estejam na lista nova fazem a etapa parar sem gravar nada (o script de cópia recusaria o pacote);
com `limpar=True` (opção --limpar) eles são removidos, sempre dentro de files/.
"""

from __future__ import annotations

import io
import json
import os
import re
import zipfile
from pathlib import Path

from . import loctext
from .reinserir import caminho_ingles
from .io_seguro import (
    RAIZ_PROJETO,
    caminho_gravavel,
    gravar_atomico,
    gravar_json_atomico,
    gravar_texto_atomico,
    ler_binario,
    ler_json,
    sha256,
)

PASTA_BUILD = RAIZ_PROJETO / "build" / "loctext" / "english"
PASTA_PACOTE = RAIZ_PROJETO / "app" / "ptbr_copy_package"
ARQUIVO_RS = RAIZ_PROJETO / "app" / "src" / "traducoes_geradas.rs"
NBPATCH = RAIZ_PROJETO / "dist" / "ptbr_traducao" / "ptbr_traducao.nbpatch"

CAMINHO_RE = re.compile(r"Debug/11/[0-9a-f]{2}/[0-9a-f]{2}/[0-9a-f]{2}")
NOME_RE = re.compile(r"11[0-9a-f]{6}")
MOTIVO_SEM_OVERLAY = (
    "O .nbpatch que substitui um arquivo existente falha no reNut 0.1.6 com STATUS_OBJECT_NAME_NOT_FOUND "
    "(0xc0000034): o VFS descarta o blob de mods/.cache porque HasChildVanished procura o nome do cache "
    "dentro da pasta original do jogo (mod_loader.cpp/Mount + host_provider.cpp). A v0.5.0 contorna o "
    "defeito entregando loctext/englishus como arquivos novos. Esta copia fisica serve apenas de teste A/B."
)


class PacoteIniciadorInvalido(RuntimeError):
    pass


def _itens_traduzidos(manifesto: dict, pasta_build: Path) -> list[dict]:
    try:
        return _itens_validados(manifesto, pasta_build)
    except PacoteIniciadorInvalido:
        raise
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise PacoteIniciadorInvalido(f"manifesto da F5 malformado ou arquivo ilegível: {exc!r}") from exc


def _itens_validados(manifesto: dict, pasta_build: Path) -> list[dict]:
    itens, vistos = [], set()
    for item in manifesto["arquivos"]:
        if not item.get("frases_traduzidas"):
            continue
        caminho, nome = item["caminho_jogo"], item["arquivo"]
        if not isinstance(nome, str) or not NOME_RE.fullmatch(nome):
            raise PacoteIniciadorInvalido(f"nome de arquivo fora do padrão: {nome!r}")
        if not isinstance(caminho, str) or not CAMINHO_RE.fullmatch(caminho) or caminho != caminho_ingles(nome):
            raise PacoteIniciadorInvalido(f"{nome}: caminho fora do padrão Debug/11: {caminho!r}")
        if caminho in vistos:
            raise PacoteIniciadorInvalido(f"caminho repetido no manifesto: {caminho}")
        vistos.add(caminho)
        dados = ler_binario(pasta_build / item["arquivo"])
        if sha256(dados) != item["destino_sha256"] or len(dados) != item["destino_tamanho"]:
            raise PacoteIniciadorInvalido(f"{caminho}: o arquivo gerado não confere com o manifesto; rode reinserir")
        loctext.ler(dados)  # precisa continuar legível pelo leitor do projeto
        if item["destino_sha256"] == item["origem_sha256"]:
            # Arquivo com apenas tokens técnicos (cores/HTML) ou nomes idênticos: não há o que
            # substituir na cópia física. Ele continua no .nbpatch (pasta englishus completa), mas
            # não entra em app/ptbr_copy_package/files nem na lista embutida.
            continue
        itens.append({**item, "dados": dados})
    if not itens:
        raise PacoteIniciadorInvalido("nenhum arquivo traduzido no manifesto da F5")
    return sorted(itens, key=lambda i: i["caminho_jogo"])


def _conferir_nbpatch(nbpatch: bytes, itens: list[dict], manifesto: dict) -> str | None:
    try:
        with zipfile.ZipFile(io.BytesIO(nbpatch)) as z:
            pj = json.loads(z.read("patch.json").decode("utf-8"))
    except (zipfile.BadZipFile, KeyError, ValueError) as exc:
        raise PacoteIniciadorInvalido(f".nbpatch ilegível: {exc}") from exc
    arquivos = pj.get("Files", [])
    no_patch = {(f["Path"], f["TargetSha256"]) for f in arquivos}
    if arquivos and all(str(f["Path"]).startswith("loctext/englishus/") for f in arquivos):
        # v0.6.0: o pacote entrega a pasta inglesa inteira como arquivos novos.
        esperado = {(f"loctext/englishus/{i['arquivo']}", i["destino_sha256"]) for i in manifesto["arquivos"]}
        if any(f.get("Kind") != "new" for f in arquivos):
            raise PacoteIniciadorInvalido(".nbpatch inglês tem arquivo que não é Kind=new")
    else:
        # v0.4.x: pacote delta sobre Debug/11, restrito aos arquivos traduzidos.
        esperado = {(i["caminho_jogo"], i["destino_sha256"]) for i in itens}
    if no_patch != esperado:
        raise PacoteIniciadorInvalido(".nbpatch e saída da F5 listam arquivos diferentes; rode empacotar de novo")
    return pj.get("Version")


def codigo_rust(itens: list[dict], pasta_pacote: Path, arquivo_rs: Path) -> str:
    linhas = [
        "// Gerado por `python -I tools/ptbr.py sincronizar-iniciador` a partir da saída da F5",
        "// (build/loctext/english/manifest.json). Não edite à mão.",
        f"pub const TRANSLATIONS: [TranslationFile; {len(itens)}] = [",
    ]
    for i in itens:
        alvo = pasta_pacote / "files" / Path(*i["caminho_jogo"].split("/"))
        rel = os.path.relpath(alvo, arquivo_rs.parent).replace(os.sep, "/")
        linhas += [
            "    TranslationFile {",
            f'        path: "{i["caminho_jogo"]}",',
            f"        source_size: {i['origem_tamanho']:_},",
            f'        bytes: include_bytes!("{rel}"),',
            "    },",
        ]
    linhas.append("];")
    return "\n".join(linhas) + "\n"


def manifesto_pacote(itens: list[dict], versao: str | None, nbpatch_sha: str | None) -> dict:
    return {
        "format": 1,
        "id": "ptbr_traducao_physical_copy",
        "name": "Traducao PT-BR - copia fisica",
        "version": versao,
        "method": "copy-game-tree-and-replace-files",
        "native_overlay": {"used": False, "reason": MOTIVO_SEM_OVERLAY},
        "source_nbpatch_sha256": nbpatch_sha,
        "files": [
            {
                "path": i["caminho_jogo"],
                "source_sha256": i["origem_sha256"],
                "source_size": i["origem_tamanho"],
                "target_sha256": i["destino_sha256"],
                "target_size": i["destino_tamanho"],
            }
            for i in itens
        ],
    }


def executar(
    pasta_build: Path = PASTA_BUILD,
    pasta_pacote: Path = PASTA_PACOTE,
    arquivo_rs: Path = ARQUIVO_RS,
    nbpatch: Path | None = NBPATCH,
    limpar: bool = False,
) -> dict:
    """Valida tudo e só então grava. Arquivos em files/ que não estão na lista nova (versões
    anteriores, temporários interrompidos) fariam aplicar-copia.ps1 recusar o pacote: sem `limpar`
    a etapa para sem gravar nada; com `limpar` eles são removidos (só arquivos comuns dentro de files/).
    """
    # destinos conferidos antes de qualquer leitura pesada ou gravação
    pasta_pacote = caminho_gravavel(pasta_pacote)
    arquivo_rs = caminho_gravavel(arquivo_rs)
    try:
        manifesto = ler_json(pasta_build / "manifest.json")
    except ValueError as exc:
        raise PacoteIniciadorInvalido(f"manifesto da F5 ilegível: {exc}") from exc
    itens = _itens_traduzidos(manifesto, pasta_build)
    versao = nbpatch_sha = None
    if nbpatch is not None:
        dados_patch = ler_binario(nbpatch)
        versao = _conferir_nbpatch(dados_patch, itens, manifesto)
        nbpatch_sha = sha256(dados_patch)

    pasta_files = pasta_pacote / "files"
    listados = {pasta_files / Path(*i["caminho_jogo"].split("/")) for i in itens}
    antigos = []
    if pasta_files.exists():
        for p in sorted(pasta_files.rglob("*")):
            if p.is_symlink() or p.is_junction():
                raise PacoteIniciadorInvalido(f"link inesperado no pacote do iniciador: {p}")
            if p.is_file() and p not in listados:
                antigos.append(p)
    rel_antigos = [p.relative_to(pasta_files).as_posix() for p in antigos]
    if antigos and not limpar:
        raise PacoteIniciadorInvalido(
            "o pacote do iniciador tem arquivos fora da lista nova (o script de cópia os recusaria): "
            f"{', '.join(rel_antigos)}; rode de novo com --limpar para removê-los"
        )
    for p in antigos:
        os.unlink(caminho_gravavel(p))

    for i in itens:
        gravar_atomico(pasta_files / Path(*i["caminho_jogo"].split("/")), i["dados"])
    gravar_json_atomico(pasta_pacote / "manifest.json", manifesto_pacote(itens, versao, nbpatch_sha))
    gravar_texto_atomico(arquivo_rs, codigo_rust(itens, pasta_pacote, arquivo_rs))
    return {
        "estado": "PASS",
        "arquivos": len(itens),
        "frases": sum(i["frases_traduzidas"] for i in itens),
        "versao": versao,
        "nbpatch_sha256": nbpatch_sha,
        "removidos": rel_antigos,
        "pacote": str(pasta_pacote),
        "rust": str(arquivo_rs),
    }
