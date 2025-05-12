import streamlit as st
import pandas as pd
import snowflake.connector

st.set_page_config(page_title="CNPJ - Sistema Web Empresa", page_icon="logo_fgv.png")

def get_connection():
    return snowflake.connector.connect(
        account   = st.secrets["snowflake"]["account"],
        user      = st.secrets["snowflake"]["user"],
        password  = st.secrets["snowflake"]["password"],
        warehouse = st.secrets["snowflake"]["warehouse"],
        database  = st.secrets["snowflake"]["database"],
        schema    = st.secrets["snowflake"]["schema"],
    )

def execute_search_query_cnpj(cnpj):
    conn   = get_connection()
    query  = f"SELECT * FROM TB_MVP_CONS WHERE CNPJ = '{cnpj}'"
    cur    = conn.cursor()
    cur.execute(query)
    data   = cur.fetchall()
    cols   = [d[0] for d in cur.description]
    cur.close()
    conn.close()
    return pd.DataFrame(data, columns=cols)

def mod_cons_cnpj_ui():
    with st.container(border=True):
        st.title("Filtros: CNPJ")
        input_cnpj = st.text_input("CNPJ:", value="", key="input_cnpj", help="Digite o CNPJ de interesse (Exemplo: 26909999000260)")
        pesquisar  = st.button("Pesquisar", key="search_cnpj")
    return input_cnpj, pesquisar

def mod_cons_cnpj_server(input_cnpj, pesquisar):
    if pesquisar:
        if not input_cnpj.strip():
            st.error("Por favor, insira um CNPJ válido.")
            return

        with st.spinner("Executando a query..."):
            df_result = execute_search_query_cnpj(input_cnpj.strip())

        if df_result.empty:
            st.warning("Não há dados para o CNPJ informado.")
        else:
            with st.container(border=True):
                for _, row in df_result.iterrows():
                    cnpj = row.get("CNPJ", "")
                    razao   = row.get("RAZAO_SOCIAL")
                    header = f"{cnpj} – {razao}" if razao and pd.notna(razao) and str(razao).strip() else cnpj
                    with st.expander(header):
                        st.write(row.to_dict())

input_cnpj, pesquisar = mod_cons_cnpj_ui()
mod_cons_cnpj_server(input_cnpj, pesquisar)
