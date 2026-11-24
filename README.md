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

## Revisão 0.8.0 (em desenvolvimento, sem Release)

A branch `main` traz a **revisão integral** da tradução do jogo: as 6.110 entradas foram auditadas e
revisadas (sentido, gramática, voz dos personagens, rimas da Grunty, terminologia e menus), e
**448 frases foram corrigidas**, sem alterar nomes protegidos, códigos ou a estrutura dos arquivos.
O relatório completo, a lista de alterações e as pendências estão em `docs/revisao-0.8.0/`.

A 0.8.0 ainda **não tem Release**. A Release **v0.7.0** continua sendo o pacote estável publicado. Quem
quiser testar a revisão pode gerar o pacote a partir do código da `main`, com Python 3.11+:

```
python -I tools/gerar_mod.py --jogo "C:\caminho\da\instalacao\do\reNut"
```

O SHA-256 esperado do `.nbpatch` 0.8.0 é
`d250b5959e7f0171355f9d6a3e1ac031e8c123dfb5fbfb0423beca538e20d8db`. A validação visual da 0.8.0 cobriu o
menu e a abertura da história; mundos, desafios, créditos e multijogador foram conferidos pelo texto.

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

## Launcher do reNut (prévia 0.9.0, não lançada)

O repositório também publica o código, o catálogo e a documentação da tradução da interface do
launcher original do reNut. O patch binário **não é distribuído**: o reNut não possui licença formal
que autorize redistribuir binários modificados. O gerador `launcher-patch/gerar_patch.py` cria o
patch na sua máquina a partir da sua cópia legítima do reNut `big-lua-energy` (0.11.21); o aplicador
confere o SHA-256 antes e depois de gravar.

- Cobertura textual: 225/225 entradas do executável + 2 descrições em DLLs.
- Cobertura visual: 14 PASS, 1 PARTIAL, 1 BLOCKED e 6 NOT_TESTED; **não é 100%**.
- O `renut.exe` e as DLLs originais nunca são alterados; o patch é aplicado em cópias.
- Instruções: `launcher-patch/LEIA-ME.md`; limites em `docs/relatorio-launcher-0.9.0.md`.

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
4. O SHA-256 esperado do `.nbpatch` gerado pela Release v0.7.0 é
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
* `launcher-patch/` contém o catálogo, o gerador, o aplicador e a documentação do launcher; o
  patch binário é gerado localmente e não entra no repositório.
* `tests/` contém os testes; rode `python -m pytest` na raiz.
* `docs/formato-loctext.md` descreve o formato dos arquivos de texto e
  `docs/manutencao.md` resume o fluxo de trabalho.
* `AGENTS.md` fixa a política permanente; `docs/politica-publicacao.md` explica o fluxo e as
  verificações.

Os testes `tests/test_privacidade.py` e `tests/test_seguranca.py` examinam os arquivos rastreados e
falham se encontrarem caminhos pessoais, e-mails, credenciais ou arquivos do jogo. Antes de cada
envio, rode `python -m pytest` e `python -I tools/verificar_privacidade.py --publico`. Para bloquear
commits e pushes automaticamente, ative os ganchos com `git config core.hooksPath .githooks`.

## Sincronização e segurança

A branch `main` recebe apenas conteúdo auditado. A política permanente está em `AGENTS.md`; o fluxo,
os testes e os ganchos estão em `docs/politica-publicacao.md`. O histórico privado de desenvolvimento
não é publicado, e Releases ou tags exigem autorização explícita. O workflow do GitHub Actions roda
os testes e o Gitleaks em cada push e pull request.

## Créditos

**Tradução PT-BR:** [@yasumitsuru](https://github.com/yasumitsuru)

**Projeto reNut original:** [masterspike52/reNut](https://github.com/masterspike52/reNut)

Este é um projeto comunitário independente e não oficial, sem afiliação com a Rare, a Microsoft ou
os desenvolvedores do reNut. Banjo-Kazooie e seus personagens pertencem aos seus respectivos
titulares. O repositório não distribui arquivos do jogo.

O código-fonte das ferramentas e dos testes é distribuído sob a licença MIT. A tradução e o jogo
têm avisos próprios em `NOTICE.md`.
