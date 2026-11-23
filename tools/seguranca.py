"""Verificações de segurança para o repositório público e para a árvore local.

Uso:
    python -I tools/verificar_privacidade.py
    python -I tools/verificar_privacidade.py --publico
    python -I tools/verificar_privacidade.py --staged
    python -I tools/verificar_privacidade.py --push --publico

O verificador examina os arquivos rastreados (ou preparados), as regras do `.gitignore`, os
commits que seriam enviados e, no modo público, a licença, a identidade dos commits, o remoto e
as tags. Ele nunca imprime o valor completo de um segredo ou caminho pessoal: só o começo e ***.

Sai com código 1 quando encontra qualquer problema de severidade alta ou média.
"""

from __future__ import annotations

import argparse
import getpass
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

RAIZ_PADRAO = Path(__file__).resolve().parents[1]

# ---------------------------------------------------------------------------------------------
# Arquivos e tipos
# ---------------------------------------------------------------------------------------------

SUFIXOS_PROIBIDOS = (
    ".exe", ".dll", ".pdb", ".lib", ".obj", ".o", ".so", ".dylib", ".msi", ".bin",
    ".iso", ".xex", ".xexp", ".xbe", ".xiso", ".xcp", ".sbp", ".nbpatch", ".zip",
    ".7z", ".rar", ".tar", ".gz", ".dmp", ".log", ".key", ".pem", ".pfx", ".p12",
    ".crt", ".cer", ".kdbx", ".ovpn", ".sav", ".save", ".profile", ".gpd",
)

NOMES_PROIBIDOS = {
    "renut.exe", "renut.toml", "renut.cfg", "launcher.cfg", "account.json",
    "achievements.json", ".env", "id_rsa", "id_ed25519", "thumbs.db", "desktop.ini",
}

PASTAS_PROIBIDAS_SEMPRE = {
    "data/strings", "saves", "profiles", "logs", "crashdumps", "sentry", "gamerpics",
    "secrets", ".venv", "__pycache__", ".pytest_cache", ".understory",
}

PASTAS_PROIBIDAS_PUBLICO = {
    "app", "dist", "build", "target", "work", "user", "guide",
}

SUFIXOS_PERMITIDOS_PUBLICO = {
    ".md", ".py", ".json", ".csv", ".toml", ".txt", ".yml", ".yaml", ".sh",
    ".cmd", ".ps1", ".ini",
}

NOMES_PERMITIDOS_PUBLICO = {
    ".gitignore", ".gitattributes", "LICENSE", "NOTICE.md", "AGENTS.md",
    "pytest.ini", ".githooks/pre-commit", ".githooks/pre-push",
}

# ---------------------------------------------------------------------------------------------
# Padrões de conteúdo
# ---------------------------------------------------------------------------------------------

RE_CAMINHO = re.compile(r"(?<![A-Za-z0-9])[A-Za-z]:[\\/][^\s\"'<>|*?\r\n]{1,240}")
RE_UNC = re.compile(r"\\\\[A-Za-z0-9._-]{1,64}\\[^\s\"'<>|*\r\n]{1,200}")
RE_FILE_URL = re.compile(r"file:///[A-Za-z]:[^\s\"'<>|*\r\n]{1,240}", re.IGNORECASE)
RE_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}")
RE_TOKEN_GITHUB = re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")
RE_TOKEN_GITHUB_FINO = re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")
RE_CHAVE_AWS = re.compile(r"\bAKIA[0-9A-Z]{16}\b")
RE_CHAVE_OPENAI = re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b")
RE_CHAVE_ANTHROPIC = re.compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}\b")
RE_CHAVE_PRIVADA = re.compile(r"-----BEGIN [A-Z0-9 ]{0,40}PRIVATE KEY-----")
RE_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\b")
RE_CREDENCIAL = re.compile(
    r"(?i)\b(api[_-]?key|apikey|secret|senha|password|passwd|token|bearer)\b"
    r"\s*[:=]\s*[\"']?([A-Za-z0-9_\-./+=]{12,})"
)
RE_IP_PRIVADO = re.compile(
    r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}"
    r"|192\.168\.\d{1,3}\.\d{1,3}"
    r"|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b"
)

