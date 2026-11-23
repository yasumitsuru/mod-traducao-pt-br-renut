# Instruções do projeto — tradução PT-BR de Banjo-Kazooie: Nuts & Bolts

Este arquivo é a referência permanente para pessoas e agentes que trabalham neste repositório.
Ele complementa o `README.md`, o `NOTICE.md` e `docs/politica-publicacao.md`.

## Política permanente de Git, segurança e sincronização com GitHub

> Toda alteração concluída e validada neste projeto deve ser sincronizada com o repositório público
> autorizado. Antes de cada commit ou push, o agente deve auditar os arquivos novos e modificados,
> revisar o `.gitignore`, verificar o índice e o histórico Git destinado ao remoto, executar os
> testes de privacidade e de detecção de segredos, e confirmar que nenhum dado sensível ou material
> não distribuível será publicado. É proibido enviar o histórico Git privado, utilizar force push,
> publicar credenciais, caminhos particulares, arquivos originais do jogo ou binários não
> autorizados. Se qualquer verificação falhar, o push deve ser bloqueado até a correção.
> Releases e tags de versão exigem autorização explícita do usuário.

Repositório público autorizado: <https://github.com/yasumitsuru/mod-traducao-pt-br-renut>.
Conta autorizada: `yasumitsuru`. Projeto de referência: <https://github.com/masterspike52/reNut>.

## Hierarquia e alcance

Esta política vale para o agente principal, orquestradores, subagentes, revisores, agentes de teste,
agentes de documentação e qualquer agente que prepare commits ou pushes. Quem não puder cumpri-la
não deve publicar; deve registrar o bloqueio e deixar o trabalho local íntegro.

## Fluxo obrigatório

1. Implementar a alteração.
2. Executar os testes relevantes.
3. Auditar os arquivos modificados.
4. Revisar cada arquivo novo e confirmar que ele pode ser redistribuído.
5. Revisar o `.gitignore` e testar as regras com `git check-ignore`.
6. Auditar o índice e os commits que seriam enviados.
7. Rodar a verificação de privacidade e o Gitleaks.
8. Preparar a versão pública sanitizada em uma árvore separada.
9. Criar o commit público com identidade noreply.
10. Enviar para a branch `main` sem `--force` e sem `--mirror`.
11. Conferir o conteúdo efetivamente publicado, a Release e as tags.

## Histórico privado e histórico público

O histórico de desenvolvimento local é privado. Ele contém caminhos da máquina, nomes de usuário,
e-mails e outros metadados que não podem ser publicados. Nunca envie esse histórico, nem crie uma
branch pública a partir dele. A árvore pública tem histórico próprio, linear, com um único autor
`yasumitsuru <yasumitsuru@users.noreply.github.com>`.

Não copie `.git` entre projetos, não use `git push --mirror`, não reescreva o histórico privado e
não resolva divergências com `--force`. Se o remoto divergir, busque, compare, transporte apenas as
alterações sanitizadas e resolva os conflitos sem perder trabalho.

## `.gitignore` e inclusão explícita

O `.gitignore` público começa com `*` e libera apenas caminhos conhecidos. Toda nova pasta ou tipo de
arquivo precisa ser adicionado à lista de inclusão e testado. Arquivos já rastreados não são
protegidos por uma regra nova: confira o índice com `git ls-files`.

Ficam fora do repositório público, entre outros:

* Executáveis, DLLs, `.exe`, `.dll`, `.msi`, `.pdb` e binários de teste.
* ISO, XEX, XEXP, DLC, Title Updates, saves, perfis, `Content/`, `TDATA/` e `UDATA/`.
* `renut.toml`, `renut.cfg`, `launcher.cfg`, `renut.exe` e cópias traduzidas.
* Arquivos `.nbpatch`, `.zip`, `.patch` binários e builds de distribuição.
* `data/strings/`, dumps do jogo, capturas com dados privados e conteúdo de terceiros.
* `.env`, tokens, chaves, certificados, logs, dumps, caches, ambientes virtuais e arquivos de IDE.
* Configurações de agentes, checkpoints, fila/estado do Understory e relatórios internos.
* Caminhos absolutos particulares e qualquer metadado da máquina de desenvolvimento.

O código autoral, os catálogos PT-BR, os manifestos, a documentação segura e os testes sanitizados
podem ser publicados quando passarem pelas verificações.

## Auditoria de arquivos novos

Abra o arquivo, confirme o propósito, procure caminhos absolutos, e-mails, tokens, metadados e
referências locais, confirme a origem e os direitos de redistribuição e só então prepare o commit.
Não use `git add .` nem `git add -A` sem revisar o resultado. Prefira inclusão explícita e leia o
diff preparado, inclusive em arquivos binários.

## Sanitização

Substitua caminhos absolutos por caminhos relativos ou placeholders. Use arquivos de exemplo para
configurações. Não copie segredos para relatórios. Se um arquivo não puder ser sanitizado sem perder
a finalidade, exclua-o da publicação.

## Verificações obrigatórias

```text
python -m pytest
python -I tools/verificar_privacidade.py --publico
gitleaks detect --source . --no-banner --redact
git status --porcelain=v1 -uall
git diff --cached --stat
```

O workflow `.github/workflows/testes.yml` roda os testes, a verificação de privacidade e o Gitleaks
em cada push e pull request, sem exigir credenciais privadas. Os ganchos locais `.githooks/pre-commit`
e `.githooks/pre-push` podem ser ativados com:

```text
git config core.hooksPath .githooks
```

Os ganchos não substituem os testes: qualquer um pode ser ignorado. A aprovação exige a saída real
dos comandos, não a intenção de rodá-los.

## Estado do launcher

A tradução do launcher do reNut está na prévia **0.9.0**, não lançada. A cobertura textual é completa
(225/225 entradas do executável + 2 descrições em DLLs), mas a cobertura visual tem estados PASS,
PARTIAL, BLOCKED e NOT_TESTED e **não** é 100%. O `renut.exe` e as DLLs originais nunca são
alterados; o patch é aplicado em cópias.

O patch binário não é distribuído porque o reNut não possui licença formal que autorize redistribuir
binários modificados. O repositório publica o catálogo, o gerador, o aplicador e a documentação; cada
usuário gera o patch na própria cópia. Não publique executáveis completos, DLLs modificadas ou
capturas de terceiros.

O mod do jogo permanece na **v0.7.0** e não deve ser alterado por esta política.

## Releases e tags

Não crie Release, tag de versão, asset de Release ou binário de distribuição sem autorização
explícita do usuário. A Release e a tag **v0.7.0** existentes devem permanecer intactas. Commits
normais na `main` são permitidos depois das verificações.

## Critérios de conclusão

Uma entrega só é concluída quando os testes e as auditorias aplicáveis passam, o diff público foi
revisado, o remoto foi conferido e o relatório registra o que foi publicado, o que ficou de fora e
quais limitações permanecem. Use os estados **PASS**, **PARTIAL**, **BLOCKED** e **NOT_TESTED** com
evidência; nunca declare PASS sem executar o teste correspondente.

## Relatório mínimo

* Repositório e branch sincronizados.
* SHA do último commit público.
* Arquivos adicionados, modificados e excluídos da publicação.
* Regras novas do `.gitignore`.
* Resultado da auditoria do histórico, do Gitleaks e dos testes de privacidade.
* Resultado dos testes funcionais relevantes.
* Confirmação de que o histórico privado foi preservado.
* Confirmação de que nenhuma Release ou tag foi criada e de que a v0.7.0 continua intacta.
* Limitações e próximo passo.