# Relatório — tradução PT-BR do launcher do reNut (0.9.0 corretiva)

Data: 2026-11-23
Estado: **prévia corretiva, não publicada**. A cobertura textual do catálogo é
completa; a cobertura visual tem estados BLOCKED/NOT_TESTED e **não** é 100%.

## 1. Versão e integridade

| Item | Valor |
|---|---|
| Release do reNut | `big-lua-energy` |
| Versão instalada | `0.11.21` (string interna `0.11.0-dev.g0b78fa33`) |
| Arquitetura | PE32+ x86-64, 9 seções após o patch |
| `renut.exe` original | 94.151.680 bytes |
| SHA-256 original | `b303e0b12598fe4e076a1d51c027674797953f252c1f5250d7313311aad03fe7` |
| Cópia traduzida | 94.154.752 bytes |
| SHA-256 da cópia | `49e78d5156a0944ca96f9f1d2ab608c6ebeec9a3afdd5d65dba64033453f7f31` |
| Patch do executável | 280 regiões, 54.119 bytes de JSON |
| Manifesto | `launcher-patch/manifesto.json` (`0.9.0-preview.1`) |
| DLL `rexui.dll` | 669.696 bytes; original `79d5a545…7a9c`; traduzida `9307053a…7395` |
| DLL `rexhid.dll` | 382.464 bytes; original `f79df02a…8677`; traduzida `b105cd53…6def` |
| Mod do jogo | v0.7.0, `.nbpatch` `7cd39a34…5e25` (conferido, não alterado) |

## 2. Diagnóstico da falha anterior

A prévia 0.8.0 partiu de uma premissa errada: catalogou apenas os literais de
`launcher_menu.cpp` e só varreu o `renut.exe` em UTF-8. Ficaram de fora:

1. **Strings de outros módulos** — `game_setup.cpp`, `updater.cpp` e `workshop.cpp`
   fornecem dezenas de mensagens exibidas pelo launcher (erros de disco, região,
   pacote, rede, arquivo danificado, progresso e estados da oficina).
2. **Descrições das configurações** — as ajudas de VÍDEO e CONTROLES são literais de
   `renut.exe`/DLLs que não estavam no catálogo. A prévia via apenas os rótulos.
3. **Strings UTF-16** — os títulos e filtros dos seletores nativos do Windows são
   `wchar_t`; a busca em UTF-8 nunca os encontrava.
4. **Strings em DLLs** — `Fullscreen` (rexui.dll) e o texto de ajuda de
   `hid.drivers` (rexhid.dll) não podem ser alcançados por um patch só no `.exe`.
5. **Booleanos e vazio** — `ON`, `OFF` e `NONE` não existem como literais NUL-terminados
   no `.rdata`; o compilador os monta como imediatos de código ou reaproveita o final
   de outra string.
6. **Comprimento fixo** — algumas ajudas são lidas com o comprimento do inglês. Uma
   tradução maior era cortada no meio (a oclusão ambiente terminava em “na resoluç”).
   Os rótulos de D-pad apareciam como `D-PAD ESQUE`, `D-PAD DIREIT`.
7. **Duplicação e pooling** — `ON` é o final de `VIOLATION`; `NONE` aparece em dois
   imediatos; as mensagens “Can't write…” se repetem em vários módulos.

## 3. Inventário e diff do catálogo

| Item | 0.8.0 | 0.9.0 |
|---|---|---|
| Entradas no catálogo | 135 | **225** |
| Encontradas no binário | 133 | **223** |
| Traduzidas no mesmo espaço | 99 | **151** |
| Realocadas para `.ptbr` | 34 | **71** |
| Traduzidas por imediato de código | 0 | **1** (`NONE` → `NADA`, dois sítios) |
| Bloqueadas | 0 | **0** |
| Ausentes do binário | 2 | **2** (`NEEDED`, `Took `) |
| Strings UTF-16 | 0 | **8** |
| DLLs cobertas | 0 | **2** |

**Novas entradas: 90** — 58 mensagens, 21 ajudas, 8 seletores e 3 valores. Nenhuma
entrada antiga foi removida. O catálogo antigo está preservado em
`work/catalogo-0.8.0.json`; o diff completo está em `docs/auditoria-catalogo-0.9.0.md`.

