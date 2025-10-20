import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
import geopandas as gpd


# --- Barra lateral para navegação ---
st.sidebar.image("images/brasao2.jpg", width=300)
st.sidebar.title("Navegação")
selecao = st.sidebar.radio("Escolha a seção:",
                           ["Página Inicial", "Introdução", "Critérios de Seleção", "Gráficos", "Mapas"])

# --- Função para carregar os dados do arquivo limpo ---
def carregar_dados_escolas():
    """Carrega o arquivo CSV limpo das escolas prioritárias"""
    try:
        # Tenta carregar o arquivo limpo
        dados = pd.read_csv('planilhas/Escolas_Prioritarias_LIMPO.csv', encoding='utf-8')
        return dados
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo limpo: {e}")
        return None

# --- Função para carregar dados de Metas e IDEB ---
@st.cache_data
def carregar_dados_metas_ideb():
    """Carrega os dados de metas e IDEB"""
    try:
        # Tentar diferentes codificações
        codificacoes = ['latin-1', 'iso-8859-1', 'cp1252', 'utf-8']
        
        for encoding in codificacoes:
            try:
                df = pd.read_csv('planilhas/metas e idebes.csv', sep=';', decimal=',', encoding=encoding)
                return df
            except UnicodeDecodeError:
                continue
            except Exception:
                continue
        
        # Última tentativa
        df = pd.read_csv('planilhas/metas e idebes.csv', sep=';', decimal=',', encoding='latin-1', engine='python')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo de metas e IDEB: {e}")
        return pd.DataFrame()

# --- Função para criar o mapa interativo ---
def criar_mapa_escolas():
    """Cria mapa interativo com as escolas prioritárias e municípios com SRE"""
    try:
        # Carregar dados das escolas
        df_escolas = pd.read_csv('mapa/escolas_prioritárias.csv', sep=';', encoding='utf-8', skiprows=1)
        
        # Renomear colunas
        novas_colunas = [
            'NUMERO', 'SRE', 'ESCOLA', 'INEP', 'EQUIPE_RESPONSAVEL', 
            'LATITUDE', 'LONGITUDE', 'IDEBES_2024', 'META_2025'
        ]
        df_escolas.columns = novas_colunas
        
        # Limpar e preparar dados
        df_escolas_clean = df_escolas.dropna(subset=['LATITUDE', 'LONGITUDE']).copy()
        df_escolas_clean['LATITUDE'] = df_escolas_clean['LATITUDE'].astype(str).str.replace(',', '.').astype(float)
        df_escolas_clean['LONGITUDE'] = df_escolas_clean['LONGITUDE'].astype(str).str.replace(',', '.').astype(float)
        
        # Carregar relação município-SRE
        df_regionais = pd.read_csv('mapa/regionais_sedu.csv')
        
        # Criar dicionário município -> SRE
        municipio_para_sre = {}
        for idx, row in df_regionais.iterrows():
            municipio = row['MUNICIPIO'].upper().strip()
            sre = row['REGIONAL_SRE'].strip()
            municipio_para_sre[municipio] = sre
        
        # Criar mapa base
        mapa = folium.Map(
            location=[-20.0, -40.5],
            zoom_start=8,
            tiles='OpenStreetMap',
            min_zoom=7,
            max_zoom=15
        )
        
        # Cores para cada equipe
        cores_equipe = {
            'GEM': 'blue',
            'GETI': 'green', 
            'GEIEF': 'orange',
            'GEACIQ': 'red'
        }
        
        # Cores para cada SRE (para os municípios)
        cores_sre = {
            'SRE AFONSO CLÁUDIO': '#FF6B6B',
            'SRE BARRA DE SÃO FRANCISCO': '#4ECDC4',
            'SRE CACHOEIRO DE ITAPEMIRIM': '#45B7D1',
            'SRE CARAPINA': '#96CEB4',
            'SRE CARIACICA': '#FECA57',
            'SRE COLATINA': '#FF9FF3',
            'SRE GUARAPARI': '#54A0FF',
            'SRE LINHARES': '#5F27CD',
            'SRE NOVA VENÉCIA': '#00D2D3',
            'SRE SÃO MATEUS': '#FF9F43',
            'SRE VILA VELHA': '#10AC84',
            'SRE VITÓRIA': '#EE5A24'
        }
        
        # Adicionar marcadores das escolas
        for idx, escola in df_escolas_clean.iterrows():
            equipe = escola['EQUIPE_RESPONSAVEL']
            cor = cores_equipe.get(equipe, 'gray')
            
            # Criar popup informativo
            popup_text = f"""
            <b>{escola['ESCOLA']}</b><br>
            <b>SRE:</b> {escola['SRE']}<br>
            <b>Equipe:</b> {equipe}<br>
            <b>IDEBES 2024:</b> {escola['IDEBES_2024']}<br>
            <b>INEP:</b> {escola['INEP']}
            """
            
            # Adicionar marcador
            folium.Marker(
                location=[escola['LATITUDE'], escola['LONGITUDE']],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=escola['ESCOLA'],
                icon=folium.Icon(color=cor, icon='info-sign')
            ).add_to(mapa)
        
        # Adicionar municípios do ES com tooltips
        try:
            gdf_municipios = gpd.read_file('mapa/BR_Municipios_2022.shp')
            gdf_es = gdf_municipios[gdf_municipios['SIGLA_UF'] == 'ES']
            
            # Função para normalizar nomes (remover acentos)
            def normalizar_nome(nome):
                return (nome.upper()
                        .replace('Á', 'A').replace('À', 'A').replace('Â', 'A').replace('Ã', 'A')
                        .replace('É', 'E').replace('Ê', 'E')
                        .replace('Í', 'I')
                        .replace('Ó', 'O').replace('Ô', 'O').replace('Õ', 'O')
                        .replace('Ú', 'U')
                        .replace('Ç', 'C')
                        .strip())
            
            # Criar dicionário normalizado
            municipio_para_sre_normalizado = {}
            for municipio, sre in municipio_para_sre.items():
                municipio_normalizado = normalizar_nome(municipio)
                municipio_para_sre_normalizado[municipio_normalizado] = sre
            
            # Adicionar cada município individualmente com tooltip personalizado
            for idx, municipio in gdf_es.iterrows():
                municipio_nome = municipio['NM_MUN']
                municipio_nome_normalizado = normalizar_nome(municipio_nome)
                
                # Buscar SRE no dicionário normalizado
                sre_encontrada = municipio_para_sre_normalizado.get(municipio_nome_normalizado, "SRE não identificada")
                
                # Determinar cor
                cor = cores_sre.get(sre_encontrada, '#95a5a6')
                
                # Tooltip no formato: "Vitória - SRE Carapina"
                tooltip_text = f"{municipio_nome} - {sre_encontrada}"
                
                # Criar GeoJson para o município
                geojson = folium.GeoJson(
                    municipio['geometry'],
                    style_function=lambda feature, cor=cor: {
                        'fillColor': cor,
                        'color': '#2c3e50',
                        'weight': 1.5,
                        'fillOpacity': 0.7,
                    }
                )
                
                # Adicionar tooltip personalizado
                geojson.add_child(folium.Tooltip(
                    tooltip_text,
                    style="background-color: #2c3e50; color: white; font-family: Arial; font-size: 12px; padding: 8px; border-radius: 4px;"
                ))
                
                geojson.add_to(mapa)
            
            st.success("✅ Mapa com municípios coloridos por SRE criado com sucesso!")
            
        except Exception as e:
            st.warning(f"Shapefile dos municípios não encontrado: {e}")
        
        return mapa, df_escolas_clean
        
    except Exception as e:
        st.error(f"Erro ao criar mapa: {e}")
        return None, None

