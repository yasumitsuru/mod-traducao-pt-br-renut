"""Testes contra os arquivos reais do jogo (pulados se config/caminhos.toml ou o jogo não existirem).

Os arquivos do jogo são lidos somente em modo "rb" e nada é gravado (nem em work/).
"""

import unittest

import _caminho  # noqa: F401
from nbptbr import config, loctext, roundtrip
from nbptbr.io_seguro import ler_binario


def _caminhos():
    try:
        cam = config.carregar()
    except FileNotFoundError:
        return None
    return cam if cam.pasta_idioma("spanish").is_dir() else None


CAM = _caminhos()


@unittest.skipIf(CAM is None, "jogo extraído não encontrado (config/caminhos.toml)")
class TestJogoReal(unittest.TestCase):
    def test_roundtrip_espanhol_107_arquivos(self):
        res = roundtrip.executar(CAM, "spanish", gravar_copias=False)
        self.assertEqual(len(res), 107)
        falhas = [(r.arquivo, r.erro) for r in res if not r.ok]
        self.assertEqual(falhas, [])
        self.assertEqual(sum(r.frases for r in res), 6355)

    def test_reinsercao_de_todas_as_frases_relê_igual(self):
        # F5: troca todas as frases por versões maiores, com acentos do PT-BR, e relê.
        for nome, origem in roundtrip.arquivos_do_idioma(CAM, "spanish"):
            with self.subTest(arquivo=nome):
                arq = loctext.ler(ler_binario(origem))
                novos = {f.chave: f.texto + " — ação ÇÃÕ" for f in arq.frases()}
                saida = loctext.escrever(arq.com_textos_por_chave(novos))
                relido = loctext.ler(saida)
                self.assertEqual({f.chave: f.texto for f in relido.frases()}, novos)
                self.assertEqual(relido.conteiner.cabecalho, arq.conteiner.cabecalho)

    def test_chaves_do_ingles_iguais_ao_espanhol_exceto_creditos(self):
        diferentes = []
        for nome, origem in roundtrip.arquivos_do_idioma(CAM, "spanish"):
            es = {f.chave for f in loctext.ler(ler_binario(origem)).frases()}
            en = {f.chave for f in loctext.ler(ler_binario(CAM.arquivo_ingles(nome))).frases()}
            if es != en:
                diferentes.append(nome)
                self.assertTrue(es <= en or nome == "11606e97")
        self.assertEqual(diferentes, ["11606e97"])  # créditos: 479 chaves (es) x 540 (en)


if __name__ == "__main__":
    unittest.main()
