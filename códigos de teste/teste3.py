import streamlit as st
import pandas as pd
import os

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Educação no Espírito Santo", layout="wide")

# --- VERIFICAÇÃO DE ARQUIVOS ---
def verificar_arquivos():
    """Verifica se todos os arquivos necessários estão presentes"""
    arquivos_necessarios = {
        'shapefile': 'mapa/BR_Municipios_2022.shp',
        'regionais_csv': 'mapa/regionais_sedu.csv',
        'metas_ideb': 'planilhas/metas e idebes.csv',
        'escolas_prioritarias': 'planilhas/Escolas_Prioritarias_LIMPO.csv'
    }
    
    arquivos_faltantes = {}
    for nome, caminho in arquivos_necessarios.items():
        if not os.path.exists(caminho):
            arquivos_faltantes[nome] = caminho
    
    return arquivos_faltantes

# --- FUNÇÕES PARA CARREGAR DADOS ---
def carregar_dados_escolas():
    """Carrega o arquivo CSV limpo das escolas prioritárias"""
    try:
        dados = pd.read_csv('planilhas/Escolas_Prioritarias_LIMPO.csv', encoding='utf-8')
        return dados
    except Exception as e:
        st.error(f"Erro ao carregar o arquivo limpo: {e}")
        return None

@st.cache_data
def carregar_dados_metas_ideb():
    """Carrega os dados de metas e IDEB"""
    try:
        codificacoes = ['latin-1', 'iso-8859-1', 'cp1252', 'utf-8']
        
        for encoding in codificacoes:
            try:
                df = pd.read_csv('planilhas/metas e idebes.csv', sep=';', decimal=',', encoding=encoding)
                return df
            except UnicodeDecodeError:
                continue
            except Exception:
                continue
        
        df = pd.read_csv('planilhas/metas e idebes.csv', sep=';', decimal=',', encoding='latin-1', engine='python')
        return df
    except Exception as e:
        st.error(f"Erro ao carregar arquivo de metas e IDEB: {e}")
        return pd.DataFrame()

@st.cache_data
def carregar_mapeamento_sre():
    """Carrega o mapeamento SRE do arquivo CSV"""
    try:
        df_regionais = pd.read_csv('mapa/regionais_sedu.csv', encoding='utf-8')
        return df_regionais
    except Exception as e:
        st.error(f"Erro ao carregar mapeamento SRE: {e}")
        return pd.DataFrame(columns=['MUNICIPIO', 'REGIONAL_SRE'])

# REMOVI O @st.cache_data DESTA FUNÇÃO
def aplicar_mapeamento_sre(gdf):
    """Aplica o mapeamento SRE a um GeoDataFrame"""
    df_regionais = carregar_mapeamento_sre()
    
    if df_regionais.empty:
        gdf['REGIONAL_SRE'] = 'SRE ' + gdf['NM_MUN'].str[:3]
    else:
        mapeamento_sre = dict(zip(df_regionais['MUNICIPIO'], df_regionais['REGIONAL_SRE']))
        gdf['REGIONAL_SRE'] = gdf['NM_MUN'].str.upper().map(mapeamento_sre)
        gdf['REGIONAL_SRE'] = gdf['REGIONAL_SRE'].fillna('SRE Não Especificada')
    
    return gdf