MARCAS_PESSOAIS = (
    "\\users\\", "/users/", "onedrive", "appdata", "\\decomp\\", "\\desktop\\",
    "\\documents\\", "\\downloads\\", "program files", "\\quiverlauncher",
)
MARCAS_EXEMPLO = (
    "<pasta", "<usuario", "caminho\\para", "caminho/para", "c:\\jogos\\",
    "c:/jogos/", "c:\\games\\", "c:/games/",
)
USUARIO_LOCAL = getpass.getuser()
USUARIOS_GENERICOS = {"runner", "user", "users", "root", "admin", "administrator"}
# Nomes genéricos de CI não geram ruído. O usuário real desta máquina não está na lista: se
# aparecer no conteúdo público, a verificação precisa falhar.

EMAILS_IGNORADOS = ("users.noreply.github.com", "example.com")

REMOTOS_PERMITIDOS = {
    "https://github.com/yasumitsuru/mod-traducao-pt-br-renut.git",
    "https://github.com/yasumitsuru/mod-traducao-pt-br-renut",
}
EMAIL_PUBLICO = "yasumitsuru@users.noreply.github.com"
TAGS_PERMITIDAS = {"v0.7.0"}


@dataclass(frozen=True)
class Problema:
    categoria: str
    severidade: str  # alto | medio | baixo
    origem: str
    linha: int
    trecho: str

    def como_texto(self) -> str:
        return f"{self.origem}:{self.linha}: {self.categoria}: {self.trecho}"

    def como_dict(self) -> dict:
        return {
            "categoria": self.categoria,
            "severidade": self.severidade,
            "origem": self.origem,
            "linha": self.linha,
            "trecho": self.trecho,
        }


def _redigir(texto: str, manter: int = 6) -> str:
    limpo = texto.strip().replace("\x00", "")
    if len(limpo) <= manter:
        return "***"
    return limpo[:manter] + "***"


def _redigir_email(email: str) -> str:
    usuario, _, dominio = email.partition("@")
    tld = dominio.rsplit(".", 1)[-1] if "." in dominio else ""
    return f"{usuario[:2]}***@***{('.' + tld) if tld else ''}"


def classificar_caminho(caminho: str) -> tuple[str, str] | None:
    """Devolve (categoria, severidade) ou None para caminhos genéricos de exemplo."""
    baixo = caminho.replace("/", "\\").lower()
    if any(marca in baixo for marca in MARCAS_PESSOAIS):
        return ("caminho_pessoal", "alto")
    if any(marca in baixo for marca in MARCAS_EXEMPLO):
        return None
    if baixo.startswith("\\\\"):
        return ("caminho_rede", "medio")
    return ("caminho_absoluto", "baixo")


def examinar_texto(texto: str, origem: str) -> list[Problema]:
    problemas: list[Problema] = []
    vistos: set[tuple[str, str, int, str]] = set()

    def registrar(categoria: str, severidade: str, numero: int, valor: str) -> None:
        problema = Problema(categoria, severidade, origem, numero, _redigir(valor))
        chave = (categoria, origem, numero, problema.trecho)
        if chave not in vistos:
            vistos.add(chave)
            problemas.append(problema)

    for numero, linha in enumerate(texto.splitlines(), start=1):
        for achado in RE_CAMINHO.finditer(linha):
            classe = classificar_caminho(achado.group(0))
            if classe is not None:
                registrar(classe[0], classe[1], numero, achado.group(0))
        for achado in RE_UNC.finditer(linha):
            registrar("caminho_rede", "baixo", numero, achado.group(0))
        for achado in RE_FILE_URL.finditer(linha):
            registrar("caminho_pessoal", "alto", numero, achado.group(0))

        for achado in RE_EMAIL.finditer(linha):
            email = achado.group(0)
            categoria = "email_noreply" if any(t in email.lower() for t in EMAILS_IGNORADOS) else "email"
            severidade = "baixo" if categoria == "email_noreply" else "alto"
            problema = Problema(categoria, severidade, origem, numero, _redigir_email(email))
            chave = (categoria, origem, numero, problema.trecho)
            if chave not in vistos:
                vistos.add(chave)
                problemas.append(problema)

        for categoria, severidade, regex in (
            ("token_github", "alto", RE_TOKEN_GITHUB),
            ("token_github", "alto", RE_TOKEN_GITHUB_FINO),
            ("chave_aws", "alto", RE_CHAVE_AWS),
            ("chave_ia", "alto", RE_CHAVE_OPENAI),
            ("chave_ia", "alto", RE_CHAVE_ANTHROPIC),
            ("chave_privada", "alto", RE_CHAVE_PRIVADA),
            ("token_jwt", "alto", RE_JWT),
            ("credencial", "alto", RE_CREDENCIAL),
            ("ip_privado", "medio", RE_IP_PRIVADO),
        ):
            for achado in regex.finditer(linha):
                registrar(categoria, severidade, numero, achado.group(0))

        if USUARIO_LOCAL and len(USUARIO_LOCAL) >= 4 and USUARIO_LOCAL.lower() not in USUARIOS_GENERICOS:
            for achado in re.finditer(re.escape(USUARIO_LOCAL), linha, re.IGNORECASE):
                registrar("nome_de_usuario", "alto", numero, achado.group(0))

    return problemas


