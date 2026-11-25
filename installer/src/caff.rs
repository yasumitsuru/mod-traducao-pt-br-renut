//! CAFF 07.08.06.0036 — o conteiner dos arquivos de texto do jogo.
//!
//! Porte fiel de `tools/nbptbr/caff.py`, restrito ao subconjunto observado nos arquivos
//! loctext (uma secao `.data` e um simbolo). Qualquer desvio vira erro, nunca um palpite.

pub const ASSINATURA: &[u8] = b"CAFF07.08.06.0036\x00\x00\x00";
pub const TAM_CABECALHO: usize = 0x78;
pub const ALINHAMENTO_SECAO: usize = 16;

fn u32_be(b: &[u8], o: usize) -> Result<u32, String> {
    let fatia = b.get(o..o + 4).ok_or_else(|| "Arquivo CAFF truncado.".to_string())?;
    Ok(u32::from_be_bytes([fatia[0], fatia[1], fatia[2], fatia[3]]))
}

pub fn alinhar(valor: usize, base: usize) -> usize {
    valor.div_ceil(base) * base
}

#[derive(Clone)]
pub struct Caff {
    pub cabecalho: Vec<u8>,
    pub nomes_secao: Vec<u8>,
    pub nome_simbolo: Vec<u8>,
    pub dados: Vec<u8>,
}

impl Caff {
    pub fn asset(&self) -> String {
        String::from_utf8_lossy(&self.nome_simbolo)
            .split(',')
            .next()
            .unwrap_or("")
            .to_string()
    }

    pub fn tam_info(&self) -> Result<usize, String> {
        Ok(u32_be(&self.cabecalho, 0x50)? as usize)
    }

    pub fn checksum(&self) -> Result<u32, String> {
        u32_be(&self.cabecalho, 0x18)
    }
}

fn exigir(condicao: bool, mensagem: &str) -> Result<(), String> {
    if condicao {
        Ok(())
    } else {
        Err(mensagem.to_string())
    }
}

fn validar_cabecalho(b: &[u8]) -> Result<(), String> {
    exigir(b.len() >= TAM_CABECALHO, "Arquivo menor que o cabecalho CAFF.")?;
    exigir(&b[..20] == ASSINATURA, "Assinatura CAFF inesperada.")?;
    exigir(u32_be(b, 0x14)? == TAM_CABECALHO as u32, "Campo 0x14 do CAFF não é 0x78.")?;
    exigir(
        u32_be(b, 0x1C)? == 1 && u32_be(b, 0x20)? == 1,
        "Esperado 1 símbolo e 1 seção no CAFF.",
    )?;
    exigir(b[0x24..0x48] == [0u8; 0x24], "Bytes reservados do CAFF não são zero.")?;
    exigir(
        b[0x48..0x4C] == [0x01, 0x01, 0x00, 0x00],
        "Bytes 0x48..0x4B do CAFF são inesperados.",
    )?;
    exigir(
        u32_be(b, 0x50)? == u32_be(b, 0x60)?,
        "Tamanhos da área de informações do CAFF divergem.",
    )?;
    exigir(
        b[0x54..0x60] == [0u8; 12] && b[0x64..0x78] == [0u8; 0x14],
        "Campos reservados do CAFF não são zero.",
    )?;
    exigir(u32_be(b, 0x50)? % 4 == 0, "Área de informações do CAFF não alinhada a 4.")?;
    Ok(())
}

