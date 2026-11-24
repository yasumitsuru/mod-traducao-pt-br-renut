# Revisão 0.8.0 — pendências, tempo de leitura e glossário

## Decisões ambíguas mantidas (texto atual preservado)

* **G1** `111dc2ac[3387]`: Hoedown Town está como 'Cidade Country' (o espanhol usa 'Ciudad Música Country'); não é nome protegido e não há nome oficial em PT-BR. Alternativas: manter 'Cidade Country'; 'Cidade do Forró'; manter 'Hoedown Town' como nome próprio. Impacto: baixo: piada de uma linha do S.J.; nenhuma outra entrada citada na fatia usa o termo
* **G1** `11132aff[ad2f]`: 'Some coats' está como 'Casacos' (sem 'Alguns'); as outras opções da Q75 misturam plural nu e singular com artigo. Sem a imagem do objeto não dá para saber se 'casacos' é a melhor leitura. Alternativas: manter 'Casacos'; 'Alguns casacos'; 'Casacos pendurados'. Impacto: baixo: a resposta continua coerente com a pergunta (o que pende de uma corrente)
* **G1** `11a8e97b[2d0d]`: Kazooie pergunta pelo 'old Loggo Breath' (apelido insultuoso). Se o alvo for Gruntilda (feminina), 'o velho Bafo de Loggo' deveria concordar no feminino; a entrada não mostra quem é. Alternativas: manter 'o velho Bafo de Loggo'; 'a velha Bafo de Loggo' (se for a Grunty). Impacto: baixo: só concordância do apelido; o espanhol oficial também é neutro ('el viejo aliento de Loggo').
* **G1** `11a8e97b[a5f1]`: Kazooie chama o S.J. de 'SCART Mouth'; 'Boca de Tomada' segue o espanhol ('boca de enchufe'), mas SCART é um conector de vídeo, não tomada de energia. Alternativas: manter 'Boca de Tomada'; 'Boca de Scart'; 'Boca de Plugue'. Impacto: baixo: humor/insulto da Kazooie; sentido geral preservado.
* **G1** `11b5ef5f[0b6e]`: Os títulos de menu das combinações usam 'Torre do Alçapão 3' (e 1, 2), enquanto as falas usam 'nº 3'. Sem 'nº' economiza espaço no rótulo. Alternativas: manter sem 'nº' nos rótulos; padronizar com 'nº' (+3 caracteres) nos três rótulos (0b6e, 7bf0, 02f2). Impacto: baixo: só padronização de rótulo; risco de rótulo mais largo.
* **G1** `11cf84ff[5520]`: 'Estou horrorizado!' está no masculino, mas o EN não marca gênero e o NPC do Resort é desconhecido Alternativas: Manter o masculino atual; Reescrever sem marca de gênero. Impacto: Baixo: depende do NPC que fala a linha (não identificável pela chave); sem efeito no sentido.
* **G1** `11cf84ff[04d4]`: 'Fico tonto' está no masculino; EN neutro e NPC do Distrito dos Teatros desconhecido Alternativas: Manter o masculino atual; Reescrever sem marca de gênero. Impacto: Baixo: depende do NPC que fala a linha (não identificável pela chave); sem efeito no sentido.
* **G1** `11cf84ff[04d7]`: 'letárgico e inchado' está no masculino; EN neutro e NPC do Distrito dos Teatros desconhecido Alternativas: Manter o masculino atual; Reescrever sem marca de gênero. Impacto: Baixo: depende do NPC que fala a linha (não identificável pela chave); sem efeito no sentido.
* **G1** `11f0cc45[6a50]`: Trocadilho 'ahead' / 'a head': Gruntilda é só uma cabeça. 'na frente' mantém o idioma (parar enquanto está ganhando) mas perde o jogo com 'cabeça'. Alternativas: enquanto estava... na frente (atual); enquanto ainda tinha... cabeça no lugar; enquanto estava... com a cabeça erguida. Impacto: Baixo: humor da narração de abertura; sentido geral preservado.
* **G1** `11f0cc45[e1a7]`: 'coletatlão' é neologismo (coletar + decatlão) que o espanhol e os fãs não usam; pode não ser compreendido de imediato. Alternativas: Que comece o coletatlão! (atual); Que comece a maratona de coleta!; Que comece o collectathon!. Impacto: Baixo: piada metalinguística do S.J. sobre o gênero collect-a-thon.
* **G2** `111fcbbb[05da]`: Tanktup virou 'Tanquetup' no catálogo (placa, título, percurso de piscina e peça Banjo-Brawl); o espanhol oficial mantém 'Tanktup' e o guia manda manter nome de personagem. Alternativas: Manter Tanquetup (já consistente em 4 arquivos); Voltar para Tanktup em 111fcbbb[05da,807d], 114c6966[8cc1] e 1183ab14[23dd]. Impacto: Consistência de nome entre placa, percurso e peça; mudar só aqui criaria dois nomes.
* **G2** `111fcbbb[807d]`: Mesmo caso do Tanktup (título da placa). Alternativas: Manter Tanquetup; Tanktup. Impacto: Ver 05da.
* **G2** `11a378ff[1384]`: 'Desjejum' (breakfast) é palavra formal para um Klungo coloquial; 'café da manhã' é o uso comum no Brasil (também em 8a48). Alternativas: Manter desjejum; Trocar por café da manhã em 1384 e 8a48. Impacto: Só registro; sem perda de sentido.
* **G2** `11b97d91[2347]`: Grafia do Klungo para 'Bear': 'Urssso' (75 ocorrências no catálogo; 5 nesta fatia em banjoland_act5) x 'Ursso' (58; é a do glossário e a usada em nuttyacres_act6). Alternativas: Unificar para 'Ursso' (glossário); Atualizar o glossário para 'Urssso'; Manter as duas. Impacto: Baixo: consistência de voz, nenhum efeito no sentido; decisão de consolidação global
* **G2** `11b97d91[c709]`: 'Mr. Patch' fica em inglês (15 ocorrências), enquanto Mr. Fit = Sr. Em Forma e Mr. Ribs = Sr. Costelas. Alternativas: Manter 'Mr. Patch' (nome do chefe da série); Sr. Remendo (liga com 'remendos' da fala game6_objectives). Impacto: Baixo: nome de chefe inflável; mudar exige troca em todo o catálogo
* **G2** `11b97d91[7427]`: Trocadilho 'NO BODY' (ninguém / sem corpo) com Sr. Costelas: PT mantém 'NENHUM CORPO', literal, sem o duplo sentido de 'ninguém'. Alternativas: Manter 'sem NENHUM CORPO'; 'sem NINGUÉM (nem corpo) para cuidar de você'. Impacto: Baixo: piada do Jinjo rosa; sentido geral preservado
* **G2** `11aa2945[d536]`: 'get Jiggy with it' (referência musical) perdido em 'ganhar o Jiggy'. Alternativas: Manter; Nada mal, mas não o bastante para ficar 'Jiggy' desta vez. Impacto: Baixo: referência cultural de uma fala do Sr. Em Forma/NPC aéreo
* **G2** `11c67778[c4ac]`: 'Recognize!' (gíria de respeito/hip-hop) está literal em 'Reconheça!'. Alternativas: Reconheça! (atual); Respeita!; Pode crer!. Impacto: Baixo: fim de fala de piada; sentido geral preservado.
* **G2** `11c7ed5c[29e8]`: 'Cloud Cuckooland' está como 'Nuvem Cucolândia' (ordem estranha, sem artigo); aparece em mais de um arquivo. Alternativas: Nuvem Cucolândia (atual); Cucolândia das Nuvens; Terra do Cuco nas Nuvens. Impacto: Baixo: referência ao Banjo-Tooie; decidir globalmente para manter coerência.
* **G2** `11c67778[d6f7]`: Grafia do 'Bear' do Klungo: 'Urssso' (3 s, 75 ocorrências no catálogo) x 'Ursso' (guia/glossário, 58). Mesmo personagem alterna entre Banjoland (Urssso) e Nutty Acres (Ursso). Alternativas: Padronizar em Ursso (glossário); Padronizar em Urssso; Manter como está (sibilo variável). Impacto: Baixo-médio: consistência de voz; troca em massa exige decisão da consolidação.
* **G2** `11dde832[9744]`: "Stony Kickball Challenge" ficou "Desafio de Futebol de Pedra", mas em d536 "a Stony" virou "Pedrusco". Alternativas: Manter "Desafio de Futebol de Pedra"; "Desafio de Futebol dos Pedruscos". Impacto: Baixo: consistência do nome do desafio com o termo Pedrusco; sem efeito na jogabilidade.
* **G2** `11dad8a4[6655]`: "aardvark" (Sr. Em Forma) foi traduzido como "tamanduá"; o animal correto é o porco-formigueiro (oricteropo). Alternativas: Manter "tamanduá" (compreensão popular); "porco-formigueiro". Impacto: Baixo: zoologia do personagem; decidir junto com outras menções na consolidação.
* **G3** `11055bb1[c9eb]`: "Rocket Luncher" (nave do Capitão Foobar) é trocadilho de "launcher" com "lunch"; "Lançador de Foguetes" perde o jogo de palavras. Alternativas: Manter "Lançador de Foguetes"; &quot;Lança-Lanches&quot; (jogo com lanche); Manter o nome em inglês como "Star Spanners". Impacto: Baixo: nome de nave citado de passagem pelo Pikelet; sem efeito na missão.
* **G3** `112303c4[75ce]`: Jinjo vermelho fala em haiku (5-7-5 sílabas) nas quatro falas (intro, lose, objectives, win); a PT mantém o tom curto e sério, mas não respeita a métrica 5-7-5. Alternativas: Manter as falas como estão; Reescrever em 5-7-5 sílabas poéticas, por exemplo "Olá, urso e pássaro." (5) como primeiro verso. Impacto: Médio-baixo: a graça é a métrica; o jogador entende a fala sem ela. Decisão editorial.
* **G3** `112303c4[a1ea]`: Grafia de Klungo para "urso": "Ursso" neste arquivo e "Urssso" em terrorium_act*; o glossário registra "Ursso". Alternativas: Padronizar tudo em "Ursso" (glossário); Padronizar tudo em "Urssso" (forma dominante); Manter variações por mundo. Impacto: Baixo: só grafia; mudança em massa não feita pelo revisor.
* **G3** `11818841[9744]`: "Splice the mainbrace!" é bordão naval (servir grogue); a PT "Levanta âncora!" muda o sentido (partir) mas mantém o tom de pirata. Alternativas: Manter "Levanta âncora!"; "Hora do grogue!"; "Ao convés, marujos!". Impacto: Baixo: exclamação de abertura do Capitão Blubber.
* **G3** `119ae8df[0a16]`: Trocadilho 'Stop'/'Swop' (referência ao Stop 'n' Swop, nome mantido no glossário) com iniciais maiúsculas virou 'parar de procurar e trocar a chave', sem a referência. Mesma questão em a4f1 (Se você parar... eu troco). Alternativas: manter o texto atual (sem a referência); capitalizar 'Parar' e 'Trocar' para sugerir o Easter egg; usar 'Stop' e 'Swop' em inglês como no nome do recurso. Impacto: Baixo: perde-se a piada/referência para fãs; objetivo (achar a Chave de Gelo e trocar por Ficha Jinjo) continua correto.
* **G3** `119ae8df[a4f1]`: Mesma referência 'Stop'/'Swop' do jinjoyellow_lose (0a16): 'Stop what you're doing... I'll Swop it' perdeu as iniciais maiúsculas/o jogo de palavras. Alternativas: manter; Se você Parar o que está fazendo e encontrar minha Chave de Gelo, eu Troco por uma Ficha Jinjo!. Impacto: Baixo; decidir junto com 0a16 para manter coerência.
* **G3** `11e51de2[9fae]`: Piada das Spice Girls: 'Jinjo Esportista' traduz Sporty, mas Baby, Scary, Posh e Ginger ficaram em ingles. O espanhol traduziu todos os apelidos. Alternativas: Manter 'Jinjo Esportista'; 'Jinjo Sporty' (mantem a referencia reconhecivel; exigiria checar o nome do Jinjo rosa em outras telas). Impacto: Baixo: so reconhecimento da piada; a fala funciona nos dois casos.
* **G3** `11e22d74[9d67]`: O anfitriao dos dardos/dados nao e identificado no texto; 'fico um pouco tonto' esta no masculino. Se a voz for feminina (por exemplo Tooty), seria 'tonta'. O espanhol (me mareo) e neutro. Alternativas: Manter 'tonto'; Neutralizar: 'Só de olhar já me dá uma tontura...'. Impacto: Baixo: so concordancia de genero se o falante for feminino.
* **G4** `113b4c15[c622]`: Dicas citam termos de menu em maiúscula copiando o inglês (Amigos, Regras da Partida, Partida Rápida, Equipe/Solo). Se os rótulos reais usam caixa de frase, as dicas deveriam seguir. Alternativas: manter; minúsculas (amigos, regras da partida, partida rápida, equipe/solo). Impacto: Baixo (só caixa; depende dos rótulos de G4-02)
* **G4** `110f9757[905c]`: Teletransportar para: (21 caracteres contra 8 do original) é longo para um título, mas igual ao rótulo Teletransportar de 1149a294[b82b]; o glossário usa Teleporte. Alternativas: manter; Teleportar para:. Impacto: Baixo (comprimento/terminologia)
* **G4** `112658dd[57a4]`: Eggs Held (ovos que o jogador segura agora) está como Ovos pegos, que pode ser lido como total coletado. Alternativas: manter; Ovos carregados. Impacto: Baixo (HUD do desafio, rótulo curto)
* **G4** `113b4c15[3333]`: DNF (Did Not Finish) permanece idêntico ao inglês; o espanhol usou ST (Sin Terminar). Alternativas: DNF; NC (Não concluiu). Impacto: Baixo: só a coluna de resultados do multijogador.
* **G4** `114483e7[576b]`: [BACK] BACK: o texto BACK após o ícone foi mantido como no original; como o botão Back do Xbox 360 aparece em PT-BR (Voltar?) e se o ícone já traz texto não é verificável aqui Alternativas: manter [BACK] BACK (atual, igual ao original e ao ES); trocar por [BACK] Voltar; remover o texto e deixar só [BACK]. Impacto: baixo: dica de carregamento (também em da5e)
* **G4** `114483e7[5798]`: Off/On (toggleoff/toggleon) estão como Não/Sim, seguindo o ES (No/Sí); o EN diz Off/On Alternativas: manter Não/Sim (atual); Desligado/Ligado (literal). Impacto: baixo: depende de onde os valores aparecem (inverter eixo, vibração); par com 38fa
* **G4** `1149a294[e9a4]`: Attach/Detach: editor usa Fixar/Separar e guincho usa Prender/Soltar (5e9d, 68f1); Soltar também é Drop e Release. Mantido por serem contextos distintos Alternativas: manter Fixar/Separar (editor) e Prender/Soltar (guincho); unificar tudo em Prender/Soltar. Impacto: baixo: nenhuma tela mostra os dois pares juntos, pelo que se deduz das chaves
* **G4** `115cdc72[6b05]`: 'Sponsor' (login LIVE) está como 'Patrocinador' (calco; o espanhol oficial também usa 'patrocinador'). Não dá para confirmar pelas chaves se o termo designa o perfil principal que leva os demais à LIVE. As duas frases também diferem na forma verbal: 'não está pronto' x 'não conectado' (b607). Alternativas: manter 'Patrocinador'; Perfil principal; Anfitrião. Impacto: Baixo: só rótulo de status do login LIVE; entendível como está.
* **G4** `11765bae[d775]`: 'the mooning conservationist' (Humba Wumba, Terrarium of Terror): 'mooning' pode ser 'mostrar o traseiro' (atual: 'sem-vergonha') ou 'sonhadora/apaixonada/aérea'; o espanhol oficial não ajuda (só 'la conservacionista'). Mantido o texto atual por falta de contexto da cena. Alternativas: a conservacionista sem-vergonha (atual); a conservacionista sonhadora; a conservacionista apaixonada; a conservacionista que mostra o traseiro. Impacto: baixo: legenda curta dos créditos de abertura; não afeta objetivos nem jogabilidade
* **G5** `114c6966[340c]`: 'Fore!' foi traduzido como 'Bola aí!'; em PT-BR 'bola aí' soa como pedido, não como o aviso de golfe. Não é narrativo; manter até decisão da consolidação. Alternativas: Olha a bola!; Atenção, bola!; Fore!. Impacto: Só a exclamação de abertura da descrição do Golfe; nenhuma regra ou número muda.
* **G5** `114c6966[7711]`: 'Dam Busted' (trocadilho com 'Dambusters') virou 'Represa Bum!', com onomatopeia que o original não tem. Alternativas: Represa Rompida; Represa Estourada; Represa Bum! (atual). Impacto: Título de uma tela de desafio; sem efeito em regras.
* **G5** `114c6966[8f15]`: 'with their sheep' virou 'com as ovelhas' (plural, sem posse); no Golfe cada jogador usa a própria bola, então talvez fosse singular. Sem como confirmar no texto. Alternativas: marcou com a ovelha dele(a); marcou com a própria ovelha; marcou com as ovelhas (atual). Impacto: Frase de aviso no Golfe; entendimento intacto.
* **G5** `114c6966[2cb5]`: A piada 'egg on your face' foi para 'o ovo vai cair na sua cara', que não bate com esquecer de pegar o ovo; o espanhol faz o mesmo. Sem idiomática equivalente em PT. Alternativas: ou vai ficar com cara de tacho... entendeu?; ou vai ficar com ovo na cara... entendeu?; ou o ovo vai cair na sua cara... entendeu? (atual). Impacto: Trocadilho de humor numa dica; instruções e regras não mudam.
* **G5** `1169b65d[a2f1]`: 'Beacon' = 'Baliza' (herdado do espanhol); em PT-BR 'baliza' também é manobra de estacionar e baliza de trânsito, e pode confundir. Vale também para block__group_beacon [9f7d]. Alternativas: Sinalizador; Farol Giratório; Baliza (atual). Impacto: Rótulo da peça (bloco e grupo); precisaria olhar a aparência no jogo.
* **G5** `1170b914[8286]`: Descrição diz "luzes estilosas de rolê", mas o rótulo da peça é "Luz de Cruzeiro" (cruisin' light). Alternativas: Manter "luzes estilosas de rolê" (descritivo, EN em minúsculas); Turbinar veículo com Luz de Cruzeiro estilosa. Impacto: Baixo: peça identificável pelo ícone; só consistência de nome.
* **G5** `1170b914[94fd]`: Descrição diz "bola de ferrugem"; o rótulo do projétil é "Bola Oxidada". Alternativas: Manter "bola de ferrugem" (mais natural); Trocar por "bola oxidada". Impacto: Baixo: projétil, não peça de montagem.
* **G5** `1170b914[dd82]`: "Bolota" (EN lump) pode ser lido como bolota/noz; o rótulo da peça é "Lastro". Alternativas: Manter Bolota; Massa grande e pesada que puxar veículo para baixo; Lastro grande e pesado que puxar veículo para baixo. Impacto: Baixo: sentido de peso fica claro pelo resto da frase.
* **G5** `11fbc3ac[155e]`: Trocadilho 'You Clanker' (wanker -> clanker) perdido; PT diz só 'Clanker' Alternativas: Manter 'Você Vai Ficar Cego, Clanker...'; Você Vai Ficar Cego, Seu Clanker.... Impacto: Baixo: título de desafio; piada adulta já perdida no espanhol
* **G5** `11fbc3ac[b7e4]`: 'Baa for the Course' (par for the course + baa) virou 'Campo de Ovelhas', sem a piada Alternativas: Manter 'Campo de Ovelhas'; Par de Bééé; Bééé-rdie no Campo. Impacto: Baixo: título do desafio de golfe de ovelhas
* **G5** `1183ab14[fafe]`: 'Dragumfly' (drag + dragonfly) virou só 'Libélula' (igual ao espanhol) Alternativas: Manter 'Libélula'; Dragolibélula; Arrancalibélula. Impacto: Baixo: nome de veículo do multijogador
* **G5** `11fbc3ac[0f5c]`: 'Checkpoint Charlies' perdeu a referência ao Checkpoint Charlie Alternativas: Manter 'Pontos de Controle'; Pontos de Controle Charlie. Impacto: Baixo: título de desafio
* **G5** `11fbc3ac[f021]`: 'You Little Squirt' (fedelho + esguicho de líquido) virou 'Seu Pivete!', sem a ideia de líquido do desafio Alternativas: Manter 'Seu Pivete!'; Seu Esguichinho!. Impacto: Baixo: título de desafio de resfriar ventiladores
* **G5** `11fbc3ac[b621]`: O original é o acrônimo U.F.O. = Unpleasant Fat Oaf e o resumo (234f) diz 'U.F.O.'; em PT 'Gorda Desagradável' perde a ligação com 'OVNI' (o espanhol também perdeu). Alternativas: Manter 'Gorda Desagradável'; Obesa Vil Nojenta e Imunda (O.V.N.I.); Ogra Vulgar, Nojenta e Insuportável (O.V.N.I.). Impacto: Só humor do título; não afeta regras do desafio
* **G5** `11fbc3ac[2b0f]`: 'Brown Bears Can't Jump' (White Men Can't Jump) perdeu 'Brown'; 'Saltar' é aceitável mas 'Pular' é mais comum. Alternativas: Manter 'Ursos Não Sabem Saltar'; Ursos Pardos Não Sabem Pular; Ursos Pardos Não Sabem Enterrar. Impacto: Referência de humor; título já funciona
* **G5** `11fbc3ac[7c4e]`: 'No Holds Beared' (No Holds Barred + bear) virou 'Sem Regras' e perdeu o trocadilho com urso. Alternativas: Manter 'Sem Regras'; Sem Regras de Urso. Impacto: Só humor do título

