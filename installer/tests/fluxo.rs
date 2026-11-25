//! Fluxo completo do instalador com uma copia SINTETICA do jogo (nada do jogo real).
//!
//! Cobre: deteccao, instalacao do mod, idempotencia, recusa de pasta estranha, cancelamento,
//! remocao e criacao real de atalho `.lnk` numa pasta temporaria.

use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::AtomicBool;

use instalador_renut_ptbr::detect;
use instalador_renut_ptbr::fixtures;
use instalador_renut_ptbr::manifesto::Manifesto;
use instalador_renut_ptbr::modpack;
use instalador_renut_ptbr::plano::{self, Opcoes, Remocao};
use instalador_renut_ptbr::sha256::hash_texto;
use instalador_renut_ptbr::traducao::{ArquivoTrad, FraseTrad};

fn nomes() -> Vec<String> {
    (0..107u32)
        .map(|i| format!("{:08x}", 0x1100_0000 + i))
        .collect()
}

fn catalogo() -> Vec<ArquivoTrad> {
    let h = hash_texto("Hola");
    nomes()
        .into_iter()
        .map(|arquivo| ArquivoTrad {
            arquivo,
            asset: "aid_loctext_teste".into(),
            frases: vec![FraseTrad {
                id: "1000".into(),
                chave: "saudacao".into(),
                hash_es: Some(h.clone()),
                texto_ptbr: "Ola, mundo!".into(),
            }],
        })
        .collect()
}

fn criar_jogo(raiz: &Path) {
    fs::create_dir_all(raiz.join("game").join("extraido")).unwrap();
    fs::create_dir_all(raiz.join("mods")).unwrap();
    fs::write(raiz.join("renut.exe"), b"executavel sintetico de teste").unwrap();
    fs::write(raiz.join("version.txt"), b"big-lua-energy\n").unwrap();
    let mapa: HashMap<String, Vec<(String, String, String)>> = nomes()
        .into_iter()
        .map(|n| {
            (
                n,
                vec![("saudacao".to_string(), "Hello".to_string(), "Hola".to_string())],
            )
        })
        .collect();
    fixtures::jogo_sintetico(
        &raiz.join("game").join("extraido"),
        &nomes(),
        &mapa,
    );
}

fn opcoes(mod_jogo: bool) -> Opcoes {
    Opcoes {
        mod_jogo,
        launcher: false,
        atalho: false,
    }
}

#[test]
fn instala_reinstala_e_remove_o_mod() {
    let tmp = tempfile::tempdir().unwrap();
    let raiz = tmp.path().join("reNut com espaços ç");
    criar_jogo(&raiz);
    let cat = catalogo();
    let jogo = raiz.join("game").join("extraido");
    let gerado = modpack::gerar(&jogo, &cat, |_, _| {}).unwrap();
    assert_eq!(gerado.arquivos, 107);
    assert_eq!(gerado.frases, 107);
    let sha = gerado.sha256.clone();

    let original_sha = instalador_renut_ptbr::sha256::sha256_hex(
        &fs::read(jogo.join("Debug").join("11").join("00").join("00").join("00")).unwrap(),
    );

    let d = detect::analisar(&raiz, &cat);
    assert!(d.jogo_ok, "{}", d.jogo_detalhe);
    assert!(d.pode_instalar_mod());

    let mut eventos = Vec::new();
    let r = plano::instalar_com(&d, &opcoes(true), &AtomicBool::new(false), &mut |e| {
        eventos.push(format!("{e:?}"))
    }, &cat, &sha)
    .unwrap();
    assert!(r.mod_ok);
    let pasta = raiz.join("mods").join("ptbr_traducao");
    assert_eq!(
        instalador_renut_ptbr::patch::sha256_arquivo(&pasta.join("ptbr_traducao.nbpatch")).unwrap(),
        sha
    );
    assert!(pasta.join("mod.toml").is_file());
    assert!(plano::mod_habilitado(&raiz.join("mods").join("mods.json")));
    assert!(Manifesto::carregar(&raiz).is_some());
    assert!(!eventos.is_empty());

    // Reexecutar nao duplica nem corrompe.
    let d2 = detect::analisar(&raiz, &cat);
    let r2 = plano::instalar_com(&d2, &opcoes(true), &AtomicBool::new(false), &mut |_| {}, &cat, &sha)
        .unwrap();
    assert!(r2.mod_ok);
    assert_eq!(
        instalador_renut_ptbr::patch::sha256_arquivo(&pasta.join("ptbr_traducao.nbpatch")).unwrap(),
        sha
    );

    // Remover preserva o jogo e os outros mods.
    fs::write(raiz.join("mods").join("outro_mod.txt"), b"nao mexa").unwrap();
    let d3 = detect::analisar(&raiz, &cat);
    let mut e3 = |_e: plano::Evento| {};
    let ms = plano::remover(
        &d3,
        &Remocao {
            mod_jogo: true,
            launcher: false,
            atalho: false,
        },
        &mut e3,
    )
    .unwrap();
    assert!(ms.iter().any(|m| m.contains("removida")));
    assert!(!pasta.exists());
    assert!(raiz.join("mods").join("outro_mod.txt").is_file());
    assert!(!plano::mod_habilitado(&raiz.join("mods").join("mods.json")));
    assert!(Manifesto::carregar(&raiz).is_none());
    assert_eq!(
        instalador_renut_ptbr::sha256::sha256_hex(
            &fs::read(jogo.join("Debug").join("11").join("00").join("00").join("00")).unwrap()
        ),
        original_sha,
        "o arquivo do jogo nao pode mudar"
    );
    assert_eq!(
        fs::read(raiz.join("renut.exe")).unwrap(),
        b"executavel sintetico de teste"
    );
}

