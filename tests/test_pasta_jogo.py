"""Destino novo e isolado para a pasta de teste do jogo."""

import os
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import _caminho  # noqa: F401
from nbptbr import io_seguro, pasta_jogo
from nbptbr.config import Caminhos

(io_seguro.RAIZ_PROJETO / "work").mkdir(parents=True, exist_ok=True)


class TestDestinoSeguro(unittest.TestCase):
    def test_destino_legado_recusa_ancestral_juncao_fora_da_raiz(self):
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            raiz = base / "projeto"
            fora = base / "fora"
            raiz.mkdir()
            fora.mkdir()
            origem = base / "origem"
            (origem / "Debug").mkdir(parents=True)
            link = raiz / "link"
            pasta_jogo._winapi.CreateJunction(str(fora), str(link))
            try:
                with (
                    mock.patch.object(io_seguro, "RAIZ_PROJETO", raiz),
                    mock.patch.object(pasta_jogo, "PASTA_JOGO", link / "extraido"),
                    mock.patch.object(pasta_jogo, "ler_json", return_value={"arquivos": []}),
                ):
                    with self.assertRaises(io_seguro.EscritaForaDaRaiz):
                        pasta_jogo.executar(Caminhos(extraido=origem))
                self.assertFalse((fora / "extraido").exists())
            finally:
                os.rmdir(link)

    def test_destino_existente_e_recusado_sem_alteracao(self):
        with tempfile.TemporaryDirectory(dir=io_seguro.RAIZ_PROJETO / "work") as tmp:
            destino = Path(tmp) / "jogo_existente"
            destino.mkdir()
            marcador = destino / "preservar.txt"
            marcador.write_bytes(b"nao sobrescrever")

            try:
                with mock.patch.object(pasta_jogo, "ler_json", return_value={"arquivos": []}):
                    pasta_jogo.executar(Caminhos(extraido=Path("nao-lido")), destino=destino)
            except TypeError:
                self.fail("executar ainda nao aceita destino isolado")
            except FileExistsError:
                pass
            else:
                self.fail("executar deveria recusar um destino existente")

            self.assertEqual(marcador.read_bytes(), b"nao sobrescrever")

    def test_destino_fora_da_raiz_e_recusado(self):
        fora = io_seguro.RAIZ_PROJETO.parent / "nbptbr-fora-do-projeto-nao-criar"
        try:
            with mock.patch.object(pasta_jogo, "ler_json", return_value={"arquivos": []}):
                pasta_jogo.executar(Caminhos(extraido=Path("nao-lido")), destino=fora)
        except TypeError:
            self.fail("executar ainda nao aceita destino isolado")
        except io_seguro.EscritaForaDaRaiz:
            pass
        else:
            self.fail("executar deveria recusar escrita fora da raiz")


if __name__ == "__main__":
    unittest.main()
