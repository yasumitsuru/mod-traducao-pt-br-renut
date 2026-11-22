"""Verificação de privacidade dos arquivos rastreados.

Uso:
    python -I tools/verificar_privacidade.py [raiz]

Sai com código 1 quando encontra caminho pessoal, e-mail, credencial ou arquivo proibido.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]

PROIBIDOS = (
    ".nbpatch", ".zip", ".iso", ".xex", ".xexp", ".sbp", ".dmp", ".log",
    ".key", ".pem", "renut.toml", "renut.cfg",
)

PADROES = (
    ("caminho_pessoal", re.compile(r"[A-Za-z]:[\\/][^\s\"\'<>|]*?(?:\\Users\\|/Users/|OneDrive|AppData)", re.IGNORECASE)),
    ("email", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,24}")),
    ("token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9_-]{20,})\b")),
    ("chave_privada", re.compile(r"-----BEGIN [A-Z0-9 ]{0,40}PRIVATE KEY-----")),
    ("credencial", re.compile(r"(?i)\b(?:api[_-]?key|secret|password|passwd|token)\b\s*[:=]\s*[\"\']?[A-Za-z0-9_\-./+=]{12,}")),
)

IGNORAR_EMAIL = ("users.noreply.github.com", "example.com")


def arquivos_rastreados(raiz: Path) -> list[str]:
    try:
        saida = subprocess.run(
            ["git", "-C", str(raiz), "ls-files", "-z"],
            capture_output=True,
            check=True,
        ).stdout.decode("utf-8", "replace")
        return [nome for nome in saida.split("\x00") if nome]
    except (OSError, subprocess.CalledProcessError):
        return sorted(
            p.relative_to(raiz).as_posix()
            for p in raiz.rglob("*")
            if p.is_file() and ".git" not in p.parts
        )


def examinar(raiz: Path) -> list[str]:
    problemas: list[str] = []
    for nome in arquivos_rastreados(raiz):
        baixo = nome.lower()
        if any(baixo.endswith(sufixo) for sufixo in PROIBIDOS):
            problemas.append(f"arquivo proibido: {nome}")
            continue
        caminho = raiz / nome
        if not caminho.is_file():
            continue
        dados = caminho.read_bytes()
        if b"\x00" in dados[:8192]:
            problemas.append(f"arquivo binario rastreado: {nome}")
            continue
        texto = dados.decode("utf-8", "ignore")
        for numero, linha in enumerate(texto.splitlines(), start=1):
            for categoria, padrao in PADROES:
                achado = padrao.search(linha)
                if not achado:
                    continue
                valor = achado.group(0)
                if categoria == "email" and any(tema in valor for tema in IGNORAR_EMAIL):
                    continue
                problemas.append(f"{nome}:{numero}: {categoria}: {valor[:6]}***")
    return problemas


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    raiz = Path(argv[0]).resolve() if argv else RAIZ
    problemas = examinar(raiz)
    if problemas:
        print(f"{len(problemas)} problema(s) de privacidade:")
        for problema in problemas:
            print(f"  {problema}")
        return 1
    print("Privacidade: nenhum padrão sensível nos arquivos rastreados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
