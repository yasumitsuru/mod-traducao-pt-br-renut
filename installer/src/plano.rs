//! Instalacao transacional: prepara tudo numa area temporaria, confere e so entao publica.
//! Qualquer falha desfaz o que foi criado e restaura o que existia antes.

use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};

use serde_json::{Value, json};

use crate::atalho::{self, NOME_ATALHO};
use crate::detect::{Deteccao, PASTA_LAUNCHER};
use crate::manifesto::{self, ComponenteLauncher, ComponenteMod, Manifesto};
use crate::modpack::{self, SHA_ESPERADO};
use crate::patch;
use crate::sistema::formatar_bytes;
use crate::toml_min;

pub struct Opcoes {
    pub mod_jogo: bool,
    pub launcher: bool,
    pub atalho: bool,
}

pub struct Remocao {
    pub mod_jogo: bool,
    pub launcher: bool,
    pub atalho: bool,
}

#[derive(Clone, Default, Debug)]
pub struct Resultado {
    pub mod_ok: bool,
    pub launcher_ok: bool,
    pub atalho_ok: bool,
    pub mensagens: Vec<String>,
    pub mod_local: Option<String>,
    pub launcher_local: Option<String>,
    pub atalho_local: Option<String>,
}

#[derive(Debug)]
pub enum Evento {
    Etapa {
        numero: usize,
        total: usize,
        titulo: String,
    },
    Progresso {
        fracao: f32,
        texto: String,
    },
    Aviso(String),
}

const TOTAL_ETAPAS: usize = 9;

fn etapa<F: FnMut(Evento)>(emitir: &mut F, numero: usize, titulo: &str) {
    emitir(Evento::Etapa {
        numero,
        total: TOTAL_ETAPAS,
        titulo: titulo.to_string(),
    });
}

fn progresso<F: FnMut(Evento)>(emitir: &mut F, fracao: f32, texto: &str) {
    emitir(Evento::Progresso {
        fracao: fracao.clamp(0.0, 1.0),
        texto: texto.to_string(),
    });
}

fn pasta_temporaria(raiz: &Path) -> PathBuf {
    let n = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_nanos())
        .unwrap_or(0);
    let base = raiz.join(manifesto::PASTA_ESTADO);
    let _ = fs::create_dir_all(&base);
    base.join(format!("tmp-{}-{n}", std::process::id()))
}

struct Transacao {
    temp: PathBuf,
    backups: Vec<(PathBuf, PathBuf)>,
    criados: Vec<PathBuf>,
    mods_json_original: Option<(PathBuf, Vec<u8>)>,
    /// Arquivos de configuração reescritos nesta transação (conteúdo original para desfazer).
    arquivos_originais: Vec<(PathBuf, Vec<u8>)>,
    atalho_criado: Option<PathBuf>,
    publicado: bool,
}

impl Transacao {
    fn nova(temp: PathBuf) -> Self {
        Self {
            temp,
            backups: Vec::new(),
            criados: Vec::new(),
            mods_json_original: None,
            arquivos_originais: Vec::new(),
            atalho_criado: None,
            publicado: false,
        }
    }

    fn backup(&mut self, caminho: &Path) -> Result<(), String> {
        if !caminho.exists() {
            return Ok(());
        }
        let nome = caminho
            .file_name()
            .map(|n| n.to_string_lossy().to_string())
            .unwrap_or_else(|| "item".into());
        let destino = self
            .temp
            .join(format!("backup-{}-{nome}", self.backups.len()));
        if caminho.is_dir() {
            fs::rename(caminho, &destino)
                .map_err(|e| format!("Não consegui guardar {}: {e}", caminho.display()))?;
        } else {
            fs::rename(caminho, &destino)
                .map_err(|e| format!("Não consegui guardar {}: {e}", caminho.display()))?;
        }
        self.backups.push((caminho.to_path_buf(), destino));
        Ok(())
    }

    fn criar_pasta(&mut self, caminho: &Path) -> Result<(), String> {
        if !caminho.exists() {
            fs::create_dir_all(caminho)
                .map_err(|e| format!("Não criei {}: {e}", caminho.display()))?;
            self.criados.push(caminho.to_path_buf());
        }
        Ok(())
    }

    fn publicar(&mut self, de: &Path, para: &Path) -> Result<(), String> {
        if let Some(pai) = para.parent() {
            self.criar_pasta(pai)?;
        }
        if para.exists() {
            self.backup(para)?;
        }
        fs::rename(de, para)
            .map_err(|e| format!("Não movi {} para {}: {e}", de.display(), para.display()))?;
        self.criados.push(para.to_path_buf());
        Ok(())
    }

    fn desfazer(&mut self) {
        if self.publicado {
            return;
        }
        for p in self.criados.clone().iter().rev() {
            if p.is_dir() {
                let _ = fs::remove_dir_all(p);
            } else if p.is_file() {
                let _ = fs::remove_file(p);
            }
        }
        for (original, backup) in self.backups.clone().iter().rev() {
            if backup.exists() {
                let _ = fs::rename(backup, original);
            }
        }
        for (destino, original) in self.arquivos_originais.iter().rev() {
            let _ = fs::write(destino, original);
        }
        if let Some((destino, original)) = &self.mods_json_original {
            let _ = fs::write(destino, original);
        }
        if let Some(a) = &self.atalho_criado {
            let _ = atalho::remover(a);
        }
        let _ = fs::remove_dir_all(&self.temp);
        if let Some(base) = self.temp.parent() {
            let _ = fs::remove_dir(base);
        }
    }

