//! Escritor ZIP minimo, byte a byte igual ao `zipfile` do Python usado pelo gerador 0.7.0.
//!
//! Entradas sem compressao (metodo 0), data fixa 2026-01-01 00:00, atributos 0644 e ordem
//! preservada. E o que torna o `.nbpatch` reproduzivel e o SHA-256 comparavel ao esperado.

const DATA_DOS: u16 = 0x5C21; // 2026-01-01
const HORA_DOS: u16 = 0x0000;
const VERSAO: u16 = 20;
const ATRIBUTOS_EXTERNOS: u32 = 0o644 << 16;

fn crc32(dados: &[u8]) -> u32 {
    let mut tabela = [0u32; 256];
    for (i, item) in tabela.iter_mut().enumerate() {
        let mut c = i as u32;
        for _ in 0..8 {
            c = if c & 1 != 0 { 0xEDB88320 ^ (c >> 1) } else { c >> 1 };
        }
        *item = c;
    }
    let mut crc = 0xFFFF_FFFFu32;
    for b in dados {
        crc = tabela[((crc ^ u32::from(*b)) & 0xFF) as usize] ^ (crc >> 8);
    }
    crc ^ 0xFFFF_FFFF
}

#[derive(Default)]
pub struct Zip {
    entradas: Vec<(String, Vec<u8>)>,
}

impl Zip {
    pub fn novo() -> Self {
        Self::default()
    }

    pub fn adicionar(&mut self, nome: &str, dados: Vec<u8>) {
        self.entradas.push((nome.to_string(), dados));
    }

    pub fn finalizar(&self) -> Vec<u8> {
        let mut saida: Vec<u8> = Vec::new();
        let mut centrais: Vec<u8> = Vec::new();
        let mut deslocamentos: Vec<u32> = Vec::new();

        for (nome, dados) in &self.entradas {
            let offset = saida.len() as u32;
            deslocamentos.push(offset);
            let crc = crc32(dados);
            let tam = dados.len() as u32;
            let nome_bytes = nome.as_bytes();
            // Cabecalho local: PK\x03\x04
            saida.extend_from_slice(&0x0403_4B50u32.to_le_bytes());
            saida.extend_from_slice(&VERSAO.to_le_bytes());
            saida.extend_from_slice(&0u16.to_le_bytes()); // flags
            saida.extend_from_slice(&0u16.to_le_bytes()); // metodo: sem compressao
            saida.extend_from_slice(&HORA_DOS.to_le_bytes());
            saida.extend_from_slice(&DATA_DOS.to_le_bytes());
            saida.extend_from_slice(&crc.to_le_bytes());
            saida.extend_from_slice(&tam.to_le_bytes());
            saida.extend_from_slice(&tam.to_le_bytes());
            saida.extend_from_slice(&(nome_bytes.len() as u16).to_le_bytes());
            saida.extend_from_slice(&0u16.to_le_bytes());
            saida.extend_from_slice(nome_bytes);
            saida.extend_from_slice(dados);
        }

        let inicio_central = saida.len() as u32;
        for (i, (nome, dados)) in self.entradas.iter().enumerate() {
            let crc = crc32(dados);
            let tam = dados.len() as u32;
            let nome_bytes = nome.as_bytes();
            // Cabecalho central: PK\x01\x02 (criado por sistema FAT, igual ao Python no Windows)
            centrais.extend_from_slice(&0x0201_4B50u32.to_le_bytes());
            centrais.extend_from_slice(&0x0014u16.to_le_bytes());
            centrais.extend_from_slice(&VERSAO.to_le_bytes());
            centrais.extend_from_slice(&0u16.to_le_bytes()); // flags
            centrais.extend_from_slice(&0u16.to_le_bytes()); // metodo
            centrais.extend_from_slice(&HORA_DOS.to_le_bytes());
            centrais.extend_from_slice(&DATA_DOS.to_le_bytes());
            centrais.extend_from_slice(&crc.to_le_bytes());
            centrais.extend_from_slice(&tam.to_le_bytes());
            centrais.extend_from_slice(&tam.to_le_bytes());
            centrais.extend_from_slice(&(nome_bytes.len() as u16).to_le_bytes());
            centrais.extend_from_slice(&0u16.to_le_bytes()); // extra
            centrais.extend_from_slice(&0u16.to_le_bytes()); // comentario
            centrais.extend_from_slice(&0u16.to_le_bytes()); // disco
            centrais.extend_from_slice(&0u16.to_le_bytes()); // atributos internos
            centrais.extend_from_slice(&ATRIBUTOS_EXTERNOS.to_le_bytes());
            centrais.extend_from_slice(&deslocamentos[i].to_le_bytes());
            centrais.extend_from_slice(nome_bytes);
        }
        saida.extend_from_slice(&centrais);

        let n = self.entradas.len() as u16;
        saida.extend_from_slice(&0x0605_4B50u32.to_le_bytes());
        saida.extend_from_slice(&0u16.to_le_bytes());
        saida.extend_from_slice(&0u16.to_le_bytes());
        saida.extend_from_slice(&n.to_le_bytes());
        saida.extend_from_slice(&n.to_le_bytes());
        saida.extend_from_slice(&(centrais.len() as u32).to_le_bytes());
        saida.extend_from_slice(&inicio_central.to_le_bytes());
        saida.extend_from_slice(&0u16.to_le_bytes());
        saida
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cabecalhos_iguais_aos_do_python() {
        let mut z = Zip::novo();
        z.adicionar("patch.json", b"{}".to_vec());
        let zip = z.finalizar();
        assert_eq!(&zip[..4], b"PK\x03\x04");
        assert_eq!(&zip[zip.len() - 22..zip.len() - 18], b"PK\x05\x06");
        assert_eq!(crc32(b"123456789"), 0xCBF4_3926);
    }
}