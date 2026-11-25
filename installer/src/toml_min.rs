//! Leitura e edicao pontual do `renut.toml`, sem dependencia de parser TOML.
//!
//! So interessam as chaves de caminho e o idioma. O arquivo original nunca e reescrito: a
//! edicao acontece numa copia dentro do runtime traduzido.

use std::path::PathBuf;

#[derive(Clone, Default)]
pub struct ConfigRenut {
    pub texto: String,
    pub app_root: Option<PathBuf>,
    pub user_root: Option<PathBuf>,
    pub game_root: Option<PathBuf>,
    pub update_root: Option<PathBuf>,
    pub user_language: Option<u32>,
}

fn limpar_valor(v: &str) -> String {
    let v = v.trim();
    let v = v.split(" #").next().unwrap_or(v).trim();
    if (v.starts_with('\'') && v.ends_with('\'') && v.len() >= 2)
        || (v.starts_with('"') && v.ends_with('"') && v.len() >= 2)
    {
        v[1..v.len() - 1].to_string()
    } else {
        v.to_string()
    }
}

pub fn ler(texto: &str) -> ConfigRenut {
    let mut cfg = ConfigRenut {
        texto: texto.to_string(),
        ..Default::default()
    };
    let mut secao = String::new();
    for linha in texto.lines() {
        let l = linha.trim();
        if l.starts_with('[') && l.ends_with(']') {
            secao = l.trim_matches(['[', ']']).trim().to_lowercase();
            continue;
        }
        let Some((chave, valor)) = l.split_once('=') else {
            continue;
        };
        let chave = chave.trim().to_lowercase();
        let valor = limpar_valor(valor);
        match (secao.as_str(), chave.as_str()) {
            ("app", "root") => cfg.app_root = Some(PathBuf::from(valor)),
            ("app", "user_root") => cfg.user_root = Some(PathBuf::from(valor)),
            ("title", "game_root") => cfg.game_root = Some(PathBuf::from(valor)),
            ("title", "update_root") => cfg.update_root = Some(PathBuf::from(valor)),
            ("kernel", "user_language") => cfg.user_language = valor.parse().ok(),
            _ => {}
        }
    }
    cfg
}

/// Devolve o texto com `[kernel] user_language = 1`, preservando todas as outras linhas.
/// Retorna tambem se houve mudanca.
pub fn com_idioma_ingles(texto: &str) -> (String, bool) {
    let mut linhas: Vec<String> = texto.lines().map(str::to_string).collect();
    let mut secao = String::new();
    let mut indice_kernel: Option<usize> = None;
    let mut indice_chave: Option<usize> = None;

    for (i, linha) in linhas.iter().enumerate() {
        let l = linha.trim();
        if l.starts_with('[') && l.ends_with(']') {
            secao = l.trim_matches(['[', ']']).trim().to_lowercase();
            if secao == "kernel" {
                indice_kernel = Some(i);
            }
            continue;
        }
        if secao == "kernel" {
            if let Some((c, _)) = l.split_once('=') {
                if c.trim().eq_ignore_ascii_case("user_language") {
                    indice_chave = Some(i);
                }
            }
        }
    }

    if let Some(i) = indice_chave {
        let atual = linhas[i].trim().to_string();
        if atual == "user_language = 1" {
            return (texto.to_string(), false);
        }
        let recuo: String = linhas[i]
            .chars()
            .take_while(|c| c.is_whitespace())
            .collect();
        linhas[i] = format!("{recuo}user_language = 1");
    } else if let Some(i) = indice_kernel {
        linhas.insert(i + 1, "user_language = 1".to_string());
    } else {
        if linhas.last().is_some_and(|l| !l.trim().is_empty()) {
            linhas.push(String::new());
        }
        linhas.push("[kernel]".to_string());
        linhas.push("user_language = 1".to_string());
    }
    let mut novo = linhas.join("\n");
    novo.push('\n');
    (novo, true)
}

/// Valor TOML de um caminho: string literal com barras normais (como o reNut grava os seus);
/// se o caminho tiver aspas simples, string basica.
fn valor_caminho(pasta: &std::path::Path) -> String {
    let texto = pasta.to_string_lossy().replace('\\', "/");
    if texto.contains('\'') {
        format!("\"{}\"", texto.replace('"', "\\\""))
    } else {
        format!("'{texto}'")
    }
}

/// `[renut] renut_mods_folder` configurado, se houver.
pub fn pasta_mods_configurada(texto: &str) -> Option<String> {
    let mut secao = String::new();
    for linha in texto.lines() {
        let l = linha.trim();
        if l.starts_with('[') && l.ends_with(']') {
            secao = l.trim_matches(['[', ']']).trim().to_lowercase();
            continue;
        }
        if secao == "renut" {
            if let Some((c, v)) = l.split_once('=') {
                if c.trim().eq_ignore_ascii_case("renut_mods_folder") {
                    return Some(limpar_valor(v));
                }
            }
        }
    }
    None
}

