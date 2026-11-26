# Histórico de versões

## v1.0.0 — distribuição integrada (2026-11-25)

Primeira distribuição com instalador gráfico. Componentes: tradução do jogo **0.8.0**, tradução do
launcher **0.9.0** e instalador **1.0.0**.

### Tradução do jogo v0.8.0

- Revisão integral das 6.110 entradas do catálogo, com auditoria automática e revisão linguística e
  contextual de todas as entradas.
- 448 correções em relação à v0.7.0 (5.662 frases mantidas), com revisão independente de todas elas.
- Melhorias linguísticas e contextuais: sentido, gramática, concordância, crase e pontuação.
- Revisão das características de fala dos personagens: infinitivos de Humba, Mumbo e Klungo, grafia
  "Urssso" do Klungo unificada, sarcasmo da Kazooie e fala de pirata do Capitão Blubber.
- Melhorias nas rimas da Gruntilda, refeitas onde a tradução literal as tinha perdido.
- Padronização terminológica (S.J. no quiz, Peão de Fazenda, Sr. Costelas, Coco Louco, setas,
  nomes de peças iguais aos rótulos da garagem) e glossário atualizado.
- Correções nos menus: caixa de frase nos rótulos do multijogador e comandos unificados.
- Nomes protegidos de fases e mundos preservados.
- Pacote `.nbpatch` 0.8.0: 107 arquivos, 6.099 frases, SHA-256
  `d250b5959e7f0171355f9d6a3e1ac031e8c123dfb5fbfb0423beca538e20d8db`, gerado localmente.

### Tradução do launcher v0.9.0

- Tradução do launcher original do reNut `big-lua-energy` 0.11.21.
- Tradução de menus, opções e descrições, incluindo mensagens em UTF-16 das janelas nativas.
- Tradução das duas descrições que vêm das DLLs `rexui.dll` e `rexhid.dll`.
- Aplicação reversível numa cópia (`launcher-ptbr/`), com verificação de integridade por SHA-256.
- O `renut.exe` e as DLLs originais são preservados.

### Instalador integrado v1.0.0

- Novo instalador gráfico portátil para Windows x86-64, em português, sem Python nem Rust, offline.
- Seleção da pasta raiz do reNut e detecção automática do que está instalado.
- Instalação independente da tradução do jogo, da tradução do launcher e do atalho.
- Tradução do jogo e do launcher geradas no computador do usuário a partir dos arquivos legítimos
  dele; nenhum arquivo do jogo, do reNut ou patch binário acompanha o instalador.
- Atualização automática da tradução v0.7.0 para a 0.8.0, sem remoção manual.
- Criação do atalho na área de trabalho.
- Verificação de integridade por SHA-256 antes de gravar.
- Reinstalação e remoção por componente, preservando saves, perfis, outros mods e originais.
- Rollback: se algo falha, o estado anterior é restaurado.
- Correção do carregamento de mods pelo launcher traduzido (ele procurava os mods na própria pasta).
- Perfil do guia do launcher traduzido (conta e conquistas em `launcher-ptbr/guide`) preservado na
  reinstalação e na remoção.
- Com o jogo ou o launcher aberto, instalação e remoção recusam antes de mudar qualquer coisa.
- Atalho gravado pela interface nativa do Windows: funciona em caminhos com qualquer caractere.
- Caixas de marcar visíveis no tema escuro.
- Compilação reproduzível (o mesmo código gera o mesmo SHA-256).
- Correções ortográficas nas mensagens do instalador.

## v0.7.0 (2026-11-22)

- Tradução de 100% do catálogo (6.110 de 6.110 entradas), entregue como gerador local do
  `.nbpatch` (SHA-256 `7cd39a34efbae21dc8d3f919e63349e15df88397080ad59dd07207da0f5b5e25`).