def examinar_bytes(dados: bytes, origem: str) -> list[Problema]:
    if not dados:
        return []
    if b"\x00" in dados[:8192]:
        return [Problema("arquivo_binario", "alto", origem, 0, "conteúdo binário")]
    return examinar_texto(dados.decode("utf-8", "ignore"), origem)


# ---------------------------------------------------------------------------------------------
# Git
# ---------------------------------------------------------------------------------------------


def _git(raiz: Path, *args: str, texto: bool = True) -> str | bytes:
    resultado = subprocess.run(
        ["git", "-C", str(raiz), *args],
        capture_output=True,
        check=False,
    )
    if resultado.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} falhou: {resultado.stderr.decode('utf-8', 'replace').strip()}"
        )
    return resultado.stdout.decode("utf-8", "replace") if texto else resultado.stdout


def arquivos_rastreados(raiz: Path) -> list[str]:
    saida = _git(raiz, "ls-files", "-z", texto=False)
    return [nome for nome in saida.decode("utf-8", "replace").split("\x00") if nome]


def arquivos_estagiados(raiz: Path) -> list[str]:
    saida = _git(raiz, "diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR", texto=False)
    return [nome for nome in saida.decode("utf-8", "replace").split("\x00") if nome]


def _intervalo_commits(raiz: Path) -> str:
    try:
        upstream = _git(raiz, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}").strip()
    except RuntimeError:
        upstream = ""
    if upstream:
        return f"{upstream}..HEAD"
    try:
        _git(raiz, "rev-parse", "--verify", "origin/main")
        return "origin/main..HEAD"
    except RuntimeError:
        return "HEAD"


def _ler_objetos(raiz: Path, ids: list[str]) -> dict[str, bytes]:
    if not ids:
        return {}
    entrada = ("\n".join(ids) + "\n").encode()
    processo = subprocess.run(
        ["git", "-C", str(raiz), "cat-file", "--batch"],
        input=entrada,
        capture_output=True,
        check=False,
    )
    dados = processo.stdout
    posicao = 0
    blobs: dict[str, bytes] = {}
    while posicao < len(dados):
        quebra = dados.find(b"\n", posicao)
        if quebra < 0:
            break
        cabecalho = dados[posicao:quebra].split()
        posicao = quebra + 1
        if len(cabecalho) < 3:
            continue
        oid = cabecalho[0].decode()
        tipo = cabecalho[1]
        tamanho = int(cabecalho[2])
        conteudo = dados[posicao : posicao + tamanho]
        posicao += tamanho + 1
        if tipo == b"blob":
            blobs[oid] = conteudo
    return blobs


