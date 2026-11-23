# Auditoria do catálogo do launcher — 0.8.0 → 0.9.0

Data: 2026-11-23
Objetivo: comparar o catálogo da prévia 0.8.0 com o inventário completo desta correção,
explicar por que a interface continuava em inglês e registrar cada classe de string.

## 1. Números

| Item | 0.8.0 | 0.9.0 |
|---|---|---|
| Entradas no catálogo do `renut.exe` | 135 | 225 |
| Entradas nas DLLs do motor | 0 | 2 |
| Total identificado | 135 | **227** |
| Traduzidas com efeito | 133 | **225** |
| Ausentes do binário instalado | 2 | 2 |
| No mesmo espaço | 99 | 151 |
| Realocadas | 34 | 71 |
| Por imediato de código | 0 | 1 (`NONE` → `NADA`, 2 sítios) |
| Bloqueadas | 0 | 0 |
| UTF-16 | 0 | 8 |
| Regiões binárias no `.exe` | 171 | 280 |
| Regiões nas DLLs | 0 | 4 |

Cobertura textual efetiva: **225/225 = 100%** do que existe e é traduzível no
inventário. Sobre o inventário inteiro: **225/227 = 99,1%** (as 2 ausentes não existem
no binário e não aparecem).

## 2. Strings novas (92)

### 2.1 Descrições de configuração no `renut.exe` (21)

VÍDEO (18): renderizador, resolução, campo de visão, horário, resolução de sombra,
suavidade de sombra, filtro anisotrópico, oclusão ambiente, reflexos, distância de
detalhe, distância de capim, profundidade de campo, bloom, MSAA, cortes suaves,
antisserrilhamento, V-Sync e limite de FPS.

CONTROLES (3): sensibilidade do mouse, inverter Y e “só jogador 1”.

Todas foram encurtadas para caber no comprimento original. Isso evita o corte no meio
de palavra que a versão 0.8.0 apresentava na oclusão ambiente.

### 2.2 Descrições fornecidas por DLLs (2)

| Texto | Arquivo | Método |
|---|---|---|
| `Fullscreen` | `rexui.dll` | in-place 10 → 10 bytes (`TELA CHEIA`) |
| `Input drivers in priority order, comma separated` | `rexhid.dll` | in-place 48 → 43 bytes (`Drivers de entrada por prioridade, vírgula`) |

As DLLs originais não são alteradas; o patch é aplicado em cópias dentro da pasta de
destino.

### 2.3 Seletores nativos em UTF-16 (8)

| Texto | Tradução | Onde |
|---|---|---|
| Choose a folder | Escolha uma pasta | PASTA JOGO/UPDATE/SAVE |
| Choose the game disc's image | Escolha a imagem do disco | EXTRAIR DISCO |
| Choose Title Update #3 (the TU_... file) | Escolha a Atualização #3 (TU_...) | EXTRAIR ATUALIZAÇÃO |
| Choose a screenshot of the vehicle | Escolha uma captura do veículo | COMPARTILHAR |
| Choose the DLC package | Escolha o pacote DLC | ADICIONAR DLC |
| Disc images (*.iso) | Imagens (*.iso) | filtro do ISO |
| All files | Todos | filtro geral |
| Pictures (*.png, *.jpg) | Imagens (*.png, *.jpg) | filtro da captura |

Os títulos são exibidos com espaços de preenchimento à direita quando a tradução é
mais curta; isso é invisível na janela e não corta o texto.

### 2.4 Mensagens do extrator, do atualizador e da oficina (58)

- **Extrator** (`game_setup.cpp`): disco cheio, arquivo danificado, pasta sem
  permissão, ISO que não é GDFX, ISO sem `default.xex`, disco de outro jogo/região,
  pacote inválido, pacote de outro jogo, pacote que não é atualização, atualização de
  outra região, atualização que não é #3, pasta de update igual à do jogo,
  atualização ilegível, atualização sem `default.xexp`, DLC duplicado, DLC inválido,
  pacotes múltiplos, sucesso da extração/atualização/DLC e cancelamento.
- **Atualizador** (`updater.cpp`): GitHub respondeu, download interrompido, gravação
  impossível, zip ilegível/fora da pasta/danificado, mover/colocar em uso, sem
  conexão, resposta ilegível, nenhuma release, sem download para o sistema.
- **Oficina** (`workshop.cpp`): captura ilegível/grande demais, lista ilegível,
  download incompleto, gravação no save, cabeçalho do veículo, veículo danificado,
  nome vazio, captura ausente e veículo grande demais.

### 2.5 Valores de exibição (3)

| Texto | Tradução | Método |
|---|---|---|
| `ON` | `SIM` | realocado; `ON` é o final de `VIOLATION`, então só a referência RIP de `SettingValue` é atualizada |
| `OFF` | `NÃO` | realocado; a referência da função de configuração é filtrada para não afetar o decodificador de imagens |
| `NONE` | `NADA` | imediato de código em dois sítios (`0x454E4F4E` → `0x4144414E`) |

O valor booleano gravado continua `true`/`false`; apenas o texto exibido muda.

## 3. Strings do código ausentes do binário

| ID | Texto | Motivo |
|---|---|---|
| `status.needed` | `NEEDED` | não existe como literal no `renut.exe` instalado; o estado “falta” não é exibido por esse texto |
| `workshop.took_prefix` | `Took ` | não existe como literal; a remoção de veículo é montada de outra forma no binário |