### Cobertura textual

- Executável: **223 traduzidas / 223 encontradas = 100%**.
- DLLs do motor: **2 / 2 traduzidas**.
- Inventário inteiro: **225 / 227 = 99,1%** (as 2 ausentes não existem no binário
  instalado e não produzem efeito).
- Catálogo do executável: **223 / 225 = 99,1%**.
- Isso **não** inclui valores técnicos (`D3D12`, `4K`, `HIGH`, `OFF`, `SDL3` etc.),
  nomes de teclas, conteúdo de terceiros e botões do Windows, classificados na §7.

## 4. Correções técnicas

- **UTF-16LE**: o gerador procura literais largos terminados em `\0\0`, realoca ou
  preenche com espaços largos e atualiza ponteiros/RIP. Cobre títulos e filtros dos
  seletores nativos.
- **Imediatos de código**: `NONE` é montado por `mov dword [rbp+…], 0x454E4F4E` em
  dois pontos. Foi trocado por `NADA` (`0x4144414E`) sem mexer no fluxo.
- **Pooling de `ON`**: `ON` é o final de `VIOLATION`; o patch não sobrescreve a palavra
  original. Ele cria `SIM` na seção `.ptbr` e atualiza **somente** a referência RIP da
  função `SettingValue`. `OFF` é realocado do mesmo jeito, com a referência filtrada
  para não afetar o uso da string pelo decodificador de imagens.
- **Comprimento fixo**: todas as ajudas de configuração e de teclas foram encurtadas
  para caber no comprimento original; nenhuma delas é realocada. Isso elimina o corte
  no meio de palavras e os rótulos truncados.
- **DLLs**: patches in-place de 10→10 bytes (`Fullscreen` → `TELA CHEIA`) e 48→43
  bytes (ajuda de `hid.drivers`), com checksum PE recalculado. Aplicados **somente em
  cópias**; os originais não são abertos para escrita.
- **Sem alteração de lógica**: nenhuma instrução de código é reescrita além dos dois
  imediatos de exibição; ASLR, DEP, SEH, relocações e imports continuam válidos.

## 5. Matriz visual

Capturas em `work/fotos/corretiva/` (privadas). A matriz completa está em
`launcher-patch/matriz-visual.json`.

| # | Tela / estado | Resultado | Status |
|---|---|---|---|
| 1 | Menu principal 720p (10 itens) | PT-BR, acentos, sem corte | PASS |
| 2 | Menu principal 1080p | PT-BR, layout preservado | PASS |
| 3 | AJUSTES (3 páginas + MENU) | PT-BR | PASS |
| 4 | IDIOMA (12 idiomas, seleção, ajuda, rolagem) | PT-BR, lista rola até Russo | PASS |
| 5 | VÍDEO (19 rótulos + descrições + rolagem) | PT-BR; descrições completas | PASS |
| 6 | CONTROLES (6 opções + ações + rolagem + espera de tecla) | PT-BR; CIMA/BAIXO/ESQUERDA/DIREITA completos | PASS |
| 7 | OFICINA (cabeçalho, grade, rodapé) | PT-BR; nomes de veículos são conteúdo de terceiros | PASS |
| 8 | COMPARTILHAR sem veículos | PT-BR; `NADA` no veículo; aviso traduzido | PASS |
| 9 | COMPARTILHAR com veículo (nome, descrição, captura, envio) | Depende de save com veículo | BLOCKED |
| 10 | Seletor de pasta | Título `Escolha uma pasta` | PASS |
| 11 | Seletor de ISO | Título `Escolha a imagem do disco`; filtro `Imagens (*.iso)` | PASS |
| 12 | Seletor de atualização | Título `Escolha a Atualização #3 (TU_...)` | PASS |
| 13 | Seletor de DLC | Abriu picker de pasta com título traduzido; não confirmado como DLC | PARTIAL |
| 14 | Extração: progresso e conclusão | `EXTRAINDO DISCO DO JOGO 56% (3,5 GB de 6,1 GB)`, `ESC / B PARAR`, `Os arquivos do jogo estão em…` | PASS (ver §9) |
| 15 | Extração: cancelamento a tempo | O ESC chegou depois do fim | NOT_TESTED |
| 16 | Erros de arquivo sintético (ISO/pacote inválido) | O seletor manteve o ISO real selecionado | NOT_TESTED |
| 17 | Atualização automática (download/instalação/erro) | Sem release nova para provocar | NOT_TESTED |
| 18 | 4K | Monitor disponível é 2560×1440 | NOT_TESTED |
| 19 | Reversão e reaplicação | CLI e app conferem hashes | PASS |
| 20 | Integração com o jogo PT-BR | `.nbpatch` intacto; jogo não iniciado nesta rodada | NOT_TESTED |
| 21 | Fechamento (SAIR) | Processo encerrou | PASS |
| 22 | Gamepad | Sem controle disponível | NOT_TESTED |