# MANTIVE O CACHE AQUI PORQUE A FUNÇÃO INTERNA FOI CORRIGIDA
@st.cache_data
def carregar_dados_geograficos():
    """Carrega os municípios do ES a partir do shapefile"""
    try:
        import geopandas as gpd
        
        gdf_br = gpd.read_file('mapa/BR_Municipios_2022.shp')
        
        # Identificar a coluna do código da UF
        coluna_uf = None
        for col in ['CD_UF', 'COD_UF', 'SIGLA_UF', 'UF']:
            if col in gdf_br.columns:
                coluna_uf = col
                break
        
        if coluna_uf is None:
            st.error("Não foi possível encontrar coluna de UF no shapefile")
            return None
        
        # Filtrar apenas Espírito Santo
        if gdf_br[coluna_uf].dtype == 'object':
            gdf_es = gdf_br[gdf_br[coluna_uf] == '32'].copy()
        else:
            gdf_es = gdf_br[gdf_br[coluna_uf] == 32].copy()
        
        # Identificar coluna do nome do município
        coluna_nome = None
        for col in ['NM_MUN', 'NOME_MUN', 'MUNICIPIO', 'NOME']:
            if col in gdf_es.columns:
                coluna_nome = col
                break
        
        if coluna_nome is None:
            st.error("Não foi possível encontrar coluna de nome do município")
            return None
        
        gdf_es = gdf_es.rename(columns={coluna_nome: 'NM_MUN'})
        
        # Agora esta função não tem mais cache, então não dá erro
        gdf_es = aplicar_mapeamento_sre(gdf_es)
        
        return gdf_es
        
    except Exception as e:
        st.error(f"Erro ao carregar shapefile: {e}")
        return None

# --- BARRA LATERAL PARA NAVEGAÇÃO ---
st.sidebar.title("Navegação")
selecao = st.sidebar.radio("Escolha a seção:",
                           ["Página Inicial", "Introdução", "Critérios de Seleção", "Dados básicos", "Gráficos", "Mapas"])

# --- Status do Sistema ---
arquivos_faltantes = verificar_arquivos()
if arquivos_faltantes:
    st.sidebar.error(f"⚠️ Arquivos faltantes: {len(arquivos_faltantes)}")
else:
    st.sidebar.success("✅ Todos os arquivos encontrados")

# --- SEÇÃO: PÁGINA INICIAL ---
if selecao == "Página Inicial":
   st.image("images/brasao1.png")
   st.title("Educação no Espírito Santo: Escolas Prioritárias")
   st.subheader("Autor: Luís Eduardo Formentini")
   
   col1, col2 = st.columns([2, 1])
   
   with col1:
       st.header("Bem-vindo!")
       st.write("""
               Este aplicativo é um protótipo para análise de dados educacionais.
               Ele está dividido em seções para futura expansão com tabelas, gráficos e mapas.
               """)
   
   with col2:
       st.image("images/euzin.jpg", caption="Prof Ms Luís Eduardo Formentini")

# --- SEÇÃO: INTRODUÇÃO ---
elif selecao == "Introdução":
    st.header("O que são Escolas Prioritárias?")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("""
        As **Escolas Prioritárias** são unidades escolares que demandam maior apoio da SEDU e da SRE, no que diz respeito
        ao alcance ou não das metas, considerando os resultados do Índice de Desenvolvimento da
        Educação Básica - IDEB e/ou Índice de Desenvolvimento da Educação Básica no Espírito
        Santo - IDEBES, além de outros critérios que a SEDU julgar necessário.
        
        As Escolas Prioritárias foram instituídas na Rede Estadual de Ensino do Espírito Santo como parte das ações do **Circuito de Gestão (CdG)** por meio da Portaria Nº 034-R, de 16 de fevereiro de 2018. 
        """)
    
    with col2:
        st.image("images/brasao2.jpg")

# --- SEÇÃO: CRITÉRIOS DE SELEÇÃO ---
elif selecao == "Critérios de Seleção":
    st.header("Critérios de Seleção das Escolas Prioritárias")
    
    st.write("""
    Os critérios estabelecidos para a definição das Escolas Prioritárias consideram diferentes dimensões da equidade e do desempenho educacional.
    """)
    
    dados_escolas = carregar_dados_escolas()
    
    if dados_escolas is not None:
        if 'SRE' in dados_escolas.columns and 'ESCOLA' in dados_escolas.columns:
            st.subheader("Filtro por SRE")
            
            sres = sorted(dados_escolas["SRE"].unique())
            sres_selecionadas = st.multiselect(
                "Selecione a(s) SRE(s):",
                options=sres,
                default=sres
            )
            
            dados_filtrados = dados_escolas[dados_escolas["SRE"].isin(sres_selecionadas)]
            
            st.subheader(f"Escolas Prioritárias ({len(dados_filtrados)} encontradas)")
            st.dataframe(dados_filtrados, width='stretch')
            
            if len(dados_filtrados) > 0:
                st.write(f"**Total de escolas:** {len(dados_filtrados)}")
                st.write(f"**SREs representadas:** {len(dados_filtrados['SRE'].unique())}")
        
        else:
            st.error("Colunas 'SRE' e 'ESCOLA' não encontradas no arquivo limpo.")

