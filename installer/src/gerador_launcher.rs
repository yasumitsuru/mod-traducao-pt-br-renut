//! Geracao LOCAL dos patches do launcher do reNut.
//!
//! Porte fiel de `launcher-patch/gerar_patch.py` (renut.exe) e `gerar_engine_patch.py`
//! (rexui.dll e rexhid.dll). O instalador nao carrega nenhum patch pronto: le os arquivos
//! legitimos do usuario, aplica o catalogo publico `launcher-patch/entradas_launcher.json`
//! (textos PT-BR e onde procurar os originais) e confere o resultado com os SHA-256 do
//! manifesto. Os bytes antigos de cada edicao vem da copia do proprio usuario.

use std::collections::{HashMap, HashSet};

use iced_x86::{Decoder, DecoderOptions, Instruction, Mnemonic, OpKind, Register};
use serde_json::Value;

const ENTRADAS: &str = include_str!("../../launcher-patch/entradas_launcher.json");
const SECTION_ALIGN: u64 = 0x1000;
const FILE_ALIGN: u64 = 0x200;

fn align_up(v: u64, a: u64) -> u64 {
    v.div_ceil(a) * a
}

fn rd16(d: &[u8], o: usize) -> u16 {
    u16::from_le_bytes([d[o], d[o + 1]])
}

fn rd32(d: &[u8], o: usize) -> u32 {
    u32::from_le_bytes([d[o], d[o + 1], d[o + 2], d[o + 3]])
}

fn rd64(d: &[u8], o: usize) -> u64 {
    let mut b = [0u8; 8];
    b.copy_from_slice(&d[o..o + 8]);
    u64::from_le_bytes(b)
}

struct Secao {
    nome: String,
    vsize: u64,
    vaddr: u64,
    rsize: u64,
    raw: u64,
}

struct Pe {
    pe: usize,
    opt: usize,
    image_base: u64,
    checksum_off: usize,
    nsec: u16,
    sec_tab: usize,
    secoes: Vec<Secao>,
    relocs: HashSet<u64>,
}

impl Pe {
    fn ler(d: &[u8]) -> Result<Pe, String> {
        if d.len() < 0x40 {
            return Err("Arquivo PE pequeno demais.".into());
        }
        let pe = rd32(d, 0x3C) as usize;
        if pe + 24 > d.len() {
            return Err("Cabeçalho PE fora do arquivo.".into());
        }
        let opt = pe + 24;
        let image_base = rd64(d, opt + 24);
        let nsec = rd16(d, pe + 6);
        let opt_size = rd16(d, pe + 20) as usize;
        let sec_tab = opt + opt_size;
        let mut secoes = Vec::new();
        for i in 0..nsec as usize {
            let off = sec_tab + 40 * i;
            if off + 40 > d.len() {
                return Err("Tabela de seções fora do arquivo.".into());
            }
            let bruto = &d[off..off + 8];
            let fim = bruto.iter().rposition(|&b| b != 0).map(|p| p + 1).unwrap_or(0);
            let nome: String = bruto[..fim].iter().map(|&b| b as char).collect();
            secoes.push(Secao {
                nome,
                vsize: rd32(d, off + 8) as u64,
                vaddr: rd32(d, off + 12) as u64,
                rsize: rd32(d, off + 16) as u64,
                raw: rd32(d, off + 20) as u64,
            });
        }
        let mut p = Pe {
            pe,
            opt,
            image_base,
            checksum_off: opt + 64,
            nsec,
            sec_tab,
            secoes,
            relocs: HashSet::new(),
        };
        p.relocs = p.ler_relocs(d);
        Ok(p)
    }

    fn ler_relocs(&self, data: &[u8]) -> HashSet<u64> {
        let mut out = HashSet::new();
        let Some(sec) = self.secoes.iter().find(|s| s.nome == ".reloc") else {
            return out;
        };
        let ini = sec.raw as usize;
        let fim = (ini + sec.rsize as usize).min(data.len());
        if ini >= fim {
            return out;
        }
        let d = &data[ini..fim];
        let mut i = 0usize;
        while i + 8 <= d.len() {
            let page = rd32(d, i) as u64;
            let size = rd32(d, i + 4) as usize;
            if size < 8 {
                break;
            }
            let mut j = 8;
            while j < size {
                if i + j + 2 > d.len() {
                    break;
                }
                let ent = rd16(d, i + j);
                if ent >> 12 == 10 {
                    out.insert(page + (ent & 0xFFF) as u64);
                }
                j += 2;
            }
            i += size;
        }
        out
    }