**Contagem:** 14 PASS, 1 PARTIAL, 1 BLOCKED, 6 NOT_TESTED (22 estados).
**Não há 100% visual.**

## 6. Testes funcionais e de layout

| Teste | Resultado |
|---|---|
| Inicialização e menu | PASS |
| Navegação por teclado (setas, Enter, BACK) | PASS |
| Navegação por mouse | PASS com ressalva: o driver de teste precisou de calibração; o launcher respondeu |
| Alteração de configuração (TELA CHEIA SIM↔NÃO) | PASS |
| Alteração de configuração (SSAO High→Off) | PASS, restaurado depois |
| Lista de idiomas (12) e rolagem | PASS |
| VÍDEO completo (19 linhas, 2 páginas) | PASS |
| CONTROLES completo (6 opções + ações, rolagem) | PASS |
| Espera de tecla (`TECLA`) | PASS (estado exibido); cancelamento por ESC não limpou de imediato |
| Oficina e compartilhamento vazio | PASS |
| Reversão | PASS |
| Reaplicação | PASS |
| 1080p | PASS |
| 4K | NOT_TESTED |
| Texto cortado/sobreposto | Nenhum corte novo encontrado; rodapé da oficina já nascia colado à borda esquerda |
| Acentuação | ã, õ, ç, ê, ô, á, é, í, ó, ú renderizados; o `Ã` de ATUALIZAÇÃO é estreito no fonte像素, mas presente |

## 7. Textos que permanecem em inglês (classificados)

| Texto | Onde | Classificação | Motivo |
|---|---|---|---|
| `D3D12`, `4K`, `150%`, `16X`, `8X`, `MAX`, `SMAA`, `SDL3` | VÍDEO/CONTROLES | valor técnico | tokens gravados no `renut.toml`; traduzir quebraria a leitura |
| `GAME`, `HIGH`, `OFF`, `RESOL.` | VÍDEO | valor técnico | valores de opção do motor; `OFF` é escolha, não booleano |
| `W S A D Q E ESC TAB UP DOWN LEFT RIGHT SPACE LMB RMB` | CONTROLES | nome de tecla | identificadores, não texto |
| Showdown Town, Spiral Mountain, Nutty Acres, Banjoland, LOGBOX 720, Jiggosseum, Terrarium of Terror, Test-O-Track, Klungo's Arcade | textos do jogo | nome próprio protegido | regra do projeto |
| Nomes/descrições de veículos | OFICINA/COMPARTILHAR | conteúdo de terceiros | dados do usuário/oficina |
| `Abrir`, `Cancelar`, `Selecionar pasta` | janelas nativas | externo ao launcher | UI do Windows (já em pt-BR nesta máquina) |
| `renut_mouse_camera`, `default.xex`, `default.xexp`, `TU_...` | ajudas | termo técnico | nomes de arquivo/chave |

Nenhuma ocorrência ficou sem classificação nas telas percorridas.

## 8. Reversão e reprodutibilidade

1. Original identificado por SHA-256 (`b303…`) antes de qualquer escrita.
2. Patch aplicado numa pasta nova; saída `49e78d…`.
3. DLLs aplicadas nas cópias; hashes `9307…` e `b105…`.
4. Reversão removeu o `.exe` e as duas DLLs traduzidas; os arquivos originais
   continuaram com os hashes de entrada.
5. Reaplicação produziu os mesmos hashes (determinístico).

Testes automatizados: `cargo build`, `cargo test` (25 + 2 + 1), `pytest` (96),
`pytest launcher-patch/test_aplicar.py` (3) e `rebuild_check` — todos PASS.