# --- SEÇÃO: DADOS BÁSICOS ---
elif selecao == "Dados básicos":
    st.header("Dados básicos")
    st.write("Aqui vamos mostrar tabelas com informações de escolas.")
    dados = pd.DataFrame({
        "Escola": ["Escola A", "Escola B", "Escola C"],
        "Município": ["Vitória", "Serra", "Vila Velha"],
        "IDEBES 2024": [5.6, 6.2, 5.9]
    })
    st.dataframe(dados, width='stretch')

# --- SEÇÃO: GRÁFICOS ---
elif selecao == "Gráficos":
    st.header("📊 Análise de Metas e IDEBES")
    st.markdown("Série histórica de 2021 a 2024")
    
    df = carregar_dados_metas_ideb()
    
    if df.empty:
        st.error("Não foi possível carregar os dados de metas e IDEB.")
    else:
        st.sidebar.header("Filtros - Metas e IDEB")
        
        municipio_options = ['Todos'] + sorted(df['MUNICÍPIO'].unique().tolist())
        municipio_selecionado = st.sidebar.selectbox(
            "Selecione o Município:",
            options=municipio_options,
            index=1 if len(municipio_options) > 1 else 0
        )
        
        if municipio_selecionado == "Todos":
            escola_options = ['Todas'] + sorted(df['ESCOLA'].unique().tolist())
        else:
            escola_options = ['Todas'] + sorted(df[df['MUNICÍPIO'] == municipio_selecionado]['ESCOLA'].unique().tolist())
        
        escola_selecionada = st.sidebar.selectbox(
            "Selecione a Escola:",
            options=escola_options,
            index=1 if len(escola_options) > 1 else 0
        )
        
        if municipio_selecionado == "Todos":
            dados_filtrados = df.copy()
        else:
            dados_filtrados = df[df['MUNICÍPIO'] == municipio_selecionado]
        
        if escola_selecionada != "Todas":
            dados_filtrados = dados_filtrados[dados_filtrados['ESCOLA'] == escola_selecionada]
        else:
            if municipio_selecionado != "Todos" and not dados_filtrados.empty:
                escola_padrao = dados_filtrados['ESCOLA'].iloc[0]
                dados_filtrados = dados_filtrados[dados_filtrados['ESCOLA'] == escola_padrao]
                escola_selecionada = escola_padrao
        
        if not dados_filtrados.empty:
            dados_filtrados = dados_filtrados.sort_values('ANO')
            
            import plotly.graph_objects as go
            fig = go.Figure()

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

            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("📋 Dados Detalhados")
            st.dataframe(
                dados_filtrados[['ANO', 'META', 'IDEBES']].style.format({'META': '{:.2f}', 'IDEBES': '{:.2f}'}),
                width='stretch'
            )
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Média da META", f"{dados_filtrados['META'].mean():.2f}")
            with col2:
                st.metric("Média do IDEBES", f"{dados_filtrados['IDEBES'].mean():.2f}")
            with col3:
                ultimo_ano = dados_filtrados.iloc[-1]
                desempenho = "✅ Atingiu" if ultimo_ano['IDEBES'] >= ultimo_ano['META'] else "❌ Não Atingiu"
                st.metric("Desempenho 2024", desempenho)

