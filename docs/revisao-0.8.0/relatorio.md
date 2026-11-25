# Relatório da revisão 0.8.0 — tradução PT-BR do jogo

Revisão integral da tradução brasileira de **Banjo-Kazooie: Nuts & Bolts** executado pelo reNut,
feita sobre o catálogo da versão 0.7.0. A 0.8.0 é uma **versão de desenvolvimento**: não há Release
nem tag. A Release **v0.7.0** continua publicada e intacta.

Escopo exclusivo: texto do jogo (`loctext`). O launcher do reNut (patch 0.9.0) e o instalador gráfico
**não** foram alterados, e nada mudou em temporizadores, velocidade ou sequência de diálogos.

Documentos desta revisão:

| Documento | Conteúdo |
|---|---|
| `guia-de-revisao.md` | regras, estilo dos personagens, gravidade e formato das propostas |
| `alteracoes.md` | lista completa das alterações (ID, chave, categoria, personagem, gravidade, tipo, trecho curto do original, antes, depois, motivo, status) |
| `dialogos-por-personagem.md` | correções de diálogo agrupadas por personagem e por mundo |
| `pendencias.md` | decisões ambíguas mantidas, falas longas para o futuro mod de diálogo manual e propostas de glossário |

O texto original do jogo não é publicado: os documentos trazem só o PT-BR, os IDs e trechos curtos
(até 40 caracteres) do inglês.

## Método

1. **Auditoria automática** das 6.110 entradas (`python -I tools/ptbr.py auditar`): integridade do
   catálogo (IDs, chaves, hash do original, entradas obsoletas ou ausentes), códigos e marcadores,
   inglês remanescente, português europeu, crase e concordância frequentes, palavras repetidas,
   pontuação, números, espaço em volta dos ícones, caracteres suspeitos, comprimento de rótulos e falas
   e originais iguais traduzidos de formas diferentes.
2. **Revisão linguística e contextual de todas as entradas** por cinco frentes independentes (G1
   Showdown Town, Spiral Mountain e história; G2 Nutty Acres e Banjoland; G3 LOGBOX 720, Jiggosseum e
   Terrarium of Terror; G4 menus, HUD, multijogador e créditos; G5 desafios, veículos, peças e
   garagem), com o inglês como fonte e o espanhol oficial como referência. Por causa do limite de uso
   da conta, o trabalho foi dividido em 19 fatias menores; cada uma entregou um arquivo de propostas
   conferido por `checar-propostas` (catálogo atual, códigos, fonte, nomes protegidos).
3. **Consolidação e revisão do orquestrador**: propostas transformadas em lotes rastreáveis, com
   ajustes pontuais (inversões forçadas em rimas), uma proposta recusada e duas rodadas de
   consistência (grafia do Klungo; nomes entre rótulos, explicações e falas).
4. **Revisão independente** de cada correção contra o original, por revisores que não participaram
   das correções, seguida de um lote com os achados.
5. **Regeneração do pacote** por dois caminhos (`empacotar` e o gerador local), comparação frase a
   frase com a 0.7.0, leitura e reinserção, testes automatizados e teste visual numa cópia isolada.

## Lotes aplicados

| Lote | Conteúdo | Frases |
|---|---|---|
| 610 | G1 — Showdown Town, Spiral Mountain e história | 102 |
| 611 | G2 — Nutty Acres e Banjoland | 87 |
| 612 | G3 — LOGBOX 720, Jiggosseum e Terrarium of Terror | 60 |
| 613 | G4 — menus, HUD, multijogador e créditos | 109 |
| 614 | G5 — desafios, veículos, peças e garagem | 40 |
| 615 | achados da revisão independente | 14 |
| 616 | consistência: grafia do Klungo ("Urssso") | 50 |
| 617 | consistência: nomes entre rótulos, explicações e falas | 4 |
| 618 | ajuste final apontado pela auditoria pós-revisão | 1 |

