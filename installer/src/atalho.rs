//! Atalho `.lnk` na área de trabalho real do usuário.
//!
//! A área de trabalho vem do próprio Windows (`SHGetKnownFolderPath`), que já considera o
//! redirecionamento pelo OneDrive ou por política de grupo. O atalho é gravado pela interface
//! nativa do Windows (`IShellLinkW` + `IPersistFile`), em Unicode: funciona com qualquer caractere
//! no caminho (acentos, `ñ`, japonês...) e não abre nenhum outro programa. Nada é baixado.

use std::path::{Path, PathBuf};

pub const NOME_ATALHO: &str = "Banjo-Kazooie Nuts & Bolts — PT-BR.lnk";

/// Caminho da área de trabalho do usuário atual, resolvido pelo Windows.
pub fn area_de_trabalho() -> Result<PathBuf, String> {
    // Usado apenas pelos testes automatizados; nunca é definido na instalação normal.
    if let Ok(dir) = std::env::var("PTBR_INSTALADOR_ATALHO_DIR") {
        let p = PathBuf::from(dir);
        if p.is_dir() {
            return Ok(p);
        }
    }
    let Some(caminho) = crate::sistema::area_de_trabalho_do_windows() else {
        return Err("O Windows não informou a pasta da área de trabalho.".into());
    };
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
    com::gravar(destino, alvo, trabalho, descricao)
        .map_err(|e| format!("O Windows recusou a criação do atalho ({e})."))?;
    if !destino.is_file() {
        return Err(format!(
            "O Windows não gravou o atalho esperado ({}).",
            destino.display()
        ));
    }
    Ok(destino.to_path_buf())
}

/// Lê o destino de um `.lnk` (para conferir o que foi criado).
pub fn destino_do_atalho(lnk: &Path) -> Result<PathBuf, String> {
    com::ler_alvo(lnk).map_err(|e| format!("Não consegui ler o atalho {} ({e}).", lnk.display()))
}

pub fn remover(lnk: &Path) -> Result<(), String> {
    if !lnk.exists() {
        return Ok(());
    }
    std::fs::remove_file(lnk)
        .map_err(|e| format!("Não consegui remover o atalho {}: {e}", lnk.display()))?;
    if lnk.exists() {
        return Err(format!("Não consegui remover o atalho {}.", lnk.display()));
    }
    Ok(())
}

#[cfg(windows)]
mod com {
    //! Chamadas COM mínimas para `IShellLinkW` e `IPersistFile`. Só as entradas usadas das
    //! tabelas virtuais têm tipo; as demais ocupam a posição com um ponteiro.

    use std::ffi::c_void;
    use std::os::windows::ffi::OsStrExt;
    use std::path::{Path, PathBuf};

    use windows_sys::core::{GUID, HRESULT};
    use windows_sys::Win32::System::Com::{
        CoCreateInstance, CoInitializeEx, CoUninitialize, CLSCTX_INPROC_SERVER,
        COINIT_APARTMENTTHREADED,
    };
    use windows_sys::Win32::UI::Shell::ShellLink;

    const IID_ISHELLLINKW: GUID = GUID::from_u128(0x000214f9_0000_0000_c000_000000000046);
    const IID_IPERSISTFILE: GUID = GUID::from_u128(0x0000010b_0000_0000_c000_000000000046);
    /// O apartamento COM desta thread já existia com outro modelo: dá para usar, sem encerrar.
    const RPC_E_CHANGED_MODE: HRESULT = 0x8001_0106_u32 as HRESULT;
    const STGM_READ: u32 = 0;
    /// `SLGP_RAWPATH`: o caminho como foi gravado, sem expandir variáveis.
    const SLGP_RAWPATH: u32 = 4;

    type Fn0 = usize;

    #[repr(C)]
    struct IUnknownVtbl {
        query_interface:
            unsafe extern "system" fn(*mut c_void, *const GUID, *mut *mut c_void) -> HRESULT,
        add_ref: Fn0,
        release: unsafe extern "system" fn(*mut c_void) -> u32,
    }

