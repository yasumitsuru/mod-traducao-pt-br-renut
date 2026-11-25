//! Patch binario do launcher do reNut, aplicado SOMENTE em copias.
//!
//! Diferenca em relacao ao aplicador antigo: a instalacao do launcher so termina com sucesso
//! quando o executavel E as duas DLLs obrigatorias conferem com o manifesto. Se uma DLL falhar,
//! a operacao inteira falha e nada e publicado.

use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, Ordering};

use crate::sha256::sha256_hex;

const MANIFESTO: &str = include_str!("../../launcher-patch/manifesto.json");
const MANIFESTO_ENGINE: &str = include_str!("../../launcher-patch/engine/manifesto.json");
// Os patches binarios do launcher NAO sao embutidos: o executavel e as DLLs traduzidos sao gerados
// na hora a partir dos arquivos do usuario (gerador_launcher). Daqui so vem o manifesto com os
// SHA-256 de entrada e de saida da versao suportada.

pub const NOME_EXE_TRADUZIDO: &str = "renut.ptbr.exe";

#[derive(Clone)]
pub struct ManifestoLauncher {
    pub patch_version: String,
    pub status: String,
    pub release: String,
    pub version: String,
    pub input_size: u64,
    pub input_sha256: String,
    pub output_size: u64,
    pub output_sha256: String,
}

#[derive(Clone)]
pub struct Componente {
    pub file: String,
    pub patch_file: String,
    pub input_size: u64,
    pub input_sha256: String,
    pub output_size: u64,
    pub output_sha256: String,
}

#[derive(Clone)]
pub struct Edit {
    pub offset: usize,
    pub old: Vec<u8>,
    pub new: Vec<u8>,
    pub note: String,
}

#[derive(Clone)]
pub struct Patch {
    pub edits: Vec<Edit>,
}

pub struct ResumoRuntime {
    pub exe_sha: String,
    pub dlls: Vec<(String, String)>,
    pub arquivos: Vec<String>,
    pub bytes: u64,
}

pub fn manifesto() -> Result<ManifestoLauncher, String> {
    let v: serde_json::Value =
        serde_json::from_str(MANIFESTO).map_err(|e| format!("Manifesto do launcher inválido: {e}"))?;
    Ok(ManifestoLauncher {
        patch_version: v["patch_version"].as_str().unwrap_or("").to_string(),
        status: v["status"].as_str().unwrap_or("").to_string(),
        release: v["release"].as_str().unwrap_or("").to_string(),
        version: v["version"].as_str().unwrap_or("").to_string(),
        input_size: v["input_size"].as_u64().unwrap_or(0),
        input_sha256: v["input_sha256"].as_str().unwrap_or("").to_string(),
        output_size: v["output_size"].as_u64().unwrap_or(0),
        output_sha256: v["output_sha256"].as_str().unwrap_or("").to_string(),
    })
}

pub fn componentes() -> Result<Vec<Componente>, String> {
    let v: serde_json::Value = serde_json::from_str(MANIFESTO_ENGINE)
        .map_err(|e| format!("Manifesto do motor inválido: {e}"))?;
    let lista = v["components"]
        .as_array()
        .ok_or("Manifesto do motor sem componentes.")?;
    let mut out = Vec::new();
    for c in lista {
        out.push(Componente {
            file: c["file"].as_str().ok_or("Componente sem arquivo.")?.to_string(),
            patch_file: c["patch_file"]
                .as_str()
                .ok_or("Componente sem patch.")?
                .to_string(),
            input_size: c["input_size"].as_u64().ok_or("Componente sem tamanho.")?,
            input_sha256: c["input_sha256"]
                .as_str()
                .ok_or("Componente sem hash.")?
                .to_string(),
            output_size: c["output_size"].as_u64().ok_or("Componente sem tamanho de saida.")?,
            output_sha256: c["output_sha256"]
                .as_str()
                .ok_or("Componente sem hash de saida.")?
                .to_string(),
        });
    }
    Ok(out)
}

