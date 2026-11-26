# MOD tradução PT-BR para o RENUT

Tradução de **Banjo-Kazooie: Nuts & Bolts** para português brasileiro, destinada à versão de PC
executada pelo projeto [reNut](https://github.com/masterspike52/reNut).

A **distribuição v1.0.0** reúne num único **instalador gráfico portátil**:

| Componente | Versão |
|---|---|
| Distribuição integrada | 1.0.0 |
| Tradução PT-BR do jogo | 0.8.0 (revisão integral das 6.110 entradas) |
| Tradução PT-BR do launcher original do reNut | 0.9.0 |
| Instalador gráfico | 1.0.0 |

> **Nada do jogo nem do reNut acompanha o instalador.** O pacote da tradução do jogo e a cópia
> traduzida do launcher são **gerados no seu computador**, a partir da sua instalação legítima, e
> conferidos por SHA-256 antes de serem gravados. Os arquivos originais nunca são alterados.

## Funcionalidades

* Tradução de menus, diálogos, legendas, desafios, objetivos, tutoriais, HUD, peças de veículos e
  créditos do jogo (cobertura textual de 100% do catálogo: 6.110 de 6.110 entradas).
* Revisão 0.8.0: 448 frases corrigidas em relação à v0.7.0 (sentido, gramática, rimas da Gruntilda,
  fala de Humba, Mumbo e Klungo, terminologia e menus), com revisão independente.
* Tradução da interface do launcher original do reNut (menus, opções, descrições e mensagens),
  aplicada numa **cópia** do executável e de duas DLLs.
* Instalador em português, sem Python nem Rust, funcionando offline: escolhe a pasta do reNut, detecta
  o que está instalado, instala ou remove cada componente, cria o atalho na área de trabalho, atualiza
  a v0.7.0 automaticamente e desfaz tudo se algo falhar.

Os **nomes oficiais dos mapas e mundos permanecem no idioma original** (Showdown Town, Spiral
Mountain, Nutty Acres, Banjoland, LOGBOX 720, Jiggosseum, Terrarium of Terror, Test-O-Track e
Klungo's Arcade).

## Download

Página da Release: <https://github.com/yasumitsuru/mod-traducao-pt-br-renut/releases/tag/v1.0.0>

Baixe na seção **Assets**:

* `Instalador-reNut-PTBR-v1.0.0.exe` — o instalador.
* `SHA256SUMS.txt` — os hashes para conferência.
* `LEIA-ME.txt` e `LICENCAS-TERCEIROS.txt` — instruções e licenças das bibliotecas usadas.

Os arquivos automáticos “Source code (zip/tar.gz)” do GitHub são o código-fonte do projeto e **não**
instalam a tradução.

## Requisitos

* Windows 10 ou 11, 64 bits (x86-64).
* reNut instalado e com o jogo **já extraído** (a pasta que contém o `renut.exe`).
* Para a tradução do launcher: reNut **`big-lua-energy` 0.11.21**, com o `renut.exe`, a `rexui.dll`
  e a `rexhid.dll` originais dessa versão (conferidos por SHA-256).
* Sua cópia legítima de Banjo-Kazooie: Nuts & Bolts. O instalador **não inclui o jogo**.

## Instalação passo a passo

1. Baixe `Instalador-reNut-PTBR-v1.0.0.exe`.
2. Execute o instalador (não precisa de administrador; se o Windows SmartScreen avisar que o
   arquivo é desconhecido, confira o SHA-256 e escolha **Mais informações → Executar assim mesmo**).
3. Clique em **PROCURAR...**.
4. Selecione a **pasta raiz do reNut** (a que contém o `renut.exe`).
5. Escolha os componentes: **tradução do jogo**, **tradução do launcher** e **atalho**.
6. Clique em **INSTALAR COMPONENTES SELECIONADOS** e aguarde a conferência dos hashes.
7. Use o atalho **Banjo-Kazooie Nuts & Bolts — PT-BR** criado na área de trabalho, clique em
   **JOGAR** e jogue.

O instalador já habilita o mod em `mods.json`; não é preciso ativá-lo pelo menu **F9**. O launcher
traduzido define o idioma interno do jogo como **English (1)**, que é o idioma usado pela tradução.
Se você abrir o jogo pelo `renut.exe` original (sem o launcher traduzido), escolha **English (1)**
nas opções.

## Opções do instalador

| Opção | O que faz |
|---|---|
| Tradução do jogo | Gera o pacote 0.8.0 a partir da sua cópia do jogo e instala em `mods/ptbr_traducao`. |
| Tradução do launcher | Cria `launcher-ptbr/` com uma cópia traduzida do `renut.exe`, da `rexui.dll` e da `rexhid.dll` e aponta essa cópia para a pasta `mods` da instalação. |
| Atalho | Cria o atalho na área de trabalho (para o launcher traduzido, ou para o `renut.exe` original se só o mod estiver instalado). |

As três opções são independentes. A remoção também pode ser feita por componente.

## Compatibilidade com o reNut

* **Tradução do jogo:** é gerada a partir dos textos da sua cópia extraída; o instalador só instala
  o pacote se ele bater exatamente com o SHA-256 conferido
  (`d250b5959e7f0171355f9d6a3e1ac031e8c123dfb5fbfb0423beca538e20d8db`).
* **Tradução do launcher:** é um patch binário gerado localmente para **uma única versão** do reNut,
  `big-lua-energy` 0.11.21 (`renut.exe` com SHA-256 `b303e0b1…3fe7`). Com outra versão, a opção fica
  bloqueada e nada é aplicado à força.

## Atualização de versões anteriores

Se a tradução v0.7.0 estiver instalada, o instalador a reconhece e oferece atualizar para a 0.8.0
sem remover nada à mão: a pasta antiga é substituída de uma vez e volta se algo falhar. Instalações
anteriores do launcher traduzido recebem também a correção que faz o launcher carregar a tradução
(antes ele procurava os mods na própria pasta).

## Desinstalação

Abra o instalador, escolha a pasta do reNut, marque o que quer remover e clique em
**REMOVER SELECIONADOS**.
O instalador só apaga o que ele mesmo criou e conferiu: saves, perfis, outros mods, o `renut.exe` e
as DLLs originais ficam intactos.

## Limitações conhecidas

* **Cobertura visual parcial.** Foram conferidos na tela: título, menu, abertura, diálogos e HUD de
  Spiral Mountain, inclusive pelo atalho do launcher traduzido. Mundos, desafios, garagem em uso,
  créditos finais e multijogador foram revisados pelo texto, mas **não foram percorridos
  visualmente**. O launcher tem estados visuais PASS, PARTIAL, BLOCKED e NOT_TESTED.
* **Diálogos que avançam sozinhos.** Algumas falas passam rápido para a leitura em português; o
  avanço manual pelo botão A **não** faz parte desta versão.
* O launcher traduzido só existe para o reNut `big-lua-energy` 0.11.21.
* O instalador não tem assinatura digital; o Windows pode mostrar o aviso do SmartScreen.
* O launcher traduzido guarda um perfil do guia próprio (conta e conquistas) em
  `launcher-ptbr/guide`, separado do perfil do `renut.exe` original; os saves são os mesmos. Esse
  perfil é preservado na reinstalação e na remoção.
* Onze entradas dos créditos existem só no arquivo em espanhol do jogo; estão traduzidas no
  catálogo, mas não aparecem no arquivo inglês usado pela tradução.

## Solução de problemas

* **“Não encontrei o renut.exe nesta pasta.”** Escolha a pasta que contém o `renut.exe`, não as
  pastas `game` ou `mods`.
* **A tradução do jogo está indisponível.** Termine a extração do disco e da atualização no reNut e
  abra o instalador de novo.
* **O launcher está bloqueado.** Sua versão do reNut não é a `big-lua-energy` 0.11.21; o mod do jogo
  continua instalável.
* **O jogo abriu em inglês.** Use o atalho criado pelo instalador; se abrir pelo `renut.exe`
  original, escolha **English (1)** nas opções. Se você tinha o launcher traduzido de uma versão
  anterior do instalador, reinstale a tradução do jogo com esta versão.
* **A instalação falhou.** Nada fica pela metade: o instalador restaura o estado anterior. Feche o
  jogo e o reNut e tente de novo.
* **“... está em uso. Nada foi alterado.”** O jogo ou o launcher traduzido está aberto. Feche-o e
  repita a instalação ou a remoção.

## Segurança

* Os arquivos da tradução são gerados localmente a partir da sua instalação legítima; a distribuição
  não acompanha o jogo, o reNut, executáveis traduzidos, DLLs nem o pacote `.nbpatch`.
* O instalador não baixa nada, não envia dados e funciona offline.
* Antes de gravar, cada arquivo gerado é conferido por SHA-256; os originais nunca são escritos.

## Verificação de SHA-256

No PowerShell, na pasta onde você baixou os arquivos:

```
Get-FileHash .\Instalador-reNut-PTBR-v1.0.0.exe -Algorithm SHA256
```

O valor deve ser igual ao listado em `SHA256SUMS.txt` da Release.

## Código-fonte e compilação

O código do instalador está em `installer/` (Rust). Para compilar o mesmo executável:

```
powershell -ExecutionPolicy Bypass -File installer\build-portatil.ps1 -Versao 1.0.0
```

O catálogo da tradução fica em `data/traducao/`, os lotes de revisão em `data/lotes/`, o glossário
em `data/glossario.csv` e os nomes protegidos em `data/nomes-protegidos.csv`. O gerador em Python
(`tools/gerar_mod.py`) produz o mesmo pacote 0.8.0 que o instalador. O relatório da revisão está em
`docs/revisao-0.8.0/` e o histórico de versões em `CHANGELOG.md`.

A Release **v0.7.0** continua disponível com o gerador da versão anterior:
<https://github.com/yasumitsuru/mod-traducao-pt-br-renut/releases/tag/v0.7.0>

## Sincronização e segurança do repositório

A branch `main` recebe apenas conteúdo auditado. A política permanente está em `AGENTS.md`; o fluxo,
os testes e os ganchos estão em `docs/politica-publicacao.md`. O histórico privado de desenvolvimento
não é publicado, e Releases ou tags exigem autorização explícita. O workflow do GitHub Actions roda
os testes e o Gitleaks em cada push e pull request.

## Créditos

**Tradução PT-BR:** [@yasumitsuru](https://github.com/yasumitsuru)

**Projeto reNut original:** [masterspike52/reNut](https://github.com/masterspike52/reNut)

## Direitos autorais

Este é um projeto comunitário independente e **não oficial**, sem afiliação com a Rare, a Microsoft
ou os desenvolvedores do reNut, e não é endossado por eles. Banjo-Kazooie, seus personagens e o jogo
pertencem aos seus respectivos titulares. O repositório e a Release não distribuem arquivos do jogo
nem do reNut.

O código-fonte das ferramentas, dos testes e do instalador é distribuído sob a licença MIT. A
tradução e o jogo têm avisos próprios em `NOTICE.md`; as licenças das bibliotecas do instalador
estão em `LICENCAS-TERCEIROS.txt` (Release) e resumidas em `installer/LICENCAS-TERCEIROS.md`.
