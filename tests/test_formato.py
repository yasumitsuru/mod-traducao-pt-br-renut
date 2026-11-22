"""F1/F5 — leitura, escrita e reinserção em arquivos loctext sintéticos."""

import struct
import unittest

import _caminho  # noqa: F401
import sintetico
from nbptbr import caff, loctext, lsbl
from nbptbr.caff import FormatoInvalido

TEXTOS = {
    "dialog__intro": "{MOODHAPPY}¡Hola, Banjo! ¿Listo?",
    "dialog__outro": "Pulsa [A] para continuar.{PAGEBREAK}Adiós",
    "menu__vacia": "",
    "ui__valor": "%s / %d",
}


class TestIdaEVolta(unittest.TestCase):
    def assert_identico(self, dados: bytes) -> loctext.ArquivoLoctext:
        arq = loctext.ler(dados)
        self.assertEqual(loctext.escrever(arq), dados)
        return arq

    def test_basico(self):
        arq = self.assert_identico(sintetico.montar_arquivo(TEXTOS))
        frases = arq.frases()
        self.assertEqual([f.chave for f in frases], sorted(TEXTOS))
        self.assertEqual({f.chave: f.texto for f in frases}, TEXTOS)
        self.assertEqual(arq.nome_asset, "aid_loctext_banjox_teste")
        self.assertEqual(arq.conteiner.checksum, 0x0BADF00D)

    def test_sem_indice_uma_chave(self):
        self.assert_identico(sintetico.montar_arquivo({"so__uma": "x"}, com_indice=False))

    def test_tamanhos_de_nome_que_exigem_preenchimento(self):
        # varia o tamanho do nome do símbolo para cobrir os 4 restos de alinhamento
        for extra in range(4):
            dados = sintetico.montar_arquivo(TEXTOS, nome_asset="aid_loctext_banjox_t" + "x" * extra)
            self.assert_identico(dados)

    def test_bloco_de_colisoes_e_lsbl_em_endereco_impar(self):
        textos = dict(TEXTOS, dialog__fim1="fim")  # nome com 12 letras -> 13 bytes com \0
        col = [("dialog__fim1", 0xE09B, 0)]
        hashes = {"dialog__fim1": 0x0000, "dialog__intro": 0x4000, "dialog__outro": 0x5000,
                  "menu__vacia": 0x9000, "ui__valor": 0xA000}
        dados = sintetico.montar_arquivo(textos, colisoes=col, hashes=hashes)
        arq = self.assert_identico(dados)
        self.assertEqual(arq.asset.colisoes(), [lsbl.Colisao("dialog__fim1", 0xE09B, 0)])
        desl_lsbl = struct.unpack_from(">I", arq.conteiner.dados, 0)[0]
        self.assertEqual(desl_lsbl, 12 + 8 + 13)
        self.assertEqual(desl_lsbl % 2, 1)  # o LSBL começa em endereço ímpar, como em 1169b65d

    def test_tabela_de_comentarios_preservada(self):
        coment = struct.pack("<2I", 8 + 8 + 4, 1) + struct.pack("<II", 0x00123400, 0) + b"; x\x00"
        arq = self.assert_identico(sintetico.montar_arquivo(TEXTOS, comentarios=coment))
        self.assertEqual(arq.asset.tabela_comentarios, coment)


class TestReinsercao(unittest.TestCase):
    def test_substituir_textos_recalcula_tudo(self):
        original = sintetico.montar_arquivo(TEXTOS, comentarios=struct.pack("<2I", 8, 0))
        arq = loctext.ler(original)
        novos = {
            "dialog__intro": "{MOODHAPPY}Olá, Banjo! Pronto? Ação, emoção e coração!",
            "ui__valor": "%s de %d",
        }
        novo = loctext.escrever(arq.com_textos_por_chave(novos))
        self.assertNotEqual(novo, original)
        relido = loctext.ler(novo)
        esperado = dict(TEXTOS, **novos)
        self.assertEqual({f.chave: f.texto for f in relido.frases()}, esperado)
        # cabeçalho fixo (com checksum) intacto; tabelas cruas intactas
        self.assertEqual(relido.conteiner.cabecalho, arq.conteiner.cabecalho)
        self.assertEqual(relido.asset.tabela_chaves, arq.asset.tabela_chaves)
        self.assertEqual(relido.asset.tabela_comentarios, arq.asset.tabela_comentarios)
        self.assertEqual(relido.asset.tabela_indice, arq.asset.tabela_indice)
        self.assertEqual(len(relido.conteiner.dados) % 16, 0)
        # escrever de novo o relido é estável
        self.assertEqual(loctext.escrever(relido), novo)

    def test_texto_mais_curto(self):
        arq = loctext.ler(sintetico.montar_arquivo(TEXTOS))
        novo = loctext.escrever(arq.com_textos_por_chave({k: "" for k in TEXTOS}))
        self.assertEqual({f.texto for f in loctext.ler(novo).frases()}, {""})

    def test_chave_desconhecida(self):
        arq = loctext.ler(sintetico.montar_arquivo(TEXTOS))
        with self.assertRaises(KeyError):
            arq.com_textos_por_chave({"nao__existe": "x"})

    def test_nulo_proibido(self):
        arq = loctext.ler(sintetico.montar_arquivo(TEXTOS))
        with self.assertRaises(FormatoInvalido):
            arq.com_textos_por_chave({"ui__valor": "a\x00b"})


class TestEntradasInvalidas(unittest.TestCase):
    def setUp(self):
        self.dados = sintetico.montar_arquivo(TEXTOS)

    def alterar(self, pos: int, novo: bytes) -> bytes:
        return self.dados[:pos] + novo + self.dados[pos + len(novo):]

    def test_assinatura(self):
        with self.assertRaises(FormatoInvalido):
            loctext.ler(self.alterar(0, b"XAFF"))

    def test_arquivo_truncado(self):
        with self.assertRaises(FormatoInvalido):
            loctext.ler(self.dados[:-16])

    def test_lsbl_ausente(self):
        arq = loctext.ler(self.dados)
        pos = 0x78 + arq.conteiner.tam_info + 12
        with self.assertRaises(FormatoInvalido):
            loctext.ler(self.alterar(pos, b"XSBL"))

    def test_info_que_mudaria_de_tamanho(self):
        c = caff.ler(self.dados)
        from dataclasses import replace

        with self.assertRaises(FormatoInvalido):
            caff.escrever(replace(c, nome_simbolo=c.nome_simbolo + b"_mais_longo_que_o_original"))


if __name__ == "__main__":
    unittest.main()
