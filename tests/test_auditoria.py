"""Revisão 0.8.0 — auditoria de qualidade, propostas de revisão e comparação de pacotes.

Os testes de unidade usam frases sintéticas (sem texto do jogo). Os gates que dependem do
inventário real (`data/strings`) pulam quando ele não existe (repositório público).
"""

import io
import shutil
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

import _caminho  # noqa: F401
import sintetico
from nbptbr import auditoria, comparar, extrair, revisao
from nbptbr.empacotar import montar_portugues
from nbptbr.io_seguro import RAIZ_PROJETO, gravar_json_atomico

RAIZ = Path(__file__).resolve().parents[1]
TMP = RAIZ_PROJETO / "work" / "testes" / "auditoria"


def _tem_inventario() -> bool:
    pasta = RAIZ / "data" / "strings"
    return pasta.is_dir() and any(pasta.glob("*.json"))


class _Ctx(auditoria.Contexto):
    def __init__(self):
        super().__init__(nomes_mantidos=["Showdown Town", "Banjoland", "Xbox LIVE"], glossario=[])


def _regras(en, pt, cat="dialogo", es=None):
    return {a.regra for a in auditoria.auditar_frase(en, es, pt, cat, _Ctx())}


class TestClassificacao(unittest.TestCase):
    def test_categorias_e_mundos(self):
        self.assertEqual(auditoria.categoria("aid_loctext_banjox_ui_frontend"), "menu")
        self.assertEqual(auditoria.categoria("aid_loctext_banjox_ui_ingame_main"), "hud")
        self.assertEqual(auditoria.categoria("aid_loctext_banjox_blocks"), "pecas")
        self.assertEqual(auditoria.categoria("aid_loctext_banjox_nuttyacres_act1"), "dialogo")
        self.assertEqual(auditoria.categoria("aid_loctext_banjox_test_aerial"), "teste")
        self.assertEqual(auditoria.mundo("aid_loctext_banjox_cpu_act2"), "LOGBOX 720")
        self.assertEqual(auditoria.mundo("aid_loctext_banjox_worldofsport_act1"), "Jiggosseum")
        self.assertEqual(auditoria.mundo("aid_loctext_banjox_terrorium_actww"), "Terrarium of Terror")
        self.assertIsNone(auditoria.mundo("aid_loctext_banjox_credits"))

    def test_grupos_cobrem_os_assets_sem_sobreposicao(self):
        exemplos = ["showdowntown_log", "nuttyacres_act3", "banjoland_e3", "cpu_act1", "worldofsport_act2",
                    "terrorium_act4", "ui_frontend", "credits", "challenges", "blocks", "vehicles"]
        for a in exemplos:
            grupos = [g for g, (_, regra) in auditoria.GRUPOS.items() if regra(a)]
            self.assertEqual(len(grupos), 1, (a, grupos))
        self.assertIsNone(auditoria.grupo_do_asset("aid_loctext_banjox_tt_cpu_act1"))