    fn off_to_rva(&self, off: u64) -> Option<u64> {
        self.secoes
            .iter()
            .find(|s| s.raw <= off && off < s.raw + s.rsize)
            .map(|s| s.vaddr + (off - s.raw))
    }

    fn rva_to_off(&self, rva: u64) -> Option<u64> {
        self.secoes
            .iter()
            .find(|s| s.vaddr <= rva && rva < s.vaddr + s.rsize.max(s.vsize))
            .map(|s| s.raw + (rva - s.vaddr))
    }
}

/// Checksum do jeito do gerador Python (soma de palavras de 16 bits com dobra, sem o tamanho).
fn checksum_pe(out: &mut [u8], checksum_off: usize) -> [u8; 4] {
    out[checksum_off..checksum_off + 4].copy_from_slice(&[0, 0, 0, 0]);
    let mut total: u64 = 0;
    let mut i = 0usize;
    while i < out.len() {
        let w = out[i] as u64 | if i + 1 < out.len() { (out[i + 1] as u64) << 8 } else { 0 };
        total += w;
        total = (total & 0xFFFF) + (total >> 16);
        i += 2;
    }
    total = (total & 0xFFFF) + (total >> 16);
    (total as u32).to_le_bytes()
}

struct CodeEdit {
    offset: u64,
    old: Vec<u8>,
    new: Vec<u8>,
}

struct Entrada {
    id: String,
    en: String,
    pt: String,
    utf16: bool,
    arquivo: String,
    offsets: Option<Vec<u64>>,
    ref_addrs: Option<Vec<u64>>,
    code_edits: Vec<CodeEdit>,
}

fn lista_u64(v: &Value) -> Option<Vec<u64>> {
    v.as_array()
        .map(|a| a.iter().filter_map(|x| x.as_u64()).collect())
}

fn carregar_entradas() -> Result<Vec<Entrada>, String> {
    let v: Value = serde_json::from_str(ENTRADAS)
        .map_err(|e| format!("Catálogo do launcher embutido inválido: {e}"))?;
    let lista = v.as_array().ok_or("Catálogo do launcher sem lista de entradas.")?;
    let mut out = Vec::with_capacity(lista.len());
    for e in lista {
        let mut code_edits = Vec::new();
        if let Some(ce) = e["code_edits"].as_array() {
            for c in ce {
                code_edits.push(CodeEdit {
                    offset: c["offset"].as_u64().ok_or("code_edit sem offset")?,
                    old: crate::patch::decodificar_base64(c["old"].as_str().unwrap_or(""))?,
                    new: crate::patch::decodificar_base64(c["new"].as_str().unwrap_or(""))?,
                });
            }
        }
        out.push(Entrada {
            id: e["id"].as_str().unwrap_or("").to_string(),
            en: e["en"].as_str().ok_or("entrada sem en")?.to_string(),
            pt: e["pt"].as_str().ok_or("entrada sem pt")?.to_string(),
            utf16: e["encoding"].as_str() == Some("utf-16le"),
            arquivo: e["file"].as_str().unwrap_or("renut.exe").to_string(),
            offsets: lista_u64(&e["offsets"]),
            ref_addrs: lista_u64(&e["ref_addrs"]),
            code_edits,
        });
    }
    Ok(out)
}

fn codificar(texto: &str, utf16: bool) -> Vec<u8> {
    if utf16 {
        texto.encode_utf16().flat_map(|u| u.to_le_bytes()).collect()
    } else {
        texto.as_bytes().to_vec()
    }
}

fn completar(texto: &[u8], total: usize, utf16: bool) -> Vec<u8> {
    if total <= texto.len() {
        return texto.to_vec();
    }
    let fill: &[u8] = if utf16 { &[0x20, 0x00] } else { &[0x20] };
    let mut out = texto.to_vec();
    for _ in 0..(total - texto.len()) / fill.len() {
        out.extend_from_slice(fill);
    }
    out
}

