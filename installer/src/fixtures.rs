//! Arquivos loctext sinteticos para os testes (nao contem nada do jogo).

use crate::caff;

pub fn texto_com_acentos() -> String {
    "Ação, coração, pão e irmã".to_string()
}

/// Tabela de chaves no formato LSBL: (hash, indice, nome).
pub fn tabela_chaves(itens: &[(u16, u16, &str)]) -> Vec<u8> {
    let mut nomes = Vec::new();
    let mut deslocamentos = Vec::new();
    for (_, _, nome) in itens {
        deslocamentos.push(nomes.len() as u32);
        nomes.extend_from_slice(nome.as_bytes());
        nomes.push(0);
    }
    let tam = 8 + 8 * itens.len() + nomes.len();
    let mut t = Vec::with_capacity(tam);
    t.extend_from_slice(&(tam as u32).to_le_bytes());
    t.extend_from_slice(&(itens.len() as u32).to_le_bytes());
    for (i, (hash, indice, _)) in itens.iter().enumerate() {
        t.extend_from_slice(&hash.to_le_bytes());
        t.extend_from_slice(&indice.to_le_bytes());
        t.extend_from_slice(&deslocamentos[i].to_le_bytes());
    }
    t.extend_from_slice(&nomes);
    t
}

/// Monta um arquivo completo (CAFF + LSBL) com as frases dadas, na ordem informada.
pub fn arquivo_loctext(nome_asset: &str, frases: &[(&str, &str)]) -> Vec<u8> {
    let hashes: Vec<u16> = (0..frases.len()).map(|i| 0x1000 + i as u16).collect();
    let textos: Vec<String> = frases.iter().map(|(_, t)| (*t).to_string()).collect();
    let chaves: Vec<(u16, u16, &str)> = frases
        .iter()
        .enumerate()
        .map(|(i, (c, _))| (hashes[i], i as u16 + 1, *c))
        .collect();
    let asset = crate::lsbl::AssetTexto {
        bloco_colisoes: Vec::new(),
        n_colisoes: 0,
        hashes,
        textos,
        tabela_chaves: tabela_chaves(&chaves),
        tabela_comentarios: None,
        tabela_indice: None,
    };

    let info_len = {
        // Mesma conta de `caff::area_info`, para caber no campo 0x50 do cabecalho.
        let mut n = 4 + 1 + 28 + b".data\0".len() + 8 + nome_asset.len() + 1 + 18;
        n = caff::alinhar(n, 4);
        n
    };
    let mut cabecalho = vec![0u8; caff::TAM_CABECALHO];
    cabecalho[..20].copy_from_slice(caff::ASSINATURA);
    cabecalho[0x14..0x18].copy_from_slice(&(caff::TAM_CABECALHO as u32).to_be_bytes());
    cabecalho[0x1C..0x20].copy_from_slice(&1u32.to_be_bytes());
    cabecalho[0x20..0x24].copy_from_slice(&1u32.to_be_bytes());
    cabecalho[0x48..0x4C].copy_from_slice(&[0x01, 0x01, 0x00, 0x00]);
    cabecalho[0x4C..0x50].copy_from_slice(&(b".data\0".len() as u32).to_be_bytes());
    cabecalho[0x50..0x54].copy_from_slice(&(info_len as u32).to_be_bytes());
    cabecalho[0x60..0x64].copy_from_slice(&(info_len as u32).to_be_bytes());

    let secao = crate::lsbl::escrever(&asset).unwrap();
    let c = caff::Caff {
        cabecalho,
        nomes_secao: b".data\0".to_vec(),
        nome_simbolo: nome_asset.as_bytes().to_vec(),
        dados: secao,
    };
    caff::escrever(&c).unwrap()
}

/// Cria uma "instalacao do jogo" sintetica com os 107 nomes esperados quando `completo`.
pub fn jogo_sintetico(
    raiz: &std::path::Path,
    nomes: &[String],
    traducoes_por_arquivo: &std::collections::HashMap<String, Vec<(String, String, String)>>,
) {
    for nome in nomes {
        let pares = traducoes_por_arquivo
            .get(nome)
            .cloned()
            .unwrap_or_default();
        let frases_en: Vec<(String, String)> = pares
            .iter()
            .map(|(k, en, _)| (k.clone(), en.clone()))
            .collect();
        let frases_ref: Vec<(String, String)> = pares
            .iter()
            .map(|(k, _, es)| (k.clone(), es.clone()))
            .collect();
        let en: Vec<(&str, &str)> = frases_en
            .iter()
            .map(|(a, b)| (a.as_str(), b.as_str()))
            .collect();
        let es: Vec<(&str, &str)> = frases_ref
            .iter()
            .map(|(a, b)| (a.as_str(), b.as_str()))
            .collect();
        let dir_en = raiz.join("Debug").join(&nome[0..2]).join(&nome[2..4]).join(&nome[4..6]);
        std::fs::create_dir_all(&dir_en).unwrap();
        std::fs::write(dir_en.join(&nome[6..8]), arquivo_loctext("aid_loctext_teste", &en)).unwrap();
        let dir_es = raiz.join("loctext").join("spanish");
        std::fs::create_dir_all(&dir_es).unwrap();
        std::fs::write(dir_es.join(nome), arquivo_loctext("aid_loctext_teste", &es)).unwrap();
    }
}