"""Nomes oficiais de fases, mundos e áreas jogáveis que NÃO podem ser traduzidos.

Regra do projeto (2026-11-21): os nomes próprios de fases, mapas, mundos e localidades usadas
como nomes oficiais de áreas jogáveis permanecem exatamente como no original inglês. O restante
da frase continua traduzido. A fonte única da verdade é `data/nomes-protegidos.csv`.
"""

import unittest

import _caminho  # noqa: F401
from nbptbr import protegidos
from nbptbr.validar import validar_frase


class TestGlossarioProtegido(unittest.TestCase):
    def test_lista_oficial(self):
        nomes = {n.nome: n for n in protegidos.carregar()}
        for esperado in (
            "Showdown Town",
            "Spiral Mountain",
            "Nutty Acres",
            "Banjoland",
            "LOGBOX 720",
            "Jiggosseum",
            "Terrarium of Terror",
            "Test-O-Track",
            "Klungo's Arcade",
        ):
            self.assertIn(esperado, nomes)
        self.assertEqual(nomes["Jiggosseum"].variantes[0], "Jiggoliseu")

    def test_detecta_variante_traduzida(self):
        for texto in (
            "Volte para a Cidade do Duelo.",
            "A Montanha Espiral espera.",
            "Visite os Bosques Malucos.",
            "Bem-vindo a Banjolândia!",
            "O SJBOX 720 é tecnológico.",
            "O Jiggoliseu recebe os jogos.",
            "O Terrário do Terror é sinistro.",
            "Jogue na Pista de Testes.",
            "O Fliperama do Klungo fica na Orla.",
        ):
            with self.subTest(texto=texto):
                self.assertTrue(protegidos.violacoes(texto), texto)

    def test_nao_marca_nome_oficial(self):
        for texto in (
            "Volte para Showdown Town.",
            "Spiral Mountain, Nutty Acres, Banjoland, LOGBOX 720, Jiggosseum e Terrarium of Terror.",
            "Test-O-Track e Klungo's Arcade.",
            "A cidade central chama-se Showdown Town.",
            "Banjoland é o nome oficial desta fase.",
        ):
            with self.subTest(texto=texto):
                self.assertEqual(protegidos.violacoes(texto), [])

    def test_nao_marca_palavra_comum_por_substring(self):
        self.assertEqual(protegidos.violacoes("A pista está livre."), [])

    def test_substitui_preservando_o_resto(self):
        casos = {
            "Volte para a Cidade do Duelo agora.": "Volte para Showdown Town agora.",
            "Placares da Montanha Espiral": "Placares de Spiral Mountain",
            "Vá aos Bosques Malucos": "Vá a Nutty Acres",
            "Estatísticas de Banjolândia": "Estatísticas de Banjoland",
            "Circuito do SJBOX 720": "Circuito do LOGBOX 720",
            "A arena do Jiggoliseu": "A arena do Jiggosseum",
            "No Terrário do Terror": "No Terrarium of Terror",
            "Jogando na Pista de Testes": "Jogando em Test-O-Track",
            "No Fliperama do Klungo": "No Klungo's Arcade",
            "BANJOLÂNDIA ATO 1": "BANJOLAND ATO 1",
            "Ele parou na loja e depois foi à Cidade do Duelo.": "Ele parou na loja e depois foi a Showdown Town.",
        }
        for entrada, esperado in casos.items():
            with self.subTest(entrada=entrada):
                self.assertEqual(protegidos.substituir(entrada), esperado)

    def test_validador_reprova_variante(self):
        regras = {(n, r) for n, r, _ in validar_frase("Return to Showdown Town.", "Volte para a Cidade do Duelo.")}
        self.assertIn(("ERRO", "nome_protegido"), regras)

    def test_validador_avisa_nome_ausente(self):
        regras = {r for n, r, _ in validar_frase("Return to Showdown Town.", "Volte para lá.") if n == "AVISO"}
        self.assertIn("nome_protegido_ausente", regras)

    def test_traducao_versionada_sem_variantes(self):
        pendencias = protegidos.auditar()
        self.assertEqual(pendencias, [], f"{len(pendencias)} frase(s) com nome traduzido")


if __name__ == "__main__":
    unittest.main()