Total: **467 aplicações** em **448 entradas** distintas (algumas entradas receberam um ajuste posterior;
duas voltaram ao texto 0.7.0 por decisão da revisão independente).

## Resultado (itens obrigatórios)

| # | Item | Resultado |
|---|---|---|
| 1 | Entradas auditadas | **6.110 de 6.110** (auditoria automática e revisão linguística de todas) |
| 2 | Traduções consideradas corretas | **5.662** (sem alteração líquida) |
| 3 | Traduções corrigidas | **448** entradas (467 aplicações) |
| 4 | Problemas críticos | **0** CRITICAL; 25 HIGH, 215 MEDIUM, 208 LOW (gravidade da primeira correção de cada entrada) |
| 5 | Problemas gramaticais | **45** entradas (56 aplicações) |
| 6 | Problemas contextuais | **74** entradas (57 de tradução/sentido + 17 de contexto) |
| 7 | Correções de diálogos | **257** (mais 26 do quiz e 6 de placas informativas) |
| 8 | Correções de menus | **99** (27 de menus + 72 do multijogador) |
| 9 | Correções de HUD | **2** |
| 10 | Correções terminológicas | **67** entradas (69 aplicações) |
| 11 | Problemas técnicos encontrados | **0** de integridade (IDs, chaves, hash, obsoletas, ausentes), **0** códigos danificados, **0** caracteres fora da fonte, **0** variantes de nomes protegidos; 1 `&quot;` perdido numa piada foi restaurado |
| 12 | Textos não traduzidos identificados | 89 idênticos ao inglês + 20 com palavras/trechos em inglês; todos analisados: nomes próprios, títulos de jogos, marcas e respostas-trocadilho mantidos com justificativa (96 entradas "mantidas com achado"); corrigidos "Save corrompido", "Muddy X-115 Beta" e espanholismos ("Chirivia", "Bici", "gordito", "flechas") |
| 13 | Entradas inalteradas | **5.662** |
| 14 | Lista completa das alterações | `alteracoes.md` |
| 15 | Comparação anterior × corrigida | `alteracoes.md` (antes/depois) e a comparação de pacotes abaixo |
| 16 | Testes automatizados | `pytest`: 146 passam, 1 pulado; o teste da árvore pública só passa depois de `publicar.py atualizar` (feito na publicação); `validar` PASS (0 erros); `auditar-nomes` 0 violações |
| 17 | Geração do `.nbpatch` | **PASS** — 107 arquivos (`Kind=new`), 6.099 frases, 1.145.999 bytes; `empacotar` e o gerador local produzem o mesmo arquivo byte a byte |
| 18 | SHA-256 do pacote corrigido | **`d250b5959e7f0171355f9d6a3e1ac031e8c123dfb5fbfb0423beca538e20d8db`** (0.7.0: `7cd39a34efbae21dc8d3f919e63349e15df88397080ad59dd07207da0f5b5e25`) |
| 19 | Validação visual | **PARTIAL** — ver abaixo |
| 20 | Pendências e bloqueios | ver abaixo e `pendencias.md` |
| 21 | Revisão independente | **448 de 448** correções revisadas: 414 nas rodadas R1/R2 (401 ok, 11 ajustar, 2 reverter; achados aplicados no lote 615) + 36 na reconferência R3, que também revalidou os 14 ajustes aplicados depois (50/50 ok) — ver "Auditoria da contagem" |
| 22 | Commits sincronizados com o GitHub | registrados em `docs/progresso.md` após a publicação |
| 23 | Launcher e instalador | **não modificados** (hashes de `launcher-patch/`, `installer/`, `app/` e do instalador conferidos antes e depois) |
| 24 | Release | **nenhuma Release ou tag criada**; v0.7.0 intacta |

### Diálogos por personagem e mundo

