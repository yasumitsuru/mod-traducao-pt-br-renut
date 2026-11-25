//! Consultas ao sistema operacional (espaco livre) sem dependencias pesadas.

use std::path::Path;

#[cfg(windows)]
pub fn espaco_livre(pasta: &Path) -> Option<u64> {
    use std::os::windows::ffi::OsStrExt;
    let wide: Vec<u16> = pasta
        .as_os_str()
        .encode_wide()
        .chain(std::iter::once(0))
        .collect();
    let mut livre: u64 = 0;
    let ok = unsafe {
        windows_sys::Win32::Storage::FileSystem::GetDiskFreeSpaceExW(
            wide.as_ptr(),
            &mut livre,
            std::ptr::null_mut(),
            std::ptr::null_mut(),
        )
    };
    if ok != 0 { Some(livre) } else { None }
}

#[cfg(not(windows))]
pub fn espaco_livre(_pasta: &Path) -> Option<u64> {
    None
}

#[cfg(windows)]
pub fn area_de_trabalho_do_windows() -> Option<std::path::PathBuf> {
    use windows_sys::Win32::System::Com::CoTaskMemFree;
    use windows_sys::Win32::UI::Shell::{FOLDERID_Desktop, SHGetKnownFolderPath};
    let mut ponteiro: *mut u16 = std::ptr::null_mut();
    let ok = unsafe {
        SHGetKnownFolderPath(
            &FOLDERID_Desktop,
            0,
            std::ptr::null_mut(),
            &mut ponteiro,
        )
    };
    if ok != 0 || ponteiro.is_null() {
        return None;
    }
    let mut tamanho = 0usize;
    unsafe {
        while *ponteiro.add(tamanho) != 0 {
            tamanho += 1;
        }
    }
    let fatia = unsafe { std::slice::from_raw_parts(ponteiro, tamanho) };
    let caminho = std::path::PathBuf::from(String::from_utf16_lossy(fatia));
    unsafe { CoTaskMemFree(ponteiro as *const core::ffi::c_void) };
    Some(caminho)
}

#[cfg(not(windows))]
pub fn area_de_trabalho_do_windows() -> Option<std::path::PathBuf> {
    None
}

/// Remove o prefixo verbatim (`\\?\`) que `canonicalize` adiciona no Windows. O prefixo nao pode
/// ir para o `renut.toml`, para o atalho nem para o manifesto.
pub fn limpar_prefixo(p: &Path) -> std::path::PathBuf {
    let s = p.to_string_lossy();
    if let Some(resto) = s.strip_prefix(r"\\?\UNC\") {
        return std::path::PathBuf::from(format!(r"\\{resto}"));
    }
    if let Some(resto) = s.strip_prefix(r"\\?\") {
        return std::path::PathBuf::from(resto.to_string());
    }
    p.to_path_buf()
}

pub fn milhar(n: usize) -> String {
    let texto = n.to_string();
    let mut saida = String::new();
    for (i, c) in texto.chars().enumerate() {
        if i > 0 && (texto.len() - i) % 3 == 0 {
            saida.push('.');
        }
        saida.push(c);
    }
    saida
}

pub fn formatar_bytes(bytes: u64) -> String {
    const UNIDADES: [&str; 5] = ["B", "KB", "MB", "GB", "TB"];
    let mut valor = bytes as f64;
    let mut i = 0;
    while valor >= 1024.0 && i + 1 < UNIDADES.len() {
        valor /= 1024.0;
        i += 1;
    }
    if i == 0 {
        format!("{bytes} B")
    } else {
        format!("{valor:.1} {}", UNIDADES[i])
    }
}