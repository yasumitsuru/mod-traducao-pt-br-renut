#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

//! Instalador grafico da traducao PT-BR para o reNut.
//!
//! Fluxo: escolher a pasta do reNut -> conferir a deteccao -> marcar as opcoes ->
//! INSTALAR COMPONENTES SELECIONADOS. O trabalho pesado roda em segundo plano para a
//! janela nunca congelar, e o cancelamento acontece em pontos consistentes.

use std::path::PathBuf;
use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::mpsc::{self, Receiver};
use std::sync::Arc;

use eframe::egui;

use instalador_renut_ptbr::detect::{self, Deteccao};
use instalador_renut_ptbr::plano::{self, Evento, Opcoes, Remocao, Resultado};
use instalador_renut_ptbr::sistema::formatar_bytes;
use instalador_renut_ptbr::{atalho, patch, traducao};

const FUNDO: egui::Color32 = egui::Color32::from_rgb(15, 23, 38);
const CARTAO: egui::Color32 = egui::Color32::from_rgb(24, 35, 55);
const CARTAO_CLARO: egui::Color32 = egui::Color32::from_rgb(32, 46, 72);
const CREME: egui::Color32 = egui::Color32::from_rgb(244, 238, 224);
const CINZA: egui::Color32 = egui::Color32::from_rgb(168, 183, 208);
const AZUL: egui::Color32 = egui::Color32::from_rgb(64, 120, 214);
const VERDE: egui::Color32 = egui::Color32::from_rgb(88, 196, 138);
const AMBAR: egui::Color32 = egui::Color32::from_rgb(232, 176, 74);
const VERMELHO: egui::Color32 = egui::Color32::from_rgb(230, 110, 100);
const BORDA: egui::Color32 = egui::Color32::from_rgb(46, 63, 92);

const ETAPAS: [&str; 9] = [
    "Verificando instalação",
    "Validando arquivos",
    "Preparando tradução do jogo",
    "Gerando arquivos PT-BR",
    "Preparando launcher",
    "Aplicando patches",
    "Verificando integridade",
    "Criando atalho",
    "Concluindo instalação",
];

#[derive(Clone, Copy, PartialEq, Eq)]
enum AcaoConfirmada {
    Instalar,
    Remover,
}

struct Confirmacao {
    acao: AcaoConfirmada,
    titulo: String,
    linhas: Vec<String>,
    aviso: Option<String>,
}

#[derive(Clone, Copy, PartialEq, Eq)]
enum Trabalho {
    Analisando,
    Instalando,
    Removendo,
}

enum Mensagem {
    Analise(Box<Deteccao>),
    Evento(Evento),
    FimInstalacao(Result<Resultado, String>),
    FimRemocao(Result<Vec<String>, String>),
}

struct App {
    caminho: String,
    deteccao: Option<Deteccao>,
    erro: Option<String>,
    trabalho: Option<Trabalho>,
    canal: Option<Receiver<Mensagem>>,
    cancelar: Arc<AtomicBool>,
    etapa: (usize, usize, String),
    fracao: f32,
    progresso_texto: String,
    avisos: Vec<String>,
    op_mod: bool,
    op_launcher: bool,
    op_atalho: bool,
    manutencao: bool,
    rem_mod: bool,
    rem_launcher: bool,
    rem_atalho: bool,
    confirmacao: Option<Confirmacao>,
    resultado: Option<Resultado>,
    remocao_mensagens: Option<Vec<String>>,
    mostrar_detalhes: bool,
    estilo_aplicado: bool,
    analise_inicial: bool,
}

impl App {
    fn new() -> Self {
        Self {
            caminho: String::new(),
            deteccao: None,
            erro: None,
            trabalho: None,
            canal: None,
            cancelar: Arc::new(AtomicBool::new(false)),
            etapa: (0, 9, String::new()),
            fracao: 0.0,
            progresso_texto: String::new(),
            avisos: Vec::new(),
            op_mod: false,
            op_launcher: false,
            op_atalho: true,
            manutencao: false,
            rem_mod: false,
            rem_launcher: false,
            rem_atalho: false,
            confirmacao: None,
            resultado: None,
            remocao_mensagens: None,
            mostrar_detalhes: false,
            estilo_aplicado: false,
            analise_inicial: false,
        }
    }

    fn ocupado(&self) -> bool {
        self.trabalho.is_some()
    }

    fn procurar(&mut self) {
        let inicial = if self.caminho.trim().is_empty() {
            None
        } else {
            Some(PathBuf::from(self.caminho.trim()))
        };
        let mut dialogo = rfd::FileDialog::new()
            .set_title("Selecione a pasta onde o reNut está instalado");
        if let Some(p) = inicial.filter(|p| p.is_dir()) {
            dialogo = dialogo.set_directory(p);
        }
        if let Some(pasta) = dialogo.pick_folder() {
            self.caminho = pasta.to_string_lossy().to_string();
            self.analisar();
        }
    }

    fn analisar(&mut self) {
        if self.ocupado() {
            return;
        }
        let caminho = self.caminho.trim().to_string();
        if caminho.is_empty() {
            self.erro = Some("Escolha a pasta onde o reNut está instalado.".into());
            self.deteccao = None;
            return;
        }
        self.erro = None;
        self.resultado = None;
        self.remocao_mensagens = None;
        self.deteccao = None;
        self.trabalho = Some(Trabalho::Analisando);
        self.progresso_texto = "Conferindo a pasta escolhida…".into();
        let (tx, rx) = mpsc::channel();
        self.canal = Some(rx);
        std::thread::spawn(move || {
            let catalogo = match traducao::carregar() {
                Ok(c) => c,
                Err(e) => {
                    let _ = tx.send(Mensagem::FimInstalacao(Err(e)));
                    return;
                }
            };
            let d = detect::analisar(&PathBuf::from(caminho), &catalogo);
            let _ = tx.send(Mensagem::Analise(Box::new(d)));
        });
    }

