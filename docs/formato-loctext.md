# Formato dos arquivos loctext (CAFF + LSBL)

Documento técnico. Tudo aqui foi verificado por leitura somente-leitura dos arquivos do jogo
extraído e confirmado pelo leitor/gravador em `tools/nbptbr/` com ida e volta byte a byte.

## Onde ficam os textos

| Idioma | Local (relativo a `game\extraido`) | Arquivos | Frases |
|---|---|---|---|
| 14 idiomas (czech … tradchinese) | `loctext\<idioma>\<hash>` | 107 cada | 6355 (latinos/cirílico) ou 6416 (ja/ko/zh) |
| inglês | `Debug\11\XX\YY\ZZ` (o hash quebrado em 4 pares; ex.: `Debug\11\02\6b\27` = `11026b27`) | 107 | 6416 |

* Os 107 nomes (hashes) são idênticos em todas as pastas e no `Debug\11`.
* As chaves de cada arquivo são iguais ao inglês, **exceto** `11606e97` (`aid_loctext_banjox_credits`):
  479 chaves nos idiomas latinos/cirílico contra 540 no inglês/ja/ko/zh.
* `Debug\db_index.txt` lista os 107 assets `aid_loctext_*` com o mesmo ID do inglês.
* A pasta `update\` do reNut tem bundles `aid_bundle_banjoxdlc_..._loctext_common_<idioma>` (formato
  xcompress, magic `0F F5 12 ED`), inclusive `spanish`. **Não se sabe** se eles sobrepõem os arquivos de
  `loctext\spanish` (ver "Pendências").

Correção dos fatos iniciais: **o texto é UTF-16 little-endian**, não big-endian. O contêiner
CAFF é big-endian; o asset LSBL dentro dele é little-endian. Não há compressão (LZX/zlib) nesses arquivos.

## 1. Contêiner CAFF `07.08.06.0036` (big-endian)

Subconjunto usado pelos 1605 arquivos loctext: **1 seção (`.data`) e 1 símbolo**.

### 1.1 Cabeçalho fixo (0x78 bytes)

| Offset | Tipo | Valor / significado |
|---|---|---|
| 0x00 | char[20] | `CAFF07.08.06.0036` + 3 bytes 0 |
| 0x14 | u32 | `0x78` (tamanho do cabeçalho fixo) |
| 0x18 | u32 | checksum (ver 1.4) |
| 0x1C | u32 | 1 (nº de símbolos) |
| 0x20 | u32 | 1 (nº de seções) |
| 0x24 | 36 B | zeros |
| 0x48 | u8[4] | `01 01 00 00` |
| 0x4C | u32 | tamanho da tabela de nomes de seção (6 = `.data\0`) |
| 0x50 | u32 | tamanho da área de informações (múltiplo de 4) |
| 0x54 | 12 B | zeros |
| 0x60 | u32 | tamanho da área de informações (repetido) |
| 0x64 | 20 B | zeros |

### 1.2 Área de informações (a partir de 0x78, empacotada, sem alinhamento interno)

```
u32 0
u8  4                      alinhamento da seção (2^4 = 16)
u32 0
u32 tamanho_da_secao
u32 0, u32 0, u32 0, u32 0
u32 tamanho_da_secao       (repetido)
char[6] ".data\0"          nomes de seção
u32 tamanho_nomes_simbolo  (inclui o \0)
u32 0
char[] nome_do_simbolo\0   ex.: "aid_loctext_banjox_tt_cpu_act3,1220524793,2.33"
u32 0, u32 1, u32 0, u32 tamanho_da_secao
u8  1, u8 4
zeros até alinhar a 4      (0 a 3 bytes)
```

O nome do símbolo é `<asset>,<id>,<versão>`. O asset é igual em todos os idiomas; o id muda por idioma.

### 1.3 Seção `.data`

Começa em `0x78 + tamanho_area_info` e vai até o fim do arquivo. Seu tamanho é sempre múltiplo de 16.

### 1.4 Checksum (0x18)

Algoritmo **desconhecido**, mas verificado nos 1605 arquivos que o cabeçalho fixo inteiro (inclusive o
checksum) é **função apenas do tamanho da área de informações** (0x50): arquivos diferentes com o mesmo
tamanho de área têm cabeçalhos idênticos byte a byte, independentemente do conteúdo da seção.

| área de info | checksum |
|---|---|
| 0x6C | 0x02634270 |
| 0x70 | 0x0E635E60 |
| 0x74 | 0x0A635A60 |
| 0x78 | 0x06635660 |
| 0x7C | 0x02635260 |
| 0x80 | 0x0E62AD90 |
| 0x84 | 0x0A62A990 |

Consequência: a tradução muda só a seção; a área de informações mantém o tamanho (o nome do asset não
muda) e o cabeçalho original continua válido. O gravador recusa qualquer alteração que mudaria o tamanho
da área de informações. Testados sem sucesso: CRC32 (várias variantes), Adler-32, FNV-1/1a, Jenkins e
somas/XOR rotacionados de bytes e palavras.

## 2. Seção `.data`: preâmbulo + LSBL

### 2.1 Preâmbulo (big-endian)

| Offset | Tipo | Significado |
|---|---|---|
| +0x00 | u32 | deslocamento do LSBL na seção (12 quando não há bloco de colisões) |
| +0x04 | u32 | deslocamento do bloco de colisões (0 = ausente; senão 12) |
| +0x08 | u16 | nº de entradas do bloco de colisões |
| +0x0A | u16 | 0 |

**Bloco de colisões** (só em 4 arquivos por idioma: `11132aff`, `114483e7`, `1169b65d`, `11fbc3ac`):
`n × [u32 deslocamento_do_nome][u16 hash_original][u16 hash_substituto]` seguido dos nomes ASCII com `\0`
(deslocamentos relativos ao início da seção). Lista chaves cujo hash colidiu com outra; na tabela de
chaves elas usam hashes pequenos (0, 1, 2, …). Ex.: `logquiz__question135answer1` (original `0xE09B`).
O LSBL vem logo depois, **sem alinhamento** (em `1169b65d` começa em endereço ímpar).

### 2.2 LSBL (little-endian)

```
"LSBL"
u32 0x1C        tamanho do cabeçalho
u32 4
u32 0x1C        deslocamento da tabela de frases
u32 d_chaves    deslocamento da tabela de chaves
u32 d_coment    deslocamento da tabela de comentários (0 = ausente)
u32 d_indice    deslocamento da tabela de índice (0 = ausente)
```

As tabelas são **contíguas**, nesta ordem: frases, chaves, [comentários], [índice].
Depois do LSBL, zeros até o tamanho da seção (múltiplo de 16 contado a partir do início da seção).

**Tabela de frases**
```
u32 tamanho        = 8 + 6·(n+1) + 2·total_unidades + 2
u32 n
(n+1) × [u16 hash][u32 deslocamento em unidades UTF-16]   ordenadas por hash crescente
        a última entrada é [0xFFFF][total_unidades]