/// Devolve o texto com `[renut] renut_mods_folder` apontando para `pasta`, preservando as outras
/// linhas. O reNut resolve a pasta de mods relativa ao executavel; o launcher traduzido roda de
/// `launcher-ptbr/` e, sem esta chave, procuraria `launcher-ptbr/mods` em vez da pasta da instalacao.
pub fn com_pasta_mods(texto: &str, pasta: &std::path::Path) -> (String, bool) {
    let linha_nova = format!("renut_mods_folder = {}", valor_caminho(pasta));
    let mut linhas: Vec<String> = texto.lines().map(str::to_string).collect();
    let mut secao = String::new();
    let mut indice_secao: Option<usize> = None;
    let mut indice_chave: Option<usize> = None;
    for (i, linha) in linhas.iter().enumerate() {
        let l = linha.trim();
        if l.starts_with('[') && l.ends_with(']') {
            secao = l.trim_matches(['[', ']']).trim().to_lowercase();
            if secao == "renut" && indice_secao.is_none() {
                indice_secao = Some(i);
            }
            continue;
        }
        if secao == "renut" {
            if let Some((c, _)) = l.split_once('=') {
                if c.trim().eq_ignore_ascii_case("renut_mods_folder") {
                    indice_chave = Some(i);
                }
            }
        }
    }
    if let Some(i) = indice_chave {
        if linhas[i].trim() == linha_nova {
            return (texto.to_string(), false);
        }
        let recuo: String = linhas[i].chars().take_while(|c| c.is_whitespace()).collect();
        linhas[i] = format!("{recuo}{linha_nova}");
    } else if let Some(i) = indice_secao {
        linhas.insert(i + 1, linha_nova);
    } else {
        if linhas.last().is_some_and(|l| !l.trim().is_empty()) {
            linhas.push(String::new());
        }
        linhas.push("[renut]".to_string());
        linhas.push(linha_nova);
    }
    let mut novo = linhas.join("\n");
    novo.push('\n');
    (novo, true)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn pasta_de_mods_entra_na_secao_renut_sem_mexer_no_resto() {
        let texto = "[app]\nroot = 'C:/Jogos/reNut'\n\n[renut]\nrenut_msaa = '8x'\n\n[kernel]\nuser_language = 1\n";
        let pasta = std::path::Path::new("C:\\Jogos\\reNut com espaco\\mods");
        let (novo, mudou) = com_pasta_mods(texto, pasta);
        assert!(mudou);
        assert!(
            novo.contains("[renut]\nrenut_mods_folder = 'C:/Jogos/reNut com espaco/mods'\nrenut_msaa = '8x'"),
            "{novo}"
        );
        assert!(novo.contains("root = 'C:/Jogos/reNut'"));
        assert!(novo.contains("[kernel]\nuser_language = 1"));
        assert_eq!(pasta_mods_configurada(&novo).as_deref(), Some("C:/Jogos/reNut com espaco/mods"));
        let (de_novo, mudou2) = com_pasta_mods(&novo, pasta);
        assert!(!mudou2);
        assert_eq!(de_novo, novo);
    }

    #[test]
    fn pasta_de_mods_substitui_valor_antigo_e_cria_secao() {
        let (novo, _) = com_pasta_mods("[renut]\n  renut_mods_folder = 'mods'\n", std::path::Path::new("D:/r/mods"));
        assert_eq!(novo, "[renut]\n  renut_mods_folder = 'D:/r/mods'\n");
        let (novo, _) = com_pasta_mods("[app]\nroot = 'x'\n", std::path::Path::new("D:/r/mods"));
        assert_eq!(novo, "[app]\nroot = 'x'\n\n[renut]\nrenut_mods_folder = 'D:/r/mods'\n");
    }

    const EXEMPLO: &str = "[app]\nroot = 'C:/Games/reNut'\nuser_root = 'C:/Games/reNut/save'\n\n[title]\ngame_root = 'C:/Games/reNut/game/extraido'\nupdate_root = 'C:/Games/reNut/update/TU3'\n\n[ui]\ntitle = 'renut'\n";

    #[test]
    fn le_caminhos() {
        let c = ler(EXEMPLO);
        assert_eq!(c.app_root.unwrap().to_string_lossy(), "C:/Games/reNut");
        assert_eq!(
            c.game_root.unwrap().to_string_lossy(),
            "C:/Games/reNut/game/extraido"
        );
        assert_eq!(c.user_language, None);
    }

    #[test]
    fn adiciona_idioma_sem_mexer_no_resto() {
        let (novo, mudou) = com_idioma_ingles(EXEMPLO);
        assert!(mudou);
        assert!(novo.contains("[kernel]\nuser_language = 1"));
        assert!(novo.contains("root = 'C:/Games/reNut'"));
        let c = ler(&novo);
        assert_eq!(c.user_language, Some(1));
    }

    #[test]
    fn preserva_idioma_quando_ja_e_um() {
        let texto = "[kernel]\nuser_language = 1\n";
        let (novo, mudou) = com_idioma_ingles(texto);
        assert!(!mudou);
        assert_eq!(novo, texto);
    }
}