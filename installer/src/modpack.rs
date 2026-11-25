//! Geracao local do mod PT-BR (`.nbpatch` + `mod.toml`) a partir da copia legitima do jogo.
//!
//! Porte fiel de `tools/gerar_mod.py` + `tools/nbptbr/empacotar.py`. O formato e o mesmo desde a
//! 0.7.0: pasta nova `loctext/englishus`, arquivos `Kind="new"`, ZIP sem compressao. O pacote
//! atual e o da revisao 0.8.0; o SHA-256 resultante e comparado com o pacote conferido, e o da
//! Release v0.7.0 fica registrado para reconhecer instalacoes anteriores e atualiza-las.

use std::collections::HashMap;
use std::path::Path;

use crate::loctext;
use crate::sha256::{hash_texto, sha256_hex};
use crate::traducao::ArquivoTrad;
use crate::zipw::Zip;

pub const VERSAO: &str = "0.8.0";
pub const ID_MOD: &str = "ptbr_traducao";
pub const SHA_ESPERADO: &str = "d250b5959e7f0171355f9d6a3e1ac031e8c123dfb5fbfb0423beca538e20d8db";
/// Release v0.7.0 (referencia historica): reconhecida para atualizar para a versao atual.
pub const VERSAO_V070: &str = "0.7.0";
pub const SHA_V070: &str = "7cd39a34efbae21dc8d3f919e63349e15df88397080ad59dd07207da0f5b5e25";
/// Pacotes que este instalador sabe que criou (versao, SHA-256 do `.nbpatch`).
pub const VERSOES_CONHECIDAS: &[(&str, &str)] = &[(VERSAO, SHA_ESPERADO), (VERSAO_V070, SHA_V070)];

/// Versao do mod de traducao a que pertence um `.nbpatch`, pelo SHA-256.
pub fn versao_do_sha(sha: &str) -> Option<&'static str> {
    VERSOES_CONHECIDAS.iter().find(|(_, s)| *s == sha).map(|(v, _)| *v)
}
pub const FRASES_ESPERADAS: usize = 6099;
pub const ARQUIVOS_ESPERADOS: usize = 107;

pub struct ModGerado {
    pub nbpatch: Vec<u8>,
    pub mod_toml: String,
    pub sha256: String,
    pub frases: usize,
    pub arquivos: usize,
    pub sha_confere: bool,
}

fn escapar_json(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 2);
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            c if (c as u32) < 0x20 => out.push_str(&format!("\\u{:04x}", c as u32)),
            c => out.push(c),
        }
    }
    out
}

/// Mesmo texto de `mod_toml` do gerador Python (somente ASCII).
pub fn mod_toml(n_frases: usize) -> String {
    format!(
        "name = \"Traducao PT-BR\"\n\
         description = \"Brazilian Portuguese text loaded from loctext/englishus (English, 1). \
         The game files are not modified. {n_frases} translated phrases.\"\n\
         version = \"{VERSAO}\"\n\
         author = \"Projeto de traducao PT-BR (fas)\"\n"
    )
}

/// Mesmo `patch.json` do gerador Python (indentacao de 2 espacos, ordem dos campos preservada).
pub fn patch_json(arquivos: &[(String, String, u64, String)]) -> String {
    let mut s = String::new();
    s.push_str("{\n");
    s.push_str("  \"Format\": 1,\n");
    s.push_str("  \"Name\": \"Traducao PT-BR\",\n");
    s.push_str(&format!("  \"Id\": \"{ID_MOD}\",\n"));
    s.push_str(&format!("  \"Version\": \"{VERSAO}\",\n"));
    s.push_str("  \"Author\": \"Projeto de traducao PT-BR (fas)\",\n");
    s.push_str("  \"Category\": \"Translation\",\n");
    s.push_str("  \"Requires\": [],\n");
    s.push_str("  \"Conflicts\": [],\n");
    s.push_str("  \"Ops\": [],\n");
    if arquivos.is_empty() {
        s.push_str("  \"Files\": [],\n");
    } else {
        s.push_str("  \"Files\": [\n");
        for (i, (caminho, sha, tamanho, entry)) in arquivos.iter().enumerate() {
            s.push_str("    {\n");
            s.push_str(&format!("      \"Path\": \"{}\",\n", escapar_json(caminho)));
            s.push_str("      \"Kind\": \"new\",\n");
            s.push_str(&format!("      \"TargetSha256\": \"{sha}\",\n"));
            s.push_str(&format!("      \"TargetSize\": {tamanho},\n"));
            s.push_str(&format!("      \"Entry\": \"{}\"\n", escapar_json(entry)));
            s.push_str(if i + 1 == arquivos.len() { "    }\n" } else { "    },\n" });
        }
        s.push_str("  ],\n");
    }
    s.push_str("  \"ExeMods\": []\n");
    s.push_str("}\n");
    s
}

