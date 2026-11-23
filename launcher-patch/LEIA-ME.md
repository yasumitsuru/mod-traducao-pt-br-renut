# Tradução PT-BR do launcher do reNut — prévia 0.9.0

Este componente traduz a interface do **launcher original** do reNut para português do Brasil,
sem criar outro launcher e sem alterar o `renut.exe` nem as DLLs originais. O patch é aplicado a
uma **cópia** do launcher, numa pasta separada; a instalação original fica byte a byte intacta.

> **Estado: prévia 0.9.0, não lançada.** A cobertura textual é completa (225 de 225 entradas do
> executável + 2 descrições nas DLLs). A cobertura visual tem estados PASS, PARTIAL, BLOCKED e
> NOT_TESTED e **não** é 100%. Não é uma Release.

> **O patch binário não é distribuído.** O repositório do reNut não possui licença formal que
> autorize redistribuir binários modificados. Este repositório publica o catálogo, o gerador, o
> aplicador e a documentação; cada usuário gera o patch na própria cópia legítima do reNut.

## Versão suportada

| Item | Valor |
|---|---|
| Release do reNut | `big-lua-energy` |
| Versão instalada | `0.11.21` |
| Tamanho do `renut.exe` | 94.151.680 bytes |
| SHA-256 do `renut.exe` original | `b303e0b12598fe4e076a1d51c027674797953f252c1f5250d7313311aad03fe7` |
| SHA-256 da cópia traduzida | `49e78d5156a0944ca96f9f1d2ab608c6ebeec9a3afdd5d65dba64033453f7f31` |
| DLL `rexui.dll` | 669.696 bytes; original `79d5a545.7a9c`; traduzida `9307053a.7395` |
| DLL `rexhid.dll` | 382.464 bytes; original `f79df02a.8677`; traduzida `b105cd53.6def` |
| Mod do jogo | v0.7.0, `.nbpatch` `7cd39a34.5e25` (não alterado) |

O aplicador **recusa** qualquer outro executável ou DLL. Não tente aplicar em versões diferentes
do reNut.

## O que está traduzido

* Menu principal: JOGAR, EXTRAIR DISCO, EXTRAIR ATUALIZAÇÃO, ADICIONAR DLC, PASTA JOGO, PASTA
  UPDATE, PASTA SAVE, OFICINA, AJUSTES, SAIR.
* Páginas de opções: IDIOMA, VÍDEO, CONTROLES, com cabeçalhos e botão MENU.
* Lista de idiomas, configurações de vídeo e entrada, descrições completas e valores SIM/NÃO.
* Nomes das ações de teclado/controle e o texto de ajuda do teclado.
* Oficina, compartilhamento, avisos, progresso de extração, mensagens do extrator/atualizador e
  títulos/filtros dos seletores nativos.
* As duas descrições que vêm de `rexui.dll` e `rexhid.dll`, aplicadas em **cópias** das DLLs.

## O que permanece em inglês (de propósito)

* Valores técnicos de configuração (`D3D12`, `4K`, `150%`, `GAME`, `RESOL.`, `16X`, `HIGH`, `OFF`,
  `8X`, `MAX`, `SMAA`, `SDL3`, `1.00`): são tokens gravados no `renut.toml` e nos registros.
* Nomes de teclas (`W`, `S`, `A`, `D`, `ESC`, `TAB`, `UP`, `DOWN`, `SPACE`, `LMB`, `RMB` etc.).
* Nomes de fases/mundos protegidos: Showdown Town, Spiral Mountain, Nutty Acres, Banjoland,
  LOGBOX 720, Jiggosseum, Terrarium of Terror, Test-O-Track e Klungo's Arcade.
* Conteúdo de terceiros, nomes/descrições de veículos da oficina e capturas do usuário.
* Botões internos das janelas do Windows (Abrir, Cancelar, Selecionar pasta).

## Como gerar o patch na sua cópia

Pré-requisito: Python 3.11 ou mais recente e uma instalação funcional do reNut
`big-lua-energy` 0.11.21. O reNut é somente leitura para o gerador.

