//! Catalogo de traducoes embutido no executavel (gerado por `build.rs` a partir de
//! `data/traducao`). Contem somente as frases traduzidas pelo projeto.

use serde_json::Value;

pub struct FraseTrad {
    pub id: String,
    pub chave: String,
    pub hash_es: Option<String>,
    pub texto_ptbr: String,
}

pub struct ArquivoTrad {
    pub arquivo: String,
    pub asset: String,
    pub frases: Vec<FraseTrad>,
}

const CATALOGO: &str = include_str!(concat!(env!("OUT_DIR"), "/traducao.json"));

pub fn carregar() -> Result<Vec<ArquivoTrad>, String> {
    let lista: Value = serde_json::from_str(CATALOGO)
        .map_err(|e| format!("Catálogo de traduções embutido inválido: {e}"))?;
    let itens = lista
        .as_array()
        .ok_or("Catálogo de traduções embutido não é uma lista.")?;
    let mut out = Vec::with_capacity(itens.len());
    for item in itens {
        let arquivo = item["arquivo"]
            .as_str()
            .ok_or("Catálogo sem o campo 'arquivo'.")?
            .to_string();
        let asset = item["asset"].as_str().unwrap_or("").to_string();
        let mut frases = Vec::new();
        for f in item["frases"].as_array().ok_or("Catálogo sem frases.")? {
            frases.push(FraseTrad {
                id: f["id"].as_str().unwrap_or("").to_string(),
                chave: f["chave"].as_str().ok_or("Frase sem chave.")?.to_string(),
                hash_es: f["hash_es"].as_str().map(str::to_string),
                texto_ptbr: f["texto_ptbr"].as_str().unwrap_or("").to_string(),
            });
        }
        out.push(ArquivoTrad {
            arquivo,
            asset,
            frases,
        });
    }
    out.sort_by(|a, b| a.arquivo.cmp(&b.arquivo));
    Ok(out)
}

#[cfg(test)]
mod tests {
    #[test]
    fn catalogo_tem_os_107_arquivos() {
        let c = super::carregar().unwrap();
        assert_eq!(c.len(), 107, "arquivos no catalogo");
        let total: usize = c.iter().map(|a| a.frases.len()).sum();
        assert!(total > 6000, "frases no catalogo: {total}");
    }
}