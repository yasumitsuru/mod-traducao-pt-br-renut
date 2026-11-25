//! Verificador de linha de comando do instalador.
//!
//! Usado pelos testes reais e por diagnostico. Nao substitui a interface grafica:
//!
//!   renut-instalador-checar status  <pasta do reNut>
//!   renut-instalador-checar instalar <pasta> [--jogo] [--launcher] [--atalho]
//!   renut-instalador-checar remover  <pasta> [--jogo] [--launcher] [--atalho]
//!   renut-instalador-checar gerar-mod <pasta do jogo extraido> <pasta de saida>

use std::path::PathBuf;
use std::sync::atomic::AtomicBool;

use instalador_renut_ptbr::{detect, modpack, plano, traducao};

fn main() {
    let mut args: Vec<String> = std::env::args().skip(1).collect();
    if args.is_empty() {
        eprintln!("uso: renut-instalador-checar <status|instalar|remover|gerar-mod> ...");
        std::process::exit(2);
    }
    let comando = args.remove(0);
    let flags: Vec<String> = args.iter().filter(|a| a.starts_with("--")).cloned().collect();
    let posicionais: Vec<String> = args.into_iter().filter(|a| !a.starts_with("--")).collect();
    let tem = |f: &str| flags.iter().any(|x| x == f);

    let catalogo = match traducao::carregar() {
        Ok(c) => c,
        Err(e) => falhar(&e),
    };

    match comando.as_str() {
        "status" => {
            let raiz = PathBuf::from(posicionais.first().cloned().unwrap_or_default());
            let d = detect::analisar(&raiz, &catalogo);
            println!("Pasta: {}", d.raiz.display());
            println!("ReNut encontrado: {}", d.renut_exe.is_some());
            println!("Versão (version.txt): {}", d.release);
            println!("Executável compatível: {}", d.exe_compativel);
            println!("Jogo encontrado: {} ({})", d.jogo_ok, d.jogo_detalhe);
            println!(
                "Tradução do jogo instalada: {} ({})",
                d.mod_instalado, d.mod_detalhe
            );
            println!(
                "Launcher traduzido instalado: {} ({})",
                d.launcher_instalado, d.launcher_detalhe
            );
            println!("DLLs: {} ({})", d.dlls_ok, d.dlls_detalhe);
            println!("Status: {}", d.status_geral());
            for p in &d.problemas {
                println!("PROBLEMA: {p}");
            }
            for a in &d.avisos {
                println!("AVISO: {a}");
            }
            std::process::exit(if d.exe_compativel { 0 } else { 3 });
        }
        "instalar" => {
            let raiz = PathBuf::from(posicionais.first().cloned().unwrap_or_default());
            let d = detect::analisar(&raiz, &catalogo);
            let opcoes = plano::Opcoes {
                mod_jogo: tem("--jogo"),
                launcher: tem("--launcher"),
                atalho: tem("--atalho"),
            };
            let cancelar = AtomicBool::new(false);
            let mut emitir = |e: plano::Evento| match e {
                plano::Evento::Etapa { numero, total, titulo } => {
                    println!("[{numero}/{total}] {titulo}");
                }
                plano::Evento::Progresso { fracao, texto } => {
                    println!("  {:>5.1}%  {}", fracao * 100.0, texto);
                }
                plano::Evento::Aviso(t) => println!("AVISO: {t}"),
            };
            match plano::instalar(&d, &opcoes, &cancelar, &mut emitir) {
                Ok(r) => {
                    for m in &r.mensagens {
                        println!("OK: {m}");
                    }
                    println!(
                        "RESULTADO: jogo={} launcher={} atalho={}",
                        r.mod_ok, r.launcher_ok, r.atalho_ok
                    );
                }
                Err(e) => falhar(&e),
            }
        }
        "remover" => {
            let raiz = PathBuf::from(posicionais.first().cloned().unwrap_or_default());
            let d = detect::analisar(&raiz, &catalogo);
            let remocao = plano::Remocao {
                mod_jogo: tem("--jogo") || flags.is_empty(),
                launcher: tem("--launcher") || flags.is_empty(),
                atalho: tem("--atalho") || flags.is_empty(),
            };
            let mut emitir = |e: plano::Evento| match e {
                plano::Evento::Etapa { numero, total, titulo } => {
                    println!("[{numero}/{total}] {titulo}");
                }
                plano::Evento::Progresso { .. } => {}
                plano::Evento::Aviso(t) => println!("AVISO: {t}"),
            };
            match plano::remover(&d, &remocao, &mut emitir) {
                Ok(ms) => {
                    for m in ms {
                        println!("OK: {m}");
                    }
                }
                Err(e) => falhar(&e),
            }
        }
        "gerar-mod" => {
            let jogo = PathBuf::from(posicionais.first().cloned().unwrap_or_default());
            let saida = PathBuf::from(posicionais.get(1).cloned().unwrap_or_default());
            match modpack::gerar(&jogo, &catalogo, |i, t| {
                if i % 20 == 0 || i == t {
                    println!("  {i}/{t}");
                }
            }) {
                Ok(g) => {
                    std::fs::create_dir_all(&saida).unwrap();
                    std::fs::write(saida.join("ptbr_traducao.nbpatch"), &g.nbpatch).unwrap();
                    std::fs::write(saida.join("mod.toml"), &g.mod_toml).unwrap();
                    println!(
                        "arquivos={} frases={} bytes={} sha256={} confere={}",
                        g.arquivos,
                        g.frases,
                        g.nbpatch.len(),
                        g.sha256,
                        g.sha_confere
                    );
                    if !g.sha_confere {
                        std::process::exit(4);
                    }
                }
                Err(e) => falhar(&e),
            }
        }
        outro => falhar(&format!("comando desconhecido: {outro}")),
    }
}

fn falhar(mensagem: &str) -> ! {
    eprintln!("ERRO: {mensagem}");
    std::process::exit(1)
}