/// Uma frase que veio do catalogo, já com o texto que vai para o arquivo.
fn aplicar_traducao(
    nome: &str,
    base: &[u8],
    referencia: &HashMap<String, String>,
    trad: &ArquivoTrad,
) -> Result<(Vec<u8>, usize), String> {
    let arq = loctext::ler(base)
        .map_err(|e| format!("O texto do jogo {nome} não pode ser lido: {e}"))?;
    let existentes: HashMap<String, String> = arq
        .frases()?
        .into_iter()
        .map(|f| (f.chave, f.texto))
        .collect();
    let mut novos: HashMap<String, String> = HashMap::new();
    for t in &trad.frases {
        if t.texto_ptbr.is_empty() {
            continue;
        }
        if !existentes.contains_key(&t.chave) {
            continue; // chave só existe no espanhol (creditos)
        }
        if let Some(esperado) = &t.hash_es {
            if let Some(ref_es) = referencia.get(&t.chave) {
                let obtido = hash_texto(ref_es);
                if &obtido != esperado {
                    return Err(format!(
                        "O texto original de {nome} mudou desde a tradução (chave {}). \
                         Sua cópia do jogo não é a versão suportada.",
                        t.chave
                    ));
                }
            }
        }
        novos.insert(t.chave.clone(), t.texto_ptbr.clone());
    }
    let substituidas = novos.len();
    let novo = loctext::escrever(&arq.com_textos_por_chave(&novos)?)?;

    // Aceite da reinsercao: releitura frase a frase tem de bater com o esperado.
    let relido = loctext::ler(&novo)?;
    let mut esperado: HashMap<String, String> = existentes.clone();
    for (k, v) in &novos {
        esperado.insert(k.clone(), v.clone());
    }
    let obtido: HashMap<String, String> = relido
        .frases()?
        .into_iter()
        .map(|f| (f.chave, f.texto))
        .collect();
    if obtido != esperado {
        return Err(format!("O arquivo gerado de {nome} não confere com a tradução."));
    }
    Ok((novo, substituidas))
}

fn caminho_ingles(extraido: &Path, nome: &str) -> std::path::PathBuf {
    extraido
        .join("Debug")
        .join(&nome[0..2])
        .join(&nome[2..4])
        .join(&nome[4..6])
        .join(&nome[6..8])
}

