//! LSBL — a tabela de textos dentro da secao `.data` de um loctext.
//!
//! Porte fiel de `tools/nbptbr/lsbl.py`. As tabelas de chaves, comentarios e indice sao
//! preservadas byte a byte; so a tabela de frases e reescrita, com deslocamentos recalculados.

use crate::caff::{ALINHAMENTO_SECAO, alinhar};

pub const MAGICO: &[u8] = b"LSBL";
pub const TAM_CAB_LSBL: usize = 0x1C;
pub const HASH_TERMINAL: u16 = 0xFFFF;

fn exigir(condicao: bool, mensagem: &str) -> Result<(), String> {
    if condicao {
        Ok(())
    } else {
        Err(mensagem.to_string())
    }
}

fn u16_le(b: &[u8], o: usize) -> Result<u16, String> {
    let f = b.get(o..o + 2).ok_or("LSBL truncado.")?;
    Ok(u16::from_le_bytes([f[0], f[1]]))
}

fn u32_le(b: &[u8], o: usize) -> Result<u32, String> {
    let f = b.get(o..o + 4).ok_or("LSBL truncado.")?;
    Ok(u32::from_le_bytes([f[0], f[1], f[2], f[3]]))
}

fn u16_be(b: &[u8], o: usize) -> Result<u16, String> {
    let f = b.get(o..o + 2).ok_or("Secao de texto truncada.")?;
    Ok(u16::from_be_bytes([f[0], f[1]]))
}

fn u32_be(b: &[u8], o: usize) -> Result<u32, String> {
    let f = b.get(o..o + 4).ok_or("Secao de texto truncada.")?;
    Ok(u32::from_be_bytes([f[0], f[1], f[2], f[3]]))
}

#[derive(Clone, Debug)]
pub struct Chave {
    pub hash: u16,
    pub indice: u16,
    pub nome: String,
}

#[derive(Clone)]
pub struct AssetTexto {
    pub bloco_colisoes: Vec<u8>,
    pub n_colisoes: u16,
    pub hashes: Vec<u16>,
    pub textos: Vec<String>,
    pub tabela_chaves: Vec<u8>,
    pub tabela_comentarios: Option<Vec<u8>>,
    pub tabela_indice: Option<Vec<u8>>,
}

impl AssetTexto {
    pub fn chaves(&self) -> Result<Vec<Chave>, String> {
        ler_chaves(&self.tabela_chaves)
    }

    pub fn com_textos(&self, textos: Vec<String>) -> Result<AssetTexto, String> {
        exigir(
            textos.len() == self.textos.len(),
            "Quantidade de textos diferente da original.",
        )?;
        for t in &textos {
            exigir(!t.contains('\0'), "Texto não pode conter caractere nulo.")?;
        }
        let mut novo = self.clone();
        novo.textos = textos;
        Ok(novo)
    }
}

fn ler_chaves(t: &[u8]) -> Result<Vec<Chave>, String> {
    let tam = u32_le(t, 0)? as usize;
    let n = u32_le(t, 4)? as usize;
    exigir(tam == t.len(), "Tamanho da tabela de chaves não confere.")?;
    let inicio_nomes = 8 + 8 * n;
    exigir(inicio_nomes <= t.len(), "Tabela de chaves truncada.")?;
    let nomes = &t[inicio_nomes..];
    exigir(
        nomes.iter().filter(|x| **x == 0).count() == n && nomes.ends_with(b"\x00"),
        "Nomes de chave da tabela não terminam em nulo.",
    )?;
    let mut out = Vec::with_capacity(n);
    for i in 0..n {
        let h = u16_le(t, 8 + 8 * i)?;
        let idx = u16_le(t, 10 + 8 * i)?;
        let off = u32_le(t, 12 + 8 * i)? as usize;
        let fim = nomes
            .get(off..)
            .ok_or("Deslocamento de nome de chave fora da tabela.")?
            .iter()
            .position(|x| *x == 0)
            .ok_or("Nome de chave sem terminador.")?
            + off;
        out.push(Chave {
            hash: h,
            indice: idx,
            nome: String::from_utf8_lossy(&nomes[off..fim]).to_string(),
        });
    }
    Ok(out)
}

