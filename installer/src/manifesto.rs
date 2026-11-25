//! Manifesto privado da instalacao, com os arquivos e hashes gerenciados pelo instalador.

use std::fs;
use std::path::{Path, PathBuf};

use serde_json::{Map, Value, json};

use crate::sha256::sha256_hex;

pub const PASTA_ESTADO: &str = ".ptbr-instalador";
pub const ARQUIVO_MANIFESTO: &str = "manifesto.json";
pub const SCHEMA: &str = "renut-instalador-ptbr/1";

#[derive(Clone, Default)]
pub struct ComponenteMod {
    pub pasta: String,
    pub nbpatch_sha256: String,
    pub mod_toml_sha256: String,
}

#[derive(Clone, Default)]
pub struct ComponenteLauncher {
    pub pasta: String,
    pub exe: String,
    pub exe_sha256: String,
    pub dlls: Vec<(String, String)>,
    pub arquivos: Vec<(String, String)>,
}

#[derive(Clone, Default)]
pub struct Manifesto {
    pub raiz: String,
    pub instalado_em: String,
    pub mod_jogo: Option<ComponenteMod>,
    pub launcher: Option<ComponenteLauncher>,
    pub atalho: Option<String>,
}

impl Manifesto {
    pub fn caminho(raiz: &Path) -> PathBuf {
        raiz.join(PASTA_ESTADO).join(ARQUIVO_MANIFESTO)
    }

    pub fn carregar(raiz: &Path) -> Option<Manifesto> {
        let texto = fs::read_to_string(Self::caminho(raiz)).ok()?;
        let v: Value = serde_json::from_str(&texto).ok()?;
        let mut m = Manifesto {
            raiz: v["raiz"].as_str().unwrap_or("").to_string(),
            instalado_em: v["instalado_em"].as_str().unwrap_or("").to_string(),
            ..Default::default()
        };
        if let Some(mj) = v.get("mod_jogo").and_then(|x| x.as_object()) {
            m.mod_jogo = Some(ComponenteMod {
                pasta: mj["pasta"].as_str().unwrap_or("").to_string(),
                nbpatch_sha256: mj["nbpatch_sha256"].as_str().unwrap_or("").to_string(),
                mod_toml_sha256: mj["mod_toml_sha256"].as_str().unwrap_or("").to_string(),
            });
        }
        if let Some(l) = v.get("launcher").and_then(|x| x.as_object()) {
            let dlls = l["dlls"]
                .as_object()
                .map(|o| {
                    o.iter()
                        .map(|(k, v)| (k.clone(), v.as_str().unwrap_or("").to_string()))
                        .collect()
                })
                .unwrap_or_default();
            let arquivos = l["arquivos"]
                .as_object()
                .map(|o| {
                    o.iter()
                        .map(|(k, v)| (k.clone(), v.as_str().unwrap_or("").to_string()))
                        .collect()
                })
                .unwrap_or_default();
            m.launcher = Some(ComponenteLauncher {
                pasta: l["pasta"].as_str().unwrap_or("").to_string(),
                exe: l["exe"].as_str().unwrap_or("").to_string(),
                exe_sha256: l["exe_sha256"].as_str().unwrap_or("").to_string(),
                dlls,
                arquivos,
            });
        }
        m.atalho = v["atalho"].as_str().map(str::to_string);
        Some(m)
    }

    pub fn gravar(&self, raiz: &Path) -> Result<(), String> {
        let mut obj = Map::new();
        obj.insert("schema".into(), json!(SCHEMA));
        obj.insert("instalado_em".into(), json!(self.instalado_em));
        obj.insert("raiz".into(), json!(self.raiz));
        match &self.mod_jogo {
            Some(m) => {
                obj.insert(
                    "mod_jogo".into(),
                    json!({
                        "pasta": m.pasta,
                        "nbpatch_sha256": m.nbpatch_sha256,
                        "mod_toml_sha256": m.mod_toml_sha256,
                    }),
                );
            }
            None => {
                obj.insert("mod_jogo".into(), Value::Null);
            }
        }
        match &self.launcher {
            Some(l) => {
                let dlls: Map<String, Value> = l
                    .dlls
                    .iter()
                    .map(|(k, v)| (k.clone(), json!(v)))
                    .collect();
                let arquivos: Map<String, Value> = l
                    .arquivos
                    .iter()
                    .map(|(k, v)| (k.clone(), json!(v)))
                    .collect();
                obj.insert(
                    "launcher".into(),
                    json!({
                        "pasta": l.pasta,
                        "exe": l.exe,
                        "exe_sha256": l.exe_sha256,
                        "dlls": Value::Object(dlls),
                        "arquivos": Value::Object(arquivos),
                    }),
                );
            }
            None => {
                obj.insert("launcher".into(), Value::Null);
            }
        }
        obj.insert(
            "atalho".into(),
            self.atalho.clone().map(Value::String).unwrap_or(Value::Null),
        );
        let texto = serde_json::to_string_pretty(&Value::Object(obj))
            .map_err(|e| format!("Não montei o manifesto: {e}"))?;
        gravar_texto(&Self::caminho(raiz), &(texto + "\n"))
    }