pub(crate) fn decodificar_base64(s: &str) -> Result<Vec<u8>, String> {
    fn valor(c: u8) -> Option<u8> {
        match c {
            b'A'..=b'Z' => Some(c - b'A'),
            b'a'..=b'z' => Some(c - b'a' + 26),
            b'0'..=b'9' => Some(c - b'0' + 52),
            b'+' => Some(62),
            b'/' => Some(63),
            _ => None,
        }
    }
    let mut out = Vec::new();
    let mut buf = 0u32;
    let mut bits = 0u32;
    for c in s.bytes() {
        if c == b'=' || c.is_ascii_whitespace() {
            continue;
        }
        let v = valor(c).ok_or_else(|| format!("Base64 inválido: {c}"))?;
        buf = (buf << 6) | u32::from(v);
        bits += 6;
        if bits >= 8 {
            bits -= 8;
            out.push((buf >> bits) as u8);
            buf &= (1 << bits) - 1;
        }
    }
    Ok(out)
}

pub fn sha256_arquivo(p: &Path) -> Result<String, String> {
    let dados = fs::read(p).map_err(|e| format!("Não li {}: {e}", p.display()))?;
    Ok(sha256_hex(&dados))
}

pub fn verificar_executavel(exe: &Path) -> Result<String, String> {
    let meta = fs::metadata(exe).map_err(|_| format!("renut.exe não encontrado em {}", exe.display()))?;
    let m = manifesto()?;
    if meta.len() != m.input_size {
        return Err(format!(
            "O renut.exe tem {} bytes; a versão suportada ({}) tem {} bytes.",
            meta.len(),
            m.version,
            m.input_size
        ));
    }
    let sha = sha256_arquivo(exe)?;
    if sha != m.input_sha256 {
        return Err(format!(
            "O renut.exe não é a versão suportada ({} {}).\nEsperado: {}\nEncontrado: {}",
            m.release, m.version, m.input_sha256, sha
        ));
    }
    Ok(sha)
}

fn gravar_verificando(destino: &Path, dados: &[u8]) -> Result<(), String> {
    let pasta = destino
        .parent()
        .ok_or_else(|| format!("Destino sem pasta: {}", destino.display()))?;
    fs::create_dir_all(pasta).map_err(|e| format!("Não criei {}: {e}", pasta.display()))?;
    let tmp = destino.with_file_name(format!(
        ".{}.ptbr-tmp",
        destino.file_name().unwrap_or_default().to_string_lossy()
    ));
    {
        let mut f = fs::File::create(&tmp).map_err(|e| format!("Não criei {}: {e}", tmp.display()))?;
        f.write_all(dados).map_err(|e| format!("Não gravei {}: {e}", tmp.display()))?;
        f.sync_all().ok();
    }
    let conferido = fs::read(&tmp).map_err(|e| format!("Não reli {}: {e}", tmp.display()))?;
    if sha256_hex(&conferido) != sha256_hex(dados) {
        let _ = fs::remove_file(&tmp);
        return Err("A cópia gravada não passou na verificação.".into());
    }
    if destino.exists() {
        fs::remove_file(destino).map_err(|e| format!("Não substitui {}: {e}", destino.display()))?;
    }
    fs::rename(&tmp, destino).map_err(|e| format!("Não renomeei {}: {e}", destino.display()))?;
    Ok(())
}

/// Aplica o patch do executável numa cópia verificada.
pub fn aplicar_executavel(origem: &Path, destino: &Path) -> Result<String, String> {
    let m = manifesto()?;
    verificar_executavel(origem)?;
    let dados = fs::read(origem).map_err(|e| format!("Não li {}: {e}", origem.display()))?;
    // Gerado aqui, a partir do renut.exe do usuario (nenhum patch pronto e distribuido).
    let novo = crate::gerador_launcher::gerar_executavel(&dados)?;
    let sha = sha256_hex(&novo);
    if novo.len() as u64 != m.output_size || sha != m.output_sha256 {
        return Err(format!(
            "O resultado do patch do executável não confere com o manifesto.\nEsperado: {} ({} bytes)\nObtido: {} ({} bytes)",
            m.output_sha256,
            m.output_size,
            sha,
            novo.len()
        ));
    }
    gravar_verificando(destino, &novo)?;
    if sha256_arquivo(destino)? != m.output_sha256 {
        return Err("A cópia do executável gravada não passou na segunda verificação.".into());
    }
    Ok(sha)
}