/// Gera o pacote completo. `progresso` recebe (arquivo atual, total de arquivos).
pub fn gerar<F: FnMut(usize, usize)>(
    extraido: &Path,
    catalogo: &[ArquivoTrad],
    mut progresso: F,
) -> Result<ModGerado, String> {
    if !extraido.join("Debug").is_dir() || !extraido.join("loctext").join("spanish").is_dir() {
        return Err(
            "A pasta do jogo não parece ser a extração completa do reNut (faltam Debug ou \
             loctext/spanish)."
                .into(),
        );
    }
    if extraido.join("loctext").join("englishus").exists() {
        return Err(
            "A pasta do jogo já tem loctext/englishus; o mod precisa criar essa pasta, não \
             substituir uma existente."
                .into(),
        );
    }
    if catalogo.len() != ARQUIVOS_ESPERADOS {
        return Err(format!(
            "O catálogo embutido está incompleto: {} de {ARQUIVOS_ESPERADOS} arquivos.",
            catalogo.len()
        ));
    }

    let mut nomes: Vec<String> = catalogo.iter().map(|a| a.arquivo.clone()).collect();
    nomes.sort();
    let mut faltando_en = Vec::new();
    let mut faltando_es = Vec::new();
    for nome in &nomes {
        if !caminho_ingles(extraido, nome).is_file() {
            faltando_en.push(nome.clone());
        }
        if !extraido.join("loctext").join("spanish").join(nome).is_file() {
            faltando_es.push(nome.clone());
        }
    }
    if !faltando_en.is_empty() || !faltando_es.is_empty() {
        let mut detalhes = Vec::new();
        if !faltando_en.is_empty() {
            detalhes.push(format!("{} texto(s) em inglês", faltando_en.len()));
        }
        if !faltando_es.is_empty() {
            detalhes.push(format!("{} texto(s) em espanhol", faltando_es.len()));
        }
        return Err(format!(
            "A pasta do jogo não é a versão completa esperada: faltam {}. \
             Confira se o jogo terminou de extrair e se a pasta e a certa.",
            detalhes.join(" e ")
        ));
    }

    let mut entradas_zip: Vec<(String, Vec<u8>)> = Vec::new();
    let mut arquivos_json: Vec<(String, String, u64, String)> = Vec::new();
    let mut total_frases = 0usize;
    let total = nomes.len();

    for (i, nome) in nomes.iter().enumerate() {
        let base = std::fs::read(caminho_ingles(extraido, nome))
            .map_err(|e| format!("Não li o texto do jogo {nome}: {e}"))?;
        let espanhol = std::fs::read(extraido.join("loctext").join("spanish").join(nome))
            .map_err(|e| format!("Não li a referencia em espanhol de {nome}: {e}"))?;
        let referencia: HashMap<String, String> = loctext::ler(&espanhol)
            .map_err(|e| format!("A referência em espanhol de {nome} é inválida: {e}"))?
            .frases()?
            .into_iter()
            .map(|f| (f.chave, f.texto))
            .collect();
        let trad = catalogo
            .iter()
            .find(|a| &a.arquivo == nome)
            .ok_or_else(|| format!("Catálogo sem o arquivo {nome}."))?;
        let (novo, substituidas) = aplicar_traducao(nome, &base, &referencia, trad)?;
        // Confere que o arquivo gerado continua sendo um loctext valido.
        loctext::ler(&novo)?;
        total_frases += substituidas;

        let caminho = format!("loctext/englishus/{nome}");
        let entry = format!("files/{caminho}");
        let sha = sha256_hex(&novo);
        let tamanho = novo.len() as u64;
        arquivos_json.push((caminho, sha, tamanho, entry.clone()));
        entradas_zip.push((entry, novo));
        progresso(i + 1, total);
    }

    let pj = patch_json(&arquivos_json);
    let mut zip = Zip::novo();
    zip.adicionar("patch.json", pj.into_bytes());
    for (nome, dados) in entradas_zip {
        zip.adicionar(&nome, dados);
    }
    let nbpatch = zip.finalizar();
    let sha256 = sha256_hex(&nbpatch);
    let sha_confere = sha256 == SHA_ESPERADO;
    Ok(ModGerado {
        mod_toml: mod_toml(total_frases),
        nbpatch,
        sha256,
        frases: total_frases,
        arquivos: total,
        sha_confere,
    })
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn zip_do_mod_igual_ao_do_python() {
        let mut z = Zip::novo();
        z.adicionar(
            "patch.json",
            patch_json(&[(
                "loctext/englishus/1100216a".to_string(),
                "af2bad7518b9d1342e9ec1881c27113f9f1285ba2b9d98ad88124c8d8052ef05".to_string(),
                640,
                "files/loctext/englishus/1100216a".to_string(),
            )])
            .into_bytes(),
        );
        z.adicionar("files/loctext/englishus/1100216a", vec![0u8; 640]);
        let zip = z.finalizar();
        // Bytes conferidos contra o `zipfile` do Python (mesmo patch.json é mesmo conteudo).
        // O patch.json leva a versao: 0.7.0 dava 2d7dd0b6…d966; 0.8.0 da 96afb271…6940
        // (os dois valores recalculados por tools/nbptbr/empacotar.py em 2026-11-25).
        assert_eq!(zip.len(), 1394);
        assert_eq!(
            sha256_hex(&zip),
            "96afb2714f98603bdffd5dd8418166caf4d2b771dcd312c91176f8a03ddf6940"
        );
    }
}