As duas ficam registradas como **ausentes**, não como traduzidas.

## 4. Strings no binário fora do catálogo

Classificadas como valores técnicos, nomes de teclas, nomes protegidos ou conteúdo
externo. As principais:

- Valores: `D3D12`, `4K`, `150%`, `GAME`, `HIGH`, `OFF`, `RESOL.`, `16X`, `8X`, `MAX`,
  `SMAA`, `SDL3`, `1.00`.
- Teclas: `W`, `S`, `A`, `D`, `Q`, `E`, `ESC`, `TAB`, `UP`, `DOWN`, `LEFT`, `RIGHT`,
  `SPACE`, `LMB`, `RMB`, `C`, `V`, `F`.
- Nomes/chaves: `renut_mouse_camera`, `renut_resolution`, `default.xex`,
  `default.xexp`, `TU_...`.
- Nomes de mundos/fases protegidos.
- Nomes e descrições de veículos da oficina e capturas.
- Botões e rótulos internos das janelas do Windows.

Nenhuma ocorrência visível nas telas percorridas ficou sem classificação.

## 5. Strings montadas em tempo de execução

- `SettingValue`: escolhe `SIM`/`NÃO`, `NADA`, formata número com duas casas ou aplica
  maiúsculas ao valor da configuração.
- `DrawUpdate`: concatena `BAIXANDO `, `INSTALANDO `, `ATUALIZADO `, `ERRO NO UPDATE: `
  e o nome da release.
- `game_setup`: concatena `Não foi possível gravar ` + caminho + ` (o disco está
  cheio?).`; `Esse é o ` + nome + `; o reNut roda na Atualização de Título #3.`
- `workshop`: concatena nome do veículo + ` está nos seus veículos…` e mensagens de
  status.
- `progress`: formata `{}  {}%  ({} de {})`.

Os fragmentos foram traduzidos; a ordem gramatical foi conferida nas telas de
progresso/sucesso e nas mensagens de estado vazio.

## 6. Tabela de falhas da versão anterior

| Texto original | Tela | Causa de não tradução | Solução aplicada | Resultado visual |
|---|---|---|---|---|
| Fullscreen (descrição) | VÍDEO | vinha de `rexui.dll`; o patch 0.8.0 só cobria o `.exe` | patch in-place em cópia da DLL | PASS (`TELA CHEIA`) |
| Input drivers… | CONTROLES | vinha de `rexhid.dll` | patch in-place em cópia da DLL | PASS |
| Renderer backend… | VÍDEO | ajuda não catalogada | nova entrada, no mesmo espaço | PASS |
| Internal render resolution… | VÍDEO | idem | nova entrada | PASS |
| Field of view… | VÍDEO | idem | nova entrada | PASS |
| Showdown Town's time of day… | VÍDEO | idem | nova entrada (nome protegido mantido) | PASS |
| Shadow map / softness… | VÍDEO | idem | nova entrada | PASS |
| Anisotropic / SSAO / reflections… | VÍDEO | idem | nova entrada; texto encurtado | PASS |
| Detail / grass / DOF / bloom / MSAA / cut-outs / AA / V-Sync / FPS | VÍDEO | idem | novas entradas | PASS |
| How far the camera turns… | CONTROLES | ajuda não catalogada | nova entrada | PASS |
| Moving the mouse up looks down… | CONTROLES | idem | nova entrada | PASS |
| Only player 1… | CONTROLES | idem | nova entrada | PASS |
| `ON` / `OFF` | VÍDEO/CONTROLES | imediatos/pooling, sem literal NUL | realocação com referência filtrada | PASS (`SIM`/`NÃO`) |
| `NONE` | COMPARTILHAR / tecla vazia | imediato de código | `NADA` nos dois sítios | PASS |
| Choose a folder… | seletores | UTF-16 não varrido | patch UTF-16 | PASS |
| Choose the game disc's image… | seletor de ISO | UTF-16 | patch UTF-16 | PASS |
| Choose Title Update #3… | seletor de update | UTF-16 | patch UTF-16 | PASS |
| Disc images / All files / Pictures | filtros | UTF-16 | patch UTF-16 | PASS |
| Can't write / read / make… | extração | `game_setup.cpp` fora do catálogo | novas entradas | PASS (texto) / erro sintético NOT_TESTED |
| That is not an Xbox 360… | extração | idem | novas entradas | PASS (texto) / NOT_TESTED |
| GitHub answered / download… | atualização | `updater.cpp` fora do catálogo | novas entradas | NOT_TESTED |
| The workshop answered… | oficina | `workshop.cpp` fora do catálogo | novas entradas | PASS (texto) / rede BLOCKED |
| D-PAD ESQUE / DIREIT | CONTROLES | ajuda lida com comprimento fixo | tradução encurtada | PASS (`ESQUERDA`/`DIREITA`) |
| Oclusão… “na resoluç” | VÍDEO | realocação com comprimento fixo | tradução no mesmo espaço | PASS (texto completo) |

## 7. Conclusão da auditoria

A versão 0.8.0 não era 100% porque o catálogo era uma lista de conveniência, não um
inventário fechado: faltavam módulos, DLLs, UTF-16, imediatos e comprimentos fixos. A
0.9.0 fecha o inventário do que o launcher exibe e classifica o que fica de fora. A
cobertura textual efetiva é 100%; a cobertura visual continua com estados BLOCKED e
NOT_TESTED, registrados em `matriz-visual.json` e no relatório 0.9.0.