# --- Seção: Página Inicial ---
if selecao == "Página Inicial":
    st.image("images/brasao1.png")
    st.title("Educação no Espírito Santo")
    st.title("Escolas Prioritárias") 
    st.subheader("**Autor**: Luís Eduardo Formentini")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.header("Bem-vindo!")
        st.write("""
                Este aplicativo é um protótipo para análise de dados educacionais.
                Ele está dividido em seções para futura expansão com tabelas, gráficos e mapas.
                """)
    
    with col2:
        st.image("images/euzin.jpg", caption="Prof Ms Luís Eduardo Formentini", width='stretch')

# --- Seção: Introdução ---
elif selecao == "Introdução":
    st.header("O que são Escolas Prioritárias?")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("""
        As **Escolas Prioritárias** são unidades escolares que demandam maior apoio da SEDU e da SRE, no que diz respeito
        ao alcance ou não das metas, considerando os resultados do Índice de Desenvolvimento da
        Educação Básica - IDEB e/ou Índice de Desenvolvimento da Educação Básica no Espírito
        Santo - IDEBES, além de outros critérios que a SEDU julgar necessário.
                 
        As Escolas Prioritárias foram instituídas na Rede Estadual de Ensino do Espírito Santo como parte das ações do Circuito de Gestão (CdG) por meio da **Portaria Nº 034-R**, de 16 de fevereiro de 2018.
        Essa portaria foi revogada pela **Portaria Nº 154-R, de 17 de dezembro de 2020**, que manteve a orientação de um atendimento diferenciado às Escolas Prioritárias. 

        Nos anos de 2023 e 2024 a definição sobre quais unidades escolares seriam consideradas prioritárias foi oficializada, respectivamente por meio da **CI/SEDU/GS/Nº03** e da **CI/SEDU/GS/Nº 06**, sendo que todas as Superintendências Regionais foram contempladas com uma ou mais unidades escolares definidas como prioritárias que ofertam o Ensino Fundamental Anos Finais e o Ensino Médio Parcial e Integral. 

        Vale ressaltar que os critérios de seleção, quantitativos, tipo de assessoramento e distribuição das Escolas Prioritárias nas SREs são definidos pela Sedu-Unidade Central a cada ano.
         
        """)

    st.markdown("📚 Para saber mais sobre o Idebes [clique aqui](https://sedu.es.gov.br/indice-de-desenvolvimento-da-educacao-basica-do-espirito-santo-idebes)")
    
    with col2:
        st.image("images/brasao2.jpg")
       

