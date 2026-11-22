"""F5 — reinserção a partir do JSON de tradução."""

import unittest

import _caminho  # noqa: F401
import sintetico
from nbptbr import loctext
from nbptbr.extrair import hash_texto
from nbptbr.reinserir import ReinsercaoRecusada, reinserir_bytes

TEXTOS = {"dialog__a": "{MOODHAPPY}¡Hola!", "dialog__b": "Pulsa [A]", "dialog__c": ""}


def traducao_de(dados: bytes, ptbr: dict[str, str]) -> dict:
    arq = loctext.ler(dados)
    return {
        "arquivo": "teste",
        "frases": [
            {"id": f.id, "chave": f.chave, "hash_es": hash_texto(f.texto), "texto_ptbr": ptbr.get(f.chave, "")}
            for f in arq.frases()
        ],
    }


class TestReinserir(unittest.TestCase):
    def test_sem_traducao_e_identico(self):
        dados = sintetico.montar_arquivo(TEXTOS)
        saida, n = reinserir_bytes(dados, traducao_de(dados, {}))
        self.assertEqual((saida, n), (dados, 0))

    def test_aplica_traducao(self):
        dados = sintetico.montar_arquivo(TEXTOS)
        saida, n = reinserir_bytes(dados, traducao_de(dados, {"dialog__a": "{MOODHAPPY}Olá, ação!"}))
        self.assertEqual(n, 1)
        frases = {f.chave: f.texto for f in loctext.ler(saida).frases()}
        self.assertEqual(frases, dict(TEXTOS, dialog__a="{MOODHAPPY}Olá, ação!"))

    def test_recusa_original_alterado(self):
        dados = sintetico.montar_arquivo(TEXTOS)
        trad = traducao_de(dados, {"dialog__b": "Aperte [A]"})
        trad["frases"][1]["hash_es"] = "0" * 16
        with self.assertRaises(ReinsercaoRecusada):
            reinserir_bytes(dados, trad)

    def test_aceita_quando_o_espanhol_nao_existe(self):
        # Créditos: 11 chaves não têm texto em espanhol; a base inglesa é a única referência.
        dados = sintetico.montar_arquivo(TEXTOS)
        trad = traducao_de(dados, {"dialog__a": "{MOODHAPPY}Olá!"})
        trad["frases"][0]["hash_es"] = None
        saida, n = reinserir_bytes(dados, trad, textos_es={})
        self.assertEqual(n, 1)
        self.assertEqual({f.chave: f.texto for f in loctext.ler(saida).frases()}["dialog__a"], "{MOODHAPPY}Olá!")


if __name__ == "__main__":
    unittest.main()
