import streamlit as st



def main():
    st.logo('logo_ibre.png')
    about = st.Page("home/sobre.py", title="Sobre", icon=":material/double_arrow:")
    
    cnae_uf = st.Page("consulta/cnae_uf.py", title="CNAE & UF", icon=":material/double_arrow:")
    cnae_cities = st.Page("consulta/cnae_cidades.py", title="CNAE & Cidades", icon=":material/double_arrow:")
    cnpj = st.Page("consulta/cnpj.py", title="CNPJ", icon=":material/double_arrow:")
    
    overview = st.Page("overview/visao_geral.py", title="Visão Geral", icon=":material/double_arrow:")
    
    cnae_codes = st.Page("codigos_cnae/tabela_completa.py", title="Tabela Completa", icon=":material/double_arrow:")
    
    data_dict = st.Page("layout/dicionario_dados.py", title="Dicionário de Dados", icon=":material/double_arrow:")
    
    
    pg = st.navigation(
        {
            "Home": [about],
            "Consulta": [cnae_uf, cnae_cities, cnpj],
            "Overview": [overview],
            "Códigos CNAE": [cnae_codes],
            "Layout": [data_dict]
        }
    )
    
    pg.run()


if __name__ == '__main__':

    main()