    fn concluir(&mut self) {
        self.publicado = true;
        let _ = fs::remove_dir_all(&self.temp);
        if let Some(base) = self.temp.parent() {
            let _ = fs::remove_dir(base);
        }
    }
}

/// A pasta do mod foi criada por este instalador: o `.nbpatch` é o esperado agora, o que o
/// manifesto do instalador registrou na instalação anterior, ou o de uma versão conhecida (0.7.0),
/// que pode ser atualizada sem remoção manual.
fn mod_parece_nosso(dir: &Path, esperado: &str, registrado: Option<&str>) -> bool {
    let nb = dir.join(format!("{}.nbpatch", modpack::ID_MOD));
    nb.is_file()
        && patch::sha256_arquivo(&nb)
            .map(|s| s == esperado || Some(s.as_str()) == registrado || modpack::versao_do_sha(&s).is_some())
            .unwrap_or(false)
}

fn sha_registrado(det: &Deteccao) -> Option<&str> {
    det.manifesto
        .as_ref()
        .and_then(|m| m.mod_jogo.as_ref())
        .map(|m| m.nbpatch_sha256.as_str())
}

fn launcher_parece_nosso(dir: &Path) -> bool {
    let exe = dir.join(patch::NOME_EXE_TRADUZIDO);
    let Ok(m) = patch::manifesto() else {
        return false;
    };
    exe.is_file() && patch::sha256_arquivo(&exe).map(|s| s == m.output_sha256).unwrap_or(false)
}

/// Pastas que o próprio reNut cria ao rodar o launcher traduzido (perfil do guia com conquistas,
/// relatórios de falha, logs, saves relativos). Não são do instalador: nunca entram no manifesto,
/// sobrevivem à reinstalação e ficam na pasta depois da remoção.
const DADOS_DE_USO: [&str; 6] = ["guide", "crashdumps", "logs", "save", "user", "sentry"];
/// Configurações que o instalador grava na cópia e que o launcher pode reescrever.
const CONFIGS_LAUNCHER: [&str; 3] = ["renut.toml", "renut.cfg", "launcher.cfg"];

fn eh_dado_de_uso(rel: &str) -> bool {
    let primeiro = rel.split(['/', '\\']).next().unwrap_or("");
    DADOS_DE_USO.iter().any(|d| d.eq_ignore_ascii_case(primeiro))
}

/// Sobra de uma remoção anterior: sem o executável traduzido, só com dados de uso do launcher e
/// configurações. Pode ser reaproveitada pela reinstalação sem perder o perfil.
fn launcher_so_tem_dados_de_uso(dir: &Path) -> bool {
    if dir.join(patch::NOME_EXE_TRADUZIDO).exists() {
        return false;
    }
    let Ok(itens) = fs::read_dir(dir) else {
        return false;
    };
    for item in itens.flatten() {
        let nome = item.file_name().to_string_lossy().to_string();
        let aceito = if item.path().is_dir() {
            DADOS_DE_USO.iter().any(|d| d.eq_ignore_ascii_case(&nome))
        } else {
            CONFIGS_LAUNCHER.iter().any(|c| c.eq_ignore_ascii_case(&nome))
        };
        if !aceito {
            return false;
        }
    }
    true
}

fn copiar_arvore(de: &Path, para: &Path) -> Result<(), String> {
    fs::create_dir_all(para).map_err(|e| format!("Não criei {}: {e}", para.display()))?;
    let itens = fs::read_dir(de).map_err(|e| format!("Não li {}: {e}", de.display()))?;
    for item in itens.flatten() {
        let origem = item.path();
        let alvo = para.join(item.file_name());
        if origem.is_dir() {
            copiar_arvore(&origem, &alvo)?;
        } else if origem.is_file() {
            fs::copy(&origem, &alvo)
                .map_err(|e| format!("Não copiei {}: {e}", origem.display()))?;
        }
    }
    Ok(())
}

/// Leva os dados de uso da cópia anterior do launcher para a nova. Copia (não move): se a
/// instalação falhar, a cópia anterior volta inteira.
fn levar_dados_de_uso(anterior: &Path, nova: &Path) -> Result<Vec<String>, String> {
    let mut levados = Vec::new();
    for nome in DADOS_DE_USO {
        let de = anterior.join(nome);
        let para = nova.join(nome);
        if de.is_dir() && !para.exists() {
            copiar_arvore(&de, &para)?;
            levados.push(nome.to_string());
        }
    }
    Ok(levados)
}

/// Confere se a pasta pode ser apagada agora: no Windows, renomear uma pasta falha enquanto um
/// arquivo dela está aberto (o launcher traduzido rodando, por exemplo). Assim a remoção não
/// começa e para no meio, deixando o launcher incompleto.
fn pasta_livre(pasta: &Path) -> bool {
    let teste = pasta.with_file_name(format!(
        "{}.conferindo-{}",
        pasta.file_name().map(|n| n.to_string_lossy().to_string()).unwrap_or_default(),
        std::process::id()
    ));
    if fs::rename(pasta, &teste).is_err() {
        return false;
    }
    for _ in 0..20 {
        if fs::rename(&teste, pasta).is_ok() {
            return true;
        }
        std::thread::sleep(std::time::Duration::from_millis(100));
    }
    false
}