pub fn ler(b: &[u8]) -> Result<Caff, String> {
    validar_cabecalho(b)?;
    let tam_nomes_secao = u32_be(b, 0x4C)? as usize;
    let tam_info = u32_be(b, 0x50)? as usize;
    let inicio_dados = TAM_CABECALHO + tam_info;
    exigir(inicio_dados <= b.len(), "Area de informacoes do CAFF ultrapassa o arquivo.")?;

    let mut p = TAM_CABECALHO;
    exigir(u32_be(b, p)? == 0, "Campo info+0x00 do CAFF não é zero.")?;
    p += 4;
    exigir(*b.get(p).ok_or("CAFF truncado.")? == 4, "Alinhamento da seção do CAFF não é 4.")?;
    p += 1;
    let secao = b.get(p..p + 28).ok_or("CAFF truncado na entrada da seção.")?;
    let mut campos = [0u32; 7];
    for (i, c) in campos.iter_mut().enumerate() {
        *c = u32::from_be_bytes([
            secao[i * 4],
            secao[i * 4 + 1],
            secao[i * 4 + 2],
            secao[i * 4 + 3],
        ]);
    }
    p += 28;
    let tam_secao = campos[1] as usize;
    exigir(
        campos[0] == 0 && campos[2] == 0 && campos[3] == 0 && campos[4] == 0 && campos[5] == 0,
        "Entrada de seção do CAFF com campos inesperados.",
    )?;
    exigir(campos[6] as usize == tam_secao, "Tamanhos da seção do CAFF divergem.")?;
    let nomes_secao = b
        .get(p..p + tam_nomes_secao)
        .ok_or("Tabela de nomes de seção do CAFF truncada.")?
        .to_vec();
    exigir(nomes_secao == b".data\x00", "Nome de seção do CAFF inesperado.")?;
    p += tam_nomes_secao;
    let tam_nomes_simbolo = u32_be(b, p)? as usize;
    exigir(u32_be(b, p + 4)? == 0, "Campo após o tamanho dos nomes de símbolo não é zero.")?;
    p += 8;
    let nomes_simbolo = b
        .get(p..p + tam_nomes_simbolo)
        .ok_or("Tabela de nomes de simbolo do CAFF truncada.")?
        .to_vec();
    exigir(
        nomes_simbolo.ends_with(b"\x00") && nomes_simbolo.iter().filter(|x| **x == 0).count() == 1,
        "Tabela de nomes de símbolo do CAFF inválida.",
    )?;
    p += tam_nomes_simbolo;
    let simbolo = b.get(p..p + 18).ok_or("Entrada de simbolo do CAFF truncada.")?;
    let valores = [
        u32::from_be_bytes([simbolo[0], simbolo[1], simbolo[2], simbolo[3]]),
        u32::from_be_bytes([simbolo[4], simbolo[5], simbolo[6], simbolo[7]]),
        u32::from_be_bytes([simbolo[8], simbolo[9], simbolo[10], simbolo[11]]),
        u32::from_be_bytes([simbolo[12], simbolo[13], simbolo[14], simbolo[15]]),
    ];
    exigir(
        valores == [0, 1, 0, tam_secao as u32] && simbolo[16] == 1 && simbolo[17] == 4,
        "Entrada de simbolo do CAFF inesperada.",
    )?;
    p += 18;
    exigir(
        alinhar(p - TAM_CABECALHO, 4) == tam_info,
        "Tamanho da área de informações do CAFF não confere.",
    )?;
    exigir(
        b[p..inicio_dados].iter().all(|x| *x == 0),
        "Preenchimento da área de informações do CAFF não é zero.",
    )?;
    exigir(
        inicio_dados + tam_secao == b.len(),
        "Tamanho do CAFF difere de cabeçalho + informações + seção.",
    )?;
    exigir(
        tam_secao % ALINHAMENTO_SECAO == 0,
        "Seção do CAFF não é múltipla de 16.",
    )?;
    let mut nome_simbolo = nomes_simbolo;
    nome_simbolo.pop();
    Ok(Caff {
        cabecalho: b[..TAM_CABECALHO].to_vec(),
        nomes_secao,
        nome_simbolo,
        dados: b[inicio_dados..].to_vec(),
    })
}

fn area_info(c: &Caff) -> Vec<u8> {
    let tam_secao = c.dados.len() as u32;
    let mut nome = c.nome_simbolo.clone();
    nome.push(0);
    let mut info = Vec::new();
    info.extend_from_slice(&0u32.to_be_bytes());
    info.push(4);
    for v in [0u32, tam_secao, 0, 0, 0, 0, tam_secao] {
        info.extend_from_slice(&v.to_be_bytes());
    }
    info.extend_from_slice(&c.nomes_secao);
    info.extend_from_slice(&(nome.len() as u32).to_be_bytes());
    info.extend_from_slice(&0u32.to_be_bytes());
    info.extend_from_slice(&nome);
    for v in [0u32, 1, 0, tam_secao] {
        info.extend_from_slice(&v.to_be_bytes());
    }
    info.push(1);
    info.push(4);
    let sobra = alinhar(info.len(), 4) - info.len();
    info.extend(std::iter::repeat_n(0u8, sobra));
    info
}

pub fn escrever(c: &Caff) -> Result<Vec<u8>, String> {
    exigir(
        c.dados.len() % ALINHAMENTO_SECAO == 0,
        "Dados da seção CAFF precisam ser múltiplos de 16.",
    )?;
    validar_cabecalho(&c.cabecalho)?;
    let info = area_info(c);
    exigir(
        info.len() == c.tam_info()?,
        "A área de informações do CAFF mudou de tamanho; o checksum do cabeçalho não pode ser recalculado.",
    )?;
    let mut saida = c.cabecalho.clone();
    saida.extend_from_slice(&info);
    saida.extend_from_slice(&c.dados);
    Ok(saida)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn recusa_arquivo_curto() {
        assert!(ler(b"CAFF").is_err());
    }

    #[test]
    fn alinhamento() {
        assert_eq!(alinhar(1, 16), 16);
        assert_eq!(alinhar(16, 16), 16);
        assert_eq!(alinhar(17, 16), 32);
    }
}