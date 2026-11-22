"""Códigos de controle encontrados nas frases do jogo.

Levantamento nas 6355 frases em espanhol (ver docs/formato-loctext.md):
  {MOODHAPPY} {MOODSAD} {MOODANGRY} {MOODDEFAULT} {PAGEBREAK}   -> marcas de humor/página
  [A] [B] [X] [Y] [LT] [RT] [LS] [RS] [LSTICK] [RSTICK] [DPAD] [BACK] [START] -> ícones de botão
  <font color=[white]> ... </font>, <br>, </br>, <ds>, </ds>, <div align="center"> ... </div> -> marcação
  %s %S %d %i %02d                                             -> valores inseridos pelo jogo
Não há caracteres de controle (< U+0020) nem quebras de linha literais nas frases.
"""

from __future__ import annotations

import re

# Ordem importa: tags HTML primeiro (consomem o "[white]" de <font color=[white]>).
CODIGO_RE = re.compile(
    r"""
      <[^<>]*>                              # <font color=[x]>, </font>, <br>, <div ...>
    | \{[A-Za-z0-9_]+\}                     # {MOODHAPPY}, {PAGEBREAK}
    | \[[A-Za-z0-9_]+\]                     # [A], [LSTICK]
    | %%                                    # porcentagem literal escapada
    | %[-+\#0]*\d*(?:\.\d+)?[sSdiuxXfc]     # %s, %02d
    """,
    re.VERBOSE,
)

PRINTF_RE = re.compile(r"^%[-+\#0]*\d*(?:\.\d+)?[sSdiuxXfc]$")


def extrair(texto: str) -> list[str]:
    """Lista os códigos na ordem em que aparecem."""
    return [m.group(0) for m in CODIGO_RE.finditer(texto)]


def eh_printf(codigo: str) -> bool:
    return bool(PRINTF_RE.match(codigo))


def sem_codigos(texto: str) -> str:
    """Texto visível (sem códigos), usado para medir comprimento e checar caracteres."""
    return CODIGO_RE.sub("", texto)
