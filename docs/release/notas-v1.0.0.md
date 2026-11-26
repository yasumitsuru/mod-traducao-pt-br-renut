## Novidades

- **Tradução revisada do jogo v0.8.0**: as 6.110 entradas foram auditadas e revisadas; 448 frases
  corrigidas (rimas da Gruntilda, fala de Humba, Mumbo e Klungo, sentido, gramática, terminologia e
  menus), com revisão independente.
- **Tradução do launcher original do reNut v0.9.0**: menus, opções, descrições e mensagens em PT-BR,
  aplicados numa cópia do launcher.
- **Instalador gráfico integrado**, portátil e em português, sem Python nem Rust e sem internet.
- **Atualização automática** de instalações anteriores (tradução v0.7.0).
- **Atalho na área de trabalho** que abre o launcher traduzido com a tradução do jogo carregada.
- **Instalação e remoção independentes** de cada componente, com verificação de SHA-256 e rollback.
- **Perfil do launcher traduzido preservado** na reinstalação e na remoção; instalação e remoção
  recusam com segurança se o jogo ou o launcher estiver aberto.

## Como instalar

1. Baixe `Instalador-reNut-PTBR-v1.0.0.exe` abaixo.
2. Execute o instalador (não precisa de administrador).
3. Clique em **PROCURAR...** e selecione a pasta raiz do reNut (a que contém o `renut.exe`).
4. Marque a tradução do jogo, a tradução do launcher e o atalho, como preferir.
5. Clique em **INSTALAR COMPONENTES SELECIONADOS**.
6. Use o atalho **Banjo-Kazooie Nuts & Bolts — PT-BR** da área de trabalho e clique em **JOGAR**.

O mod já fica habilitado (não é preciso usar o F9). Se abrir o jogo pelo `renut.exe` original, escolha
**English (1)** nas opções: é o idioma interno usado pela tradução.

## Compatibilidade

- **Tradução do jogo:** gerada a partir da sua cópia extraída do jogo; o instalador só instala o
  pacote se ele bater com o SHA-256 `d250b5959e7f0171355f9d6a3e1ac031e8c123dfb5fbfb0423beca538e20d8db`.
- **Tradução do launcher:** somente reNut **`big-lua-energy` 0.11.21** (`renut.exe`, `rexui.dll` e
  `rexhid.dll` originais, conferidos por SHA-256). Com outra versão, a opção fica bloqueada e o mod do
  jogo continua instalável.
- Windows 10/11 x86-64.

## Limitações conhecidas

- **Cobertura visual parcial:** título, menu, abertura, diálogos e HUD de Spiral Mountain foram
  conferidos na tela (inclusive pelo atalho). Mundos, desafios, garagem em uso, créditos finais e
  multijogador foram revisados pelo texto, mas não percorridos visualmente.
- **Diálogos que avançam sozinhos:** algumas falas podem passar rápido para a leitura. O avanço
  manual pelo botão A ainda **não** existe e está planejado para uma versão futura.
- O launcher tem estados visuais ainda PARTIAL, BLOCKED e NOT_TESTED em algumas telas.
- **Atualização automática do reNut:** ao abrir, o reNut 0.11.21 instala sozinho a versão nova
  publicada no GitHub. Nos testes, a cópia traduzida recebeu as DLLs novas e continuou abrindo em
  PT-BR, com o jogo carregando a tradução 0.8.0, mas essa combinação não é homologada e as duas
  descrições das DLLs voltam ao inglês. Se o `renut.exe` original se atualizar, a tradução do
  launcher fica bloqueada no instalador (a tradução do jogo continua instalável, sem teste com a
  versão nova do reNut).
- O instalador não tem assinatura digital; o Windows SmartScreen pode avisar.
- O launcher traduzido tem um perfil do guia próprio (conta e conquistas) em
  `launcher-ptbr/guide`, separado do perfil do `renut.exe` original. Os saves são os mesmos.
- Onze entradas dos créditos existem só no arquivo em espanhol do jogo e não aparecem no inglês.

## Segurança

- Os arquivos da tradução são **gerados localmente** a partir da sua instalação legítima e conferidos
  por SHA-256. A distribuição **não acompanha o jogo**, o reNut, executáveis ou DLLs traduzidos, nem o
  pacote `.nbpatch`.
- O instalador não baixa nada e não envia dados. O `renut.exe`, as DLLs originais, os saves, os
  perfis e outros mods não são alterados.
- Confira o download com `SHA256SUMS.txt`.

## Créditos

- Tradução PT-BR: [@yasumitsuru](https://github.com/yasumitsuru)
- Projeto reNut original: [masterspike52/reNut](https://github.com/masterspike52/reNut)

Projeto comunitário independente e **não oficial**, sem afiliação com a Rare, a Microsoft ou os
desenvolvedores do reNut, e não endossado por eles. Banjo-Kazooie e seus personagens pertencem aos
seus respectivos titulares. As licenças das bibliotecas do instalador estão em
`LICENCAS-TERCEIROS.txt`.
