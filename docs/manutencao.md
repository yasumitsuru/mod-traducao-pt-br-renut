# Manutenção da tradução

## Fonte da verdade

`data/traducao/<hash>.json` guarda, por arquivo do jogo, a lista de frases com `id`, `chave`,
`hash_es` e `texto_ptbr`. É o único lugar onde a tradução é editada. `data/strings/` é uma extração
do jogo, regenerável, e não entra no Git.

## Fluxo

1. `python -I tools/ptbr.py extrair` relê o jogo e preserva as traduções existentes.
2. Edite o texto em `data/traducao/` ou aplique um lote de `data/lotes/`.
3. `python -I tools/ptbr.py validar` confere códigos de controle, acentos, comprimento e nomes
   protegidos.
4. `python -I tools/ptbr.py reinserir` reconstrói os arquivos de texto.
5. `python -I tools/ptbr.py empacotar --versao X.Y.Z` gera `dist/ptbr_traducao`.

## Regras

* Nomes de mapas e mundos listados em `data/nomes-protegidos.csv` nunca são traduzidos.
* O validador reprova variantes traduzidas desses nomes.
* Nenhum arquivo original do jogo, save, log ou configuração local entra no Git.
* Antes de enviar, rode `python -m pytest` (inclui a verificação de privacidade).
* Para bloquear o commit automaticamente, ative o gancho incluído:
  `git config core.hooksPath .githooks`.