fn atualizar_mods_json(mods_json: &Path, ativar: bool) -> Result<(), String> {
    let original = if mods_json.is_file() {
        Some(fs::read(mods_json).map_err(|e| format!("Não li {}: {e}", mods_json.display()))?)
    } else {
        None
    };
    let mut valor: Value = match &original {
        Some(bytes) => serde_json::from_slice(bytes)
            .map_err(|e| format!("O arquivo mods.json do reNut está inválido: {e}"))?,
        None => json!({"disabled": [], "load_order": []}),
    };
    if !valor.is_object() {
        return Err("O arquivo mods.json do reNut não tem o formato esperado.".into());
    }
    if ativar {
        if !valor["load_order"].is_array() {
            valor["load_order"] = json!([]);
        }
        if !valor["disabled"].is_array() {
            valor["disabled"] = json!([]);
        }
        let lista = valor["load_order"].as_array_mut().unwrap();
        if !lista.iter().any(|x| x.as_str() == Some(modpack::ID_MOD)) {
            lista.push(json!(modpack::ID_MOD));
        }
        let desativados = valor["disabled"].as_array_mut().unwrap();
        desativados.retain(|x| x.as_str() != Some(modpack::ID_MOD));
    } else if let Some(lista) = valor["load_order"].as_array_mut() {
        lista.retain(|x| x.as_str() != Some(modpack::ID_MOD));
    }
    let texto = serde_json::to_string_pretty(&valor).map_err(|e| e.to_string())? + "\n";
    manifesto::gravar_texto(mods_json, &texto)?;
    if let Some(bytes) = original {
        let marcador = mods_json
            .parent()
            .unwrap_or(Path::new("."))
            .join(format!(".mods-json-original-{}", std::process::id()));
        let _ = fs::write(&marcador, bytes);
        let _ = fs::remove_file(marcador);
    }
    Ok(())
}

fn copiar_config_launcher(
    raiz: &Path,
    destino: &Path,
    mods: Option<&Path>,
    avisos: &mut Vec<String>,
) -> Result<bool, String> {
    let mut escreveu_toml = false;
    let toml_origem = raiz.join("renut.toml");
    if toml_origem.is_file() {
        let texto = fs::read_to_string(&toml_origem)
            .map_err(|e| format!("Não li {}: {e}", toml_origem.display()))?;
        let (novo, mudou) = toml_min::com_idioma_ingles(&texto);
        // O launcher traduzido roda de launcher-ptbr/: sem esta chave o reNut procuraria os mods em
        // launcher-ptbr/mods e a tradução do jogo não carregaria pelo atalho.
        let novo = match mods {
            Some(pasta) => toml_min::com_pasta_mods(&novo, pasta).0,
            None => novo,
        };
        if mudou {
            avisos.push(
                "No launcher traduzido, [kernel] user_language foi definido como 1 (English), \
                 que é o idioma usado pela tradução. As demais configurações foram preservadas."
                    .into(),
            );
        }
        manifesto::gravar_texto(&destino.join("renut.toml"), &novo)?;
        escreveu_toml = true;
    } else {
        avisos.push(
            "Não havia renut.toml na instalação; o launcher traduzido usará os padrões do reNut."
                .into(),
        );
    }
    let cfg = raiz.join("renut.cfg");
    if cfg.is_file() {
        let bytes = fs::read(&cfg).map_err(|e| format!("Não li {}: {e}", cfg.display()))?;
        manifesto::gravar_bytes_verificando(&destino.join("renut.cfg"), &bytes)?;
    }
    let launcher_cfg = raiz.join("launcher.cfg");
    if launcher_cfg.is_file() {
        let bytes =
            fs::read(&launcher_cfg).map_err(|e| format!("Não li {}: {e}", launcher_cfg.display()))?;
        manifesto::gravar_bytes_verificando(&destino.join("launcher.cfg"), &bytes)?;
    }
    Ok(escreveu_toml)
}

fn listar_arquivos(pasta: &Path) -> Vec<(String, String)> {
    let mut out = Vec::new();
    fn andar(base: &Path, atual: &Path, out: &mut Vec<(String, String)>) {
        let Ok(itens) = fs::read_dir(atual) else { return };
        for item in itens.flatten() {
            let p = item.path();
            if p.is_dir() {
                andar(base, &p, out);
            } else if p.is_file() {
                if let Ok(rel) = p.strip_prefix(base) {
                    let sha = patch::sha256_arquivo(&p).unwrap_or_default();
                    out.push((rel.to_string_lossy().replace('\\', "/"), sha));
                }
            }
        }
    }
    andar(pasta, pasta, &mut out);
    out.sort();
    out
}

/// Instala os componentes escolhidos. `emitir` recebe o progresso real de cada etapa.
pub fn instalar<F: FnMut(Evento)>(
    det: &Deteccao,
    opcoes: &Opcoes,
    cancelar: &AtomicBool,
    emitir: &mut F,
) -> Result<Resultado, String> {
    let catalogo = crate::traducao::carregar()?;
    instalar_com(det, opcoes, cancelar, emitir, &catalogo, SHA_ESPERADO)
}

