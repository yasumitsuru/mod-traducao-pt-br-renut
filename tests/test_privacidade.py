"""Impede que dados pessoais, credenciais ou arquivos do jogo entrem no repositório público."""

import sys
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / "tools"))

import seguranca  # noqa: E402


class TestPrivacidade(unittest.TestCase):
    def test_arvore_publica_limpa(self):
        if not (RAIZ / ".git").exists():
            self.skipTest("clone Git necessário para a auditoria completa")
        problemas = seguranca.examinar(RAIZ, publico=True)
        self.assertEqual(problemas, [], "\n".join(problemas))

    def test_gitignore_de_inclusao_explicita(self):
        problemas = seguranca.validar_gitignore(RAIZ, publico=True)
        self.assertEqual([p.como_texto() for p in problemas], [])

    def test_sem_binarios_ou_arquivos_do_jogo(self):
        proibidos = (
            ".nbpatch", ".iso", ".xex", ".zip", ".xexp", ".sbp", ".exe", ".dll",
            ".patch", ".sav", ".save", ".profile",
        )
        encontrados = [
            p.relative_to(RAIZ).as_posix()
            for p in RAIZ.rglob("*")
            if p.is_file() and ".git" not in p.parts and p.name.lower().endswith(proibidos)
        ]
        self.assertEqual(encontrados, [])

    def test_politica_permanente_presente(self):
        texto = " ".join((RAIZ / "AGENTS.md").read_text(encoding="utf-8").split())
        for trecho in (
            "Política permanente de Git, segurança e sincronização com GitHub",
            "É proibido enviar o histórico Git privado",
            "force push",
            "Releases e tags de versão exigem autorização explícita",
            "v0.7.0",
        ):
            self.assertIn(" ".join(trecho.split()), texto)

    def test_launcher_publicado_sem_patch_binario(self):
        pasta = RAIZ / "launcher-patch"
        self.assertTrue((pasta / "gerar_patch.py").is_file())
        self.assertTrue((pasta / "aplicar.py").is_file())
        self.assertTrue((pasta / "entradas_launcher.json").is_file())
        self.assertFalse(list(pasta.glob("*.patch")))
        self.assertFalse(list((pasta / "engine").glob("*.patch")))

    def test_licenca_e_aviso(self):
        self.assertTrue((RAIZ / "LICENSE").is_file())
        aviso = (RAIZ / "NOTICE.md").read_text(encoding="utf-8")
        self.assertIn("Rare", aviso)
        self.assertIn("Microsoft", aviso)
        self.assertIn("reNut", aviso)


if __name__ == "__main__":
    unittest.main()