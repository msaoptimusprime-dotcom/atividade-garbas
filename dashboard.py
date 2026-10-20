import io
import zipfile

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Dashboard de Saúde - UBS",
    layout="wide"
)

st.title("Dashboard de Unidades Básicas de Saúde")
st.write(
    "Análise das Unidades Básicas de Saúde (UBS) "
    "utilizando Python, Pandas, Plotly e Streamlit."
)


# Dicionário com os nomes dos estados brasileiros
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


ARQUIVO_FIXO = "Unidades_Basicas_Saude-UBS_csv.zip"


def ler_csv(conteudo):
    """Lê um CSV identificando automaticamente o separador."""
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
        f"Não foi possível interpretar o CSV: {ultimo_erro}"
    )


def carregar_dados(caminho):
    with zipfile.ZipFile(caminho) as pasta:
        arquivos_csv = [
            nome for nome in pasta.namelist()
            if nome.lower().endswith(".csv")
            and not nome.startswith("__MACOSX/")
        ]

        if not arquivos_csv:
            raise ValueError("O arquivo ZIP não contém nenhum CSV.")

        return ler_csv(pasta.read(arquivos_csv[0]))


try:
    df = carregar_dados(ARQUIVO_FIXO)

except FileNotFoundError:
    st.error(
        "O arquivo ZIP não foi encontrado. "
        "Adicione-o ao repositório do GitHub, na mesma pasta do dashboard.py."
    )
    st.stop()

except Exception as erro:
    st.error(f"Erro ao carregar os dados: {erro}")
    st.stop()

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
        f"Não foi possível interpretar o CSV. Detalhes: {ultimo_erro}"
    )


def carregar_dados(arquivo):
    """Carrega dados de um CSV ou de um ZIP que contenha um CSV."""
    conteudo = arquivo.getvalue()

    if arquivo.name.lower().endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(conteudo)) as pasta:
            arquivos_csv = [
                nome for nome in pasta.namelist()
                if nome.lower().endswith(".csv")
                and not nome.startswith("__MACOSX/")
            ]

            if not arquivos_csv:
                raise ValueError(
                    "Não foi encontrado nenhum arquivo CSV dentro do ZIP."
                )

            # Utiliza o primeiro CSV encontrado
            return ler_csv(pasta.read(arquivos_csv[0]))

    return ler_csv(conteudo)


# Envio do arquivo
st.sidebar.header("Configurações")

arquivo = st.sidebar.file_uploader(
    "Envie o arquivo de dados",
    type=["csv", "zip"]
)

if arquivo is None:
    st.info("Envie o arquivo CSV ou ZIP para começar a análise.")
    st.stop()


# Leitura do arquivo
try:
    df = carregar_dados(arquivo)

except Exception as erro:
    st.error(f"Erro ao carregar o arquivo: {erro}")
    st.stop()


# Limpeza básica dos dados
df.columns = df.columns.str.strip().str.upper()

for coluna in df.select_dtypes(include="object").columns:
    df[coluna] = df[coluna].str.strip()

df = df.drop_duplicates()

# Verifica as colunas necessárias
if "UF" not in df.columns or "NOME" not in df.columns:
    st.error(
        "As colunas UF e NOME não foram encontradas. "
        "Confira a estrutura do arquivo enviado."
    )
    st.write("Colunas encontradas:", df.columns.tolist())
    st.stop()


# Padroniza a coluna de estado
df["UF"] = df["UF"].astype("string").str.strip().str.upper()

# Converte códigos numéricos de UF para siglas, caso necessário
codigos_uf = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR",
    "15": "PA", "16": "AP", "17": "TO", "21": "MA",
    "22": "PI", "23": "CE", "24": "RN", "25": "PB",
    "26": "PE", "27": "AL", "28": "SE", "29": "BA",
    "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
    "41": "PR", "42": "SC", "43": "RS", "50": "MS",
    "51": "MT", "52": "GO", "53": "DF"
}

df["UF"] = df["UF"].replace(codigos_uf)

# Cria a coluna com o nome completo do estado
df["ESTADO"] = df["UF"].map(nomes_estados)

# Remove linhas sem informação de estado
df = df.dropna(subset=["ESTADO"])

# Remove colunas que não serão utilizadas
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


# Filtros
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


# Indicadores
total_ubs = len(dados_filtrados)
total_estados = dados_filtrados["ESTADO"].nunique()

st.subheader("Indicadores gerais")

col1, col2 = st.columns(2)

col1.metric(
    "Total de UBS",
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
        "Este gráfico permite comparar a quantidade de UBS "
        "registradas em cada estado. Uma quantidade maior de "
        "unidades não significa, por si só, que o atendimento "
        "à população seja melhor."
    )
else:
    st.warning("Não há dados para os estados selecionados.")


# Gráfico 2: participação de cada estado
st.subheader("2. Proporção de UBS por estado")

if not ubs_por_estado.empty:
    fig_pizza = px.pie(
        ubs_por_estado,
        names="ESTADO",
        values="Quantidade",
        title="Participação dos estados no total de UBS",
        hole=0.4
    )

    st.plotly_chart(
        fig_pizza,
        use_container_width=True
    )

    st.write(
        "Este gráfico apresenta a proporção de UBS de cada "
        "estado em relação ao total de unidades dos estados "
        "selecionados."
    )
else:
    st.warning("Não há dados para gerar o gráfico.")


# Tabela dos dados tratados
st.subheader("3. Tabela de dados das UBS")

# Exibe o nome completo do estado e oculta as colunas removidas
colunas_exibicao = [
    coluna for coluna in dados_filtrados.columns
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