# --- SEÇÃO: MAPAS ---
elif selecao == "Mapas":
    st.header("🗺️ Mapas Interativos das Escolas Prioritárias")
    
    try:
        import geopandas as gpd
        from streamlit_folium import st_folium
    except ImportError:
        st.error("""
        **Bibliotecas necessárias não encontradas!**
        Instale com: `pip install geopandas streamlit-folium`
        """)
        st.stop()
    
    # Carregar dados
    with st.spinner("Carregando dados geográficos..."):
        gdf_es = carregar_dados_geograficos()
    
    escolas_prioritarias = carregar_dados_escolas()
    
    # === DIAGNÓSTICO - ADICIONE ESTAS LINHAS ===
    st.subheader("🔍 Diagnóstico dos Dados")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Dados Geográficos (gdf_es):**")
        if gdf_es is not None:
            st.success(f"✅ Carregado: {len(gdf_es)} municípios")
            st.write(f"Colunas: {list(gdf_es.columns)}")
            if 'REGIONAL_SRE' in gdf_es.columns:
                st.write(f"Coluna REGIONAL_SRE: {gdf_es['REGIONAL_SRE'].unique()[:5]}")
            else:
                st.error("❌ Coluna REGIONAL_SRE não encontrada")
            st.dataframe(gdf_es[['NM_MUN', 'REGIONAL_SRE']].head() if 'REGIONAL_SRE' in gdf_es.columns else gdf_es.head(), width='stretch')
        else:
            st.error("❌ gdf_es é None")
    
    with col2:
        st.write("**Dados das Escolas:**")
        if escolas_prioritarias is not None:
            st.success(f"✅ Carregado: {len(escolas_prioritarias)} escolas")
            st.write(f"Colunas: {list(escolas_prioritarias.columns)}")
            # Verificar se tem coordenadas
            if 'LATITUDE' in escolas_prioritarias.columns and 'LONGITUDE' in escolas_prioritarias.columns:
                escolas_com_coord = escolas_prioritarias[escolas_prioritarias['LATITUDE'].notna()].shape[0]
                st.write(f"Escolas com coordenadas: {escolas_com_coord}")
                st.dataframe(escolas_prioritarias[['ESCOLA', 'LATITUDE', 'LONGITUDE']].head(), width='stretch')
            else:
                st.error("❌ Colunas LATITUDE e LONGITUDE não encontradas")
                # Mostrar quais colunas existem que podem ser coordenadas
                colunas_coordenadas = [col for col in escolas_prioritarias.columns if 'LAT' in col.upper() or 'LONG' in col.upper() or 'COORD' in col.upper()]
                if colunas_coordenadas:
                    st.write(f"Colunas que podem ser coordenadas: {colunas_coordenadas}")
        else:
            st.error("❌ escolas_prioritarias é None")
    # === FIM DO DIAGNÓSTICO ===
    
    if gdf_es is None or escolas_prioritarias is None:
        st.error("Não foi possível carregar os dados para o mapa.")
    else:
        # Estatísticas
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Municípios", len(gdf_es))
        with col2:
            if 'REGIONAL_SRE' in gdf_es.columns:
                st.metric("SREs", gdf_es['REGIONAL_SRE'].nunique())
            else:
                st.metric("SREs", "N/A")
        with col3:
            st.metric("Escolas", len(escolas_prioritarias))
        
        # Configurações
        st.subheader("Configurações do Mapa")
        col1, col2 = st.columns(2)
        
        with col1:
            zoom_inicial = st.slider("Zoom Inicial", 7, 12, 8)
        with col2:
            mostrar_legenda = st.checkbox("Mostrar Legenda", value=True)
        
        # Criar mapa
        try:
            import folium
            import matplotlib.colors as mcolors
            import random
            
            m = folium.Map(
                location=[-20.3, -40.3], 
                zoom_start=zoom_inicial, 
                min_zoom=7, 
                max_zoom=13
            )
            
            # Cores para cada SRE (se existir a coluna)
            if 'REGIONAL_SRE' in gdf_es.columns:
                regionais_unicas = gdf_es['REGIONAL_SRE'].dropna().unique()
                cores_disponiveis = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())
                random.shuffle(cores_disponiveis)
                cores_regionais = {regional: cores_disponiveis[i] for i, regional in enumerate(regionais_unicas)}
                
                # Adicionar municípios com cores
                for _, row in gdf_es.iterrows():
                    regional = row['REGIONAL_SRE']
                    cor = cores_regionais.get(regional, 'gray')
                    geojson = folium.GeoJson(
                        row['geometry'],
                        style_function=lambda feature, cor=cor: {
                            'fillColor': cor,
                            'color': 'black',
                            'weight': 0.5,
                            'fillOpacity': 0.6
                        },
                        tooltip=folium.Tooltip(f"{row['NM_MUN']} - {regional}")
                    )
                    geojson.add_to(m)
            else:
                # Fallback: municípios sem cores por SRE
                for _, row in gdf_es.iterrows():
                    geojson = folium.GeoJson(
                        row['geometry'],
                        style_function=lambda feature: {
                            'fillColor': 'lightblue',
                            'color': 'black',
                            'weight': 0.5,
                            'fillOpacity': 0.6
                        },
                        tooltip=folium.Tooltip(f"{row['NM_MUN']}")
                    )
                    geojson.add_to(m)
                st.warning("⚠️ Mostrando municípios sem cores por SRE (coluna REGIONAL_SRE não encontrada)")
            
            # Adicionar escolas (se tiver coordenadas)
            escolas_com_coordenadas = 0
            if 'LATITUDE' in escolas_prioritarias.columns and 'LONGITUDE' in escolas_prioritarias.columns:
                for index, row in escolas_prioritarias.iterrows():
                    if pd.notna(row.get('LATITUDE')) and pd.notna(row.get('LONGITUDE')):
                        nome = row['ESCOLA']
                        lat = row['LATITUDE']
                        lon = row['LONGITUDE']
                        idebes = row.get('IDEBES 2024', 'N/A')
                        
                        popup_text = f"<strong>{nome}</strong><br>IDEBES 2024: {idebes}"
                        
                        folium.Marker(
                            location=[lat, lon],
                            popup=popup_text,
                            icon=folium.Icon(color='red', icon='info-sign')
                        ).add_to(m)
                        escolas_com_coordenadas += 1
            else:
                st.warning("⚠️ Não foi possível adicionar escolas ao mapa (coordenadas não encontradas)")
            
            # Legenda (se tiver SREs)
            if mostrar_legenda and 'REGIONAL_SRE' in gdf_es.columns and cores_regionais:
                legend_html = '''
                <div style="position: fixed; bottom: 50px; left: 50px; width: 250px; height: auto; 
                            background-color: white; border:2px solid grey; z-index:9999; 
                            font-size:12px; padding: 10px; border-radius: 5px;">
                <p style="margin:0; font-weight:bold;">Legenda - Regionais SEDU</p>
                '''
                
                for regional, cor in list(cores_regionais.items()):
                    legend_html += f'<p style="margin:2px 0;"><i class="fa fa-square" style="color:{cor}"></i> {regional}</p>'
                
                legend_html += '</div>'
                m.get_root().html.add_child(folium.Element(legend_html))
            
            # Estatísticas
            st.success(f"""
            **Mapa gerado com sucesso!**
            - 🏙️ {len(gdf_es)} municípios carregados
            - 🏫 {escolas_com_coordenadas} escolas prioritárias marcadas
            """)
            
            # Mostrar mapa
            st_folium(m, width=800, height=600, returned_objects=[])
            
        except Exception as e:
            st.error(f"Erro ao gerar o mapa: {e}")


# --- STATUS FINAL ---
st.sidebar.markdown("---")
st.sidebar.info("Sistema de Análise Educacional - v1.0")