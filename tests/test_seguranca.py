"""Testes unitários das regras de privacidade, sem tocar no repositório real."""

import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "tools"))

import seguranca  # noqa: E402


class TestPadroes(unittest.TestCase):
    def test_reconhece_caminho_pessoal(self):
        texto = "C:" + "\\Users\\" + "alguem" + "\\OneDrive\\jogo"
        achados = seguranca.examinar_texto(texto, "teste")
        self.assertTrue(any(a.categoria == "caminho_pessoal" for a in achados))
        self.assertTrue(all("alguem" not in a.trecho for a in achados))

    def test_exemplo_documental_nao_e_pessoal(self):
        texto = "C:" + "\\jogos\\" + "BanjoKazooieNutsAndBolts-reNut\\game\\extraido"
        achados = seguranca.examinar_texto(texto, "teste")
        self.assertFalse([a for a in achados if a.severidade == "alto"])

    def test_reconhece_token_e_email(self):
        token = "ghp_" + ("a" * 30)
        email = "pessoa" + "@" + "teste.invalid"
        achados = seguranca.examinar_texto(f"token {token} e email {email}", "teste")
        categorias = {a.categoria for a in achados}
        self.assertIn("token_github", categorias)
        self.assertIn("email", categorias)

    def test_reconhece_chave_privada(self):
        texto = "-----BEGIN " + "PRIVATE KEY-----"
        achados = seguranca.examinar_texto(texto, "teste")
        self.assertTrue(any(a.categoria == "chave_privada" for a in achados))

    def test_reconhece_ip_privado(self):
        ip = ".".join(("192", "168", "1", "10"))
        achados = seguranca.examinar_texto(f"servidor em {ip}", "teste")
        self.assertTrue(any(a.categoria == "ip_privado" for a in achados))

    def test_email_noreply_e_aceito(self):
        achados = seguranca.examinar_texto(
            "autor: yasumitsuru@users.noreply.github.com", "teste"
        )
        self.assertFalse([a for a in achados if a.severidade == "alto"])


class TestArquivos(unittest.TestCase):
    def test_binario_e_recusado(self):
        achados = seguranca.examinar_bytes(b"\x00\x01\x02", "teste.bin")
        self.assertTrue(any(a.categoria == "arquivo_binario" for a in achados))

    def test_publico_recusa_app_e_binarios(self):
        self.assertIsNotNone(seguranca._nome_proibido("app/src/main.rs", publico=True))
        self.assertIsNotNone(seguranca._nome_proibido("renut.exe", publico=True))
        self.assertIsNotNone(seguranca._nome_proibido("launcher-patch/x.patch", publico=True))
        self.assertIsNone(seguranca._nome_proibido("README.md", publico=True))
        self.assertIsNone(seguranca._nome_proibido("launcher-patch/aplicar.py", publico=True))

    def test_local_permite_patch_do_launcher(self):
        self.assertIsNone(
            seguranca._nome_proibido("launcher-patch/renut_launcher_ptbr.patch", publico=False)
        )
        self.assertIsNotNone(seguranca._nome_proibido("renut.exe", publico=False))


if __name__ == "__main__":
    unittest.main()