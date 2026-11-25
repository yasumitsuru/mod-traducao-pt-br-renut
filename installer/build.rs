//! Junta os catalogos versionados de `data/traducao` num unico JSON embutido no executavel.
//!
//! O instalador nao distribui texto do jogo: so as frases traduzidas pelo projeto. Os textos
//! originais continuam sendo lidos da instalacao legitima do usuario em tempo de instalacao.

use std::env;
use std::fs;
use std::path::{Path, PathBuf};

fn main() {
    let raiz = PathBuf::from(env::var("CARGO_MANIFEST_DIR").unwrap())
        .parent()
        .expect("installer/ precisa estar dentro do projeto")
        .to_path_buf();
    let pasta = raiz.join("data").join("traducao");
    println!("cargo:rerun-if-changed={}", pasta.display());
    println!("cargo:rerun-if-changed=build.rs");

    let mut arquivos: Vec<PathBuf> = fs::read_dir(&pasta)
        .unwrap_or_else(|e| panic!("nao li {}: {e}", pasta.display()))
        .filter_map(|e| e.ok().map(|e| e.path()))
        .filter(|p| p.extension().is_some_and(|x| x == "json"))
        .collect();
    arquivos.sort();

    let mut saida = String::from("[\n");
    for (i, caminho) in arquivos.iter().enumerate() {
        println!("cargo:rerun-if-changed={}", caminho.display());
        let texto = fs::read_to_string(caminho)
            .unwrap_or_else(|e| panic!("nao li {}: {e}", caminho.display()));
        if i > 0 {
            saida.push_str(",\n");
        }
        saida.push_str(texto.trim());
    }
    saida.push_str("\n]\n");

    // Valida antes de gravar: um JSON quebrado falha no build, nao na maquina do usuario.
    let _: serde_json::Value = serde_json::from_str(&saida).expect("data/traducao invalido");
    let destino = Path::new(&env::var("OUT_DIR").unwrap()).join("traducao.json");
    fs::write(&destino, saida).expect("nao gravei o catalogo embutido");

    println!("cargo:rustc-env=PTBR_TRADUCAO_ARQUIVOS={}", arquivos.len());
}