    fn aplicar_deteccao(&mut self, d: Deteccao) {
        // Padroes seguros: marcar o que ainda nao esta instalado, nunca substituir por engano.
        self.op_mod = d.pode_instalar_mod() && !d.mod_instalado;
        self.op_launcher = d.pode_instalar_launcher() && !d.launcher_instalado;
        self.op_atalho = true;
        self.manutencao = d.mod_instalado || d.launcher_instalado || d.atalho.is_some();
        self.rem_mod = false;
        self.rem_launcher = false;
        self.rem_atalho = false;
        self.deteccao = Some(d);
    }

    fn inicio(&mut self) {
        let Some(d) = self.deteccao.clone() else {
            self.erro = Some("Escolha e confira a pasta do reNut antes de instalar.".into());
            return;
        };
        if self.op_mod || self.op_launcher {
            let mut linhas = Vec::new();
            let mut aviso = None;
            if self.op_mod {
                linhas.push(format!(
                    "Tradução do jogo: {} arquivos de texto serão gerados a partir da sua cópia \
                     legítima e instalados em mods/ptbr_traducao.",
                    instalador_renut_ptbr::modpack::ARQUIVOS_ESPERADOS
                ));
                if d.mod_instalado {
                    aviso = Some(format!(
                        "A tradução do jogo já está instalada e será substituída pela mesma \
                         versão {} (reinstalação verificada).",
                        instalador_renut_ptbr::modpack::VERSAO
                    ));
                } else if d.mod_desatualizado {
                    aviso = Some(format!(
                        "A tradução {} instalada será atualizada para a {}. A pasta anterior é \
                         substituída de uma vez e volta se algo falhar; saves e outros mods não mudam.",
                        d.mod_versao.as_deref().unwrap_or("anterior"),
                        instalador_renut_ptbr::modpack::VERSAO
                    ));
                }
            }
            if self.op_launcher {
                linhas.push(format!(
                    "Launcher: uma cópia isolada será criada em {} (cerca de 110 MB). \
                     O renut.exe e as DLLs originais não são alterados.",
                    d.raiz.join("launcher-ptbr").display()
                ));
                if d.launcher_instalado {
                    aviso = Some(
                        "O launcher traduzido já existe e será substituído por uma cópia nova, \
                         conferida arquivo por arquivo."
                            .to_string(),
                    );
                }
            }
            if self.op_atalho {
                linhas.push(
                    "Atalho: será criado ou atualizado na sua área de trabalho, apontando para o \
                     launcher traduzido (ou para o reNut original, se o launcher não for traduzido)."
                        .into(),
                );
            }
            linhas.push(
                "Saves, outros mods, DLCs, Title Updates e configurações da instalação original \
                 não serão modificados."
                    .into(),
            );
            self.confirmacao = Some(Confirmacao {
                acao: AcaoConfirmada::Instalar,
                titulo: "Confirmar instalação".into(),
                linhas,
                aviso,
            });
        }
    }

    fn remover(&mut self) {
        let Some(d) = self.deteccao.clone() else {
            return;
        };
        let mut linhas = Vec::new();
        if self.rem_mod {
            linhas.push(
                "Remover a tradução do jogo: apaga somente os arquivos do mod PT-BR que este \
                 instalador criou, preservando os outros mods."
                    .into(),
            );
        }
        if self.rem_launcher {
            linhas.push(
                "Remover o launcher traduzido: apaga a pasta copiada, conferindo cada hash. \
                 O renut.exe e as DLLs originais permanecem intactos."
                    .into(),
            );
        }
        if self.rem_atalho {
            linhas.push("Remover o atalho criado por este instalador na área de trabalho.".into());
        }
        if linhas.is_empty() {
            return;
        }
        if !d.mod_instalado && self.rem_mod {
            linhas.push("Observação: a tradução do jogo não está instalada.".into());
        }
        self.confirmacao = Some(Confirmacao {
            acao: AcaoConfirmada::Remover,
            titulo: "Confirmar remoção".into(),
            linhas,
            aviso: None,
        });
    }

    fn executar_instalacao(&mut self, d: Deteccao) {
        self.confirmacao = None;
        self.trabalho = Some(Trabalho::Instalando);
        self.erro = None;
        self.resultado = None;
        self.avisos.clear();
        self.etapa = (0, 9, String::new());
        self.fracao = 0.0;
        self.progresso_texto = "Começando…".into();
        self.cancelar = Arc::new(AtomicBool::new(false));
        let cancelar = self.cancelar.clone();
        let opcoes = Opcoes {
            mod_jogo: self.op_mod,
            launcher: self.op_launcher,
            atalho: self.op_atalho,
        };
        let (tx, rx) = mpsc::channel();
        self.canal = Some(rx);
        std::thread::spawn(move || {
            let mut emitir = |e: Evento| {
                let _ = tx.send(Mensagem::Evento(e));
            };
            let r = plano::instalar(&d, &opcoes, &cancelar, &mut emitir);
            let _ = tx.send(Mensagem::FimInstalacao(r));
        });
    }

    fn executar_remocao(&mut self, d: Deteccao, remocao: Remocao) {
        self.confirmacao = None;
        self.trabalho = Some(Trabalho::Removendo);
        self.erro = None;
        self.remocao_mensagens = None;
        self.etapa = (0, 9, String::new());
        self.fracao = 0.0;
        self.progresso_texto = "Removendo…".into();
        let (tx, rx) = mpsc::channel();
        self.canal = Some(rx);
        std::thread::spawn(move || {
            let mut emitir = |e: Evento| {
                let _ = tx.send(Mensagem::Evento(e));
            };
            let r = plano::remover(&d, &remocao, &mut emitir);
            let _ = tx.send(Mensagem::FimRemocao(r));
        });
    }

