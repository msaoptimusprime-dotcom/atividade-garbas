import io
import zipfile

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Dashboard de Saúde - UBS",
    page_icon="🏥",
    layout="wide"
)

st.title("🏥 Dashboard de Unidades Básicas de Saúde")
st.write(
    "Dashboard de análise das Unidades Básicas de Saúde (UBS), "
    "desenvolvido com Python, Pandas, Plotly e Streamlit."
)

# Nomes dos estados brasileiros
nomes_estados = {
    "AC": "Acre",
    "AL": "Alagoas",
    "AP": "Amapá",
    "AM": "Amazonas",
    "BA": "Bahia",
    "CE": "Ceará",
    "DF": "Distrito Federal",
    "ES": "Espírito Santo",
    "GO": "Goiás",
    "MA": "Maranhão",
    "MT": "Mato Grosso",
    "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais",
    "PA": "Pará",
    "PB": "Paraíba",
    "PR": "Paraná",
    "PE": "Pernambuco",
    "PI": "Piauí",
    "RJ": "Rio de Janeiro",
    "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul",
    "RO": "Rondônia",
    "RR": "Roraima",
    "SC": "Santa Catarina",
    "SP": "São Paulo",
    "SE": "Sergipe",
    "TO": "Tocantins"
}


def ler_csv(conteudo):
    """Lê um arquivo CSV e tenta identificar o separador."""
    for separador in [",", ";", "\t"]:
        for codificacao in ["utf-8", "latin-1"]:
            try:
                dados = pd.read_csv(
                    io.BytesIO(conteudo),
                    sep=separador,
                    encoding=codificacao
                )

                if len(dados.columns) > 1:
                    return dados

            except Exception:
                continue

    raise ValueError("Não foi possível ler o arquivo CSV.")


def carregar_dados(arquivo):
    """Carrega dados de um arquivo CSV ou ZIP."""
    conteudo = arquivo.getvalue()

    if arquivo.name.lower().endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(conteudo)) as pasta:
            arquivos_csv = [
                nome for nome in pasta.namelist()
                if nome.lower().endswith(".csv")
            ]

            if not arquivos_csv:
                raise ValueError("O ZIP não contém arquivos CSV.")

            return ler_csv(pasta.read(arquivos_csv[0]))

    return ler_csv(conteudo)


st.sidebar.header("Configurações")

arquivo = st.sidebar.file_uploader(
    "Envie o arquivo de dados",
    type=["csv", "zip"]
)

if arquivo is None:
    st.info("Envie o arquivo CSV ou ZIP para começar a análise.")
    st.stop()

try:
    df = carregar_dados(arquivo)
except Exception as erro:
    st.error(f"Erro ao carregar o arquivo: {erro}")
    st.stop()


# Tratamento inicial dos dados
df.columns = df.columns.str.strip().str.upper()

for coluna in df.select_dtypes(include="object").columns:
    df[coluna] = df[coluna].str.strip()

df = df.drop_duplicates()

# Verificação das colunas necessárias
if "UF" not in df.columns or "NOME" not in df.columns:
    st.error("O arquivo precisa conter as colunas UF e NOME.")
    st.write("Colunas encontradas:", list(df.columns))
    st.stop()

# Padronização das siglas dos estados
df["UF"] = df["UF"].astype("string").str.strip().str.upper()

# Criação da coluna com os nomes dos estados
df["ESTADO"] = df["UF"].map(nomes_estados)

# Remoção das colunas que não serão utilizadas
colunas_remover = [
    "LATITUDE",
    "LONGITUDE",
    "LOGRADOURO"
]

df = df.drop(
    columns=[
        coluna for coluna in colunas_remover
        if coluna in df.columns
    ]
)

# Filtro por nome do estado
st.sidebar.subheader("Filtros")

estados_disponiveis = sorted(
    df["ESTADO"].dropna().unique().tolist()
)

estados_selecionados = st.sidebar.multiselect(
    "Selecione os estados",
    options=estados_disponiveis,
    default=estados_disponiveis
)

dados_filtrados = df[
    df["ESTADO"].isin(estados_selecionados)
].copy()


# Indicadores gerais
total_ubs = len(dados_filtrados)
total_estados = dados_filtrados["ESTADO"].nunique()

col1, col2 = st.columns(2)

col1.metric("Total de UBS", f"{total_ubs:,}".replace(",", "."))
col2.metric("Estados selecionados", total_estados)

st.divider()


# Gráfico 1: UBS por estado
st.subheader("1. Quantidade de UBS por estado")

ubs_por_estado = (
    dados_filtrados["ESTADO"]
    .value_counts()
    .reset_index()
)

ubs_por_estado.columns = ["Estado", "Quantidade"]

ubs_por_estado = ubs_por_estado.sort_values(
    "Quantidade",
    ascending=False
)

fig_estados = px.bar(
    ubs_por_estado,
    x="Estado",
    y="Quantidade",
    title="Distribuição das UBS por estado",
    labels={
        "Estado": "Estado",
        "Quantidade": "Número de UBS"
    },
    color="Quantidade",
    color_continuous_scale="Blues"
)

fig_estados.update_layout(
    xaxis_title="Estado",
    yaxis_title="Quantidade de UBS"
)

st.plotly_chart(fig_estados, use_container_width=True)

st.write(
    "O gráfico compara a quantidade de UBS cadastradas em cada estado. "
    "Esses números representam os registros encontrados na base de dados "
    "e não indicam, isoladamente, a qualidade do atendimento."
)


# Gráfico 2: distribuição das UBS
st.subheader("2. Participação de cada estado")

fig_pizza = px.pie(
    ubs_por_estado,
    names="Estado",
    values="Quantidade",
    title="Proporção de UBS por estado",
    hole=0.4
)

st.plotly_chart(fig_pizza, use_container_width=True)

st.write(
    "O gráfico mostra a participação de cada estado no total de UBS "
    "presentes nos dados filtrados."
)


# Tabela de dados
st.subheader("3. Dados das UBS")

# Oculta as siglas e apresenta os nomes dos estados
colunas_exibicao = [
    coluna for coluna in dados_filtrados.columns
    if coluna not in ["UF", "LATITUDE", "LONGITUDE", "LOGRADOURO"]
]

st.dataframe(
    dados_filtrados[colunas_exibicao],
    use_container_width=True,
    hide_index=True
)


# Download dos dados tratados
csv_tratado = dados_filtrados[colunas_exibicao].to_csv(
    index=False,
    sep=";",
    encoding="utf-8-sig"
)

st.download_button(
    label="📥 Baixar dados tratados",
    data=csv_tratado,
    file_name="ubs_dados_tratados.csv",
    mime="text/csv"
)

st.divider()

st.caption(
    "Projeto escolar de Ciência de Dados | "
    "Python, Pandas, Plotly e Streamlit."
)