/// Variante usada pelos testes com uma cópia sintetica do jogo (SHA é catalogo do teste).
pub fn instalar_com<F: FnMut(Evento)>(
    det: &Deteccao,
    opcoes: &Opcoes,
    cancelar: &AtomicBool,
    emitir: &mut F,
    catalogo: &[crate::traducao::ArquivoTrad],
    sha_esperado: &str,
) -> Result<Resultado, String> {
    let raiz = det.raiz.clone();
    let mut resultado = Resultado::default();
    if !det.raiz_valida || det.renut_exe.is_none() {
        return Err("Escolha uma pasta válida que contenha o renut.exe.".into());
    }
    if !opcoes.mod_jogo && !opcoes.launcher && !opcoes.atalho {
        return Err("Selecione pelo menos uma opção.".into());
    }
    if opcoes.atalho && !opcoes.mod_jogo && !opcoes.launcher && !det.mod_instalado && !det.launcher_instalado {
        return Err("Não há tradução instalada para apontar o atalho.".into());
    }

    etapa(emitir, 1, "Verificando instalação");
    progresso(emitir, 0.05, "Conferindo a pasta escolhida");
    if opcoes.mod_jogo && !det.pode_instalar_mod() {
        return Err(format!(
            "A tradução do jogo não pode ser instalada: {}",
            det.jogo_detalhe
        ));
    }
    if opcoes.launcher && !det.pode_instalar_launcher() {
        return Err(format!(
            "O launcher não pode ser traduzido: {}. {}",
            det.dlls_detalhe,
            det.problemas.first().cloned().unwrap_or_default()
        ));
    }

    etapa(emitir, 2, "Validando arquivos");
    let necessario = if opcoes.mod_jogo { 3 * 1024 * 1024 } else { 0 }
        + if opcoes.launcher { 130 * 1024 * 1024 } else { 0 };
    if let Some(livre) = det.espaco_livre {
        if livre < necessario + 32 * 1024 * 1024 {
            return Err(format!(
                "Espaço insuficiente no disco: livre {}, necessário cerca de {}.",
                formatar_bytes(livre),
                formatar_bytes(necessario)
            ));
        }
    }
    progresso(emitir, 0.15, "Arquivos de origem conferidos");

    let temp = pasta_temporaria(&raiz);
    let _ = fs::remove_dir_all(&temp);
    fs::create_dir_all(&temp).map_err(|e| format!("Não criei a área temporária: {e}"))?;
    let mut tx = Transacao::nova(temp.clone());
    let resultado_final = (|| -> Result<Resultado, String> {
        // ---------- Mod do jogo ----------
        let pasta_mod_nova = temp.join("mod");
        if opcoes.mod_jogo {
            etapa(emitir, 3, "Preparando tradução do jogo");
            progresso(emitir, 0.2, "Lendo os textos da sua cópia do jogo");
            let jogo = det
                .jogo
                .as_ref()
                .ok_or("A pasta do jogo não foi encontrada.")?;
            if cancelar.load(Ordering::Relaxed) {
                return Err("Instalação cancelada.".into());
            }
            etapa(emitir, 4, "Gerando arquivos PT-BR");
            let gerado = modpack::gerar(jogo, catalogo, |i, total| {
                progresso(
                    emitir,
                    0.2 + 0.2 * (i as f32 / total.max(1) as f32),
                    &format!("Aplicando a tradução: {i}/{total}"),
                );
            })?;
            if !gerado.sha_confere && gerado.sha256 != sha_esperado {
                return Err(format!(
                    "O pacote gerado não corresponde à versão {} conferida.\n\
                     Esperado: {sha_esperado}\nObtido:   {}\n\
                     Sua cópia do jogo provavelmente não é a versão suportada. Nada foi instalado.",
                    modpack::VERSAO,
                    gerado.sha256
                ));
            }
            fs::create_dir_all(&pasta_mod_nova).map_err(|e| e.to_string())?;
            fs::write(
                pasta_mod_nova.join(format!("{}.nbpatch", modpack::ID_MOD)),
                &gerado.nbpatch,
            )
            .map_err(|e| format!("Não gravei o pacote da tradução: {e}"))?;
            manifesto::gravar_texto(&pasta_mod_nova.join("mod.toml"), &gerado.mod_toml)?;
            let conferido = patch::sha256_arquivo(
                &pasta_mod_nova.join(format!("{}.nbpatch", modpack::ID_MOD)),
            )?;
            if conferido != sha_esperado {
                return Err("O pacote gravado não passou na verificação.".into());
            }
            resultado.mensagens.push(format!(
                "Tradução do jogo {}: {} arquivos, {} frases, SHA-256 {}.",
                modpack::VERSAO,
                gerado.arquivos,
                crate::sistema::milhar(gerado.frases),
                gerado.sha256
            ));
            if det.mod_desatualizado {
                resultado.mensagens.push(format!(
                    "Atualizada da versão {} para a {}; a pasta anterior foi substituída por inteiro.",
                    det.mod_versao.as_deref().unwrap_or("anterior"),
                    modpack::VERSAO
                ));
            }
        }

        // ---------- Launcher ----------
        let pasta_launcher_nova = temp.join("launcher");
        if opcoes.launcher {
            etapa(emitir, 5, "Preparando launcher");
            progresso(emitir, 0.45, "Copiando o runtime para uma pasta isolada");
            let origem = raiz.clone();
            let resumo = patch::preparar_runtime(&origem, &pasta_launcher_nova, cancelar, |i, total, texto| {
                progresso(
                    emitir,
                    0.45 + 0.3 * (i as f32 / total.max(1) as f32),
                    texto,
                );
            })?;
            etapa(emitir, 6, "Aplicando patches");
            let mut avisos_config = Vec::new();
            copiar_config_launcher(&raiz, &pasta_launcher_nova, det.mods_dir.as_deref(), &mut avisos_config)?;
            for a in avisos_config {
                emitir(Evento::Aviso(a));
            }
            etapa(emitir, 7, "Verificando integridade");
            let mut esperados: Vec<(String, String)> = Vec::new();
            esperados.push((patch::NOME_EXE_TRADUZIDO.to_string(), resumo.exe_sha.clone()));
            for (nome, sha) in &resumo.dlls {
                esperados.push((nome.clone(), sha.clone()));
            }
            if let Some(sha) = patch::sha256_arquivo(&pasta_launcher_nova.join(patch::NOME_EXE_TRADUZIDO)).ok() {
                let m = patch::manifesto()?;
                if sha != m.output_sha256 {
                    return Err("O executável traduzido não passou na verificação final.".into());
                }
            }
            for comp in patch::componentes()? {
                let sha = patch::sha256_arquivo(&pasta_launcher_nova.join(&comp.file))?;
                if sha != comp.output_sha256 {
                    return Err(format!(
                        "A DLL {} não passou na verificação final; a instalação foi cancelada.",
                        comp.file
                    ));
                }
            }
            resultado.mensagens.push(format!(
                "Launcher: executável + {} DLLs obrigatórias traduzidas e conferidas ({}).",
                resumo.dlls.len(),
                formatar_bytes(resumo.bytes)
            ));
        }

        // ---------- Publicacao ----------
        // Mod
        if opcoes.mod_jogo {
            let destino = det
                .mod_pasta
                .clone()
                .ok_or("A pasta de mods do reNut não foi determinada.")?;
            if destino.exists() && !mod_parece_nosso(&destino, sha_esperado, sha_registrado(det)) {
                return Err(format!(
                    "Já existe uma pasta {} que não foi criada por este instalador. \
                     Renomeie-a e tente de novo; nada foi alterado.",
                    destino.display()
                ));
            }
            if let Some(mods) = &det.mods_dir {
                tx.criar_pasta(mods)?;
            }
            tx.publicar(&pasta_mod_nova, &destino)?;
            let nb = destino.join(format!("{}.nbpatch", modpack::ID_MOD));
            if patch::sha256_arquivo(&nb)? != sha_esperado {
                return Err("O pacote publicado não passou na conferência.".into());
            }
            if let Some(mods) = &det.mods_dir {
                let mods_json = mods.join("mods.json");
                let anterior = if mods_json.is_file() {
                    Some(fs::read(&mods_json).map_err(|e| e.to_string())?)
                } else {
                    None
                };
                atualizar_mods_json(&mods_json, true)?;
                if let Some(bytes) = anterior {
                    tx.mods_json_original = Some((mods_json.clone(), bytes));
                }
            }
            resultado.mod_ok = true;
            resultado.mod_local = Some(destino.to_string_lossy().to_string());
        }

        // Launcher traduzido já instalado e não reinstalado agora: garante que ele carregue a
        // tradução da pasta de mods da instalação (instalações anteriores não tinham a chave).
        let mut toml_launcher_reparado: Option<String> = None;
        if opcoes.mod_jogo && !opcoes.launcher && det.launcher_instalado {
            if let (Some(mods), Some(pasta)) = (&det.mods_dir, &det.launcher_pasta) {
                let toml = pasta.join("renut.toml");
                if toml.is_file() {
                    let texto = fs::read_to_string(&toml)
                        .map_err(|e| format!("Não li {}: {e}", toml.display()))?;
                    let (novo, mudou) = toml_min::com_pasta_mods(&texto, mods);
                    if mudou {
                        tx.arquivos_originais.push((toml.clone(), texto.into_bytes()));
                        manifesto::gravar_texto(&toml, &novo)?;
                        toml_launcher_reparado = Some(patch::sha256_arquivo(&toml)?);
                        resultado.mensagens.push(
                            "Launcher traduzido ajustado para carregar os mods da pasta da instalação."
                                .into(),
                        );
                    }
                }
            }
        }

        // Launcher
        if opcoes.launcher {
            let destino = raiz.join(PASTA_LAUNCHER);
            let mut anterior = None;
            if destino.exists() {
                if !launcher_parece_nosso(&destino) && !launcher_so_tem_dados_de_uso(&destino) {
                    return Err(format!(
                        "Já existe a pasta {} com arquivos que não são deste instalador. \
                         Renomeie-a e tente de novo; nada foi alterado.",
                        destino.display()
                    ));
                }
                tx.backup(&destino).map_err(|e| {
                    format!("{e}. Feche o launcher traduzido e o jogo e tente de novo; nada foi alterado.")
                })?;
                anterior = tx.backups.last().map(|(_, b)| b.clone());
            }
            tx.publicar(&pasta_launcher_nova, &destino)?;
            if let Some(antiga) = &anterior {
                let levados = levar_dados_de_uso(antiga, &destino)?;
                if !levados.is_empty() {
                    resultado.mensagens.push(format!(
                        "Perfil e dados de uso do launcher traduzido preservados ({}).",
                        levados.join(", ")
                    ));
                }
            }
            let m = patch::manifesto()?;
            if patch::sha256_arquivo(&destino.join(patch::NOME_EXE_TRADUZIDO))? != m.output_sha256 {
                return Err("O launcher publicado não passou na conferência.".into());
            }
            for comp in patch::componentes()? {
                if patch::sha256_arquivo(&destino.join(&comp.file))? != comp.output_sha256 {
                    return Err(format!(
                        "O launcher publicado não tem {} traduzida; a instalação foi cancelada.",
                        comp.file
                    ));
                }
            }
            resultado.launcher_ok = true;
            resultado.launcher_local = Some(destino.to_string_lossy().to_string());
        }

        // ---------- Atalho ----------
        if opcoes.atalho {
            etapa(emitir, 8, "Criando atalho");
            let (alvo, trabalho, descricao) = if resultado.launcher_ok || det.launcher_instalado {
                let pasta = raiz.join(PASTA_LAUNCHER);
                (
                    pasta.join(patch::NOME_EXE_TRADUZIDO),
                    pasta,
                    "Banjo-Kazooie: Nuts & Bolts em português do Brasil (launcher reNut traduzido)",
                )
            } else {
                (
                    raiz.join("renut.exe"),
                    raiz.clone(),
                    "Banjo-Kazooie: Nuts & Bolts em português do Brasil (mod PT-BR)",
                )
            };
            if !alvo.is_file() {
                return Err(format!(
                    "O atalho apontaria para um executável que não existe: {}",
                    alvo.display()
                ));
            }
            let nome_lnk = atalho::area_de_trabalho()?.join(NOME_ATALHO);
            let anterior_era_nosso = det
                .manifesto
                .as_ref()
                .and_then(|m| m.atalho.clone())
                .map(|a| PathBuf::from(a) == nome_lnk)
                .unwrap_or(false);
            if nome_lnk.exists() && !anterior_era_nosso {
                return Err(format!(
                    "Já existe um atalho chamado \"{}\" na área de trabalho que não foi criado \
                     por este instalador. Nada foi alterado.",
                    NOME_ATALHO
                ));
            }
            let criado = atalho::criar(&alvo, &trabalho, descricao)?;
            tx.atalho_criado = Some(criado.clone());
            let lido = atalho::destino_do_atalho(&criado)?;
            if lido != alvo {
                return Err(format!(
                    "O atalho foi criado, mas aponta para {} em vez de {}.",
                    lido.display(),
                    alvo.display()
                ));
            }
            resultado.atalho_ok = true;
            resultado.atalho_local = Some(criado.to_string_lossy().to_string());
        }

        // ---------- Manifesto ----------
        etapa(emitir, 9, "Concluindo instalação");
        let mut manifesto = det.manifesto.clone().unwrap_or_default();
        manifesto.raiz = raiz.to_string_lossy().to_string();
        manifesto.instalado_em = manifesto::agora_utc();
        if resultado.mod_ok {
            let destino = det.mod_pasta.clone().unwrap();
            manifesto.mod_jogo = Some(ComponenteMod {
                pasta: destino.to_string_lossy().to_string(),
                nbpatch_sha256: patch::sha256_arquivo(&destino.join(format!(
                    "{}.nbpatch",
                    modpack::ID_MOD
                )))?,
                mod_toml_sha256: patch::sha256_arquivo(&destino.join("mod.toml"))?,
            });
        }
        if resultado.launcher_ok {
            let destino = raiz.join(PASTA_LAUNCHER);
            let m = patch::manifesto()?;
            // Os dados de uso (perfil do guia, logs...) não são do instalador: ficam fora do
            // manifesto para que a remoção nunca os apague.
            let arquivos: Vec<(String, String)> = listar_arquivos(&destino)
                .into_iter()
                .filter(|(rel, _)| !eh_dado_de_uso(rel))
                .collect();
            let dlls = patch::componentes()?
                .iter()
                .map(|c| (c.file.clone(), c.output_sha256.clone()))
                .collect();
            manifesto.launcher = Some(ComponenteLauncher {
                pasta: destino.to_string_lossy().to_string(),
                exe: patch::NOME_EXE_TRADUZIDO.to_string(),
                exe_sha256: m.output_sha256,
                dlls,
                arquivos,
            });
        }
        if let (Some(sha), Some(l)) = (&toml_launcher_reparado, manifesto.launcher.as_mut()) {
            for (nome, h) in l.arquivos.iter_mut() {
                if nome == "renut.toml" {
                    *h = sha.clone();
                }
            }
        }
        if resultado.atalho_ok {
            manifesto.atalho = resultado.atalho_local.clone();
        }
        manifesto.gravar(&raiz)?;

        progresso(emitir, 1.0, "Concluído");
        Ok(resultado)
    })();

    match resultado_final {
        Ok(r) => {
            tx.concluir();
            Ok(r)
        }
        Err(e) => {
            tx.desfazer();
            Err(e)
        }
    }
}