#[test]
fn recusa_pasta_de_mod_que_nao_e_nossa() {
    let tmp = tempfile::tempdir().unwrap();
    let raiz = tmp.path().join("reNut");
    criar_jogo(&raiz);
    let cat = catalogo();
    let gerado = modpack::gerar(&raiz.join("game").join("extraido"), &cat, |_, _| {}).unwrap();
    let pasta = raiz.join("mods").join("ptbr_traducao");
    fs::create_dir_all(&pasta).unwrap();
    fs::write(pasta.join("arquivo_estranho.txt"), b"nao apague").unwrap();

    let d = detect::analisar(&raiz, &cat);
    let erro = plano::instalar_com(
        &d,
        &opcoes(true),
        &AtomicBool::new(false),
        &mut |_| {},
        &cat,
        &gerado.sha256,
    )
    .unwrap_err();
    assert!(erro.contains("não foi criada por este instalador"), "{erro}");
    assert!(pasta.join("arquivo_estranho.txt").is_file());
    assert!(!Manifesto::carregar(&raiz).is_some());
}

#[test]
fn cancelamento_nao_deixa_arquivos() {
    let tmp = tempfile::tempdir().unwrap();
    let raiz = tmp.path().join("reNut");
    criar_jogo(&raiz);
    let cat = catalogo();
    let gerado = modpack::gerar(&raiz.join("game").join("extraido"), &cat, |_, _| {}).unwrap();
    let d = detect::analisar(&raiz, &cat);
    let cancelar = AtomicBool::new(true);
    let erro = plano::instalar_com(&d, &opcoes(true), &cancelar, &mut |_| {}, &cat, &gerado.sha256)
        .unwrap_err();
    assert!(erro.contains("cancelada"), "{erro}");
    assert!(!raiz.join("mods").join("ptbr_traducao").exists());
    assert!(!Manifesto::carregar(&raiz).is_some());
}

#[test]
fn pacote_com_hash_diferente_nao_instala() {
    let tmp = tempfile::tempdir().unwrap();
    let raiz = tmp.path().join("reNut");
    criar_jogo(&raiz);
    let cat = catalogo();
    let d = detect::analisar(&raiz, &cat);
    let erro = plano::instalar_com(
        &d,
        &opcoes(true),
        &AtomicBool::new(false),
        &mut |_| {},
        &cat,
        "0000000000000000000000000000000000000000000000000000000000000000",
    )
    .unwrap_err();
    assert!(erro.contains("não corresponde"), "{erro}");
    assert!(!raiz.join("mods").join("ptbr_traducao").exists());
}

#[test]
fn pasta_vazia_e_pasta_inexistente_nao_sao_instalacao() {
    let tmp = tempfile::tempdir().unwrap();
    let vazia = tmp.path().join("vazia");
    fs::create_dir_all(&vazia).unwrap();
    let cat = catalogo();
    let d = detect::analisar(&vazia, &cat);
    assert!(d.raiz_valida);
    assert!(d.renut_exe.is_none());
    assert!(!d.exe_compativel);
    assert!(d.problemas.iter().any(|p| p.contains("renut.exe")));

    let d2 = detect::analisar(&tmp.path().join("nao_existe"), &cat);
    assert!(!d2.raiz_valida);
    assert!(!d2.problemas.is_empty());
}

