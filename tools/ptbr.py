"""Linha de comando do projeto de tradução PT-BR de Banjo-Kazooie: Nuts & Bolts.

Uso (sempre com python -I, a partir da raiz do projeto):
    python -I tools/ptbr.py roundtrip [--idioma spanish|todos|english]
    python -I tools/ptbr.py info <arquivo>
    python -I tools/ptbr.py extrair
    python -I tools/ptbr.py fonte
    python -I tools/ptbr.py validar [--arquivo HASH] [--limiar 0.20]
    python -I tools/ptbr.py aplicar-lote data/lotes/lote-NNN.json
    python -I tools/ptbr.py auditar-nomes [--detalhes]
    python -I tools/ptbr.py corrigir-nomes --lote data/lotes/lote-NNN.json
    python -I tools/ptbr.py reinserir [--relatorio work/relatorio-novo.json]
    python -I tools/ptbr.py empacotar [--versao 0.2.0] [--destino work/pacote-novo]
    python -I tools/ptbr.py sincronizar-iniciador
    python -I tools/ptbr.py jogo-isolado --destino work/jogo/extraido

Pastas do jogo e do reNut são lidas em modo somente leitura; toda saída fica na raiz do projeto.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from nbptbr import config, loctext  # noqa: E402
from nbptbr.io_seguro import EscritaForaDaRaiz, RAIZ_PROJETO, caminho_gravavel, gravar_json_atomico, ler_binario, sha256  # noqa: E402


def _destino_novo(valor: str | Path) -> Path:
    """Valida um caminho de saída novo, relativo à raiz do projeto ou absoluto nela."""
    entrada = Path(valor)
    if not entrada.is_absolute():
        entrada = RAIZ_PROJETO / entrada
    destino = caminho_gravavel(entrada)
    if os.path.lexists(entrada):
        raise FileExistsError(f"destino ja existe: {entrada}")
    return destino


def cmd_roundtrip(args: argparse.Namespace) -> int:
    from nbptbr import roundtrip

    cam = config.carregar()
    idiomas = list(config.IDIOMAS) + ["english"] if args.idioma == "todos" else [args.idioma]
    falhas_total = 0
    for idioma in idiomas:
        res = roundtrip.executar(cam, idioma, gravar_copias=not args.sem_copias)
        ok = sum(r.ok for r in res)
        frases = sum(r.frases for r in res)
        falhas = [r for r in res if not r.ok]
        falhas_total += len(falhas)
        estado = "PASS" if not falhas and res else "FAIL"
        print(f"{idioma:12s} arquivos={len(res):3d} identicos={ok:3d} frases={frases:5d} -> {estado}")
        for r in falhas[:10]:
            print(f"   FALHA {r.arquivo}: {r.erro or 'SHA-256 diferente'}")
    if not args.sem_copias:
        print(f"Cópias e relatórios em {roundtrip.PASTA_TRABALHO}")
    return 1 if falhas_total else 0


def cmd_info(args: argparse.Namespace) -> int:
    dados = ler_binario(args.arquivo)
    arq = loctext.ler(dados)
    a = arq.asset
    print(f"asset        : {arq.nome_asset}")
    print(f"símbolo      : {arq.conteiner.nome_simbolo.decode('ascii')}")
    print(f"sha256       : {sha256(dados)}")
    print(f"checksum CAFF: {arq.conteiner.checksum:#010x}  área de info: {arq.conteiner.tam_info:#x}")
    print(f"seção .data  : {len(arq.conteiner.dados)} bytes")
    print(f"frases       : {len(a.textos)}  vazias: {sum(1 for t in a.textos if not t)}")
    print(f"comentários  : {'sim' if a.tabela_comentarios else 'não'}  índice: {'sim' if a.tabela_indice else 'não'}")
    print(f"colisões     : {[c.nome for c in a.colisoes()]}")
    for f in arq.frases()[: args.limite]:
        print(f"  [{f.id}] {f.chave}: {f.texto[:70]!r}")
    return 0


def cmd_extrair(args: argparse.Namespace) -> int:
    from nbptbr import extrair

    resumo = extrair.executar(config.carregar())
    for linha in resumo["por_arquivo"]:
        print(f"{linha['arquivo']} {linha['asset']:52s} frases={linha['frases']:4d} vazias={linha['vazias']:3d}")
    print(f"TOTAL arquivos={resumo['arquivos']} frases={resumo['frases']} vazias={resumo['vazias']} "
          f"com_ingles={resumo['com_ingles']}")
    return 0


def cmd_fonte(args: argparse.Namespace) -> int:
    from nbptbr import fonte

    r = fonte.executar(config.carregar())
    print(f"precache_euro.ini: {r['precache']} caracteres; euro.sbp: {r['sbp']} glyphs")
    print(f"PT-BR: faltando no precache={r['faltando_precache'] or 'nenhum'}; faltando no sbp={r['faltando_sbp'] or 'nenhum'}")
    print(f"Gravado em {r['saida']}")
    return 0


def cmd_validar(args: argparse.Namespace) -> int:
    from nbptbr import validar

    rel = validar.executar(arquivo=args.arquivo, limiar=args.limiar, so_traduzidas=args.so_traduzidas)
    print(validar.formatar_resumo(rel, detalhes=args.detalhes))
    return 0 if rel["estado"] == "PASS" else 1


def cmd_aplicar_lote(args: argparse.Namespace) -> int:
    from nbptbr import lotes, validar

    r = lotes.aplicar(args.lote)
    print(f"lote {r['lote']}: {r['frases']} frases em {r['arquivos']} arquivos")
    rel = validar.executar(so_traduzidas=True)
    print(validar.formatar_resumo(rel, detalhes=True))
    return 0 if rel["estado"] == "PASS" else 1


def cmd_pendentes(args: argparse.Namespace) -> int:
    """Lista (somente leitura) as frases ainda sem tradução de um arquivo: id, chave, inglês, espanhol."""
    from nbptbr.extrair import carregar_strings, carregar_traducao

    for nome in args.arquivos:
        d = carregar_strings(nome)
        feitas = {f["id"] for f in carregar_traducao(nome)["frases"] if f.get("texto_ptbr")}
        print(f"### {nome} {d['asset']}")
        for f in d["frases"]:
            ref = f["texto_en"] if f["texto_en"] is not None else f["texto_es"]
            if ref and f["id"] not in feitas:
                print(f"[{f['id']}] {f['chave']}\n  EN: {f['texto_en']!r}\n  ES: {f['texto_es']!r}")
    return 0


def cmd_checar_lote(args: argparse.Namespace) -> int:
    from nbptbr import lotes

    r = lotes.checar(args.lote, limiar=args.limiar)
    c = r["contagem"]
    print(f"{r['estado']}: frases={c.get('frases', 0)} erros={c.get('ERRO', 0)} avisos={c.get('AVISO', 0)} "
          f"faltam_nos_arquivos={c.get('faltam', 0)}")
    for nivel, arq, fid, regra, msg in r["itens"]:
        print(f"  {nivel:5s} {arq}[{fid}] {regra}: {msg}")
    return 0 if r["estado"] == "PASS" else 1


def cmd_auditar_nomes(args: argparse.Namespace) -> int:
    from nbptbr import protegidos

    itens = protegidos.auditar()
    print(f"nomes protegidos: {len(itens)} frase(s) com variante traduzida")
    for item in itens:
        variantes = ", ".join(f"{v['variante']} -> {v['nome']}" for v in item["violacoes"])
        print(f"  {item['arquivo']}[{item['id']}] {item['chave']}: {variantes}")
    return 0 if not itens else 1


def cmd_corrigir_nomes(args: argparse.Namespace) -> int:
    from nbptbr import protegidos

    try:
        destino = _destino_novo(args.lote)
    except (EscritaForaDaRaiz, FileExistsError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2
    lote = protegidos.lote_correcao(args.numero)
    n = sum(len(v) for v in lote["traducoes"].values())
    gravar_json_atomico(destino, lote)
    print(f"lote {lote['lote']}: {n} frase(s) em {len(lote['traducoes'])} arquivo(s) -> {destino}")
    print("Confira com: python -I tools/ptbr.py checar-lote " + str(destino))
    return 0


def cmd_reinserir(args: argparse.Namespace) -> int:
    from nbptbr import reinserir, validar

    relatorio = None
    if args.relatorio:
        try:
            relatorio = _destino_novo(args.relatorio)
        except (EscritaForaDaRaiz, FileExistsError) as exc:
            print(f"ERRO: {exc}", file=sys.stderr)
            return 2
    relatorio_original = validar.ARQ_RELATORIO
    try:
        if relatorio is not None:
            validar.ARQ_RELATORIO = relatorio
        r = reinserir.executar(config.carregar())
    finally:
        validar.ARQ_RELATORIO = relatorio_original
    print(f"arquivos={r['arquivos']} com_traducao={r['com_traducao']} frases_substituidas={r['substituidas']} -> {r['estado']}")
    print(f"Saída em {r['saida']}")
    return 0 if r["estado"] == "PASS" else 1


def cmd_empacotar(args: argparse.Namespace) -> int:
    from nbptbr import empacotar

    destino = None
    if args.destino:
        try:
            destino = _destino_novo(args.destino)
        except (EscritaForaDaRaiz, FileExistsError) as exc:
            print(f"ERRO: {exc}", file=sys.stderr)
            return 2
    cam = config.carregar()
    pasta_dist_original = empacotar.PASTA_DIST
    try:
        if destino is not None:
            empacotar.PASTA_DIST = destino
        r = empacotar.executar(cam, versao=args.versao)
    finally:
        empacotar.PASTA_DIST = pasta_dist_original
    print(f"{r['estado']}: {r['arquivos']} arquivo(s), {r['frases']} frases, {r['tamanho']} bytes, sha256 {r['sha256']}")
    print(f"Mod gerado em {r['saida']} (EXPERIMENTAL: validar no jogo)")
    destino_instalacao = (cam.renut / "mods" / empacotar.ID_MOD) if cam.renut else None
    if args.destino:
        print("Saida isolada de ensaio; nada foi copiado para a pasta mods.")
    elif destino_instalacao:
        print("Para instalar (copie e cole no PowerShell; nada foi copiado automaticamente):")
        print(f"  Copy-Item -LiteralPath '{r['saida']}' -Destination '{destino_instalacao.parent}' -Recurse -Force")
    return 0


def cmd_jogo_isolado(args: argparse.Namespace) -> int:
    from nbptbr import pasta_jogo

    try:
        destino = _destino_novo(args.destino)
        r = pasta_jogo.executar(config.carregar(), destino=destino)
    except (EscritaForaDaRaiz, FileExistsError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2
    print(f"{r['estado']}: arquivos_texto={r['arquivos_texto']} traduzidos={r['arquivos_traduzidos']}")
    print(f"Pasta isolada: {r['pasta']}")
    print("Juncoes apontam para o jogo original, aberto somente para leitura.")
    return 0 if r["estado"] == "PASS" else 1


def cmd_sincronizar_iniciador(args: argparse.Namespace) -> int:
    from nbptbr import iniciador

    nbpatch = None if args.sem_nbpatch else iniciador.NBPATCH
    try:
        r = iniciador.executar(nbpatch=nbpatch, limpar=args.limpar)
    except (iniciador.PacoteIniciadorInvalido, EscritaForaDaRaiz, FileNotFoundError) as exc:
        print(f"ERRO: {exc}", file=sys.stderr)
        return 2
    print(f"{r['estado']}: {r['arquivos']} arquivo(s) traduzido(s), {r['frases']} frases, versao {r['versao']}")
    print(f"Pacote do iniciador: {r['pacote']}")
    print(f"Lista embutida: {r['rust']}")
    if r["removidos"]:
        print(f"Removidos do pacote (fora da lista nova): {', '.join(r['removidos'])}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="ptbr", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("roundtrip", help="F1: ler e reescrever, comparando SHA-256")
    s.add_argument("--idioma", default="spanish", help="spanish (padrão), english, todos ou outro idioma")
    s.add_argument("--sem-copias", action="store_true", help="não gravar cópias em work/roundtrip")
    s.set_defaults(fn=cmd_roundtrip)

    s = sub.add_parser("info", help="resumo de um arquivo loctext")
    s.add_argument("arquivo")
    s.add_argument("--limite", type=int, default=10)
    s.set_defaults(fn=cmd_info)

    s = sub.add_parser("extrair", help="F2: exportar frases para data/strings e data/traducao")
    s.set_defaults(fn=cmd_extrair)

    s = sub.add_parser("fonte", help="F3: inventário de caracteres da fonte euro")
    s.set_defaults(fn=cmd_fonte)

    s = sub.add_parser("validar", help="F3: validar traduções")
    s.add_argument("--arquivo", help="só este arquivo (hash)")
    s.add_argument("--limiar", type=float, default=0.20, help="aviso se o texto crescer mais que isso (0.20 = +20%%)")
    s.add_argument("--so-traduzidas", action="store_true", help="não contar pendentes")
    s.add_argument("--detalhes", action="store_true")
    s.set_defaults(fn=cmd_validar)

    s = sub.add_parser("aplicar-lote", help="F4: aplicar data/lotes/lote-NNN.json e validar")
    s.add_argument("lote")
    s.set_defaults(fn=cmd_aplicar_lote)

    s = sub.add_parser("pendentes", help="F4: listar frases sem tradução (somente leitura)")
    s.add_argument("arquivos", nargs="+")
    s.set_defaults(fn=cmd_pendentes)

    s = sub.add_parser("checar-lote", help="F4: conferir um lote sem gravar nada")
    s.add_argument("lote")
    s.add_argument("--limiar", type=float, default=0.20)
    s.set_defaults(fn=cmd_checar_lote)

    s = sub.add_parser("auditar-nomes", help="conferir nomes de fases/mundos traduzidos (somente leitura)")
    s.set_defaults(fn=cmd_auditar_nomes)

    s = sub.add_parser("corrigir-nomes", help="gerar um lote que restaura os nomes oficiais")
    s.add_argument("--lote", required=True, help="arquivo novo do lote, dentro da raiz do projeto")
    s.add_argument("--numero", default="519", help="número do lote (padrão 519)")
    s.set_defaults(fn=cmd_corrigir_nomes)

    s = sub.add_parser("reinserir", help="F5: gerar os textos ingleses com o PT-BR em build/loctext/english")
    s.add_argument("--relatorio", help="gravar a validação em um arquivo novo dentro da raiz do projeto")
    s.set_defaults(fn=cmd_reinserir)

    s = sub.add_parser("empacotar", help="F6: gerar dist/ptbr_traducao (mod.toml + .nbpatch) — experimental")
    s.add_argument("--versao", default="0.1.0")
    s.add_argument("--destino", help="ensaio: gravar em uma pasta nova dentro da raiz, sem substituir nada")
    s.set_defaults(fn=cmd_empacotar)

    s = sub.add_parser(
        "sincronizar-iniciador",
        help="levar a saída da F5 (e o .nbpatch da F6) para o pacote embutido no iniciador (app/)",
    )
    s.add_argument("--sem-nbpatch", action="store_true", help="não conferir dist/ptbr_traducao/*.nbpatch")
    s.add_argument("--limpar", action="store_true",
                   help="remover de app/ptbr_copy_package/files os arquivos que não estão na lista nova")
    s.set_defaults(fn=cmd_sincronizar_iniciador)

    s = sub.add_parser("jogo-isolado", help="montar cópia de teste em uma pasta nova dentro do projeto")
    s.add_argument("--destino", required=True, help="caminho novo da pasta extraido, dentro da raiz do projeto")
    s.set_defaults(fn=cmd_jogo_isolado)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