Gruntilda (Grunty) 71 (sobretudo rimas refeitas que a tradução literal tinha perdido), Klungo 67
(50 da unificação "Urssso" e 17 de voz/gramática), Humba 15 e Mumbo 14 (infinitivos devolvidos à fala
quebrada), Jinjos 14, Capitão Blubber 8 (fala de pirata), Tomás Troféu 8, Bottles 7, Kazooie 6, Banjo 6,
S.J. 5, Sr. Em Forma 5, outros NPCs 13 e 18 sem personagem identificável com segurança.

Por mundo: Nutty Acres 66, Banjoland 48, Spiral Mountain 37, LOGBOX 720 29, Jiggosseum 29,
Showdown Town 21, Terrarium of Terror 19, sem mundo 8. Detalhes em `dialogos-por-personagem.md`.

### Decisões de terminologia (glossário)

Entraram no glossário: Peão de Fazenda (Farmhand; "jornaleiro" é vendedor de jornal), Sr. Costelas
(Mr. Ribs), Cara de Narigão (Snozz Face), Seta (não "flecha"), Coco Louco (Loco Coco), corrida com
barreiras (hurdles), Vaso de Planta, Hélice Falsa (Dummy Propeller), Flutuante (Hover; "planador" é
glider) e Bike (não "Bici"). A grafia do Klungo foi unificada em "Urssso". O quiz do S.J. deixou de
usar "L.O.G." (o glossário manda S.J.). Nenhum nome protegido foi alterado.

## Comparação do pacote com a 0.7.0

| | 0.7.0 | 0.8.0 |
|---|---|---|
| Arquivos | 107 | 107 |
| Frases aplicadas | 6.099 | 6.099 |
| Tamanho | 1.144.559 bytes | 1.145.999 bytes |
| SHA-256 | `7cd39a34…5e25` | `d250b595…d8db` |

* **56** arquivos de texto mudaram; os outros 51 ficaram byte a byte iguais.
* **448** frases mudaram, e são **exatamente** as entradas alteradas no catálogo (nenhuma mudança
  inesperada; `comparar.conferir_esperado` sem divergência); nenhuma chave, tabela ou estrutura mudou.
* Os 107 arquivos do pacote leem e regravam idênticos (ida e volta).
* As 11 entradas só do espanhol (créditos) foram revisadas e continuam fora do pacote inglês.

## Validação visual

Cópia isolada (`work/renut_teste-0.8.0`, jogo original só leitura, mod 0.8.0 com o SHA acima):

| Tela | Estado |
|---|---|
| Logotipos de abertura, título | PASS (sem texto) |
| Menu "UM JOGADOR", "INICIAR NOVO JOGO", "CONTINUAR JOGO SALVO", "SELECIONAR/VOLTAR", aviso de salvamento | PASS |
| Abertura da história em Spiral Mountain (narração em sépia), incluindo duas falas corrigidas na 0.8.0 | PASS — texto inteiro, acentos corretos, sem corte nem sobreposição |
| Diálogo seguinte (Kazooie na casa) | PASS no que apareceu |
| Mundos, desafios, garagem em uso, HUD de desafio, créditos finais, multijogador, cenas posteriores | **NOT_TESTED** — exigem save avançado; não há save de teste descartável no projeto |

A cobertura visual **não** é integral. A validação dessas áreas é textual (auditoria, revisão,
validador e comparação de pacotes).

## Pendências

* **Instalador fixado na 0.7.0** (decisão D24): o instalador gráfico continua conferindo o SHA da 0.7.0.
  O binário local já compilado embute o catálogo 0.7.0 e segue instalando a 0.7.0; recompilado com o
  catálogo revisado, ele recusa instalar até uma missão própria atualizar a referência. Para usar a
  0.8.0 hoje: `python -I tools/gerar_mod.py --jogo "<pasta do reNut>"` e copiar `ptbr_traducao` para
  `mods`.