#[cfg(windows)]
#[test]
fn atalho_real_aponta_para_o_executavel() {
    let tmp = tempfile::tempdir().unwrap();
    let alvo = tmp.path().join("launcher").join("renut.ptbr.exe");
    fs::create_dir_all(alvo.parent().unwrap()).unwrap();
    fs::write(&alvo, b"exe").unwrap();
    let desktop = tmp.path().join("desktop");
    fs::create_dir_all(&desktop).unwrap();
    let lnk = desktop.join(instalador_renut_ptbr::atalho::NOME_ATALHO);

    instalador_renut_ptbr::atalho::criar_em(&lnk, &alvo, alvo.parent().unwrap(), "teste").unwrap();
    assert!(lnk.is_file());
    let lido = instalador_renut_ptbr::atalho::destino_do_atalho(&lnk).unwrap();
    assert_eq!(lido, alvo);
    instalador_renut_ptbr::atalho::remover(&lnk).unwrap();
    assert!(!lnk.exists());
}

#[test]
fn remover_runtime_nao_apaga_arquivo_alterado() {
    let tmp = tempfile::tempdir().unwrap();
    let pasta = tmp.path().join("launcher");
    fs::create_dir_all(&pasta).unwrap();
    let bom = pasta.join("a.dll");
    let alterado = pasta.join("b.dll");
    fs::write(&bom, b"igual").unwrap();
    fs::write(&alterado, b"mudou").unwrap();
    let esperados = vec![
        (
            "a.dll".to_string(),
            instalador_renut_ptbr::sha256::sha256_hex(b"igual"),
        ),
        (
            "b.dll".to_string(),
            instalador_renut_ptbr::sha256::sha256_hex(b"original"),
        ),
    ];
    let erro =
        instalador_renut_ptbr::patch::remover_runtime(&pasta, &esperados).unwrap_err();
    assert!(erro.contains("b.dll"));
    assert!(!bom.exists());
    assert!(alterado.is_file(), "arquivo alterado nao pode ser apagado");
}

#[test]
fn prefixo_verbatim_e_removido_do_caminho() {
    let p = PathBuf::from(r"\\?\C:\Games\reNut");
    assert_eq!(
        instalador_renut_ptbr::sistema::limpar_prefixo(&p).to_string_lossy(),
        r"C:\Games\reNut"
    );
}
// ---------------------------------------------------------------------------------------------
// Revisao 0.8.0: atualizacao de uma versao anterior, reversao em falha e preservacao de arquivos.

fn catalogo_com(texto: &str) -> Vec<ArquivoTrad> {
    let mut c = catalogo();
    for a in &mut c {
        a.frases[0].texto_ptbr = texto.to_string();
    }
    c
}

fn sha_de(p: &Path) -> String {
    instalador_renut_ptbr::patch::sha256_arquivo(p).unwrap()
}

fn sem_sobras_temporarias(raiz: &Path) -> bool {
    let estado = raiz.join(".ptbr-instalador");
    !estado.is_dir()
        || !fs::read_dir(&estado)
            .unwrap()
            .flatten()
            .any(|e| e.file_name().to_string_lossy().starts_with("tmp-"))
}

