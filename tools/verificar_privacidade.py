"""Linha de comando da verificação de privacidade e segurança.

Uso:
    python -I tools/verificar_privacidade.py
    python -I tools/verificar_privacidade.py --publico
    python -I tools/verificar_privacidade.py --staged
    python -I tools/verificar_privacidade.py --push --publico

A implementação fica em `tools/seguranca.py`; este arquivo existe para que o gancho de commit e
os testes tenham um comando estável.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import seguranca  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(seguranca.main())