"""Leitura e escrita de alto nível de um arquivo loctext (CAFF + asset de texto)."""

from __future__ import annotations

from dataclasses import dataclass, replace

from . import caff, lsbl
from .caff import FormatoInvalido


@dataclass(frozen=True)
class Frase:
    id: str  # hash da chave em 4 dígitos hex (único por arquivo)
    chave: str
    indice: int  # posição alfabética da chave (1..n)
    texto: str


@dataclass(frozen=True)
class ArquivoLoctext:
    conteiner: caff.Caff
    asset: lsbl.AssetTexto

    @property
    def nome_asset(self) -> str:
        return self.conteiner.asset

    def frases(self) -> list[Frase]:
        """Frases ordenadas pela chave (ordem alfabética = índice da chave)."""
        chaves = self.asset.chaves()
        out = [
            Frase(id=f"{c.hash:04x}", chave=c.nome, indice=c.indice, texto=t)
            for c, t in zip(chaves, self.asset.textos, strict=True)
        ]
        return sorted(out, key=lambda f: f.indice)

    def com_textos_por_chave(self, novos: dict[str, str]) -> "ArquivoLoctext":
        """Substitui textos pelas chaves dadas; chaves desconhecidas geram erro."""
        chaves = self.asset.chaves()
        nomes = {c.nome for c in chaves}
        desconhecidas = sorted(set(novos) - nomes)
        if desconhecidas:
            raise KeyError(f"chaves inexistentes em {self.nome_asset}: {desconhecidas[:5]}")
        textos = tuple(novos.get(c.nome, t) for c, t in zip(chaves, self.asset.textos, strict=True))
        return replace(self, asset=self.asset.com_textos(textos))


def ler(dados: bytes) -> ArquivoLoctext:
    c = caff.ler(dados)
    return ArquivoLoctext(conteiner=c, asset=lsbl.ler(c.dados))


def escrever(arq: ArquivoLoctext) -> bytes:
    secao = lsbl.escrever(arq.asset)
    return caff.escrever(replace(arq.conteiner, dados=secao))


__all__ = ["ArquivoLoctext", "Frase", "FormatoInvalido", "ler", "escrever"]
