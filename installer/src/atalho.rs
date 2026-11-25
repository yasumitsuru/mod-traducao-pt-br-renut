//! Atalho `.lnk` na area de trabalho real do usuario.
//!
//! Usa o proprio Windows (WScript.Shell via PowerShell embutido no sistema) para resolver a
//! area de trabalho mesmo quando ela esta redirecionada (OneDrive, politica de grupo) e para
//! gravar o atalho com icone do executavel escolhido. Nada e baixado.

use std::path::{Path, PathBuf};
use std::process::Command;

pub const NOME_ATALHO: &str = "Banjo-Kazooie Nuts & Bolts — PT-BR.lnk";

fn base64_utf16(texto: &str) -> String {
    let mut bytes = Vec::with_capacity(texto.len() * 2);
    for u in texto.encode_utf16() {
        bytes.extend_from_slice(&u.to_le_bytes());
    }
    const ALFABETO: &[u8] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    let mut out = String::new();
    for grupo in bytes.chunks(3) {
        let b = [grupo[0], *grupo.get(1).unwrap_or(&0), *grupo.get(2).unwrap_or(&0)];
        let n = (u32::from(b[0]) << 16) | (u32::from(b[1]) << 8) | u32::from(b[2]);
        out.push(ALFABETO[(n >> 18) as usize & 63] as char);
        out.push(ALFABETO[(n >> 12) as usize & 63] as char);
        out.push(if grupo.len() > 1 {
            ALFABETO[(n >> 6) as usize & 63] as char
        } else {
            '='
        });
        out.push(if grupo.len() > 2 {
            ALFABETO[n as usize & 63] as char
        } else {
            '='
        });
    }
    out
}

fn ps_aspas(s: &str) -> String {
    format!("'{}'", s.replace('\'', "''"))
}

fn executar(script: &str) -> Result<String, String> {
    let codificado = base64_utf16(script);
    let mut cmd = Command::new("powershell.exe");
    cmd.args([
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-EncodedCommand",
        &codificado,
    ]);
    #[cfg(windows)]
    {
        use std::os::windows::process::CommandExt;
        cmd.creation_flags(0x0800_0000); // CREATE_NO_WINDOW
    }
    let saida = cmd
        .output()
        .map_err(|e| format!("Não consegui falar com o Windows para criar o atalho: {e}"))?;
    if !saida.status.success() {
        let erro = String::from_utf8_lossy(&saida.stderr);
        return Err(format!(
            "O Windows recusou a criacao do atalho: {}",
            erro.trim()
        ));
    }
    Ok(String::from_utf8_lossy(&saida.stdout).trim().to_string())
}

/// Caminho da area de trabalho do usuario atual, resolvido pelo Windows.
pub fn area_de_trabalho() -> Result<PathBuf, String> {
    // Override usado apenas pelos testes automatizados; nunca e definido na instalacao normal.
    if let Ok(dir) = std::env::var("PTBR_INSTALADOR_ATALHO_DIR") {
        let p = PathBuf::from(dir);
        if p.is_dir() {
            return Ok(p);
        }
    }
    let script = "$ErrorActionPreference='Stop'\n\
        $w = New-Object -ComObject WScript.Shell\n\
        $d = $w.SpecialFolders.Item('Desktop')\n\
        if (-not $d) { $d = [Environment]::GetFolderPath('Desktop') }\n\
        Write-Output $d\n";
    let saida = if let Some(p) = crate::sistema::area_de_trabalho_do_windows() {
        p.to_string_lossy().to_string()
    } else {
        executar(script)?
    };
    let caminho = PathBuf::from(saida.trim());
    if !caminho.is_dir() {
        return Err(format!(
            "A área de trabalho do usuário não foi encontrada ({}).",
            caminho.display()
        ));
    }
    Ok(caminho)
}

pub fn caminho_padrao() -> Result<PathBuf, String> {
    Ok(area_de_trabalho()?.join(NOME_ATALHO))
}

/// Cria (ou atualiza) o atalho do instalador. Devolve o caminho do `.lnk`.
pub fn criar(alvo: &Path, trabalho: &Path, descricao: &str) -> Result<PathBuf, String> {
    criar_em(&caminho_padrao()?, alvo, trabalho, descricao)
}

/// Igual a `criar`, mas numa pasta escolhida (usado pelos testes automatizados).
pub fn criar_em(
    destino: &Path,
    alvo: &Path,
    trabalho: &Path,
    descricao: &str,
) -> Result<PathBuf, String> {
    if !alvo.is_file() {
        return Err(format!("O executável do atalho não existe: {}", alvo.display()));
    }
    if let Some(pai) = destino.parent() {
        std::fs::create_dir_all(pai).map_err(|e| format!("Não criei {}: {e}", pai.display()))?;
    }
    let destino = destino.to_path_buf();
    let script = format!(
        "$ErrorActionPreference='Stop'\n\
         $w = New-Object -ComObject WScript.Shell\n\
         $s = $w.CreateShortcut({})\n\
         $s.TargetPath = {}\n\
         $s.WorkingDirectory = {}\n\
         $s.IconLocation = {}\n\
         $s.Description = {}\n\
         $s.Save()\n\
         Write-Output 'OK'\n",
        ps_aspas(&destino.to_string_lossy()),
        ps_aspas(&alvo.to_string_lossy()),
        ps_aspas(&trabalho.to_string_lossy()),
        ps_aspas(&format!("{},0", alvo.to_string_lossy())),
        ps_aspas(descricao),
    );
    let saida = executar(&script)?;
    if !destino.is_file() {
        return Err(format!(
            "O Windows não gravou o atalho esperado ({}).",
            destino.display()
        ));
    }
    if !saida.contains("OK") {
        return Err("O Windows não confirmou a criacao do atalho.".into());
    }
    Ok(destino)
}

/// Le o destino de um `.lnk` (para conferir o que foi criado).
pub fn destino_do_atalho(lnk: &Path) -> Result<PathBuf, String> {
    let script = format!(
        "$ErrorActionPreference='Stop'\n\
         $w = New-Object -ComObject WScript.Shell\n\
         $s = $w.CreateShortcut({})\n\
         Write-Output $s.TargetPath\n",
        ps_aspas(&lnk.to_string_lossy())
    );
    let saida = executar(&script)?;
    Ok(PathBuf::from(saida.trim()))
}

pub fn remover(lnk: &Path) -> Result<(), String> {
    if !lnk.exists() {
        return Ok(());
    }
    let script = format!(
        "$ErrorActionPreference='Stop'\n\
         Remove-Item -LiteralPath {} -Force\n\
         Write-Output 'OK'\n",
        ps_aspas(&lnk.to_string_lossy())
    );
    executar(&script)?;
    if lnk.exists() {
        return Err(format!("Não consegui remover o atalho {}.", lnk.display()));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn base64_utf16_com_acentos() {
        let s = base64_utf16("Ação");
        assert!(!s.is_empty());
        assert!(s.ends_with('='));
    }

    #[test]
    fn nome_do_atalho_e_o_pedido() {
        assert_eq!(NOME_ATALHO, "Banjo-Kazooie Nuts & Bolts — PT-BR.lnk");
    }
}