* **Validação visual** dos mundos, desafios, garagem, créditos e multijogador (NOT_TESTED).
* **Decisões ambíguas mantidas** (55 registros em `pendencias.md`, quase todas de impacto baixo):
  trocadilhos difíceis (Hoedown Town, NO BODY, Recognize!, Rocket Luncher), gênero de NPCs não
  identificados, nomes sem forma oficial (Tanquetup, Mr. Patch, Nuvem Cucolândia), "a conservacionista
  sem-vergonha" (mooning) e o haiku do Jinjo vermelho. As pendências sobre a grafia do Klungo foram
  resolvidas pelo lote 616.
* **Tempo de leitura**: 62 falas longas registradas para o futuro mod de diálogo manual; nenhuma foi
  cortada à força e nenhum temporizador foi alterado.
* **Rótulos que cresceram** (a conferir na tela): "Confusão dos Monstros Malucos", "Iniciar sala de
  espera", "Vaso de Planta", "Bola Enferrujada", "Jogando uma partida privada do grupo".

## Auditoria da contagem 448 × 414 (2026-11-25)

A diferença de 34 entre as 448 entradas corrigidas e as 414 da revisão independente vem de:

* **36 entradas que não estavam nas planilhas R1/R2**: 35 frases do Klungo cuja única mudança foi a
  unificação mecânica "Ursso" → "Urssso" (lote 616) e o rótulo `114483e7[357c]`, incluído pela
  própria revisão independente no lote 615 para unificar "Sair para o menu principal";
* **2 entradas revisadas que voltaram ao texto 0.7.0** (`114483e7[938f]` e `[515a]`, revertidas pelo
  revisor R2) e por isso não contam como corrigidas.

412 + 36 = 448. A reconferência independente **R3** revisou essas 36 entradas e revalidou, depois de
aplicados, os 13 ajustes pedidos pelos revisores (lote 615), o rótulo 357c e o ajuste final do lote
618 (50 entradas): **50 ok, 0 ajustar, 0 reverter**. Um script confirmou que nas 35 frases do Klungo a
única diferença é a grafia, sem alteração acidental, e que os códigos batem com o original. Nenhuma
tradução aprovada foi alterada nesta etapa.

## Integração ao instalador (2026-11-25)

* O instalador gráfico passou a gerar e conferir o pacote **0.8.0** (`d250b595…d8db`), byte a byte
  igual ao do `empacotar` e do `tools/gerar_mod.py` (conferido contra a cópia real do jogo).
* Reconhece a **0.7.0** instalada (pelo SHA histórico `7cd39a34…5e25` e pelo manifesto que ele mesmo
  grava) e atualiza para a 0.8.0 sem remoção manual, numa transação que restaura a anterior se algo
  falhar.
* **Defeito encontrado e corrigido:** o launcher traduzido roda de `launcher-ptbr/` e o reNut procurava
  os mods nessa pasta; aberto pelo atalho, o jogo ficava em inglês. A cópia do launcher agora recebe
  `[renut] renut_mods_folder` apontando para a pasta `mods` da instalação, e instalar só a tradução do
  jogo repara instalações antigas. Confirmado na cópia isolada: "2 of 2 mods enabled in …\reNut\mods"
  e o jogo em PT-BR 0.8.0 pelo atalho.

## Validação visual (atualização de 2026-11-25)

| Tela | Estado |
|---|---|
| Abertura pelo atalho criado pelo instalador (launcher traduzido + mod 0.8.0) | PASS |
| Título com os textos legais corrigidos na 0.8.0, menu, abertura em sépia, diálogos de Banjo, Kazooie, Jamjars e Grunty, HUD/minimapa de Spiral Mountain | PASS — sem corte, acentos corretos |
| Mundos, desafios, garagem em uso, tutoriais avançados, créditos finais, multijogador | **NOT_TESTED** — os saves disponíveis são só um perfil, sem progresso; a jogabilidade não é automatizável com segurança |

A homologação visual **não** é integral.