    pub fn remover_estado(raiz: &Path) -> Result<(), String> {
        let pasta = raiz.join(PASTA_ESTADO);
        if !pasta.exists() {
            return Ok(());
        }
        // So apaga a pasta de estado, que e exclusiva do instalador.
        for item in fs::read_dir(&pasta).map_err(|e| format!("Não li {}: {e}", pasta.display()))? {
            let item = item.map_err(|e| e.to_string())?;
            if item.path().is_file() {
                fs::remove_file(item.path()).ok();
            }
        }
        fs::remove_dir(&pasta).map_err(|e| format!("Não removi {}: {e}", pasta.display()))?;
        Ok(())
    }
}

pub fn gravar_texto(destino: &Path, texto: &str) -> Result<(), String> {
    let pasta = destino
        .parent()
        .ok_or_else(|| format!("Destino sem pasta: {}", destino.display()))?;
    fs::create_dir_all(pasta).map_err(|e| format!("Não criei {}: {e}", pasta.display()))?;
    let tmp = destino.with_file_name(format!(
        ".{}.tmp",
        destino.file_name().unwrap_or_default().to_string_lossy()
    ));
    fs::write(&tmp, texto.as_bytes()).map_err(|e| format!("Não gravei {}: {e}", tmp.display()))?;
    if destino.exists() {
        fs::remove_file(destino).map_err(|e| format!("Não substitui {}: {e}", destino.display()))?;
    }
    fs::rename(&tmp, destino).map_err(|e| format!("Não renomeei {}: {e}", destino.display()))?;
    Ok(())
}

pub fn gravar_bytes_verificando(destino: &Path, dados: &[u8]) -> Result<(), String> {
    let pasta = destino
        .parent()
        .ok_or_else(|| format!("Destino sem pasta: {}", destino.display()))?;
    fs::create_dir_all(pasta).map_err(|e| format!("Não criei {}: {e}", pasta.display()))?;
    let tmp = destino.with_file_name(format!(
        ".{}.tmp",
        destino.file_name().unwrap_or_default().to_string_lossy()
    ));
    fs::write(&tmp, dados).map_err(|e| format!("Não gravei {}: {e}", tmp.display()))?;
    let lido = fs::read(&tmp).map_err(|e| format!("Não reli {}: {e}", tmp.display()))?;
    if sha256_hex(&lido) != sha256_hex(dados) {
        let _ = fs::remove_file(&tmp);
        return Err("O arquivo gravado não passou na verificação.".into());
    }
    if destino.exists() {
        fs::remove_file(destino).map_err(|e| format!("Não substitui {}: {e}", destino.display()))?;
    }
    fs::rename(&tmp, destino).map_err(|e| format!("Não renomeei {}: {e}", destino.display()))?;
    Ok(())
}

/// Data e hora UTC em texto, sem dependencia de biblioteca de tempo.
pub fn agora_utc() -> String {
    let segs = std::time::SystemTime::now()
        .duration_since(std::time::UNIX_EPOCH)
        .map(|d| d.as_secs())
        .unwrap_or(0);
    let dias = segs / 86_400;
    let (ano, mes, dia) = civil_de_dias(dias as i64);
    let h = (segs % 86_400) / 3600;
    let m = (segs % 3600) / 60;
    let s = segs % 60;
    format!("{ano:04}-{mes:02}-{dia:02}T{h:02}:{m:02}:{s:02}Z")
}

fn civil_de_dias(dias: i64) -> (i64, u32, u32) {
    // Algoritmo de Howard Hinnant (proleptico gregoriano).
    let z = dias + 719_468;
    let era = if z >= 0 { z } else { z - 146_096 } / 146_097;
    let doe = z - era * 146_097;
    let yoe = (doe - doe / 1460 + doe / 36_524 - doe / 146_096) / 365;
    let y = yoe + era * 400;
    let doy = doe - (365 * yoe + yoe / 4 - yoe / 100);
    let mp = (5 * doy + 2) / 153;
    let d = (doy - (153 * mp + 2) / 5 + 1) as u32;
    let m = if mp < 10 { mp + 3 } else { mp - 9 } as u32;
    (if m <= 2 { y + 1 } else { y }, m, d)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn data_conhecida() {
        // 1970-01-01 e 2026-11-23 (conferidos por calendario).
        assert_eq!(civil_de_dias(0), (1970, 1, 1));
        assert_eq!(civil_de_dias(20_780), (2026, 11, 23));
    }
}