    #[repr(C)]
    struct IShellLinkWVtbl {
        base: IUnknownVtbl,
        get_path: unsafe extern "system" fn(*mut c_void, *mut u16, i32, *mut c_void, u32) -> HRESULT,
        get_id_list: Fn0,
        set_id_list: Fn0,
        get_description: Fn0,
        set_description: unsafe extern "system" fn(*mut c_void, *const u16) -> HRESULT,
        get_working_directory: Fn0,
        set_working_directory: unsafe extern "system" fn(*mut c_void, *const u16) -> HRESULT,
        get_arguments: Fn0,
        set_arguments: Fn0,
        get_hotkey: Fn0,
        set_hotkey: Fn0,
        get_show_cmd: Fn0,
        set_show_cmd: Fn0,
        get_icon_location: Fn0,
        set_icon_location: unsafe extern "system" fn(*mut c_void, *const u16, i32) -> HRESULT,
        set_relative_path: Fn0,
        resolve: Fn0,
        set_path: unsafe extern "system" fn(*mut c_void, *const u16) -> HRESULT,
    }

    #[repr(C)]
    struct IPersistFileVtbl {
        base: IUnknownVtbl,
        get_class_id: Fn0,
        is_dirty: Fn0,
        load: unsafe extern "system" fn(*mut c_void, *const u16, u32) -> HRESULT,
        save: unsafe extern "system" fn(*mut c_void, *const u16, i32) -> HRESULT,
        save_completed: Fn0,
        get_cur_file: Fn0,
    }

    /// Um objeto COM com a tabela `V`; libera a referência ao sair do escopo.
    struct Objeto<V> {
        ptr: *mut c_void,
        _v: std::marker::PhantomData<V>,
    }

    impl<V> Objeto<V> {
        fn vt(&self) -> &V {
            unsafe { &**(self.ptr as *mut *const V) }
        }
    }

    impl<V> Drop for Objeto<V> {
        fn drop(&mut self) {
            unsafe {
                let base = &**(self.ptr as *mut *const IUnknownVtbl);
                (base.release)(self.ptr);
            }
        }
    }

    /// Inicializa o COM nesta thread e o encerra no fim, quando fomos nós que inicializamos.
    struct Apartamento(bool);

    impl Apartamento {
        fn abrir() -> Result<Self, String> {
            let hr = unsafe { CoInitializeEx(std::ptr::null(), COINIT_APARTMENTTHREADED as u32) };
            if hr >= 0 {
                Ok(Self(true))
            } else if hr == RPC_E_CHANGED_MODE {
                Ok(Self(false))
            } else {
                Err(format!("CoInitializeEx 0x{:08X}", hr as u32))
            }
        }
    }

    impl Drop for Apartamento {
        fn drop(&mut self) {
            if self.0 {
                unsafe { CoUninitialize() };
            }
        }
    }

    fn largo(s: &std::ffi::OsStr) -> Vec<u16> {
        s.encode_wide().chain(std::iter::once(0)).collect()
    }

    fn conferir(hr: HRESULT, etapa: &str) -> Result<(), String> {
        if hr >= 0 {
            Ok(())
        } else {
            Err(format!("{etapa} 0x{:08X}", hr as u32))
        }
    }

    fn link() -> Result<(Objeto<IShellLinkWVtbl>, Objeto<IPersistFileVtbl>), String> {
        let mut p: *mut c_void = std::ptr::null_mut();
        let hr = unsafe {
            CoCreateInstance(&ShellLink, std::ptr::null_mut(), CLSCTX_INPROC_SERVER, &IID_ISHELLLINKW, &mut p)
        };
        conferir(hr, "CoCreateInstance")?;
        let link = Objeto::<IShellLinkWVtbl> { ptr: p, _v: std::marker::PhantomData };
        let mut q: *mut c_void = std::ptr::null_mut();
        let hr = unsafe { (link.vt().base.query_interface)(link.ptr, &IID_IPERSISTFILE, &mut q) };
        conferir(hr, "IPersistFile")?;
        let arquivo = Objeto::<IPersistFileVtbl> { ptr: q, _v: std::marker::PhantomData };
        Ok((link, arquivo))
    }

