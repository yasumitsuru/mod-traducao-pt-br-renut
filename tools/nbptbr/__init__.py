"""Ferramentas da tradução PT-BR de Banjo-Kazooie: Nuts & Bolts (mod reNut).

Módulos:
    io_seguro  -- leitura somente-leitura de pastas externas e escrita atômica restrita à raiz.
    caff       -- contêiner CAFF 07.08.06.0036 (subconjunto usado pelos arquivos loctext).
    lsbl       -- asset de texto (preâmbulo + tabela LSBL com frases, chaves, comentários e índice).
    loctext    -- leitura/escrita de alto nível de um arquivo loctext completo.
    codigos    -- códigos de controle presentes nas frases ({MOODHAPPY}, [A], <font ...>, %s...).
    config     -- caminhos externos (config/caminhos.toml, fora do git).
"""

__all__ = ["io_seguro", "caff", "lsbl", "loctext", "codigos", "config"]
