import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="Dicionário de Dados - Sistema Web Empresa", 
    page_icon="logo_fgv.png"
)

# --- Query e cache ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_layout():
    url = "https://cdn.datatables.net/plug-ins/1.10.11/i18n/Portuguese-Brasil.json"

    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        st.error(f"Erro ao carregar JSON: {response.status_code}")
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
    dados_json = load_layout()

    # Exibir os dados no Streamlit
    st.title("Visualizador de JSON do DataTables")
    st.json(dados_json)

main()
