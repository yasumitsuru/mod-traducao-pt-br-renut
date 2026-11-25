//! Confere a geracao LOCAL dos patches do launcher contra a copia real do reNut, quando
//! RENUT_ROOT aponta para a pasta da versao suportada (big-lua-energy 0.11.21).

use std::path::PathBuf;

use instalador_renut_ptbr::{gerador_launcher, patch, sha256::sha256_hex};

#[test]
fn gera_o_launcher_e_as_dlls_byte_a_byte() {
    let Ok(raiz) = std::env::var("RENUT_ROOT") else {
        eprintln!("RENUT_ROOT nao definido: teste real ignorado");
        return;
    };
    let raiz = PathBuf::from(raiz);
    let m = patch::manifesto().unwrap();
    let exe = std::fs::read(raiz.join("renut.exe")).unwrap();
    assert_eq!(sha256_hex(&exe), m.input_sha256, "renut.exe de outra versao");
    let t = std::time::Instant::now();
    let out = gerador_launcher::gerar_executavel(&exe).unwrap();
    eprintln!("renut.exe gerado em {:?}", t.elapsed());
    assert_eq!(out.len() as u64, m.output_size);
    assert_eq!(sha256_hex(&out), m.output_sha256);
    for c in patch::componentes().unwrap() {
        let d = std::fs::read(raiz.join(&c.file)).unwrap();
        assert_eq!(sha256_hex(&d), c.input_sha256, "{} de outra versao", c.file);
        let o = gerador_launcher::gerar_dll(&c.file, &d).unwrap();
        assert_eq!(sha256_hex(&o), c.output_sha256, "{}", c.file);
    }
}
