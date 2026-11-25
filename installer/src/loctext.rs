//! Leitura e escrita de alto nivel de um arquivo de texto do jogo (CAFF + LSBL).

use crate::caff::{self, Caff};
use crate::lsbl::{self, AssetTexto};

#[derive(Clone, Debug)]
pub struct Frase {
    /// Hash da chave em quatro digitos hexadecimais (unico por arquivo).
    pub id: String,
    pub chave: String,
    pub indice: u16,
    pub texto: String,
}

#[derive(Clone)]
pub struct ArquivoLoctext {
    pub conteiner: Caff,
    pub asset: AssetTexto,
}

impl ArquivoLoctext {
    pub fn nome_asset(&self) -> String {
        self.conteiner.asset()
    }

    /// Frases na ordem alfabetica da chave (o mesmo `indice` gravado no arquivo).
    pub fn frases(&self) -> Result<Vec<Frase>, String> {
        let chaves = self.asset.chaves()?;
        if chaves.len() != self.asset.textos.len() {
            return Err("Tabela de chaves e de frases com tamanhos diferentes.".into());
        }
        let mut out: Vec<Frase> = chaves
            .iter()
            .zip(self.asset.textos.iter())
            .map(|(c, t)| Frase {
                id: format!("{:04x}", c.hash),
                chave: c.nome.clone(),
                indice: c.indice,
                texto: t.clone(),
            })
            .collect();
        out.sort_by_key(|f| f.indice);
        Ok(out)
    }

    pub fn com_textos_por_chave(&self, novos: &std::collections::HashMap<String, String>) -> Result<Self, String> {
        let chaves = self.asset.chaves()?;
        let textos: Vec<String> = chaves
            .iter()
            .zip(self.asset.textos.iter())
            .map(|(c, antigo)| novos.get(&c.nome).cloned().unwrap_or_else(|| antigo.clone()))
            .collect();
        Ok(ArquivoLoctext {
            conteiner: self.conteiner.clone(),
            asset: self.asset.com_textos(textos)?,
        })
    }
}

pub fn ler(dados: &[u8]) -> Result<ArquivoLoctext, String> {
    let conteiner = caff::ler(dados)?;
    let asset = lsbl::ler(&conteiner.dados)?;
    Ok(ArquivoLoctext { conteiner, asset })
}

pub fn escrever(arq: &ArquivoLoctext) -> Result<Vec<u8>, String> {
    let secao = lsbl::escrever(&arq.asset)?;
    let conteiner = Caff {
        cabecalho: arq.conteiner.cabecalho.clone(),
        nomes_secao: arq.conteiner.nomes_secao.clone(),
        nome_simbolo: arq.conteiner.nome_simbolo.clone(),
        dados: secao,
    };
    caff::escrever(&conteiner)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn le_e_reescreve_sem_perder_nada() {
        let dados = crate::fixtures::arquivo_loctext(
            "aid_loctext_banjox_teste,1220524793,2.33",
            &[("alpha", "Primeira"), ("beta", "Segunda com acento: ção")],
        );
        let arq = ler(&dados).unwrap();
        let frases = arq.frases().unwrap();
        assert_eq!(frases.len(), 2);
        assert_eq!(frases[0].chave, "alpha");
        let mut novos = std::collections::HashMap::new();
        novos.insert("beta".to_string(), "Trocada".to_string());
        let novo = escrever(&arq.com_textos_por_chave(&novos).unwrap()).unwrap();
        let relido = ler(&novo).unwrap();
        let f = relido.frases().unwrap();
        assert_eq!(f[0].texto, "Primeira");
        assert_eq!(f[1].texto, "Trocada");
        // Mesmo tamanho de area de informacoes: o cabecalho (com checksum) continua valido.
        assert_eq!(&novo[..caff::TAM_CABECALHO], &dados[..caff::TAM_CABECALHO]);
    }
}