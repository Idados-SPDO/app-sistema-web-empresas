import streamlit as st
import pandas as pd
import snowflake.connector
import math
from io import BytesIO

st.set_page_config(page_title="CNAE/Cidades - Sistema Web Empresa", page_icon="logo_fgv.png")

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
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT DISTINCT CODIGO_DESCR FROM TB_CNAE_DESCR ORDER BY CODIGO_DESCR")
    opts = [r[0] for r in cur.fetchall()]
    cur.close(); conn.close()
    return opts

@st.cache_data(show_spinner=False)
def get_uf_options():
    conn = get_connection(); cur = conn.cursor()
    cur.execute("SELECT DISTINCT UF FROM TB_UF_MUNICIPIO ORDER BY UF")
    opts = [r[0] for r in cur.fetchall()]
    cur.close(); conn.close()
    return opts

@st.cache_data(show_spinner=False)
def get_municipio_options(selected_ufs):
    conn    = get_connection()
    ufs_str = ",".join(f"'{u}'" for u in selected_ufs)
    cur     = conn.cursor()
    cur.execute(f"""
        SELECT DISTINCT MUNICIPIO
        FROM TB_UF_MUNICIPIO
        WHERE UF IN ({ufs_str})
        ORDER BY MUNICIPIO
    """)
    opts = [r[0] for r in cur.fetchall()]
    cur.close(); conn.close()
    return opts

def execute_search_query(selected_cnaes, selected_ufs, selected_municipios):
    conn = get_connection()
    cur  = conn.cursor()

    clauses = []
    if selected_cnaes:
        cnae_str = ",".join(f"'{c}'" for c in selected_cnaes)
        clauses.append(f"CNAE_DESCR IN ({cnae_str})")
    if selected_ufs:
        uf_str = ",".join(f"'{u}'" for u in selected_ufs)
        clauses.append(f"UF IN ({uf_str})")
    if selected_municipios:
        mun_str = ",".join(f"'{m}'" for m in selected_municipios)
        clauses.append(f"MUNICIPIO IN ({mun_str})")

    sql = "SELECT * FROM TB_MVP_CONS"
    if clauses:
        sql += " WHERE " + " AND ".join(clauses)

    cur.execute(sql)
    data = cur.fetchall()
    cols = [d[0] for d in cur.description]
    cur.close(); conn.close()
    return pd.DataFrame(data, columns=cols)

# estado inicial
if "df_result_city" not in st.session_state:
    st.session_state.df_result_city = None
if "current_page_city" not in st.session_state:
    st.session_state.current_page_city = 1

with st.container(border=True):
    st.title("Filtros: CNAE/UF/Município")

    # 1) Sempre exibe Atividade Econômica
    cnae_opts = get_cnae_options()
    selected_cnaes = st.multiselect(
        "Atividade Econômica:",
        options=cnae_opts,
        default=[],
        key="cnae_select_city"
    )

    col1, col2 = st.columns(2)

    # 2) Sempre exibe UF
    uf_opts = get_uf_options()
    selected_ufs = col1.multiselect(
        "UF:",
        options=uf_opts,
        default= [],
        key="uf_select_city",
        help="Digite a UF de interesse. (Ex: SP)"
    )

    # 3) Sempre exibe Município (mesmo que a lista venha vazia)
    municipio_opts = get_municipio_options(selected_ufs) if selected_ufs else []
    selected_municipios = col2.multiselect(
        "Município:",
        options=municipio_opts,
        default=[],
        key="municipio_select_city",
        help="Selecione quantos municípios desejar."
    )

    # 4) Botão SEM trava: sempre ativo
    if st.button("Pesquisar", key="search_city"):
        st.session_state.df_result_city = execute_search_query(
            selected_cnaes, selected_ufs, selected_municipios
        )
        st.session_state.current_page_city = 1


df_city = st.session_state.df_result_city

if df_city is not None:
    if df_city.empty:
        st.warning("Não há dados para exibir para os filtros selecionados")
    else:
        # configurações de paginação
        page_size     = 50
        total_records = len(df_city)
        total_pages   = math.ceil(total_records / page_size)
        with st.container(border=True):
            
            # seletor de página
            st.session_state.current_page_city = st.selectbox(
                "Página",
                options=list(range(1, total_pages + 1)),
                index=st.session_state.current_page_city - 1,
                format_func=lambda x: f"{x} de {total_pages}"
            )

            # intervalo de linhas
            start_idx = (st.session_state.current_page_city - 1) * page_size
            end_idx   = min(start_idx + page_size, total_records)
            page_df   = df_city.iloc[start_idx:end_idx]

            # indicação de registros
            st.write(f"Exibindo registros {start_idx+1}–{end_idx} de {total_records}")

            # botão de download (todo o df)
            towrite = BytesIO()
            df_city.to_excel(towrite, index=False, sheet_name="Resultados")
            towrite.seek(0)
            st.download_button(
                "📥 Baixar resultados (XLSX)",
                data=towrite,
                file_name="cnae_cidades_resultados.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="download_city"
            )

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
                # separa com duas quebras de linha para melhor leitura no Markdown
                return "\n\n".join(linhas)
            def safe(val):
                return val if pd.notna(val) and str(val).strip() else "--"

            header_cols = [
                "CNPJ",
                "Nome Fantasia",
                "Matriz/Filial",
                "Porte",
                "Capital",
                "CNAE Fiscal",
                "Descrição CNAE"
            ]
            st.markdown("**" + "** | **".join(header_cols) + "**")
            # exibição paginada
            for _, record in page_df.iterrows():
                cnpj          = safe(record.get("CNPJ"))
                nome_fant     = safe(record.get("NOME_FANTASIA"))
                matriz_filial = safe(record.get("MATRIZ_FILIAL"))
                porte         = safe(record.get("PORTE"))
                capital       = safe(record.get("CAPITAL"))
                cnae_fiscal   = safe(record.get("CNAE_FISCAL"))
                cnae_descr    = safe(record.get("CNAE_DESCR"))

                # monta o título do expander
                title = f"{cnpj} | {nome_fant} | {matriz_filial} | {porte} | {capital} | {cnae_fiscal} | {cnae_descr}"
                with st.expander(title):
                    st.write(formatar_texto(record))
