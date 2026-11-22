"""Nomes oficiais de fases e mundos que não podem ser traduzidos.

A lista fica em `data/nomes-protegidos.csv` (fonte única da verdade). O validador reprova uma
tradução que troque um desses nomes por uma variante traduzida; a auditoria retroativa encontra as
frases já gravadas e o corretor restaura o nome original sem apagar o resto da tradução.
"""

from __future__ import annotations

import csv
import glob
import re
from dataclasses import dataclass

from .io_seguro import RAIZ_PROJETO

ARQ_NOMES = RAIZ_PROJETO / "data" / "nomes-protegidos.csv"

# Contrações que ficam erradas quando um nome traduzido (feminino) vira um nome próprio inglês.
# Aplicadas só quando vêm imediatamente antes do nome oficial, para não mexer no resto da frase.
_CONTRACOES = (
    (r"\bna\s+", "em "),
    (r"\bnas\s+", "em "),
    (r"\bda\s+", "de "),
    (r"\bdas\s+", "de "),
    (r"\bà\s+", "a "),
    (r"\bàs\s+", "a "),
    (r"\bpela\s+", "por "),
    (r"\bpelas\s+", "por "),
    (r"\bpara\s+(?:a|o|as|os)\s+", "para "),
    (r"\baos\s+", "a "),
)


@dataclass(frozen=True)
class NomeProtegido:
    nome: str
    tipo: str
    variantes: tuple[str, ...]
    nota: str


def carregar(caminho=ARQ_NOMES) -> list[NomeProtegido]:
    if not caminho.exists():
        return []
    with open(caminho, "r", encoding="utf-8", newline="") as f:
        return [
            NomeProtegido(
                r["nome_oficial"].strip(),
                r.get("tipo", "").strip(),
                tuple(v.strip() for v in r.get("variantes_proibidas", "").split("|") if v.strip()),
                r.get("nota", "").strip(),
            )
            for r in csv.DictReader(f)
        ]


def _limite(padrao: str) -> str:
    return rf"(?<![\w]){padrao}(?![\w])"


def _padroes(nomes: list[NomeProtegido] | None = None):
    for nome in nomes if nomes is not None else carregar():
        for variante in nome.variantes:
            yield nome, variante, re.compile(_limite(re.escape(variante)), re.IGNORECASE)


def violacoes(texto: str, nomes: list[NomeProtegido] | None = None) -> list[tuple[str, str, str]]:
    """Devolve [(nome oficial, variante encontrada, trecho)] para cada nome traduzido no texto."""
    achados: list[tuple[str, str, str]] = []
    for nome, variante, padrao in _padroes(nomes):
        for m in padrao.finditer(texto):
            achados.append((nome.nome, variante, texto[max(0, m.start() - 24) : m.end() + 24]))
    return achados


def ausentes(texto_ref: str, texto_ptbr: str, nomes: list[NomeProtegido] | None = None) -> list[str]:
    """Nomes oficiais citados no original que sumiram da tradução (sem aparecer a variante errada)."""
    faltando = []
    for nome in nomes if nomes is not None else carregar():
        if re.search(_limite(re.escape(nome.nome)), texto_ref, re.IGNORECASE) and not re.search(
            _limite(re.escape(nome.nome)), texto_ptbr, re.IGNORECASE
        ):
            faltando.append(nome.nome)
    return faltando


def _caixa(canonico: str, encontrado: str) -> str:
    letras = [c for c in encontrado if c.isalpha()]
    if letras and all(c.isupper() for c in letras):
        return canonico.upper()
    return canonico


def substituir(texto: str, nomes: list[NomeProtegido] | None = None) -> str:
    """Troca cada variante traduzida pelo nome oficial, preservando o restante da frase."""
    for nome in nomes if nomes is not None else carregar():
        for variante in nome.variantes:
            padrao = re.compile(_limite(re.escape(variante)), re.IGNORECASE)
            texto = padrao.sub(lambda m, n=nome.nome: _caixa(n, m.group(0)), texto)
        # Só ajusta a contração que encosta no próprio nome oficial.
        alvo = re.compile(rf"({re.escape(nome.nome)})", re.IGNORECASE)
        for contra, troca in _CONTRACOES:
            texto = re.sub(contra + alvo.pattern, lambda m, t=troca: t + m.group(1), texto)
    return texto


def auditar() -> list[dict]:
    """Varre data/traducao e devolve as frases com nome oficial traduzido (somente leitura)."""
    import json

    achados = []
    for caminho in sorted(glob.glob(str(RAIZ_PROJETO / "data" / "traducao" / "*.json"))):
        with open(caminho, "r", encoding="utf-8") as f:
            doc = json.load(f)
        for frase in doc.get("frases", []):
            texto = frase.get("texto_ptbr") or ""
            if not texto:
                continue
            itens = violacoes(texto)
            if itens:
                achados.append(
                    {
                        "arquivo": doc["arquivo"],
                        "id": frase["id"],
                        "chave": frase["chave"],
                        "texto": texto,
                        "violacoes": [{"nome": n, "variante": v} for n, v, _ in itens],
                    }
                )
    return achados


def lote_correcao(numero: str = "515") -> dict:
    """Monta o lote que restaura os nomes; não grava nada."""
    traducoes: dict[str, dict[str, str]] = {}
    for item in auditar():
        novo = substituir(item["texto"])
        if novo != item["texto"]:
            traducoes.setdefault(item["arquivo"], {})[item["id"]] = novo
    return {
        "lote": numero,
        "descricao": "correção retroativa: restaura nomes oficiais de fases, mundos e áreas jogáveis",
        "traducoes": traducoes,
    }