    fn processar_mensagens(&mut self) {
        let mut recebidas = Vec::new();
        if let Some(rx) = &self.canal {
            while let Ok(m) = rx.try_recv() {
                recebidas.push(m);
            }
        }
        for m in recebidas {
            match m {
                Mensagem::Analise(d) => {
                    self.trabalho = None;
                    self.aplicar_deteccao(*d);
                }
                Mensagem::Evento(e) => match e {
                    Evento::Etapa {
                        numero,
                        total,
                        titulo,
                    } => {
                        self.etapa = (numero, total, titulo.clone());
                        self.progresso_texto = titulo;
                    }
                    Evento::Progresso { fracao, texto } => {
                        self.fracao = fracao;
                        self.progresso_texto = texto;
                    }
                    Evento::Aviso(t) => self.avisos.push(t),
                },
                Mensagem::FimInstalacao(r) => {
                    self.trabalho = None;
                    self.canal = None;
                    match r {
                        Ok(res) => {
                            self.resultado = Some(res);
                            self.avisos.clear();
                            self.caminho = self.caminho.clone();
                            let caminho = self.caminho.clone();
                            self.canal = None;
                            self.analisar_caminho(caminho);
                        }
                        Err(e) => self.erro = Some(e),
                    }
                }
                Mensagem::FimRemocao(r) => {
                    self.trabalho = None;
                    self.canal = None;
                    match r {
                        Ok(ms) => {
                            self.remocao_mensagens = Some(ms);
                            let caminho = self.caminho.clone();
                            self.analisar_caminho(caminho);
                        }
                        Err(e) => self.erro = Some(e),
                    }
                }
            }
        }
    }

    fn analisar_caminho(&mut self, caminho: String) {
        self.caminho = caminho.clone();
        if caminho.trim().is_empty() {
            return;
        }
        self.progresso_texto = "Conferindo a pasta escolhida…".into();
        let (tx, rx) = mpsc::channel();
        self.canal = Some(rx);
        self.trabalho = Some(Trabalho::Analisando);
        std::thread::spawn(move || {
            let catalogo = match traducao::carregar() {
                Ok(c) => c,
                Err(_) => Vec::new(),
            };
            let d = detect::analisar(&PathBuf::from(caminho), &catalogo);
            let _ = tx.send(Mensagem::Analise(Box::new(d)));
        });
    }