fn validar_colisoes(bloco: &[u8], n: u16) -> Result<(), String> {
    for i in 0..n as usize {
        let off = u32_be(bloco, 8 * i)? as usize;
        let _h_orig = u16_be(bloco, 8 * i + 4)?;
        let _h_sub = u16_be(bloco, 8 * i + 6)?;
        let rel = off
            .checked_sub(12)
            .ok_or("Deslocamento de colisão inválido.")?;
        exigir(
            bloco.get(rel..).is_some_and(|r| r.contains(&0)),
            "Nome de colisao sem terminador.",
        )?;
    }
    Ok(())
}

fn tabela(lsbl: &[u8], desl: usize) -> Result<&[u8], String> {
    let tam = u32_le(lsbl, desl)? as usize;
    lsbl.get(desl..desl + tam)
        .ok_or_else(|| "Tabela LSBL ultrapassa o arquivo.".to_string())
}

pub fn ler(secao: &[u8]) -> Result<AssetTexto, String> {
    exigir(secao.len() >= 12, "Secao de texto curta demais.")?;
    let desl_lsbl = u32_be(secao, 0)? as usize;
    let desl_col = u32_be(secao, 4)? as usize;
    let n_col = u16_be(secao, 8)?;
    let zero = u16_be(secao, 10)?;
    exigir(zero == 0, "Preâmbulo da seção: campo reservado diferente de zero.")?;
    if n_col == 0 {
        exigir(
            desl_col == 0 && desl_lsbl == 12,
            "Preambulo sem colisoes com deslocamentos inesperados.",
        )?;
    } else {
        exigir(
            desl_col == 12 && desl_lsbl > 12 + 8 * n_col as usize,
            "Preâmbulo com colisões inválido.",
        )?;
    }
    exigir(desl_lsbl <= secao.len(), "LSBL fora da seção.")?;
    let bloco_col = secao[12..desl_lsbl].to_vec();
    if n_col != 0 {
        validar_colisoes(&bloco_col, n_col)?;
    }

    let l = desl_lsbl;
    exigir(secao.get(l..l + 4) == Some(MAGICO), "Assinatura LSBL ausente.")?;
    let tam_cab = u32_le(secao, l + 4)? as usize;
    let quatro = u32_le(secao, l + 8)?;
    let d_frases = u32_le(secao, l + 12)? as usize;
    let d_chaves = u32_le(secao, l + 16)? as usize;
    let d_coment = u32_le(secao, l + 20)? as usize;
    let d_indice = u32_le(secao, l + 24)? as usize;
    exigir(
        tam_cab == TAM_CAB_LSBL && quatro == 4 && d_frases == TAM_CAB_LSBL,
        "Cabecalho LSBL inesperado.",
    )?;

    let resto = &secao[l..];
    let t_frases = tabela(resto, d_frases)?;
    exigir(
        d_frases + t_frases.len() == d_chaves,
        "Tabela de chaves não segue a de frases.",
    )?;
    let t_chaves = tabela(resto, d_chaves)?;
    let mut fim = d_chaves + t_chaves.len();
    let mut t_coment = None;
    if d_coment != 0 {
        exigir(d_coment == fim, "Tabela de comentarios fora de ordem.")?;
        let t = tabela(resto, d_coment)?;
        fim = d_coment + t.len();
        t_coment = Some(t.to_vec());
    }
    let mut t_indice = None;
    if d_indice != 0 {
        exigir(d_indice == fim, "Tabela de indice fora de ordem.")?;
        let t = tabela(resto, d_indice)?;
        fim = d_indice + t.len();
        t_indice = Some(t.to_vec());
    }

    let esperado = alinhar(l + fim, ALINHAMENTO_SECAO);
    exigir(
        secao.len() == esperado,
        "Tamanho da seção diferente do alinhamento de 16.",
    )?;
    exigir(
        secao[l + fim..].iter().all(|x| *x == 0),
        "Preenchimento final da seção não é zero.",
    )?;

    let (hashes, textos) = ler_frases(t_frases)?;
    let chaves = ler_chaves(t_chaves)?;
    exigir(
        chaves.iter().map(|c| c.hash).collect::<Vec<_>>() == hashes,
        "Hashes das tabelas de frases e de chaves divergem.",
    )?;
    let mut indices: Vec<u16> = chaves.iter().map(|c| c.indice).collect();
    indices.sort_unstable();
    exigir(
        indices == (1..=chaves.len() as u16).collect::<Vec<_>>(),
        "Indices de chave invalidos.",
    )?;

    Ok(AssetTexto {
        bloco_colisoes: bloco_col,
        n_colisoes: n_col,
        hashes,
        textos,
        tabela_chaves: t_chaves.to_vec(),
        tabela_comentarios: t_coment,
        tabela_indice: t_indice,
    })
}

