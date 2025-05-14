import streamlit as st
import pandas as pd
import json
from pathlib import Path

st.set_page_config(
    page_title="Dicionário de Dados - Sistema Web Empresa", 
    page_icon="logo_fgv.png"
)

# --- Query e cache ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_layout():
    # 1) monta o caminho relativo à raiz do projeto
    json_path = Path.cwd() / "layout" / "dicionario.json"
    
    # 2) opcional: se quiser um fallback caso muda o cwd em algum ambiente
    if not json_path.exists():
        json_path = Path(__file__).resolve().parent / "layout" / "dicionario.json"
    
    # 3) tenta abrir
    try:
        return json.loads(json_path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        st.error(f"Arquivo não encontrado em:\n{json_path}")
    except json.JSONDecodeError as e:
        st.error(f"Erro ao decodificar JSON em {json_path}:\n{e}")
    return {}

# --- App principal ---------------------------------------------------------
def main():
    st.title("Dicionário de Dados do Cadastro Nacional da Pessoa Jurídica")

    st.markdown(
        """
        O Cadastro Nacional da Pessoa Jurídica (CNPJ) é um banco de dados gerenciado pela
        Secretaria Especial da Receita Federal do Brasil (RFB), que armazena informações
        cadastrais das pessoas jurídicas e outras entidades de interesse das administrações
        tributárias da União, dos Estados, do Distrito Federal e dos Municípios.

        A origem dos dados: [Portal de Dados Abertos](https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica---cnpj).
        """
    )
    st.write("---")

    # carrega e exibe o layout
        # carrega o JSON
    layout = load_layout()

        # 1) Se for um mapeamento simples chave->valor, vira um DF de duas colunas
    df_kv = pd.DataFrame(
            list(layout.items()),
            columns=['Variável', 'Descrição']
    )

        # no Streamlit, basta:
    st.dataframe(df_kv)


main()
