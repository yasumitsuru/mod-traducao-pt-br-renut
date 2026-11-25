//! Deteccao da instalacao do reNut a partir da pasta escolhida pelo usuario.

use std::fs;
use std::path::{Path, PathBuf};

use crate::manifesto::Manifesto;
use crate::modpack::{self, ID_MOD, SHA_ESPERADO};
use crate::patch;
use crate::sistema::espaco_livre;
use crate::toml_min::{self, ConfigRenut};
use crate::traducao::ArquivoTrad;

pub const PASTA_LAUNCHER: &str = "launcher-ptbr";

#[derive(Clone, Default)]
pub struct Deteccao {
    pub raiz: PathBuf,
    pub raiz_valida: bool,
    pub problemas: Vec<String>,
    pub avisos: Vec<String>,

    pub renut_exe: Option<PathBuf>,
    pub exe_sha: String,
    pub exe_tamanho: u64,
    pub release: String,
    pub exe_compativel: bool,

    pub config: Option<ConfigRenut>,
    pub jogo: Option<PathBuf>,
    pub jogo_ok: bool,
    pub jogo_detalhe: String,
    pub jogos_faltando: usize,

    pub mods_dir: Option<PathBuf>,
    pub mod_pasta: Option<PathBuf>,
    pub mod_instalado: bool,
    pub mod_sha: String,
    /// Versao conhecida encontrada em mods/ptbr_traducao ("0.8.0", "0.7.0"), se houver.
    pub mod_versao: Option<String>,
    /// Uma versao anterior conhecida (0.7.0) esta instalada e pode ser atualizada.
    pub mod_desatualizado: bool,
    pub mod_detalhe: String,

    pub dlls_ok: bool,
    pub dlls_detalhe: String,

    pub launcher_pasta: Option<PathBuf>,
    pub launcher_instalado: bool,
    pub launcher_sha: String,
    pub launcher_detalhe: String,

    pub atalho: Option<PathBuf>,
    pub atalho_existe: bool,

    pub espaco_livre: Option<u64>,
    pub idioma: Option<u32>,
    pub manifesto: Option<Manifesto>,
}

impl Deteccao {
    pub fn pode_instalar_mod(&self) -> bool {
        self.jogo_ok
    }

    pub fn erro_de_pasta(&self) -> bool {
        !self.raiz_valida || self.renut_exe.is_none()
    }

    pub fn pode_instalar_launcher(&self) -> bool {
        self.exe_compativel && self.dlls_ok
    }

    pub fn status_geral(&self) -> String {
        if !self.raiz_valida {
            return "Escolha a pasta onde o reNut está instalado.".into();
        }
        if self.renut_exe.is_none() {
            return "O renut.exe não foi encontrado nesta pasta.".into();
        }
        if !self.exe_compativel {
            return "ReNut encontrado, mas a versão não é a suportada.".into();
        }
        if self.mod_instalado || self.launcher_instalado {
            return "Tradução já instalada; você pode reparar, reinstalar ou remover.".into();
        }
        if self.pode_instalar_mod() && self.pode_instalar_launcher() {
            "Tudo pronto para instalar.".into()
        } else if self.pode_instalar_mod() {
            "A tradução do jogo pode ser instalada; o launcher não é compatível.".into()
        } else {
            "A pasta do jogo não foi encontrada ou está incompleta.".into()
        }
    }
}

pub fn caminho_ingles(extraido: &Path, nome: &str) -> PathBuf {
    extraido
        .join("Debug")
        .join(&nome[0..2])
        .join(&nome[2..4])
        .join(&nome[4..6])
        .join(&nome[6..8])
}

pub fn parece_extraido(p: &Path) -> bool {
    p.join("Debug").is_dir() && p.join("loctext").join("spanish").is_dir()
}

fn resolver_jogo(raiz: &Path, cfg: &Option<ConfigRenut>) -> Option<PathBuf> {
    let mut tentativas: Vec<PathBuf> = Vec::new();
    if let Some(c) = cfg {
        if let Some(g) = &c.game_root {
            tentativas.push(g.clone());
        }
    }
    tentativas.push(raiz.join("game").join("extraido"));
    tentativas.push(raiz.join("extraido"));
    tentativas.push(raiz.to_path_buf());
    if let Some(pai) = raiz.parent() {
        tentativas.push(pai.join("game").join("extraido"));
        tentativas.push(pai.to_path_buf());
    }
    for t in &tentativas {
        if parece_extraido(t) {
            return Some(t.clone());
        }
    }
    // Procura ate dois niveis abaixo, sem seguir links.
    if let Ok(itens) = fs::read_dir(raiz) {
        for item in itens.flatten() {
            let p = item.path();
            if p.is_dir() && parece_extraido(&p) {
                return Some(p);
            }
            if p.is_dir() {
                if let Ok(sub) = fs::read_dir(&p) {
                    for s in sub.flatten() {
                        if s.path().is_dir() && parece_extraido(&s.path()) {
                            return Some(s.path());
                        }
                    }
                }
            }
        }
    }
    None
}

