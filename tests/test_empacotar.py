"""F6 — delta NBDL e montagem do .nbpatch (sintético)."""

import io
import json
import struct
import unittest
import zipfile

import _caminho  # noqa: F401
import sintetico
from nbptbr import empacotar, loctext
from nbptbr.empacotar import PacoteInvalido, aplicar_delta, delta_literal, montar, varint, verificar_pacote


class TestNbdl(unittest.TestCase):
    def test_varint_leb128(self):
        self.assertEqual(varint(0), b"\x00")
        self.assertEqual(varint(127), b"\x7f")
        self.assertEqual(varint(128), b"\x80\x01")
        self.assertEqual(varint(300), b"\xac\x02")

    def test_literal_ida_e_volta(self):
        alvo = bytes(range(256)) * 5
        d = delta_literal(alvo)
        self.assertEqual(d[:4], b"NBDL")
        self.assertEqual(struct.unpack_from("<Q", d, 8)[0], len(alvo))
        self.assertEqual(aplicar_delta(b"origem qualquer", d), alvo)

    def test_operacao_copia(self):
        d = b"NBDL" + struct.pack("<IQ", 1, 7) + b"\x01" + varint(2) + varint(3) + b"\x02" + varint(4) + b"WXYZ"
        self.assertEqual(aplicar_delta(b"abcdef", d), b"cdeWXYZ")

    def test_erros(self):
        with self.assertRaises(PacoteInvalido):
            aplicar_delta(b"", b"XXXX" + bytes(12))
        curto = b"NBDL" + struct.pack("<IQ", 1, 10) + b"\x02" + varint(2) + b"ab"
        with self.assertRaises(PacoteInvalido):
            aplicar_delta(b"", curto)
        with self.assertRaises(PacoteInvalido):
            aplicar_delta(b"", b"NBDL" + struct.pack("<IQ", 1, 1) + b"\x07")


class TestPacote(unittest.TestCase):
    def setUp(self):
        textos = {"menu__a": "Menú", "menu__b": "Salir"}
        self.orig = sintetico.montar_arquivo(textos)
        arq = loctext.ler(self.orig)
        self.novo = loctext.escrever(arq.com_textos_por_chave({"menu__a": "Menu", "menu__b": "Sair"}))
        self.igual = sintetico.montar_arquivo({"x__y": "z"}, nome_asset="aid_loctext_banjox_outro")

    def montar(self):
        originais = {"loctext/spanish/11000001": self.orig, "loctext/spanish/11000002": self.igual}
        gerados = {"loctext/spanish/11000001": self.novo, "loctext/spanish/11000002": self.igual}
        return originais, montar(originais, gerados, "0.0.1")

    def test_so_arquivos_alterados_e_campos(self):
        originais, (pacote, pj) = self.montar()
        self.assertEqual(len(pj["Files"]), 1)
        f = pj["Files"][0]
        self.assertEqual(f["Path"], "loctext/spanish/11000001")
        self.assertEqual(f["Kind"], "delta")
        self.assertEqual(f["Entry"], "files/loctext/spanish/11000001.nbdl")
        self.assertEqual(len(f["SourceSha256"]), 64)
        self.assertEqual(f["TargetSize"], len(self.novo))
        with zipfile.ZipFile(io.BytesIO(pacote)) as z:
            self.assertEqual(z.namelist(), ["patch.json", "files/loctext/spanish/11000001.nbdl"])
            self.assertTrue(all(i.compress_type == zipfile.ZIP_STORED for i in z.infolist()))
            self.assertEqual(json.loads(z.read("patch.json")), pj)
        self.assertEqual(pacote[:4], b"PK\x03\x04")
        self.assertEqual(verificar_pacote(pacote, originais), 1)

    def test_entries_uses_full_path_when_leaf_names_repeat(self):
        path_a = "Debug/11/26/58/e6"
        path_b = "Debug/11/ab/cd/e6"
        originais = {path_a: self.orig, path_b: self.orig}
        arq = loctext.ler(self.orig)
        novo_a = loctext.escrever(arq.com_textos_por_chave({"menu__a": "Menu A"}))
        novo_b = loctext.escrever(arq.com_textos_por_chave({"menu__b": "Sair B"}))
        gerados = {path_a: novo_a, path_b: novo_b}

        pacote, pj = montar(originais, gerados, "0.0.1")

        entradas = [arquivo["Entry"] for arquivo in pj["Files"]]
        self.assertEqual(entradas, [
            "files/Debug/11/26/58/e6.nbdl",
            "files/Debug/11/ab/cd/e6.nbdl",
        ])
        self.assertEqual(len(set(entradas)), 2)
        with zipfile.ZipFile(io.BytesIO(pacote)) as z:
            self.assertEqual(z.namelist(), ["patch.json", *entradas])
            self.assertEqual(aplicar_delta(self.orig, z.read(entradas[0])), novo_a)
            self.assertEqual(aplicar_delta(self.orig, z.read(entradas[1])), novo_b)
        self.assertEqual(verificar_pacote(pacote, originais), 2)

    def test_byte_estavel(self):
        _, (p1, _) = self.montar()
        _, (p2, _) = self.montar()
        self.assertEqual(p1, p2)

    def test_origem_diferente_e_detectada(self):
        originais, (pacote, _) = self.montar()
        outro = dict(originais, **{"loctext/spanish/11000001": self.igual})
        with self.assertRaises(PacoteInvalido):
            verificar_pacote(pacote, outro)

    def test_sem_alteracoes(self):
        with self.assertRaises(PacoteInvalido):
            montar({"a": self.orig}, {"a": self.orig}, "0.0.1")

    def test_mod_toml(self):
        t = empacotar.mod_toml("0.1.0", 61)
        self.assertTrue(t.isascii())
        self.assertIn('version = "0.1.0"', t)
        self.assertIn("loctext/englishus", t)
        self.assertIn("English, 1", t)
        self.assertIn("61 translated phrases", t)
        self.assertNotIn("English fallback", t)
        for chave in ("name", "description", "version", "author"):
            self.assertIn(f"{chave} = ", t)


if __name__ == "__main__":
    unittest.main()
