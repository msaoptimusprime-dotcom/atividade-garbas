import io
import zipfile

import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Dashboard de Saúde - UBS",
    layout="wide"
)

st.title("Dashboard de UBS")
st.write(
    "Este projeto apresenta uma análise dos dados das Unidades "
    "Básicas de Saúde (UBS) utilizando Pandas, Plotly e Streamlit."
)

st.sidebar.header("Configurações")
arquivo = st.sidebar.file_uploader(
    "Envie o arquivo de dados",
    type=["csv", "zip"]
)


def ler_csv(conteudo):
    """Lê um CSV tentando identificar a separação das colunas."""
    for separador in [",", ";", "\t"]:
        try:
            dados = pd.read_csv(
                io.BytesIO(conteudo),
                sep=separador,
                encoding="utf-8"
            )

            if len(dados.columns) > 1:
                return dados
        except UnicodeDecodeError:
            break

    for separador in [",", ";", "\t"]:
        try:
            dados = pd.read_csv(
                io.BytesIO(conteudo),
                sep=separador,
                encoding="latin-1"
            )

            if len(dados.columns) > 1:
                return dados
        except Exception:
            continue

    raise ValueError("Não foi possível ler o arquivo CSV.")


def carregar_dados(arquivo):
    """Carrega os dados de um arquivo CSV ou ZIP."""
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


if arquivo is None:
    st.info("Envie o arquivo CSV ou ZIP para visualizar a análise.")
    st.stop()


try:
    df = carregar_dados(arquivo)
except Exception as erro:
    st.error(f"Erro ao carregar os dados: {erro}")
    st.stop()


# Limpeza básica dos dados
df.columns = df.columns.str.strip().str.upper()

for coluna in df.select_dtypes(include="object").columns:
    df[coluna] = df[coluna].str.strip()

df = df.drop_duplicates()

# Verifica se as colunas principais existem
colunas_obrigatorias = ["UF", "NOME"]

for coluna in colunas_obrigatorias:
    if coluna not in df.columns:
        st.error(f"A coluna obrigatória '{coluna}' não foi encontrada.")
        st.write("Colunas disponíveis:", list(df.columns))
        st.stop()

# Padroniza os estados
df["UF"] = df["UF"].astype("string").str.strip().str.upper()

# Converte coordenadas para números, quando disponíveis
for coluna in ["LATITUDE", "LONGITUDE"]:
    if coluna in df.columns:
        df[coluna] = pd.to_numeric(
            df[coluna].astype(str).str.replace(",", ".", regex=False),
            errors="coerce"
        )

# Filtros
st.sidebar.subheader("Filtros")

estados = sorted(df["UF"].dropna().unique().tolist())

estados_selecionados = st.sidebar.multiselect(
    "Selecione o estado",
    options=estados,
    default=estados
)

dados_filtrados = df[df["UF"].isin(estados_selecionados)].copy()

# Indicadores
total_ubs = len(dados_filtrados)
total_estados = dados_filtrados["UF"].nunique()

if "LATITUDE" in dados_filtrados.columns and \
        "LONGITUDE" in dados_filtrados.columns:

    coordenadas_validas = dados_filtrados[
        dados_filtrados["LATITUDE"].notna()
        & dados_filtrados["LONGITUDE"].notna()
    ]

    total_coordenadas = len(coordenadas_validas)

else:
    coordenadas_validas = pd.DataFrame()
    total_coordenadas = 0

st.subheader("Indicadores gerais")

col1, col2, col3 = st.columns(3)

col1.metric("Total de UBS", f"{total_ubs:,}".replace(",", "."))
col2.metric("Estados encontrados", total_estados)
col3.metric(
    "UBS com coordenadas",
    f"{total_coordenadas:,}".replace(",", ".")
)

st.divider()

# Gráfico 1: quantidade de UBS por estado
st.subheader("1. Quantidade de UBS por estado")

ubs_por_estado = (
    dados_filtrados["UF"]
    .value_counts()
    .reset_index()
)

ubs_por_estado.columns = ["Estado", "Quantidade"]

fig_estados = px.bar(
    ubs_por_estado.sort_values("Quantidade", ascending=False),
    x="Estado",
    y="Quantidade",
    title="Distribuição das UBS por estado",
    labels={
        "Estado": "Estado (UF)",
        "Quantidade": "Número de UBS"
    },
    color="Quantidade",
    color_continuous_scale="Blues"
)

fig_estados.update_layout(
    xaxis_title="Estado",
    yaxis_title="Quantidade de UBS",
    showlegend=False
)

st.plotly_chart(fig_estados, use_container_width=True)

st.write(
    "Este gráfico permite comparar a quantidade de unidades cadastradas "
    "em cada estado. Uma quantidade maior não significa, necessariamente, "
    "que o atendimento à população seja melhor."
)

# Gráfico 2: UBS com e sem coordenadas
st.subheader("2. Qualidade dos dados de localização")

if "LATITUDE" in dados_filtrados.columns and \
        "LONGITUDE" in dados_filtrados.columns:

    total_sem_coordenadas = total_ubs - total_coordenadas

    dados_localizacao = pd.DataFrame({
        "Situação": ["Com coordenadas", "Sem coordenadas"],
        "Quantidade": [total_coordenadas, total_sem_coordenadas]
    })

    fig_localizacao = px.pie(
        dados_localizacao,
        names="Situação",
        values="Quantidade",
        title="UBS com e sem informações de localização",
        hole=0.4
    )

    st.plotly_chart(fig_localizacao, use_container_width=True)

    st.write(
        "Este gráfico mostra quantas unidades possuem latitude e longitude "
        "registradas. Dados ausentes podem dificultar a localização das UBS "
        "em mapas."
    )

else:
    st.warning(
        "Não foi possível criar o gráfico de localização porque "
        "as colunas LATITUDE e LONGITUDE não foram encontradas."
    )

# Mapa das UBS
st.subheader("3. Localização das UBS")

if not coordenadas_validas.empty:
    mapa = coordenadas_validas.dropna(
        subset=["LATITUDE", "LONGITUDE"]
    ).copy()

    mapa = mapa[
        mapa["LATITUDE"].between(-90, 90)
        & mapa["LONGITUDE"].between(-180, 180)
    ]

    if not mapa.empty:
        fig_mapa = px.scatter_map(
            mapa,
            lat="LATITUDE",
            lon="LONGITUDE",
            hover_name="NOME",
            hover_data=[
                coluna for coluna in ["UF", "BAIRRO"]
                if coluna in mapa.columns
            ],
            zoom=3,
            height=500,
            title="Mapa das Unidades Básicas de Saúde"
        )

        st.plotly_chart(fig_mapa, use_container_width=True)
    else:
        st.warning("Não há coordenadas válidas para exibir no mapa.")
else:
    st.info("O mapa precisa de latitude e longitude válidas.")

# Tabela de dados
st.subheader("4. Tabela de dados")

st.write(
    "A tabela abaixo apresenta os registros após a remoção de duplicatas "
    "e a aplicação dos filtros."
)

st.dataframe(
    dados_filtrados,
    use_container_width=True,
    hide_index=True
)

# Download dos dados tratados
csv_tratado = dados_filtrados.to_csv(
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

st.divider()

st.caption(
    "Projeto escolar de Ciência de Dados | "
    "Ferramentas: Python, Pandas, Plotly e Streamlit."
)