/// Todas as posicoes de `agulha` em `dados`, inclusive sobrepostas (como `bytes.find` em laco).
fn todas(dados: &[u8], agulha: &[u8]) -> Vec<u64> {
    let mut out = Vec::new();
    if agulha.is_empty() {
        return out;
    }
    let busca = memchr::memmem::Finder::new(agulha);
    let mut ini = 0usize;
    while ini <= dados.len() {
        match busca.find(&dados[ini..]) {
            Some(p) => {
                out.push((ini + p) as u64);
                ini += p + 1;
            }
            None => break,
        }
    }
    out
}

#[derive(Clone)]
struct RipRef {
    addr: u64,
    disp_off: u64,
    len: u64,
}

#[derive(Clone)]
struct ImmSite {
    addr: u64,
    file_off: Option<u64>,
}

#[derive(Clone)]
struct ImmCand {
    window: usize,
    size: usize,
    addr: u64,
    file_off: Option<u64>,
}

enum Ref {
    Rip(RipRef),
    Ptr { file_off: u64, reloc: bool },
}

struct Edicao {
    offset: u64,
    old: Vec<u8>,
    new: Vec<u8>,
    prio: i64,
}

enum ItemReloc {
    Entrada,
    Ptr { indice: usize, file_off: u64 },
    Rip { indice: usize, r: RipRef },
}

/// Mapa que preserva a ordem de insercao, como o `dict` do Python (update mantem a posicao).
struct Ordenado {
    chaves: Vec<Option<u64>>,
    valores: HashMap<Option<u64>, ImmCand>,
}

impl Ordenado {
    fn novo() -> Self {
        Self { chaves: Vec::new(), valores: HashMap::new() }
    }
    fn contem(&self, k: &Option<u64>) -> bool {
        self.valores.contains_key(k)
    }
    fn inserir(&mut self, k: Option<u64>, v: ImmCand) {
        if !self.valores.contains_key(&k) {
            self.chaves.push(k);
        }
        self.valores.insert(k, v);
    }
    fn valores_em_ordem(&self) -> Vec<ImmCand> {
        self.chaves.iter().map(|k| self.valores[k].clone()).collect()
    }
}

fn mesclar(covered: &mut Vec<(usize, usize)>) {
    covered.sort();
    let mut merged: Vec<(usize, usize)> = Vec::new();
    for &(a, b) in covered.iter() {
        if let Some(ultimo) = merged.last_mut() {
            if a <= ultimo.1 {
                ultimo.1 = ultimo.1.max(b);
                continue;
            }
        }
        merged.push((a, b));
    }
    *covered = merged;
}

fn achar_grupos(n: usize, sites: &[ImmCand]) -> Vec<ImmCand> {
    let mut found = Ordenado::novo();
    for anchor in sites {
        if anchor.size < 4 || !(anchor.window == 0 || anchor.window + anchor.size == n) {
            continue;
        }
        let mut chosen = Ordenado::novo();
        chosen.inserir(anchor.file_off, anchor.clone());
        let mut covered = vec![(anchor.window, anchor.window + anchor.size)];
        let mut ordered: Vec<&ImmCand> = sites.iter().collect();
        ordered.sort_by_key(|x| x.addr.abs_diff(anchor.addr));
        for cand in ordered {
            if cand.addr.abs_diff(anchor.addr) > 96 {
                break;
            }
            if chosen.contem(&cand.file_off) {
                continue;
            }
            let (cs, ce) = (cand.window, cand.window + cand.size);
            if ce > n {
                continue;
            }
            if covered.iter().any(|&(a, b)| cs == a && ce == b) {
                continue;
            }
            if covered.iter().any(|&(a, b)| cs <= b && a <= ce) {
                chosen.inserir(cand.file_off, cand.clone());
                covered.push((cs, ce));
                mesclar(&mut covered);
            }
            if covered == [(0, n)] {
                break;
            }
        }
        if covered == [(0, n)] {
            for k in &chosen.chaves {
                found.inserir(*k, chosen.valores[k].clone());
            }
        }
    }
    found.valores_em_ordem()
}