/// Remove componentes instalados, preservando tudo o que não pertence ao instalador.
pub fn remover<F: FnMut(Evento)>(
    det: &Deteccao,
    remocao: &Remocao,
    emitir: &mut F,
) -> Result<Vec<String>, String> {
    let raiz = det.raiz.clone();
    let mut mensagens = Vec::new();
    let mut manifesto = det.manifesto.clone().unwrap_or_default();
    manifesto.raiz = raiz.to_string_lossy().to_string();

    // Antes de mudar qualquer coisa: nada do que vai sair pode estar aberto (jogo ou launcher
    // rodando). Sem isso a remoção pararia no meio e deixaria o launcher incompleto.
    let mut ocupadas = Vec::new();
    for (pedido, pasta) in [
        (remocao.mod_jogo, &det.mod_pasta),
        (remocao.launcher, &det.launcher_pasta),
    ] {
        if let (true, Some(p)) = (pedido, pasta) {
            if p.exists() && !pasta_livre(p) {
                ocupadas.push(p.display().to_string());
            }
        }
    }
    if !ocupadas.is_empty() {
        return Err(format!(
            "Feche o jogo e o launcher traduzido e tente de novo: {} está em uso. Nada foi removido.",
            ocupadas.join(" e ")
        ));
    }

    if remocao.mod_jogo {
        etapa(emitir, 1, "Removendo tradução do jogo");
        if let Some(pasta) = &det.mod_pasta {
            if pasta.exists() {
                let esperado = det
                    .manifesto
                    .as_ref()
                    .and_then(|m| m.mod_jogo.as_ref())
                    .map(|m| m.nbpatch_sha256.clone())
                    .unwrap_or_else(|| SHA_ESPERADO.to_string());
                if !mod_parece_nosso(pasta, &esperado, sha_registrado(det)) {
                    return Err(format!(
                        "A pasta {} não é a tradução criada por este instalador; nada foi removido.",
                        pasta.display()
                    ));
                }
                for nome in [
                    format!("{}.nbpatch", modpack::ID_MOD),
                    "mod.toml".to_string(),
                ] {
                    let p = pasta.join(&nome);
                    if p.is_file() {
                        fs::remove_file(&p)
                            .map_err(|e| format!("Não removi {}: {e}", p.display()))?;
                    }
                }
                let restantes: Vec<String> = fs::read_dir(pasta)
                    .map(|i| {
                        i.flatten()
                            .map(|x| x.file_name().to_string_lossy().to_string())
                            .collect()
                    })
                    .unwrap_or_default();
                if restantes.is_empty() {
                    let _ = fs::remove_dir(pasta);
                    mensagens.push("Tradução do jogo removida.".into());
                } else {
                    mensagens.push(format!(
                        "Tradução do jogo removida; a pasta ficou com arquivos que não são nossos: {}.",
                        restantes.join(", ")
                    ));
                }
            }
            if let Some(mods) = &det.mods_dir {
                let mods_json = mods.join("mods.json");
                if mods_json.is_file() {
                    atualizar_mods_json(&mods_json, false)?;
                }
            }
            manifesto.mod_jogo = None;
        }
    }

    if remocao.launcher {
        etapa(emitir, 2, "Removendo launcher traduzido");
        if let Some(pasta) = &det.launcher_pasta {
            if pasta.exists() {
                if !launcher_parece_nosso(pasta) && !launcher_so_tem_dados_de_uso(pasta) {
                    return Err(format!(
                        "A pasta {} não é o launcher criado por este instalador; nada foi removido.",
                        pasta.display()
                    ));
                }
                let esperados = manifesto
                    .launcher
                    .as_ref()
                    .map(|l| l.arquivos.clone())
                    .unwrap_or_else(|| {
                        let mut v = vec![(
                            patch::NOME_EXE_TRADUZIDO.to_string(),
                            patch::manifesto().map(|m| m.output_sha256).unwrap_or_default(),
                        )];
                        for c in patch::componentes().unwrap_or_default() {
                            v.push((c.file, c.output_sha256));
                        }
                        v
                    });
                match patch::remover_runtime(pasta, &esperados) {
                    Ok(_) => mensagens.push("Launcher traduzido removido; originais intactos.".into()),
                    Err(e) => mensagens.push(e),
                }
                if !pasta.join(patch::NOME_EXE_TRADUZIDO).exists() {
                    manifesto.launcher = None;
                }
                if pasta.exists() && launcher_so_tem_dados_de_uso(pasta) {
                    mensagens.push(format!(
                        "A pasta {} ficou só com o perfil e os dados de uso do launcher traduzido; \
                         eles voltam a ser usados se você reinstalar o launcher.",
                        pasta.display()
                    ));
                }
            } else {
                manifesto.launcher = None;
            }
        }
    }

    // Se o launcher saiu e o atalho era nosso, ele não pode continuar apontando para um
    // executável que não existe: volta para o reNut original (mod continua) ou é removido.
    if remocao.launcher && !remocao.atalho {
        if let Some(a) = det.manifesto.as_ref().and_then(|m| m.atalho.clone()) {
            let lnk = PathBuf::from(&a);
            if lnk.exists() {
                if manifesto.mod_jogo.is_some() {
                    let alvo = raiz.join("renut.exe");
                    if alvo.is_file() {
                        atalho::criar(&alvo, &raiz, "Banjo-Kazooie: Nuts & Bolts em português do Brasil (mod PT-BR)")?;
                        manifesto.atalho = Some(a);
                        mensagens.push(
                            "O atalho agora aponta para o reNut original, porque o launcher traduzido foi removido."
                                .into(),
                        );
                    }
                } else {
                    atalho::remover(&lnk)?;
                    manifesto.atalho = None;
                    mensagens.push("Atalho removido junto com o launcher traduzido.".into());
                }
            }
        }
    }

    if remocao.atalho {
        etapa(emitir, 3, "Removendo atalho");
        if let Some(a) = det
            .manifesto
            .as_ref()
            .and_then(|m| m.atalho.clone())
            .map(PathBuf::from)
        {
            if a.exists() {
                atalho::remover(&a)?;
                mensagens.push(format!("Atalho removido: {}", a.display()));
            }
            manifesto.atalho = None;
        } else if let Some(a) = &det.atalho {
            return Err(format!(
                "O atalho {} não foi criado por este instalador; ele não será apagado.",
                a.display()
            ));
        }
    }

    if manifesto.mod_jogo.is_none() && manifesto.launcher.is_none() && manifesto.atalho.is_none() {
        Manifesto::remover_estado(&raiz)?;
    } else {
        manifesto.gravar(&raiz)?;
    }
    Ok(mensagens)
}