# --- Seção: Critérios de Seleção ---
elif selecao == "Critérios de Seleção":
    st.header("Critérios de Seleção das Escolas Prioritárias")
    
    st.write("""
        
    Os critérios estabelecidos para a definição das Escolas Prioritárias no ano de 2025 consideram diferentes dimensões da equidade e do desempenho educacional, sendo eles:

    **Equidade educacional:** análise da distribuição dos estudantes por padrão de desempenho no Programa de Avaliação da Educação Básica do Espírito Santo - PAEBES em Matemática e Língua Portuguesa;

    **Desafio de crescimento:** diferença entre a meta estabelecida para o ano vigente e o Índice de Desenvolvimento da Educação Básica - IDEBES do ano anterior;

    **Histórico de atingimento de metas:** número de vezes que a escola alcançou ou não as metas nos últimos três anos;

    **Número de matrículas na etapa de ensino:** consideração da quantidade de matrículas em cada etapa de ensino;

    **Complexidade de gestão:** aspectos que impactam a organização e a execução das ações pedagógicas e administrativas.

    """)

    st.markdown("<p style='font-size: 1.2em; font-weight: bold'>Abaixo está a lista de escolas prioritárias com possibilidade de filtro por Superintendência Regional de Educação (SREs).</p>", unsafe_allow_html=True)
    
   # Carregar dados do arquivo limpo
    dados_escolas = carregar_dados_escolas()

    if dados_escolas is not None:
        # Verifica se as colunas necessárias existem
        if 'SRE' in dados_escolas.columns and 'ESCOLA' in dados_escolas.columns:
        
            # --- FILTRO SRE ---
            st.subheader("Filtro por SRE")
        
            # Obter lista única de SREs dos dados
            sres_disponiveis = sorted(dados_escolas['SRE'].unique())
        
            # Adicionar opção "TODAS AS SREs"
            sres_com_todas = ["TODAS AS SREs"] + sres_disponiveis

            sre_selecionada = st.selectbox(
                "Selecione uma SRE:",
                options=sres_com_todas,
                index=0
            )

            if sre_selecionada == "TODAS AS SREs":
                st.info("Visualizando dados de todas as SREs")
                dados_filtrados = dados_escolas
            else:
                st.info(f"Filtrado por: {sre_selecionada}")
                dados_filtrados = dados_escolas[dados_escolas["SRE"] == sre_selecionada]
        
            # Ordenar os dados por SRE e Escola (ordem alfabética)
            dados_filtrados = dados_filtrados.sort_values(['SRE', 'ESCOLA'])
        
            # Mostrar resultados SEM o índice
            st.subheader(f"Escolas Prioritárias ({len(dados_filtrados)} encontradas)")
            st.dataframe(dados_filtrados[['SRE', 'ESCOLA']], 
                        width='stretch', 
                        hide_index=True)  # Esta linha remove a coluna de números
        
            # Estatísticas rápidas
            if len(dados_filtrados) > 0:
                st.write(f"**Total de escolas:** {len(dados_filtrados)}")
                if sre_selecionada == "TODAS AS SREs":
                    st.write(f"**SREs representadas:** {len(dados_filtrados['SRE'].unique())}")
        
        else:
            st.error("Colunas 'SRE' e 'ESCOLA' não encontradas no arquivo limpo.")
            st.write("Colunas encontradas:", list(dados_escolas.columns))

    else:
        st.error("Não foi possível carregar o arquivo 'planilhas/Escolas_Prioritarias_LIMPO.csv'")