fn ler_frases(t: &[u8]) -> Result<(Vec<u16>, Vec<String>), String> {
    let tam = u32_le(t, 0)? as usize;
    let n = u32_le(t, 4)? as usize;
    exigir(n <= 1_000_000, "Numero de frases absurdo.")?;
    let mut hashes = Vec::with_capacity(n);
    let mut deslocamentos = Vec::with_capacity(n + 1);
    for i in 0..=n {
        hashes.push(u16_le(t, 8 + 6 * i)?);
        deslocamentos.push(u32_le(t, 10 + 6 * i)? as usize);
    }
    let terminal = hashes.pop().ok_or("Tabela de frases vazia.")?;
    exigir(terminal == HASH_TERMINAL, "Entrada terminal da tabela de frases ausente.")?;
    let mut ordenados = hashes.clone();
    ordenados.sort_unstable();
    ordenados.dedup();
    exigir(
        ordenados == hashes,
        "Hashes de frase fora de ordem ou repetidos.",
    )?;
    let inicio = 8 + 6 * (n + 1);
    let total = deslocamentos[n];
    exigir(
        tam == inicio + 2 * total + 2,
        "Tamanho da tabela de frases não confere.",
    )?;
    exigir(
        t.get(inicio + 2 * total..inicio + 2 * total + 2) == Some(&[0, 0]),
        "Final da tabela de frases não é u16 zero.",
    )?;
    let mut textos = Vec::with_capacity(n);
    for i in 0..n {
        let (a, z) = (deslocamentos[i], deslocamentos[i + 1]);
        exigir(a < z, "Deslocamentos de frase não são crescentes.")?;
        let bruto = t
            .get(inicio + 2 * a..inicio + 2 * z)
            .ok_or("Frase fora da tabela.")?;
        exigir(
            bruto.len() >= 2 && bruto[bruto.len() - 2..] == [0, 0],
            "Frase sem terminador nulo.",
        )?;
        let unidades: Vec<u16> = bruto[..bruto.len() - 2]
            .chunks_exact(2)
            .map(|p| u16::from_le_bytes([p[0], p[1]]))
            .collect();
        let texto = String::from_utf16(&unidades)
            .map_err(|_| "Texto do jogo com surrogate UTF-16 inválido.".to_string())?;
        exigir(!texto.contains('\0'), "Frase com nulo interno.")?;
        textos.push(texto);
    }
    Ok((hashes, textos))
}

