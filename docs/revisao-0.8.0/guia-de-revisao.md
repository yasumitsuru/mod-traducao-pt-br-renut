# Guia da revisão 0.8.0 — tradução PT-BR do jogo

Referência única para quem revisa as 6.110 entradas do catálogo (`data/traducao`). Vale para as
cinco frentes de revisão, para o revisor independente e para a consolidação.

## Escopo

* Só o texto do jogo (`loctext`). O launcher do reNut (patch 0.9.0) e o instalador gráfico ficam
  **fora** e não são alterados.
* Não há mudança de temporizador, velocidade de diálogo ou sequência de falas. Fala longa demais
  para o tempo de exibição é **registrada** (`tempo_de_leitura`), não cortada à força.
* Fonte principal: **inglês**. O espanhol oficial serve para tirar dúvida de sentido e de espaço,
  nunca para substituir o inglês sem justificativa.

## Regra de ouro

Corrija quando houver **ganho claro**: sentido errado, gramática, concordância, contexto,
personagem descaracterizado, termo inconsistente, inglês remanescente, problema técnico. **Não
reescreva** uma tradução correta só por gosto. Não invente piada que o original não tem, nem
contexto que a entrada não mostra. Na dúvida com impacto narrativo, mantenha o texto atual e
registre a pendência com as alternativas.

## Regras fixas do projeto (não negociáveis nesta revisão)

1. **Nomes protegidos** (`data/nomes-protegidos.csv`): Showdown Town, Spiral Mountain, Nutty Acres,
   Banjoland, LOGBOX 720, Jiggosseum, Terrarium of Terror, Test-O-Track, Klungo's Arcade ficam
   exatamente assim, inclusive em MAIÚSCULAS quando o original estiver em maiúsculas. Traduza a frase
   em volta ("Volte para Spiral Mountain").
2. **Glossário** (`data/glossario.csv`): personagens mantêm o nome (Banjo, Kazooie, Mumbo, Humba,
   Klungo, Grunty/Gruntilda, Bottles, Boggy, Jamjars...); L.O.G. = **S.J.** (Senhor dos Jogos);
   Jiggy/Jiggies; Notas; Motores do Mumbo; Banco de Jiggies; Troféu T.T.; Tomás Troféu; Sr. Em Forma;
   Parafuso de Apertar; Plataforma de Teleporte; Projetos (blueprints); Engenhocas; Chassi etc.
   Proponha mudança de glossário só com motivo forte, no campo `glossario` (nunca troca em massa).
3. **Códigos**: `{MOODHAPPY}` `{MOODSAD}` `{MOODANGRY}` `{MOODDEFAULT}` `{PAGEBREAK}`, `%s %d %02d`,
   ícones `[A] [B] [X] [Y] [LT] [RT] [LS] [RS] [BACK] [START]...`, marcação `<font ...>`, `<br>`,
   `&quot;`. Mesma quantidade, mesma ordem dos `%s/%d`, sem apagar nem criar. `{MOOD...}` fica no
   início quando estiver no início do original. `{PAGEBREAK}` divide o balão: mantenha a divisão no
   mesmo ponto de sentido.
4. **Caracteres**: só os da fonte do jogo (`data/fonte_euro.json`); nada de `¿ ¡`. Reticências como
   no catálogo (`...`). Sem espaço duplo, sem espaço antes de `, . ! ? ; :`.
5. **Interface em caixa de frase** (D8): "Menu principal", "Tempo restante". Exceção: quando o
   original inteiro está em MAIÚSCULAS, a tradução também fica em maiúsculas.

## Português brasileiro

* PT-BR contemporâneo e natural. Nada de português europeu (estás, ecrã, equipa, "estar a fazer",
  autocarro, facto, registo...). Tratamento padrão **você**; plural **vocês** quando o NPC fala com a
  dupla (Banjo e Kazooie) — seja coerente dentro da mesma conversa.
* Interface: imperativo de 3ª pessoa ("Aperte o Botão [A]", "Selecione", "Escolha"); mantenha o
  padrão já dominante no arquivo, sem trocar em massa "Aperte"/"Pressione" quando os dois estão
  corretos.
* "pra" só na boca de personagem informal (Kazooie, NPCs debochados); narração, tutorial e menus usam
  "para".
* Concordância de gênero dos personagens: Kazooie, Humba, Grunty (Gruntilda), Tooty, Mingella,
  Brentilda são femininas; Banjo, Mumbo, Klungo, S.J., Bottles, Jamjars, Boggy são masculinos. Siga
  os pronomes do inglês quando houver.
* Abreviação só quando o espaço exige (ex.: "Área de transf."), e de forma consistente.

## Personagens (estilo a preservar)

Confirme sempre pelo inglês da própria entrada; isto é o padrão já usado no catálogo:

* **Banjo**: simpático, simples, educado, às vezes ingênuo; nada de agressividade gratuita.
* **Kazooie**: sarcástica, provocadora, apelidos e insultos criativos; não suavize.
* **Gruntilda (Grunty)**: fala muitas vezes **rimando**; insultos e ameaças com humor. Se o inglês
  rima, procure rima em PT-BR sem perder o sentido.
* **S.J. (L.O.G.)**: o "Senhor dos Jogos", pomposo, metalinguístico, piadas sobre videogames.
* **Mumbo Jumbo** e **Humba Wumba**: fala quebrada com verbos no infinitivo e sem artigos
  ("Urso ter sorte", "Humba dar..."). Chamam Banjo de "Urso". Mumbo tem interjeições próprias
  ("Oomenacka!", "Eekumbokum!").
* **Klungo**: sibila (`sss`) e fala na terceira pessoa ("Klungo precisssar", "Ursso"). Mantenha a
  grafia consistente no mesmo personagem.
* **Bottles**: toupeira simpática e didática. **Jamjars**: locutor/radialista com bordões.
  **Tomás Troféu**: fala rimando. **Capitão Blubber/Flash McBlubber**: fala de pirata ("Arrr",
  "marujo", "rapaz").
* Demais NPCs: identifique pelo próprio texto (chave, mundo, o que dizem) e mantenha a voz de cada um.

## Gravidade

* **CRITICAL**: muda o sentido ou atrapalha jogar (instrução errada, botão errado, objetivo errado,
  código quebrado).
* **HIGH**: erro gramatical ou de contexto importante (concordância, crase, frase sem sentido, fala
  atribuída ao personagem errado, inglês que ficou).
* **MEDIUM**: frase artificial, literal demais ou termo inconsistente.
* **LOW**: melhoria de estilo sem perda de sentido (só se o ganho for claro).

## Entrega de cada frente

Cada frente escreve **somente** `work/revisao/propostas/<GRUPO>.json` (fora do git) no formato de
`tools/nbptbr/revisao.py` e confere com:

```
.venv\Scripts\python -I tools/ptbr.py checar-propostas work/revisao/propostas/<GRUPO>.json
```

O resultado precisa ser `PASS` (zero problemas). `pt_anterior` é copiado exatamente do catálogo.
`evidencia` cita no máximo um trecho curto do original (até 60 caracteres) e o contexto (quem fala,
mundo, missão, chave). Ninguém edita `data/` diretamente: a consolidação transforma as propostas
aceitas em lotes (`data/lotes/lote-610…`) e aplica com `aplicar-lote`.
