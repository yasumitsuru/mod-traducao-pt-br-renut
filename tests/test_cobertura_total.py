"""Gate de cobertura da F4: 100% das frases traduzíveis com texto revisado.

Este teste é o critério de saída da missão de 100%: qualquer frase com original não vazio e sem
`texto_ptbr` volta a reprovar. Ele usa o inventário real (`data/strings`) e o validador do projeto,
sem alterar denominadores.
"""

import io
import unittest
from contextlib import redirect_stdout
from pathlib import Path

import _caminho  # noqa: F401
from nbptbr import protegidos, validar
from nbptbr.extrair import carregar_strings, carregar_traducao, nomes_traducao

RAIZ = Path(__file__).resolve().parents[1]


def _tem_inventario() -> bool:
    """O inventário do jogo é regenerável e não é versionado; sem ele, os gates de cobertura pulam."""
    pasta = RAIZ / "data" / "strings"
    return pasta.is_dir() and any(pasta.glob("*.json"))


class TestCoberturaTotal(unittest.TestCase):
    @unittest.skipUnless(_tem_inventario(), "inventário data/strings ausente (rode: tools/ptbr.py extrair)")
    def test_todas_as_frases_traduziveis_estao_traduzidas(self):
        with redirect_stdout(io.StringIO()):
            rel = validar.executar(so_traduzidas=False)

        self.assertEqual(rel["estado"], "PASS", rel["itens"][:5])
        self.assertEqual(rel["frases"], 6427)
        self.assertEqual(rel["vazias_no_original"], 317)
        self.assertEqual(rel["pendentes"], 0, "ainda há frases traduzíveis sem tradução")
        self.assertEqual(rel["traduzidas"], 6110)
        self.assertEqual(rel["erros"], 0)

    def test_nomes_protegidos_sem_variantes_traduzidas(self):
        self.assertEqual(protegidos.auditar(), [])

    @unittest.skipUnless(_tem_inventario(), "inventário data/strings ausente (rode: tools/ptbr.py extrair)")
    def test_creditos_exclusivos_do_espanhol_continuam_separados(self):
        so_es = []
        for nome in nomes_traducao():
            for f in carregar_strings(nome)["frases"]:
                if f.get("texto_es") and f.get("texto_en") is None:
                    so_es.append((nome, f["id"]))
        self.assertEqual(len(so_es), 11)
        self.assertEqual({nome for nome, _ in so_es}, {"11606e97"})

        # As 11 chaves não entram no arquivo inglês (a F5 as ignora por chave), mas estão traduzidas
        # no catálogo. Nenhuma entrada inglesa pode ser fabricada para "aumentar" a cobertura.
        trad = {f["id"]: f for f in carregar_traducao("11606e97")["frases"]}
        for _, fid in so_es:
            self.assertTrue(trad[fid].get("texto_ptbr"), f"crédito só em espanhol sem tradução: {fid}")


if __name__ == "__main__":
    unittest.main()