def examinar_commits(raiz: Path) -> list[Problema]:
    intervalo = _intervalo_commits(raiz)
    problemas: list[Problema] = []

    formato = "%H%x1f%an%x1f%ae%x1f%B%x1e"
    saida = _git(raiz, "log", f"--format={formato}", intervalo)
    for registro in saida.split("\x1e"):
        partes = registro.strip("\n").split("\x1f")
        if len(partes) < 4:
            continue
        sha, autor, email, mensagem = partes[:4]
        problemas.extend(examinar_texto(autor, f"commit:{sha[:12]}:autor"))
        problemas.extend(examinar_texto(email, f"commit:{sha[:12]}:email"))
        problemas.extend(examinar_texto(mensagem, f"commit:{sha[:12]}:mensagem"))

    caminhos: dict[str, list[str]] = {}
    for linha in _git(raiz, "rev-list", "--objects", intervalo).splitlines():
        partes = linha.split(" ", 1)
        if len(partes) == 2:
            caminhos.setdefault(partes[0], []).append(partes[1])

    for oid, dados in _ler_objetos(raiz, list(caminhos)).items():
        rotulo = f"blob:{oid[:12]}"
        onde = caminhos.get(oid, [])
        if onde:
            rotulo += f" ({onde[0]})"
        problemas.extend(examinar_bytes(dados, rotulo))

    vistos: set[tuple[str, str, int, str]] = set()
    unicos: list[Problema] = []
    for problema in problemas:
        chave = (problema.categoria, problema.origem, problema.linha, problema.trecho)
        if chave not in vistos:
            vistos.add(chave)
            unicos.append(problema)
    return unicos


# ---------------------------------------------------------------------------------------------
# Regras de arquivos e do .gitignore
# ---------------------------------------------------------------------------------------------


def _partes(nome: str) -> tuple[str, ...]:
    return tuple(parte.lower() for parte in Path(nome).parts)


def _nome_proibido(nome: str, publico: bool) -> str | None:
    baixo = nome.lower()
    partes = _partes(nome)
    if baixo.rsplit("/", 1)[-1] in NOMES_PROIBIDOS:
        return "nome proibido"
    if any(baixo.endswith(sufixo) for sufixo in SUFIXOS_PROIBIDOS):
        return "extensão proibida"
    pastas = set(PASTAS_PROIBIDAS_SEMPRE)
    if publico:
        pastas |= PASTAS_PROIBIDAS_PUBLICO
    for pasta in pastas:
        if pasta in partes or baixo.startswith(pasta + "/"):
            return f"pasta proibida ({pasta})"
    if publico:
        if baixo in {item.lower() for item in NOMES_PERMITIDOS_PUBLICO}:
            return None
        sufixo = Path(baixo).suffix
        if sufixo not in SUFIXOS_PERMITIDOS_PUBLICO:
            return "tipo não permitido no repositório público"
    return None


def examinar_arquivos(raiz: Path, nomes: list[str], publico: bool) -> list[Problema]:
    problemas: list[Problema] = []
    for nome in nomes:
        caminho = raiz / nome
        if not caminho.is_file():
            continue
        motivo = _nome_proibido(nome, publico)
        if motivo:
            problemas.append(Problema("arquivo_proibido", "alto", nome, 0, motivo))
            continue
        problemas.extend(examinar_bytes(caminho.read_bytes(), nome))
    return problemas


def _esta_ignorado(raiz: Path, nome: str) -> bool:
    resultado = subprocess.run(
        ["git", "-C", str(raiz), "check-ignore", "--no-index", "-q", "--", nome],
        capture_output=True,
        check=False,
    )
    return resultado.returncode == 0


