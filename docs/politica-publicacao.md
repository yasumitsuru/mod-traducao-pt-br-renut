# Política de publicação e segurança

Este documento explica como a política permanente de `AGENTS.md` é aplicada neste repositório.

## Separação entre privado e público

O desenvolvimento privado e o repositório público são árvores separadas. O histórico público é
linear e contém apenas commits sanitizados, com autor `yasumitsuru
<yasumitsuru@users.noreply.github.com>`. O histórico privado não é enviado, nem parcialmente.

A publicação é feita em uma área de trabalho pública independente, com histórico próprio. Não se
copia a pasta `.git` do projeto privado, não se usa `git push --mirror` e não se reescreve o
histórico público.

## Inclusão explícita

O `.gitignore` começa com `*` e libera somente caminhos revisados. Cada pasta nova precisa de uma
regra `!` correspondente. As regras são testadas com `git check-ignore --no-index`:

```text
git check-ignore --no-index -q -- README.md            # deve sair 1 (não ignorado)
git check-ignore --no-index -q -- segredo.exe          # deve sair 0 (ignorado)
git check-ignore --no-index -q -- data/strings/x.json  # deve sair 0 (ignorado)
```

Arquivos já rastreados não são protegidos por uma regra nova. Antes de cada envio, confira:

```text
git ls-files
git status --porcelain=v1 -uall
git diff --cached --stat
```

## O que não entra

* Executáveis, DLLs, `.exe`, `.dll`, `.msi`, `.pdb`, binários de teste e builds.
* ISO, XEX, XEXP, DLC, Title Updates, saves, perfis, `Content/`, `TDATA/` e `UDATA/`.
* `renut.toml`, `renut.cfg`, `launcher.cfg`, `renut.exe` e cópias traduzidas.
* `.nbpatch`, `.zip`, `.patch` binários e assets de Release.
* `data/strings/`, dumps do jogo, capturas privadas e conteúdo de terceiros.
* Credenciais, tokens, chaves, certificados, logs, dumps, caches e configurações locais.
* Caminhos absolutos particulares, nomes de usuário e metadados da máquina.

O launcher é publicado como código, catálogo, gerador, aplicador e documentação. O patch binário é
gerado localmente a partir da cópia legítima do reNut; ele não é distribuído porque o reNut não tem
licença formal que autorize redistribuir binários modificados.

## Verificações antes do commit

```text
python -m pytest
python -I tools/verificar_privacidade.py --publico
git diff --cached --stat
```

O verificador examina os arquivos rastreados, o `.gitignore`, os commits que seriam enviados, a
licença, a identidade dos commits, o remoto e as tags. Ele recusa caminhos pessoais, e-mails, tokens,
chaves, credenciais, IPs privados, arquivos binários e tipos não permitidos.

## Verificações antes do push

```text
python -I tools/verificar_privacidade.py --push --publico
gitleaks detect --source . --no-banner --redact
python -m pytest
```

O Gitleaks percorre todo o histórico público. O workflow do GitHub Actions repete essas verificações
em cada push e pull request, sem usar credenciais privadas.

## Ganchos locais

```text
git config core.hooksPath .githooks
```

* `pre-commit`: examina apenas o que está preparado, com a política pública.
* `pre-push`: examina a árvore, os commits que seriam enviados e roda os testes quando o pytest
  estiver disponível.

Os ganchos podem ser ignorados; por isso o CI e a revisão humana continuam obrigatórios.

## Identidade e remoto

* Branch: `main`.
* Autor: `yasumitsuru <yasumitsuru@users.noreply.github.com>`.
* Remoto: `https://github.com/yasumitsuru/mod-traducao-pt-br-renut`.
* Proibido: `--force`, `--mirror`, branches privadas, tags antigas e qualquer remoto não autorizado.

## Releases e tags

Não crie Release, tag, asset de Release ou binário de distribuição sem autorização explícita. A
Release e a tag **v0.7.0** existentes devem permanecer intactas. Commits normais na `main` são
permitidos depois das verificações.

## Estados

Use **PASS**, **PARTIAL**, **BLOCKED** e **NOT_TESTED** com evidência. A cobertura textual do
launcher é completa, mas a cobertura visual tem estados parciais e não testados; não declare 100%
visual. O mod do jogo permanece na v0.7.0.

## Relatório de cada sincronização

Registre o SHA publicado, os arquivos adicionados/modificados/excluídos, as regras novas do
`.gitignore`, o resultado do Gitleaks, dos testes de privacidade e dos testes funcionais, e confirme
que o histórico privado foi preservado e que nenhuma Release/tag foi criada.