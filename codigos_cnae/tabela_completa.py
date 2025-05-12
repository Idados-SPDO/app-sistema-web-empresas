import streamlit as st
import pandas as pd
import snowflake.connector

st.set_page_config(
    page_title="Tabela Completa - Sistema Web Empresa", 
    page_icon="logo_fgv.png"
)

# --- Carrega o CSS que redimensiona o iframe -------------------------------
# Baixe o arquivo style.css do repositório e coloque ao lado deste script
st.markdown(
    """
    <style>
      iframe {
        height: 100px;
        width: 500px;
      }
    </style>
    """,
    unsafe_allow_html=True
)  # necessário para que o iframe do pagination ganhe altura :contentReference[oaicite:0]{index=0}

# --- Conexão com o banco ---------------------------------------------------
def get_connection():
    return snowflake.connector.connect(
        account   = st.secrets["snowflake"]["account"],
        user      = st.secrets["snowflake"]["user"],
        password  = st.secrets["snowflake"]["password"],
        warehouse = st.secrets["snowflake"]["warehouse"],
        database  = st.secrets["snowflake"]["database"],
        schema    = st.secrets["snowflake"]["schema"],
    )

# --- Query e cache ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_cnaes_table():
    conn = get_connection()
    df = pd.read_sql(
        "SELECT DISTINCT CODIGO as codigo, DESCRICAO as descricao FROM TB_CNAE_DESCR",
        conn
    )
    conn.close()
    return df

# --- App principal ---------------------------------------------------------
def main():
    st.title("Consulta de Códigos CNAE - Tabela Completa")

    # campo de busca
    df_cnaes = load_cnaes_table()
    termo = st.text_input(
        "Pesquisar por código ou descrição:",
        placeholder="Digite parte do código ou da descrição"
    )
    if termo:
        mask_code = df_cnaes["CODIGO"].astype(str).str.contains(termo, case=False)
        mask_desc = df_cnaes["DESCRICAO"].str.contains(termo, case=False)
        df_filt = df_cnaes[mask_code | mask_desc]
    else:
        df_filt = df_cnaes

    # paginação por blocos de 30 linhas
    page_size = 30
    list_df = [df_filt[i : i + page_size] for i in range(0, len(df_filt), page_size)]
    if not list_df:
        st.warning("Nenhum registro encontrado.")
        return

    st.dataframe(df_filt, use_container_width=True)


main()