def validar_gitignore(raiz: Path, publico: bool) -> list[Problema]:
    problemas: list[Problema] = []
    caminho = raiz / ".gitignore"
    if not caminho.is_file():
        return [Problema("gitignore", "alto", ".gitignore", 0, "arquivo ausente")]
    texto = caminho.read_text(encoding="utf-8", errors="replace")
    linhas = [linha.strip() for linha in texto.splitlines() if linha.strip() and not linha.lstrip().startswith("#")]

    if publico:
        if not linhas or linhas[0] != "*":
            problemas.append(Problema("gitignore", "alto", ".gitignore", 1, "a primeira regra deve ser *"))
        for exigido in (
            "!/.gitignore", "!/README.md", "!/LICENSE", "!/NOTICE.md", "!/AGENTS.md",
            "!/launcher-patch/", "!/launcher-patch/**", "!/tools/", "!/tests/",
            "!/docs/", "!/.githooks/", "!/.github/",
        ):
            if exigido not in linhas:
                problemas.append(Problema("gitignore", "alto", ".gitignore", 0, f"falta {exigido}"))
        for proibido in ("*.exe", "*.dll", "*.patch", "*.nbpatch", "*.zip", "*.iso", "*.xex",
                         "data/strings/", "renut.toml", "renut.cfg", ".env"):
            if proibido not in linhas:
                problemas.append(Problema("gitignore", "alto", ".gitignore", 0, f"falta bloquear {proibido}"))
        for nome in ("README.md", "AGENTS.md", "launcher-patch/aplicar.py"):
            if _esta_ignorado(raiz, nome):
                problemas.append(Problema("gitignore", "alto", ".gitignore", 0, f"liberação não funciona: {nome}"))
        for nome in ("segredo.exe", "launcher-patch/renut_launcher_ptbr.patch", "data/strings/x.json"):
            if not _esta_ignorado(raiz, nome):
                problemas.append(Problema("gitignore", "alto", ".gitignore", 0, f"regra não bloqueia: {nome}"))
    else:
        for exigido in ("*.exe", "*.dll", "*.nbpatch", "*.zip", "*.iso", "*.xex",
                        "data/strings/", "renut.toml", "renut.cfg", ".env", ".venv/", "__pycache__/"):
            if exigido not in linhas:
                problemas.append(Problema("gitignore", "alto", ".gitignore", 0, f"falta bloquear {exigido}"))
        if _esta_ignorado(raiz, "launcher-patch/renut_launcher_ptbr.patch"):
            problemas.append(Problema("gitignore", "alto", ".gitignore", 0, "o patch do launcher está ignorado"))
        if not _esta_ignorado(raiz, "segredo.exe"):
            problemas.append(Problema("gitignore", "alto", ".gitignore", 0, "*.exe não está bloqueado"))

    for nome in arquivos_rastreados(raiz):
        motivo = _nome_proibido(nome, publico)
        if motivo:
            problemas.append(Problema("arquivo_proibido", "alto", nome, 0, motivo))
    return problemas


def validar_licenca(raiz: Path) -> list[Problema]:
    problemas: list[Problema] = []
    licenca = raiz / "LICENSE"
    aviso = raiz / "NOTICE.md"
    if not licenca.is_file():
        problemas.append(Problema("licenca", "alto", "LICENSE", 0, "arquivo ausente"))
    elif "MIT" not in licenca.read_text(encoding="utf-8", errors="replace"):
        problemas.append(Problema("licenca", "alto", "LICENSE", 0, "licença MIT não encontrada"))
    if not aviso.is_file():
        problemas.append(Problema("licenca", "alto", "NOTICE.md", 0, "arquivo ausente"))
    else:
        texto = aviso.read_text(encoding="utf-8", errors="replace")
        for termo in ("Rare", "Microsoft", "reNut", "não"):
            if termo not in texto:
                problemas.append(Problema("licenca", "alto", "NOTICE.md", 0, f"falta menção a {termo}"))
    return problemas


