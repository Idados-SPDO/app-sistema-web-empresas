import streamlit as st
import pandas as pd
import snowflake.connector
import math
from io import BytesIO

st.set_page_config(page_title="CNAE/UF - Sistema Web Empresa", page_icon="logo_fgv.png")

def get_connection():
    return snowflake.connector.connect(
        account   = st.secrets["snowflake"]["account"],
        user      = st.secrets["snowflake"]["user"],
        password  = st.secrets["snowflake"]["password"],
        warehouse = st.secrets["snowflake"]["warehouse"],
        database  = st.secrets["snowflake"]["database"],
        schema    = st.secrets["snowflake"]["schema"],
    )

@st.cache_data(show_spinner=False)
def get_cnae_options():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT DISTINCT CODIGO_DESCR FROM TB_CNAE_DESCR ORDER BY CODIGO_DESCR")
    opts = [r[0] for r in cur.fetchall()]
    cur.close(); conn.close()
    return opts

@st.cache_data(show_spinner=False)
def get_uf_options():
    conn = get_connection()
    cur  = conn.cursor()
    cur.execute("SELECT DISTINCT UF FROM TB_UF_MUNICIPIO ORDER BY UF")
    opts = [r[0] for r in cur.fetchall()]
    cur.close(); conn.close()
    return opts

def execute_search_query(selected_cnaes, selected_ufs):
    conn = get_connection()
    cnae_str = ",".join(f"'{c}'" for c in selected_cnaes)
    uf_str   = ",".join(f"'{u}'" for u in selected_ufs)
    sql = f"""
        SELECT *
        FROM TB_MVP_CONS
        WHERE UF IN ({uf_str})
          AND CNAE_DESCR IN ({cnae_str})
    """
    df = pd.read_sql(sql, conn)
    conn.close()
    return df

# inicializa estado
if "df_result_uf" not in st.session_state:
    st.session_state.df_result_uf = None

# filtros
with st.container(border=True):
    st.title("Filtros: CNAE/UF")
    cnae_opts      = get_cnae_options()
    uf_opts        = get_uf_options()
    col1, col2 = st.columns(2)
    selected_cnaes = col1.multiselect(
        "Atividade Econômica:",
        options=cnae_opts,
        default=[cnae_opts[0]] if cnae_opts else [],
        key="cnae_select_uf"
    )
    selected_ufs   = col2.multiselect(
        "UF:",
        options=uf_opts,
        default=[uf_opts[0]] if uf_opts else [],
        key="uf_select_uf",
        help="Digite a UF de interesse. (Exemplo: SP)"
    )
    if st.button("Pesquisar", key="search_uf"):
        st.session_state.df_result_uf = execute_search_query(selected_cnaes, selected_ufs)

df_uf = st.session_state.df_result_uf
# após carregar df_uf...
if df_uf is not None:
    if df_uf.empty:
        st.warning("Não há dados para exibir para os filtros selecionados")
    else:
        # configurações de paginação
        page_size = 50
        total_records = len(df_uf)
        total_pages = math.ceil(total_records / page_size)

        # inicializa ou lê página atual
        if "page_uf" not in st.session_state:
            st.session_state.page_uf = 1

        with st.container(border=True):
            # seletor de página
            st.session_state.page_uf = st.selectbox(
                "Página",
                options=list(range(1, total_pages + 1)),
                index=st.session_state.page_uf - 1,
                format_func=lambda x: f"{x} de {total_pages}"
            )

            # calcula intervalo de linhas
            start_idx = (st.session_state.page_uf - 1) * page_size
            end_idx   = min(start_idx + page_size, total_records)
            page_df   = df_uf.iloc[start_idx:end_idx]

            # indicação de quantos registros estão sendo mostrados
            st.write(f"Exibindo registros {start_idx+1}–{end_idx} de {total_records}")

            # botão de download (mantém o download de todo o df ou, se preferir, troque para page_df)
            towrite = BytesIO()
            df_uf.to_excel(towrite, index=False, sheet_name="Resultados")
            towrite.seek(0)
            st.download_button(
                "📥 Baixar resultados (XLSX)",
                data=towrite,
                file_name="cnae_uf_resultados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_uf"
            )

            # exibição paginada
            for _, record in page_df.iterrows():
                cnpj = record.get("CNPJ", "")
                razao = record.get("RAZAO_SOCIAL", "")
                header = f"{cnpj} – {razao}" if razao and pd.notna(razao) and str(razao).strip() else cnpj
                with st.expander(header):
                    st.write(record.to_dict())