    fn cabecalho(&mut self, ui: &mut egui::Ui) {
        ui.horizontal(|ui| {
            ui.label(
                egui::RichText::new("TRADUÇÃO PT-BR PARA RENUT")
                    .size(11.0)
                    .strong()
                    .color(AMBAR),
            );
            ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                let (texto, cor) = match &self.deteccao {
                    None => ("AGUARDANDO A PASTA", CINZA),
                    Some(d) if d.mod_instalado || d.launcher_instalado => ("INSTALADO", VERDE),
                    Some(d) if d.pode_instalar_mod() && d.pode_instalar_launcher() => {
                        ("PRONTO PARA INSTALAR", VERDE)
                    }
                    Some(d) if d.pode_instalar_mod() => ("SÓ O MOD DO JOGO", AMBAR),
                    Some(_) => ("VERIFIQUE A PASTA", VERMELHO),
                };
                selo(ui, texto, cor);
            });
        });
        ui.label(
            egui::RichText::new("Instalador de Tradução PT-BR para reNut")
                .size(26.0)
                .strong()
                .color(CREME),
        );
        ui.label(
            egui::RichText::new(
                "Traduza o texto do jogo e a interface do launcher original, sem alterar os \
                 arquivos originais.",
            )
            .size(13.0)
            .color(CINZA),
        );
        ui.add_space(10.0);
    }

    fn tela_pasta(&mut self, ui: &mut egui::Ui) {
        cartao(ui, |ui| {
            ui.label(egui::RichText::new("Pasta raiz do reNut").size(12.0).color(CINZA));
            ui.add_space(4.0);
            ui.horizontal(|ui| {
                let largura = (ui.available_width() - 150.0).max(260.0);
                let resposta = ui.add(
                    egui::TextEdit::singleline(&mut self.caminho)
                        .hint_text("Ex.: D:\\Jogos\\reNut")
                        .desired_width(largura)
                        .font(egui::TextStyle::Monospace),
                );
                if resposta.lost_focus() && ui.input(|i| i.key_pressed(egui::Key::Enter)) {
                    self.analisar();
                }
                let procurar = ui.add(
                    egui::Button::new(egui::RichText::new("PROCURAR...").strong().size(14.0))
                        .min_size(egui::vec2(130.0, 34.0))
                        .fill(AZUL),
                );
                if procurar.clicked() && !self.ocupado() {
                    self.procurar();
                }
            });
            ui.add_space(6.0);
            ui.horizontal(|ui| {
                ui.label(
                    egui::RichText::new(
                        "Escolha a pasta que contém o renut.exe. Não é preciso escolher a pasta \
                         game nem a pasta mods.",
                    )
                    .size(11.5)
                    .color(CINZA),
                );
                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                    let b = ui.add_enabled(
                        !self.ocupado() && !self.caminho.trim().is_empty(),
                        egui::Button::new(egui::RichText::new("Verificar pasta").size(12.0)),
                    );
                    if b.clicked() {
                        self.analisar();
                    }
                });
            });
        });
    }

    fn tela_status(&mut self, ui: &mut egui::Ui) {
        let Some(d) = self.deteccao.clone() else {
            return;
        };
        cartao(ui, |ui| {
            ui.horizontal(|ui| {
                ui.label(egui::RichText::new("Resumo da instalação").size(15.0).strong().color(CREME));
                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                    ui.label(egui::RichText::new(d.status_geral()).size(11.5).color(CINZA));
                });
            });
            ui.add_space(8.0);
            let (selo_renut, cor_renut) = if d.renut_exe.is_some() {
                ("ENCONTRADO", VERDE)
            } else {
                ("NÃO ENCONTRADO", VERMELHO)
            };
            let (selo_versao, cor_versao) = if d.exe_compativel {
                ("COMPATÍVEL", VERDE)
            } else {
                ("INCOMPATÍVEL", VERMELHO)
            };
            let (selo_jogo, cor_jogo) = if d.jogo_ok {
                ("ENCONTRADO", VERDE)
            } else {
                ("NÃO ENCONTRADO", VERMELHO)
            };
            let (selo_mod, cor_mod) = if d.mod_instalado {
                ("INSTALADA", VERDE)
            } else if d.pode_instalar_mod() {
                ("DISPONÍVEL", AZUL)
            } else {
                ("INDISPONÍVEL", VERMELHO)
            };
            let (selo_launcher, cor_launcher) = if d.launcher_instalado {
                ("INSTALADO", VERDE)
            } else if d.pode_instalar_launcher() {
                ("DISPONÍVEL", AZUL)
            } else {
                ("INDISPONÍVEL", VERMELHO)
            };
            let linhas: Vec<(&str, String, &str, egui::Color32)> = vec![
                (
                    "ReNut encontrado",
                    if d.renut_exe.is_some() {
                        format!(
                            "renut.exe conferido · {}",
                            if d.release.is_empty() {
                                "versão não identificada".to_string()
                            } else {
                                d.release.clone()
                            }
                        )
                    } else {
                        "renut.exe não encontrado nesta pasta".to_string()
                    },
                    selo_renut,
                    cor_renut,
                ),
                (
                    "Versão compatível",
                    if d.exe_compativel {
                        format!(
                            "SHA-256 conferido · patch do launcher {}",
                            patch::manifesto().map(|m| m.version).unwrap_or_default()
                        )
                    } else {
                        "o patch do launcher só aceita a versão big-lua-energy 0.11.21".to_string()
                    },
                    selo_versao,
                    cor_versao,
                ),
                (
                    "Jogo encontrado",
                    d.jogo_detalhe.clone(),
                    selo_jogo,
                    cor_jogo,
                ),
                (
                    "Tradução do jogo",
                    d.mod_detalhe.clone(),
                    selo_mod,
                    cor_mod,
                ),
                (
                    "Patch do launcher",
                    format!("{} · {}", d.dlls_detalhe, d.launcher_detalhe),
                    selo_launcher,
                    cor_launcher,
                ),
            ];
            for (rotulo, detalhe, texto_selo, cor_selo) in linhas {
                ui.horizontal(|ui| {
                    ui.add_sized(
                        [160.0, 18.0],
                        egui::Label::new(egui::RichText::new(rotulo).size(12.5).color(CREME)),
                    );
                    selo(ui, texto_selo, cor_selo);
                    ui.add(
                        egui::Label::new(egui::RichText::new(detalhe).size(11.5).color(CINZA))
                            .wrap(),
                    );
                });
                ui.add_space(2.0);
            }
            if let Some(livre) = d.espaco_livre {
                ui.add_space(4.0);
                ui.label(
                    egui::RichText::new(format!(
                        "Espaço livre na unidade: {} · atalho: {}",
                        formatar_bytes(livre),
                        d.atalho
                            .as_ref()
                            .and_then(|p| p.file_name())
                            .map(|n| n.to_string_lossy().to_string())
                            .unwrap_or_else(|| "ainda não criado".into())
                    ))
                    .size(11.0)
                    .color(CINZA),
                );
            }
        });
        if d.renut_exe.is_none() {
            ui.add_space(6.0);
            aviso(
                ui,
                "Esta pasta não contém o renut.exe. Escolha a pasta onde o reNut foi instalado \
                 (a mesma que tem o renut.exe, renut.toml e a pasta game).",
                VERMELHO,
            );
        }
        ui.add_space(8.0);
    }

    fn tela_opcoes(&mut self, ui: &mut egui::Ui) {
        let Some(d) = self.deteccao.clone() else {
            return;
        };
        if self.resultado.is_some() || self.remocao_mensagens.is_some() {
            return;
        }
        cartao(ui, |ui| {
            ui.label(egui::RichText::new("O que instalar").size(15.0).strong().color(CREME));
            ui.label(
                egui::RichText::new("As três opções são independentes. Marque só o que deseja.")
                    .size(11.5)
                    .color(CINZA),
            );
            ui.add_space(8.0);
            let versao_mod = instalador_renut_ptbr::modpack::VERSAO;
            let descricao_mod = if d.mod_instalado {
                format!("Já instalada. Marcar de novo reinstala e confere o SHA-256 do pacote {versao_mod}.")
            } else if d.mod_desatualizado && d.pode_instalar_mod() {
                format!(
                    "Versão {} instalada. Marque para atualizar para a {versao_mod}, sem remover nada à mão.",
                    d.mod_versao.as_deref().unwrap_or("anterior")
                )
            } else if d.pode_instalar_mod() {
                "Gera o pacote localmente a partir da sua cópia do jogo e instala em mods/ptbr_traducao.".to_string()
            } else {
                "Indisponível: a pasta do jogo não foi encontrada ou está incompleta.".to_string()
            };
            let rotulo_mod = format!("Mod PT-BR {versao_mod} · 107 arquivos · 6.110 frases");
            opcao(
                ui,
                &mut self.op_mod,
                d.pode_instalar_mod(),
                "Instalar tradução PT-BR do jogo",
                &descricao_mod,
                &rotulo_mod,
            );
            ui.add_space(6.0);
            opcao(
                ui,
                &mut self.op_launcher,
                d.pode_instalar_launcher(),
                "Aplicar tradução PT-BR ao launcher do reNut",
                if d.launcher_instalado {
                    "Já instalado. Marcar de novo recria a cópia traduzida e confere executável e DLLs."
                } else if d.pode_instalar_launcher() {
                    "Cria uma cópia isolada em launcher-ptbr e traduz o executável e as duas DLLs obrigatórias."
                } else {
                    "Indisponível: o renut.exe ou as DLLs não são a versão suportada. O patch nunca e aplicado à força."
                },
                "Launcher 0.9.0-preview.1 · reNut 0.11.21",
            );
            ui.add_space(6.0);
            opcao(
                ui,
                &mut self.op_atalho,
                true,
                "Criar atalho na área de trabalho",
                "Criado só depois que a instalação for verificada. Resolve a área de trabalho real do Windows.",
                "Banjo-Kazooie Nuts & Bolts — PT-BR",
            );

            if let Some(idioma) = d.idioma {
                if idioma != 1 {
                    ui.add_space(8.0);
                    aviso(
                        ui,
                        &format!(
                            "O renut.toml está no idioma {idioma}. A tradução do jogo usa English (1). \
                             No launcher traduzido o instalador ajusta o idioma na cópia; no launcher \
                             original, selecione English no menu do jogo."
                        ),
                        AMBAR,
                    );
                }
            }
            for p in &d.problemas {
                ui.add_space(6.0);
                aviso(ui, p, VERMELHO);
            }
        });
    }

    fn botao_instalar(&mut self, ui: &mut egui::Ui) {
        if self.resultado.is_some() || self.remocao_mensagens.is_some() || self.ocupado() {
            return;
        }
        let Some(d) = self.deteccao.clone() else {
            ui.label(
                egui::RichText::new("Escolha a pasta do reNut para começar.")
                    .size(12.0)
                    .color(CINZA),
            );
            return;
        };
        let habilitado = self.erro.is_none()
            && (self.op_mod || self.op_launcher)
            && (!self.op_mod || d.pode_instalar_mod())
            && (!self.op_launcher || d.pode_instalar_launcher());
        let largura = ui.available_width().min(620.0);
        let mut clicado = false;
        ui.with_layout(egui::Layout::top_down(egui::Align::Center), |ui| {
            let botao = egui::Button::new(
                egui::RichText::new("INSTALAR COMPONENTES SELECIONADOS")
                    .size(16.0)
                    .strong()
                    .color(if habilitado { egui::Color32::WHITE } else { CINZA }),
            )
            .min_size(egui::vec2(largura, 44.0))
            .fill(if habilitado { AZUL } else { CARTAO_CLARO });
            if ui.add_enabled(habilitado, botao).clicked() {
                clicado = true;
            }
        });
        if clicado {
            self.inicio();
        }
        if !habilitado {
            ui.add_space(2.0);
            let motivo = if d.erro_de_pasta() {
                "A pasta ainda não e uma instalação válida do reNut."
            } else if self.op_mod || self.op_launcher {
                "Resolva as pendências acima para liberar a instalação."
            } else {
                "Marque pelo menos uma tradução para instalar."
            };
            ui.label(egui::RichText::new(motivo).size(10.5).color(CINZA));
        }
    }

    fn manutencao(&mut self, ui: &mut egui::Ui) {
        let Some(d) = self.deteccao.clone() else {
            return;
        };
        if self.resultado.is_some() || self.remocao_mensagens.is_some() {
            return;
        }
        if d.mod_instalado || d.launcher_instalado || d.atalho.is_some() {
            ui.add_space(6.0);
            ui.horizontal(|ui| {
                let resposta = ui.add(
                    egui::Button::new(
                        egui::RichText::new(if self.manutencao {
                            "Manutenção da instalação ▾"
                        } else {
                            "Manutenção da instalação ▸"
                        })
                        .size(12.5),
                    )
                    .fill(CARTAO_CLARO),
                );
                if resposta.clicked() {
                    self.manutencao = !self.manutencao;
                }
                ui.label(
                    egui::RichText::new(
                        "Remover componentes instalados por este instalador, com verificação de hashes.",
                    )
                    .size(11.0)
                    .color(CINZA),
                );
            });
            if self.manutencao {
                ui.add_space(6.0);
                cartao_claro(ui, |ui| {
                    ui.add_enabled(
                        d.mod_instalado,
                        egui::Checkbox::new(&mut self.rem_mod, "Remover tradução do jogo"),
                    );
                    ui.add_enabled(
                        d.launcher_instalado,
                        egui::Checkbox::new(&mut self.rem_launcher, "Remover launcher traduzido"),
                    );
                    ui.add_enabled(
                        d.atalho.is_some(),
                        egui::Checkbox::new(
                            &mut self.rem_atalho,
                            "Remover atalho da área de trabalho",
                        ),
                    );
                    ui.add_space(6.0);
                    let ativo = !self.ocupado()
                        && (self.rem_mod || self.rem_launcher || self.rem_atalho);
                    let b = egui::Button::new(
                        egui::RichText::new("REMOVER SELECIONADOS")
                            .size(13.0)
                            .strong()
                            .color(if ativo { CREME } else { CINZA }),
                    )
                    .fill(if ativo {
                        egui::Color32::from_rgb(120, 52, 56)
                    } else {
                        CARTAO
                    })
                    .min_size(egui::vec2(240.0, 34.0));
                    if ui.add_enabled(ativo, b).clicked() {
                        self.remover();
                    }
                });
            }
        }
    }

    fn tela_detalhes(&mut self, ui: &mut egui::Ui) {
        let Some(d) = self.deteccao.clone() else {
            return;
        };
        ui.add_space(4.0);
        let titulo = if self.mostrar_detalhes {
            "Detalhes técnicos ▾"
        } else {
            "Detalhes técnicos ▸"
        };
        if ui
            .add(egui::Button::new(egui::RichText::new(titulo).size(11.5)).fill(CARTAO))
            .clicked()
        {
            self.mostrar_detalhes = !self.mostrar_detalhes;
        }
        if self.mostrar_detalhes {
            cartao_claro(ui, |ui| {
                let linhas = [
                    ("Pasta raiz", d.raiz.display().to_string()),
                    (
                        "Executável",
                        d.renut_exe
                            .as_ref()
                            .map(|p| format!("{} ({} bytes)", p.display(), d.exe_tamanho))
                            .unwrap_or_else(|| "não encontrado".into()),
                    ),
                    (
                        "SHA-256 do renut.exe",
                        if d.exe_sha.is_empty() {
                            "—".into()
                        } else {
                            d.exe_sha.clone()
                        },
                    ),
                    (
                        "Pasta do jogo",
                        d.jogo
                            .as_ref()
                            .map(|p| p.display().to_string())
                            .unwrap_or_else(|| "não encontrada".into()),
                    ),
                    (
                        "Pasta de mods",
                        d.mods_dir
                            .as_ref()
                            .map(|p| p.display().to_string())
                            .unwrap_or_else(|| "não determinada".into()),
                    ),
                    (
                        "Manifesto do instalador",
                        if d.manifesto.is_some() {
                            "presente".into()
                        } else {
                            "ainda não criado".into()
                        },
                    ),
                    (
                        "Idioma no renut.toml",
                        d.idioma
                            .map(|i| i.to_string())
                            .unwrap_or_else(|| "não configurado".into()),
                    ),
                ];
                for (rotulo, valor) in linhas {
                    ui.horizontal_wrapped(|ui| {
                        ui.label(egui::RichText::new(format!("{rotulo}: ")).size(11.0).color(CINZA));
                        ui.label(
                            egui::RichText::new(valor)
                                .size(11.0)
                                .monospace()
                                .color(CREME),
                        );
                    });
                }
                for a in &d.avisos {
                    ui.add_space(4.0);
                    ui.label(egui::RichText::new(format!("• {a}")).size(11.0).color(AMBAR));
                }
            });
        }
    }

    fn tela_progresso(&mut self, ui: &mut egui::Ui) {
        let trabalho = self.trabalho;
        let titulo = match trabalho {
            Some(Trabalho::Analisando) => "Conferindo a pasta do reNut",
            Some(Trabalho::Instalando) => "Instalando componentes",
            Some(Trabalho::Removendo) => "Removendo componentes",
            None => return,
        };
        cartao(ui, |ui| {
            ui.label(egui::RichText::new(titulo).size(20.0).strong().color(CREME));
            ui.add_space(8.0);
            if matches!(trabalho, Some(Trabalho::Analisando) | Some(Trabalho::Removendo)) {
                ui.spinner();
                ui.label(egui::RichText::new(&self.progresso_texto).size(12.5).color(CINZA));
                for a in &self.avisos {
                    ui.add_space(4.0);
                    ui.label(egui::RichText::new(format!("• {a}")).size(11.0).color(AMBAR));
                }
                return;
            }
            let (numero, total, _) = self.etapa.clone();
            for (i, nome) in ETAPAS.iter().enumerate() {
                let indice = i + 1;
                let (marca, _cor) = if indice < numero {
                    ("✔", VERDE)
                } else if indice == numero {
                    ("▶", AMBAR)
                } else {
                    ("·", CINZA)
                };
                let mut texto = egui::RichText::new(format!("{marca}  {indice}. {nome}")).size(12.5);
                texto = if indice == numero {
                    texto.strong().color(CREME)
                } else if indice < numero {
                    texto.color(VERDE)
                } else {
                    texto.color(CINZA)
                };
                ui.label(texto);
                if total > 0 && numero > 0 {
                    let _ = total;
                }
            }
            ui.add_space(10.0);
            ui.add(
                egui::ProgressBar::new(self.fracao)
                    .desired_width(ui.available_width())
                    .text(format!("{:.0}%", self.fracao * 100.0))
                    .animate(true),
            );
            ui.add_space(6.0);
            ui.label(egui::RichText::new(&self.progresso_texto).size(12.0).color(CINZA));
            for a in &self.avisos {
                ui.add_space(4.0);
                ui.label(egui::RichText::new(format!("• {a}")).size(11.0).color(AMBAR));
            }
            ui.add_space(10.0);
            let b = egui::Button::new(
                egui::RichText::new(if self.cancelar.load(Ordering::Relaxed) {
                    "Cancelando no próximo ponto seguro…"
                } else {
                    "Cancelar"
                })
                .size(12.5),
            )
            .fill(CARTAO_CLARO);
            if ui
                .add_enabled(!self.cancelar.load(Ordering::Relaxed), b)
                .clicked()
            {
                self.cancelar.store(true, Ordering::Relaxed);
            }
        });
    }

    fn tela_resultado(&mut self, ui: &mut egui::Ui) {
        let Some(r) = self.resultado.clone() else {
            return;
        };
        cartao(ui, |ui| {
            ui.horizontal(|ui| {
                selo(ui, "INSTALAÇÃO CONCLUÍDA", VERDE);
                ui.label(
                    egui::RichText::new("Tudo foi verificado antes de ser publicado.")
                        .size(12.0)
                        .color(CINZA),
                );
            });
            ui.add_space(8.0);
            for m in &r.mensagens {
                ui.label(egui::RichText::new(format!("• {m}")).size(12.0).color(CREME));
            }
            if r.mod_ok {
                ui.label(
                    egui::RichText::new(
                        "O jogo lerá o texto em English (1); o mod não altera nenhum arquivo do jogo.",
                    )
                    .size(11.5)
                    .color(CINZA),
                );
            }
            if r.launcher_ok {
                ui.label(
                    egui::RichText::new(
                        "Abra o jogo pelo launcher traduzido ou pelo atalho criado. \
                         O renut.exe original continua intacto.",
                    )
                    .size(11.5)
                    .color(CINZA),
                );
            }
            if let Some(a) = &r.atalho_local {
                ui.label(
                    egui::RichText::new(format!("Atalho criado: {a}")).size(11.5).color(CINZA),
                );
            }
            if !r.atalho_ok && self.op_atalho {
                ui.label(
                    egui::RichText::new("O atalho não foi confirmado nesta execução.")
                        .size(11.5)
                        .color(AMBAR),
                );
            }
            ui.add_space(10.0);
            ui.horizontal(|ui| {
                if let Some(p) = &r.launcher_local {
                    if ui.button("Abrir pasta do launcher").clicked() {
                        abrir_pasta(std::path::Path::new(p));
                    }
                }
                if let Some(p) = &r.mod_local {
                    if ui.button("Abrir pasta do mod").clicked() {
                        abrir_pasta(std::path::Path::new(p));
                    }
                }
                if ui.button("Voltar ao início").clicked() {
                    self.resultado = None;
                    let caminho = self.caminho.clone();
                    self.analisar_caminho(caminho);
                }
            });
        });
    }

    fn tela_remocao(&mut self, ui: &mut egui::Ui) {
        let Some(ms) = self.remocao_mensagens.clone() else {
            return;
        };
        cartao(ui, |ui| {
            selo(ui, "REMOÇÃO CONCLUÍDA", VERDE);
            ui.add_space(8.0);
            for m in &ms {
                ui.label(egui::RichText::new(format!("• {m}")).size(12.0).color(CREME));
            }
            ui.label(
                egui::RichText::new(
                    "Os arquivos originais do reNut e do jogo não foram alterados. \
                     Outros mods e saves foram preservados.",
                )
                .size(11.5)
                .color(CINZA),
            );
            ui.add_space(8.0);
            if ui.button("Voltar ao início").clicked() {
                self.remocao_mensagens = None;
                let caminho = self.caminho.clone();
                self.analisar_caminho(caminho);
            }
        });
    }

    fn erro(&mut self, ui: &mut egui::Ui) {
        let Some(e) = self.erro.clone() else {
            return;
        };
        cartao(ui, |ui| {
            ui.horizontal(|ui| {
                selo(ui, "NÃO FOI POSSÍVEL CONCLUIR", VERMELHO);
            });
            ui.add_space(6.0);
            ui.add(
                egui::Label::new(egui::RichText::new(&e).size(12.5).color(CREME)).wrap(),
            );
            ui.add_space(4.0);
            ui.label(
                egui::RichText::new(
                    "O instalador desfaz o que criou quando algo falha e não apaga arquivos que \
                     não sejam dele. Os arquivos originais continuam intactos.",
                )
                .size(11.0)
                .color(CINZA),
            );
            ui.add_space(8.0);
            ui.horizontal(|ui| {
                if ui.button("Tentar de novo").clicked() {
                    self.erro = None;
                    let caminho = self.caminho.clone();
                    self.analisar_caminho(caminho);
                }
                if ui.button("Escolher outra pasta").clicked() {
                    self.erro = None;
                    self.procurar();
                }
            });
        });
    }

    fn confirmacao(&mut self, ctx: &egui::Context) {
        let Some(c) = &self.confirmacao else {
            return;
        };
        let mut confirmar = false;
        let mut cancelar = false;
        egui::Window::new(c.titulo.clone())
            .collapsible(false)
            .resizable(false)
            .anchor(egui::Align2::CENTER_CENTER, [0.0, 0.0])
            .max_width(560.0)
            .show(ctx, |ui| {
                ui.label(
                    egui::RichText::new("Confira o que será feito:")
                        .size(12.5)
                        .color(CINZA),
                );
                ui.add_space(6.0);
                for l in &c.linhas {
                    ui.add(egui::Label::new(egui::RichText::new(format!("• {l}")).size(12.0)).wrap());
                    ui.add_space(2.0);
                }
                if let Some(a) = &c.aviso {
                    ui.add_space(6.0);
                    aviso(ui, a, AMBAR);
                }
                ui.add_space(10.0);
                ui.horizontal(|ui| {
                    let texto = match c.acao {
                        AcaoConfirmada::Instalar => "CONFIRMAR INSTALAÇÃO",
                        AcaoConfirmada::Remover => "CONFIRMAR REMOÇÃO",
                    };
                    if ui
                        .add(
                            egui::Button::new(egui::RichText::new(texto).strong().size(13.0))
                                .fill(AZUL)
                                .min_size(egui::vec2(220.0, 36.0)),
                        )
                        .clicked()
                    {
                        confirmar = true;
                    }
                    if ui
                        .add(
                            egui::Button::new(egui::RichText::new("CANCELAR").size(13.0))
                                .fill(CARTAO_CLARO)
                                .min_size(egui::vec2(120.0, 36.0)),
                        )
                        .clicked()
                    {
                        cancelar = true;
                    }
                });
            });
        if cancelar {
            self.confirmacao = None;
        }
        if confirmar {
            let acao = self.confirmacao.as_ref().map(|c| c.acao);
            self.confirmacao = None;
            match acao {
                Some(AcaoConfirmada::Instalar) => {
                    if let Some(d) = self.deteccao.clone() {
                        self.executar_instalacao(d);
                    }
                }
                Some(AcaoConfirmada::Remover) => {
                    if let Some(d) = self.deteccao.clone() {
                        let remocao = Remocao {
                            mod_jogo: self.rem_mod,
                            launcher: self.rem_launcher,
                            atalho: self.rem_atalho,
                        };
                        self.executar_remocao(d, remocao);
                    }
                }
                None => {}
            }
        }
    }
}

