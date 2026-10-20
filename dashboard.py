import io
import zipfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# Configuração da página
st.set_page_config(
    page_title="Dashboard de Saúde - UBS",
    layout="wide"
)

st.title("Dashboard de Unidades Básicas de Saúde")
st.write(
    "Análise das Unidades Básicas de Saúde (UBS) "
    "utilizando Python, Pandas, Plotly e Streamlit."
)


# Arquivo de dados salvo junto ao dashboard.py
ARQUIVO_FIXO = (
    Path(__file__).parent
    / "Unidades_Basicas_Saude-UBS_csv.zip"
)


# Dicionário de siglas e nomes dos estados
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

# Códigos numéricos utilizados para identificar os estados
codigos_uf = {
    "11": "RO",
    "12": "AC",
    "13": "AM",
    "14": "RR",
    "15": "PA",
    "16": "AP",
    "17": "TO",
    "21": "MA",
    "22": "PI",
    "23": "CE",
    "24": "RN",
    "25": "PB",
    "26": "PE",
    "27": "AL",
    "28": "SE",
    "29": "BA",
    "31": "MG",
    "32": "ES",
    "33": "RJ",
    "35": "SP",
    "41": "PR",
    "42": "SC",
    "43": "RS",
    "50": "MS",
    "51": "MT",
    "52": "GO",
    "53": "DF"
}

# Permite reconhecer também nomes completos dos estados
estados_por_nome = {
    nome.casefold(): sigla
    for sigla, nome in nomes_estados.items()
}


def ler_csv(conteudo):
    """Lê o CSV tentando identificar o separador e a codificação."""

    ultimo_erro = None

    for codificacao in ["utf-8-sig", "latin-1"]:
        try:
            dados = pd.read_csv(
                io.BytesIO(conteudo),
                sep=None,
                engine="python",
                encoding=codificacao,
                dtype=str
            )

            dados.columns = (
                dados.columns
                .str.strip()
                .str.replace("\ufeff", "", regex=False)
                .str.upper()
            )

            if len(dados.columns) > 1:
                return dados

        except Exception as erro:
            ultimo_erro = erro

    raise ValueError(
        f"Não foi possível ler o CSV: {ultimo_erro}"
    )


def carregar_dados(caminho):
    """Carrega o primeiro arquivo CSV encontrado dentro do ZIP."""

    with zipfile.ZipFile(caminho, "r") as pasta:
        arquivos_csv = [
            nome
            for nome in pasta.namelist()
            if nome.lower().endswith(".csv")
            and not nome.startswith("__MACOSX/")
        ]

        if not arquivos_csv:
            raise ValueError(
                "Não foi encontrado nenhum arquivo CSV dentro do ZIP."
            )

        return ler_csv(pasta.read(arquivos_csv[0]))


# Carregamento automático do arquivo
try:
    if not ARQUIVO_FIXO.exists():
        st.error(
            "O arquivo de dados não foi encontrado. "
            "Adicione Unidades_Basicas_Saude-UBS_csv.zip "
            "à mesma pasta do dashboard.py no GitHub."
        )
        st.stop()

    df = carregar_dados(ARQUIVO_FIXO)

except Exception as erro:
    st.error(f"Erro ao carregar os dados: {erro}")
    st.stop()


# Tratamento básico dos dados
df.columns = df.columns.str.strip().str.upper()

for coluna in df.select_dtypes(include="object").columns:
    df[coluna] = df[coluna].str.strip()

df = df.drop_duplicates()

# Verifica as colunas necessárias
colunas_obrigatorias = ["UF", "NOME"]
colunas_ausentes = [
    coluna
    for coluna in colunas_obrigatorias
    if coluna not in df.columns
]

if colunas_ausentes:
    st.error(
        "O arquivo não contém todas as colunas necessárias: "
        + ", ".join(colunas_ausentes)
    )
    st.write("Colunas encontradas:", df.columns.tolist())
    st.stop()


