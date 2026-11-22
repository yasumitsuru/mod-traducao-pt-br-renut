"""Caminhos externos (somente leitura) lidos de config/caminhos.toml.

O arquivo real fica fora do git (contém caminhos da máquina). Modelo versionado:
config/caminhos.exemplo.toml.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path

from .io_seguro import RAIZ_PROJETO

ARQUIVO_CONFIG = RAIZ_PROJETO / "config" / "caminhos.toml"

IDIOMAS = (
    "czech", "dutch", "french", "german", "italian", "japanese", "korean",
    "norwegian", "polish", "russian", "simpchinese", "spanish", "swedish", "tradchinese",
)
IDIOMA_ALVO = "spanish"  # slot substituído pela tradução PT-BR (user_language = 5)


@dataclass(frozen=True)
class Caminhos:
    extraido: Path  # ...\game\extraido
    renut: Path | None = None

    @property
    def loctext(self) -> Path:
        return self.extraido / "loctext"

    def pasta_idioma(self, idioma: str) -> Path:
        if idioma == "english":
            raise ValueError("o inglês não tem pasta própria; use arquivo_ingles()")
        return self.loctext / idioma

    def arquivo_ingles(self, nome: str) -> Path:
        """O inglês fica em Debug\\11\\XX\\YY\\ZZ, com o mesmo nome (hash) dos arquivos de loctext."""
        if len(nome) != 8:
            raise ValueError(f"nome de arquivo loctext inesperado: {nome}")
        return self.extraido / "Debug" / nome[0:2] / nome[2:4] / nome[4:6] / nome[6:8]

    @property
    def fonte_euro(self) -> Path:
        return self.extraido / "xuifontcachefont" / "euro.sbp"

    @property
    def precache_euro(self) -> Path:
        return self.extraido / "xuifontcachemeta" / "precache_euro.ini"


def carregar(caminho: Path | None = None) -> Caminhos:
    arq = caminho or ARQUIVO_CONFIG
    if not arq.exists():
        raise FileNotFoundError(
            f"{arq} não existe. Copie config/caminhos.exemplo.toml para config/caminhos.toml e ajuste os caminhos."
        )
    with open(arq, "rb") as f:
        dados = tomllib.load(f)
    jogo = dados.get("jogo", {})
    renut = jogo.get("renut")
    return Caminhos(extraido=Path(jogo["extraido"]), renut=Path(renut) if renut else None)