fn eh_desvio(m: Mnemonic) -> bool {
    let nome = format!("{m:?}").to_lowercase();
    nome.starts_with('j') || nome.starts_with("call") || nome.starts_with("loop")
}

fn eh_imediato(k: OpKind) -> bool {
    matches!(
        k,
        OpKind::Immediate8
            | OpKind::Immediate8_2nd
            | OpKind::Immediate16
            | OpKind::Immediate32
            | OpKind::Immediate64
            | OpKind::Immediate8to16
            | OpKind::Immediate8to32
            | OpKind::Immediate8to64
            | OpKind::Immediate32to64
    )
}

/// Gera o `renut.ptbr.exe` a partir do `renut.exe` do usuario. Devolve os bytes de saida.
pub fn gerar_executavel(data: &[u8]) -> Result<Vec<u8>, String> {
    let pe = Pe::ler(data)?;
    let text = pe
        .secoes
        .iter()
        .find(|s| s.nome == ".text")
        .ok_or("O renut.exe não tem seção .text.")?;
    let ini = text.raw as usize;
    let fim = (ini + text.rsize as usize).min(data.len());
    let code = &data[ini..fim];
    let code_rva = text.vaddr;

    let mut rip_refs: HashMap<u64, Vec<RipRef>> = HashMap::new();
    let mut imm_by_bytes: HashMap<Vec<u8>, Vec<ImmSite>> = HashMap::new();
    let mut dec = Decoder::with_ip(64, code, code_rva, DecoderOptions::NONE);
    let mut ins = Instruction::default();
    while dec.can_decode() {
        dec.decode_out(&mut ins);
        if ins.is_invalid() {
            // O capstone para no primeiro byte invalido; o .text da versao suportada nao tem nenhum.
            break;
        }
        let addr = ins.ip();
        let len = ins.len() as u64;
        let rel = (addr - code_rva) as usize;
        let bytes = &code[rel..rel + len as usize];
        let mnem = ins.mnemonic();
        for i in 0..ins.op_count() {
            let k = ins.op_kind(i);
            if k == OpKind::Memory {
                if ins.memory_base() == Register::RIP {
                    let alvo = ins.ip_rel_memory_address();
                    rip_refs.entry(alvo).or_default().push(RipRef {
                        addr,
                        disp_off: len - 4,
                        len,
                    });
                }
            } else if eh_imediato(k) {
                if eh_desvio(mnem) {
                    continue;
                }
                let val = ins.immediate(i);
                for size in [1usize, 2, 4, 8] {
                    let raw: Vec<u8> = if size == 8 {
                        if mnem != Mnemonic::Mov {
                            continue;
                        }
                        val.to_le_bytes().to_vec()
                    } else {
                        let max = (1u64 << (size * 8)) - 1;
                        if val > max {
                            continue;
                        }
                        (val & max).to_le_bytes()[..size].to_vec()
                    };
                    if raw.iter().all(|&b| b == 0) {
                        continue;
                    }
                    if bytes.len() < size {
                        continue;
                    }
                    let pos = (0..=bytes.len() - size).rev().find(|&p| bytes[p..p + size] == raw[..]);
                    let Some(pos) = pos else { continue };
                    imm_by_bytes.entry(raw).or_default().push(ImmSite {
                        addr,
                        file_off: pe.rva_to_off(addr + pos as u64),
                    });
                }
            }
        }
    }

    let entradas = carregar_entradas()?;
    let mut edits: Vec<Edicao> = Vec::new();
    let mut reloc: Vec<ItemReloc> = Vec::new();
    let mut reloc_textos: Vec<(Vec<u8>, bool)> = Vec::new();
    let mut imm_claims: HashMap<u64, (usize, Vec<u8>)> = HashMap::new();

    fn add(edits: &mut Vec<Edicao>, offset: u64, old: Vec<u8>, new: Vec<u8>, prio: i64) -> Result<(), String> {
        if old.len() != new.len() {
            return Err(format!("edição com tamanhos diferentes em {offset:#x}"));
        }
        if old != new {
            edits.push(Edicao { offset, old, new, prio });
        }
        Ok(())
    }

    for e in entradas.iter().filter(|e| e.arquivo == "renut.exe") {
        let nb = codificar(&e.en, e.utf16);
        let pb = codificar(&e.pt, e.utf16);
        if !e.code_edits.is_empty() {
            for ce in &e.code_edits {
                add(&mut edits, ce.offset, ce.old.clone(), ce.new.clone(), 20000)?;
            }
            continue;
        }
        let term: &[u8] = if e.utf16 { &[0, 0] } else { &[0] };
        struct Occ {
            off: u64,
            rva: u64,
        }
        let mut occ: Vec<Occ> = Vec::new();
        for off in todas(data, &nb) {
            let Some(r) = pe.off_to_rva(off) else { continue };
            let a_ini = (off as usize + nb.len()).min(data.len());
            let a_fim = (off as usize + nb.len() + term.len()).min(data.len());
            if &data[a_ini..a_fim] != term {
                continue;
            }
            if let Some(permitidos) = &e.offsets {
                if !permitidos.contains(&off) {
                    continue;
                }
            }
            occ.push(Occ { off, rva: r });
        }
        let mut refs: Vec<Ref> = Vec::new();
        for o in &occ {
            if let Some(lista) = rip_refs.get(&o.rva) {
                for x in lista {
                    refs.push(Ref::Rip(x.clone()));
                }
            }
            let va = pe.image_base + o.rva;
            for q in todas(data, &va.to_le_bytes()) {
                let reloc = pe.off_to_rva(q).is_some_and(|r| pe.relocs.contains(&r));
                refs.push(Ref::Ptr { file_off: q, reloc });
            }
        }
        if let Some(addrs) = &e.ref_addrs {
            refs.retain(|r| matches!(r, Ref::Rip(x) if addrs.contains(&x.addr)));
        }
        let mut imms: Vec<ImmCand> = Vec::new();
        if !e.utf16 {
            for i in 0..nb.len() {
                for size in [8usize, 4, 2] {
                    if i + size > nb.len() {
                        continue;
                    }
                    let raw = &nb[i..i + size];
                    if raw.iter().all(|&b| b == 0) {
                        continue;
                    }
                    if let Some(sites) = imm_by_bytes.get(raw) {
                        for s in sites {
                            imms.push(ImmCand { window: i, size, addr: s.addr, file_off: s.file_off });
                        }
                    }
                }
            }
            let mut vistos: HashSet<(Option<u64>, usize, usize)> = HashSet::new();
            imms.retain(|x| vistos.insert((x.file_off, x.window, x.size)));
            imms = achar_grupos(nb.len(), &imms);
        }
        let cabe = pb.len() <= nb.len();
        let tem_imm = !imms.is_empty();
        let refs_seguras = !refs.is_empty()
            && refs.iter().all(|r| match r {
                Ref::Ptr { reloc, .. } => *reloc,
                Ref::Rip(_) => true,
            });
        if occ.is_empty() && imms.is_empty() {
            continue; // ausente do binario
        }
        if cabe {
            let padded = completar(&pb, nb.len(), e.utf16);
            for o in &occ {
                add(&mut edits, o.off, nb.clone(), padded.clone(), nb.len() as i64)?;
            }
            for x in &imms {
                let Some(fo) = x.file_off else { continue };
                if x.window + x.size > padded.len() {
                    continue;
                }
                let new = padded[x.window..x.window + x.size].to_vec();
                let fo_u = fo as usize;
                if fo_u + x.size > data.len() {
                    continue;
                }
                let old = &data[fo_u..fo_u + x.size];
                if old != &new[..] && new.len() == x.size && old.iter().all(|&c| (32..127).contains(&c)) {
                    let substituir = match imm_claims.get(&fo) {
                        None => true,
                        Some((tam, _)) => nb.len() > *tam,
                    };
                    if substituir {
                        imm_claims.insert(fo, (nb.len(), new));
                    }
                }
            }
        } else if refs_seguras && !tem_imm {
            let indice = reloc_textos.len();
            reloc_textos.push((pb.clone(), e.utf16));
            reloc.push(ItemReloc::Entrada);
            for r in refs {
                match r {
                    Ref::Ptr { file_off, .. } => reloc.push(ItemReloc::Ptr { indice, file_off }),
                    Ref::Rip(x) => reloc.push(ItemReloc::Rip { indice, r: x }),
                }
            }
        }
        // bloqueadas: nenhuma edicao (como no gerador Python)
        let _ = &e.id;
    }

    let mut claims: Vec<(u64, Vec<u8>)> = imm_claims.into_iter().map(|(k, (_, v))| (k, v)).collect();
    claims.sort_by_key(|c| c.0);
    for (off, new) in claims {
        let o = off as usize;
        let old = data[o..o + new.len()].to_vec();
        add(&mut edits, off, old, new, 1)?;
    }

    let tem_secao = !reloc_textos.is_empty();
    if tem_secao {
        let mut blob: Vec<u8> = Vec::new();
        let mut new_rvas: Vec<u64> = Vec::new();
        for (pb, utf16) in &reloc_textos {
            while blob.len() % 16 != 0 {
                blob.push(0);
            }
            new_rvas.push(blob.len() as u64);
            blob.extend_from_slice(pb);
            blob.extend_from_slice(if *utf16 { &[0, 0] } else { &[0] });
        }
        let mut last = &pe.secoes[0];
        for s in &pe.secoes {
            if s.vaddr > last.vaddr {
                last = s;
            }
        }
        let new_rva = align_up(last.vaddr + last.vsize.max(last.rsize), SECTION_ALIGN);
        let new_raw = align_up(data.len() as u64, FILE_ALIGN);
        let vsize = blob.len() as u64;
        let rsize = align_up(vsize, FILE_ALIGN);
        let header_off = pe.sec_tab + 40 * pe.nsec as usize;
        let mut header = b".ptbr\0\0\0".to_vec();
        for v in [vsize as u32, new_rva as u32, rsize as u32, new_raw as u32] {
            header.extend_from_slice(&v.to_le_bytes());
        }
        header.extend_from_slice(&[0u8; 12]);
        header.extend_from_slice(&0x4000_0040u32.to_le_bytes());
        edits.push(Edicao {
            offset: header_off as u64,
            old: data[header_off..header_off + 40].to_vec(),
            new: header,
            prio: 10000,
        });
        let nsec_off = pe.pe + 6;
        edits.push(Edicao {
            offset: nsec_off as u64,
            old: data[nsec_off..nsec_off + 2].to_vec(),
            new: (pe.nsec + 1).to_le_bytes().to_vec(),
            prio: 10000,
        });
        let size_img = align_up(new_rva + vsize, SECTION_ALIGN);
        edits.push(Edicao {
            offset: (pe.opt + 56) as u64,
            old: data[pe.opt + 56..pe.opt + 60].to_vec(),
            new: (size_img as u32).to_le_bytes().to_vec(),
            prio: 10000,
        });
        let pad = (new_raw - data.len() as u64) as usize;
        let mut body = vec![0u8; pad];
        body.extend_from_slice(&blob);
        body.extend(std::iter::repeat_n(0u8, (rsize - vsize) as usize));
        edits.push(Edicao { offset: data.len() as u64, old: Vec::new(), new: body, prio: 10000 });
        for item in &reloc {
            match item {
                ItemReloc::Entrada => {}
                ItemReloc::Ptr { indice, file_off } => {
                    let alvo = new_rva + new_rvas[*indice];
                    let o = *file_off as usize;
                    edits.push(Edicao {
                        offset: *file_off,
                        old: data[o..o + 8].to_vec(),
                        new: (pe.image_base + alvo).to_le_bytes().to_vec(),
                        prio: 10000,
                    });
                }
                ItemReloc::Rip { indice, r } => {
                    let alvo = new_rva + new_rvas[*indice];
                    let insn_off = pe.rva_to_off(r.addr).ok_or("instrução fora das seções")?;
                    let disp_off = (insn_off + r.disp_off) as usize;
                    let new_disp = (alvo as i64 - (r.addr + r.len) as i64) as i32;
                    edits.push(Edicao {
                        offset: disp_off as u64,
                        old: data[disp_off..disp_off + 4].to_vec(),
                        new: new_disp.to_le_bytes().to_vec(),
                        prio: 10000,
                    });
                }
            }
        }
    }

    // Mesma selecao do gerador: prioridade maior primeiro, sem sobreposicao.
    let mut ordem: Vec<usize> = (0..edits.len()).collect();
    ordem.sort_by_key(|&i| (-edits[i].prio, edits[i].offset));
    let mut aceitas: Vec<usize> = Vec::new();
    for i in ordem {
        let e = &edits[i];
        let fim = e.offset + e.old.len() as u64;
        if aceitas.iter().any(|&j| {
            let a = &edits[j];
            e.offset < a.offset + a.old.len() as u64 && a.offset < fim
        }) {
            continue;
        }
        aceitas.push(i);
    }
    aceitas.sort_by_key(|&i| edits[i].offset);
    for par in aceitas.windows(2) {
        let (a, b) = (&edits[par[0]], &edits[par[1]]);
        if a.offset + a.old.len() as u64 > b.offset {
            return Err(format!("edições sobrepostas em {:#x}", b.offset));
        }
    }

    let mut out = data.to_vec();
    for &i in &aceitas {
        let e = &edits[i];
        let off = e.offset as usize;
        if !e.old.is_empty() && out[off..off + e.old.len()] != e.old[..] {
            return Err(format!("bytes antigos não conferem em {off:#x}"));
        }
        if off + e.new.len() > out.len() {
            out.resize(off + e.new.len(), 0);
        }
        out[off..off + e.new.len()].copy_from_slice(&e.new);
    }
    if tem_secao {
        let csum = checksum_pe(&mut out, pe.checksum_off);
        out[pe.checksum_off..pe.checksum_off + 4].copy_from_slice(&csum);
    }
    Ok(out)
}