impl eframe::App for App {
    fn ui(&mut self, ui: &mut egui::Ui, _frame: &mut eframe::Frame) {
        self.processar_mensagens();
        if self.analise_inicial && !self.ocupado() {
            self.analise_inicial = false;
            self.analisar();
        }
        if !self.estilo_aplicado {
            let mut visuals = egui::Visuals::dark();
            visuals.panel_fill = FUNDO;
            visuals.window_fill = CARTAO;
            visuals.window_stroke = egui::Stroke::new(1.0, BORDA);
            visuals.widgets.inactive.bg_fill = CARTAO_CLARO;
            visuals.widgets.hovered.bg_fill = egui::Color32::from_rgb(48, 68, 104);
            visuals.widgets.active.bg_fill = AZUL;
            visuals.selection.bg_fill = AZUL;
            visuals.override_text_color = Some(CREME);
            ui.ctx().set_visuals(visuals);
            ui.ctx().all_styles_mut(|style| {
                style.spacing.item_spacing = egui::vec2(8.0, 7.0);
                style.text_styles.insert(
                    egui::TextStyle::Body,
                    egui::FontId::new(13.0, egui::FontFamily::Proportional),
                );
                style.text_styles.insert(
                    egui::TextStyle::Button,
                    egui::FontId::new(13.0, egui::FontFamily::Proportional),
                );
            });
            self.estilo_aplicado = true;
        }
        if self.ocupado() {
            ui.ctx()
                .request_repaint_after(std::time::Duration::from_millis(80));
        }
        egui::Panel::bottom("acoes")
            .frame(
                egui::Frame::new()
                    .fill(egui::Color32::from_rgb(19, 29, 46))
                    .inner_margin(egui::Margin::symmetric(22, 10)),
            )
            .show(ui, |ui| {
                self.botao_instalar(ui);
            });
        egui::Frame::new()
            .fill(FUNDO)
            .inner_margin(egui::Margin::symmetric(22, 16))
            .show(ui, |ui| {
                egui::ScrollArea::vertical()
                    .auto_shrink([false, false])
                    .show(ui, |ui| {
                        self.cabecalho(ui);
                        if self.ocupado() {
                            self.tela_progresso(ui);
                        } else if self.resultado.is_some() {
                            self.tela_resultado(ui);
                        } else if self.remocao_mensagens.is_some() {
                            self.tela_remocao(ui);
                        } else {
                            self.tela_pasta(ui);
                            ui.add_space(8.0);
                            if self.deteccao.is_some() {
                                self.tela_status(ui);
                                self.tela_opcoes(ui);
                                self.manutencao(ui);
                                self.tela_detalhes(ui);
                            }
                        }
                        if self.erro.is_some() {
                            self.erro(ui);
                        }
                        ui.add_space(14.0);
                        ui.separator();
                        ui.add_space(4.0);
                        ui.label(
                            egui::RichText::new(
                                format!(
                                    "Instalador portátil v{} · gera tudo a partir da sua cópia legítima \
                                     do reNut · não inclui arquivos do jogo nem do reNut · tradução do \
                                     launcher 0.9.0 · tradução do jogo {} · licenças de terceiros em \
                                     LICENCAS-TERCEIROS.txt (Release)",
                                    env!("CARGO_PKG_VERSION"),
                                    instalador_renut_ptbr::modpack::VERSAO
                                ),
                            )
                            .size(10.0)
                            .color(CINZA),
                        );
                    });
            });
        self.confirmacao(ui.ctx());
    }
}

