# Código temporário para diagnóstico - pode colocar em uma célula separada ou no início
import pandas as pd
import streamlit as st

def limpar_csv():
    # Lê o arquivo
    try:
        df = pd.read_csv('Escolas Prioritárias trabalho.csv', sep=';', encoding='utf-8')
    except:
        df = pd.read_csv('Escolas Prioritárias trabalho.csv', sep=';', encoding='latin-1')
    
    st.write("**Arquivo original:**")
    st.write("Colunas:", df.columns.tolist())
    st.dataframe(df.head(10))
    
    # Limpeza
    df_limpo = df.copy()
    
    # Remove BOM se existir
    df_limpo.columns = df_limpo.columns.str.replace('\ufeff', '')
    
    # Se tiver apenas uma coluna com os dados separados por ;
    if len(df_limpo.columns) == 1 and ';' in df_limpo.iloc[0, 0]:
        st.info("Separando dados que estão em uma coluna...")
        colunas_separadas = df_limpo[df_limpo.columns[0]].str.split(';', expand=True)
        if colunas_separadas.shape[1] >= 2:
            df_limpo = colunas_separadas
            df_limpo.columns = ['SRE', 'ESCOLA'][:colunas_separadas.shape[1]]
    
    # Remove linhas vazias
    df_limpo = df_limpo.dropna()
    
    st.write("**Arquivo limpo:**")
    st.write("Colunas:", df_limpo.columns.tolist())
    st.dataframe(df_limpo.head(10))
    
    # Salva o arquivo limpo
    df_limpo.to_csv('Escolas_Prioritarias_LIMPO.csv', index=False, encoding='utf-8')
    st.success("Arquivo limpo salvo como 'Escolas_Prioritarias_LIMPO.csv'")
    
    return df_limpo

# Para executar a limpeza
df_limpo = limpar_csv()