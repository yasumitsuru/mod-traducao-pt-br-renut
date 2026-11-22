"""Gate público de cobertura: toda entrada com texto original tem tradução.

Não depende do jogo extraído: o hash do texto original vazio (SHA-256 de string vazia) identifica
as entradas sem conteúdo, então o catálogo sozinho prova a cobertura.
"""

import json
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
PASTA = RAIZ / "data" / "traducao"
HASH_VAZIO = "e3b0c44298fc1c14"


class TestCoberturaPublica(unittest.TestCase):
    def test_catalogo_inteiro_traduzido(self):
        arquivos = sorted(PASTA.glob("*.json"))
        self.assertEqual(len(arquivos), 107)

        total = vazias = traduzidas = sem_traducao = 0
        faltando = []
        for arquivo in arquivos:
            dados = json.loads(arquivo.read_text(encoding="utf-8"))
            for frase in dados["frases"]:
                total += 1
                if str(frase.get("hash_es", "")).startswith(HASH_VAZIO):
                    vazias += 1
                    continue
                if frase.get("texto_ptbr"):
                    traduzidas += 1
                else:
                    sem_traducao += 1
                    faltando.append(f"{arquivo.stem}:{frase['id']}")

        self.assertEqual(total, 6427)
        self.assertEqual(vazias, 317)
        self.assertEqual(sem_traducao, 0, f"entradas sem tradução: {faltando[:5]}")
        self.assertEqual(traduzidas, 6110)


if __name__ == "__main__":
    unittest.main()
