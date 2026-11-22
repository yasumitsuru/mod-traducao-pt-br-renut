"""Testes do gerador local que reproduz o pacote 0.7.0 a partir do jogo do usuário."""

from __future__ import annotations

import tempfile
import unittest
import zipfile
from pathlib import Path

import _caminho  # noqa: F401
import gerar_mod

RAIZ = Path(__file__).resolve().parents[1]


class TestResolucao(unittest.TestCase):
    def test_aceita_a_raiz_do_reNut(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            (raiz / "game" / "extraido" / "Debug").mkdir(parents=True)
            (raiz / "game" / "extraido" / "loctext" / "spanish").mkdir(parents=True)
            self.assertEqual(gerar_mod.resolver_extraido(raiz), raiz / "game" / "extraido")

    def test_aceita_a_pasta_debug_11(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            (raiz / "Debug" / "11").mkdir(parents=True)
            (raiz / "loctext" / "spanish").mkdir(parents=True)
            self.assertEqual(gerar_mod.resolver_extraido(raiz / "Debug" / "11"), raiz)

    def test_recusa_pasta_sem_jogo(self):
        with tempfile.TemporaryDirectory() as pasta:
            with self.assertRaises(SystemExit):
                gerar_mod.resolver_extraido(Path(pasta))


class TestGeracaoReal(unittest.TestCase):
    def test_reproduz_o_sha_do_pacote_validado(self):
        try:
            from nbptbr import config

            cam = config.carregar()
        except (FileNotFoundError, KeyError, ValueError):
            self.skipTest("config/caminhos.toml ausente nesta cópia")
        if not (cam.extraido / "Debug" / "11").is_dir():
            self.skipTest("jogo não está disponível nesta máquina")

        with tempfile.TemporaryDirectory() as pasta:
            codigo = gerar_mod.main(
                ["--jogo", str(cam.extraido / "Debug" / "11"), "--saida", pasta]
            )
            self.assertEqual(codigo, 0)
            patch = Path(pasta) / "ptbr_traducao" / "ptbr_traducao.nbpatch"
            self.assertTrue(patch.is_file())
            self.assertEqual(gerar_mod._hash(patch.read_bytes()), gerar_mod.SHA_ESPERADO)
            mod = (Path(pasta) / "ptbr_traducao" / "mod.toml").read_text("utf-8")
            self.assertIn('version = "0.7.0"', mod)


class TestPacoteGerador(unittest.TestCase):
    def test_zip_nao_contem_jogo_nem_binario(self):
        caminho = RAIZ / "dist" / "release" / f"reNut-Traducao-PTBR-v{gerar_mod.VERSAO}-gerador.zip"
        if not caminho.is_file():
            self.skipTest("pacote do gerador ainda não foi montado")
        with zipfile.ZipFile(caminho) as pacote:
            nomes = pacote.namelist()
            self.assertIn("gerar_mod.py", nomes)
            self.assertIn("LEIA-ME.md", nomes)
            self.assertEqual(len([n for n in nomes if n.startswith("data/traducao/")]), 107)
            for proibido in (".nbpatch", ".zip", ".iso", ".xex", ".sbp"):
                self.assertFalse([n for n in nomes if n.endswith(proibido)], proibido)


if __name__ == "__main__":
    unittest.main()