"""F3 — regras do validador e inventário da fonte."""

import unittest

import _caminho  # noqa: F401
from nbptbr import codigos
from nbptbr.fonte import ConjuntoFonte, codigos_precache, de_faixas, para_faixas
from nbptbr.validar import TermoGlossario, validar_frase

LATIN = set(range(0x20, 0x7F)) | set(range(0xA1, 0x180)) | {0x2013, 0x2014, 0x2018, 0x2019, 0x201C, 0x201D, 0x2026}
FONTE = ConjuntoFonte(precache=LATIN - {0xB7}, sbp=LATIN | {0xB7})


def regras(es, pt, **kw):
    return {(n, r) for n, r, _ in validar_frase(es, pt, FONTE, **kw)}


class TestCodigos(unittest.TestCase):
    def test_extrai_na_ordem(self):
        t = "{MOODHAPPY}Pulsa [A] <font color=[white]>ya</font> %s de %02d {PAGEBREAK}100%%"
        self.assertEqual(
            codigos.extrair(t),
            ["{MOODHAPPY}", "[A]", "<font color=[white]>", "</font>", "%s", "%02d", "{PAGEBREAK}", "%%"],
        )

    def test_porcentagem_literal_nao_e_codigo(self):
        self.assertEqual(codigos.extrair("% Completado"), [])


class TestValidarFrase(unittest.TestCase):
    def test_ok(self):
        self.assertEqual(regras("{MOODHAPPY}¡Hola, %s! Acción.", "{MOODHAPPY}Olá, %s! Ação."), set())

    def test_pendente_e_vazia(self):
        self.assertEqual(regras("Hola", ""), {("PENDENTE", "pendente")})
        self.assertEqual(regras("", ""), set())

    def test_codigo_faltando(self):
        self.assertIn(("ERRO", "codigos"), regras("{MOODSAD}Pulsa [A]", "Aperte [A]"))

    def test_codigo_sobrando(self):
        self.assertIn(("ERRO", "codigos"), regras("Pulsa [A]", "Aperte [A] ou [B]"))

    def test_ordem_printf(self):
        self.assertIn(("ERRO", "ordem_printf"), regras("%s tiene %d", "%d tem %s"))

    def test_ordem_outros_codigos_e_aviso(self):
        self.assertIn(("AVISO", "ordem_codigos"), regras("[A] o [B]", "[B] ou [A]"))

    def test_caractere_sem_glyph(self):
        self.assertIn(("ERRO", "fonte"), regras("Hola", "Olá ☃"))

    def test_caractere_fora_do_precache(self):
        self.assertIn(("AVISO", "fonte_precache"), regras("Hola", "Olá·"))

    def test_controle(self):
        self.assertIn(("ERRO", "controle"), regras("Hola", "Olá\nmundo"))

    def test_comprimento(self):
        avisos = validar_frase("Hola", "Olá, tudo bem com você?", FONTE, limiar=0.2)
        self.assertTrue(any(r == "comprimento" and m.startswith("+") for _, r, m in avisos))
        self.assertNotIn(("AVISO", "comprimento"), regras("Hola", "Olá!", limiar=0.2))

    def test_espacos_e_pontuacao_espanhola(self):
        self.assertIn(("AVISO", "espacos_pontas"), regras("Hola ", "Olá"))
        self.assertIn(("AVISO", "espaco_duplo"), regras("Hola mundo", "Olá  mundo"))
        self.assertIn(("AVISO", "pontuacao_es"), regras("¿Qué?", "¿O quê?"))

    def test_glossario(self):
        g = [TermoGlossario("Showdown Town", "Ciudad Duelo", "Cidade do Duelo", True)]
        self.assertIn(("AVISO", "glossario"), regras("Ve a Ciudad Duelo", "Vá para a cidade", glossario=g))
        self.assertNotIn(("AVISO", "glossario"), regras("Ve a Ciudad Duelo", "Vá para Cidade do Duelo", glossario=g))


class TestFonte(unittest.TestCase):
    def test_faixas_ida_e_volta(self):
        cods = {0x20, 0x21, 0x22, 0xE1, 0x2026}
        self.assertEqual(de_faixas(para_faixas(cods)), cods)

    def test_precache_utf16be(self):
        dados = b"\xfe\xff" + "aãç\r\n".encode("utf-16-be")
        self.assertEqual(codigos_precache(dados), {ord("a"), ord("ã"), ord("ç")})


if __name__ == "__main__":
    unittest.main()