fn aplicar_dll(origem: &Path, destino: &Path, comp: &Componente) -> Result<String, String> {
    let dados = fs::read(origem).map_err(|e| format!("Não li {}: {e}", origem.display()))?;
    if dados.len() as u64 != comp.input_size || sha256_hex(&dados) != comp.input_sha256 {
        return Err(format!(
            "{} não é a versão suportada do reNut; nada foi alterado.",
            comp.file
        ));
    }
    let novo = crate::gerador_launcher::gerar_dll(&comp.file, &dados)?;
    let sha = sha256_hex(&novo);
    if novo.len() as u64 != comp.output_size || sha != comp.output_sha256 {
        return Err(format!(
            "O resultado do patch de {} não confere com o manifesto; a instalação foi cancelada.",
            comp.file
        ));
    }
    gravar_verificando(destino, &novo)?;
    if sha256_arquivo(destino)? != comp.output_sha256 {
        return Err(format!("A cópia traduzida de {} não passou na verificação.", comp.file));
    }
    Ok(sha)
}

fn copiar_arquivo(origem: &Path, destino: &Path) -> Result<u64, String> {
    let meta = fs::metadata(origem).map_err(|e| format!("Não li {}: {e}", origem.display()))?;
    if meta.len() > 512 * 1024 * 1024 {
        return Err(format!("Arquivo grande demais para copiar: {}", origem.display()));
    }
    if let Some(pai) = destino.parent() {
        fs::create_dir_all(pai).map_err(|e| format!("Não criei {}: {e}", pai.display()))?;
    }
    fs::copy(origem, destino)
        .map_err(|e| format!("Não copiei {}: {e}", origem.display()))?;
    Ok(meta.len())
}

fn copiar_pasta(origem: &Path, destino: &Path, profundidade: usize) -> Result<Vec<String>, String> {
    let mut arquivos = Vec::new();
    if profundidade > 3 || !origem.is_dir() {
        return Ok(arquivos);
    }
    fs::create_dir_all(destino).map_err(|e| format!("Não criei {}: {e}", destino.display()))?;
    for item in fs::read_dir(origem).map_err(|e| format!("Não li {}: {e}", origem.display()))? {
        let item = item.map_err(|e| e.to_string())?;
        let tipo = item.file_type().map_err(|e| e.to_string())?;
        if tipo.is_symlink() {
            return Err(format!(
                "A pasta {} contém um link simbólico; por segurança ele não é copiado.",
                origem.display()
            ));
        }
        let alvo = destino.join(item.file_name());
        if tipo.is_dir() {
            fs::create_dir_all(&alvo).map_err(|e| format!("Não criei {}: {e}", alvo.display()))?;
            arquivos.extend(copiar_pasta(&item.path(), &alvo, profundidade + 1)?);
        } else if tipo.is_file() {
            copiar_arquivo(&item.path(), &alvo)?;
            arquivos.push(alvo.to_string_lossy().to_string());
        }
    }
    Ok(arquivos)
}

