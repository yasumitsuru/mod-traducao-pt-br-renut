#!/usr/bin/env python3
"""Gera o mod PT-BR no seu computador, a partir da sua copia do jogo.

O pacote nao acompanha arquivos do jogo: ele e montado aqui, lendo os textos originais
que ja existem na sua instalacao legitima do reNut. O resultado e a pasta
`saida/ptbr_traducao`, pronta para copiar para a pasta `mods`.

Uso:
    python gerar_mod.py --jogo "C:\\caminho\\da\\instalacao\\do\\reNut"
    python gerar_mod.py --jogo "C:\\...\\game\\extraido"
    python gerar_mod.py --jogo "C:\\...\\reNut" --saida "C:\\caminho\\saida"

Sem argumentos, o programa pede o caminho.
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
PASTA_TOOLS = RAIZ / "tools" if (RAIZ / "tools" / "nbptbr").is_dir() else RAIZ
sys.path.insert(0, str(PASTA_TOOLS))

from nbptbr import loctext  # noqa: E402
from nbptbr.empacotar import mod_toml, montar_portugues, verificar_pacote_portugues  # noqa: E402
from nbptbr.extrair import PASTA_TRADUCAO, carregar_traducao  # noqa: E402
from nbptbr.reinserir import reinserir_bytes  # noqa: E402

# Revisao 0.8.0 (desenvolvimento, sem Release): catalogo revisado em data/traducao.
VERSAO = "0.8.0"
SHA_ESPERADO = "d250b5959e7f0171355f9d6a3e1ac031e8c123dfb5fbfb0423beca538e20d8db"
# Referencia historica da Release v0.7.0 (nao muda): o pacote publicado e validado no jogo.
VERSAO_V070 = "0.7.0"
SHA_V070 = "7cd39a34efbae21dc8d3f919e63349e15df88397080ad59dd07207da0f5b5e25"
ARQUIVOS_ESPERADOS = 107
FRASES_ESPERADAS = 6099


def _hash(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def _gravar(destino: Path, dados: bytes) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    fd, temporario = tempfile.mkstemp(prefix=f".{destino.name}.", suffix=".tmp", dir=destino.parent)
    try:
        with os.fdopen(fd, "wb") as arquivo:
            arquivo.write(dados)
            arquivo.flush()
            os.fsync(arquivo.fileno())
        os.replace(temporario, destino)
    except BaseException:
        try:
            os.unlink(temporario)
        except FileNotFoundError:
            pass
        raise


def _parece_extraido(pasta: Path) -> bool:
    return (pasta / "Debug").is_dir() and (pasta / "loctext" / "spanish").is_dir()


def resolver_extraido(entrada: Path) -> Path:
    """Aceita a pasta do reNut, a pasta game/extraido ou qualquer pasta pai dela."""
    entrada = entrada.expanduser()
    try:
        entrada = entrada.resolve()
    except OSError:
        pass
    if not entrada.exists():
        raise SystemExit(f"A pasta nao existe: {entrada}")

    tentativas = [
        entrada,
        entrada / "game" / "extraido",
        entrada / "extraido",
        entrada.parent,
        entrada.parent.parent,
        entrada.parent / "game" / "extraido",
    ]
    for pasta in tentativas:
        if _parece_extraido(pasta):
            return pasta

    # Procura ate tres niveis abaixo (instalacoes que aninham a pasta do jogo).
    for atual, pastas, _arquivos in os.walk(entrada):
        profundidade = len(Path(atual).relative_to(entrada).parts)
        if profundidade >= 4:
            pastas[:] = []
            continue
        for nome in list(pastas):
            candidato = Path(atual) / nome
            if _parece_extraido(candidato):
                return candidato

    raise SystemExit(
        "Nao encontrei a pasta do jogo. Escolha a pasta que contem `game\\extraido` "
        "(a instalacao do reNut) ou a propria pasta `extraido`.\n"
        f"Recebi: {entrada}"
    )


def _pedir_caminho() -> Path:
    print("Onde esta a sua instalacao do reNut?")
    print("Cole o caminho da pasta que contem `game\\extraido` (ou da pasta `extraido`).")
    try:
        texto = input("Caminho: ").strip().strip('"').strip("'")
    except EOFError:
        texto = ""
    if not texto:
        raise SystemExit("Nenhum caminho informado. Rode de novo com --jogo \"C:\\...\\reNut\".")
    return Path(texto)


def gerar(extraido: Path, saida: Path) -> dict:
    nomes = sorted(arquivo.stem for arquivo in PASTA_TRADUCAO.glob("*.json"))
    if len(nomes) != ARQUIVOS_ESPERADOS:
        raise SystemExit(
            f"Os arquivos de traducao estao incompletos: {len(nomes)} de {ARQUIVOS_ESPERADOS}. "
            "Extraia o pacote de novo."
        )

    faltando_es = [nome for nome in nomes if not (extraido / "loctext" / "spanish" / nome).is_file()]
    faltando_en = [
        nome
        for nome in nomes
        if not (extraido / "Debug" / nome[0:2] / nome[2:4] / nome[4:6] / nome[6:8]).is_file()
    ]
    if faltando_es or faltando_en:
        detalhes = []
        if faltando_es:
            detalhes.append(f"{len(faltando_es)} texto(s) em espanhol")
        if faltando_en:
            detalhes.append(f"{len(faltando_en)} texto(s) em ingles")
        raise SystemExit(
            "A pasta do jogo nao parece ser a versao completa esperada: faltam "
            + " e ".join(detalhes)
            + ". Confira se o jogo terminou de extrair e se a pasta e a certa."
        )

    gerados: dict[str, bytes] = {}
    total_frases = 0
    for numero, nome in enumerate(nomes, 1):
        base = (extraido / "Debug" / nome[0:2] / nome[2:4] / nome[4:6] / nome[6:8]).read_bytes()
        espanhol = (extraido / "loctext" / "spanish" / nome).read_bytes()
        referencia = {f.chave: f.texto for f in loctext.ler(espanhol).frases()}
        novo, substituidas = reinserir_bytes(base, carregar_traducao(nome), referencia)
        gerados[nome] = novo
        total_frases += substituidas
        print(f"\rAplicando a traducao: {numero}/{len(nomes)}", end="", flush=True)
    print()

    nbpatch, _patch_json = montar_portugues(gerados, VERSAO)
    verificar_pacote_portugues(nbpatch, gerados)
    texto_mod = mod_toml(VERSAO, total_frases).encode("utf-8")

    _gravar(saida / "ptbr_traducao" / "ptbr_traducao.nbpatch", nbpatch)
    _gravar(saida / "ptbr_traducao" / "mod.toml", texto_mod)

    return {
        "arquivos": len(gerados),
        "frases": total_frases,
        "nbpatch": nbpatch,
        "sha256": _hash(nbpatch),
        "saida": saida / "ptbr_traducao",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=f"Gera o mod de traducao PT-BR {VERSAO} a partir da sua copia legitima do jogo."
    )
    parser.add_argument("--jogo", help="pasta do reNut, da pasta game\\extraido ou da pasta extraido")
    parser.add_argument("--saida", default="saida", help="pasta onde criar ptbr_traducao (padrao: saida)")
    args = parser.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    print("=" * 64)
    print(f"  Traducao PT-BR para reNut - versao {VERSAO}")
    print("=" * 64)
    print()

    entrada = Path(args.jogo) if args.jogo else _pedir_caminho()
    extraido = resolver_extraido(entrada)
    print(f"Jogo encontrado em: {extraido}")
    print()

    resultado = gerar(extraido, Path(args.saida).expanduser().resolve())

    print()
    print(f"Arquivos gerados: {resultado['arquivos']}")
    print(f"Frases traduzidas aplicadas: {resultado['frases']}")
    print(f"SHA-256 do pacote: {resultado['sha256']}")
    print(f"SHA-256 esperado:  {SHA_ESPERADO}")

    if resultado["sha256"] == SHA_ESPERADO and resultado["frases"] == FRASES_ESPERADAS:
        print()
        print(f"RESULTADO: PASS - e exatamente o pacote {VERSAO} conferido pelo projeto.")
    else:
        print()
        print(f"RESULTADO: ATENCAO - o pacote foi gerado, mas nao coincide com o build {VERSAO} conferido.")
        print("Sua copia do jogo pode ser de outra versao ou estar incompleta. Nao instale este pacote")
        print("sem conferir; relate a diferenca no GitHub se quiser ajuda.")

    print()
    print("Pasta pronta para instalar:")
    print(f"  {resultado['saida']}")
    print()
    print("Como instalar:")
    print("  1. Copie a pasta `ptbr_traducao` inteira para a pasta `mods` do reNut.")
    print("  2. No jogo, escolha o idioma English (1).")
    print("  3. Abra o menu de mods com F9, habilite a traducao e reinicie se preciso.")
    print()
    return 0 if resultado["sha256"] == SHA_ESPERADO else 2


if __name__ == "__main__":
    raise SystemExit(main())