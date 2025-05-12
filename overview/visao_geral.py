import streamlit as st
import pandas as pd
import snowflake.connector
import altair as alt

st.set_page_config(
    page_title="Visão Geral - Sistema Web Empresa", 
    page_icon="logo_fgv.png"
)

# --- Conexão com o banco ---------------------------------------------------
def get_connection():
    """
    Estabelece e retorna a conexão com o Snowflake
    utilizando os dados configurados em st.secrets.
    """
    return snowflake.connector.connect(
        account   = st.secrets["snowflake"]["account"],
        user      = st.secrets["snowflake"]["user"],
        password  = st.secrets["snowflake"]["password"],
        warehouse = st.secrets["snowflake"]["warehouse"],
        database  = st.secrets["snowflake"]["database"],
        schema    = st.secrets["snowflake"]["schema"],
    )

# --- Queries e cache -------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_overview_counts():
    """
    Retorna os principais totais:
      - tot_count: total de empresas ativas
      - subclasses: número de subclasses CNAE
      - estados: número de estados + DF
      - municipios: número de municípios
    """
    conn = get_connection()
    cur = conn.cursor()
    # totais
    cur.execute("SELECT COUNT(*) FROM TB_MVP_CONS")
    tot_count = cur.fetchone()[0]
    # subclasses
    cur.execute("SELECT COUNT(DISTINCT CODIGO_DESCR) FROM TB_CNAE_DESCR")
    subclasses = cur.fetchone()[0]
    # estados
    cur.execute("SELECT COUNT(DISTINCT UF) FROM TB_UF_MUNICIPIO")
    estados = cur.fetchone()[0]
    # municipios
    cur.execute("SELECT COUNT(DISTINCT MUNICIPIO) FROM TB_UF_MUNICIPIO")
    municipios = cur.fetchone()[0]
    cur.close()
    conn.close()
    return tot_count, subclasses, estados, municipios

@st.cache_data(show_spinner=False)
def load_count1():
    """
    Retorna DataFrame com contagem de empresas por (cnae_descr, uf).
    """
    conn = get_connection()
    query = """
      SELECT * FROM TB_CNAE_UF
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

@st.cache_data(show_spinner=False)
def load_count2():
    """
    Retorna DataFrame com contagem de empresas por (cnae_descr, uf, municipio).
    """
    conn = get_connection()
    query = """
      SELECT * FROM TB_CNAE_UF_MUNICIPIO
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# --- App principal ---------------------------------------------------------
def main():
    st.title("Overview: Empresas Ativas")

    # carrega os dados
    tot_count, subclasses, estados, municipios = load_overview_counts()
    df1 = load_count1()
    df2 = load_count2()

    # --- Métricas no topo ----------------------------------------------
    col1, col2, col3, col4 = st.columns(4)
    items = [
        ("Total de Empresas Ativas", f"{tot_count:,}"),
        ("Subclasses da CNAE",       f"{subclasses:,}"),
        ("Estados + DF",             f"{estados:,}"),
        ("Municípios",               f"{municipios:,}"),
    ]
    
    for col, (label, value) in zip((col1, col2, col3, col4), items):
        with col:
            st.markdown(
                f"""
                <div style="
                    border:1px solid #ccc;
                    border-radius:6px;
                    padding:16px;
                    display: flex;
                    flex-direction:column;
                    justify-content: center;
                    align-itens: center;
                    text-align:center;
                    box-shadow:2px 2px 6px rgba(0,0,0,0.05);
                ">
                    <div style="font-size:0.9rem; color:#555;">{label}</div>
                    <div style="font-size:1.7rem;">{value}</div>
                </div>
                """,
                unsafe_allow_html=True
        )

    st.markdown("---")

    # --- Top 10: CNAE X UF ---------------------------------------------
    st.subheader("TOP 10: CNAE X UF")
    st.caption("Os dez estados mais representativos por atividade econômica.")

    # filtro de CNAE
    df1 = df1.dropna()
    cnae_list = sorted(df1["CNAE_DESCR"].unique())
    sel_cnae = st.selectbox("Selecione CNAE:", cnae_list, index=0)

    # prepara dados e plot
    top_uf = (
        df1[df1["CNAE_DESCR"] == sel_cnae]
        .nlargest(10, "COUNTER")
        .rename(columns={"UF": "Estado", "COUNTER": "Nº Empresas Ativas"})
    )
    if not top_uf.empty:
        chart = (
            alt.Chart(top_uf)
            .mark_bar()
            .encode(
                x=alt.X("Nº Empresas Ativas:Q", title="Nº Empresas"),
                y=alt.Y("Estado:N", sort="-x"),
                tooltip=["Estado", "Nº Empresas Ativas"]
            )
            .properties(width=700, height=400)
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado para esse CNAE.")

    st.markdown("---")

    # --- CNAE X CIDADES -------------------------------------------------
    st.subheader("CNAE X CIDADES")
    st.caption("Os municípios mais representativos por atividade econômica.")

    # filtro de UF
    uf_list = sorted(df2["UF"].unique())
    sel_uf = st.selectbox("Selecione UF:", uf_list, index=0)

    # filtra e exibe tabela
    df_mun = (
        df2[(df2["CNAE_DESCR"] == sel_cnae) & (df2["UF"] == sel_uf)]
        .sort_values("COUNTER", ascending=False)
        .rename(columns={"CNAE_DESCR":"Atividade Realizada","MUNICIPIO": "Município", "COUNTER": "Nº Empresas Ativas"})
    )
    if not df_mun.empty:
        st.dataframe(df_mun[["Atividade Realizada","Município", "Nº Empresas Ativas"]])
    else:
        st.info("Nenhum município encontrado para essa combinação.")

main()