def validar_identidade(raiz: Path) -> list[Problema]:
    problemas: list[Problema] = []
    # Em pull request o checkout é um commit de merge temporário, com autor e branch do GitHub.
    # A identidade noreply é exigida nos pushes para a main, não no commit efêmero do PR.
    em_pr = (
        os.environ.get("GITHUB_ACTIONS") == "true"
        and os.environ.get("GITHUB_EVENT_NAME") == "pull_request"
    )
    ramo = _git(raiz, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if ramo != "main" and not em_pr:
        problemas.append(Problema("identidade", "alto", "git", 0, f"branch atual é {ramo}"))
    autores = {
        linha.strip()
        for linha in _git(raiz, "log", "--format=%ae").splitlines()
        if linha.strip()
    }
    extras = autores - {EMAIL_PUBLICO}
    if extras and not em_pr:
        problemas.append(Problema("identidade", "alto", "git", 0, f"e-mails fora do noreply: {len(extras)}"))
    remotos = [linha for linha in _git(raiz, "remote", "-v").splitlines() if linha.strip()]
    urls = {partes[1] for linha in remotos if len(partes := linha.split()) >= 2}
    if not urls:
        problemas.append(Problema("identidade", "medio", "git", 0, "nenhum remoto configurado"))
    elif urls - REMOTOS_PERMITIDOS:
        problemas.append(Problema("identidade", "alto", "git", 0, "remoto fora da lista autorizada"))
    sujo = _git(raiz, "status", "--porcelain=v1", "-uall").strip()
    if sujo:
        problemas.append(Problema("identidade", "alto", "git", 0, "árvore pública com alterações pendentes"))
    return problemas


def validar_tags(raiz: Path) -> list[Problema]:
    tags = {linha.strip() for linha in _git(raiz, "tag", "-l").splitlines() if linha.strip()}
    extras = tags - TAGS_PERMITIDAS
    if extras:
        return [Problema("tag", "alto", "git", 0, f"tags não autorizadas: {len(extras)}")]
    return []


# ---------------------------------------------------------------------------------------------
# API e linha de comando
# ---------------------------------------------------------------------------------------------


def examinar(raiz: Path | None = None, publico: bool = False) -> list[str]:
    raiz = (raiz or RAIZ_PADRAO).resolve()
    problemas: list[Problema] = []
    nomes = arquivos_rastreados(raiz)
    problemas.extend(examinar_arquivos(raiz, nomes, publico))
    problemas.extend(validar_gitignore(raiz, publico))
    if publico:
        problemas.extend(validar_licenca(raiz))
        problemas.extend(validar_identidade(raiz))
        problemas.extend(validar_tags(raiz))
    return [problema.como_texto() for problema in problemas if problema.severidade in ("alto", "medio")]


def _imprimir(problemas: list[Problema], rotulo: str) -> int:
    graves = [problema for problema in problemas if problema.severidade in ("alto", "medio")]
    baixos = [problema for problema in problemas if problema.severidade == "baixo"]
    if not graves:
        print(f"{rotulo}: PASS")
        if baixos:
            print(f"  {len(baixos)} aviso(s) informativo(s) de caminho absoluto/rede; não bloqueiam.")
        return 0
    print(f"{rotulo}: FAIL ({len(graves)} problema(s))")
    for problema in graves:
        print(f"  {problema.como_texto()}")
    return 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verificação de privacidade e segurança")
    parser.add_argument("--raiz", default=None, help="raiz do repositório (padrão: pasta do projeto)")
    parser.add_argument("--publico", action="store_true", help="aplica a política de inclusão explícita")
    parser.add_argument("--staged", action="store_true", help="examina apenas o que está preparado")
    parser.add_argument("--push", action="store_true", help="examina os commits que seriam enviados")
    args = parser.parse_args(argv)

    raiz = Path(args.raiz).resolve() if args.raiz else RAIZ_PADRAO
    if not (raiz / ".git").exists():
        print(f"Raiz sem repositório Git: {raiz}", file=sys.stderr)
        return 1

    problemas: list[Problema] = []
    if args.staged:
        nomes = arquivos_estagiados(raiz)
        if not nomes:
            print("Nada preparado; a verificação de commit não tem o que examinar.")
        problemas.extend(examinar_arquivos(raiz, nomes, args.publico))
        problemas.extend(validar_gitignore(raiz, args.publico))
    else:
        nomes = arquivos_rastreados(raiz)
        problemas.extend(examinar_arquivos(raiz, nomes, args.publico))
        problemas.extend(validar_gitignore(raiz, args.publico))
        if args.publico:
            problemas.extend(validar_licenca(raiz))
            problemas.extend(validar_identidade(raiz))
            problemas.extend(validar_tags(raiz))
        if args.push:
            problemas.extend(examinar_commits(raiz))

    rotulo = "Privacidade pública" if args.publico else "Privacidade"
    return _imprimir(problemas, rotulo)


if __name__ == "__main__":
    raise SystemExit(main())