    pub fn gravar(destino: &Path, alvo: &Path, trabalho: &Path, descricao: &str) -> Result<(), String> {
        let _com = Apartamento::abrir()?;
        let (link, arquivo) = link()?;
        let alvo_w = largo(alvo.as_os_str());
        let trabalho_w = largo(trabalho.as_os_str());
        let descricao_w = largo(std::ffi::OsStr::new(descricao));
        let destino_w = largo(destino.as_os_str());
        unsafe {
            let vt = link.vt();
            conferir((vt.set_path)(link.ptr, alvo_w.as_ptr()), "SetPath")?;
            conferir((vt.set_working_directory)(link.ptr, trabalho_w.as_ptr()), "SetWorkingDirectory")?;
            conferir((vt.set_icon_location)(link.ptr, alvo_w.as_ptr(), 0), "SetIconLocation")?;
            conferir((vt.set_description)(link.ptr, descricao_w.as_ptr()), "SetDescription")?;
            conferir((arquivo.vt().save)(arquivo.ptr, destino_w.as_ptr(), 1), "Save")?;
        }
        Ok(())
    }

    pub fn ler_alvo(lnk: &Path) -> Result<PathBuf, String> {
        let _com = Apartamento::abrir()?;
        let (link, arquivo) = link()?;
        let lnk_w = largo(lnk.as_os_str());
        let mut buf = vec![0u16; 32768];
        unsafe {
            conferir((arquivo.vt().load)(arquivo.ptr, lnk_w.as_ptr(), STGM_READ), "Load")?;
            conferir(
                (link.vt().get_path)(link.ptr, buf.as_mut_ptr(), buf.len() as i32, std::ptr::null_mut(), SLGP_RAWPATH),
                "GetPath",
            )?;
        }
        let fim = buf.iter().position(|&c| c == 0).unwrap_or(buf.len());
        Ok(PathBuf::from(String::from_utf16_lossy(&buf[..fim])))
    }
}

#[cfg(not(windows))]
mod com {
    use std::path::{Path, PathBuf};

    pub fn gravar(_: &Path, _: &Path, _: &Path, _: &str) -> Result<(), String> {
        Err("atalhos .lnk só existem no Windows".into())
    }

    pub fn ler_alvo(_: &Path) -> Result<PathBuf, String> {
        Err("atalhos .lnk só existem no Windows".into())
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn nome_do_atalho_e_o_pedido() {
        assert_eq!(NOME_ATALHO, "Banjo-Kazooie Nuts & Bolts — PT-BR.lnk");
    }

    #[cfg(windows)]
    #[test]
    fn atalho_com_caracteres_fora_do_latim() {
        let base = std::env::temp_dir().join(format!("atalho-unicode-Ação-日本語-{}", std::process::id()));
        let _ = std::fs::remove_dir_all(&base);
        let alvo = base.join("reNut ñ 日本語").join("launcher-ptbr").join("renut.ptbr.exe");
        std::fs::create_dir_all(alvo.parent().unwrap()).unwrap();
        std::fs::write(&alvo, b"exe").unwrap();
        let lnk = base.join("área de trabalho").join(NOME_ATALHO);
        criar_em(&lnk, &alvo, alvo.parent().unwrap(), "Banjo-Kazooie: Nuts & Bolts em português do Brasil")
            .unwrap();
        assert_eq!(destino_do_atalho(&lnk).unwrap(), alvo);
        // Gravar de novo atualiza o mesmo atalho.
        criar_em(&lnk, &alvo, alvo.parent().unwrap(), "outra descrição").unwrap();
        assert_eq!(destino_do_atalho(&lnk).unwrap(), alvo);
        remover(&lnk).unwrap();
        assert!(!lnk.exists());
        let _ = std::fs::remove_dir_all(&base);
    }
}
