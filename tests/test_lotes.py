"""F4 — aplicação de lotes de tradução (em pasta temporária dentro de work/)."""

import json
import shutil
import unittest
from unittest import mock

import _caminho  # noqa: F401
from nbptbr import extrair, lotes
from nbptbr.io_seguro import RAIZ_PROJETO, gravar_json_atomico

TMP = RAIZ_PROJETO / "work" / "testes" / "lotes"


class TestLotes(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(TMP, ignore_errors=True)
        self.trad = TMP / "traducao"
        gravar_json_atomico(self.trad / "aaaa0001.json", {
            "arquivo": "aaaa0001", "asset": "aid_x",
            "frases": [{"id": "0001", "chave": "a", "hash_es": "h", "texto_ptbr": ""},
                       {"id": "0002", "chave": "b", "hash_es": "h", "texto_ptbr": ""}],
        })
        self.patches = [mock.patch.object(extrair, "PASTA_TRADUCAO", self.trad),
                        mock.patch.object(lotes, "PASTA_TRADUCAO", self.trad)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(TMP, ignore_errors=True)

    def lote(self, traducoes, num="009"):
        caminho = TMP / "lote.json"
        gravar_json_atomico(caminho, {"lote": num, "traducoes": traducoes})
        return caminho

    def test_aplica_e_marca_lote(self):
        r = lotes.aplicar(self.lote({"aaaa0001": {"0002": "olá"}}))
        self.assertEqual(r, {"lote": "009", "arquivos": 1, "frases": 1})
        doc = json.loads((self.trad / "aaaa0001.json").read_text(encoding="utf-8"))
        self.assertEqual(doc["frases"][1], {"id": "0002", "chave": "b", "hash_es": "h", "texto_ptbr": "olá", "lote": "009"})
        self.assertEqual(doc["frases"][0]["texto_ptbr"], "")

    def test_id_inexistente_nao_grava_nada(self):
        antes = (self.trad / "aaaa0001.json").read_bytes()
        with self.assertRaises(lotes.LoteInvalido):
            lotes.aplicar(self.lote({"aaaa0001": {"0001": "ok", "ffff": "x"}}))
        self.assertEqual((self.trad / "aaaa0001.json").read_bytes(), antes)

    def test_arquivo_inexistente(self):
        with self.assertRaises(lotes.LoteInvalido):
            lotes.aplicar(self.lote({"bbbb0002": {"0001": "x"}}))


if __name__ == "__main__":
    unittest.main()
