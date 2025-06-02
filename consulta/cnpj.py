import streamlit as st
import pandas as pd
import snowflake.connector
import math
from st_aggrid import AgGrid, GridOptionsBuilder

st.set_page_config(page_title="CNPJ - Sistema Web Empresa", page_icon="logo_fgv.png", layout='wide')

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
    # Remove pontos, barras e traços
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
        input_cnpj = st.text_input(
            "CNPJ:", 
            value="", 
            key="input_cnpj", 
            help="Digite o CNPJ de interesse (Ex: 26909999000260 ou 26.909.999/0002-60)"
        )
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
    # 1) Se o usuário clicou em "Pesquisar", executa a query e guarda em session_state
    if pesquisar:
        if not input_cnpj.strip():
            st.error("Por favor, insira um CNPJ válido.")
            return
        with st.spinner("Executando a query..."):
            df_result = execute_search_query_cnpj(input_cnpj.strip())
        # Guarda em session_state para persistir entre reruns
        st.session_state.df_cnpj = df_result

    # 2) Se já existia um resultado salvo em session_state, reusa-o para exibir a grade
    if "df_cnpj" not in st.session_state:
        return  # nada a fazer até que o usuário pesquise ao menos uma vez

    df_result = st.session_state.df_cnpj

    # 3) Se estiver vazio, mostra aviso e retorna
    if df_result.empty:
        st.warning("Não há dados para o CNPJ informado.")
        return

    # 4) Garante que existe a coluna orig_index
    if "orig_index" not in df_result.columns:
        df_result["orig_index"] = df_result.index

    # 5) Monta o DataFrame 'disp' apenas com as colunas que vamos exibir + orig_index
    cols_visiveis = [
        "CNPJ",
        "NOME_FANTASIA",
        "MATRIZ_FILIAL",
        "PORTE",
        "CAPITAL",
        "CNAE_FISCAL",
        "CNAE_DESCR",
        "orig_index"
    ]
    disp = df_result[cols_visiveis].copy()

    # 6) Paginação
    page_size     = 50
    total_records = len(disp)
    total_pages   = math.ceil(total_records / page_size)

    with st.container(border=True):
        # Se tiver mais de uma página, exibe o selectbox
        if total_pages > 1:
            current_page = st.selectbox(
                "Página",
                options=list(range(1, total_pages + 1)),
                index=0,
                format_func=lambda x: f"{x} de {total_pages}",
                key="page_cnpj"
            )
        else:
            current_page = 1

        start_idx = (current_page - 1) * page_size
        end_idx   = min(start_idx + page_size, total_records)
        page_df   = disp.iloc[start_idx:end_idx]

        st.write(f"Exibindo registros {start_idx + 1}–{end_idx} de {total_records}")

        # 7) Configura o AgGrid
        gb = GridOptionsBuilder.from_dataframe(page_df)
        gb.configure_selection("single", use_checkbox=False)
        gb.configure_column("orig_index", hide=True)  # oculta, mas mantém disponível
        grid_opts = gb.build()

        grid_resp = AgGrid(
            page_df,
            gridOptions=grid_opts,
            enable_enterprise_modules=False,
            theme="streamlit",
            height=600,
            fit_columns_on_grid_load=True,
        )

        # 8) Verifica se há linha selecionada
        sel = grid_resp["selected_rows"]
        selected_index = None
        if isinstance(sel, list) and sel:
            selected_index = sel[0]["orig_index"]
        elif isinstance(sel, pd.DataFrame) and not sel.empty:
            selected_index = sel.iloc[0]["orig_index"]

        # 9) Se houver seleção, guarda em session_state para manter entre reruns
        if selected_index is not None:
            st.session_state.selected_index_cnpj = selected_index
        else:
            # Caso o usuário clique fora da linha, limpa a seleção anterior
            if "selected_index_cnpj" in st.session_state:
                st.session_state.pop("selected_index_cnpj")

    # 10) Depois de tudo, se ainda estiver setado selected_index_cnpj, exibe o diálogo
    if "selected_index_cnpj" in st.session_state:
        idx = st.session_state.selected_index_cnpj
        full_row = df_result.loc[idx]

        @st.dialog("Detalhes da empresa")
        def show_details():
            st.markdown("#### Dados completos:")
            st.markdown(formatar_texto(full_row))

        show_details()


# === Chamadas principais ===
input_cnpj, pesquisar = mod_cons_cnpj_ui()
mod_cons_cnpj_server(input_cnpj, pesquisar)
