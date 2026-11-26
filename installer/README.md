# Instalador PT-BR do reNut

Aplicativo Windows portátil que instala a tradução PT-BR do jogo e a tradução do launcher
original do reNut, com detecção da pasta, verificação de hashes, instalação transacional,
atalho na área de trabalho e remoção segura.

**Não é um launcher novo.** O programa só instala, verifica e remove; o jogo continua sendo
aberto pelo `renut.exe` original ou pela cópia traduzida do próprio reNut.

## O que ele faz

| Opção | Resultado |
|---|---|
| Instalar tradução PT-BR do jogo | Gera `ptbr_traducao.nbpatch` **na hora**, a partir da cópia legítima do jogo, confere o SHA-256 `d250b595…d8db` (tradução revisada 0.8.0) e instala em `<mods>/ptbr_traducao` (mais `mod.toml`). Se encontrar a 0.7.0 instalada, atualiza para a 0.8.0 de uma vez, sem remoção manual, e restaura a anterior se algo falhar. |
| Aplicar tradução ao launcher | Cria `<reNut>/launcher-ptbr/` com uma cópia do executável e de todas as DLLs, aplica o patch do executável e das DLLs `rexui.dll`/`rexhid.dll` **nas cópias** e confere cada hash. A configuração copiada recebe `[renut] renut_mods_folder` apontando para a pasta `mods` da instalação, para o jogo aberto pelo launcher traduzido carregar a tradução. |
| Criar atalho | Cria `Banjo-Kazooie Nuts & Bolts — PT-BR.lnk` na área de trabalho real do usuário, apontando para o launcher traduzido (ou para o `renut.exe` original, se só o mod estiver instalado). |

A instalação é transacional: tudo é preparado em `<reNut>/.ptbr-instalador/tmp-…`, conferido e
só então publicado. Uma falha desfaz o que foi criado e restaura o que existia. O que não é do
instalador nunca é apagado.

## Arquitetura

```
installer/
  Cargo.toml
  build.rs            embute data/traducao num único catálogo (somente texto do projeto)
  src/
    main.rs           interface egui em português
    detect.rs         detecção da instalação, do jogo, do mod e do launcher
    plano.rs          instalação/remoção transacional e manifesto
    modpack.rs        gerador local do .nbpatch (porte de tools/gerar_mod.py)
    caff.rs           porte de tools/nbptbr/caff.py
    lsbl.rs           porte de tools/nbptbr/lsbl.py
    loctext.rs        leitura/escrita de um texto do jogo
    zipw.rs           ZIP byte a byte igual ao do gerador Python
    patch.rs          conferência do launcher (exe + 2 DLLs) e remoção segura
    gerador_launcher.rs  gera a cópia traduzida a partir do renut.exe e das DLLs do usuário
    atalho.rs         atalho .lnk pela interface nativa do Windows (IShellLinkW, Unicode)
    manifesto.rs      manifesto privado da instalação
    toml_min.rs       leitura/edição pontual do renut.toml
    sistema.rs        espaço livre, DPI, prefixos de caminho
  tests/              fluxo sintético e teste com a cópia real (opcional)
```

O catálogo público do launcher (`launcher-patch/entradas_launcher.json`) e os manifestos (só
hashes) são lidos em tempo de compilação de `launcher-patch/` (`include_str!`): existe uma única
fonte da verdade, sem cópias. Nenhum patch binário é embutido. O catálogo de tradução vem de
`data/traducao/` pelo `build.rs`.

## Integração com o reNut

O reNut deriva a pasta de mods de `[app] root` no `renut.toml`, não da pasta do executável. Por
isso o runtime traduzido é uma pasta separada, mas o `renut.toml` copiado continua apontando
`[app] root`, `user_root`, `[title] game_root` e `update_root` para a instalação original:

* o mod fica na mesma pasta `mods` que o reNut original usa;
* os saves, DLCs, Title Updates e o jogo extraído são os mesmos, sem duplicar 1 GB de arquivos;
* o `renut.exe` e as DLLs originais nunca são abertos para escrita.

No `renut.toml` da cópia, apenas `[kernel] user_language` é definido como `1` (English), que é o
idioma usado pela tradução. O `renut.toml` original não é alterado. As demais configurações são
preservadas linha a linha.

Se o launcher traduzido for removido e o mod continuar instalado, o atalho é recriado apontando
para o `renut.exe` original. Se nada mais estiver instalado, o atalho é removido.

O reNut grava o perfil do guia (conta, conquistas, imagens do jogador) ao lado do executável que
está rodando. Por isso o launcher traduzido tem um perfil próprio em `launcher-ptbr/guide`. Esses
dados de uso (`guide`, `crashdumps`, `logs`, `save`, `user`, `sentry`) não são do instalador:
ficam fora do manifesto, são levados para a cópia nova na reinstalação e continuam na pasta
depois da remoção. Os saves continuam na pasta `save` da instalação (`user_root`).

## Segurança