/// Prepara a pasta temporária do runtime traduzido: exe, todas as DLLs, as duas DLLs do motor
/// traduzidas e o `lua_api` (quando existe). A pasta final só recebe o resultado depois de tudo
/// conferido.
pub fn preparar_runtime<F: FnMut(usize, usize, &str)>(
    origem_dir: &Path,
    temp_dir: &Path,
    cancelar: &AtomicBool,
    mut progresso: F,
) -> Result<ResumoRuntime, String> {
    if !origem_dir.is_dir() {
        return Err("A pasta do reNut não existe.".into());
    }
    if temp_dir.exists() {
        fs::remove_dir_all(temp_dir).map_err(|e| format!("Não limpei {}: {e}", temp_dir.display()))?;
    }
    fs::create_dir_all(temp_dir).map_err(|e| format!("Não criei {}: {e}", temp_dir.display()))?;

    let dlls_origem: Vec<PathBuf> = fs::read_dir(origem_dir)
        .map_err(|e| format!("Não li {}: {e}", origem_dir.display()))?
        .filter_map(|i| i.ok())
        .map(|i| i.path())
        .filter(|p| {
            p.is_file()
                && p.extension()
                    .is_some_and(|x| x.eq_ignore_ascii_case("dll"))
        })
        .collect();
    let componentes = componentes()?;
    for comp in &componentes {
        if !dlls_origem
            .iter()
            .any(|p| p.file_name().is_some_and(|n| n.eq_ignore_ascii_case(&comp.file)))
        {
            return Err(format!(
                "A DLL obrigatória {} não existe na pasta do reNut.",
                comp.file
            ));
        }
    }
    let total = 1 + dlls_origem.len() + componentes.len();
    let mut feito = 0;

    if cancelar.load(Ordering::Relaxed) {
        return Err("Instalação cancelada.".into());
    }
    progresso(feito, total, "Traduzindo o executável");
    let exe_sha = aplicar_executavel(&origem_dir.join("renut.exe"), &temp_dir.join(NOME_EXE_TRADUZIDO))?;
    feito += 1;

    let mut copiadas = Vec::new();
    for dll in &dlls_origem {
        if cancelar.load(Ordering::Relaxed) {
            return Err("Instalação cancelada.".into());
        }
        let nome = dll
            .file_name()
            .ok_or("Nome de DLL inválido.")?
            .to_string_lossy()
            .to_string();
        progresso(feito, total, &format!("Copiando {nome}"));
        copiar_arquivo(dll, &temp_dir.join(&nome))?;
        copiadas.push(nome);
        feito += 1;
    }

    let mut dlls = Vec::new();
    for comp in &componentes {
        if cancelar.load(Ordering::Relaxed) {
            return Err("Instalação cancelada.".into());
        }
        progresso(feito, total, &format!("Traduzindo {}", comp.file));
        let nome_existente = copiadas
            .iter()
            .find(|n| n.eq_ignore_ascii_case(&comp.file))
            .ok_or_else(|| format!("{} não foi copiada.", comp.file))?;
        let destino = temp_dir.join(nome_existente);
        let sha = aplicar_dll(&origem_dir.join(nome_existente), &destino, comp)?;
        dlls.push((comp.file.clone(), sha));
        feito += 1;
    }

    // Conferência final de TODOS os componentes obrigatorios (nada de sucesso parcial).
    for comp in &componentes {
        let arquivo = temp_dir.join(&comp.file);
        let sha = sha256_arquivo(&arquivo)?;
        if sha != comp.output_sha256 {
            return Err(format!(
                "Verificação final: {} não está traduzida. A instalação foi cancelada.",
                comp.file
            ));
        }
    }
    let exe_final = temp_dir.join(NOME_EXE_TRADUZIDO);
    let m = manifesto()?;
    if sha256_arquivo(&exe_final)? != m.output_sha256 {
        return Err("Verificação final: o executável traduzido não confere.".into());
    }

    let mut arquivos: Vec<String> = vec![NOME_EXE_TRADUZIDO.to_string()];
    arquivos.extend(copiadas.iter().cloned());
    let mut bytes = fs::metadata(&exe_final).map(|m| m.len()).unwrap_or(0);
    bytes += dlls_origem
        .iter()
        .filter_map(|p| fs::metadata(p).ok())
        .map(|m| m.len())
        .sum::<u64>();

    if origem_dir.join("lua_api").is_dir() {
        progresso(feito, total, "Copiando lua_api");
        let extras = copiar_pasta(&origem_dir.join("lua_api"), &temp_dir.join("lua_api"), 0)?;
        for e in extras {
            if let Ok(rel) = Path::new(&e).strip_prefix(temp_dir) {
                arquivos.push(rel.to_string_lossy().replace('\\', "/"));
            }
        }
    }
    for nome in ["version.txt", "installed_release.txt", "installed-build.txt"] {
        let origem = origem_dir.join(nome);
        if origem.is_file() {
            copiar_arquivo(&origem, &temp_dir.join(nome))?;
            arquivos.push(nome.to_string());
        }
    }

    Ok(ResumoRuntime {
        exe_sha,
        dlls,
        arquivos,
        bytes,
    })
}

