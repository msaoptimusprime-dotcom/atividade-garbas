import io
import zipfile

import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Dashboard de Saúde — UBS",
    page_icon="",
    layout="wide",
)

UF_NOMES = {
    11: "Rondônia", 12: "Acre", 13: "Amazonas", 14: "Roraima",
    15: "Pará", 16: "Amapá", 17: "Tocantins", 21: "Maranhão",
    22: "Piauí", 23: "Ceará", 24: "Rio Grande do Norte", 25: "Paraíba",
    26: "Pernambuco", 27: "Alagoas", 28: "Sergipe", 29: "Bahia",
    31: "Minas Gerais", 32: "Espírito Santo", 33: "Rio de Janeiro",
    35: "São Paulo", 41: "Paraná", 42: "Santa Catarina",
    43: "Rio Grande do Sul", 50: "Mato Grosso do Sul",
    51: "Mato Grosso", 52: "Goiás", 53: "Distrito Federal",
}


def ler_arquivo(upload):
    """Lê CSV ou ZIP contendo um CSV, tentando codificações comuns."""
    conteudo = upload.getvalue()
    nome = upload.name.lower()

    if nome.endswith(".zip"):
        with zipfile.ZipFile(io.BytesIO(conteudo)) as arquivo_zip:
            csvs = [n for n in arquivo_zip.namelist()
                    if n.lower().endswith(".csv") and not n.startswith("__MACOSX/")]
            if not csvs:
                raise ValueError("O ZIP não contém nenhum arquivo CSV.")
            conteudo = arquivo_zip.read(csvs[0])

    erros = []
    for encoding in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(io.BytesIO(conteudo), sep=None, engine="python",
                               encoding=encoding)
        except Exception as erro:
            erros.append(str(erro))
    raise ValueError("Não foi possível ler o arquivo. Confira se ele é um CSV válido.")


def preparar_dados(dados):
    """Padroniza nomes de colunas e trata campos usados no dashboard."""
    dados = dados.copy()
    dados.columns = [str(col).strip().upper() for col in dados.columns]

    obrigatorias = {"CNES", "UF", "IBGE", "NOME", "BAIRRO", "LATITUDE", "LONGITUDE"}
    ausentes = obrigatorias - set(dados.columns)
    if ausentes:
        raise ValueError(
            "Não encontrei estas colunas esperadas: "
            + ", ".join(sorted(ausentes))
            + ". Colunas recebidas: "
            + ", ".join(dados.columns)
        )

    # Converte códigos para números; valores inválidos viram ausentes (NaN).
    for coluna in ("CNES", "UF", "IBGE"):
        dados[coluna] = pd.to_numeric(dados[coluna], errors="coerce").astype("Int64")

    # A base pode conter coordenadas com vírgula como separador decimal.
    for coluna in ("LATITUDE", "LONGITUDE"):
        dados[coluna] = pd.to_numeric(
            dados[coluna].astype("string").str.strip().str.replace(",", ".", regex=False),
            errors="coerce",
        )

    # Limpa espaços e mantém explícitos os textos que estavam vazios.
    for coluna in ("NOME", "BAIRRO", "LOGRADOURO"):
        dados[coluna] = (
            dados[coluna].astype("string").str.strip()
            .replace("", pd.NA)
        )

    # Remove duplicatas exatas; o total removido será informado na tela.
    quantidade_antes = len(dados)
    dados = dados.drop_duplicates()
    duplicatas_removidas = quantidade_antes - len(dados)

    dados["ESTADO"] = dados["UF"].map(
        lambda codigo: UF_NOMES.get(int(codigo), f"Código {codigo}")
        if pd.notna(codigo) else "UF não informada"
    )
    dados["COORDENADAS_OK"] = (
        dados["LATITUDE"].between(-34, 6, inclusive="both")
        & dados["LONGITUDE"].between(-74, -34, inclusive="both")
    )

    return dados, duplicatas_removidas


