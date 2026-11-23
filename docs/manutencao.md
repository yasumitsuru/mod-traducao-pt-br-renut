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
6. `python -I tools/gerar_mod.py --jogo CAMINHO --saida PASTA` reproduz o pacote a partir da cópia
   do jogo; é o caminho usado pelo gerador publicado na Release e deve resultar no mesmo SHA-256.

## Launcher

O patch do launcher não é distribuído. Para gerá-lo na própria cópia do reNut:

1. `python -I launcher-patch/gerar_patch.py --exe "<renut>\renut.exe" --saida launcher-patch/renut_launcher_ptbr.patch`
2. `python -I launcher-patch/gerar_engine_patch.py --renut "<renut>"`
3. `python -I launcher-patch/aplicar.py status --renut "<renut>"`
4. `python -I launcher-patch/aplicar.py aplicar --renut "<renut>" --saida "<pasta separada>\renut.ptbr.exe"`

O aplicador recusa versões diferentes de `big-lua-energy` 0.11.21 e confere os hashes antes de
gravar. O `renut.exe` e as DLLs originais nunca são abertos para escrita.

## Regras

* Nomes de mapas e mundos listados em `data/nomes-protegidos.csv` nunca são traduzidos.
* O validador reprova variantes traduzidas desses nomes.
* Nenhum arquivo original do jogo, save, log ou configuração local entra no Git.
* Antes de enviar, rode `python -m pytest` e `python -I tools/verificar_privacidade.py --publico`
  (inclui a verificação de privacidade e a política de inclusão explícita).
* Rode o Gitleaks no histórico antes de um push: `gitleaks detect --source . --no-banner --redact`.
* Para bloquear commits e pushes automaticamente, ative os ganchos incluídos:
  `git config core.hooksPath .githooks`.
* A política completa está em `AGENTS.md` e `docs/politica-publicacao.md`.