fn carregar() -> App {
    let mut app = App::new();
    let args: Vec<String> = std::env::args().collect();
    if let Some(i) = args.iter().position(|a| a == "--pasta") {
        if let Some(p) = args.get(i + 1) {
            app.caminho = p.clone();
            app.analise_inicial = true;
        }
    }
    app
}

fn main() {
    let opcoes = eframe::NativeOptions {
        renderer: eframe::Renderer::Glow,
        viewport: egui::ViewportBuilder::default()
            .with_inner_size([1060.0, 780.0])
            .with_min_inner_size([880.0, 620.0])
            .with_title("Instalador de Tradução PT-BR para reNut"),
        ..Default::default()
    };
    if let Err(e) = eframe::run_native(
        "Instalador de Tradução PT-BR para reNut",
        opcoes,
        Box::new(|_cc| Ok(Box::new(carregar()))),
    ) {
        // Sem console no build final: registra ao lado do executavel para diagnostico.
        if let Ok(mut f) = std::fs::File::create("instalador-renut-erro.txt") {
            use std::io::Write;
            let _ = writeln!(f, "Falha ao abrir a janela: {e}");
        }
    }
}

fn cartao(ui: &mut egui::Ui, conteudo: impl FnOnce(&mut egui::Ui)) {
    egui::Frame::new()
        .fill(CARTAO)
        .stroke(egui::Stroke::new(1.0, BORDA))
        .corner_radius(egui::CornerRadius::same(12))
        .inner_margin(egui::Margin::symmetric(16, 14))
        .show(ui, |ui| {
            ui.set_width(ui.available_width());
            conteudo(ui);
        });
}