/// Le o `mods.json` é diz se o mod está habilitado (usado pelo verificador é pelos testes).
pub fn mod_habilitado(mods_json: &Path) -> bool {
    let Ok(bytes) = fs::read(mods_json) else {
        return false;
    };
    let Ok(v) = serde_json::from_slice::<Value>(&bytes) else {
        return false;
    };
    let ativo = v["load_order"]
        .as_array()
        .map(|l| l.iter().any(|x| x.as_str() == Some(modpack::ID_MOD)))
        .unwrap_or(false);
    let desativado = v["disabled"]
        .as_array()
        .map(|l| l.iter().any(|x| x.as_str() == Some(modpack::ID_MOD)))
        .unwrap_or(false);
    ativo && !desativado
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn json_do_mods_preserva_outros_mods() {
        let dir = std::env::temp_dir().join(format!("mods-json-teste-{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        let p = dir.join("mods.json");
        fs::write(&p, r#"{"disabled":["outro"],"load_order":["outro"]}"#).unwrap();
        atualizar_mods_json(&p, true).unwrap();
        assert!(mod_habilitado(&p));
        let v: Value = serde_json::from_slice(&fs::read(&p).unwrap()).unwrap();
        assert_eq!(v["load_order"].as_array().unwrap().len(), 2);
        assert_eq!(v["disabled"].as_array().unwrap()[0], "outro");
        atualizar_mods_json(&p, false).unwrap();
        assert!(!mod_habilitado(&p));
        let v: Value = serde_json::from_slice(&fs::read(&p).unwrap()).unwrap();
        assert_eq!(v["load_order"].as_array().unwrap().len(), 1);
        let _ = fs::remove_dir_all(&dir);
    }

    fn pasta_de_teste(nome: &str) -> PathBuf {
        let dir = std::env::temp_dir().join(format!("{nome}-{}", std::process::id()));
        let _ = fs::remove_dir_all(&dir);
        fs::create_dir_all(&dir).unwrap();
        dir
    }

    #[test]
    fn sobra_com_perfil_do_launcher_pode_ser_reaproveitada() {
        let dir = pasta_de_teste("launcher-sobra");
        fs::create_dir_all(dir.join("guide").join("gamerpics")).unwrap();
        fs::write(dir.join("guide").join("achievements.json"), b"{}").unwrap();
        fs::write(dir.join("guide").join("gamerpics").join("1.png"), b"png").unwrap();
        fs::write(dir.join("renut.cfg"), b"# alterado pelo reNut").unwrap();
        assert!(launcher_so_tem_dados_de_uso(&dir));
        assert!(eh_dado_de_uso("guide/achievements.json"));
        assert!(!eh_dado_de_uso("rexui.dll"));

        // Qualquer arquivo desconhecido (uma DLL, outro executável) mantém a recusa.
        fs::write(dir.join("outra.dll"), b"x").unwrap();
        assert!(!launcher_so_tem_dados_de_uso(&dir));
        fs::remove_file(dir.join("outra.dll")).unwrap();
        // Com o executável traduzido presente, a pasta é um launcher, não uma sobra.
        fs::write(dir.join(patch::NOME_EXE_TRADUZIDO), b"x").unwrap();
        assert!(!launcher_so_tem_dados_de_uso(&dir));
        let _ = fs::remove_dir_all(&dir);
    }

    #[test]
    fn dados_de_uso_vao_para_a_copia_nova_sem_sair_da_antiga() {
        let antiga = pasta_de_teste("launcher-antiga");
        let nova = pasta_de_teste("launcher-nova");
        fs::create_dir_all(antiga.join("guide").join("titles")).unwrap();
        fs::write(antiga.join("guide").join("titles").join("t.json"), b"conquistas").unwrap();
        fs::create_dir_all(antiga.join("crashdumps")).unwrap();
        fs::write(antiga.join("renut.toml"), b"antigo").unwrap();
        let levados = levar_dados_de_uso(&antiga, &nova).unwrap();
        assert_eq!(levados, vec!["guide".to_string(), "crashdumps".to_string()]);
        assert_eq!(fs::read(nova.join("guide").join("titles").join("t.json")).unwrap(), b"conquistas");
        assert!(antiga.join("guide").join("titles").join("t.json").is_file(), "copia, não move");
        assert!(!nova.join("renut.toml").exists(), "configurações vêm da instalação, não da sobra");
        let _ = fs::remove_dir_all(&antiga);
        let _ = fs::remove_dir_all(&nova);
    }

    #[test]
    fn pasta_com_arquivo_aberto_nao_esta_livre() {
        let dir = pasta_de_teste("launcher-aberto");
        let arq = dir.join("renut.ptbr.exe");
        fs::write(&arq, b"x").unwrap();
        assert!(pasta_livre(&dir));
        assert!(arq.is_file(), "a conferência devolve a pasta ao nome original");
        #[cfg(windows)]
        {
            use std::os::windows::fs::OpenOptionsExt;
            let aberto = fs::OpenOptions::new().read(true).share_mode(0).open(&arq).unwrap();
            assert!(!pasta_livre(&dir));
            drop(aberto);
            assert!(pasta_livre(&dir));
        }
        assert!(dir.is_dir());
        let _ = fs::remove_dir_all(&dir);
    }
}