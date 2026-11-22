"""Impede que dados pessoais, credenciais ou arquivos do jogo entrem no repositório."""

import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "tools"))

import verificar_privacidade  # noqa: E402


class TestPrivacidade(unittest.TestCase):
    def test_arquivos_rastreados_sem_dados_sensiveis(self):
        problemas = verificar_privacidade.examinar(RAIZ)
        self.assertEqual(problemas, [], "\n".join(problemas))

    def test_readme_tem_titulo_e_creditos(self):
        texto = (RAIZ / "README.md").read_text(encoding="utf-8")
        self.assertIn("# MOD tradução PT-BR para o RENUT", texto)
        self.assertIn("masterspike52/reNut", texto)
        self.assertIn("yasumitsuru", texto)
        self.assertIn("English (1)", texto)

    def test_sem_arquivos_do_jogo_ou_pacotes(self):
        proibidos = (".nbpatch", ".iso", ".xex", ".zip", ".xexp", ".sbp")
        encontrados = [
            p.relative_to(RAIZ).as_posix()
            for p in RAIZ.rglob("*")
            if p.is_file() and ".git" not in p.parts and p.name.lower().endswith(proibidos)
        ]
        self.assertEqual(encontrados, [])


if __name__ == "__main__":
    unittest.main()
