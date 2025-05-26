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
    cnpj = cnpj.translate(str.maketrans("", "", "./-"))
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
        input_cnpj = st.text_input("CNPJ:", value="", key="input_cnpj", help="Digite o CNPJ de interesse (Exemplo: 26909999000260 ou 26.909.999/0002-60)")
        pesquisar  = st.button("Pesquisar", key="search_cnpj")
    return input_cnpj, pesquisar

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
                for _, row in df_result.iterrows():
                    cnpj          = safe(row.get("CNPJ"))
                    nome_fant     = safe(row.get("NOME_FANTASIA"))
                    matriz_filial = safe(row.get("MATRIZ_FILIAL"))
                    porte         = safe(row.get("PORTE"))
                    capital       = safe(row.get("CAPITAL"))
                    cnae_fiscal   = safe(row.get("CNAE_FISCAL"))
                    cnae_descr    = safe(row.get("CNAE_DESCR"))

                    # monta o título do expander
                    title = f"{cnpj} | {nome_fant} | {matriz_filial} | {porte} | {capital} | {cnae_fiscal} | {cnae_descr}"
                    
                    with st.expander(title):
                        st.write(formatar_texto(row))

input_cnpj, pesquisar = mod_cons_cnpj_ui()
mod_cons_cnpj_server(input_cnpj, pesquisar)
