"""F2 — extração com um "jogo" sintético em work/testes (nunca toca no jogo real)."""

import json
import shutil
import unittest
from unittest import mock

import _caminho  # noqa: F401
import sintetico
from nbptbr import extrair
from nbptbr.config import Caminhos
from nbptbr.io_seguro import RAIZ_PROJETO, gravar_atomico, gravar_json_atomico

TMP = RAIZ_PROJETO / "work" / "testes" / "extrair"
NOME = "11aabbcc"


class TestExtrair(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(TMP, ignore_errors=True)
        jogo = TMP / "extraido"
        self.es = {"dialog__a": "{MOODHAPPY}¡Hola!", "dialog__b": "Pulsa [A]", "dialog__c": ""}
        self.en = {"dialog__a": "{MOODHAPPY}Hello!", "dialog__b": "Press [A]", "dialog__c": ""}
        gravar_atomico(jogo / "loctext" / "spanish" / NOME, sintetico.montar_arquivo(self.es))
        gravar_atomico(jogo / "Debug" / "11" / "aa" / "bb" / "cc", sintetico.montar_arquivo(self.en))
        self.cam = Caminhos(extraido=jogo)
        self.patches = [
            mock.patch.object(extrair, "PASTA_STRINGS", TMP / "strings"),
            mock.patch.object(extrair, "PASTA_TRADUCAO", TMP / "traducao"),
            mock.patch.object(extrair, "ARQ_INDICE", TMP / "indice.json"),
        ]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(TMP, ignore_errors=True)

    def ler(self, pasta):
        return json.loads((TMP / pasta / f"{NOME}.json").read_text(encoding="utf-8"))

    def test_extracao_completa_e_versionavel(self):
        r = extrair.executar(self.cam)
        self.assertEqual((r["arquivos"], r["frases"], r["vazias"], r["com_ingles"]), (1, 3, 1, 3))
        s = self.ler("strings")
        a = next(f for f in s["frases"] if f["chave"] == "dialog__a")
        self.assertEqual((a["texto_es"], a["texto_en"], a["texto_ptbr"]), ("{MOODHAPPY}¡Hola!", "{MOODHAPPY}Hello!", ""))
        self.assertEqual(a["codigos"], ["{MOODHAPPY}"])
        t = self.ler("traducao")
        self.assertEqual(set(t["frases"][0]), {"id", "chave", "hash_es", "texto_ptbr"})
        texto_versionado = json.dumps(t, ensure_ascii=False)
        self.assertNotIn("Hola", texto_versionado)
        self.assertNotIn("Pulsa", texto_versionado)

    def test_reextrair_preserva_traducao_e_lote(self):
        extrair.executar(self.cam)
        t = self.ler("traducao")
        for f in t["frases"]:
            if f["chave"] == "dialog__b":
                f["texto_ptbr"], f["lote"] = "Aperte [A]", "007"
        gravar_json_atomico(TMP / "traducao" / f"{NOME}.json", t)
        r = extrair.executar(self.cam)
        self.assertEqual(r["traduzidas"], 1)
        b = next(f for f in self.ler("traducao")["frases"] if f["chave"] == "dialog__b")
        self.assertEqual((b["texto_ptbr"], b["lote"]), ("Aperte [A]", "007"))
        self.assertNotIn("origem_mudou", b)
        s = next(f for f in self.ler("strings")["frases"] if f["chave"] == "dialog__b")
        self.assertEqual(s["texto_ptbr"], "Aperte [A]")

    def test_original_mudou_e_marcado(self):
        extrair.executar(self.cam)
        t = self.ler("traducao")
        for f in t["frases"]:
            if f["chave"] == "dialog__b":
                f["texto_ptbr"] = "Aperte [A]"
                hash_antigo = f["hash_es"]
        gravar_json_atomico(TMP / "traducao" / f"{NOME}.json", t)
        novo_es = dict(self.es, dialog__b="Pulsa [B]")
        gravar_atomico(TMP / "extraido" / "loctext" / "spanish" / NOME, sintetico.montar_arquivo(novo_es))
        extrair.executar(self.cam)
        b = next(f for f in self.ler("traducao")["frases"] if f["chave"] == "dialog__b")
        self.assertTrue(b["origem_mudou"])
        self.assertEqual(b["hash_es"], hash_antigo)


if __name__ == "__main__":
    unittest.main()