## 9. Ocorrência durante o teste visual (divulgação)

Ao tentar provocar o erro de ISO inválida com um arquivo sintético, o seletor nativo
manteve o **ISO real** selecionado e o Enter iniciou uma extração de verdade. A
extração terminou em `C:\Games\…\game\extraido`, a partir do mesmo ISO original. O
`renut.toml` foi reescrito pelo launcher ao salvar configurações durante os testes
(perdeu `[kernel] user_language = 1` e duas chaves de `[renut]`); ele foi **restaurado**
a partir de `work/renut_ptbr/renut.toml` com os caminhos de `C:\Games`, e o
`user_language = 1` foi conferido.

O que **não** foi tocado: `renut.exe` e DLLs originais, `mods/`, o `.nbpatch`
(`7cd39a34…5e25` conferido), saves e `renut.cfg`. A pasta do jogo foi reextraída do
mesmo ISO; os 14 idiomas de `loctext`, `Bundle`, `Debug`, `default.xex` e
`default.xexp` estão presentes. O jogo não foi aberto depois. Esta é uma violação da
regra “não modificar a instalação original durante o desenvolvimento” e fica
registrada; o teste de erro sintético deve ser refeito numa cópia isolada.

## 10. Integração com o jogo PT-BR

- O `.nbpatch` v0.7.0 está intacto (`7cd39a34…5e25`).
- O idioma do jogo está em `English (1)` no `renut.toml` restaurado.
- O jogo **não foi iniciado** nesta rodada; a abertura em PT-BR com o launcher
  traduzido continua NOT_TESTED. A tradução do jogo não foi alterada.

## 11. Distribuição

- Pasta: `launcher-patch/`.
- Conteúdo: catálogo-fonte e gerado, patch do executável, manifesto, patches das duas
  DLLs, geradores, aplicador, testes, atalhos, `LEIA-ME.md`, `NOTICE.md`,
  `SHA256SUMS.txt`.
- Não contém `renut.exe`, DLLs, jogo, ISO, DLC, saves, `.nbpatch` nem capturas.
- Release pública: **não publicada**.

## 12. Pendências e bloqueios

1. Compartilhar um veículo de verdade (BLOCKED: sem save com veículo).
2. Cancelar extração a tempo, erros sintéticos, atualização automática, 4K e gamepad
   (NOT_TESTED).
3. Integração com o jogo PT-BR nesta versão (NOT_TESTED).
4. Os valores técnicos continuam em inglês por decisão de compatibilidade.
5. As duas frases ausentes (`NEEDED`, `Took `) não existem no binário instalado.
6. O teste de erro sintético precisa ser refeito numa cópia isolada, com o jogo e o
   save fora do caminho real.
7. Publicação depende de homologação e de uma nova auditoria de conteúdo.

## 13. Checklist do relatório final (missão §14)

| # | Item | Resultado |
|---|---|---|
| 1 | Versão do reNut | `big-lua-energy`, 0.11.21 |
| 2 | SHA-256 original | `b303e0b1…3fe7` |
| 3 | SHA-256 traduzido | `49e78d51…7f31` |
| 4 | Strings no patch anterior | 135 (133 efetivas) |
| 5 | Strings esquecidas | 90 novas |
| 6 | Strings corrigidas | 90 novas + 8 ajudas/rótulos ajustados |
| 7 | Total traduzível | 225 efetivas (223 no .exe + 2 DLLs); 2 ausentes no catálogo |
| 8 | Cobertura textual real | 100% do efetivo; 99,1% do inventário |
| 9 | Menus/opções testados | 6 telas, 10 itens de menu, 3 páginas, 12 idiomas, 19 vídeo, 6 opções + 21 ações |
| 10 | Cobertura visual real | 14 PASS, 1 PARTIAL, 1 BLOCKED, 6 NOT_TESTED; não é 100% |
| 11 | Textos em inglês | §7 (tokens técnicos, nomes, terceiros, Windows) |
| 12 | Testes funcionais | §6 |
| 13 | Testes de layout | §6/§5 |
| 14 | Capturas | `work/fotos/corretiva/` |
| 15 | Reversão | PASS |
| 16 | Integração com o jogo | NOT_TESTED; `.nbpatch` intacto |
| 17 | Pendências | §12 |