* Recusa executáveis e DLLs com hash diferente do manifesto; nunca aplica patch à força.
* A instalação do launcher só é declarada concluída quando o executável **e** as duas DLLs
  obrigatórias conferem com o SHA-256 de saída. Uma DLL sem patch faz a operação inteira falhar
  e ser desfeita.
* Gravações atômicas (arquivo temporário + `rename`), verificação após gravar e rollback.
* Não segue links simbólicos ao copiar o runtime.
* Não sobrescreve pasta de mod, pasta de launcher ou atalho que não sejam comprovadamente do
  instalador.
* Nada é baixado; nenhuma conexão de rede é usada.
* Não pede privilégios administrativos e não abre outros programas (nem PowerShell): o atalho é
  gravado pela interface COM do próprio Windows.
* Com o jogo ou o launcher traduzido aberto, instalação e remoção recusam antes de mudar
  qualquer coisa (a pasta em uso é detectada), em vez de parar no meio.

## Testes

```
cargo test -p instalador-renut-ptbr
```

Cobre: CAFF/LSBL ida e volta, ZIP byte a byte contra o `zipfile` do Python, catálogo de 107
arquivos, manifesto, edição do `renut.toml`, detecção de pasta vazia/inexistente, instalação e
reinstalação do mod em pasta com espaços e acentos, recusa de pasta estranha, cancelamento,
hash divergente, remoção preservando outros mods, remoção que recusa arquivo alterado, criação
real de atalho `.lnk` (inclusive em caminho com japonês), perfil do launcher preservado na
reinstalação e pasta em uso detectada (Windows).

Teste com a cópia real do jogo (opcional, não roda por padrão):

```
set RENUT_GAME=<pasta do reNut>\game\extraido
cargo test --release -p instalador-renut-ptbr --test real_data -- --nocapture
```

Ele exige o pacote gerado byte a byte igual ao 0.8.0: 107 arquivos, 6.099 frases, 1.145.999 bytes e
SHA-256 `d250b5959e7f0171355f9d6a3e1ac031e8c123dfb5fbfb0423beca538e20d8db` (o mesmo do
`tools/gerar_mod.py` e do `empacotar`). O pacote da Release v0.7.0
(`7cd39a34efbae21dc8d3f919e63349e15df88397080ad59dd07207da0f5b5e25`) continua reconhecido para
atualização.

Diagnóstico por linha de comando (não substitui a interface):

```
renut-instalador-checar status   "<pasta do reNut>"
renut-instalador-checar instalar "<pasta do reNut>" --jogo --launcher --atalho
renut-instalador-checar remover  "<pasta do reNut>" --jogo --launcher --atalho
```

## Build

```
cargo build --release -p instalador-renut-ptbr
```

O executável fica em `target/release/instalador-renut-ptbr.exe` (cerca de 8,6 MB). Copie-o como
`Instalador-reNut-PTBR.exe`; é um único arquivo, sem Python, Rust, instalador ou runtime
adicional. Windows 10/11 x86-64, com o runtime C embutido (não exige o pacote VC++).

Para gerar o build **sanitizado** (sem caminhos da máquina de desenvolvimento no binário):

```
powershell -ExecutionPolicy Bypass -File installer\build-portatil.ps1 -Versao 1.0.0
```

O script liga o runtime C estaticamente, remapeia os caminhos em tempo de compilação, usa `/Brepro`
(data e GUID do PE derivados do conteúdo: o mesmo código gera o mesmo SHA-256), compila com o
`Cargo.lock` travado (`--locked`), copia o executável para
`dist/instalador/Instalador-reNut-PTBR-v1.0.0.exe` (sem `-Versao`, `Instalador-reNut-PTBR.exe`) e
grava `SHA256SUMS.txt`. Ele falha se algum caminho local sobrar no binário.

## Limitações conhecidas

* A tradução do launcher (0.9.0) é **gerada no computador do usuário**: o módulo
  `src/gerador_launcher.rs` é um porte fiel de `launcher-patch/gerar_patch.py` e
  `gerar_engine_patch.py`, lê o `renut.exe`, a `rexui.dll` e a `rexhid.dll` da instalação, aplica o
  catálogo público `launcher-patch/entradas_launcher.json` e só grava a cópia se o resultado bater
  com os SHA-256 do manifesto. Nenhum patch binário nem byte do reNut acompanha o executável.
* O jogo aberto pelo atalho do launcher traduzido foi testado numa cópia isolada (título, menu,
  abertura, diálogos e HUD de Spiral Mountain em PT-BR 0.8.0).
* A versão suportada do reNut é uma só: `big-lua-energy` 0.11.21. Outras versões ficam com o
  launcher bloqueado, mas ainda podem instalar o mod do jogo se a extração for a esperada.
* A tradução do jogo é a revisão 0.8.0 (6.110 entradas, 448 corrigidas em relação à v0.7.0; ver
  `docs/revisao-0.8.0/relatorio.md`). A cobertura visual do
  launcher continua com estados BLOCKED/NOT_TESTED no relatório do próprio componente.