# Padronização dos estados
def identificar_estado(valor):
    """Converte siglas, códigos ou nomes em nomes completos."""

    if pd.isna(valor):
        return None

    valor = str(valor).strip()

    if not valor:
        return None

    # Verifica códigos numéricos, como 35 para São Paulo
    codigo = valor.replace(".0", "")

    if codigo in codigos_uf:
        sigla = codigos_uf[codigo]
        return nomes_estados[sigla]

    # Verifica siglas, como SP
    sigla = valor.upper()

    if sigla in nomes_estados:
        return nomes_estados[sigla]

    # Verifica nomes completos, como São Paulo
    nome_normalizado = valor.casefold()

    if nome_normalizado in estados_por_nome:
        sigla = estados_por_nome[nome_normalizado]
        return nomes_estados[sigla]

    return None


df["ESTADO"] = df["UF"].apply(identificar_estado)

# Informa se existem registros sem estado reconhecido
estados_invalidos = df["ESTADO"].isna().sum()

if estados_invalidos > 0:
    st.warning(
        f"{estados_invalidos} registros não possuem um estado "
        "reconhecido e não serão incluídos nos gráficos."
    )

df = df.dropna(subset=["ESTADO"]).copy()

if df.empty:
    st.error(
        "Nenhum estado foi reconhecido na coluna UF. "
        "Verifique os dados do arquivo."
    )
    st.stop()


# Remoção das colunas que não serão utilizadas
colunas_remover = [
    "LATITUDE",
    "LONGITUDE",
    "LOGRADOURO"
]

df = df.drop(
    columns=[
        coluna
        for coluna in colunas_remover
        if coluna in df.columns
    ]
)


# Filtros
st.sidebar.header("Filtros")

estados_disponiveis = sorted(
    df["ESTADO"].unique().tolist()
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
st.subheader("Indicadores gerais")

total_ubs = len(dados_filtrados)
total_estados = dados_filtrados["ESTADO"].nunique()

col1, col2 = st.columns(2)

col1.metric(
    "Total de UBS cadastradas",
    f"{total_ubs:,}".replace(",", ".")
)

col2.metric(
    "Estados selecionados",
    total_estados
)

st.divider()


# Gráfico 1: quantidade de UBS por estado
st.subheader("1. Quantidade de UBS por estado")

ubs_por_estado = (
    dados_filtrados.groupby("ESTADO")
    .size()
    .reset_index(name="Quantidade")
    .sort_values("Quantidade", ascending=False)
)

if not ubs_por_estado.empty:

    fig_estados = px.bar(
        ubs_por_estado,
        x="ESTADO",
        y="Quantidade",
        title="Distribuição das UBS por estado",
        labels={
            "ESTADO": "Estado",
            "Quantidade": "Número de UBS"
        },
        color="Quantidade",
        color_continuous_scale="Blues"
    )

    fig_estados.update_layout(
        xaxis_title="Estado",
        yaxis_title="Quantidade de UBS",
        xaxis_tickangle=-45
    )

    st.plotly_chart(
        fig_estados,
        use_container_width=True
    )

    st.write(
        "O gráfico compara a quantidade de unidades cadastradas "
        "em cada estado. Uma quantidade maior de UBS não significa, "
        "necessariamente, que o atendimento à população seja melhor."
    )

else:
    st.warning("Não há dados para os estados selecionados.")


# Gráfico 2: proporção de UBS por estado
st.subheader("2. Proporção de UBS por estado")

if not ubs_por_estado.empty:

    fig_pizza = px.pie(
        ubs_por_estado,
        names="ESTADO",
        values="Quantidade",
        title="Participação de cada estado no total de UBS",
        hole=0.4
    )

    st.plotly_chart(
        fig_pizza,
        use_container_width=True
    )

    st.write(
        "O gráfico mostra a proporção de unidades cadastradas "
        "em cada estado em relação ao total dos estados selecionados."
    )

else:
    st.warning("Não há dados para gerar o gráfico.")


# Tabela de dados tratados
st.subheader("3. Tabela de dados das UBS")

colunas_exibicao = [
    coluna
    for coluna in dados_filtrados.columns
    if coluna not in [
        "UF",
        "LATITUDE",
        "LONGITUDE",
        "LOGRADOURO"
    ]
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
    label="Baixar dados tratados",
    data=csv_tratado,
    file_name="ubs_dados_tratados.csv",
    mime="text/csv"
)


# Informações finais
st.divider()

st.caption(
    "Projeto escolar de Ciência de Dados. "
    "Ferramentas utilizadas: Python, Pandas, Plotly e Streamlit."
)