class TestHeuristicas(unittest.TestCase):
    def test_identico_ao_ingles(self):
        self.assertIn("identico_en", _regras("Press start to play", "Press start to play"))
        # nomes mantidos de propósito não contam
        self.assertNotIn("identico_en", _regras("Banjoland", "Banjoland"))

    def test_trecho_em_ingles(self):
        self.assertIn("trecho_en", _regras("Go to the big red door now", "Vá até the big red door agora"))

    def test_portugues_europeu(self):
        self.assertIn("pt_europeu", _regras("You are on the screen", "Estás no ecrã"))
        self.assertIn("pt_europeu", _regras("I am doing it", "Estou a fazer isso"))
        self.assertNotIn("pt_europeu", _regras("Look at these", "Veja estas aqui"))

    def test_tratamento_misto(self):
        self.assertIn("tratamento_misto", _regras("Your car, you know", "O teu carro, você sabe"))

    def test_gramatica_frequente(self):
        self.assertIn("gramatica", _regras("Sometimes", "As vezes eu corro"))
        self.assertIn("gramatica", _regras("Give it to him", "Dê isso à ele"))
        self.assertIn("gramatica", _regras("There were problems", "Houveram problemas"))
        self.assertNotIn("gramatica", _regras("Sometimes", "Às vezes eu corro"))

    def test_palavra_repetida(self):
        self.assertIn("palavra_repetida", _regras("Go to the town", "Vá para para a cidade"))
        self.assertNotIn("palavra_repetida", _regras("Ha ha!", "Há há!"))

    def test_pontuacao(self):
        self.assertIn("pergunta_virou_afirmacao", _regras("Are you ready?", "Você está pronto."))
        self.assertIn("espaco_antes_pontuacao", _regras("Hello!", "Olá !"))
        self.assertIn("sem_espaco_depois", _regras("Hi, Banjo", "Oi,Banjo"))

    def test_numeros(self):
        self.assertIn("numeros", _regras("Collect 25 notes", "Junte 52 notas"))
        self.assertNotIn("numeros", _regras("Collect 1,000 notes", "Junte 1.000 notas"))

    def test_icone_grudado(self):
        self.assertIn("espaco_icone", _regras("Press [A] to jump", "Aperte[A] para pular"))
        self.assertNotIn("espaco_icone", _regras("Press [A] to jump", "Aperte [A] para pular"))

    def test_comprimento_de_rotulo(self):
        self.assertIn("comprimento_ui", _regras("Quit to Menu", "Sair para o menu principal agora", cat="menu"))
        self.assertNotIn("comprimento_ui", _regras("Quit to Menu", "Ir ao menu", cat="menu"))

    def test_caracteres_suspeitos(self):
        self.assertIn("caractere_suspeito", _regras("Game", "Jogo Ã© bom"))
        self.assertNotIn("caractere_suspeito", _regras("NO", "NÃO"))
        self.assertIn("codigo_quebrado", _regras("{MOODHAPPY}Hi", "{MOODHAPPY Oi"))

    def test_traducao_correta_nao_tem_achado(self):
        self.assertEqual(_regras("Return to Showdown Town!", "Volte para Showdown Town!"), set())


class TestInconsistencias(unittest.TestCase):
    def test_mesmo_original_com_traducoes_diferentes(self):
        entradas = [
            {"arquivo": "a", "id": "1", "categoria": "menu", "en": "Start", "es": None, "pt": "Iniciar"},
            {"arquivo": "b", "id": "2", "categoria": "menu", "en": "Start", "es": None, "pt": "Começar"},
            {"arquivo": "c", "id": "3", "categoria": "menu", "en": "START", "es": None, "pt": "INICIAR"},
        ]
        r = auditoria.inconsistencias_por_original(entradas)
        self.assertEqual(len(r), 1)
        self.assertEqual(r[0]["original"], "Start")
        self.assertEqual({v["pt"] for v in r[0]["variantes"]}, {"Iniciar", "Começar"})


