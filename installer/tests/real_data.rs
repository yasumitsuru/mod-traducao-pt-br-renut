//! Confere o porte Rust contra a copia real do jogo, quando RENUT_GAME aponta para ela.
//! Sem a variavel, o teste nao roda (as maquinas de desenvolvimento/CI nao tem o jogo).

use std::path::PathBuf;

#[test]
fn gera_o_pacote_atual_byte_a_byte() {
    let Ok(jogo) = std::env::var("RENUT_GAME") else {
        eprintln!("RENUT_GAME nao definido: teste real ignorado");
        return;
    };
    let catalogo = instalador_renut_ptbr::traducao::carregar().unwrap();
    let gerado = instalador_renut_ptbr::modpack::gerar(&PathBuf::from(jogo), &catalogo, |_, _| {})
        .expect("o pacote deveria ser gerado");
    assert_eq!(gerado.arquivos, 107);
    assert_eq!(gerado.frases, 6099, "frases aplicadas");
    assert!(gerado.sha_confere, "SHA obtido: {}", gerado.sha256);
    assert_eq!(gerado.sha256, instalador_renut_ptbr::modpack::SHA_ESPERADO);
    assert_eq!(gerado.nbpatch.len(), 1_145_999);
    if let Ok(saida) = std::env::var("RENUT_SAIDA") {
        std::fs::write(saida, &gerado.nbpatch).expect("gravar o pacote para comparar");
    }
}