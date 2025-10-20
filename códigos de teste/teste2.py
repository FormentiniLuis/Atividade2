import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Configurar a página
st.set_page_config(page_title="Análise IDEB", layout="wide")

# Título da aplicação
st.title("📊 Análise de Metas e IDEBES")
st.markdown("Série histórica de 2021 a 2024")

# Carregar os dados com diferentes codificações
@st.cache_data
def carregar_dados():
    # Tentar diferentes codificações comuns em português
    codificacoes = ['latin-1', 'iso-8859-1', 'cp1252', 'utf-8']
    
    for encoding in codificacoes:
        try:
            df = pd.read_csv('/workspaces/Atividade2/planilhas/metas e idebes.csv', sep=';', decimal=',', encoding=encoding)
            st.sidebar.success(f"Arquivo carregado com codificação: {encoding}")
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            st.error(f"Erro com codificação {encoding}: {e}")
            continue
    
    # Se nenhuma codificação funcionar, tentar com engine python
    try:
        df = pd.read_csv('metas e idebes.csv', sep=';', decimal=',', encoding='latin-1', engine='python')
        st.sidebar.success("Arquivo carregado com engine python")
        return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo: {e}")
        return pd.DataFrame()

df = carregar_dados()

# Verificar se os dados foram carregados
if df.empty:
    st.error("Não foi possível carregar o arquivo. Verifique a codificação.")
    st.stop()

# Sidebar com filtros
st.sidebar.header("Filtros")

# Filtro de MUNICÍPIO
municipio_options = ['Todos'] + sorted(df['MUNICÍPIO'].unique().tolist())
municipio_selecionado = st.sidebar.selectbox(
    "Selecione o Município:",
    options=municipio_options,
    index=1 if len(municipio_options) > 1 else 0
)

# Filtro de Escola baseado no Município selecionado
if municipio_selecionado == "Todos":
    escola_options = ['Todas'] + sorted(df['ESCOLA'].unique().tolist())
else:
    escola_options = ['Todas'] + sorted(df[df['MUNICÍPIO'] == municipio_selecionado]['ESCOLA'].unique().tolist())

escola_selecionada = st.sidebar.selectbox(
    "Selecione a Escola:",
    options=escola_options,
    index=1 if len(escola_options) > 1 else 0
)

# Filtrar dados baseado nas seleções
if municipio_selecionado == "Todos":
    dados_filtrados = df.copy()
else:
    dados_filtrados = df[df['MUNICÍPIO'] == municipio_selecionado]

if escola_selecionada != "Todas":
    dados_filtrados = dados_filtrados[dados_filtrados['ESCOLA'] == escola_selecionada]
else:
    # Se "Todas" escolas, pegar a primeira do Município para exemplo
    if municipio_selecionado != "Todos" and not dados_filtrados.empty:
        escola_padrao = dados_filtrados['ESCOLA'].iloc[0]
        dados_filtrados = dados_filtrados[dados_filtrados['ESCOLA'] == escola_padrao]
        escola_selecionada = escola_padrao

# Verificar se temos dados
if not dados_filtrados.empty:
    # Ordenar por ano
    dados_filtrados = dados_filtrados.sort_values('ANO')

    # Criar gráfico Plotly
    fig = go.Figure()

    # Adicionar linha da META (vermelho)
    fig.add_trace(go.Scatter(
        x=dados_filtrados['ANO'],
        y=dados_filtrados['META'],
        mode='lines+markers+text',
        name='META',
        line=dict(color='red', width=4),
        marker=dict(size=12, color='red'),
        text=[f'{x:.2f}' for x in dados_filtrados['META']],
        textposition='top center',
        textfont=dict(size=12, color='red')
    ))

    # Adicionar linha do IDEBES (azul)
    fig.add_trace(go.Scatter(
        x=dados_filtrados['ANO'],
        y=dados_filtrados['IDEBES'],
        mode='lines+markers+text',
        name='IDEBES',
        line=dict(color='blue', width=4),
        marker=dict(size=12, color='blue'),
        text=[f'{x:.2f}' for x in dados_filtrados['IDEBES']],
        textposition='bottom center',
        textfont=dict(size=12, color='blue')
    ))

    # Layout do gráfico
    fig.update_layout(
        title=dict(
            text=f'{escola_selecionada}<br><sup>{municipio_selecionado}</sup>',
            x=0.5,
            xanchor='center',
            font=dict(size=20)
        ),
        xaxis=dict(
            title='',
            tickmode='array',
            tickvals=[2021, 2022, 2023, 2024],
            ticktext=['2021', '2022', '2023', '2024'],
            gridcolor='lightgray',
            gridwidth=1
        ),
        yaxis=dict(
            title='Nota',
            range=[2.5, 6],
            gridcolor='lightgray',
            gridwidth=1,
            zeroline=False
        ),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        height=500,
        plot_bgcolor='white'
    )

    # Mostrar gráfico no Streamlit
    st.plotly_chart(fig, use_container_width=True)

    # Mostrar tabela com os dados
    st.subheader("📋 Dados Detalhados")
    st.dataframe(
        dados_filtrados[['ANO', 'META', 'IDEBES']].style.format({'META': '{:.2f}', 'IDEBES': '{:.2f}'}),
        use_container_width=True
    )

    # Estatísticas rápidas
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Média da META", f"{dados_filtrados['META'].mean():.2f}")

    with col2:
        st.metric("Média do IDEBES", f"{dados_filtrados['IDEBES'].mean():.2f}")

    with col3:
        # Verificar desempenho no último ano
        ultimo_ano = dados_filtrados.iloc[-1]
        desempenho = "✅ Atingiu" if ultimo_ano['IDEBES'] >= ultimo_ano['META'] else "❌ Não Atingiu"
        st.metric("Desempenho 2024", desempenho)

else:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")

# Informações gerais na sidebar
st.sidebar.markdown("---")
st.sidebar.subheader("ℹ️ Informações")
st.sidebar.write(f"**Total de escolas:** {df['ESCOLA'].nunique()}")
st.sidebar.write(f"**Total de municípios:** {df['MUNICÍPIO'].nunique()}")
st.sidebar.write(f"**Período:** {df['ANO'].min()} - {df['ANO'].max()}")