class TestPropostas(unittest.TestCase):
    def setUp(self):
        shutil.rmtree(TMP, ignore_errors=True)
        self.strings = TMP / "strings"
        self.trad = TMP / "traducao"
        gravar_json_atomico(self.strings / "aaaa0001.json", {"arquivo": "aaaa0001", "asset": "aid_x", "frases": [
            {"id": "0001", "chave": "a", "texto_en": "{MOODHAPPY}Hello, %s!", "texto_es": "{MOODHAPPY}¡Hola, %s!"},
        ]})
        gravar_json_atomico(self.trad / "aaaa0001.json", {"arquivo": "aaaa0001", "asset": "aid_x", "frases": [
            {"id": "0001", "chave": "a", "hash_es": "h", "texto_ptbr": "{MOODHAPPY}Olá, %s!"},
        ]})
        self.patches = [mock.patch.object(extrair, "PASTA_STRINGS", self.strings),
                        mock.patch.object(extrair, "PASTA_TRADUCAO", self.trad)]
        for p in self.patches:
            p.start()

    def tearDown(self):
        for p in self.patches:
            p.stop()
        shutil.rmtree(TMP, ignore_errors=True)

    def _alt(self, **kw):
        base = {"arquivo": "aaaa0001", "id": "0001", "pt_anterior": "{MOODHAPPY}Olá, %s!",
                "pt_proposto": "{MOODHAPPY}Oi, %s!", "motivo": "m", "categoria": "dialogo", "tipo": "estilo",
                "gravidade": "LOW", "evidencia": "e"}
        base.update(kw)
        return base

    def _checar(self, *alts):
        return revisao.checar({"alteracoes": list(alts)}, fonte=None, glossario=[])

    def test_proposta_valida_passa_e_vira_lote(self):
        r = self._checar(self._alt())
        self.assertEqual(r["estado"], "PASS", r)
        lote = revisao.lote([self._alt()], "610", "teste")
        self.assertEqual(lote["traducoes"], {"aaaa0001": {"0001": "{MOODHAPPY}Oi, %s!"}})

    def test_recusa_texto_anterior_desatualizado(self):
        r = self._checar(self._alt(pt_anterior="outro texto"))
        self.assertEqual(r["estado"], "FAIL")

    def test_recusa_codigo_apagado(self):
        r = self._checar(self._alt(pt_proposto="Oi, %s!"))
        self.assertEqual(r["estado"], "FAIL")
        self.assertIn("codigos", r["problemas"][0]["problema"])

    def test_recusa_gravidade_invalida_e_repeticao(self):
        self.assertEqual(self._checar(self._alt(gravidade="URGENTE"))["estado"], "FAIL")
        self.assertEqual(self._checar(self._alt(), self._alt())["estado"], "FAIL")


class TestComparacaoDePacotes(unittest.TestCase):
    def test_mostra_so_as_frases_que_mudaram(self):
        antigo = {"11000001": sintetico.montar_arquivo({"a": "Um", "b": "Dois"}),
                  "11000002": sintetico.montar_arquivo({"c": "Três"})}
        novo = dict(antigo)
        novo["11000001"] = sintetico.montar_arquivo({"a": "Um", "b": "Duas"})
        pa, _ = montar_portugues(antigo, "0.7.0")
        pn, _ = montar_portugues(novo, "0.8.0")
        r = comparar.comparar_bytes(pa, pn)
        self.assertEqual(r["arquivos_mudaram"], 1)
        self.assertEqual(r["frases_mudaram"], 1)
        self.assertEqual(r["mudancas"]["11000001"]["chaves"], ["b"])
        esperado = {"11000001": set(r["mudancas"]["11000001"]["ids"])}
        self.assertEqual(comparar.conferir_esperado(r, esperado), [])
        self.assertTrue(comparar.conferir_esperado(r, {}))


@unittest.skipUnless(_tem_inventario(), "inventário data/strings ausente (rode: tools/ptbr.py extrair)")
class TestAuditoriaReal(unittest.TestCase):
    """Gate: a auditoria cobre as 6.110 entradas e não encontra problema de integridade nem crítico."""

    @classmethod
    def setUpClass(cls):
        with redirect_stdout(io.StringIO()):
            cls.r = auditoria.executar()

    def test_cobre_todas_as_entradas(self):
        self.assertEqual(self.r["resumo"]["entradas_auditadas"], 6110)
        self.assertEqual(self.r["resumo"]["traduzidas"], 6110)
        self.assertEqual(self.r["resumo"]["so_espanhol"], 11)

    def test_sem_problema_de_integridade(self):
        self.assertEqual(self.r["integridade"], [])

    def test_sem_achado_critico(self):
        criticos = [(e["arquivo"], e["id"], a["regra"]) for e in self.r["entradas"] for a in e["achados"]
                    if a["gravidade"] == "CRITICAL"]
        self.assertEqual(criticos, [])


if __name__ == "__main__":
    unittest.main()
