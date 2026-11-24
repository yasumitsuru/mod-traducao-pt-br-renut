"""Auditoria de qualidade da tradução (revisão 0.8.0).

Complementa o validador (F3). O validador garante que o arquivo do jogo continua válido
(códigos, fonte, nomes protegidos); esta auditoria junta inglês, espanhol e PT-BR de cada entrada,
classifica a categoria e aponta, por heurística, problemas de qualidade que o validador não
cobre: texto que ficou em inglês, português europeu, pontuação divergente, números perdidos,
espaço em volta de ícones, crase e concordância comuns, inconsistência entre frases iguais etc.

Os achados são **candidatos**: quem decide é a revisão humana/linguística. Nenhum achado vira
correção automática.

Somente leitura sobre `data/`. As saídas ficam em `work/revisao/` (fora do git), porque juntam o
texto original do jogo.
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field

from . import codigos, protegidos
from .extrair import carregar_strings, carregar_traducao, hash_texto, nomes_traducao
from .io_seguro import RAIZ_PROJETO
from .validar import carregar_glossario, validar_frase

PASTA_SAIDA = RAIZ_PROJETO / "work" / "revisao"

# --------------------------------------------------------------------------------------------
# Classificação


MUNDOS = (
    ("showdowntown", "Showdown Town"),
    ("spiralmountain", "Spiral Mountain"),
    ("nuttyacres", "Nutty Acres"),
    ("banjoland", "Banjoland"),
    ("cpu", "LOGBOX 720"),
    ("worldofsport", "Jiggosseum"),
    ("terrorium", "Terrarium of Terror"),
)

# asset (sem o prefixo aid_loctext_banjox_) -> categoria
CATEGORIAS_FIXAS = {
    "ui_frontend": "menu",
    "frontend": "menu",
    "error": "menu",
    "ui_multiplayerfrontend": "multijogador",
    "ui_ingame_main": "hud",
    "ui_ingame_buttonmenu": "hud",
    "ui_ingame_movie": "menu",
    "ui_ingame_garage": "garagem",
    "ui_ingame_challengereqs": "desafio",
    "ui_htmlstylesheet": "tecnico",
    "credits": "creditos",
    "challenges": "desafio",
    "livechallenges": "desafio",
    "challenge_wimpout": "desafio",
    "instructions_challengestart": "desafio",
    "instructions_garage": "tutorial",
    "instructions_general": "tutorial",
    "garagetutorial_default": "tutorial",
    "vehicles": "pecas",
    "blocks": "pecas",
    "spiralmountain_logquiz": "quiz",
    "showdowntown_policelaws": "info",
    "showdowntown_warppads": "info",
    "showdowntown_safehouses": "info",
    "showdowntown_gameglobes": "info",
    "showdowntown_jigovend": "info",
    "banjoland_infopoints": "info",
    "spiralmountain_infopoints": "info",
    "tempplaceholder_style": "teste",
    "ui_ingame_dialog_test": "teste",
}

PERSONAGEM_POR_ASSET = {
    "showdowntown_humba": "Humba Wumba",
    "showdowntown_grunty": "Gruntilda",
    "showdowntown_klungo": "Klungo",
    "showdowntown_log": "L.O.G. (S.J.)",
    "showdowntown_jinjos": "Jinjos",
    "jinjos": "Jinjos",
    "spiralmountain_logquiz": "L.O.G. (S.J.)",
}

CATEGORIAS_UI = {"menu", "multijogador", "hud", "garagem", "pecas"}


def asset_curto(asset: str) -> str:
    return asset.replace("aid_loctext_banjox_", "")


def categoria(asset: str, chave: str = "") -> str:
    a = asset_curto(asset)
    if a in CATEGORIAS_FIXAS:
        return CATEGORIAS_FIXAS[a]
    if a.startswith("test_"):
        return "teste"
    return "dialogo"


def mundo(asset: str) -> str | None:
    a = asset_curto(asset)
    if a.startswith("tt_"):
        a = a[3:]
    for prefixo, nome in MUNDOS:
        if a.startswith(prefixo):
            return nome
    return None


def personagem_provavel(asset: str) -> str | None:
    return PERSONAGEM_POR_ASSET.get(asset_curto(asset))


# --------------------------------------------------------------------------------------------
# Utilidades de texto


def sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def visivel(texto: str) -> str:
    return codigos.sem_codigos(texto or "")


def _nomes_mantidos() -> list[str]:
    """Nomes que ficam em inglês de propósito (protegidos + termos 'manter' do glossário)."""
    nomes = {n.nome for n in protegidos.carregar()}
    for t in carregar_glossario():
        if t.termo_ptbr and t.termo_en and t.termo_ptbr.lower() == t.termo_en.lower():
            nomes.add(t.termo_ptbr)
    nomes |= {"Stop 'n' Swop", "Xbox LIVE", "Xbox 360", "Xbox", "Mk.", "Gamertag", "Nuts & Bolts",
              "Banjo-Kazooie", "Rare", "Microsoft", "Game Studios", "LOGBOX", "Klungo's Arcade"}
    return sorted(nomes, key=len, reverse=True)


def remover_nomes(texto: str, nomes: list[str]) -> str:
    for n in nomes:
        texto = re.sub(rf"(?<!\w){re.escape(n)}(?!\w)", " ", texto, flags=re.IGNORECASE)
    return texto


PALAVRAS_EN = {
    "the", "and", "you", "your", "with", "this", "that", "are", "what", "have", "will", "but",
    "just", "don't", "it's", "i'm", "you're", "of", "is", "it", "to", "be", "we", "they",
    "from", "there", "here", "press", "select", "back", "cancel", "yes", "please", "loading",
    "player", "players", "game", "games", "level", "score", "time", "start", "quit", "exit",
    "save", "load", "continue", "options", "settings", "challenge", "vehicle", "vehicles",
    "parts", "part", "wheel", "wheels", "engine", "fuel", "ammo", "weapon", "garage", "back",
    "next", "previous", "done", "close", "open", "new", "delete", "confirm", "error", "warning",
    "lap", "laps", "race", "win", "lose", "winner", "loser", "round", "team", "red", "blue",
    "very", "much", "now", "then", "when", "where", "why", "how", "who", "can't", "won't",
    "let's", "i'll", "we're", "they're", "isn't", "aren't", "wasn't", "would", "could", "should",
    "my", "our", "their", "his", "her", "him", "she", "he", "them", "an", "or", "if", "on",
    "in", "at", "by", "for", "not", "all", "get", "got", "go", "come", "see", "look",
    "out", "up", "down", "off", "over", "into", "about", "some", "any", "one", "two", "three",
}
# palavras inglesas que também são PT-BR comum ou aparecem em nomes já mantidos
FALSOS_EN = {"for", "continue", "some", "round", "total", "cinema", "laser", "spoiler", "feedback",
             "a", "e", "o", "no", "do", "me", "as", "se", "te", "la", "ok", "pro", "mega", "super",
             "turbo", "game", "bingo", "show", "fan", "fans", "chip", "hit", "kart", "mix", "online",
             "replay", "jet", "radar", "robot", "status", "test", "time", "laser", "drag", "rally",
             "gamertag", "on", "off", "in", "an", "he", "her", "his", "go", "one", "two"}

PT_EUROPEU = [
    (r"\b(estás|estáis|vós|vosso|vossa|vossos|vossas|connosco|convosco)\b", "pronome/verbo de 2ª pessoa (pt-PT)"),
    (r"\b(ecrã|ecrãs|equipa|equipas|autocarro|comboio|telemóvel|rapariga|raparigas|casa de banho|"
     r"utilizador|utilizadores|ficheiro|ficheiros|registo|registos|facto|acção|acções|"
     r"óptimo|óptima|actual|actualmente|direcção|objectivo|objectivos|contacto|contactos|"
     r"pequeno-almoço|guarda-redes|relvado|golo|golos|sítio|miúdo|miúdos|bué)\b",
     "vocabulário/grafia de pt-PT"),
    (r"\b(estou|estás|está|estamos|estão|estava|estavas|estávamos|estavam|continua|continuo|"
     r"continuas|fica|ficas|fico|andas|anda|ando) a [a-zà-ú]+(ar|er|ir)\b",
     "progressivo 'estar a + infinitivo' (pt-PT)"),
]
TU_RE = re.compile(r"\b(tu|teu|tua|teus|tuas|contigo|ti)\b", re.IGNORECASE)
VOCE_RE = re.compile(r"\b(você|vocês|seu|sua|seus|suas)\b", re.IGNORECASE)

GRAMATICA = [
    (r"\bà (ele|ela|eles|elas|você|vocês|um|uma|este|esta|esse|essa|isso|isto|aquilo|nós|mim|ti|"
     r"todos|todas|partir|cada|qualquer|ninguém|alguém|me|te|se|lhe|lhes|eu)\b", "crase indevida", "HIGH"),
    (r"(?<![\wÀ-ú])[Aa]s vezes\b", "falta crase em 'às vezes'", "HIGH"),
    (r"\bhouveram\b", "'haver' impessoal no plural", "HIGH"),
    (r"\bfazem (\w+ )?(anos|meses|dias|semanas|horas|minutos|séculos|eras)\b", "'fazer' impessoal no plural", "HIGH"),
    (r"\b(seje|esteje|menas|concerteza|derrepente|porisso|agente vai|agente pode|agente tem)\b", "grafia incorreta", "HIGH"),
    (r"\b(para|pra) mim (fazer|ir|ver|ganhar|ter|ser|dar|pegar|poder|usar|correr|jogar|vencer|terminar)\b",
     "'mim' como sujeito de infinitivo", "HIGH"),
    (r"\b(eles|elas|vocês) (tem|vem)\b", "falta acento de plural (têm/vêm)", "HIGH"),
    (r"\bhá (\w+ ){1,3}atrás\b", "redundância 'há ... atrás'", "LOW"),
    (r"\b(a nível de)\b", "construção desaconselhada", "LOW"),
    (r"\bmais (melhor|pior)\b", "comparativo duplo", "HIGH"),
]

REPETIDA_RE = re.compile(r"(?<![\wÀ-ú])([A-Za-zÀ-ú]+)\s+\1(?![\wÀ-ú])", re.IGNORECASE)
REPETIDA_OK = {"ha", "há", "he", "hi", "ho", "hu", "não", "nao", "bem", "muito", "muita", "lá", "la",
               "ai", "ah", "oh", "uh", "rá", "ra", "pi", "bip", "toc", "tic", "blá", "bla", "rá-rá",
               "zum", "ui", "olá", "sim", "vai", "corre", "rápido", "cá", "ei", "ô", "oba", "bom",
               "pare", "mais", "volta", "eba", "ops", "glub", "buá", "hum", "hã", "é", "ah-ha"}

ESPACO_ANTES_RE = re.compile(r" [,.;:!?](?![.])")
SEM_ESPACO_DEPOIS_RE = re.compile(r"[,;!?](?=[A-Za-zÀ-ú])")
MAIUSCULA_APOS_PONTO_RE = re.compile(r"(?<![.\w])(\w{1,4})?\.\s+([a-zà-ú])")
ABREV_OK = {"sr", "sra", "srta", "dr", "dra", "mk", "etc", "vs", "nº", "n", "s", "j", "g", "pág", "km",
            "min", "seg", "máx", "mín", "ex", "aprox", "trans", "transf", "prof", "st", "jr", "mr", "mrs"}
NUMERO_RE = re.compile(r"\d+(?:[.,]\d+)*")
MOJIBAKE_RE = re.compile(r"Ã[©£§¡¢ª³µº‰¨´¶]|â€|Â[ ­°ºª]")
SUSPEITOS = {"�": "caractere de substituição",
             " ": "espaço não separável", "​": "espaço de largura zero", "\t": "tabulação"}


def _numeros(texto: str) -> Counter:
    return Counter(re.sub(r"[.,]", "", n) for n in NUMERO_RE.findall(visivel(texto)))


def _final(texto: str) -> str:
    v = visivel(texto).rstrip()
    v = v.rstrip("\"'”’»)")
    return v[-1:] if v else ""


def _inicio_letra(texto: str) -> str:
    v = visivel(texto).lstrip(" \"'“‘«(-–—.…")
    return v[:1]


def _espacos_codigos(texto: str) -> list[tuple[str, bool, bool]]:
    """Para cada ícone de botão: (código, espaço antes?, espaço depois?)."""
    out = []
    for m in codigos.CODIGO_RE.finditer(texto):
        c = m.group(0)
        if not c.startswith("["):
            continue
        antes = m.start() == 0 or texto[m.start() - 1] in " (\"“"
        depois = m.end() == len(texto) or texto[m.end()] in " .,;:!?)\"”…"
        out.append((c, antes, depois))
    return out


def _ngramas(palavras: list[str], n: int) -> set[tuple[str, ...]]:
    return {tuple(palavras[i:i + n]) for i in range(len(palavras) - n + 1)}


PALAVRA_RE = re.compile(r"[A-Za-zÀ-ú']+")


@dataclass
class Achado:
    regra: str
    gravidade: str
    mensagem: str

    def como_dict(self) -> dict:
        return {"regra": self.regra, "gravidade": self.gravidade, "mensagem": self.mensagem}


@dataclass
class Contexto:
    nomes_mantidos: list[str] = field(default_factory=_nomes_mantidos)
    glossario: list = field(default_factory=carregar_glossario)


def auditar_frase(en: str, es: str | None, pt: str, cat: str, ctx: Contexto) -> list[Achado]:
    """Heurísticas de qualidade para uma entrada já traduzida."""
    out: list[Achado] = []
    if not pt:
        return out
    ven, vpt = visivel(en), visivel(pt)

    # 1. idêntico ao inglês / inglês remanescente
    letras_en = re.sub(r"[^A-Za-z]", "", remover_nomes(ven, ctx.nomes_mantidos))
    if en and pt == en and len(letras_en) >= 3 and cat not in {"tecnico", "creditos"}:
        out.append(Achado("identico_en", "HIGH", "tradução idêntica ao inglês"))
    elif cat not in {"tecnico", "creditos"}:
        limpo = remover_nomes(vpt, ctx.nomes_mantidos)
        palavras = [p.lower() for p in PALAVRA_RE.findall(limpo)]
        ingles = sorted({p for p in palavras if p in PALAVRAS_EN and p not in FALSOS_EN})
        if ingles:
            out.append(Achado("palavra_en", "MEDIUM", f"palavras em inglês: {', '.join(ingles[:8])}"))
        pal_en = [p.lower() for p in PALAVRA_RE.findall(remover_nomes(ven, ctx.nomes_mantidos))]
        comum = _ngramas(pal_en, 4) & _ngramas(palavras, 4)
        if comum and pt != en:
            out.append(Achado("trecho_en", "HIGH", "sequência de 4+ palavras igual ao inglês: "
                              + " ".join(sorted(comum)[0])))

    # 2. português europeu e tratamento
    for padrao, msg in PT_EUROPEU:
        m = re.search(padrao, vpt, re.IGNORECASE)
        if m:
            out.append(Achado("pt_europeu", "MEDIUM", f"{msg}: '{m.group(0)}'"))
    if TU_RE.search(vpt) and cat != "creditos":
        if VOCE_RE.search(vpt):
            out.append(Achado("tratamento_misto", "MEDIUM", "mistura 'tu/teu' com 'você/seu' na mesma frase"))
        else:
            out.append(Achado("tratamento_tu", "LOW", f"usa '{TU_RE.search(vpt).group(0)}' (o projeto usa 'você')"))

    # 3. gramática frequente
    for padrao, msg, grav in GRAMATICA:
        m = re.search(padrao, vpt, re.IGNORECASE)
        if m:
            out.append(Achado("gramatica", grav, f"{msg}: '{m.group(0)}'"))
    for m in REPETIDA_RE.finditer(vpt):
        if m.group(1).lower() not in REPETIDA_OK and not REPETIDA_RE.search(ven):
            out.append(Achado("palavra_repetida", "MEDIUM", f"palavra repetida: '{m.group(0)}'"))
            break

    # 4. pontuação e espaçamento
    if ESPACO_ANTES_RE.search(vpt) and not ESPACO_ANTES_RE.search(ven):
        out.append(Achado("espaco_antes_pontuacao", "LOW", "espaço antes de pontuação"))
    m = SEM_ESPACO_DEPOIS_RE.search(vpt)
    if m and not SEM_ESPACO_DEPOIS_RE.search(ven):
        out.append(Achado("sem_espaco_depois", "LOW", f"falta espaço depois de '{m.group(0)[0]}'"))
    fe, fp = _final(en), _final(pt)
    if fe == "?" and fp not in {"?", ""} and "?" not in vpt:
        out.append(Achado("pergunta_virou_afirmacao", "MEDIUM", f"inglês termina em '?' e PT em '{fp}'"))
    elif fe in {".", "!", "?", "…"} and fp not in {".", "!", "?", "…"} and len(vpt) > 25:
        out.append(Achado("pontuacao_final", "LOW", f"inglês termina em '{fe}', PT sem pontuação final"))
    elif (fe not in {".", "!", "?", "…", ":"} and fp in {".", "!"} and cat in CATEGORIAS_UI and len(vpt) < 40
          and not re.search(r"(\b\w\.|transf\.|\.\.)$", vpt.rstrip())):
        out.append(Achado("pontuacao_final_ui", "LOW", f"rótulo ganhou '{fp}' no fim"))
    if vpt.count("(") != vpt.count(")"):
        out.append(Achado("parenteses", "MEDIUM", "parênteses desbalanceados"))
    aspas = vpt.count('"')
    if aspas % 2 and ven.count('"') % 2 == 0:
        out.append(Achado("aspas", "MEDIUM", "aspas retas desbalanceadas"))
    if vpt.count("“") != vpt.count("”"):
        out.append(Achado("aspas", "MEDIUM", "aspas curvas desbalanceadas"))

    # 5. maiúsculas
    ie, ip = _inicio_letra(en), _inicio_letra(pt)
    if ie.isalpha() and ie.isupper() and ip.isalpha() and ip.islower():
        out.append(Achado("minuscula_inicio", "LOW", "inglês começa com maiúscula e PT com minúscula"))
    for m in MAIUSCULA_APOS_PONTO_RE.finditer(vpt):
        anterior = (m.group(1) or "").lower()
        if anterior in ABREV_OK or (anterior and len(anterior) == 1):
            continue
        out.append(Achado("minuscula_apos_ponto", "LOW", f"minúscula depois de ponto: '…{m.group(0)[-6:]}'"))
        break

    # 6. números
    if _numeros(en) != _numeros(pt) and cat not in {"tecnico"}:
        faltam = sorted((_numeros(en) - _numeros(pt)).elements())
        sobram = sorted((_numeros(pt) - _numeros(en)).elements())
        if faltam or sobram:
            out.append(Achado("numeros", "MEDIUM", f"números diferentes do inglês: faltam {faltam} sobram {sobram}"))

    # 7. espaço em volta de ícones de botão
    ce, cp = _espacos_codigos(en), _espacos_codigos(pt)
    if len(ce) == len(cp):
        for (c1, a1, d1), (c2, a2, d2) in zip(sorted(ce), sorted(cp)):
            if c1 == c2 and ((a1 and not a2) or (d1 and not d2)):
                out.append(Achado("espaco_icone", "LOW", f"ícone {c2} grudado no texto"))
                break

    # 8. caracteres suspeitos
    if MOJIBAKE_RE.search(pt) and not MOJIBAKE_RE.search(en):
        out.append(Achado("caractere_suspeito", "HIGH", "sequência típica de codificação quebrada (mojibake)"))
    for seq, msg in SUSPEITOS.items():
        if seq in pt and seq not in en:
            out.append(Achado("caractere_suspeito", "HIGH", f"{msg} ({seq!r})"))
    if re.search(r"\{[^{}]*$|^[^{}]*\}|\[[A-Z]+(?!\])", pt) and not re.search(r"\{[^{}]*$|\[[A-Z]+(?!\])", en):
        out.append(Achado("codigo_quebrado", "CRITICAL", "chave ou colchete de código sem fechamento"))

    # 9. comprimento
    ref = max(len(ven), len(visivel(es or "")))
    if ref:
        razao = len(vpt) / ref
        if cat in CATEGORIAS_UI and len(vpt) > 12 and razao > 1.25:
            out.append(Achado("comprimento_ui", "MEDIUM", f"rótulo {round(100 * (razao - 1))}% maior que o original"))
        elif cat in {"dialogo", "desafio", "tutorial", "quiz", "info"} and len(ven) and len(vpt) / len(ven) > 1.45 and len(vpt) > 60:
            out.append(Achado("comprimento_fala", "LOW",
                              f"fala {round(100 * (len(vpt) / len(ven) - 1))}% maior que o inglês (tempo de leitura)"))
    return out


# --------------------------------------------------------------------------------------------
# Execução


def carregar_entradas() -> list[dict]:
    """Junta extração (inglês/espanhol) e catálogo (PT-BR) de todas as entradas."""
    out = []
    for nome in nomes_traducao():
        s = carregar_strings(nome)
        t = carregar_traducao(nome)
        por_id = {f["id"]: f for f in t["frases"]}
        for f in s["frases"]:
            en, es = f.get("texto_en"), f.get("texto_es")
            tr = por_id.get(f["id"], {})
            out.append({
                "arquivo": nome,
                "asset": s["asset"],
                "id": f["id"],
                "chave": f["chave"],
                "en": en,
                "es": es,
                "pt": tr.get("texto_ptbr", ""),
                "lote": tr.get("lote"),
                "hash_es": tr.get("hash_es"),
                "no_catalogo": f["id"] in por_id,
                "so_espanhol": en is None and bool(es),
            })
        ids_s = {f["id"] for f in s["frases"]}
        for fid, tr in por_id.items():
            if fid not in ids_s:
                out.append({"arquivo": nome, "asset": s["asset"], "id": fid, "chave": tr.get("chave"),
                            "en": None, "es": None, "pt": tr.get("texto_ptbr", ""), "lote": tr.get("lote"),
                            "hash_es": tr.get("hash_es"), "no_catalogo": True, "obsoleta": True})
    return out


def executar(entradas: list[dict] | None = None) -> dict:
    """Audita todas as entradas traduzíveis. Retorna o relatório (sem gravar nada)."""
    from .fonte import ConjuntoFonte

    ctx = Contexto()
    fonte = ConjuntoFonte.carregar()
    entradas = entradas if entradas is not None else carregar_entradas()
    integridade: list[dict] = []
    auditadas: list[dict] = []
    vistos: Counter = Counter()
    for e in entradas:
        vistos[(e["arquivo"], e["id"])] += 1
        if e.get("obsoleta"):
            integridade.append({"arquivo": e["arquivo"], "id": e["id"], "problema": "entrada do catálogo sem original"})
            continue
        if not e["no_catalogo"]:
            integridade.append({"arquivo": e["arquivo"], "id": e["id"], "problema": "original sem entrada no catálogo"})
        ref = e["en"] if e["en"] is not None else (e["es"] or "")
        if not ref:
            if e["pt"]:
                integridade.append({"arquivo": e["arquivo"], "id": e["id"], "problema": "tradução de original vazio"})
            continue
        if e["es"] is not None and e["hash_es"] and e["hash_es"] != hash_texto(e["es"]):
            integridade.append({"arquivo": e["arquivo"], "id": e["id"], "problema": "hash do espanhol mudou"})
        cat = categoria(e["asset"], e["chave"])
        achados = [Achado(regra, nivel if nivel != "ERRO" else "CRITICAL", msg)
                   for nivel, regra, msg in validar_frase(ref, e["pt"], fonte, ctx.glossario, 0.20, texto_es=e["es"])
                   if nivel in {"ERRO", "PENDENTE"} or regra in {"ordem_codigos", "espacos_pontas", "espaco_duplo",
                                                                   "pontuacao_es", "glossario", "nome_protegido_ausente",
                                                                   "fonte_precache"}]
        achados += auditar_frase(ref, e["es"], e["pt"], cat, ctx)
        auditadas.append({
            **{k: e[k] for k in ("arquivo", "asset", "id", "chave", "en", "es", "pt", "lote")},
            "so_espanhol": e.get("so_espanhol", False),
            "categoria": cat,
            "mundo": mundo(e["asset"]),
            "personagem_provavel": personagem_provavel(e["asset"]),
            "codigos": codigos.extrair(ref),
            "protegidos": [n for n in protegidos.ausentes(ref, "")],
            "achados": [a.como_dict() for a in achados],
        })
    for (arq, fid), n in vistos.items():
        if n > 1:
            integridade.append({"arquivo": arq, "id": fid, "problema": f"id repetido {n} vezes"})

    inconsistencias = inconsistencias_por_original(auditadas)
    return {
        "entradas": auditadas,
        "integridade": integridade,
        "inconsistencias": inconsistencias,
        "resumo": resumir(auditadas, integridade, inconsistencias),
    }


def _normal(texto: str) -> str:
    return re.sub(r"\s+", " ", visivel(texto)).strip().lower()


def inconsistencias_por_original(entradas: list[dict]) -> list[dict]:
    """Originais iguais (mesmo texto inglês) traduzidos de formas diferentes."""
    grupos: dict[str, list[dict]] = defaultdict(list)
    for e in entradas:
        if e["categoria"] == "tecnico":
            continue
        # sensível a maiúsculas: "BACK" e "Back" são rótulos de telas diferentes
        grupos[re.sub(r"\s+", " ", visivel(e["en"] or e["es"] or "")).strip()].append(e)
    out = []
    for original, itens in grupos.items():
        if not original or len(itens) < 2:
            continue
        variantes = Counter(visivel(e["pt"]).strip() for e in itens)
        if len(variantes) > 1:
            out.append({
                "original": original[:120],
                "ocorrencias": len(itens),
                "variantes": [{"pt": pt, "vezes": n,
                               "onde": [f"{e['arquivo']}[{e['id']}]" for e in itens if visivel(e["pt"]).strip() == pt][:12]}
                              for pt, n in variantes.most_common()],
            })
    return sorted(out, key=lambda g: -g["ocorrencias"])


def resumir(entradas: list[dict], integridade: list[dict], inconsistencias: list[dict]) -> dict:
    por_regra: Counter = Counter()
    por_grav: Counter = Counter()
    por_cat: Counter = Counter()
    com_achado = 0
    for e in entradas:
        por_cat[e["categoria"]] += 1
        if e["achados"]:
            com_achado += 1
        for a in e["achados"]:
            por_regra[a["regra"]] += 1
            por_grav[a["gravidade"]] += 1
    return {
        "entradas_auditadas": len(entradas),
        "traduzidas": sum(1 for e in entradas if e["pt"]),
        "so_espanhol": sum(1 for e in entradas if e["so_espanhol"]),
        "com_achado": com_achado,
        "por_categoria": dict(sorted(por_cat.items())),
        "por_regra": dict(por_regra.most_common()),
        "por_gravidade": dict(sorted(por_grav.items())),
        "problemas_integridade": len(integridade),
        "originais_com_traducoes_diferentes": len(inconsistencias),
    }


__all__ = ["Achado", "Contexto", "auditar_frase", "carregar_entradas", "categoria", "executar",
           "inconsistencias_por_original", "mundo", "personagem_provavel", "resumir"]


# --------------------------------------------------------------------------------------------
# Planilhas de revisão (uma por frente; saída em work/, fora do git)

GRUPOS = {
    "G1": ("Showdown Town, Spiral Mountain e história",
           lambda a: a.startswith(("showdowntown_", "spiralmountain_", "test_", "tempplaceholder"))
           or a in {"gameintro", "jinjos", "actor_hitdialogs", "challenge_wimpout", "ui_ingame_dialog_test"}),
    "G2": ("Nutty Acres e Banjoland", lambda a: a.startswith(("nuttyacres_", "banjoland_"))),
    "G3": ("LOGBOX 720, Jiggosseum e Terrarium of Terror",
           lambda a: a.startswith(("cpu_", "worldofsport_", "terrorium_"))),
    "G4": ("Menus, HUD, multijogador e créditos",
           lambda a: a.startswith(("ui_", "frontend", "error", "credits", "instructions_general",
                                   "instructions_challengestart")) and a != "ui_ingame_dialog_test"),
    "G5": ("Desafios, veículos, peças e garagem",
           lambda a: a in {"challenges", "livechallenges", "instructions_garage", "garagetutorial_default",
                           "vehicles", "blocks"}),
}


def grupo_do_asset(asset: str) -> str | None:
    a = asset_curto(asset)
    if a.startswith("tt_"):
        return None  # arquivos de tempo de prova: sem frases
    for g, (_, regra) in GRUPOS.items():
        if regra(a):
            return g
    return None


def planilha(entradas: list[dict], grupo: str) -> str:
    titulo = GRUPOS[grupo][0]
    linhas = [f"# Planilha de revisão {grupo} — {titulo}", "",
              "Cada entrada: [id] chave · categoria · achados automáticos (candidatos, não decisões).",
              "EN = original (fonte principal), ES = espanhol oficial (referência), PT = tradução atual.", ""]
    atual = None
    for e in entradas:
        if grupo_do_asset(e["asset"]) != grupo:
            continue
        if e["arquivo"] != atual:
            atual = e["arquivo"]
            m = e["mundo"] or "-"
            linhas += ["", f"## {e['arquivo']} {asset_curto(e['asset'])} (mundo: {m}; categoria: {e['categoria']})", ""]
        flags = "; ".join(f"{a['gravidade']} {a['regra']}: {a['mensagem']}" for a in e["achados"])
        so_es = " · só espanhol (créditos)" if e["so_espanhol"] else ""
        linhas.append(f"[{e['id']}] {e['chave']}{so_es}" + (f"  ⚑ {flags}" if flags else ""))
        if e["en"] is not None:
            linhas.append(f"EN: {e['en']}")
        if e["es"] is not None and e["es"] != e["en"]:
            linhas.append(f"ES: {e['es']}")
        linhas.append(f"PT: {e['pt']}")
        linhas.append("")
    return "\n".join(linhas) + "\n"
