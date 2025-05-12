import streamlit as st


st.set_page_config(
    page_title="Sobre - Sistema Web Empresa", 
    page_icon="logo_fgv.png"
)

container = st.container(border=True)

container.markdown("""
    ## Sistema Web Empresas

    [![Lifecycle: experimental](https://img.shields.io/badge/lifecycle-experimental-orange.svg)](https://lifecycle.r-lib.org/articles/stages.html#experimental)

    Essa ferramenta tem por objetivo democratizar o acesso à base de dados da Receita Federal no âmbito da SPDO, atendendo as demandas de mapeamento e cadastro, bem como estimativas de amostras com empresas válidas e outros tipos de prospeções comerciais.

    Através de uma interface amigável e de fácil acesso o `<app>` permite a consulta de dados cadastrais de milhões de empresas ativas.

    Até a presente versão, a consulta ao banco de dados pode ser realizada a partir:

    * da atividade econômica e da unidade federativa >> Módulo: CNAE & UF;
    * da atividade econômica e a nível municipal >> Módulo: CNAE & Cidades;
    * do CNPJ >> Módulo: CNPJ.

    Os dados foram obtidos em [Dados Públicos CNPJ - Receita Federal](https://dados.gov.br/dados/conjuntos-dados/cadastro-nacional-da-pessoa-juridica-cnpj) e atualizados em: 14/08/2024 11:48:00.
    """, unsafe_allow_html=False)

    # Linha horizontal (divisor)
container.markdown("---")