/// Gera a copia traduzida de uma DLL do motor (rexui.dll ou rexhid.dll).
pub fn gerar_dll(arquivo: &str, data: &[u8]) -> Result<Vec<u8>, String> {
    let entradas = carregar_entradas()?;
    let e = entradas
        .iter()
        .find(|e| e.arquivo.eq_ignore_ascii_case(arquivo))
        .ok_or_else(|| format!("O catálogo não tem texto para {arquivo}."))?;
    let nb = e.en.as_bytes();
    let pb = e.pt.as_bytes();
    if pb.len() > nb.len() {
        return Err(format!("{}: a tradução não cabe no espaço original.", e.id));
    }
    let mut alvo = nb.to_vec();
    alvo.push(0);
    let achados = todas(data, &alvo);
    if achados.len() != 1 {
        return Err(format!("{}: texto original não encontrado uma única vez em {arquivo}.", e.id));
    }
    let off = achados[0] as usize;
    let mut new = pb.to_vec();
    new.extend(std::iter::repeat_n(b' ', nb.len() - pb.len()));
    new.push(0);
    let mut out = data.to_vec();
    out[off..off + nb.len() + 1].copy_from_slice(&new);
    let pe = Pe::ler(data)?;
    let csum = checksum_pe(&mut out, pe.checksum_off);
    out[pe.checksum_off..pe.checksum_off + 4].copy_from_slice(&csum);
    Ok(out)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn catalogo_publico_embutido() {
        let e = carregar_entradas().unwrap();
        assert_eq!(e.len(), 227);
        assert_eq!(e.iter().filter(|x| x.arquivo == "renut.exe").count(), 225);
        assert!(e.iter().any(|x| x.arquivo == "rexui.dll"));
        assert!(e.iter().any(|x| x.arquivo == "rexhid.dll"));
    }

    #[test]
    fn grupos_de_imediatos_cobrem_o_texto() {
        let c = |w, s, a, f| ImmCand { window: w, size: s, addr: a, file_off: Some(f) };
        let sites = vec![c(0, 4, 100, 10), c(4, 4, 110, 20), c(2, 4, 500, 30)];
        let g = achar_grupos(8, &sites);
        let offs: Vec<_> = g.iter().map(|x| x.file_off.unwrap()).collect();
        assert_eq!(offs, vec![10, 20]);
    }

    #[test]
    fn completa_com_espacos_no_encoding_certo() {
        assert_eq!(completar(b"ab", 4, false), b"ab  ");
        assert_eq!(completar(&[0x61, 0], 6, true), vec![0x61, 0, 0x20, 0, 0x20, 0]);
    }
}
