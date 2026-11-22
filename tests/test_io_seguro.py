"""Escrita restrita à raiz do projeto e atômica."""

import tempfile
import unittest
from pathlib import Path

import _caminho  # noqa: F401
from nbptbr import io_seguro


class TestIoSeguro(unittest.TestCase):
    def test_recusa_fora_da_raiz(self):
        fora = Path(tempfile.gettempdir()) / "nbptbr_nao_deve_existir.bin"
        with self.assertRaises(io_seguro.EscritaForaDaRaiz):
            io_seguro.gravar_atomico(fora, b"x")
        self.assertFalse(fora.exists())

    def test_recusa_escapar_com_ponto_ponto(self):
        with self.assertRaises(io_seguro.EscritaForaDaRaiz):
            io_seguro.caminho_gravavel("work/../../fora.txt")

    def test_grava_dentro_da_raiz_com_lf(self):
        destino = io_seguro.RAIZ_PROJETO / "work" / "testes" / "io.txt"
        io_seguro.gravar_texto_atomico(destino, "a\r\nb\n")
        try:
            self.assertEqual(destino.read_bytes(), b"a\nb\n")
            restos = [p for p in destino.parent.iterdir() if p.name.endswith(".tmp")]
            self.assertEqual(restos, [])
        finally:
            destino.unlink()

    def test_json_estavel(self):
        self.assertEqual(io_seguro.json_estavel({"t": "ação"}), '{\n  "t": "ação"\n}\n')


if __name__ == "__main__":
    unittest.main()