#[test]
fn atualiza_versao_anterior_sem_remocao_manual_e_sem_duplicar() {
    let tmp = tempfile::tempdir().unwrap();
    let raiz = tmp.path().join("reNut");
    criar_jogo(&raiz);
    let jogo = raiz.join("game").join("extraido");
    // "Versão anterior" (catálogo antigo) instalada pelo próprio instalador.
    let antigo = catalogo_com("Ola, mundo!");
    let sha_antigo = modpack::gerar(&jogo, &antigo, |_, _| {}).unwrap().sha256;
    let d = detect::analisar(&raiz, &antigo);
    plano::instalar_com(&d, &opcoes(true), &AtomicBool::new(false), &mut |_| {}, &antigo, &sha_antigo).unwrap();

    // Arquivos que a atualização não pode tocar.
    fs::create_dir_all(raiz.join("user").join("saves")).unwrap();
    fs::write(raiz.join("user").join("saves").join("slot0.sav"), b"save do jogador").unwrap();
    fs::write(raiz.join("mods").join("outro_mod.txt"), b"nao mexa").unwrap();
    let original = jogo.join("Debug").join("11").join("00").join("00").join("00");
    let sha_original = sha_de(&original);
    let sha_exe = sha_de(&raiz.join("renut.exe"));

    // Catálogo revisado: a nova versão substitui a anterior de uma vez.
    let novo = catalogo_com("Olá, mundo revisado!");
    let sha_novo = modpack::gerar(&jogo, &novo, |_, _| {}).unwrap().sha256;
    assert_ne!(sha_antigo, sha_novo);
    let d2 = detect::analisar(&raiz, &novo);
    assert!(!d2.mod_instalado, "a versão anterior não é a atual");
    let r = plano::instalar_com(&d2, &opcoes(true), &AtomicBool::new(false), &mut |_| {}, &novo, &sha_novo)
        .unwrap();
    assert!(r.mod_ok);

    let pasta = raiz.join("mods").join("ptbr_traducao");
    assert_eq!(sha_de(&pasta.join("ptbr_traducao.nbpatch")), sha_novo);
    let mut nomes_mods: Vec<String> = fs::read_dir(raiz.join("mods"))
        .unwrap()
        .flatten()
        .map(|e| e.file_name().to_string_lossy().to_string())
        .collect();
    nomes_mods.sort();
    assert_eq!(nomes_mods, vec!["mods.json", "outro_mod.txt", "ptbr_traducao"], "sem pasta duplicada");
    let mods_json = fs::read_to_string(raiz.join("mods").join("mods.json")).unwrap();
    assert_eq!(mods_json.matches("ptbr_traducao").count(), 1, "{mods_json}");
    assert_eq!(fs::read(raiz.join("user").join("saves").join("slot0.sav")).unwrap(), b"save do jogador");
    assert_eq!(fs::read(raiz.join("mods").join("outro_mod.txt")).unwrap(), b"nao mexa");
    assert_eq!(sha_de(&original), sha_original, "arquivo original do jogo intacto");
    assert_eq!(sha_de(&raiz.join("renut.exe")), sha_exe, "executável original intacto");
    let m = Manifesto::carregar(&raiz).unwrap();
    assert_eq!(m.mod_jogo.unwrap().nbpatch_sha256, sha_novo);
    assert!(sem_sobras_temporarias(&raiz));

    // Remoção depois da atualização reconhece o pacote novo pelo manifesto.
    let d3 = detect::analisar(&raiz, &novo);
    let rem = Remocao { mod_jogo: true, launcher: false, atalho: false };
    plano::remover(&d3, &rem, &mut |_| {}).unwrap();
    assert!(!pasta.exists());
    assert_eq!(fs::read(raiz.join("user").join("saves").join("slot0.sav")).unwrap(), b"save do jogador");
}

#[test]
fn falha_na_atualizacao_restaura_a_versao_anterior() {
    let tmp = tempfile::tempdir().unwrap();
    let raiz = tmp.path().join("reNut");
    criar_jogo(&raiz);
    let jogo = raiz.join("game").join("extraido");
    let antigo = catalogo_com("Ola, mundo!");
    let sha_antigo = modpack::gerar(&jogo, &antigo, |_, _| {}).unwrap().sha256;
    let d = detect::analisar(&raiz, &antigo);
    plano::instalar_com(&d, &opcoes(true), &AtomicBool::new(false), &mut |_| {}, &antigo, &sha_antigo).unwrap();
    let pasta = raiz.join("mods").join("ptbr_traducao");
    let manifesto_antes = fs::read(raiz.join(".ptbr-instalador").join("manifesto.json")).ok();

    // Provoca falha depois de publicar o pacote novo: mods.json vira uma pasta e não pode ser gravado.
    let mods_json = raiz.join("mods").join("mods.json");
    fs::remove_file(&mods_json).unwrap();
    fs::create_dir_all(&mods_json).unwrap();

    let novo = catalogo_com("Olá, mundo revisado!");
    let sha_novo = modpack::gerar(&jogo, &novo, |_, _| {}).unwrap().sha256;
    let d2 = detect::analisar(&raiz, &novo);
    let erro = plano::instalar_com(&d2, &opcoes(true), &AtomicBool::new(false), &mut |_| {}, &novo, &sha_novo);
    assert!(erro.is_err(), "a instalação deveria falhar");
    assert_eq!(sha_de(&pasta.join("ptbr_traducao.nbpatch")), sha_antigo, "a versão anterior volta inteira");
    assert!(pasta.join("mod.toml").is_file());
    assert_eq!(fs::read(raiz.join(".ptbr-instalador").join("manifesto.json")).ok(), manifesto_antes);
    assert!(sem_sobras_temporarias(&raiz));
}

#[test]
fn reconhece_as_versoes_publicadas_pelo_sha() {
    assert_eq!(modpack::VERSAO, "0.8.0");
    assert_eq!(modpack::versao_do_sha(modpack::SHA_ESPERADO), Some("0.8.0"));
    assert_eq!(
        modpack::versao_do_sha("7cd39a34efbae21dc8d3f919e63349e15df88397080ad59dd07207da0f5b5e25"),
        Some("0.7.0"),
        "o SHA histórico da Release v0.7.0 não muda"
    );
    assert_eq!(modpack::versao_do_sha("0000"), None);
    assert!(modpack::mod_toml(6099).contains("version = \"0.8.0\""));
}
