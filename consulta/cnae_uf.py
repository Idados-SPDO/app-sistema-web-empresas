import streamlit as st
import pandas as pd
import snowflake.connector
from io import BytesIO
import math
from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(page_title="CNAE/UF - Sistema Web Empresa", page_icon="logo_fgv.png",layout='wide')

st.markdown("""
<style>
span[data-baseweb="tag"] {
  color: white;
  background-color: #0E59E6;
}
</style>
""", unsafe_allow_html=True)

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

# labels e função formatar_texto (mantidos iguais)
labels = {
    "CNPJ": "CNPJ",
    "NOME_FANTASIA": "Nome Fantasia",
    "RAZAO_SOCIAL": "Razão Social",
    "MATRIZ_FILIAL": "Matriz/Filial",
    "PORTE": "Porte",
    "CAPITAL": "Capital Social",
    "SITUACAO": "Situação",
    "CNAE_FISCAL": "CNAE Fiscal",
    "CNAE_DESCR": "Descrição CNAE",
    "CNAE_SECUNDARIO": "CNAE Secundário",
    "LOGRADOURO": "Logradouro",
    "NUMERO": "Número",
    "COMPLEMENTO": "Complemento",
    "BAIRRO": "Bairro",
    "CEP": "CEP",
    "UF": "UF",
    "MUNICIPIO": "Município",
    "DDD_1": "DDD 1",
    "TELEFONE_1": "Telefone 1",
    "DDD_2": "DDD 2",
    "TELEFONE_2": "Telefone 2",
    "EMAIL": "E-mail"
}

def formatar_texto(row: pd.Series) -> str:
    linhas = []
    for col, rotulo in labels.items():
        valor = row.get(col, "")
        if pd.notna(valor) and str(valor).strip():
            linhas.append(f"**{rotulo}:** {valor}")
    return "\n\n".join(linhas)

# --- filtros e armazenamento em session_state.df_result_uf (igual) ---

if "df_result_uf" not in st.session_state:
    st.session_state.df_result_uf = None

with st.container(border=True):
    st.title("Filtros: CNAE/UF")
    cnae_opts    = get_cnae_options()
    uf_opts      = get_uf_options()
    c1, c2       = st.columns(2)
    sel_cnaes    = c1.multiselect("Atividade Econômica:", options=cnae_opts, key="cnae_select_uf")
    sel_ufs      = c2.multiselect("UF:", options=uf_opts, key="uf_select_uf")
    if st.button("Pesquisar", key="search_uf"):
        st.session_state.df_result_uf = execute_search_query(sel_cnaes, sel_ufs)

df_uf = st.session_state.df_result_uf

# se não veio nada
if df_uf is None:
    st.info("Use os filtros acima e clique em Pesquisar.")
elif df_uf.empty:
    st.warning("Não há dados para exibir para os filtros selecionados")
else:
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df_uf.to_excel(writer, index=False, sheet_name="Empresas")
        writer.close()
    output.seek(0)  # volta o cursor para o início do buffer

    st.download_button(
        label="📥 Baixar dados filtrados (Excel)",
        data=output,
        file_name=f"consulta-cnae-uf.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        help="Exporta todos os registros que atendem aos filtros"
    )
    # 1) prepara o DataFrame que será exibido (só 4 colunas + índice original)
    cols_visíveis = ["CNPJ", "NOME_FANTASIA", "MATRIZ_FILIAL", "PORTE", "CAPITAL","CNAE_FISCAL", "CNAE_DESCR"]
    disp = df_uf[cols_visíveis].copy()
    disp["orig_index"] = disp.index  # mantém referência para a linha completa
    
    page_size     = 50
    total_records = len(disp)
    total_pages   = math.ceil(total_records / page_size)

    if "page_uf" not in st.session_state:
        st.session_state.page_uf = 1
    
    page = st.selectbox(
        "Página",
        options=list(range(1, total_pages + 1)),
        index=st.session_state.page_uf - 1,
        format_func=lambda x: f"{x} de {total_pages}",
        key="page_uf"
    )

    start_idx = (page - 1) * page_size
    end_idx   = min(start_idx + page_size, total_records)
    page_disp = disp.iloc[start_idx:end_idx]

    st.write(f"Exibindo registros {start_idx+1}–{end_idx} de {total_records}")

    # 3) configura AgGrid sobre esta página
    gb = GridOptionsBuilder.from_dataframe(page_disp)
    gb.configure_selection("single", use_checkbox=False)
    gb.configure_column("orig_index", hide=True)
    grid_opts = gb.build()

    grid_resp = AgGrid(
        page_disp,
        gridOptions=grid_opts,
        enable_enterprise_modules=False,
        theme="streamlit",
        height=600,
        fit_columns_on_grid_load=True,
    )

    # 4) captura seleção e busca a linha completa em df_uf
    sel = grid_resp["selected_rows"]
    full_row = None
    if isinstance(sel, list) and sel:
        idx = sel[0]["orig_index"]
        full_row = df_uf.loc[idx]
    elif isinstance(sel, pd.DataFrame) and not sel.empty:
        idx = sel.iloc[0]["orig_index"]
        full_row = df_uf.loc[idx]

    # 5) abre o modal com todos os campos
    if full_row is not None:
        @st.dialog("Detalhes da empresa")
        def show_details():
            st.markdown("#### Dados completos:")
            st.markdown(formatar_texto(full_row))
        show_details()