## Falas para o futuro mod de diálogo manual (tempo de leitura)

Registro apenas: nenhum temporizador foi alterado nesta missão.

* **G1** `111dc2ac[979d]`: 225 caracteres no PT contra 179 no EN (+26%); fala única do S.J., deve ficar no limite de tempo de leitura
* **G1** `111dc2ac[d1aa]`: duas partes com {PAGEBREAK}: 194 e 147 caracteres; tamanho igual ao do inglês (349 vs 341), mas é a fala mais longa da fatia
* **G1** `111dc2ac[9bea]`: 201 caracteres (inglês 190); fala do S.J. de uma só vez
* **G1** `1120c047[2dc5]`: 202 caracteres (inglês 182); fala do S.J. sobre o Globo de Jogo do Jiggosseum
* **G1** `111dc2ac[3384]`: 197 caracteres (inglês 187); piada com survival horror
* **G1** `111dc2ac[ddd1]`: 195 caracteres (inglês 176)
* **G1** `11903d36[1129]`: 194 caracteres (inglês 180); Jinjo libertado, fala única
* **G1** `11159462[68c1]`: +45% sobre o inglês (92 vs 63 caracteres); fala curta de despedida da Humba, leitura ainda rápida
* **G1** `11244458[dfd6]`: 184 caracteres (inglês 163, +13%); explicação do teleporte
* **G1** `11b5ef5f[3a9c]`: Balão único de ~254 caracteres (EN ~198, +28%); a maior fala de página única da fatia. Não cortada.
* **G1** `11b5ef5f[1c73]`: Balão único de ~255 caracteres (EN ~195, +31%); Bottles, tutorial das cordas bambas. Não cortada.
* **G1** `11b5ef5f[a03f]`: Klungo, ~236 caracteres (EN ~201, +17%); sibilantes alongam a leitura. Não cortada.
* **G1** `11b5ef5f[29cb]`: Humba (blueprints), ~219 caracteres (EN ~192); a fala 5e58 (singular) é equivalente. Não cortada.
* **G1** `11b5ef5f[9fb8]`: Mumbo (peças), ~220 caracteres (EN ~190); a fala 4aa5 (singular) é equivalente. Não cortada.
* **G1** `11b5ef5f[5cd1]`: Bottles, ~209 caracteres (EN ~184) com dois ícones de botão; leitura apertada. Não cortada.
* **G1** `11b5ef5f[8cd6]`: Bottles, 93 caracteres vs 55 do EN (+69%); curta o bastante para um único balão.
* **G1** `11b5ef5f[f9ad]`: Jolly, 86 caracteres vs 53 do EN (+62%); curta.
* **G1** `11b5ef5f[a984]`: Rei Jingaling, 74 caracteres vs 47 do EN (+57%); curta.
* **G1** `11e92675[40bd]`: 197 caracteres em um único balão; conferir se o tempo de exibição comporta (nada cortado).
* **G1** `11f0cc45[6a4e]`: 189 caracteres em um único balão; conferir se o tempo de exibição comporta (nada cortado).
* **G1** `11f0cc45[6a50]`: 185 caracteres em um único balão; conferir se o tempo de exibição comporta (nada cortado).
* **G1** `11f0cc45[b0b4]`: 204 caracteres em um único balão; conferir se o tempo de exibição comporta (nada cortado).
* **G1** `11f0cc45[b41f]`: 191 caracteres em um único balão; conferir se o tempo de exibição comporta (nada cortado).
* **G2** `111fcbbb[2967]`: Placa mais longa do grupo (238 car.; EN 189), abaixo do máximo do espanhol oficial (253). Placa estática, sem temporizador.
* **G2** `11a378ff[8026]`: 2 balões ([175, 119] car.), mesmo tamanho do EN; Bottles explica o prêmio e faz a proposta.
* **G2** `11a378ff[542c]`: 3 balões ([89, 60, 87] car.), igual ao original; falas do Sr. Em Forma sem pausa para o jogador.
* **G2** `11a44869[5dac]`: 3 balões ([49, 94, 76] car.), igual ao original.
* **G2** `11a44869[9466]`: 1 balão de 177 car. com instrução de controle; EN tem 180.
* **G2** `11aa2945[d405]`: dialog__game2_intro: balão de 217 caracteres em PT (2 balão(ões)); texto não cortado
* **G2** `11c0ddca[a4f1]`: dialog__jinjoyellow_objectives: balão de 204 caracteres em PT (1 balão(ões)); texto não cortado
* **G2** `11c67778[9f3e]`: Duas páginas longas (~330 caracteres); fala de introdução do Capitão Blubber, sem corte.
* **G2** `11c67778[5aba]`: Duas páginas longas (~320 caracteres) com instruções sobre o jogo completo.
* **G2** `11c67778[ba04]`: Duas páginas (~280 caracteres) com sibilo do Klungo; leitura mais lenta.
* **G2** `11c67778[34e6]`: Duas páginas (~300 caracteres) do Klungo; leitura mais lenta.
* **G2** `11c7ed5c[4129]`: Três páginas (~330 caracteres) com o objetivo do desafio dos canos; fala essencial, sem corte.
* **G2** `11c7ed5c[542d]`: Três páginas do Mumbo com o objetivo da bomba (~260 caracteres); fala essencial.
* **G2** `11f1d3b7[10c6]`: Fala do Klungo com cerca de 190 caracteres; verificar tempo de exibição, mas o inglês também é longo.
* **G2** `11dde832[4128]`: Explicação das regras com cerca de 200 caracteres (Gobi/Boggy no futebol); original igualmente longo.
* **G2** `11d4b988[d405]`: Dois balões ({PAGEBREAK}); o segundo tem cerca de 130 caracteres.
* **G3** `11818841[e358]`: Fala longa (~170 caracteres) do Jinjo amarelo; revisar se cabe no tempo do balão.
* **G3** `11818841[5829]`: Regras do basquete (~160 caracteres) em um único balão.
* **G3** `118fe96d[4006]`: Dois balões densos ({PAGEBREAK}); o segundo tem ~110 caracteres com a regra do Jiggy.
* **G3** `119ae8df[fac8]`: Humba, dois balões longos (~190 e ~90 caracteres); a fala em infinitivo ajuda, mas é a mais longa do Terrarium.
* **G3** `119ae8df[a4f1]`: Jinjo amarelo, ~170 caracteres em um balão.
* **G3** `11e22d74[8899]`: Fala unica de ~165 caracteres (T.T., game4_successe); tamanho igual ao do original (~165). Sem corte.
* **G3** `11e22d74[9d67]`: Duas paginas ({PAGEBREAK}); a primeira tem ~150 caracteres, equivalente ao original. Sem corte.
* **G4** `110f9757[5693]`: Placar de notícias muito longo: PT 2191 caracteres contra 2028 do original; comprimento equivalente, sem corte; conferir tempo de rolagem no jogo.
* **G4** `11606e97[79bc]`: PT 136 x EN 116 caracteres; fala dos créditos um pouco maior que o original
* **G5** `114c6966[9c43]`: 163 caracteres (EN 146, ES 157) na tela de resultado da série; +12% sobre o inglês, no nível do espanhol. Não cortado.
* **G5** `114c6966[aded]`: 111 caracteres (EN 88, ES 103) na tela de resultado de equipe; maior que o inglês, próximo do espanhol. Não cortado.
* **G5** `114c6966[2883]`: 127 caracteres (EN 122) na tela de resultado individual; equivalente ao original. Sem ação.
* **G5** `1170b914[a716]`: Fala longa: PT 210 car. contra EN 191 car.; só registrada (sem corte).
* **G5** `1170b914[5634]`: Fala longa: PT 239 car. contra EN 200 car.; só registrada (sem corte).
* **G5** `1170b914[0399]`: Fala longa: PT 221 car. contra EN 186 car.; só registrada (sem corte).
* **G5** `1170b914[7ff6]`: Fala longa: PT 210 car. contra EN 172 car.; só registrada (sem corte).
* **G5** `1170b914[c25e]`: Fala longa: PT 177 car. contra EN 175 car.; só registrada (sem corte).
* **G5** `1170b914[97e9]`: Fala longa: PT 182 car. contra EN 162 car.; só registrada (sem corte).
* **G5** `1170b914[a288]`: Fala longa: PT 178 car. contra EN 171 car.; só registrada (sem corte).
* **G5** `11a4db3b[b77b]`: PT com 234 caracteres (EN 191); vídeo do tutorial do Mumbo, conferir se o tempo de exibição comporta
* **G5** `11a4db3b[ee55]`: PT com 218 caracteres (EN 193); vídeo do tutorial do Mumbo, conferir se o tempo de exibição comporta
* **G5** `11a4db3b[8ed9]`: PT com 210 caracteres (EN 168); vídeo do tutorial do Mumbo, conferir se o tempo de exibição comporta
* **G5** `11a4db3b[708d]`: PT com 210 caracteres (EN 158); vídeo do tutorial do Mumbo, conferir se o tempo de exibição comporta