fn cartao_claro(ui: &mut egui::Ui, conteudo: impl FnOnce(&mut egui::Ui)) {
    egui::Frame::new()
        .fill(CARTAO_CLARO)
        .stroke(egui::Stroke::new(1.0, BORDA))
        .corner_radius(egui::CornerRadius::same(8))
        .inner_margin(egui::Margin::symmetric(12, 10))
        .show(ui, |ui| {
            ui.set_width(ui.available_width());
            conteudo(ui);
        });
}

fn selo(ui: &mut egui::Ui, texto: &str, cor: egui::Color32) {
    egui::Frame::new()
        .fill(cor.gamma_multiply(0.18))
        .stroke(egui::Stroke::new(1.0, cor))
        .corner_radius(egui::CornerRadius::same(10))
        .inner_margin(egui::Margin::symmetric(8, 3))
        .show(ui, |ui| {
            ui.label(egui::RichText::new(texto).size(9.5).strong().color(cor));
        });
}

fn aviso(ui: &mut egui::Ui, texto: &str, cor: egui::Color32) {
    egui::Frame::new()
        .fill(cor.gamma_multiply(0.12))
        .stroke(egui::Stroke::new(1.0, cor.gamma_multiply(0.8)))
        .corner_radius(egui::CornerRadius::same(8))
        .inner_margin(egui::Margin::symmetric(10, 8))
        .show(ui, |ui| {
            ui.add(egui::Label::new(egui::RichText::new(texto).size(11.5).color(CREME)).wrap());
        });
}