```text
python -I launcher-patch/gerar_patch.py --exe "<pasta do reNut>\renut.exe" --saida launcher-patch/renut_launcher_ptbr.patch
python -I launcher-patch/gerar_engine_patch.py --renut "<pasta do reNut>"
```

O gerador confere o SHA-256 do executável e das DLLs e grava o patch com as 280 regiões do
executável e as 4 regiões das duas DLLs. Se a versão não for a suportada, ele recusa.

## Como aplicar

Use uma **pasta separada** para a cópia (por exemplo, `C:\jogos\reNut PT-BR\renut.ptbr.exe`). O
aplicador copia as DLLs e os arquivos de configuração para essa pasta, traduz o executável e aplica
os dois patches das DLLs **nas cópias**. Se você apontar para a própria pasta do reNut, o executável
é traduzido, mas as DLLs não são tocadas e o aplicador avisa que as duas descrições do motor
continuam em inglês.

```text
python -I launcher-patch/aplicar.py status   --renut "<pasta do reNut>"
python -I launcher-patch/aplicar.py aplicar  --renut "<pasta do reNut>" --saida "<pasta nova>\renut.ptbr.exe"
python -I launcher-patch/aplicar.py reverter --renut "<pasta do reNut>" --saida "<pasta nova>\renut.ptbr.exe"
```

Também há `APLICAR.cmd` e `RESTAURAR.cmd` para duplo clique. Ambos exigem Python 3.11+.

## Segurança e reversibilidade

* O `renut.exe` original **nunca é aberto para escrita**.
* As DLLs originais **nunca são abertas para escrita**; os patches são aplicados em cópias.
* Cada região do patch é conferida antes de ser aplicada; o SHA-256 é conferido antes e depois.
* Textos que não cabem no espaço original vão para uma seção nova (`.ptbr`), somente de dados, e os
  ponteiros existentes são atualizados.
* Os patches das DLLs são in-place (mesmo tamanho), com o checksum PE recalculado.
* Reverter só apaga arquivos cujo SHA-256 é o esperado; os originais são conferidos de novo.

## Cobertura visual

Resultados registrados na prévia 0.9.0:

* 14 PASS (menu, ajustes, idioma, vídeo, controles, oficina e estados principais).
* 1 PARTIAL (compartilhar um veículo de verdade).
* 1 BLOCKED (compartilhar com veículo).
* 6 NOT_TESTED (cancelamento, erros sintéticos, atualização, 4K, jogo e gamepad).

A matriz completa está em `launcher-patch/matriz-visual.json`; a cobertura textual está em
`launcher-patch/cobertura-textual.json`. O relatório técnico está em
`docs/relatorio-launcher-0.9.0.md`.

## Arquivos

```text
entradas_launcher.json     catálogo-fonte (id, original, PT-BR, tela, condição, fonte)
catalogo.json              catálogo gerado, com ocorrências, referências e status
gerar_patch.py             gera o patch do executável a partir da cópia do usuário
gerar_engine_patch.py      gera os patches das DLLs a partir da cópia do usuário
aplicar.py                 status, aplicação e reversão com conferência de SHA-256
manifesto.json             versão suportada, hashes e contagens
engine/manifesto.json      hashes das DLLs e das duas entradas traduzidas
cobertura-textual.json     números da cobertura textual
matriz-visual.json         estados visuais, incluindo BLOCKED/NOT_TESTED
```

## Aviso de terceiros

Este componente não redistribui o executável do reNut, DLLs, arquivos do jogo, ISO, DLC, saves nem
o pacote `.nbpatch` da tradução do jogo. O usuário final precisa fornecer a própria cópia oficial do
reNut `big-lua-energy`. O reNut é um projeto independente de
[masterspike52](https://github.com/masterspike52/reNut) e mantém a sua própria licença e os seus
próprios créditos. Banjo-Kazooie: Nuts & Bolts e seus nomes, personagens e assets pertencem à Rare
Ltd. e à Microsoft. Este é um trabalho independente de tradução, sem afiliação ou endosso.