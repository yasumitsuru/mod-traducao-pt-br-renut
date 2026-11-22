# MOD tradução PT-BR para o RENUT

Tradução de **Banjo-Kazooie: Nuts & Bolts** para português brasileiro, destinada à versão de PC
executada pelo projeto [reNut](https://github.com/masterspike52/reNut).

Esta é a versão **0.7.0**, com **100% de cobertura textual do catálogo**: 6.110 de 6.110 entradas
traduzíveis. O jogo em inglês contém 6.099 dessas entradas; as outras 11 são créditos que só existem
no arquivo em espanhol e ficam traduzidos no catálogo, sem entrar no pacote. O jogo continua com os
arquivos originais intactos.

> **A Release não traz um `.nbpatch` pronto para copiar.** O pacote do reNut carrega cópias dos
> arquivos de texto do jogo; distribuí-lo exigiria autorização dos titulares. Por isso a Release
> **v0.7.0** entrega um **gerador local**: ele monta o mesmo pacote validado a partir da sua cópia
> legítima do jogo. Os arquivos automáticos “Source code” do GitHub não são instaláveis.

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
* Python 3.11 ou mais recente, para executar o gerador.
* Idioma do jogo configurado para **English (1)**, conforme a compatibilidade testada nesta versão.

O mod **não inclui o jogo**. Nenhum arquivo original é distribuído aqui.

## Como baixar o gerador

1. Acesse a página da Release **v0.7.0**:
   <https://github.com/yasumitsuru/mod-traducao-pt-br-renut/releases/tag/v0.7.0>
2. Na seção **Assets**, baixe `reNut-Traducao-PTBR-v0.7.0-gerador.zip`.
3. Confira o SHA-256, se quiser:

```
certutil -hashfile reNut-Traducao-PTBR-v0.7.0-gerador.zip SHA256
```

4. Extraia o ZIP em uma pasta comum, por exemplo na Área de Trabalho.

O ZIP de código automático do GitHub não serve para instalar o mod.

## Como gerar o mod

1. Na pasta extraída, clique duas vezes em `GERAR_MOD.bat`.
2. Quando o programa pedir, informe a pasta do reNut que contém `game\extraido`.
3. Espere a mensagem `RESULTADO: PASS`. O gerador cria `saida\ptbr_traducao` com `mod.toml` e
   `ptbr_traducao.nbpatch`.
4. O SHA-256 esperado do `.nbpatch` é
   `7cd39a34efbae21dc8d3f919e63349e15df88397080ad59dd07207da0f5b5e25`. O gerador confere esse valor
   e avisa se a sua cópia do jogo for de outra versão.

Alternativa pelo terminal:

```
python gerar_mod.py --jogo "C:\caminho\da\instalacao\do\reNut"
```

## Como instalar

1. Copie a pasta `ptbr_traducao` inteira para a pasta `mods` da sua instalação do reNut.
2. Confira que `mod.toml` e `ptbr_traducao.nbpatch` estão dentro dessa pasta, sem uma subpasta
   duplicada.
3. Abra o reNut.
4. Configure o idioma do jogo para **English (1)**.
5. Abra o menu de mods com **F9** e confirme que a tradução está habilitada.
6. Reinicie o jogo, se necessário, para aplicar os recursos do mod.
7. Inicie o jogo normalmente.

## Por que não há um ZIP instalável pronto

A auditoria do pacote 0.7.0 comparou os 107 arquivos internos com a instalação do jogo. Trinta e um
são byte-idênticos aos originais; os outros 76 são os contêineres completos do jogo com as frases
traduzidas. O formato do reNut não é diferencial: publicar o `.nbpatch` seria redistribuir material
da Rare e da Microsoft. Como não há autorização documentada para isso, a Release publica o gerador
e mantém o binário fora do GitHub. Se essa autorização existir no futuro, um ZIP pronto poderá ser
publicado em outra versão, com o mesmo teste de hash.

## Como desativar

Abra o menu de mods com **F9**, desabilite a tradução e reinicie o jogo. Sem o mod, o jogo volta ao
texto original em inglês. Também é possível remover a pasta `ptbr_traducao` da pasta `mods`.

## Manutenção

* `data/traducao/` guarda a fonte da verdade da tradução: identificador, chave, hash do original e
  texto em português.
* `data/lotes/` registra os lotes aplicados; `data/glossario.csv` e `data/nomes-protegidos.csv`
  definem termos e nomes que não podem mudar.
* `tools/` contém o leitor e gravador do formato, o validador, o gerador local e o empacotador.
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