fn opcao(
    ui: &mut egui::Ui,
    valor: &mut bool,
    disponivel: bool,
    titulo: &str,
    detalhe: &str,
    tecnico: &str,
) {
    egui::Frame::new()
        .fill(CARTAO_CLARO)
        .stroke(egui::Stroke::new(1.0, BORDA))
        .corner_radius(egui::CornerRadius::same(8))
        .inner_margin(egui::Margin::symmetric(12, 10))
        .show(ui, |ui| {
            ui.set_width(ui.available_width());
            ui.horizontal(|ui| {
                let mut marcado = *valor;
                let r = ui.add_enabled(
                    disponivel,
                    egui::Checkbox::new(&mut marcado, egui::RichText::new(titulo).size(13.5).strong()),
                );
                if r.changed() {
                    *valor = marcado;
                }
                ui.with_layout(egui::Layout::right_to_left(egui::Align::Center), |ui| {
                    ui.label(egui::RichText::new(tecnico).size(10.0).color(CINZA));
                });
            });
            ui.indent(titulo, |ui| {
                ui.add(egui::Label::new(egui::RichText::new(detalhe).size(11.0).color(CINZA)).wrap());
            });
        });
}

fn abrir_pasta(pasta: &std::path::Path) {
    let alvo = if pasta.is_dir() {
        pasta.to_path_buf()
    } else {
        pasta.parent().unwrap_or(pasta).to_path_buf()
    };
    let _ = std::process::Command::new("explorer").arg(alvo).spawn();
}

#[allow(dead_code)]
fn _nome_do_atalho() -> &'static str {
    atalho::NOME_ATALHO
}