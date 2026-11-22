# MOD tradução PT-BR para o RENUT

Tradução de **Banjo-Kazooie: Nuts & Bolts** para português brasileiro, destinada à versão de PC
executada pelo projeto [reNut](https://github.com/masterspike52/reNut).

Esta é a versão **0.7.0**, com **100% de cobertura textual do catálogo**: 6.110 de 6.110 entradas
traduzíveis. O jogo em inglês contém 6.099 dessas entradas; as outras 11 são créditos que só existem
no arquivo em espanhol e ficam traduzidos no catálogo, sem entrar no pacote. O jogo continua com os
arquivos originais intactos.

## O que o mod traduz

* Menus e telas de configuração.
* Diálogos e falas dos personagens.
* Legendas e textos de apoio.
* Desafios, objetivos e tutoriais.
* HUD, avisos e mensagens do jogo.
* Nomes de peças e descrições de veículos.
* Créditos e demais textos traduzíveis do catálogo.

A cobertura de 100% se refere ao catálogo de textos traduzíveis. Os **nomes oficiais dos mapas e
mundos permanecem no idioma original** (Showdown Town, Spiral Mountain, Nutty Acres, Banjoland,
LOGBOX 720, Jiggosseum, Terrarium of Terror, Test-O-Track e Klungo's Arcade).

As telas principais foram conferidas em jogo. Desafios dentro dos mundos, garagem em uso, créditos
finais, multijogador e cenas posteriores foram validados pelo texto, mas **não foram percorridos
visualmente**; por isso não afirmamos homologação visual de todas as áreas.

## Requisitos

* Uma versão compatível do reNut.
* Instalação funcional de Banjo-Kazooie: Nuts & Bolts.
* Arquivos legítimos do jogo, fornecidos por você.
* Idioma do jogo configurado para **English (1)**, conforme a compatibilidade testada nesta versão.

O mod **não inclui o jogo**. Nenhum arquivo original é distribuído aqui.

## Como instalar

O repositório não distribui arquivos do jogo. O pacote é montado no seu computador, a partir da sua
própria instalação, com Python 3.11 ou mais recente.

1. Copie `config/caminhos.exemplo.toml` para `config/caminhos.toml` e ajuste os caminhos da sua
   instalação (o arquivo fica fora do Git).
2. Na raiz do projeto, execute:

```
python -I tools/ptbr.py extrair
python -I tools/ptbr.py reinserir
python -I tools/ptbr.py empacotar --versao 0.7.0
```

3. Copie a pasta `dist/ptbr_traducao` para a pasta `mods` da sua instalação do reNut.
4. Confira que `mod.toml` e `ptbr_traducao.nbpatch` estão dentro dessa pasta, sem uma subpasta
   duplicada.
5. Abra o reNut.
6. Configure o idioma do jogo para **English (1)** na interface de configuração.
7. Abra o menu de mods com **F9** e confirme que a tradução está habilitada.
8. Reinicie o jogo, se necessário, para aplicar os recursos do mod.
9. Inicie o jogo normalmente.

## Como desativar

Abra o menu de mods com **F9**, desabilite a tradução e reinicie o jogo. Sem o mod, o jogo volta ao
texto original em inglês. Também é possível remover a pasta `ptbr_traducao` da pasta `mods`.

## Manutenção

* `data/traducao/` guarda a fonte da verdade da tradução: identificador, chave, hash do original e
  texto em português.
* `data/lotes/` registra os lotes aplicados; `data/glossario.csv` e `data/nomes-protegidos.csv`
  definem termos e nomes que não podem mudar.
* `tools/` contém o leitor e gravador do formato, o validador e o empacotador.
* `tests/` contém os testes; rode `python -m pytest` na raiz.
* `docs/formato-loctext.md` descreve o formato dos arquivos de texto e
  `docs/manutencao.md` resume o fluxo de trabalho.

O teste `tests/test_privacidade.py` examina os arquivos rastreados e falha se encontrar caminhos
pessoais, e-mails, credenciais ou arquivos do jogo. Rode-o antes de cada envio. Para que ele bloqueie
commits automaticamente, ative o gancho com `git config core.hooksPath .githooks`.

## Créditos

**Tradução PT-BR:** [@yasumitsuru](https://github.com/yasumitsuru)

**Projeto reNut original:** [masterspike52/reNut](https://github.com/masterspike52/reNut)

Este é um projeto comunitário independente e não oficial, sem afiliação com a Rare, a Microsoft ou
os desenvolvedores do reNut. Banjo-Kazooie e seus personagens pertencem aos seus respectivos
titulares. O repositório não distribui arquivos do jogo.

O código-fonte das ferramentas e dos testes é distribuído sob a licença MIT. A tradução e o jogo
têm avisos próprios em `NOTICE.md`.