# --- Seção: Gráficos ---
elif selecao == "Gráficos":
    st.header("📊 Análise de Metas e IDEBES")
    st.markdown("Série histórica de 2021 a 2024")

    st.write("""
    "**OBS**: Os gráficos a seguir se referem somente às 22 Escolas Prioritárias
    assessoradas pela Gerência de Ensino Médio (GEM)
    """)
    
    # Carregar dados de metas e IDEB
    df = carregar_dados_metas_ideb()
    
    if df.empty:
        st.error("Não foi possível carregar os dados de metas e IDEB.")
    else:
        # Sidebar com filtros
        st.sidebar.header("Filtros - Metas e IDEB")
        
        # Filtro de SRE
        sre_options = ['Todas'] + sorted(df['SRE'].unique().tolist())
        sre_selecionada = st.sidebar.selectbox(
            "Selecione a SRE:",
            options=sre_options,
            index=1 if len(sre_options) > 1 else 0
        )
        
        # Filtro de Escola baseado na SRE selecionada
        if sre_selecionada == "Todas":
            escola_options = ['Todas'] + sorted(df['ESCOLA'].unique().tolist())
        else:
            escola_options = ['Todas'] + sorted(df[df['SRE'] == sre_selecionada]['ESCOLA'].unique().tolist())
        
        escola_selecionada = st.sidebar.selectbox(
            "Selecione a Escola:",
            options=escola_options,
            index=1 if len(escola_options) > 1 else 0
        )
        
        # Filtrar dados baseado nas seleções
        if sre_selecionada == "Todas":
            dados_filtrados = df.copy()
        else:
            dados_filtrados = df[df['SRE'] == sre_selecionada]
        
        if escola_selecionada != "Todas":
            dados_filtrados = dados_filtrados[dados_filtrados['ESCOLA'] == escola_selecionada]
        else:
            # Se "Todas" escolas, pegar a primeira da SRE para exemplo
            if sre_selecionada != "Todas" and not dados_filtrados.empty:
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
                    text=f'{escola_selecionada}<br><sup>{sre_selecionada}</sup>',
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
            st.plotly_chart(fig, config={'displayModeBar': False, 'showlegend': True})
            
            # Mostrar tabela com os dados
            st.subheader("📋 Dados Detalhados")
            st.dataframe(
                dados_filtrados[['ANO', 'META', 'IDEBES']].style.format({'META': '{:.2f}', 'IDEBES': '{:.2f}'}),
                width='stretch'
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
        
        # Informações gerais
        st.sidebar.markdown("---")
        st.sidebar.subheader("ℹ️ Informações - Metas e IDEB")
        st.sidebar.write(f"**Total de escolas:** {df['ESCOLA'].nunique()}")
        st.sidebar.write(f"**Total de SREs:** {df['SRE'].nunique()}")
        st.sidebar.write(f"**Período:** {df['ANO'].min()} - {df['ANO'].max()}")

# --- Seção: Mapas ---
elif selecao == "Mapas":
    st.header("🗺️ Mapa Interativo das Escolas Prioritárias")
    
    st.write("""
    Este mapa mostra a localização de todas as escolas prioritárias no Espírito Santo, com um código de cores baseado nas gerências responsáveis pelo assessoramento das Escolas Prioritárias
    **Cores dos marcadores:**
    - 🔵 **Azul**: GEM - Gerência de Ensino Médio.
    - 🟢 **Verde**: GETI - Gerência de Tempo Integral
    - 🟠 **Laranja**: GEIEF - Gerência de Educação Infantil e Ensino Fundamental.
    - 🔴 **Vermelho**: GEACIQ - Gerência de Educação Antirracista, do Campo, Indígena e Quilombola
    
    **💡 Dica:** Passe o mouse sobre os municípios para ver o nome e a SRE correspondente.
    """)
    
    # Criar e exibir o mapa (sem cache)
    with st.spinner('Carregando mapa...'):
        mapa, dados_escolas = criar_mapa_escolas()
        
        if mapa is not None:
            # Exibir o mapa no Streamlit
            st_folium(mapa, width=800, height=600)
            
            # Estatísticas abaixo do mapa
            if dados_escolas is not None:
                st.subheader("📊 Estatísticas do Mapa")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total de Escolas", len(dados_escolas))
                
                with col2:
                    st.metric("SREs Representadas", dados_escolas['SRE'].nunique())
                
                with col3:
                    gem_count = len(dados_escolas[dados_escolas['EQUIPE_RESPONSAVEL'] == 'GEM'])
                    st.metric("Escolas GEM", gem_count)
                
                with col4:
                    outras_count = len(dados_escolas[dados_escolas['EQUIPE_RESPONSAVEL'] != 'GEM'])
                    st.metric("Outras Equipes", outras_count)
                
                # Tabela com dados das escolas
                st.subheader("📋 Lista de Escolas no Mapa")
                st.dataframe(
                    dados_escolas[['ESCOLA', 'SRE', 'EQUIPE_RESPONSAVEL', 'IDEBES_2024']],
                    width='stretch'
                )
        else:
            st.error("Não foi possível carregar o mapa. Verifique se os arquivos necessários estão na pasta.")