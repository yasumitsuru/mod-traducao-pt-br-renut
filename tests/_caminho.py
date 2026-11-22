"""Coloca tools/ no sys.path (necessário com python -I, que ignora PYTHONPATH)."""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
FERRAMENTAS = RAIZ / "tools"
if str(FERRAMENTAS) not in sys.path:
    sys.path.insert(0, str(FERRAMENTAS))
TESTES = Path(__file__).resolve().parent
if str(TESTES) not in sys.path:
    sys.path.insert(0, str(TESTES))