fn escrever_frases(hashes: &[u16], textos: &[String]) -> Vec<u8> {
    let n = hashes.len();
    let mut corpo: Vec<u8> = Vec::new();
    let mut entradas: Vec<u8> = Vec::with_capacity(6 * (n + 1));
    let mut unidades: u32 = 0;
    for (h, txt) in hashes.iter().zip(textos.iter()) {
        entradas.extend_from_slice(&h.to_le_bytes());
        entradas.extend_from_slice(&unidades.to_le_bytes());
        for u in txt.encode_utf16() {
            corpo.extend_from_slice(&u.to_le_bytes());
        }
        corpo.extend_from_slice(&[0, 0]);
        unidades += txt.encode_utf16().count() as u32 + 1;
    }
    entradas.extend_from_slice(&HASH_TERMINAL.to_le_bytes());
    entradas.extend_from_slice(&unidades.to_le_bytes());
    let tam = 8 + entradas.len() + corpo.len() + 2;
    let mut saida = Vec::with_capacity(tam);
    saida.extend_from_slice(&(tam as u32).to_le_bytes());
    saida.extend_from_slice(&(n as u32).to_le_bytes());
    saida.extend_from_slice(&entradas);
    saida.extend_from_slice(&corpo);
    saida.extend_from_slice(&[0, 0]);
    saida
}

pub fn escrever(a: &AssetTexto) -> Result<Vec<u8>, String> {
    let t_frases = escrever_frases(&a.hashes, &a.textos);
    let d_chaves = TAM_CAB_LSBL + t_frases.len();
    let mut fim = d_chaves + a.tabela_chaves.len();
    let mut d_coment = 0usize;
    if let Some(t) = &a.tabela_comentarios {
        d_coment = fim;
        fim += t.len();
    }
    let mut d_indice = 0usize;
    if let Some(t) = &a.tabela_indice {
        d_indice = fim;
        fim += t.len();
    }
    let mut lsbl = Vec::with_capacity(fim);
    lsbl.extend_from_slice(MAGICO);
    for v in [
        TAM_CAB_LSBL as u32,
        4,
        TAM_CAB_LSBL as u32,
        d_chaves as u32,
        d_coment as u32,
        d_indice as u32,
    ] {
        lsbl.extend_from_slice(&v.to_le_bytes());
    }
    lsbl.extend_from_slice(&t_frases);
    lsbl.extend_from_slice(&a.tabela_chaves);
    if let Some(t) = &a.tabela_comentarios {
        lsbl.extend_from_slice(t);
    }
    if let Some(t) = &a.tabela_indice {
        lsbl.extend_from_slice(t);
    }

    let desl_lsbl = 12 + a.bloco_colisoes.len();
    let desl_col = if a.n_colisoes != 0 { 12 } else { 0 };
    let mut corpo = Vec::with_capacity(desl_lsbl + lsbl.len());
    corpo.extend_from_slice(&(desl_lsbl as u32).to_be_bytes());
    corpo.extend_from_slice(&(desl_col as u32).to_be_bytes());
    corpo.extend_from_slice(&a.n_colisoes.to_be_bytes());
    corpo.extend_from_slice(&0u16.to_be_bytes());
    corpo.extend_from_slice(&a.bloco_colisoes);
    corpo.extend_from_slice(&lsbl);
    let sobra = alinhar(corpo.len(), ALINHAMENTO_SECAO) - corpo.len();
    corpo.extend(std::iter::repeat_n(0u8, sobra));
    Ok(corpo)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn ida_e_volta_simples() {
        let asset = AssetTexto {
            bloco_colisoes: Vec::new(),
            n_colisoes: 0,
            hashes: vec![0x1001, 0x2002],
            textos: vec![crate::fixtures::texto_com_acentos(), "Segunda linha\ncom quebra".to_string()],
            tabela_chaves: crate::fixtures::tabela_chaves(&[(0x1001, 1, "alpha"), (0x2002, 2, "beta")]),
            tabela_comentarios: None,
            tabela_indice: None,
        };
        let secao = escrever(&asset).unwrap();
        let lido = ler(&secao).unwrap();
        assert_eq!(lido.hashes, asset.hashes);
        assert_eq!(lido.textos, asset.textos);
        assert_eq!(
            lido.chaves().unwrap().iter().map(|c| c.nome.clone()).collect::<Vec<_>>(),
            vec!["alpha", "beta"]
        );
    }

    #[test]
    fn recusa_secao_curta() {
        assert!(ler(&[0u8; 4]).is_err());
    }
}