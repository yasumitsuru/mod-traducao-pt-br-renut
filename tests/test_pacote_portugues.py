"""F6 — pacote da pasta loctext/englishus (arquivos novos, sem tocar no jogo)."""

import io
import json
import unittest
import zipfile

import _caminho  # noqa: F401
import sintetico
from nbptbr import empacotar
from nbptbr.empacotar import PacoteInvalido, montar_portugues, verificar_pacote_portugues


class TestPacotePortugues(unittest.TestCase):
    def setUp(self):
        self.gerados = {
            "11000001": sintetico.montar_arquivo({"menu__a": "Menu principal"}),
            "11000002": sintetico.montar_arquivo({"menu__b": "Sair"}),
        }

    def test_lista_a_pasta_portuguesa_como_arquivos_novos(self):
        pacote, pj = montar_portugues(self.gerados, "0.5.0")

        self.assertEqual([f["Path"] for f in pj["Files"]], [
            "loctext/englishus/11000001",
            "loctext/englishus/11000002",
        ])
        for f in pj["Files"]:
            self.assertEqual(f["Kind"], "new")
            self.assertNotIn("SourceSha256", f)
            self.assertEqual(f["Entry"], f"files/{f['Path']}")
            self.assertEqual(f["TargetSize"], len(self.gerados[f["Path"].rsplit("/", 1)[1]]))
            self.assertEqual(len(f["TargetSha256"]), 64)

        with zipfile.ZipFile(io.BytesIO(pacote)) as z:
            self.assertEqual(z.namelist(), ["patch.json"] + [f["Entry"] for f in pj["Files"]])
            self.assertTrue(all(i.compress_type == zipfile.ZIP_STORED for i in z.infolist()))
            self.assertEqual(json.loads(z.read("patch.json")), pj)
            self.assertEqual(z.read("files/loctext/englishus/11000001"), self.gerados["11000001"])

    def test_verificacao_simula_a_aplicacao(self):
        pacote, _ = montar_portugues(self.gerados, "0.5.0")
        self.assertEqual(verificar_pacote_portugues(pacote, self.gerados), 2)

    def test_pacote_byte_estavel(self):
        pacote1, _ = montar_portugues(self.gerados, "0.5.0")
        pacote2, _ = montar_portugues(self.gerados, "0.5.0")
        self.assertEqual(pacote1, pacote2)

    def test_recusa_nome_fora_do_padrao(self):
        with self.assertRaises(PacoteInvalido):
            montar_portugues({"2244aabb": self.gerados["11000001"]}, "0.5.0")
        with self.assertRaises(PacoteInvalido):
            montar_portugues({"nao-e-hash": self.gerados["11000001"]}, "0.5.0")

    def test_recusa_entrada_alterada(self):
        pacote, _ = montar_portugues(self.gerados, "0.5.0")
        buf = io.BytesIO()
        with zipfile.ZipFile(io.BytesIO(pacote)) as origem, zipfile.ZipFile(buf, "w") as destino:
            for nome in origem.namelist():
                dados = origem.read(nome)
                if nome.endswith("11000001"):
                    dados += b"x"
                destino.writestr(nome, dados)
        with self.assertRaises(PacoteInvalido):
            verificar_pacote_portugues(buf.getvalue(), self.gerados)

    def test_recusa_pacote_incompleto(self):
        pacote, pj = montar_portugues(self.gerados, "0.5.0")
        with self.assertRaises(PacoteInvalido):
            verificar_pacote_portugues(pacote, {"11000001": self.gerados["11000001"]})

    def test_mod_toml_explica_a_pasta_portuguesa(self):
        t = empacotar.mod_toml("0.5.0", 1234)
        self.assertTrue(t.isascii())
        self.assertIn('version = "0.5.0"', t)
        self.assertIn("loctext/englishus", t)
        self.assertIn("English, 1", t)
        self.assertIn("1234 translated phrases", t)
        self.assertNotIn("English fallback", t)
        for chave in ("name", "description", "version", "author"):
            self.assertIn(f"{chave} = ", t)


if __name__ == "__main__":
    unittest.main()