## Propostas de glossário

* **G2** `Farmhand (of The Year)`: Jornaleiro → Peão de Fazenda — Em PT-BR jornaleiro é vendedor de jornais; vem do 'jornalero' espanhol (trabalhador diarista).
* **G2** `arrow (indicador de direção)`: flecha → seta — Em PT-BR a indicação de direção é seta; flecha é o projétil/espanholismo. O catálogo já usa seta em 114483e7[cc63].
* **G2** `Tanktup`: Tanquetup → Tanktup — Nome de personagem; o guia manda manter e o espanhol oficial mantém. Só com decisão da consolidação, em todas as ocorrências.
* **G2** `Snozz Face`: Cara de Mocotó → Cara de Narigão — 'Snozz' = nariz/bico (es: 'cara nariz'); 'mocotó' não tem relação e a fala seguinte fala em bico comprido
* **G2** `Farmhand(s)`: jornaleiro(s) → peão(ões) de fazenda — Termo decidido pelo projeto: Farmhand = Peão de Fazenda
* **G2** `arrow (indicador de direção / HUD)`: flecha → seta — Decisão do projeto: 'setas' (não 'flechas'). Há 3 ocorrências de flecha/flechas no catálogo (uma neste arquivo).
* **G4** `Start (ação de menu)`: Começar / Iniciar → Iniciar — Iniciar já domina (Iniciar, Iniciar lobby/desafio, Start Game = Iniciar jogo no glossário); Começar ficava em 6 rótulos
* **G4** `Quit to Main Menu`: Sair para o menu principal / Voltar ao menu principal → Voltar ao menu principal — Mesmo original em 3 telas (pausa, pausa MP, teste de veículo) com duas traduções; ES usa Ir al menú principal
* **G5** `Plant Pot`: Vaso (grupo) / Vaso de Planta (bloco) → Vaso de Planta — Mesma peça com dois nomes; o completo evita a ambiguidade de 'vaso'.
* **G5** `Robo-Fix`: Robo-Conserto → Robô-Conserto — Acentuação de 'robô'.
* **G5** `Dummy Propeller`: Hélice de Teste → Hélice Falsa — 'Dummy' = falso/de enfeite (peça sem potência), não 'de teste'.
* **G5** `Bike`: Bici → Bike — 'Bici' é espanholismo/uso lusitano; no Brasil o termo comum é 'bike'
* **G5** `Hover`: Planador → Flutuante — Planador = glider (já usado em Hiperplanador/planar); Hover Chassis já é 'Chassi Flutuante'
* **G5** `Farmhand`: Lavrador (challenge); Jornaleiro (dialogs/game3, game4, game5); peão (movie) → Peão de Fazenda — Termo definido pelo projeto; unifica título do desafio, diálogos e filmes
* **G5** `Loco Coco`: Coco Loco (challenge); Coco Louco (infopoint) → Coco Louco — Unifica grafia e usa a palavra portuguesa 'louco'
* **G5** `Airways`: Aerococo Expresso (019a); Aerolinhas (game__coconutairways) → 019a: Aerococo (mantém Aerolinhas só em 'Nutty Airways') — Remove 'Expresso' inventado e reduz o título; ES oficial usa 'Aerococo'
* **RI** `Bear (Klungo)`: Ursso → Urssso — grafia majoritária e coerente com o 'sss' do personagem