fn pasta_mods(raiz: &Path, cfg: &Option<ConfigRenut>) -> PathBuf {
    let base = cfg
        .as_ref()
        .and_then(|c| c.app_root.clone())
        .unwrap_or_else(|| raiz.to_path_buf());
    base.join("mods")
}

pub fn analisar(raiz: &Path, catalogo: &[ArquivoTrad]) -> Deteccao {
    let mut d = Deteccao {
        raiz: raiz.to_path_buf(),
        ..Default::default()
    };
    let raiz = match fs::canonicalize(raiz) {
        Ok(r) if r.is_dir() => crate::sistema::limpar_prefixo(&r),
        _ => {
            d.problemas
                .push("A pasta escolhida não existe ou não pode ser aberta.".into());
            return d;
        }
    };
    d.raiz = raiz.clone();
    d.raiz_valida = true;

        let exe = raiz.join("renut.exe");
    if exe.is_file() {
        d.renut_exe = Some(exe.clone());
        if let Ok(meta) = fs::metadata(&exe) {
            d.exe_tamanho = meta.len();
        }
        d.exe_sha = patch::sha256_arquivo(&exe).unwrap_or_default();
        if let Ok(m) = patch::manifesto() {
            d.exe_compativel = d.exe_sha == m.input_sha256 && d.exe_tamanho == m.input_size;
            if !d.exe_compativel {
                d.problemas.push(format!(
                    "O renut.exe não é a versão suportada ({} {}).\nEsperado: {}\nEncontrado: {}",
                    m.release, m.version, m.input_sha256, d.exe_sha
                ));
            }
        }
        d.release = fs::read_to_string(raiz.join("version.txt"))
            .map(|s| s.trim().to_string())
            .unwrap_or_default();
    } else {
        d.problemas
            .push("Não encontrei o renut.exe nesta pasta. Escolha a pasta que contém o renut.exe.".into());
    }
    if let Ok(texto) = fs::read_to_string(raiz.join("renut.toml")) {
        let cfg = toml_min::ler(&texto);
        d.idioma = cfg.user_language;
        d.config = Some(cfg.clone());
        if let Some(idioma) = cfg.user_language {
            if idioma != 1 {
                d.avisos.push(format!(
                    "O renut.toml está no idioma {idioma}; a tradução do jogo foi feita para English (1). \
                     No launcher traduzido o idioma será ajustado para 1; no launcher original, ajuste no menu."
                ));
            }
        }
    } else {
        d.avisos.push(
            "Não encontrei o renut.toml; a detecção usará os caminhos padrão da pasta.".into(),
        );
    }
    d.jogo = resolver_jogo(&raiz, &d.config);
    if let Some(jogo) = &d.jogo {
        let faltando_en = catalogo
            .iter()
            .filter(|a| !caminho_ingles(jogo, &a.arquivo).is_file())
            .count();
        let faltando_es = catalogo
            .iter()
            .filter(|a| !jogo.join("loctext").join("spanish").join(&a.arquivo).is_file())
            .count();
        d.jogos_faltando = faltando_en + faltando_es;
        if faltando_en == 0 && faltando_es == 0 {
            d.jogo_ok = true;
            d.jogo_detalhe = "Extração completa (107 textos em inglês e espanhol).".into();
        } else {
            d.jogo_detalhe = format!(
                "Faltam {faltando_en} texto(s) em inglês e {faltando_es} em espanhol. \
                 Termine a extração do jogo no reNut."
            );
        }
    } else {
        d.jogo_detalhe =
            "Não encontrei a pasta do jogo (game/extraido com Debug e loctext).".into();
    }

    d.mods_dir = Some(pasta_mods(&raiz, &d.config));
    let pasta_mod = d
        .mods_dir
        .as_ref()
        .map(|m| m.join(ID_MOD))
        .unwrap_or_else(|| raiz.join("mods").join(ID_MOD));
    if pasta_mod.is_dir() {
        let nb = pasta_mod.join(format!("{ID_MOD}.nbpatch"));
        d.mod_sha = patch::sha256_arquivo(&nb).unwrap_or_default();
        let tem_toml = pasta_mod.join("mod.toml").is_file();
        d.mod_instalado = d.mod_sha == SHA_ESPERADO && tem_toml;
        d.mod_versao = modpack::versao_do_sha(&d.mod_sha).map(str::to_string);
        d.mod_desatualizado = !d.mod_instalado && d.mod_versao.is_some() && tem_toml;
        d.mod_detalhe = if d.mod_instalado {
            format!("Tradução {} instalada e conferida.", modpack::VERSAO)
        } else if d.mod_desatualizado {
            format!(
                "Tradução {} instalada. Marque a tradução do jogo para atualizar para a {} \
                 (a versão anterior é substituída sem remoção manual).",
                d.mod_versao.as_deref().unwrap_or("anterior"),
                modpack::VERSAO
            )
        } else if nb.is_file() {
            format!(
                "Existe uma pasta da tradução, mas o pacote não é uma versão conhecida (esperada {}).",
                modpack::VERSAO
            )
        } else {
            "Existe uma pasta da tradução sem o pacote .nbpatch.".into()
        };
    } else {
        d.mod_detalhe = "Ainda não instalada.".into();
    }
    d.mod_pasta = Some(pasta_mod);
    let componentes = patch::componentes().unwrap_or_default();
    let mut detalhes_dll = Vec::new();
    let mut dlls_ok = true;
    for comp in &componentes {
        let p = raiz.join(&comp.file);
        let sha = patch::sha256_arquivo(&p).unwrap_or_default();
        if sha != comp.input_sha256 {
            dlls_ok = false;
            if p.is_file() {
                detalhes_dll.push(format!("{} com versão diferente", comp.file));
            } else {
                detalhes_dll.push(format!("{} não encontrada", comp.file));
            }
        }
    }
    d.dlls_ok = dlls_ok && !componentes.is_empty();
    d.dlls_detalhe = if d.dlls_ok {
        format!("{} DLLs obrigatórias conferidas.", componentes.len())
    } else if detalhes_dll.is_empty() {
        "As DLLs obrigatórias não foram encontradas.".into()
    } else {
        detalhes_dll.join("; ")
    };

    let pasta_launcher = raiz.join(PASTA_LAUNCHER);
    let exe_tra = pasta_launcher.join(patch::NOME_EXE_TRADUZIDO);
    if exe_tra.is_file() {
        d.launcher_sha = patch::sha256_arquivo(&exe_tra).unwrap_or_default();
        let m = patch::manifesto().ok();
        let exe_ok = m
            .as_ref()
            .is_some_and(|m| d.launcher_sha == m.output_sha256);
        let dlls_ok = componentes.iter().all(|c| {
            patch::sha256_arquivo(&pasta_launcher.join(&c.file))
                .map(|s| s == c.output_sha256)
                .unwrap_or(false)
        });
        d.launcher_instalado = exe_ok && dlls_ok;
        if d.launcher_instalado {
            let esperado = d.mods_dir.as_ref().map(|m| m.to_string_lossy().replace('\\', "/"));
            let configurado = fs::read_to_string(pasta_launcher.join("renut.toml"))
                .ok()
                .and_then(|t| toml_min::pasta_mods_configurada(&t));
            if esperado.is_some() && configurado != esperado {
                d.avisos.push(
                    "O launcher traduzido ainda não aponta para a pasta de mods da instalação; ao instalar a tradução do jogo, o instalador corrige isso."
                        .into(),
                );
            }
        }
        d.launcher_detalhe = if d.launcher_instalado {
            "Launcher traduzido instalado; executável e DLLs conferidos.".into()
        } else {
            "Existe uma cópia do launcher, mas ela não está completa.".into()
        };
    } else {
        d.launcher_detalhe = "Ainda não instalado.".into();
    }
    d.launcher_pasta = Some(pasta_launcher);
    d.manifesto = Manifesto::carregar(&raiz);
    d.espaco_livre = espaco_livre(&raiz);

    // Atalho: o manifesto diz qual foi criado por nos; o nome padrao pode existir sem ser nosso.
    if let Some(m) = &d.manifesto {
        if let Some(a) = &m.atalho {
            let p = PathBuf::from(a);
            d.atalho_existe = p.is_file();
            d.atalho = Some(p);
        }
    }
    if d.atalho.is_none() {
        if d.atalho.is_none() {
            if let Ok(p) = crate::atalho::caminho_padrao() {
                if p.is_file() {
                    d.atalho = Some(p);
                }
            }
        }
    }
    if !d.exe_compativel {
        d.avisos.push(
            "O patch do launcher só aceita a versão big-lua-energy (0.11.21) com o SHA-256 \
             documentado. Nenhum patch será aplicado a força."
                .into(),
        );
    }
    d
}