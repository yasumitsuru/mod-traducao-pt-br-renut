"""F1 — prova de ida e volta: ler -> reescrever == original (SHA-256 igual)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from . import loctext
from .config import Caminhos
from .io_seguro import RAIZ_PROJETO, gravar_atomico, gravar_json_atomico, ler_binario, sha256

PASTA_TRABALHO = RAIZ_PROJETO / "work" / "roundtrip"


@dataclass
class Resultado:
    arquivo: str
    asset: str
    frases: int
    sha_original: str
    sha_reescrito: str
    erro: str | None = None

    @property
    def ok(self) -> bool:
        return self.erro is None and self.sha_original == self.sha_reescrito


def verificar_bytes(nome: str, dados: bytes) -> tuple[Resultado, bytes | None]:
    try:
        arq = loctext.ler(dados)
        novo = loctext.escrever(arq)
        reparse = loctext.ler(novo)
        if reparse.frases() != arq.frases():
            raise ValueError("frases divergem após reler o arquivo reescrito")
        return (
            Resultado(nome, arq.nome_asset, len(arq.asset.textos), sha256(dados), sha256(novo)),
            novo,
        )
    except Exception as e:  # registra e segue para os demais arquivos
        return Resultado(nome, "?", 0, sha256(dados), "", erro=f"{type(e).__name__}: {e}"), None


def arquivos_do_idioma(cam: Caminhos, idioma: str) -> list[tuple[str, Path]]:
    if idioma == "english":
        nomes = sorted(p.name for p in cam.pasta_idioma("spanish").iterdir() if p.is_file())
        return [(n, cam.arquivo_ingles(n)) for n in nomes]
    pasta = cam.pasta_idioma(idioma)
    return sorted((p.name, p) for p in pasta.iterdir() if p.is_file())


def executar(cam: Caminhos, idioma: str, gravar_copias: bool = True) -> list[Resultado]:
    resultados = []
    for nome, origem in arquivos_do_idioma(cam, idioma):
        res, novo = verificar_bytes(nome, ler_binario(origem))
        resultados.append(res)
        if gravar_copias and novo is not None:
            gravar_atomico(PASTA_TRABALHO / idioma / nome, novo)
    if gravar_copias:
        gravar_json_atomico(
            PASTA_TRABALHO / f"relatorio_{idioma}.json",
            {
                "idioma": idioma,
                "arquivos": len(resultados),
                "identicos": sum(r.ok for r in resultados),
                "frases": sum(r.frases for r in resultados),
                "resultados": [r.__dict__ for r in resultados],
            },
        )
    return resultados