/// Remove o runtime traduzido somente quando todos os arquivos conferem com os hashes esperados.
pub fn remover_runtime(pasta: &Path, arquivos_esperados: &[(String, String)]) -> Result<Vec<String>, String> {
    let mut removidos = Vec::new();
    let mut desconhecidos = Vec::new();
    for (rel, sha) in arquivos_esperados {
        let caminho = pasta.join(rel);
        if !caminho.is_file() {
            continue;
        }
        let atual = sha256_arquivo(&caminho)?;
        if &atual == sha {
            fs::remove_file(&caminho).map_err(|e| format!("Não removi {}: {e}", caminho.display()))?;
            removidos.push(rel.clone());
        } else {
            desconhecidos.push(rel.clone());
        }
    }
    // Nunca apaga recursivamente: só remove pastas que ficaram vazias.
    let mut dirs: Vec<PathBuf> = Vec::new();
    if pasta.is_dir() {
        for item in walkdir_simples(pasta) {
            dirs.push(item);
        }
    }
    dirs.sort_by_key(|p| std::cmp::Reverse(p.components().count()));
    for d in dirs {
        let _ = fs::remove_dir(d);
    }
    let _ = fs::remove_dir(pasta);
    if !desconhecidos.is_empty() {
        return Err(format!(
            "Alguns arquivos não foram removidos porque mudaram depois da instalação: {}",
            desconhecidos.join(", ")
        ));
    }
    Ok(removidos)
}

fn walkdir_simples(raiz: &Path) -> Vec<PathBuf> {
    let mut out = Vec::new();
    let Ok(itens) = fs::read_dir(raiz) else {
        return out;
    };
    for item in itens.flatten() {
        let p = item.path();
        if p.is_dir() {
            out.push(p.clone());
            out.extend(walkdir_simples(&p));
        }
    }
    out
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::time::{SystemTime, UNIX_EPOCH};

    fn scratch() -> PathBuf {
        let n = SystemTime::now().duration_since(UNIX_EPOCH).unwrap().as_nanos();
        let d = std::env::temp_dir().join(format!("instalador-renut-teste-{n}"));
        fs::create_dir_all(&d).unwrap();
        d
    }

    #[test]
    fn manifesto_e_componentes_embutidos() {
        let m = manifesto().unwrap();
        assert_eq!(m.version, "0.11.21");
        assert_eq!(m.output_sha256.len(), 64);
        let c = componentes().unwrap();
        assert_eq!(c.len(), 2);
        assert!(c.iter().any(|x| x.file == "rexui.dll"));
        assert!(c.iter().any(|x| x.file == "rexhid.dll"));
        // Nenhum patch binario embutido: so o manifesto e o catalogo publico.
        assert!(!include_str!("patch.rs").contains(concat!("renut_launcher_ptbr", ".patch\")")));
    }

    #[test]
    fn recusa_executavel_desconhecido() {
        let d = scratch();
        let falso = d.join("renut.exe");
        fs::write(&falso, b"nao e o renut").unwrap();
        assert!(verificar_executavel(&falso).is_err());
        let _ = fs::remove_dir_all(&d);
    }

}