st.title("Dashboard das Unidades Básicas de Saúde")
st.write(
    "Este dashboard explora os registros de Unidades Básicas de Saúde (UBS) "
    "presentes no arquivo enviado. Os filtros e gráficos ajudam a comparar "
    "a distribuição dos registros e a qualidade das informações de localização."
)

st.info(
    "A base fornecida possui códigos de estado e município, nome e endereço da UBS "
    "e coordenadas geográficas. Ela não contém população nem ano de referência; "
    "portanto, os resultados não medem cobertura por habitante nem evolução histórica."
)

upload = st.file_uploader(
    "Envie o arquivo da base de UBS (CSV ou ZIP contendo CSV)",
    type=["csv", "zip"],
)

if upload is None:
    st.markdown("### Perguntas investigadas")
    st.markdown(
        "1. **Quais estados têm mais UBS registradas nesta base?**\n"
        "2. **Quais estados têm maior proporção de registros com coordenadas válidas?**"
    )
    st.caption("Envie o arquivo para gerar os indicadores e gráficos.")
else:
    try:
        bruto = ler_arquivo(upload)
        df, duplicatas_removidas = preparar_dados(bruto)

        st.success("Arquivo carregado e dados preparados com Pandas.")
        with st.expander("O que foi feito no tratamento dos dados?"):
            st.markdown(
                "- Padronização dos nomes das colunas.\n"
                "- Conversão de códigos e coordenadas para tipos numéricos.\n"
                "- Conversão de vírgulas decimais em coordenadas para pontos.\n"
                "- Remoção de espaços extras em campos de texto.\n"
                "- Remoção apenas de linhas completamente duplicadas.\n"
                "- Identificação de coordenadas dentro de uma faixa geográfica aproximada do Brasil."
            )
            st.write(f"Linhas duplicadas exatas removidas: **{duplicatas_removidas:,}**".replace(",", "."))

        st.subheader("Indicadores gerais")
        total = len(df)
        total_estados = df.loc[df["UF"].notna(), "UF"].nunique()
        coordenadas_validas = int(df["COORDENADAS_OK"].sum())
        percentual_coord = (coordenadas_validas / total * 100) if total else 0
        nomes_ausentes = int(df["NOME"].isna().sum())

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Registros de UBS", f"{total:,}".replace(",", "."))
        c2.metric("UFs encontradas", str(total_estados))
        c3.metric("Coordenadas válidas", f"{percentual_coord:.1f}%")
        c4.metric("Nomes ausentes", f"{nomes_ausentes:,}".replace(",", "."))

        st.subheader("Filtros")
        estados = sorted(df["ESTADO"].dropna().unique().tolist())
        estados_selecionados = st.multiselect(
            "Selecione os estados",
            options=estados,
            default=estados,
        )
        filtrado = df[df["ESTADO"].isin(estados_selecionados)].copy()

        if filtrado.empty:
            st.warning("Nenhum registro corresponde aos filtros selecionados.")
        else:
            # Gráfico 1: quantidade de registros por estado.
            st.subheader("Gráfico 1 — UBS registradas por estado")
            por_estado = (
                filtrado.groupby("ESTADO", as_index=False)
                .size()
                .rename(columns={"size": "Quantidade de UBS"})
                .sort_values("Quantidade de UBS", ascending=False)
            )
            fig1 = px.bar(
                por_estado,
                x="ESTADO",
                y="Quantidade de UBS",
                title="Quantidade de registros de UBS por estado",
                labels={"ESTADO": "Estado", "Quantidade de UBS": "Registros"},
                hover_data={"Quantidade de UBS": True},
            )
            fig1.update_layout(xaxis_tickangle=-40)
            st.plotly_chart(fig1, use_container_width=True)
            st.write(
                "**Interpretação:** o gráfico mostra quantas unidades estão registradas "
                "na base em cada estado selecionado. Um total maior de registros não "
                "significa necessariamente melhor atendimento ou maior cobertura populacional."
            )

            # Gráfico 2: percentual de registros com coordenadas válidas.
            st.subheader("Gráfico 2 — Qualidade das coordenadas por estado")
            coord_estado = (
                filtrado.groupby("ESTADO", as_index=False)
                .agg(
                    Total=("COORDENADAS_OK", "size"),
                    Com_coordenadas_validas=("COORDENADAS_OK", "sum"),
                )
            )
            coord_estado["Percentual com coordenadas válidas (%)"] = (
                coord_estado["Com_coordenadas_validas"] / coord_estado["Total"] * 100
            ).round(1)
            coord_estado = coord_estado.sort_values(
                "Percentual com coordenadas válidas (%)", ascending=False
            )
            fig2 = px.bar(
                coord_estado,
                x="ESTADO",
                y="Percentual com coordenadas válidas (%)",
                title="Percentual de UBS com latitude e longitude plausíveis",
                labels={
                    "ESTADO": "Estado",
                    "Percentual com coordenadas válidas (%)": "Registros com coordenadas válidas (%)",
                },
                hover_data=["Total", "Com_coordenadas_validas"],
            )
            fig2.update_layout(xaxis_tickangle=-40, yaxis_range=[0, 100])
            st.plotly_chart(fig2, use_container_width=True)
            st.write(
                "**Interpretação:** este gráfico compara a proporção de registros cujas "
                "coordenadas estão preenchidas e dentro de uma faixa geográfica aproximada "
                "do Brasil. Ele avalia a completude plausível da localização, não a qualidade do serviço."
            )

            # Mapa de pontos: limitado para manter a aplicação responsiva.
            pontos = filtrado.loc[
                filtrado["COORDENADAS_OK"], ["NOME", "ESTADO", "BAIRRO", "LATITUDE", "LONGITUDE"]
            ].dropna(subset=["LATITUDE", "LONGITUDE"])
            if not pontos.empty:
                st.subheader("Mapa — Localização das UBS")
                limite = 5000
                if len(pontos) > limite:
                    st.caption(f"Para manter o mapa rápido, são exibidos até {limite:,} pontos amostrados.".replace(",", "."))
                    pontos = pontos.sample(n=limite, random_state=42)
                mapa = px.scatter_map(
                    pontos,
                    lat="LATITUDE",
                    lon="LONGITUDE",
                    color="ESTADO",
                    hover_name="NOME",
                    hover_data={"BAIRRO": True, "LATITUDE": False, "LONGITUDE": False},
                    zoom=3,
                    height=520,
                    title="Distribuição geográfica das UBS com coordenadas válidas",
                )
                mapa.update_layout(map_style="open-street-map", margin={"r": 0, "t": 50, "l": 0, "b": 0})
                st.plotly_chart(mapa, use_container_width=True)

            with st.expander("Ver amostra dos dados tratados"):
                st.dataframe(filtrado.head(100), use_container_width=True)

            with st.expander("Ver valores ausentes por coluna"):
                ausentes = pd.DataFrame({
                    "Coluna": filtrado.columns,
                    "Valores ausentes": [int(filtrado[col].isna().sum()) for col in filtrado.columns],
                })
                st.dataframe(ausentes, hide_index=True, use_container_width=True)

            csv_saida = filtrado.drop(columns=["COORDENADAS_OK"], errors="ignore").to_csv(index=False).encode("utf-8-sig")
            st.download_button(
                "Baixar dados filtrados em CSV",
                data=csv_saida,
                file_name="ubs_tratadas_filtradas.csv",
                mime="text/csv",
            )

    except Exception as erro:
        st.error(f"Não foi possível processar o arquivo: {erro}")
        st.caption("Confira se o arquivo contém as colunas CNES, UF, IBGE, NOME, BAIRRO, LATITUDE e LONGITUDE.")