textos UTF-16LE, cada um terminado por u16 0
u16 0              (sempre presente)
```

**Tabela de chaves**
```
u32 tamanho, u32 n
n × [u16 hash][u16 índice][u32 deslocamento do nome]      mesma ordem (por hash) da tabela de frases
nomes ASCII com \0, em ordem alfabética; índice = posição alfabética (1..n)
```

**Tabela de comentários** (11 arquivos por idioma): notas internas dos desenvolvedores em ASCII
(ex.: "; remove these once the code is committed - don't need to localise"). Entradas de 8 bytes ordenadas
por hash. Não é exibida ao jogador e é preservada byte a byte.

**Tabela de índice**: `u32 tamanho, u32 n, n × u16 hash` (uma permutação dos hashes). Ausente quando o
arquivo tem 1 a 3 chaves. Preservada byte a byte.

### 2.3 O que muda quando uma frase é traduzida

Só a tabela de frases é regerada. Em cascata são recalculados: `d_chaves`, `d_coment`, `d_indice`,
o preenchimento final da seção, o tamanho da seção (duas vezes na entrada de seção e uma no símbolo).
O cabeçalho fixo (com checksum), o preâmbulo, o bloco de colisões e as tabelas de chaves, comentários e
índice ficam idênticos.

## 3. Conteúdo das frases

* 6355 frases em espanhol, 317 vazias. Nenhum caractere de controle (< U+0020) nem quebra de linha literal.
* Códigos que precisam ser preservados (contagem no espanhol):

| Código | Ocorrências | Uso |
|---|---|---|
| `{MOODHAPPY}` `{MOODSAD}` `{MOODANGRY}` `{MOODDEFAULT}` | 376 / 293 / 41 / 5 | humor do personagem no diálogo |
| `{PAGEBREAK}` | 132 | quebra de página do balão |
| `%s` `%S` `%d` `%i` `%02d` | 158 / 6 / 8 / 2 / 6 | valores inseridos pelo jogo |
| `[A]` `[B]` `[X]` `[Y]` `[LT]` `[RT]` `[LS]` `[RS]` `[LSTICK]` `[RSTICK]` `[DPAD]` `[BACK]` `[START]` | — | ícones de botão |
| `<font color=[white]>` … `</font>`, `<br>`, `</br>`, `<ds>`, `</ds>`, `<div align="center">` … `</div>` | — | marcação |

* Caracteres não-ASCII no espanhol: `¡©¿ÁÉÑÓÚáéíñóúüő–’…™`.

## 4. Fonte (`xuifontcachefont\euro.sbp`)

* `precache_euro.ini` (UTF-16BE com BOM): 544 caracteres pré-carregados; inclui todos os do PT-BR
  (á à â ã é ê í ó ô õ ú ü ç e maiúsculas, º ª « » “ ” ‘ ’ – — …).
* `euro.sbp`: cabeçalho `01 01 22 04`, u16 BE com o nº de glyphs (33974) e registros de 10 bytes
  `[u16 código][u32 deslocamento][4 bytes de métricas]`; cada glyph é um fluxo zlib.
* Inventário gerado por `python -I tools/ptbr.py fonte` em `data/fonte_euro.json`.

## 5. Como reproduzir

```
python -I tools/ptbr.py roundtrip                 # 107 arquivos de espanhol, cópias em work/roundtrip
python -I tools/ptbr.py roundtrip --idioma todos  # 14 idiomas + inglês
python -I tools/ptbr.py info <caminho do arquivo>
.venv\Scripts\python -I -m pytest                 # ou: python -I -m unittest discover -s tests
```

Resultado registrado em 2026-11-19: espanhol 107/107 idênticos (6355 frases); todos os 14 idiomas e o
inglês 107/107 idênticos cada (1605 arquivos).

## Pendências

* Algoritmo do checksum (não bloqueia: o cabeçalho não muda).
* Algoritmo do hash de 16 bits das chaves (não bloqueia: as chaves não mudam).
* Se os bundles `update\…loctext_common_spanish` sobrepõem `loctext\spanish` no jogo — só o teste no
  jogo ou a análise desses bundles responde.
