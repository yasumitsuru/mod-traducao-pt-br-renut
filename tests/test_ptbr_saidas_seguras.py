"""Contratos da CLI para saídas isoladas sem substituir destinos existentes."""

import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

import _caminho  # noqa: F401
import ptbr
from nbptbr.io_seguro import RAIZ_PROJETO

# As saídas de teste ficam dentro de work/; ele não é versionado e pode não existir num clone novo.
(RAIZ_PROJETO / "work").mkdir(parents=True, exist_ok=True)


class TestSaidasSeguras(unittest.TestCase):
    def _executar(self, args):
        captura = io.StringIO()
        try:
            with redirect_stdout(captura), redirect_stderr(captura):
                codigo = ptbr.main(args)
        except SystemExit as exc:
            self.fail(f"a CLI nao reconheceu o comando seguro (exit={exc.code})")
        return codigo, captura.getvalue()

    def test_empacotar_rejeita_destino_existente_sem_alterar(self):
        with tempfile.TemporaryDirectory(dir=RAIZ_PROJETO / "work") as tmp:
            destino = Path(tmp) / "pacote_existente"
            destino.mkdir()
            marcador = destino / "preservar.txt"
            marcador.write_bytes(b"nao sobrescrever")

            codigo, saida = self._executar(["empacotar", "--destino", str(destino)])

            self.assertEqual(codigo, 2)
            self.assertIn("destino ja existe", saida.lower())
            self.assertEqual(marcador.read_bytes(), b"nao sobrescrever")

    def test_jogo_isolado_rejeita_destino_existente_sem_alterar(self):
        with tempfile.TemporaryDirectory(dir=RAIZ_PROJETO / "work") as tmp:
            destino = Path(tmp) / "jogo_existente"
            destino.mkdir()
            marcador = destino / "preservar.txt"
            marcador.write_bytes(b"nao sobrescrever")

            codigo, saida = self._executar(["jogo-isolado", "--destino", str(destino)])

            self.assertEqual(codigo, 2)
            self.assertIn("destino ja existe", saida.lower())
            self.assertEqual(marcador.read_bytes(), b"nao sobrescrever")

    def test_reinserir_rejeita_relatorio_existente_sem_alterar(self):
        with tempfile.TemporaryDirectory(dir=RAIZ_PROJETO / "work") as tmp:
            relatorio = Path(tmp) / "relatorio_existente.json"
            relatorio.write_bytes(b"manter evidencias anteriores")

            codigo, saida = self._executar(["reinserir", "--relatorio", str(relatorio)])

            self.assertEqual(codigo, 2)
            self.assertIn("destino ja existe", saida.lower())
            self.assertEqual(relatorio.read_bytes(), b"manter evidencias anteriores")


if __name__ == "__main__":
    unittest.main()
