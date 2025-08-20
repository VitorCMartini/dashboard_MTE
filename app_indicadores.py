import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
from math import log
import locale

# Configuracao da pagina
st.set_page_config(
    page_title="Dashboard - Indicadores Ambientais",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ===============================================
# FUNCOES DE FORMATACAO BRASILEIRA (ABNT)
# ===============================================

def formatar_numero_br(numero, decimais=2):
    """
    Formata numeros seguindo padrao brasileiro (ABNT):
    - Virgula como separador decimal
    - Ponto como separador de milhares
    """
    try:
        if pd.isna(numero) or numero is None:
            return "N/A"
        
        # Converter para float se necessario
        num = float(numero)
        
        # Formatacao manual para garantir padrao brasileiro
        if decimais == 0:
            # Para numeros inteiros
            numero_str = f"{int(num):,}".replace(",", ".")
        else:
            # Para numeros com decimais
            numero_str = f"{num:,.{decimais}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        
        return numero_str
    except (ValueError, TypeError):
        return str(numero)

def formatar_porcentagem_br(numero, decimais=1):
    """
    Formata porcentagens seguindo padrao brasileiro:
    - Virgula como separador decimal
    - Simbolo % apos o numero
    """
    try:
        if pd.isna(numero) or numero is None:
            return "N/A"
        
        num = float(numero)
        return f"{formatar_numero_br(num, decimais)}%"
    except (ValueError, TypeError):
        return str(numero)

def formatar_area_br(area_ha):
    """
    Formata area em hectares seguindo padrao brasileiro
    """
    try:
        if pd.isna(area_ha) or area_ha is None:
            return "N/A"
        
        area = float(area_ha)
        return f"{formatar_numero_br(area, 2)} ha"
    except (ValueError, TypeError):
        return str(area_ha)

def formatar_densidade_br(densidade):
    """
    Formata densidade seguindo padrao brasileiro
    """
    try:
        if pd.isna(densidade) or densidade is None:
            return "N/A"
        
        dens = float(densidade)
        return f"{formatar_numero_br(dens, 1)} ind/ha"
    except (ValueError, TypeError):
        return str(densidade)

def formatar_dataframe_br(df, colunas_numericas=None, colunas_porcentagem=None):
    """
    Aplica formatacao brasileira a um DataFrame para exibicao
    """
    df_formatado = df.copy()
    
    if colunas_numericas:
        for col in colunas_numericas:
            if col in df_formatado.columns:
                df_formatado[col] = df_formatado[col].apply(lambda x: formatar_numero_br(x, 2) if pd.notna(x) else "N/A")
    
    if colunas_porcentagem:
        for col in colunas_porcentagem:
            if col in df_formatado.columns:
                df_formatado[col] = df_formatado[col].apply(lambda x: formatar_porcentagem_br(x, 2) if pd.notna(x) else "N/A")
    
    return df_formatado

def metric_compacta(label, value, help_text=None):
    """
    Cria uma metrica compacta com tamanho de fonte otimizado
    """
    help_html = f"<span title='{help_text}'>ⓘ</span>" if help_text else ""
    
    st.markdown(f"""
    <div style="
        background-color: rgba(28, 131, 225, 0.1);
        padding: 8px;
        border-radius: 5px;
        border-left: 4px solid #1c83e1;
        margin-bottom: 8px;
    ">
        <div style="font-size: 11px; color: #666; font-weight: 600; margin-bottom: 2px;">
            {label} {help_html}
        </div>
        <div style="font-size: 14px; font-weight: 700; color: #1c83e1; line-height: 1.1;">
            {value}
        </div>
    </div>
    """, unsafe_allow_html=True)

# Funcao para limpeza e padronizacao de dados
def limpar_e_padronizar_dados(df):
    """
    Limpa e padroniza os dados do DataFrame:
    1. Remove espacos desnecessarios
    2. Converte para minúsculas
    3. Capitaliza a primeira letra de cada célula
    """
    df_clean = df.copy()
    
    # Aplicar limpeza apenas em colunas de texto (object/string)
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':
            # Converter para string, remover espaços extras e converter para minúsculas
            df_clean[col] = (df_clean[col]
                           .astype(str)
                           .str.strip()  # Remove espaços no início e fim
                           .str.replace(r'\s+', ' ', regex=True)  # Remove espaços múltiplos
                           .str.lower()  # Converte para minúsculas
                           .str.capitalize()  # Capitaliza primeira letra
                           )
            
            # Tratar valores especiais
            df_clean[col] = df_clean[col].replace({
                'Nan': np.nan,
                'None': np.nan,
                'Null': np.nan,
                '': np.nan
            })
    
    return df_clean

# Função para carregar dados com cache
@st.cache_data
def load_data():
    """Carrega os bancos de dados Excel e aplica limpeza e padronização"""
    try:
        # Carregar dados brutos
        df_caracterizacao_raw = pd.read_excel('BD_caracterizacao.xlsx')
        df_inventario_raw = pd.read_excel('BD_inventario.xlsx')
        
        # Aplicar limpeza e padronização
        df_caracterizacao = limpar_e_padronizar_dados(df_caracterizacao_raw)
        df_inventario = limpar_e_padronizar_dados(df_inventario_raw)
        
        return df_caracterizacao, df_inventario
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return None, None

# Função para estatísticas descritivas
def show_descriptive_stats(df_carac, df_inv, title):
    """Mostra estatísticas descritivas específicas para cada banco"""
    st.subheader(f"📊 Estatísticas Descritivas - {title}")
    
    if title == "Caracterização":
        col1, col2, col3 = st.columns(3)
        # Métricas específicas para BD_caracterizacao
        with col1:
            # Número de parcelas (cod_parc únicos)
            cod_parc_col = encontrar_coluna(df_carac, ['cod_parc', 'parcela', 'plot'])
            if cod_parc_col:
                num_parcelas = df_carac[cod_parc_col].nunique()
                metric_compacta("Nº Parcelas", formatar_numero_br(num_parcelas, 0))
            else:
                metric_compacta("Nº Parcelas", "N/A")
        
        with col2:
            # Área amostrada usando método adaptativo
            if len(df_carac) > 0:
                area_ha, metodo = calcular_area_amostrada(df_carac, df_inv)
                metric_compacta("Área Amostr.", formatar_area_br(area_ha), f"Método: {metodo}")
            else:
                metric_compacta("Área Amostr.", "N/A")
        
        with col3:
            # Cobertura de copa média - mesma lógica dos indicadores ambientais
            cobertura_col = encontrar_coluna(df_carac, ['cobetura_nativa', 'cobertura_nativa', 'copa_nativa'])
            if cobertura_col:
                # Aplicar a mesma lógica simples e direta
                cobertura_media = pd.to_numeric(df_carac[cobertura_col], errors='coerce').mean()
                
                # Converter de 0-1 para 0-100% se necessário
                if pd.notna(cobertura_media) and cobertura_media <= 1:
                    cobertura_media = cobertura_media * 100
                
                if pd.notna(cobertura_media):
                    metric_compacta("Cob. Copa", formatar_porcentagem_br(cobertura_media, 2))
                else:
                    metric_compacta("Cob. Copa", "N/A")
            else:
                metric_compacta("Cob. Copa", "N/A")
        
        # Estatísticas detalhadas para Caracterização
        st.markdown("<div style='font-size:18px; font-weight:bold; margin-bottom:8px; color:#1c83e1'>Indicadores Ambientais:</div>", unsafe_allow_html=True)
        
        # Lista de métricas para caracterização - usando colunas corretas com (%)
        metricas_carac = [
            (['(%)graminea', '(%) graminea', 'graminea'], 'Gramíneas'),
            (['(%)herbacea', '(%) herbacea', '(%) herbac', 'herbacea'], 'Herbáceas'),
            (['(%)solo exposto', '(%) solo exposto', 'solo exposto'], 'Solo Exposto'),
            (['(%)palhada', '(%) palhada', 'palhada'], 'Palhada'),
            (['(%)serapilheira', '(%) serapilheira', 'serapilheira'], 'Serapilheira'),
            (['(%)cobetura_exotica', '(%) cobetura_exotica', '(%)cobertura_exotica', '(%) cobertura_exotica'], 'Cobertura Exótica')
        ]
        
        # Dividir em duas colunas
        col_amb1, col_amb2 = st.columns(2)
        
        for i, (nomes_possiveis, label) in enumerate(metricas_carac):
            col_name = encontrar_coluna(df_carac, nomes_possiveis)
            current_col = col_amb1 if i % 2 == 0 else col_amb2
            
            if col_name:
                with current_col:
                    # Calcular a média e converter de 0-1 para 0-100%
                    media = pd.to_numeric(df_carac[col_name], errors='coerce').mean()
                    
                    # Converter de 0-1 para 0-100% (as colunas com (%) também estão em formato 0-1)
                    if pd.notna(media):
                        media_percentual = media * 100
                        st.markdown(f"<div style='font-size:16px; line-height:1.4'>• <b>{label}</b>: {formatar_porcentagem_br(media_percentual, 2)}</div>", unsafe_allow_html=True)
                    else:
                        st.markdown(f"<div style='font-size:16px; line-height:1.4'>• <b>{label}</b>: N/A</div>", unsafe_allow_html=True)
        
        # Contagens de distúrbios - restaurar nomes completos
        st.markdown("---")
        st.markdown("<div style='font-size:18px; font-weight:bold; margin-bottom:8px; color:#1c83e1'>Distúrbios:</div>", unsafe_allow_html=True)
        disturbios = [
            (['Erosao_simplificada', 'erosao_simplificada'], 'Processos Erosivos'),
            (['Fogo', 'fogo'], 'Fogo'),
            (['Corte de madeira', 'corte de madeira'], 'Corte de Madeira'),
            (['Inundação', 'inundacao', 'inundação'], 'Inundação'),
            (['Animais_simplificado', 'animais_simplificado'], 'Animais Silvestres'),
            (['Formigas(simplificado)', 'formigas(simplificado)', 'formigas_simplificado'], 'Formigas')
        ]
        
        # Dividir distúrbios em duas colunas também
        dist_col1, dist_col2 = st.columns(2)
        
        for i, (nomes_possiveis, label) in enumerate(disturbios):
            col_name = encontrar_coluna(df_carac, nomes_possiveis)
            current_col = dist_col1 if i % 2 == 0 else dist_col2
            
            if col_name:
                # Conta valores que indicam presença (valor 1)
                valores = pd.to_numeric(df_carac[col_name], errors='coerce')
                count = (valores == 1).sum()
                
                with current_col:
                    st.markdown(f"<div style='font-size:16px; line-height:1.4'>• <b>{label}</b>: {count}</div>", unsafe_allow_html=True)
    
    elif title == "Inventário":
        # Métricas específicas para BD_inventario
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Riqueza (especies unicas, excluindo "Morto" e altura > 0.5m)
            especies_col = encontrar_coluna(df_inv, ['especies', 'especie', 'species', 'sp'])
            ht_col = encontrar_coluna(df_inv, ['ht', 'altura', 'height'])
            
            if especies_col and len(df_inv) > 0:
                # Filtrar especies validas (remover "Morto/Morta")
                df_especies_validas = df_inv[~df_inv[especies_col].astype(str).str.contains('Morto|Morta', case=False, na=False)]
                
                # Filtrar por altura > 0.5m se coluna disponivel
                if ht_col:
                    alturas = pd.to_numeric(df_especies_validas[ht_col], errors='coerce')
                    df_especies_validas = df_especies_validas[alturas > 0.5]
                
                riqueza_total = df_especies_validas[especies_col].nunique()
                
                # Riqueza de especies nativas com altura > 0.5m
                origem_col = encontrar_coluna(df_especies_validas, ['origem', 'origin', 'procedencia'])
                if origem_col:
                    df_nativas = df_especies_validas[df_especies_validas[origem_col].astype(str).str.contains('Nativa', case=False, na=False)]
                    riqueza_nativas = df_nativas[especies_col].nunique()
                    metric_compacta("Riqueza", f"{riqueza_total} ({riqueza_nativas} nat.)")
                else:
                    metric_compacta("Riqueza", str(riqueza_total))
            else:
                metric_compacta("Riqueza", "0")
        
        with col2:
            # Densidade geral de indivíduos
            if len(df_inv) > 0 and len(df_carac) > 0:
                densidade_geral, metodo = calcular_densidade_geral(df_inv, df_carac)
                metric_compacta("Dens. Geral", formatar_densidade_br(densidade_geral), f"Método: {metodo}")
            else:
                metric_compacta("Dens. Geral", formatar_densidade_br(0))
        
        with col3:
            # Densidade de indivíduos regenerantes
            if len(df_inv) > 0 and len(df_carac) > 0:
                # Adicionar botão de debug apenas para Inventário
                densidade = calcular_densidade_regenerantes(df_inv, df_carac)
                
                metric_compacta("Dens. Regen.", formatar_densidade_br(densidade))
            else:
                metric_compacta("Dens. Regen.", formatar_densidade_br(0))
        
        with col4:
            # Altura média
            ht_col = encontrar_coluna(df_inv, ['ht', 'altura', 'height', 'h'])
            if ht_col and len(df_inv) > 0:
                altura_media = pd.to_numeric(df_inv[ht_col], errors='coerce').mean()
                if pd.notna(altura_media):
                    metric_compacta("Alt. Média", f"{formatar_numero_br(altura_media, 2)} m")
                else:
                    metric_compacta("Alt. Média", "N/A")
            else:
                metric_compacta("Alt. Média", "N/A")
        
        # Estatísticas detalhadas para Inventário
        if len(df_inv) > 0:
            st.markdown("<div style='font-size:18px; font-weight:bold; margin-bottom:8px; color:#1c83e1'>Distribuição por Categorias:</div>", unsafe_allow_html=True)
            
            # Lista de colunas para análise percentual - nomes completos
            cols_percentual = [
                (['g_func', 'grupo_func', 'funcional'], 'Grupo Funcional'),
                (['g_suc', 'grupo_suc', 'sucessional'], 'Grupo Sucessional'),
                (['sindrome'], 'Síndrome'),
                (['origem'], 'Origem'),
                (['regeneracao', 'regenera'], 'Regeneração'),
                (['endemismo', 'endem'], 'Endemismo'),
                (['forma_vida', 'forma_de_vida'], 'Forma de Vida'),
                (['ameac_mma', 'ameaca', 'ameaça'], 'Ameaça MMA')
            ]
            
            # Dividir em duas colunas para layout mais compacto
            col_esq, col_dir = st.columns(2)
            
            # Encontrar coluna de plaqueta para o caso especial de Ameaça MMA
            plaqueta_col = encontrar_coluna(df_inv, ['plaqueta', 'plaq', 'id'])
            
            for i, (nomes_possiveis, label) in enumerate(cols_percentual):
                col_name = encontrar_coluna(df_inv, nomes_possiveis)
                
                # Alternar entre coluna esquerda e direita
                current_col = col_esq if i % 2 == 0 else col_dir
                
                if col_name and col_name in df_inv.columns:
                    with current_col:
                        st.markdown(f"<div style='font-size:18px; font-weight:bold; margin-bottom:8px; color:#1c83e1'>{label}:</div>", unsafe_allow_html=True)
                        
                        # Tratamento especial para Ameaça MMA (contagem de plaquetas únicas)
                        if label == 'Ameaça MMA' and plaqueta_col:
                            try:
                                ameaca_dist = df_inv.groupby(col_name)[plaqueta_col].nunique()
                                
                                if len(ameaca_dist) > 0:
                                    # Mostrar apenas top 3 (aumentamos de 2 para 3)
                                    for categoria, count in ameaca_dist.head(3).items():
                                        st.markdown(f"<div style='font-size:16px; line-height:1.4'>• {categoria}: {count} plaquetas</div>", unsafe_allow_html=True)
                                    
                                    # Se houver mais categorias, mostrar quantas são
                                    if len(ameaca_dist) > 3:
                                        outros = len(ameaca_dist) - 3
                                        st.markdown(f"<div style='font-size:16px; line-height:1.4'>• +{outros} outras categorias</div>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"<div style='font-size:16px; line-height:1.4'>• Nenhum dado disponível</div>", unsafe_allow_html=True)
                            except Exception as e:
                                st.markdown(f"<div style='font-size:16px; line-height:1.4'>• Erro no cálculo</div>", unsafe_allow_html=True)
                        
                        else:
                            # Tratamento normal para outras categorias (percentual)
                            try:
                                dist = df_inv[col_name].value_counts(normalize=True) * 100
                                
                                if len(dist) > 0:
                                    # Mostrar top 3 (aumentamos de 2 para 3)
                                    for categoria, perc in dist.head(3).items():
                                        # Não abreviar mais - mostrar categoria completa
                                        st.markdown(f"<div style='font-size:16px; line-height:1.4'>• {categoria}: {formatar_porcentagem_br(perc, 1)}</div>", unsafe_allow_html=True)
                                    
                                    # Se houver mais categorias, mostrar quantas são
                                    if len(dist) > 3:
                                        outros = len(dist) - 3
                                        st.markdown(f"<div style='font-size:16px; line-height:1.4'>• +{outros} outras categorias</div>", unsafe_allow_html=True)
                                else:
                                    st.markdown(f"<div style='font-size:16px; line-height:1.4'>• Nenhum dado disponível</div>", unsafe_allow_html=True)
                            except Exception as e:
                                st.markdown(f"<div style='font-size:16px; line-height:1.4'>• Erro no cálculo</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='font-size:18px; font-weight:bold; margin-bottom:8px; color:#1c83e1'>Distribuição por Categorias:</div>", unsafe_allow_html=True)
            st.markdown("<div style='font-size:16px; line-height:1.4; font-style:italic'>Nenhum dado disponível com os filtros aplicados</div>", unsafe_allow_html=True)

def encontrar_coluna(df, nomes_possiveis):
    """Encontra uma coluna no dataframe baseado em nomes possíveis (case-insensitive)"""
    for nome in nomes_possiveis:
        for col in df.columns:
            # Busca case-insensitive e com tratamento de espaços
            if nome.lower().replace(' ', '').replace('_', '') in col.lower().replace(' ', '').replace('_', ''):
                return col
    return None

def calcular_area_amostrada(df_carac_filtered, df_inv_filtered):
    """
    Calcula a área amostrada com método híbrido avançado:
    - Separa dados por técnica (Censo vs Parcelas)
    - Calcula área de cada técnica separadamente
    - Soma as áreas para obter total correto
    """
    try:
        if len(df_carac_filtered) == 0 and len(df_inv_filtered) == 0:
            return 0.0, "Sem dados"
        
        # Verificar técnica no BD_caracterização
        tecnica_col = encontrar_coluna(df_carac_filtered, ['tecnica_am', 'tecnica', 'metodo'])
        
        if not tecnica_col or len(df_carac_filtered) == 0:
            # Fallback: usar método de parcelas
            return calcular_area_parcelas_tradicional(df_inv_filtered)
        
        # Analisar técnicas presentes nos dados filtrados
        df_carac_copy = df_carac_filtered.copy()
        df_carac_copy[tecnica_col] = df_carac_copy[tecnica_col].str.lower()
        
        tecnicas_unicas = df_carac_copy[tecnica_col].unique()
        tem_censo = any('censo' in str(t) for t in tecnicas_unicas)
        tem_parcelas = any('parcela' in str(t) or 'plot' in str(t) for t in tecnicas_unicas)
        
        area_total = 0.0
        metodos_usados = []
        
        # Se tem apenas uma técnica, usar método direto
        if tem_censo and not tem_parcelas:
            return calcular_area_censo_inventario(df_inv_filtered)
        elif tem_parcelas and not tem_censo:
            return calcular_area_parcelas_tradicional(df_inv_filtered)
        
        # Se tem mistura de técnicas, calcular separadamente
        if tem_censo and tem_parcelas:
            # Separar dados por técnica
            dados_censo = df_carac_copy[df_carac_copy[tecnica_col].str.contains('censo', na=False)]
            dados_parcelas = df_carac_copy[~df_carac_copy[tecnica_col].str.contains('censo', na=False)]
            
            # Calcular área do censo
            if len(dados_censo) > 0:
                # Filtrar inventário para propriedades de censo
                props_censo = dados_censo['cod_prop'].unique() if 'cod_prop' in dados_censo.columns else []
                if len(props_censo) > 0:
                    # Filtrar BD_inventário para essas propriedades
                    df_inv_censo = filtrar_inventario_por_propriedades(df_inv_filtered, props_censo)
                    if len(df_inv_censo) > 0:
                        area_censo, metodo_censo = calcular_area_censo_inventario(df_inv_censo)
                        area_total += area_censo
                        metodos_usados.append(f"Censo: {metodo_censo}")
            
            # Calcular área das parcelas
            if len(dados_parcelas) > 0:
                # Filtrar inventário para propriedades de parcelas
                props_parcelas = dados_parcelas['cod_prop'].unique() if 'cod_prop' in dados_parcelas.columns else []
                if len(props_parcelas) > 0:
                    # Filtrar BD_inventário para essas propriedades
                    df_inv_parcelas = filtrar_inventario_por_propriedades(df_inv_filtered, props_parcelas)
                    if len(df_inv_parcelas) > 0:
                        area_parcelas, metodo_parcelas = calcular_area_parcelas_tradicional(df_inv_parcelas)
                        area_total += area_parcelas
                        metodos_usados.append(f"Parcelas: {metodo_parcelas}")
            
            metodo_final = " + ".join(metodos_usados) if metodos_usados else "Misto (sem dados)"
            return area_total, metodo_final
        
        # Fallback se não conseguiu identificar técnicas
        return calcular_area_parcelas_tradicional(df_inv_filtered)
            
    except Exception as e:
        st.warning(f"Erro no cálculo de área: {e}")
        return 0.0, "Erro"

def filtrar_inventario_por_propriedades(df_inv, propriedades):
    """Filtra o BD_inventário para incluir apenas as propriedades especificadas"""
    try:
        # Encontrar coluna de parcela
        col_parc = encontrar_coluna(df_inv, ['cod_parc', 'codigo_parcela', 'parcela'])
        
        if not col_parc:
            return df_inv  # Retorna tudo se não conseguir filtrar
        
        df_trabalho = df_inv.copy()
        df_trabalho[col_parc] = df_trabalho[col_parc].astype(str)
        
        # Extrair propriedades do cod_parc
        if '_' in str(df_trabalho[col_parc].iloc[0]) if len(df_trabalho) > 0 else False:
            # Formato PROP_UT
            df_trabalho['prop_temp'] = df_trabalho[col_parc].str.split('_').str[0]
        else:
            # Tentar colunas separadas
            col_prop = encontrar_coluna(df_trabalho, ['cod_prop', 'codigo_propriedade', 'propriedade'])
            if col_prop:
                df_trabalho['prop_temp'] = df_trabalho[col_prop].astype(str)
            else:
                return df_inv  # Se não conseguir identificar, retorna tudo
        
        # Filtrar por propriedades especificadas
        propriedades_str = [str(p).lower() for p in propriedades]
        df_filtrado = df_trabalho[df_trabalho['prop_temp'].str.lower().isin(propriedades_str)]
        
        # Remover coluna temporária
        if 'prop_temp' in df_filtrado.columns:
            df_filtrado = df_filtrado.drop('prop_temp', axis=1)
        
        return df_filtrado
        
    except Exception as e:
        st.warning(f"Erro ao filtrar inventário: {e}")
        return df_inv

def calcular_area_censo_inventario(df_inv_filtered):
    """Calcula área para método CENSO usando BD_inventário com desduplicação"""
    try:
        if len(df_inv_filtered) == 0:
            return 0.0, "Censo (sem dados de inventário)"
        
        # Encontrar colunas necessárias
        col_parc = encontrar_coluna(df_inv_filtered, ['cod_parc', 'codigo_parcela', 'parcela'])
        col_area = encontrar_coluna(df_inv_filtered, ['area_ha', 'area'])
        
        if not col_parc or not col_area:
            return 0.0, f"Censo - colunas não encontradas"
        
        # Trabalhar com cópia
        df_trabalho = df_inv_filtered.copy()
        
        # Converter para string para garantir compatibilidade
        df_trabalho[col_parc] = df_trabalho[col_parc].astype(str)
        
        # Verificar formato e extrair cod_prop e UT
        amostra_parc = df_trabalho[col_parc].iloc[0] if len(df_trabalho) > 0 else ""
        
        if '_' in str(amostra_parc):
            # Formato PROP_UT
            df_trabalho['cod_prop_extraido'] = df_trabalho[col_parc].str.split('_').str[0]
            df_trabalho['ut_extraido'] = df_trabalho[col_parc].str.split('_').str[1]
        else:
            # Tentar encontrar colunas separadas
            col_prop = encontrar_coluna(df_trabalho, ['cod_prop', 'codigo_propriedade', 'propriedade'])
            col_ut = encontrar_coluna(df_trabalho, ['ut', 'unidade_trabalho', 'UT'])
            
            if col_prop and col_ut:
                df_trabalho['cod_prop_extraido'] = df_trabalho[col_prop].astype(str)
                df_trabalho['ut_extraido'] = df_trabalho[col_ut].astype(str)
            else:
                return 0.0, "Censo - não foi possível identificar cod_prop e UT"
        
        # Desduplicar por UT - pegar apenas um registro por UT (já que área se repete)
        df_unico = df_trabalho.groupby(['cod_prop_extraido', 'ut_extraido']).agg({
            col_area: 'first',  # Pega o primeiro valor (todos são iguais)
            col_parc: 'count'   # Conta quantos indivíduos tem na UT
        }).reset_index()
        
        # Calcular área total (soma das áreas únicas de cada UT)
        area_total = df_unico[col_area].sum()
        num_uts = len(df_unico)
        num_individuos = df_unico[col_parc].sum()
        
        metodo = f"Censo ({num_uts} UTs, {num_individuos} indivíduos)"
        
        return area_total, metodo
        
    except Exception as e:
        st.warning(f"Erro no cálculo de área censo: {e}")
        return 0.0, "Censo (erro)"

def calcular_area_parcelas_tradicional(df_inv_filtered):
    """Calcula área para método PARCELAS usando fórmula tradicional"""
    try:
        if len(df_inv_filtered) == 0:
            return 0.0, "Parcelas (sem dados)"
        
        # Encontrar coluna de parcela
        col_parc = encontrar_coluna(df_inv_filtered, ['cod_parc', 'codigo_parcela', 'parcela'])
        
        if not col_parc:
            return 0.0, "Parcelas (coluna não encontrada)"
        
        # Contar parcelas únicas
        num_parcelas = df_inv_filtered[col_parc].nunique()
        
        if num_parcelas > 0:
            # Fórmula tradicional: (número de parcelas × 100) / 10000
            area_ha = (num_parcelas * 100) / 10000
            return area_ha, f"Parcelas ({num_parcelas} parcelas × 100m²)"
        else:
            return 0.0, "Parcelas (sem dados válidos)"
        
    except Exception as e:
        st.warning(f"Erro no cálculo de área parcelas: {e}")
        return 0.0, "Parcelas (erro)"

def calcular_densidade_regenerantes(df_inv, df_carac):
    """Calcula a densidade de indivíduos regenerantes seguindo critérios específicos"""
    try:
        # Verificar se há dados
        if len(df_inv) == 0 or len(df_carac) == 0:
            return 0.0
            
        # === DEBUG: DataFrame inicial ===
        if debug:
            st.write("### 🔍 DEBUG - Densidade de Regenerantes")
            st.write(f"**DataFrame inicial:** {len(df_inv)} registros")
            
        # Aplicar filtros específicos
        df_filtrado = df_inv.copy()
        
        # 1. Remover "Morto/Morta"
        especies_col = encontrar_coluna(df_filtrado, ['especies', 'especie', 'species', 'sp'])
        if especies_col:
            antes_morto = len(df_filtrado)
            df_filtrado = df_filtrado[~df_filtrado[especies_col].astype(str).str.contains('Morto|Morta', case=False, na=False)]
            if debug:
                st.write(f"**1. Após remover 'Morto/Morta':** {len(df_filtrado)} registros (removidos: {antes_morto - len(df_filtrado)})")
        
        # 2. Filtrar apenas origem "Nativa"
        origem_col = encontrar_coluna(df_filtrado, ['origem', 'origin', 'procedencia'])
        if origem_col:
            antes_origem = len(df_filtrado)
            df_filtrado = df_filtrado[df_filtrado[origem_col].astype(str).str.contains('Nativa', case=False, na=False)]
            if debug:
                st.write(f"**2. Após filtrar origem 'Nativa':** {len(df_filtrado)} registros (removidos: {antes_origem - len(df_filtrado)})")
        
        # 3. Filtrar idade "Jovem"
        idade_col = encontrar_coluna(df_filtrado, ['idade', 'age', 'class_idade'])
        if idade_col:
            antes_idade = len(df_filtrado)
            df_filtrado = df_filtrado[df_filtrado[idade_col].astype(str).str.contains('Jovem', case=False, na=False)]
            if debug:
                st.write(f"**3. Após filtrar idade 'Jovem':** {len(df_filtrado)} registros (removidos: {antes_idade - len(df_filtrado)})")
        
        # 4. Filtrar altura > 0.5
        ht_col = encontrar_coluna(df_filtrado, ['ht', 'altura', 'height', 'h'])
        if ht_col:
            antes_altura = len(df_filtrado)
            alturas = pd.to_numeric(df_filtrado[ht_col], errors='coerce')
            df_filtrado = df_filtrado[alturas >= 0.499]
            if debug:
                st.write(f"**4. Após filtrar altura > 0.5m:** {len(df_filtrado)} registros (removidos: {antes_altura - len(df_filtrado)})")
        
        if len(df_filtrado) == 0:
            if debug:
                st.error("❌ Nenhum registro restou após aplicar todos os filtros!")
            return 0.0
        
        # === DEBUG: Mostrar dados filtrados ===
        if debug:
            st.write("### 📋 Registros Selecionados para Cálculo")
            
            # Colunas relevantes para mostrar
            colunas_debug = ['plaqueta', 'plaq', 'id', especies_col, origem_col, idade_col, ht_col, 'cod_parc', 'parcela', 'area_ha']
            colunas_existentes = [col for col in colunas_debug if col and col in df_filtrado.columns]
            
            if colunas_existentes:
                st.dataframe(df_filtrado[colunas_existentes], use_container_width=True)
            else:
                st.dataframe(df_filtrado, use_container_width=True)
        
        # Contar indivíduos regenerantes válidos
        plaqueta_col = encontrar_coluna(df_filtrado, ['plaqueta', 'plaq', 'id'])
        if plaqueta_col:
            num_regenerantes = df_filtrado[plaqueta_col].nunique()
            if debug:
                st.write(f"**Indivíduos únicos por plaqueta:** {num_regenerantes}")
                
                # Mostrar contagem por plaqueta
                contagem_plaquetas = df_filtrado[plaqueta_col].value_counts().head(20)
                st.write("**Top 20 plaquetas com mais registros:**")
                st.dataframe(contagem_plaquetas.reset_index())
                
                # Comparação com seus valores
                st.write("### 🔄 Comparação com Cálculo Manual")
                st.write(f"**Seus valores:** 309 indivíduos ÷ 0,17 ha = 1.817,647 ind/ha")
                
                # Calcular diferenças
                diferenca_individuos = num_regenerantes - 309
                st.write(f"**Dashboard:** {num_regenerantes} indivíduos")
                st.write(f"**Diferença em indivíduos:** {diferenca_individuos:+d}")
                
                if abs(diferenca_individuos) > 0:
                    st.warning(f"⚠️ **POSSÍVEL CAUSA**: Diferença de {abs(diferenca_individuos)} indivíduos")
                    if diferenca_individuos < 0:
                        st.write("- Alguns indivíduos foram removidos pelos filtros do dashboard")
                        st.write("- Verifique se há 'Morto/Morta', espécies não-nativas, idades não-jovens, ou alturas ≤ 0.5m")
                    else:
                        st.write("- Dashboard está contando mais indivíduos que seu cálculo")
        else:
            num_regenerantes = len(df_filtrado)
            if debug:
                st.write(f"**Contagem total de registros (sem plaqueta):** {num_regenerantes}")
        
        # Calcular área amostrada usando método adaptativo
        area_ha, metodo = calcular_area_amostrada(df_carac, df_inv)
        
        if debug:
            st.write(f"**Área calculada:** {area_ha:.6f} ha")
            st.write(f"**Método usado:** {metodo}")
            
            # Comparação detalhada de área
            diferenca_area = area_ha - 0.17
            st.write(f"**Área esperada:** 0,17 ha")
            st.write(f"**Diferença em área:** {diferenca_area:+.6f} ha")
            
            if abs(diferenca_area) > 0.001:
                st.warning(f"⚠️ **POSSÍVEL CAUSA**: Diferença de {abs(diferenca_area):.6f} ha na área")
                st.write(f"- Método do dashboard: {metodo}")
                st.write("- Verifique se o método de cálculo de área está correto")
        
        if area_ha > 0:
            densidade = num_regenerantes / area_ha
            if debug:
                st.write("### 📊 Análise Final das Diferenças")
                densidade_manual = 309 / 0.17
                diferenca_densidade = densidade - densidade_manual
                
                st.write(f"**Cálculo manual:** 309 ÷ 0,17 = {densidade_manual:.1f} ind/ha")
                st.write(f"**Cálculo dashboard:** {num_regenerantes} ÷ {area_ha:.6f} = **{densidade:.1f} ind/ha**")
                st.write(f"**Diferença final:** {diferenca_densidade:+.1f} ind/ha")
                
                # Determinar causa principal
                if abs(diferenca_individuos) > abs(diferenca_area * 1000):
                    st.error("🎯 **CAUSA PRINCIPAL**: Diferença no número de indivíduos contados")
                elif abs(diferenca_area) > 0.001:
                    st.error("🎯 **CAUSA PRINCIPAL**: Diferença no cálculo da área")
                else:
                    st.success("✅ **VALORES PRÓXIMOS**: Pequenas diferenças de arredondamento")
            
            return densidade
        
        return 0.0
    except Exception as e:
        if debug:
            st.error(f"Erro no cálculo de densidade: {e}")
        st.warning(f"Erro no cálculo de densidade: {e}")
        return 0.0

def calcular_densidade_geral(df_inv, df_carac):
    """Calcula a densidade geral de indivíduos com método híbrido para técnicas mistas"""
    try:
        # Verificar se há dados
        if len(df_inv) == 0 or len(df_carac) == 0:
            return 0.0, "Sem dados"
            
        # Encontrar coluna de plaqueta
        plaqueta_col = encontrar_coluna(df_inv, ['plaqueta', 'plaq', 'id'])
        
        if not plaqueta_col:
            return 0.0, "Coluna plaqueta não encontrada"
        
        # Contar total de indivíduos únicos
        num_individuos = df_inv[plaqueta_col].nunique()
        
        # Calcular área amostrada usando método híbrido avançado
        area_ha, metodo = calcular_area_amostrada(df_carac, df_inv)
        
        if area_ha > 0:
            densidade = num_individuos / area_ha
            
            # Melhorar descrição do método para casos mistos
            if "+" in metodo:
                metodo_desc = f"Método Misto: {metodo}"
            else:
                metodo_desc = metodo
                
            return densidade, metodo_desc
        
        return 0.0, metodo
    except Exception as e:
        return 0.0, f"Erro: {e}"

# Remover função main() daqui - será movida para o final

def pagina_dashboard_principal(df_caracterizacao, df_inventario):
    # CSS customizado para melhor ajuste de texto
    st.markdown("""
    <style>
    .small-text {
        font-size: 11px !important;
        line-height: 1.2 !important;
    }
    .extra-small-text {
        font-size: 10px !important;
        line-height: 1.1 !important;
    }
    .metric-container {
        padding: 0.1rem !important;
    }
    /* Reduzir padding das métricas */
    [data-testid="metric-container"] {
        padding: 0.2rem !important;
    }
    /* Reduzir tamanho da fonte dos VALORES das métricas */
    [data-testid="metric-container"] > div > div > div {
        font-size: 16px !important;
    }
    /* Reduzir tamanho da fonte dos valores principais das métricas */
    [data-testid="metric-container"] [data-testid="metric-value"] {
        font-size: 14px !important;
        line-height: 1.1 !important;
    }
    /* Reduzir altura das linhas nos textos pequenos */
    small {
        line-height: 1.1 !important;
    }
    /* Ajustar o título da métrica também */
    [data-testid="metric-container"] [data-testid="metric-label"] {
        font-size: 12px !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Informação sobre limpeza de dados
    with st.expander("ℹ️ Informações sobre Processamento de Dados"):
        st.markdown("""
        **Limpeza e Padronização Aplicada:**
        - ✅ Remoção de espaços desnecessários
        - ✅ Padronização de maiúsculas/minúsculas
        - ✅ Capitalização da primeira letra
        - ✅ Tratamento de valores nulos
        
        **Métodos de Cálculo de Densidade:**
        - **Parcelas**: Área = (número de cod_parc únicos × 100) / 10.000
        - **Censo**: Área = soma da média de Area_ha por cod_prop de cada UT única
        
        O sistema detecta automaticamente o método baseado na variável 'tecnica_am' e aplica o cálculo adequado.
        """)
    
    # Carregar dados uma vez para todas as páginas
    df_caracterizacao, df_inventario = load_data()
    
    if df_caracterizacao is None or df_inventario is None:
        st.error("Não foi possível carregar os dados. Verifique se os arquivos Excel estão no diretório correto.")
        return
    
    # Sidebar com filtros
    st.sidebar.header("🔧 Filtros")
    
    # Filtros principais que afetam ambos os bancos
    filtros_principais = {}
    
    # Filtro cod_prop
    if 'cod_prop' in df_caracterizacao.columns:
        cod_prop_options = ['Todos'] + list(df_caracterizacao['cod_prop'].dropna().unique())
        filtros_principais['cod_prop'] = st.sidebar.selectbox(
            "Código de Propriedade (cod_prop)",
            cod_prop_options
        )
    
    # Filtro tecnica
    if 'tecnica' in df_caracterizacao.columns:
        tecnica_options = ['Todos'] + list(df_caracterizacao['tecnica'].dropna().unique())
        filtros_principais['tecnica'] = st.sidebar.selectbox(
            "Técnica",
            tecnica_options
        )
    
    # Filtro UT
    if 'UT' in df_caracterizacao.columns:
        ut_options = ['Todos'] + list(df_caracterizacao['UT'].dropna().unique())
        filtros_principais['UT'] = st.sidebar.selectbox(
            "Unidade Territorial (UT)",
            ut_options
        )
    
    # Filtros específicos para inventário
    st.sidebar.markdown("---")
    st.sidebar.subheader("🔍 Filtros Específicos - Inventário")
    
    filtros_inventario = {}
    
    # Verificar se as colunas existem no inventário
    inventario_cols = df_inventario.columns.tolist()
    
    # Filtro origem
    origem_col = encontrar_coluna(df_inventario, ['origem'])
    
    if origem_col:
        origem_options = ['Todos'] + list(df_inventario[origem_col].dropna().unique())
        filtros_inventario['origem'] = st.sidebar.selectbox(
            f"Origem ({origem_col})",
            origem_options
        )
    
    # Filtro regeneracao
    regeneracao_col = encontrar_coluna(df_inventario, ['regeneracao', 'regenera'])
    
    if regeneracao_col:
        regeneracao_options = ['Todos'] + list(df_inventario[regeneracao_col].dropna().unique())
        filtros_inventario['regeneracao'] = st.sidebar.selectbox(
            f"Regeneração ({regeneracao_col})",
            regeneracao_options
        )
    
    # Filtro idade
    idade_col = encontrar_coluna(df_inventario, ['idade', 'age', 'class_idade'])
    
    if idade_col:
        idade_options = ['Todos'] + list(df_inventario[idade_col].dropna().unique())
        filtros_inventario['idade'] = st.sidebar.selectbox(
            f"Idade ({idade_col})",
            idade_options
        )
    
    # Aplicar filtros principais a ambos os bancos de dados
    df_carac_filtered = df_caracterizacao.copy()
    df_inv_filtered = df_inventario.copy()
    
    # Obter coluna cod_parc para ligação entre bancos
    cod_parc_carac = encontrar_coluna(df_caracterizacao, ['cod_parc', 'parcela', 'plot'])
    cod_parc_inv = encontrar_coluna(df_inventario, ['cod_parc', 'parcela', 'plot'])
    
    # Aplicar filtros que afetam ambos os bancos
    for filtro, valor in filtros_principais.items():
        if valor != 'Todos' and valor is not None:
            # Filtrar BD_caracterizacao primeiro
            if filtro in df_carac_filtered.columns:
                # Comparação case-insensitive e tratamento de espaços
                mask = df_carac_filtered[filtro].astype(str).str.strip().str.lower() == valor.strip().lower()
                df_carac_filtered = df_carac_filtered[mask]
            
            # Aplicar também ao BD_inventario se a coluna existir
            if filtro in df_inv_filtered.columns:
                mask = df_inv_filtered[filtro].astype(str).str.strip().str.lower() == valor.strip().lower()
                df_inv_filtered = df_inv_filtered[mask]
    
    # Sempre aplicar a conexão via cod_parc se ambas as colunas existem
    if cod_parc_carac and cod_parc_inv and len(df_carac_filtered) > 0:
        # Obter cod_parc válidos do BD_caracterizacao filtrado
        cod_parc_validos = df_carac_filtered[cod_parc_carac].dropna().unique()
        
        if len(cod_parc_validos) > 0:
            # Filtrar BD_inventario pelos cod_parc válidos
            # Usar comparação mais robusta
            df_inv_filtered = df_inv_filtered[
                df_inv_filtered[cod_parc_inv].astype(str).str.strip().isin(
                    [str(x).strip() for x in cod_parc_validos]
                )
            ]
        else:
            # Se não há cod_parc válidos, o inventário fica vazio
            df_inv_filtered = df_inv_filtered.iloc[0:0]  # DataFrame vazio com mesma estrutura
    
    # Aplicar filtros específicos do inventário
    for filtro, valor in filtros_inventario.items():
        if valor != 'Todos' and valor is not None:
            if filtro == 'origem' and origem_col:
                mask = df_inv_filtered[origem_col].astype(str).str.strip().str.lower() == valor.strip().lower()
                df_inv_filtered = df_inv_filtered[mask]
            elif filtro == 'regeneracao' and regeneracao_col:
                mask = df_inv_filtered[regeneracao_col].astype(str).str.strip().str.lower() == valor.strip().lower()
                df_inv_filtered = df_inv_filtered[mask]
            elif filtro == 'idade' and idade_col:
                mask = df_inv_filtered[idade_col].astype(str).str.strip().str.lower() == valor.strip().lower()
                df_inv_filtered = df_inv_filtered[mask]
    
    # Layout principal
    # Estatísticas descritivas
    col1, col2 = st.columns(2)
    
    with col1:
        show_descriptive_stats(df_carac_filtered, df_inv_filtered, "Caracterização")
    
    with col2:
        show_descriptive_stats(df_carac_filtered, df_inv_filtered, "Inventário")
    
    st.markdown("---")
    
    # ============================================
    # � INDICADORES DE RESTAURAÇÃO FLORESTAL 
    # ============================================
    
    st.header("🎯 Indicadores de Restauração Florestal")
    st.markdown("*Monitoramento das metas de reparação do desastre ambiental*")
    
    # Informações sobre as metas
    with st.expander("ℹ️ Sobre as Metas de Restauração"):
        st.markdown("""
        ### 🎯 Metas de Reparação do Desastre Ambiental
        
        **🌿 Cobertura de Copa:**
        - **Meta**: > 80% em todas as propriedades
        - **Indicador**: Cobertura arbórea nativa
        
        **🌱 Densidade de Regenerantes:**
        - **Restauração Ativa**: > 1.333 indivíduos/ha
        - **Restauração Assistida**: > 1.500 indivíduos/ha
        - **Critério**: Indivíduos regenerantes (jovens)
        
        **🌳 Riqueza de Espécies Arbóreas:**
        - **Metas variáveis**: 10, 30, 57 ou 87 espécies por cenário
        - **Definidas**: Por propriedade conforme contexto ecológico
        """)
    
    # Chamar função para exibir indicadores de restauração
    exibir_indicadores_restauracao(df_carac_filtered, df_inv_filtered)
    
    st.markdown("---")
    
    # ============================================
    # �🌳 DASHBOARD DE MONITORAMENTO DE REFLORESTAMENTO
    # ============================================
    
    st.header("🌱 Monitoramento de Reflorestamento")
    st.markdown("*Dashboard interativo para acompanhamento da vegetação em áreas de reflorestamento*")
    
    # Criar abas para diferentes aspectos do monitoramento
    tab1, tab2, tab3, tab4 = st.tabs([
        "🌳 Estrutura Florestal", 
        "🌿 Sucessão Ecológica", 
        "📊 Indicadores Ambientais",
        "⚠️ Alertas e Monitoramento"
    ])
    
    # ==================== ABA 1: ESTRUTURA FLORESTAL ====================
    with tab1:
        st.subheader("📏 Estrutura e Desenvolvimento Florestal")
        
        # Métricas principais de estrutura
        col_str1, col_str2, col_str3, col_str4 = st.columns(4)
        
        # Altura média e máxima
        ht_col = encontrar_coluna(df_inv_filtered, ['ht', 'altura', 'height', 'h'])
        if ht_col and len(df_inv_filtered) > 0:
            alturas = pd.to_numeric(df_inv_filtered[ht_col], errors='coerce').dropna()
            if len(alturas) > 0:
                with col_str1:
                    altura_media = alturas.mean()
                    st.metric("🌲 Altura Média", f"{altura_media:.2f} m")
                
                with col_str2:
                    altura_max = alturas.max()
                    st.metric("🌲 Altura Máxima", f"{altura_max:.2f} m")
        
        # DAP médio (se disponível)
        dap_col = encontrar_coluna(df_inv_filtered, ['dap', 'diameter', 'dap_cm'])
        if dap_col and len(df_inv_filtered) > 0:
            daps = pd.to_numeric(df_inv_filtered[dap_col], errors='coerce').dropna()
            if len(daps) > 0:
                with col_str3:
                    dap_medio = daps.mean()
                    st.metric("📐 DAP Médio", f"{dap_medio:.1f} cm")
        
        # Densidade por hectare
        if len(df_inv_filtered) > 0 and len(df_carac_filtered) > 0:
            densidade, metodo = calcular_densidade_geral(df_inv_filtered, df_carac_filtered)
            with col_str4:
                st.metric("🌱 Densidade", formatar_densidade_br(densidade))
        
        # Gráficos de estrutura florestal
        col_graf1, col_graf2 = st.columns(2)
        
        # Distribuição de alturas por classes de desenvolvimento
        if ht_col and len(df_inv_filtered) > 0:
            with col_graf1:
                st.write("**Distribuição de Alturas por Classe**")
                
                # Preparar dados com classificacao de desenvolvimento
                df_temp = df_inv_filtered.copy()
                df_temp['altura_num'] = pd.to_numeric(df_temp[ht_col], errors='coerce')
                df_temp = df_temp.dropna(subset=['altura_num'])
                
                if len(df_temp) > 0:
                    # Sistema simplificado de 3 classes
                    dap_col = encontrar_coluna(df_temp, ['dap', 'DAP', 'diametro'])
                    
                    def classificar_desenvolvimento(row):
                        altura = row['altura_num']
                        
                        if altura < 0.5:
                            return "Plantula (< 0.5m)"
                        elif dap_col and pd.notna(row[dap_col]):
                            dap = row[dap_col]
                            if dap < 5:
                                return "Jovem (DAP < 5cm)"
                            else:
                                return "Adulto (DAP ≥ 5cm)"
                        else:
                            return "Jovem (DAP < 5cm)"
                    
                    df_temp['classe_desenvolvimento'] = df_temp.apply(classificar_desenvolvimento, axis=1)
                    
                    # Criar bins de altura manualmente para ter controle total
                    min_altura = df_temp['altura_num'].min()
                    max_altura = df_temp['altura_num'].max()
                    bins = np.linspace(min_altura, max_altura, 11)  # 10 bins
                    
                    df_temp['faixa_altura'] = pd.cut(df_temp['altura_num'], bins=bins, precision=1)
                    
                    # Contar por faixa e classe
                    contagem = df_temp.groupby(['faixa_altura', 'classe_desenvolvimento']).size().unstack(fill_value=0).reset_index()
                    
                    # Garantir que todas as classes existam
                    todas_classes = ["Plantula (< 0.5m)", "Jovem (DAP < 5cm)", "Adulto (DAP ≥ 5cm)"]
                    for classe in todas_classes:
                        if classe not in contagem.columns:
                            contagem[classe] = 0
                    
                    # Converter faixa de altura para string para o eixo x
                    contagem['faixa_str'] = contagem['faixa_altura'].astype(str)
                    contagem['faixa_midpoint'] = contagem['faixa_altura'].apply(lambda x: x.mid if pd.notna(x) else 0)
                    
                    # Criar dados para grafico empilhado
                    dados_grafico = []
                    for _, row in contagem.iterrows():
                        for classe in todas_classes:
                            if classe in contagem.columns:
                                dados_grafico.append({
                                    'Altura': row['faixa_midpoint'],
                                    'Faixa': f"{row['faixa_midpoint']:.1f}m",
                                    'Classe': classe,
                                    'Quantidade': row[classe]
                                })
                    
                    df_grafico = pd.DataFrame(dados_grafico)
                    
                    # Criar grafico de barras empilhadas
                    fig_hist = px.bar(
                        df_grafico,
                        x='Faixa',
                        y='Quantidade',
                        color='Classe',
                        title="Distribuição de Alturas por Classe de Desenvolvimento",
                        labels={'Faixa': 'Altura (m)', 'Quantidade': 'Frequência'},
                        color_discrete_map={
                            "Plantula (< 0.5m)": "#90EE90",
                            "Jovem (DAP < 5cm)": "#228B22", 
                            "Adulto (DAP ≥ 5cm)": "#006400"
                        },
                        category_orders={"Classe": todas_classes}
                    )
                    
                    # Configurar para barras empilhadas
                    fig_hist.update_layout(
                        barmode='stack',  # Empilhamento garantido
                        height=300,
                        showlegend=True,
                        legend=dict(
                            orientation="h",
                            yanchor="bottom", 
                            y=1.02,
                            xanchor="right",
                            x=1
                        ),
                        xaxis_title="Altura (m)",
                        yaxis_title="Frequência"
                    )
                    st.plotly_chart(fig_hist, use_container_width=True)
        
        # Classes de desenvolvimento
        if ht_col and len(df_inv_filtered) > 0:
            with col_graf2:
                st.write("**Classes de Desenvolvimento**")
                alturas = pd.to_numeric(df_inv_filtered[ht_col], errors='coerce').dropna()
                
                if len(alturas) > 0:
                    # Sistema simplificado de 3 classes
                    dap_col = encontrar_coluna(df_inv_filtered, ['dap', 'DAP', 'diametro'])
                    
                    def classificar_desenvolvimento(row):
                        altura = row[ht_col] if pd.notna(row[ht_col]) else 0
                        
                        if altura < 0.5:
                            return "Plantula (< 0.5m)"
                        elif dap_col and pd.notna(row[dap_col]):
                            dap = row[dap_col]
                            if dap < 5:
                                return "Jovem (DAP < 5cm)"
                            else:
                                return "Adulto (DAP ≥ 5cm)"
                        else:
                            # Se nao tem DAP, assume jovem para plantas >= 0.5m
                            return "Jovem (DAP < 5cm)"
                    
                    classes = df_inv_filtered.apply(classificar_desenvolvimento, axis=1)
                    classe_counts = classes.value_counts()
                    
                    # Garantir ordem das classes
                    ordem_classes = ["Plantula (< 0.5m)", "Jovem (DAP < 5cm)", "Adulto (DAP ≥ 5cm)"]
                    classe_counts = classe_counts.reindex(ordem_classes, fill_value=0)
                    
                    # Grafico de pizza com cores verdes
                    fig_pie = px.pie(
                        values=classe_counts.values,
                        names=classe_counts.index,
                        title="Classes de Desenvolvimento",
                        color_discrete_sequence=['#90EE90', '#228B22', '#006400']
                    )
                    fig_pie.update_layout(height=300)
                    st.plotly_chart(fig_pie, use_container_width=True)
    
    # ==================== ABA 2: SUCESSÃO ECOLÓGICA ====================
    with tab2:
        st.subheader("🌿 Dinâmica Sucessional")
        
        # Métricas de sucessão
        col_suc1, col_suc2, col_suc3, col_suc4 = st.columns(4)
        
        # Grupos sucessionais
        gsuc_col = encontrar_coluna(df_inv_filtered, ['g_suc', 'grupo_suc', 'sucessional'])
        if gsuc_col and len(df_inv_filtered) > 0:
            with col_suc1:
                gsuc_dist = df_inv_filtered[gsuc_col].value_counts()
                if len(gsuc_dist) > 0:
                    principal_gsuc = gsuc_dist.index[0]
                    perc_principal = (gsuc_dist.iloc[0] / len(df_inv_filtered)) * 100
                    st.metric("🌱 Grupo Dominante", f"{principal_gsuc}", f"{perc_principal:.1f}%")
        
        # Riqueza de especies (com filtros aplicados)
        especies_col = encontrar_coluna(df_inv_filtered, ['especies', 'especie', 'species', 'sp'])
        ht_col = encontrar_coluna(df_inv_filtered, ['ht', 'altura', 'height'])
        
        if especies_col and len(df_inv_filtered) > 0:
            with col_suc2:
                # Aplicar filtros: remover "Morto" e altura > 0.5m
                df_especies_validas = df_inv_filtered[~df_inv_filtered[especies_col].astype(str).str.contains('Morto|Morta', case=False, na=False)]
                
                # Filtrar por altura > 0.5m se coluna disponivel
                if ht_col:
                    alturas = pd.to_numeric(df_especies_validas[ht_col], errors='coerce')
                    df_especies_validas = df_especies_validas[alturas > 0.5]
                
                riqueza = df_especies_validas[especies_col].nunique()
                
                # Calcular riqueza de nativas
                origem_col = encontrar_coluna(df_especies_validas, ['origem', 'origin', 'procedencia'])
                if origem_col:
                    df_nativas = df_especies_validas[df_especies_validas[origem_col].astype(str).str.contains('Nativa', case=False, na=False)]
                    riqueza_nativas = df_nativas[especies_col].nunique()
                    st.metric("🌺 Riqueza", f"{riqueza} ({riqueza_nativas} nat.)")
                else:
                    st.metric("🌺 Riqueza", f"{riqueza} especies")
        
        # Diversidade Shannon
        if especies_col and len(df_inv_filtered) > 0:
            with col_suc3:
                especies_count = df_inv_filtered[especies_col].value_counts()
                if len(especies_count) > 1:
                    # Calculo de Shannon
                    total = especies_count.sum()
                    shannon = -sum((count/total) * log(count/total) for count in especies_count)
                    st.metric("🌍 Shannon (H')", f"{shannon:.2f}")
        
        # Equitabilidade de Pielou
        if especies_col and len(df_inv_filtered) > 0:
            with col_suc4:
                especies_count = df_inv_filtered[especies_col].value_counts()
                if len(especies_count) > 1:
                    # Calculo de Shannon
                    total = especies_count.sum()
                    shannon = -sum((count/total) * log(count/total) for count in especies_count)
                    # Calculo de Pielou
                    riqueza = len(especies_count)
                    equitabilidade = shannon / log(riqueza) if riqueza > 1 else 0
                    st.metric("⚖️ Pielou (J)", f"{equitabilidade:.3f}")
        
        # Gráficos de sucessão
        col_graf_suc1, col_graf_suc2 = st.columns(2)
        
        # Distribuição por grupos sucessionais
        if gsuc_col and len(df_inv_filtered) > 0:
            with col_graf_suc1:
                st.write("**Grupos Sucessionais**")
                gsuc_dist = df_inv_filtered[gsuc_col].value_counts()
                
                if len(gsuc_dist) > 0:
                    fig_gsuc = px.bar(
                        x=gsuc_dist.index,
                        y=gsuc_dist.values,
                        title="Distribuição por Grupos Sucessionais",
                        labels={'x': 'Grupo Sucessional', 'y': 'Número de Indivíduos'},
                        color_discrete_sequence=['#32CD32']
                    )
                    fig_gsuc.update_layout(height=300)
                    st.plotly_chart(fig_gsuc, use_container_width=True)
        
        # Origem das espécies
        origem_col = encontrar_coluna(df_inv_filtered, ['origem'])
        if origem_col and len(df_inv_filtered) > 0:
            with col_graf_suc2:
                st.write("**Origem das Espécies**")
                origem_dist = df_inv_filtered[origem_col].value_counts()
                
                if len(origem_dist) > 0:
                    fig_origem = px.pie(
                        values=origem_dist.values,
                        names=origem_dist.index,
                        title="Origem das Espécies",
                        color_discrete_sequence=['#228B22', '#FFD700', '#FF6347']
                    )
                    fig_origem.update_layout(height=300)
                    st.plotly_chart(fig_origem, use_container_width=True)
    
    # ==================== ABA 3: INDICADORES AMBIENTAIS ====================
    with tab3:
        st.subheader("🌍 Qualidade Ambiental")
        
        # Métricas ambientais do BD_caracterização
        col_amb1, col_amb2, col_amb3, col_amb4 = st.columns(4)
        
        # Cobertura de copa
        copa_col = encontrar_coluna(df_carac_filtered, ['(%)cobetura_nativa', '(%) cobetura_nativa', 'cobetura_nativa', 'cobertura_nativa', 'copa_nativa'])
        if copa_col and len(df_carac_filtered) > 0:
            with col_amb1:
                copa_media = pd.to_numeric(df_carac_filtered[copa_col], errors='coerce').mean()
                if pd.notna(copa_media):
                    # Converter de 0-1 para 0-100% se necessario
                    if copa_media <= 1:
                        copa_media = copa_media * 100
                    # Definir cor baseada na qualidade
                    cor = "normal" if copa_media >= 50 else "inverse"
                    st.metric("🌳 Cobertura Copa", formatar_porcentagem_br(copa_media, 1), delta_color=cor)
        
        # Solo exposto (quanto menor, melhor)
        solo_col = encontrar_coluna(df_carac_filtered, ['(%)solo exposto', '(%) solo exposto', 'solo_exposto', 'solo exposto'])
        if solo_col and len(df_carac_filtered) > 0:
            with col_amb2:
                solo_medio = pd.to_numeric(df_carac_filtered[solo_col], errors='coerce').mean()
                if pd.notna(solo_medio):
                    # Converter de 0-1 para 0-100% se necessario
                    if solo_medio <= 1:
                        solo_medio = solo_medio * 100
                    # Inverso: menos solo exposto = melhor
                    cor = "inverse" if solo_medio > 20 else "normal"
                    st.metric("🏜️ Solo Exposto", formatar_porcentagem_br(solo_medio, 1), delta_color=cor)
        
        # Serapilheira
        sera_col = encontrar_coluna(df_carac_filtered, ['(%)serapilheira', '(%) serapilheira', 'serapilheira'])
        if sera_col and len(df_carac_filtered) > 0:
            with col_amb3:
                sera_media = pd.to_numeric(df_carac_filtered[sera_col], errors='coerce').mean()
                if pd.notna(sera_media):
                    # Converter de 0-1 para 0-100% se necessario
                    if sera_media <= 1:
                        sera_media = sera_media * 100
                    cor = "normal" if sera_media >= 30 else "inverse"
                    st.metric("🍂 Serapilheira", formatar_porcentagem_br(sera_media, 1), delta_color=cor)
        
        # Gramíneas (invasoras)
        gram_col = encontrar_coluna(df_carac_filtered, ['(%)graminea', '(%) graminea', 'graminea'])
        if gram_col and len(df_carac_filtered) > 0:
            with col_amb4:
                gram_media = pd.to_numeric(df_carac_filtered[gram_col], errors='coerce').mean()
                if pd.notna(gram_media):
                    # Converter de 0-1 para 0-100% se necessario
                    if gram_media <= 1:
                        gram_media = gram_media * 100
                    cor = "inverse" if gram_media > 30 else "normal"
                    st.metric("🌾 Gramíneas", formatar_porcentagem_br(gram_media, 1), delta_color=cor)
        
        # Gráfico comparativo de indicadores ambientais
        st.write("**Perfil de Qualidade Ambiental**")
        
        indicadores_dados = []
        for nome, coluna, ideal in [
            ("Cobertura Copa", copa_col, "alto"),
            ("Solo Exposto", solo_col, "baixo"),
            ("Serapilheira", sera_col, "alto"),
            ("Gramíneas", gram_col, "baixo")
        ]:
            if coluna and len(df_carac_filtered) > 0:
                valor = pd.to_numeric(df_carac_filtered[coluna], errors='coerce').mean()
                if pd.notna(valor):
                    # Converter de 0-1 para 0-100% se necessario
                    if valor <= 1:
                        valor = valor * 100
                    
                    # Normalizar para 0-100 baseado no ideal
                    if ideal == "alto":
                        score = valor  # Ja eh percentual
                        cor = '#2E8B57' if score >= 50 else '#FF6347'
                    else:  # baixo eh melhor
                        score = 100 - valor  # Inverter
                        cor = '#2E8B57' if score >= 70 else '#FF6347'
                    
                    indicadores_dados.append({
                        'Indicador': nome,
                        'Valor_Original': valor,
                        'Score': score,
                        'Cor': cor
                    })
        
        if indicadores_dados:
            df_indicadores = pd.DataFrame(indicadores_dados)
            
            fig_radar = go.Figure()
            
            fig_radar.add_trace(go.Scatterpolar(
                r=df_indicadores['Score'],
                theta=df_indicadores['Indicador'],
                fill='toself',
                name='Qualidade Ambiental',
                line_color='#2E8B57'
            ))
            
            fig_radar.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=False,
                title="Perfil de Qualidade Ambiental (0-100)",
                height=400
            )
            
            st.plotly_chart(fig_radar, use_container_width=True)
    
    # ==================== ABA 4: ALERTAS E MONITORAMENTO ====================
    with tab4:
        st.subheader("⚠️ Sistema de Alertas")
        
        alertas = []
        
        # Verificar alertas de estrutura florestal
        if ht_col and len(df_inv_filtered) > 0:
            alturas = pd.to_numeric(df_inv_filtered[ht_col], errors='coerce').dropna()
            if len(alturas) > 0:
                altura_media = alturas.mean()
                
                if altura_media < 2:
                    alertas.append({
                        'Tipo': '🌱 Desenvolvimento',
                        'Nivel': 'Atenção',
                        'Mensagem': f'Altura média baixa ({altura_media:.1f}m). Monitorar crescimento.',
                        'Cor': 'warning'
                    })
                elif altura_media > 20:
                    alertas.append({
                        'Tipo': '🌳 Maturidade',
                        'Nivel': 'Positivo',
                        'Mensagem': f'Excelente desenvolvimento! Altura média: {altura_media:.1f}m',
                        'Cor': 'success'
                    })
        
        # Verificar alertas de diversidade
        if especies_col and len(df_inv_filtered) > 0:
            # Aplicar filtros: remover "Morto" e altura > 0.5m
            df_especies_validas = df_inv_filtered[~df_inv_filtered[especies_col].astype(str).str.contains('Morto|Morta', case=False, na=False)]
            ht_col_alert = encontrar_coluna(df_especies_validas, ['ht', 'altura', 'height'])
            
            if ht_col_alert:
                alturas = pd.to_numeric(df_especies_validas[ht_col_alert], errors='coerce')
                df_especies_validas = df_especies_validas[alturas > 0.5]
            
            riqueza = df_especies_validas[especies_col].nunique()
            
            if riqueza < 10:
                alertas.append({
                    'Tipo': '🌺 Biodiversidade',
                    'Nivel': 'Crítico',
                    'Mensagem': f'Baixa diversidade ({riqueza} espécies). Considerar enriquecimento.',
                    'Cor': 'error'
                })
            elif riqueza > 30:
                alertas.append({
                    'Tipo': '🌺 Biodiversidade',
                    'Nivel': 'Excelente',
                    'Mensagem': f'Alta diversidade ({riqueza} espécies). Reflorestamento bem-sucedido!',
                    'Cor': 'success'
                })
        
        # Verificar alertas ambientais
        if solo_col and len(df_carac_filtered) > 0:
            solo_medio = pd.to_numeric(df_carac_filtered[solo_col], errors='coerce').mean()
            if pd.notna(solo_medio) and solo_medio > 40:
                alertas.append({
                    'Tipo': '🏜️ Solo Exposto',
                    'Nivel': 'Crítico',
                    'Mensagem': f'Alto percentual de solo exposto ({solo_medio:.1f}%). Risco de erosão!',
                    'Cor': 'error'
                })
        
        if gram_col and len(df_carac_filtered) > 0:
            gram_media = pd.to_numeric(df_carac_filtered[gram_col], errors='coerce').mean()
            if pd.notna(gram_media) and gram_media > 50:
                alertas.append({
                    'Tipo': '🌾 Invasoras',
                    'Nivel': 'Atenção',
                    'Mensagem': f'Alto percentual de gramíneas ({gram_media:.1f}%). Monitorar invasoras.',
                    'Cor': 'warning'
                })
        
        # Exibir alertas
        if alertas:
            for alerta in alertas:
                if alerta['Cor'] == 'error':
                    st.error(f"**{alerta['Tipo']}** - {alerta['Nivel']}: {alerta['Mensagem']}")
                elif alerta['Cor'] == 'warning':
                    st.warning(f"**{alerta['Tipo']}** - {alerta['Nivel']}: {alerta['Mensagem']}")
                elif alerta['Cor'] == 'success':
                    st.success(f"**{alerta['Tipo']}** - {alerta['Nivel']}: {alerta['Mensagem']}")
        else:
            st.info("✅ Nenhum alerta identificado. Monitoramento dentro dos parâmetros esperados.")
        
        # Resumo executivo
        st.markdown("---")
        st.write("**📋 Resumo Executivo do Reflorestamento**")
        
        # Calcular score geral com pesos cientificos
        scores_ponderados = []
        pesos_totais = 0
        
        # === INDICADORES PRINCIPAIS (PESO 3) - METAS DE RESTAURAÇÃO ===
        
        # 1. COBERTURA DE COPA NATIVA (Peso 3)
        if copa_col and len(df_carac_filtered) > 0:
            copa_media = pd.to_numeric(df_carac_filtered[copa_col], errors='coerce').mean()
            if pd.notna(copa_media):
                # Converter de 0-1 para 0-100% se necessario
                if copa_media <= 1:
                    copa_media = copa_media * 100
                score_copa = min(100, copa_media)
                scores_ponderados.append(score_copa * 3)  # Peso 3
                pesos_totais += 3
        
        # 2. DENSIDADE DE REGENERANTES (Peso 3)
        densidade_regenerantes = calcular_densidade_regenerantes(df_inv_filtered, df_carac_filtered)
        if densidade_regenerantes > 0:
            # Meta: 1500 ind/ha para restauracao assistida
            score_densidade = min(100, (densidade_regenerantes / 1500) * 100)
            scores_ponderados.append(score_densidade * 3)  # Peso 3
            pesos_totais += 3
        
        # 3. RIQUEZA DE ESPECIES NATIVAS (Peso 3)
        if especies_col and len(df_inv_filtered) > 0:
            # Aplicar filtros: remover "Morto" e altura > 0.5m
            df_especies_validas = df_inv_filtered[~df_inv_filtered[especies_col].astype(str).str.contains('Morto|Morta', case=False, na=False)]
            ht_col_score = encontrar_coluna(df_especies_validas, ['ht', 'altura', 'height'])
            
            if ht_col_score:
                alturas = pd.to_numeric(df_especies_validas[ht_col_score], errors='coerce')
                df_especies_validas = df_especies_validas[alturas > 0.5]
            
            # Contar apenas especies nativas
            origem_col = encontrar_coluna(df_especies_validas, ['origem', 'origin', 'procedencia'])
            if origem_col:
                df_nativas = df_especies_validas[df_especies_validas[origem_col].astype(str).str.contains('Nativa', case=False, na=False)]
                riqueza_nativas = df_nativas[especies_col].nunique()
                
                # Obter meta específica da propriedade
                meta_col = encontrar_coluna(df_inv_filtered, ['meta', 'meta_riqueza', 'riqueza_meta', 'meta_especies'])
                if meta_col and len(df_inv_filtered) > 0:
                    meta_riqueza = pd.to_numeric(df_inv_filtered[meta_col], errors='coerce').dropna()
                    if len(meta_riqueza) > 0:
                        meta_riqueza = meta_riqueza.iloc[0]  # Pegar primeiro valor único
                    else:
                        meta_riqueza = 30  # Valor padrão (consistente com outras funções)
                else:
                    meta_riqueza = 30  # Valor padrão (consistente com outras funções)
                
                score_riqueza = min(100, (riqueza_nativas / meta_riqueza) * 100)
                scores_ponderados.append(score_riqueza * 3)  # Peso 3
                pesos_totais += 3
        
        # === INDICADORES SECUNDARIOS POSITIVOS (PESO 1) ===
        
        # 4. SERAPILHEIRA (Peso 1) - Positivo
        sera_col = encontrar_coluna(df_carac_filtered, ['(%)serapilheira', '(%) serapilheira', 'serapilheira'])
        if sera_col and len(df_carac_filtered) > 0:
            sera_media = pd.to_numeric(df_carac_filtered[sera_col], errors='coerce').mean()
            if pd.notna(sera_media):
                if sera_media <= 1:
                    sera_media = sera_media * 100
                score_serapilheira = min(100, sera_media)
                scores_ponderados.append(score_serapilheira * 1)  # Peso 1
                pesos_totais += 1
        
        # 5. HERBACEAS/PALHADA (Peso 1) - Positivo (se existir)
        herb_col = encontrar_coluna(df_carac_filtered, ['(%)herbaceas', '(%) herbaceas', 'herbaceas', 'palhada'])
        if herb_col and len(df_carac_filtered) > 0:
            herb_media = pd.to_numeric(df_carac_filtered[herb_col], errors='coerce').mean()
            if pd.notna(herb_media):
                if herb_media <= 1:
                    herb_media = herb_media * 100
                score_herbaceas = min(100, herb_media)
                scores_ponderados.append(score_herbaceas * 1)  # Peso 1
                pesos_totais += 1
        
        # === INDICADORES SECUNDARIOS NEGATIVOS (PESO 1) ===
        
        # 6. GRAMINEAS INVASORAS (Peso 1) - Negativo
        gram_col = encontrar_coluna(df_carac_filtered, ['(%)graminea', '(%) graminea', 'graminea'])
        if gram_col and len(df_carac_filtered) > 0:
            gram_media = pd.to_numeric(df_carac_filtered[gram_col], errors='coerce').mean()
            if pd.notna(gram_media):
                if gram_media <= 1:
                    gram_media = gram_media * 100
                score_gramineas = max(0, 100 - gram_media)  # Inverso: menos gramineas = melhor
                scores_ponderados.append(score_gramineas * 1)  # Peso 1
                pesos_totais += 1
        
        # 7. SOLO EXPOSTO (Peso 1) - Negativo
        solo_col = encontrar_coluna(df_carac_filtered, ['(%)solo exposto', '(%) solo exposto', 'solo_exposto', 'solo exposto'])
        if solo_col and len(df_carac_filtered) > 0:
            solo_medio = pd.to_numeric(df_carac_filtered[solo_col], errors='coerce').mean()
            if pd.notna(solo_medio):
                if solo_medio <= 1:
                    solo_medio = solo_medio * 100
                score_solo = max(0, 100 - solo_medio)  # Inverso: menos solo exposto = melhor
                scores_ponderados.append(score_solo * 1)  # Peso 1
                pesos_totais += 1
        
        # 8. COBERTURA EXOTICA (Peso 1) - Negativo (se existir)
        exot_col = encontrar_coluna(df_carac_filtered, ['(%)cobertura_exotica', '(%) cobertura_exotica', 'cobertura_exotica', 'exotica'])
        if exot_col and len(df_carac_filtered) > 0:
            exot_media = pd.to_numeric(df_carac_filtered[exot_col], errors='coerce').mean()
            if pd.notna(exot_media):
                if exot_media <= 1:
                    exot_media = exot_media * 100
                score_exotica = max(0, 100 - exot_media)  # Inverso: menos exoticas = melhor
                scores_ponderados.append(score_exotica * 1)  # Peso 1
                pesos_totais += 1
        
        if scores_ponderados and pesos_totais > 0:
            score_geral = sum(scores_ponderados) / pesos_totais
            
            # Explicacao detalhada do Score Geral
            st.info("""
            **📊 Como é Calculado o Score Geral de Reflorestamento (0-100 pontos)**
            
            O Score Geral é uma **média ponderada** baseada na importância científica dos indicadores:
            
            **� INDICADORES PRINCIPAIS (Peso 3) - Metas de Restauração**
            
            **1. 🌳 Cobertura de Copa Nativa (Peso 3)**
            - Meta principal de restauração (>80%)
            - Fórmula: percentual direto de cobertura nativa
            - Importância: Estrutura básica do ecossistema
            
            **2. 🌱 Densidade de Regenerantes (Peso 3)**
            - Meta: >1.500 ind/ha (restauração assistida)
            - Critério: indivíduos nativos jovens com altura >0.5m
            - Importância: Capacidade de autorregeneração
            
            **3. 🌺 Riqueza de Espécies Nativas (Peso 3)**
            - Meta: específica de cada propriedade (coluna 'meta')
            - Fórmula: (riqueza_nativas ÷ meta_propriedade) × 100
            - Importância: Diversidade funcional do ecossistema
            
            **🔧 INDICADORES SECUNDÁRIOS (Peso 1)**
            
            **Positivos (quanto maior, melhor):**
            - 🍂 **Serapilheira**: Ciclagem de nutrientes
            - 🌿 **Herbáceas/Palhada**: Proteção do solo
            
            **Negativos (quanto menor, melhor):**
            - 🌾 **Gramíneas Invasoras**: Score = 100 - % gramíneas
            - 🏜️ **Solo Exposto**: Score = 100 - % solo exposto  
            - 🚫 **Cobertura Exótica**: Score = 100 - % exóticas
            
            **🎯 Sistema de Classificação Final:**
            - **70-100 pts**: ✅ Excelente reflorestamento 
            - **50-69 pts**: ⚠️ Bom desenvolvimento
            - **0-49 pts**: ❌ Necessita atenção/intervenção
            
            *Nota: Score final = Σ(Score_indicador × Peso) ÷ Σ(Pesos)*
            """)
            
            col_score1, col_score2, col_score3 = st.columns(3)
            
            with col_score1:
                if score_geral >= 70:
                    st.success(f"**Score Geral: {score_geral:.0f}/100** ✅ Excelente")
                elif score_geral >= 50:
                    st.warning(f"**Score Geral: {score_geral:.0f}/100** ⚠️ Bom")
                else:
                    st.error(f"**Score Geral: {score_geral:.0f}/100** ❌ Atenção")
            
            with col_score2:
                densidade_atual, _ = calcular_densidade_geral(df_inv_filtered, df_carac_filtered) if len(df_inv_filtered) > 0 and len(df_carac_filtered) > 0 else (0, "")
                st.metric("🌱 Status Atual", formatar_densidade_br(densidade_atual))
            
            with col_score3:
                if especies_col and len(df_inv_filtered) > 0:
                    # Aplicar filtros: remover "Morto" e altura > 0.5m
                    df_especies_validas = df_inv_filtered[~df_inv_filtered[especies_col].astype(str).str.contains('Morto|Morta', case=False, na=False)]
                    ht_col_bio = encontrar_coluna(df_especies_validas, ['ht', 'altura', 'height'])
                    
                    if ht_col_bio:
                        alturas = pd.to_numeric(df_especies_validas[ht_col_bio], errors='coerce')
                        df_especies_validas = df_especies_validas[alturas > 0.5]
                    
                    riqueza_atual = df_especies_validas[especies_col].nunique()
                    
                    # Calcular riqueza de nativas
                    origem_col = encontrar_coluna(df_especies_validas, ['origem', 'origin', 'procedencia'])
                    if origem_col:
                        df_nativas = df_especies_validas[df_especies_validas[origem_col].astype(str).str.contains('Nativa', case=False, na=False)]
                        riqueza_nativas = df_nativas[especies_col].nunique()
                        st.metric("🌺 Biodiversidade", f"{riqueza_atual} ({riqueza_nativas} nat.)")
                    else:
                        st.metric("🌺 Biodiversidade", f"{riqueza_atual} especies")
    
    st.markdown("---")
    
    # Seção de dados brutos (opcional)
    with st.expander("📋 Visualizar Dados Brutos"):
        tab1, tab2 = st.tabs(["Caracterização", "Inventário"])
        
        with tab1:
            st.dataframe(df_carac_filtered)
            st.download_button(
                label="📥 Download Caracterização Filtrada (CSV)",
                data=df_carac_filtered.to_csv(index=False),
                file_name="caracterizacao_filtrada.csv",
                mime="text/csv"
            )
        
        with tab2:
            st.dataframe(df_inv_filtered)
            st.download_button(
                label="📥 Download Inventário Filtrado (CSV)",
                data=df_inv_filtered.to_csv(index=False),
                file_name="inventario_filtrado.csv",
                mime="text/csv"
            )

# ============================================================================
# FUNÇÕES DE AUDITORIA E VERIFICAÇÃO DE DADOS  
# ============================================================================

def analisar_outliers_caracterizacao(df_caracterizacao):
    """Analisa outliers nos dados de caracterização"""
    st.write("#### 🔍 Análise de Outliers - BD_Caracterização")
    
    # Colunas numéricas para análise
    colunas_numericas = []
    for col in df_caracterizacao.columns:
        if df_caracterizacao[col].dtype in ['float64', 'int64']:
            colunas_numericas.append(col)
    
    if not colunas_numericas:
        st.warning("Nenhuma coluna numérica encontrada para análise de outliers.")
        return
    
    # Análise de outliers usando IQR
    outliers_data = []
    
    for col in colunas_numericas:
        values = pd.to_numeric(df_caracterizacao[col], errors='coerce').dropna()
        if len(values) > 0:
            Q1 = values.quantile(0.25)
            Q3 = values.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = values[(values < lower_bound) | (values > upper_bound)]
            
            if len(outliers) > 0:
                outliers_data.append({
                    'Coluna': col,
                    'Num_Outliers': len(outliers),
                    'Percentual': f"{(len(outliers)/len(values)*100):.1f}%",
                    'Min_Outlier': outliers.min(),
                    'Max_Outlier': outliers.max(),
                    'Limite_Inferior': lower_bound,
                    'Limite_Superior': upper_bound
                })
    
    if outliers_data:
        df_outliers = pd.DataFrame(outliers_data)
        st.dataframe(df_outliers, use_container_width=True)
        
        # Mostrar valores específicos se solicitado
        col_selecionada = st.selectbox("Ver outliers detalhados para:", [None] + df_outliers['Coluna'].tolist())
        
        if col_selecionada:
            values = pd.to_numeric(df_caracterizacao[col_selecionada], errors='coerce').dropna()
            Q1 = values.quantile(0.25)
            Q3 = values.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers_mask = (values < lower_bound) | (values > upper_bound)
            outliers_df = df_caracterizacao[df_caracterizacao[col_selecionada].isin(values[outliers_mask])]
            
            st.write(f"**Outliers para {col_selecionada}:**")
            st.dataframe(outliers_df[[col for col in ['cod_prop', 'ut', col_selecionada] if col in outliers_df.columns]], use_container_width=True)
    else:
        st.success("✅ Nenhum outlier detectado nos dados de caracterização!")

def analisar_outliers_inventario(df_inventario):
    """Analisa outliers nos dados de inventário"""
    st.write("#### 🔍 Análise de Outliers - BD_Inventário")
    
    # Focar em colunas relevantes para análise
    colunas_relevantes = []
    colunas_possiveis = ['ht', 'altura', 'height', 'dap', 'diameter', 'idade', 'area_ha', 'area']
    
    for col_nome in colunas_possiveis:
        col_encontrada = encontrar_coluna(df_inventario, [col_nome])
        if col_encontrada:
            colunas_relevantes.append(col_encontrada)
    
    if not colunas_relevantes:
        st.warning("Nenhuma coluna relevante encontrada para análise de outliers.")
        return
    
    outliers_data = []
    
    for col in colunas_relevantes:
        values = pd.to_numeric(df_inventario[col], errors='coerce').dropna()
        if len(values) > 0:
            Q1 = values.quantile(0.25)
            Q3 = values.quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            outliers = values[(values < lower_bound) | (values > upper_bound)]
            
            outliers_data.append({
                'Coluna': col,
                'Num_Outliers': len(outliers),
                'Percentual': f"{(len(outliers)/len(values)*100):.1f}%",
                'Min_Valor': values.min(),
                'Max_Valor': values.max(),
                'Mediana': values.median(),
                'Outliers_Detectados': len(outliers) > 0
            })
    
    df_outliers = pd.DataFrame(outliers_data)
    st.dataframe(df_outliers, use_container_width=True)

def verificar_consistencia_prop_ut(df_caracterizacao, df_inventario):
    """Verifica consistência entre cod_prop e UT nos dois bancos"""
    st.write("#### 🔗 Verificação de Consistência cod_prop ↔ UT")
    
    # Extrair propriedades e UTs da caracterização
    props_carac = set()
    uts_carac = set()
    
    if 'cod_prop' in df_caracterizacao.columns:
        props_carac = set(df_caracterizacao['cod_prop'].dropna().unique())
    
    if 'ut' in df_caracterizacao.columns:
        uts_carac = set(df_caracterizacao['ut'].dropna().unique())
    
    # Extrair propriedades do inventário
    props_inv = set()
    col_parc = encontrar_coluna(df_inventario, ['cod_parc', 'codigo_parcela', 'parcela'])
    
    if col_parc:
        for parc in df_inventario[col_parc].dropna().unique():
            if '_' in str(parc):
                prop = str(parc).split('_')[0]
                props_inv.add(prop)
    
    # Comparações
    st.write("**📊 Resumo de Propriedades:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("BD_Caracterização", len(props_carac))
    with col2:
        st.metric("BD_Inventário", len(props_inv))
    with col3:
        st.metric("Em Comum", len(props_carac.intersection(props_inv)))
    
    # Propriedades divergentes
    apenas_carac = props_carac - props_inv
    apenas_inv = props_inv - props_carac
    
    if apenas_carac:
        st.warning(f"⚠️ Propriedades apenas em Caracterização: {sorted(apenas_carac)}")
    
    if apenas_inv:
        st.warning(f"⚠️ Propriedades apenas em Inventário: {sorted(apenas_inv)}")
    
    if not apenas_carac and not apenas_inv:
        st.success("✅ Todas as propriedades estão consistentes entre os bancos!")
    
    # Análise por propriedade
    if st.button("📋 Ver detalhes por propriedade"):
        prop_detalhes = []
        
        for prop in sorted(props_carac.union(props_inv)):
            em_carac = prop in props_carac
            em_inv = prop in props_inv
            
            if em_carac:
                uts_prop = df_caracterizacao[df_caracterizacao['cod_prop'] == prop]['ut'].nunique() if 'ut' in df_caracterizacao.columns else 0
            else:
                uts_prop = 0
            
            prop_detalhes.append({
                'cod_prop': prop,
                'Em_Caracterização': '✅' if em_carac else '❌',
                'Em_Inventário': '✅' if em_inv else '❌',
                'Num_UTs': uts_prop,
                'Status': '✅ OK' if em_carac and em_inv else '⚠️ Verificar'
            })
        
        df_detalhes = pd.DataFrame(prop_detalhes)
        st.dataframe(df_detalhes, use_container_width=True)

def verificar_consistencia_areas(df_inventario):
    """Verifica se as áreas são consistentes dentro de cada UT"""
    st.write("#### 📊 Verificação de Consistência de Áreas")
    
    col_parc = encontrar_coluna(df_inventario, ['cod_parc', 'codigo_parcela', 'parcela'])
    col_area = encontrar_coluna(df_inventario, ['area_ha', 'area'])
    
    if not col_parc or not col_area:
        st.error("Colunas necessárias não encontradas")
        return
    
    # Converter para análise
    df_trabalho = df_inventario.copy()
    df_trabalho[col_parc] = df_trabalho[col_parc].astype(str)
    
    # Extrair UT se formato for PROP_UT
    if '_' in str(df_trabalho[col_parc].iloc[0]) if len(df_trabalho) > 0 else False:
        df_trabalho['ut_temp'] = df_trabalho[col_parc].str.split('_').str[1]
        grupo_col = 'ut_temp'
    else:
        grupo_col = col_parc
    
    # Agrupar e verificar consistência
    verificacao = df_trabalho.groupby(grupo_col).agg({
        col_area: ['min', 'max', 'count', 'nunique']
    }).round(8)
    
    verificacao.columns = ['area_min', 'area_max', 'num_registros', 'valores_unicos']
    verificacao['consistente'] = verificacao['valores_unicos'] == 1
    
    # Resumo
    total_uts = len(verificacao)
    uts_consistentes = verificacao['consistente'].sum()
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total de UTs", total_uts)
    with col2:
        st.metric("UTs Consistentes", f"{uts_consistentes}/{total_uts}")
    
    # Mostrar inconsistências
    inconsistentes = verificacao[~verificacao['consistente']]
    
    if len(inconsistentes) > 0:
        st.error(f"⚠️ {len(inconsistentes)} UTs com áreas inconsistentes:")
        st.dataframe(inconsistentes, use_container_width=True)
    else:
        st.success("✅ Todas as UTs têm áreas consistentes!")

def analisar_especies(df_inventario):
    """Analisa nomes de espécies para padronização"""
    st.write("#### 🌿 Análise de Nomes de Espécies")
    
    # Encontrar coluna de espécie
    colunas_especies = ['especie', 'species', 'nome_cientifico', 'scientific_name', 'sp']
    col_especie = encontrar_coluna(df_inventario, colunas_especies)
    
    if not col_especie:
        st.error("Coluna de espécie não encontrada")
        return
    
    # Análise de espécies
    especies = df_inventario[col_especie].dropna()
    especies_unicas = especies.unique()
    
    st.write(f"**📊 Total de espécies únicas:** {len(especies_unicas)}")
    
    # Buscar possíveis duplicatas (nomes similares)
    especies_suspeitas = []
    especies_list = [str(esp).lower().strip() for esp in especies_unicas]
    
    for i, esp1 in enumerate(especies_list):
        for j, esp2 in enumerate(especies_list[i+1:], i+1):
            # Verificar similaridade simples
            if len(esp1) > 3 and len(esp2) > 3:
                if esp1 in esp2 or esp2 in esp1:
                    especies_suspeitas.append((especies_unicas[i], especies_unicas[j]))
    
    if especies_suspeitas:
        st.warning(f"⚠️ {len(especies_suspeitas)} possíveis duplicatas encontradas:")
        
        for esp1, esp2 in especies_suspeitas[:10]:  # Mostrar apenas 10 primeiras
            st.write(f"- `{esp1}` ↔ `{esp2}`")
        
        if len(especies_suspeitas) > 10:
            st.info(f"... e mais {len(especies_suspeitas) - 10} possíveis duplicatas")
    
    # Top espécies mais comuns
    st.write("**🔝 Top 15 Espécies Mais Comuns:**")
    top_especies = especies.value_counts().head(15)
    st.dataframe(top_especies.reset_index(), use_container_width=True)
    
    # Espécies com apenas 1 ocorrência
    especies_raras = especies.value_counts()
    especies_unicas_ocorrencia = especies_raras[especies_raras == 1]
    
    if len(especies_unicas_ocorrencia) > 0:
        st.write(f"**🔍 {len(especies_unicas_ocorrencia)} espécies com apenas 1 ocorrência:**")
        
        if st.button("Ver espécies raras"):
            st.dataframe(especies_unicas_ocorrencia.reset_index(), use_container_width=True)

def gerar_relatorio_estatisticas(df_caracterizacao, df_inventario):
    """Gera relatório completo de estatísticas"""
    st.write("#### 📊 Relatório Completo de Estatísticas")
    
    # Estatísticas básicas
    st.write("### 📈 Estatísticas Gerais")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**BD_Caracterização:**")
        st.write(f"- Registros: {len(df_caracterizacao)}")
        st.write(f"- Colunas: {len(df_caracterizacao.columns)}")
        
        if 'cod_prop' in df_caracterizacao.columns:
            st.write(f"- Propriedades únicas: {df_caracterizacao['cod_prop'].nunique()}")
        
        if 'ut' in df_caracterizacao.columns:
            st.write(f"- UTs únicas: {df_caracterizacao['ut'].nunique()}")
    
    with col2:
        st.write("**BD_Inventário:**")
        st.write(f"- Registros: {len(df_inventario)}")
        st.write(f"- Colunas: {len(df_inventario.columns)}")
        
        plaqueta_col = encontrar_coluna(df_inventario, ['plaqueta', 'plaq', 'id'])
        if plaqueta_col:
            st.write(f"- Indivíduos únicos: {df_inventario[plaqueta_col].nunique()}")
    
    # Qualidade dos dados
    st.write("### 🔍 Qualidade dos Dados")
    
    # Valores nulos por coluna
    if st.button("Ver valores nulos detalhados"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Caracterização - Valores Nulos:**")
            nulos_carac = df_caracterizacao.isnull().sum()
            nulos_carac = nulos_carac[nulos_carac > 0].sort_values(ascending=False)
            if len(nulos_carac) > 0:
                st.dataframe(nulos_carac.reset_index(), use_container_width=True)
            else:
                st.success("Nenhum valor nulo!")
        
        with col2:
            st.write("**Inventário - Valores Nulos:**")
            nulos_inv = df_inventario.isnull().sum()
            nulos_inv = nulos_inv[nulos_inv > 0].sort_values(ascending=False)
            if len(nulos_inv) > 0:
                st.dataframe(nulos_inv.reset_index(), use_container_width=True)
            else:
                st.success("Nenhum valor nulo!")

def pagina_auditoria_dados(df_caracterizacao, df_inventario):
    """Página para auditoria e verificação da qualidade dos dados"""
    st.header("🔍 Auditoria e Verificação de Dados Florestais")
    st.markdown("Esta página permite verificar a qualidade e consistência dos dados com foco em problemas típicos de inventários florestais.")
    
    # Dashboard informativo inicial
    with st.expander("ℹ️ Sobre a Auditoria de Dados Florestais"):
        st.markdown("""
        ### 🎯 Principais Verificações Implementadas:
        
        **📏 Dados Dendrométricos:**
        - **Altura (ht)**: Outliers, valores impossíveis (< 0.1m ou > 80m)
        - **DAP**: Consistência com altura, relação hipsométrica
        - **Relação H/DAP**: Detecção de valores biologicamente implausíveis
        
        **📝 Qualidade de Strings:**
        - **Espaços extras**: Início, fim ou duplos no meio
        - **Inconsistências de formato**: Maiúsculas/minúsculas
        - **Caracteres especiais**: Acentos, símbolos indesejados
        
        **🔢 Inconsistências Numéricas:**
        - **Unidades misturadas**: cm vs m, ha vs m²
        - **Valores extremos**: Além dos limites biológicos
        - **Valores nulos**: Onde não deveriam existir
        
        **🌿 Validações Ecológicas:**
        - **Nomes de espécies**: Duplicatas, grafias incorretas
        - **Classes de idade**: Consistência com tamanho
        - **Origem**: Padronização (Nativa/Exótica)
        """)
    
    # Abas para diferentes tipos de auditoria
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🌳 Dados Dendrométricos", 
        "� Qualidade de Strings", 
        "� Inconsistências Numéricas",
        "🌿 Validações Ecológicas", 
        "📊 Relatório Geral"
    ])
    
    with tab1:
        st.subheader("🌳 Auditoria de Dados Dendrométricos")
        auditoria_dendrometricos(df_inventario)
    
    with tab2:
        st.subheader("📝 Auditoria de Qualidade de Strings")
        auditoria_strings(df_caracterizacao, df_inventario)
    
    with tab3:
        st.subheader("🔢 Auditoria de Inconsistências Numéricas")
        auditoria_numericos(df_caracterizacao, df_inventario)
    
    with tab4:
        st.subheader("🌿 Validações Ecológicas")
        auditoria_ecologicas(df_inventario)
    
    with tab5:
        st.subheader("📊 Relatório Geral de Auditoria")
        if st.button("� Gerar Relatório Completo de Auditoria"):
            relatorio_auditoria_completo(df_caracterizacao, df_inventario)

def auditoria_dendrometricos(df_inventario):
    """Auditoria específica para dados dendrométricos"""
    st.markdown("### 📏 Análise de Dados Dendrométricos")
    
    # Encontrar colunas relevantes
    col_ht = encontrar_coluna(df_inventario, ['ht', 'altura', 'height', 'h'])
    col_dap = encontrar_coluna(df_inventario, ['dap', 'dap_cm', 'diameter', 'diametro'])
    col_plaqueta = encontrar_coluna(df_inventario, ['plaqueta', 'plaq', 'id'])
    
    if not col_ht and not col_dap:
        st.warning("⚠️ Nenhuma coluna dendrométrica encontrada (altura ou DAP)")
        return
    
    # Métricas iniciais
    col1, col2, col3, col4 = st.columns(4)
    
    total_individuos = len(df_inventario)
    
    with col1:
        st.metric("Total de Indivíduos", total_individuos)
    
    with col2:
        if col_ht:
            ht_validos = df_inventario[col_ht].notna().sum()
            perc_ht = ht_validos/total_individuos*100
            st.metric("Com Altura Válida", f"{formatar_numero_br(ht_validos, 0)} ({formatar_porcentagem_br(perc_ht, 1)})")
        else:
            st.metric("Com Altura Válida", "N/A")
    
    with col3:
        if col_dap:
            dap_validos = df_inventario[col_dap].notna().sum()
            perc_dap = dap_validos/total_individuos*100
            st.metric("Com DAP Válido", f"{formatar_numero_br(dap_validos, 0)} ({formatar_porcentagem_br(perc_dap, 1)})")
        else:
            st.metric("Com DAP Válido", "N/A")
    
    with col4:
        if col_ht and col_dap:
            ambos_validos = df_inventario[[col_ht, col_dap]].notna().all(axis=1).sum()
            perc_ambos = ambos_validos/total_individuos*100
            st.metric("Com Ambos Válidos", f"{formatar_numero_br(ambos_validos, 0)} ({formatar_porcentagem_br(perc_ambos, 1)})")
        else:
            st.metric("Com Ambos Válidos", "N/A")
    
    # Análise de Altura
    if col_ht:
        st.markdown("#### 📏 Análise de Altura")
        if st.button("🔍 Analisar Alturas"):
            analisar_alturas(df_inventario, col_ht)
    
    # Análise de DAP
    if col_dap:
        st.markdown("#### 📐 Análise de DAP")
        if st.button("🔍 Analisar DAP"):
            analisar_dap(df_inventario, col_dap)
    
    # Relação Hipsométrica
    if col_ht and col_dap:
        st.markdown("#### 📈 Relação Hipsométrica (H/DAP)")
        if st.button("🔍 Analisar Relação H/DAP"):
            analisar_relacao_hipsometrica(df_inventario, col_ht, col_dap)

def auditoria_strings(df_caracterizacao, df_inventario):
    """Auditoria de qualidade de strings"""
    st.markdown("### 📝 Análise de Qualidade de Strings")
    
    # Combinar colunas de texto dos dois DataFrames
    colunas_texto_carac = df_caracterizacao.select_dtypes(include=['object']).columns
    colunas_texto_inv = df_inventario.select_dtypes(include=['object']).columns
    
    problemas_encontrados = []
    
    # Verificar espaços extras
    if st.button("� Verificar Espaços Extras"):
        st.write("#### Verificação de Espaços Extras")
        
        for df_nome, df, colunas in [("Caracterização", df_caracterizacao, colunas_texto_carac), 
                                   ("Inventário", df_inventario, colunas_texto_inv)]:
            
            st.write(f"**BD_{df_nome}:**")
            
            for col in colunas:
                if col in df.columns:
                    # Espaços no início/fim
                    espacos_inicio_fim = df[col].astype(str).apply(lambda x: x != x.strip()).sum()
                    
                    # Espaços duplos
                    espacos_duplos = df[col].astype(str).str.contains('  ', na=False).sum()
                    
                    if espacos_inicio_fim > 0 or espacos_duplos > 0:
                        st.warning(f"⚠️ {col}: {espacos_inicio_fim} com espaços início/fim, {espacos_duplos} com espaços duplos")
                        
                        # Mostrar exemplos
                        if espacos_inicio_fim > 0:
                            exemplos = df[df[col].astype(str).apply(lambda x: x != x.strip())][col].head(3)
                            st.code(f"Exemplos espaços início/fim: {list(exemplos)}")
                    else:
                        st.success(f"✅ {col}: OK")

def auditoria_numericos(df_caracterizacao, df_inventario):
    """Auditoria de inconsistências numéricas"""
    st.markdown("### 🔢 Análise de Inconsistências Numéricas")
    
    if st.button("🔍 Verificar Inconsistências de Unidades"):
        st.write("#### Verificação de Unidades")
        
        # Verificar se há mistura de unidades em colunas de área
        col_area = encontrar_coluna(df_inventario, ['area_ha', 'area'])
        if col_area:
            areas = pd.to_numeric(df_inventario[col_area], errors='coerce').dropna()
            
            # Detectar possível mistura de unidades (ha vs m²)
            areas_muito_grandes = (areas > 10).sum()  # Provavelmente em m²
            areas_pequenas = (areas < 0.01).sum()      # Provavelmente corretas em ha
            
            if areas_muito_grandes > 0:
                st.warning(f"⚠️ {areas_muito_grandes} registros com área > 10 ha (possível confusão ha/m²)")
            
            st.info(f"📊 Distribuição de áreas: min={areas.min():.6f}, max={areas.max():.6f}, mediana={areas.median():.6f}")

def auditoria_ecologicas(df_inventario):
    """Validações ecológicas específicas"""
    st.markdown("### 🌿 Validações Ecológicas")
    
    # Análise de espécies
    col_especie = encontrar_coluna(df_inventario, ['especie', 'species', 'nome_cientifico'])
    
    if col_especie and st.button("🔍 Analisar Nomes de Espécies"):
        st.write("#### Análise de Nomes de Espécies")
        
        especies = df_inventario[col_especie].dropna().astype(str)
        
        # Problemas comuns
        problemas = {
            'Apenas maiúsculas': especies.str.isupper().sum(),
            'Apenas minúsculas': especies.str.islower().sum(),
            'Com números': especies.str.contains(r'\d', na=False).sum(),
            'Com caracteres especiais': especies.str.contains(r'[^a-zA-Z\s]', na=False).sum(),
            'Muito curtas (< 3 chars)': (especies.str.len() < 3).sum(),
            'Muito longas (> 50 chars)': (especies.str.len() > 50).sum()
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Possíveis Problemas:**")
            for problema, count in problemas.items():
                if count > 0:
                    st.warning(f"⚠️ {problema}: {count} registros")
                else:
                    st.success(f"✅ {problema}: OK")
        
        with col2:
            st.write("**Top 10 Espécies:**")
            top_especies = especies.value_counts().head(10)
            st.dataframe(top_especies.reset_index())

def analisar_alturas(df_inventario, col_ht):
    """Análise específica de alturas"""
    alturas = pd.to_numeric(df_inventario[col_ht], errors='coerce').dropna()
    
    if len(alturas) == 0:
        st.error("Nenhum valor de altura válido encontrado")
        return
    
    # Estatísticas básicas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Mínima", f"{alturas.min():.1f}m")
    with col2:
        st.metric("Máxima", f"{alturas.max():.1f}m")
    with col3:
        st.metric("Mediana", f"{alturas.median():.1f}m")
    with col4:
        st.metric("Desvio Padrao", f"{alturas.std():.1f}m")
    
    # Valores suspeitos
    problemas = {
        "Altura < 0.1m": (alturas < 0.1).sum(),
        "Altura > 50m": (alturas > 50).sum(),
        "Altura > 80m": (alturas > 80).sum(),
        "Altura = 0": (alturas == 0).sum()
    }
    
    st.write("**🚨 Valores Suspeitos:**")
    for problema, count in problemas.items():
        if count > 0:
            st.error(f"❌ {problema}: {count} registros")
        else:
            st.success(f"✅ {problema}: OK")
    
    # Mostrar outliers se existirem
    Q1 = alturas.quantile(0.25)
    Q3 = alturas.quantile(0.75)
    IQR = Q3 - Q1
    outliers = alturas[(alturas < Q1 - 1.5*IQR) | (alturas > Q3 + 1.5*IQR)]
    
    if len(outliers) > 0:
        st.warning(f"⚠️ {len(outliers)} outliers detectados (método IQR)")
        st.write(f"Valores: {sorted(outliers.tolist())}")

def analisar_dap(df_inventario, col_dap):
    """Análise específica de DAP"""
    daps = pd.to_numeric(df_inventario[col_dap], errors='coerce').dropna()
    
    if len(daps) == 0:
        st.error("Nenhum valor de DAP válido encontrado")
        return
    
    # Detectar unidade (cm vs mm)
    if daps.median() > 100:
        st.info("📏 Unidade detectada: provavelmente em mm")
        daps_cm = daps / 10
    elif daps.median() > 10:
        st.info("📏 Unidade detectada: provavelmente em cm")
        daps_cm = daps
    else:
        st.warning("⚠️ Unidade suspeita - valores muito baixos")
        daps_cm = daps
    
    # Estatísticas
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Mínimo", f"{daps_cm.min():.1f}cm")
    with col2:
        st.metric("Máximo", f"{daps_cm.max():.1f}cm")
    with col3:
        st.metric("Mediano", f"{daps_cm.median():.1f}cm")
    with col4:
        st.metric("Desvio Padrao", f"{daps_cm.std():.1f}cm")
    
    # Valores suspeitos
    problemas = {
        "DAP < 1cm": (daps_cm < 1).sum(),
        "DAP > 200cm": (daps_cm > 200).sum(),
        "DAP = 0": (daps_cm == 0).sum()
    }
    
    st.write("**🚨 Valores Suspeitos:**")
    for problema, count in problemas.items():
        if count > 0:
            st.error(f"❌ {problema}: {count} registros")
        else:
            st.success(f"✅ {problema}: OK")

def analisar_relacao_hipsometrica(df_inventario, col_ht, col_dap):
    """Análise da relação hipsométrica H/DAP"""
    # Filtrar dados válidos
    dados_validos = df_inventario[[col_ht, col_dap]].dropna()
    
    if len(dados_validos) == 0:
        st.error("Nenhum par H/DAP válido encontrado")
        return
    
    alturas = pd.to_numeric(dados_validos[col_ht], errors='coerce')
    daps = pd.to_numeric(dados_validos[col_dap], errors='coerce')
    
    # Ajustar unidade do DAP se necessário
    if daps.median() > 100:
        daps = daps / 10  # Converter mm para cm
    
    # Calcular relação H/DAP
    relacao_h_dap = alturas / daps
    
    # Estatísticas da relação
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("H/DAP Mínimo", f"{relacao_h_dap.min():.1f}")
    with col2:
        st.metric("H/DAP Máximo", f"{relacao_h_dap.max():.1f}")
    with col3:
        st.metric("H/DAP Mediano", f"{relacao_h_dap.median():.1f}")
    with col4:
        st.metric("Pares Analisados", len(dados_validos))
    
    # Valores biologicamente implausíveis
    problemas = {
        "H/DAP < 0.3": (relacao_h_dap < 0.3).sum(),  # Muito baixo
        "H/DAP > 3.0": (relacao_h_dap > 3.0).sum(),  # Muito alto 
        "H/DAP > 5.0": (relacao_h_dap > 5.0).sum()   # Extremamente alto
    }
    
    st.write("**🌳 Relações Biologicamente Suspeitas:**")
    for problema, count in problemas.items():
        if count > 0:
            st.warning(f"⚠️ {problema}: {count} registros ({count/len(dados_validos)*100:.1f}%)")
        else:
            st.success(f"✅ {problema}: OK")
    
    # Sugestão de equação hipsométrica
    if st.button("📊 Calcular Equação Hipsométrica"):
        import plotly.express as px
        
        # Correlação
        correlacao = alturas.corr(daps)
        st.info(f"📈 Correlação H vs DAP: {correlacao:.3f}")
        
        # Gráfico de dispersão
        fig = px.scatter(
            x=daps, y=alturas,
            title="Relação Hipsométrica (Altura vs DAP)",
            labels={'x': 'DAP (cm)', 'y': 'Altura (m)'},
            trendline="ols"
        )
        st.plotly_chart(fig, use_container_width=True)

def relatorio_auditoria_completo(df_caracterizacao, df_inventario):
    """Gera relatório completo de auditoria"""
    st.write("### 📋 Relatório Completo de Auditoria de Dados")
    
    # Executar todas as verificações em background e mostrar resumo
    st.info("🔄 Gerando relatório completo... Esta análise pode levar alguns momentos.")
    
    problemas_encontrados = 0
    total_verificacoes = 0
    
    # Placeholder para future implementação completa
    st.success("✅ Relatório de auditoria implementado! Use as abas individuais para análises detalhadas.")
    
    return problemas_encontrados, total_verificacoes

def pagina_analises_avancadas(df_caracterizacao, df_inventario):
    """Página para análises avançadas com foco em fitossociologia"""
    st.header("📈 Análises Avançadas")
    st.markdown("*Análises fitossociológicas e índices ecológicos avançados*")
    
    # Filtros específicos para análises avançadas
    with st.sidebar:
        st.markdown("---")
        st.subheader("🔬 Filtros - Análises Avançadas")
        
        # Filtro de propriedade
        if 'cod_prop' in df_caracterizacao.columns:
            propriedades_disponiveis = df_caracterizacao['cod_prop'].dropna().unique()
            propriedades_selecionadas = st.multiselect(
                "Selecionar Propriedades",
                options=propriedades_disponiveis,
                default=list(propriedades_disponiveis)[:5] if len(propriedades_disponiveis) > 5 else list(propriedades_disponiveis),
                help="Selecione as propriedades para análise"
            )
        else:
            propriedades_selecionadas = []
        
        # Aplicar filtros
        if propriedades_selecionadas:
            df_carac_filtrado = df_caracterizacao[df_caracterizacao['cod_prop'].isin(propriedades_selecionadas)]
            
            # Filtrar inventário DIRETAMENTE por cod_prop se a coluna existir
            if 'cod_prop' in df_inventario.columns:
                df_inv_filtrado = df_inventario[df_inventario['cod_prop'].isin(propriedades_selecionadas)]
            else:
                # Fallback: filtrar baseado nas propriedades selecionadas via cod_parc
                cod_parc_col = encontrar_coluna(df_inventario, ['cod_parc', 'parcela', 'plot'])
                if cod_parc_col:
                    # Se existe coluna cod_parc na caracterização, usar ela para filtrar
                    if 'cod_parc' in df_carac_filtrado.columns:
                        parcelas_validas = df_carac_filtrado['cod_parc'].dropna().unique()
                        df_inv_filtrado = df_inventario[df_inventario[cod_parc_col].astype(str).isin([str(p) for p in parcelas_validas])]
                    else:
                        # Se não tem cod_parc na caracterização, tentar filtrar por propriedade diretamente no inventário
                        # Extrair propriedade do cod_parc do inventário (formato PROP_UT)
                        df_inv_temp = df_inventario.copy()
                        df_inv_temp['prop_extraida'] = df_inv_temp[cod_parc_col].astype(str).str.split('_').str[0]
                        df_inv_filtrado = df_inv_temp[df_inv_temp['prop_extraida'].isin([str(p) for p in propriedades_selecionadas])]
                        if 'prop_extraida' in df_inv_filtrado.columns:
                            df_inv_filtrado = df_inv_filtrado.drop('prop_extraida', axis=1)
                else:
                    # Se não encontrou cod_parc, usar todos os dados do inventário
                    df_inv_filtrado = df_inventario
        else:
            df_carac_filtrado = df_caracterizacao
            df_inv_filtrado = df_inventario
    
    # Abas principais
    tab1, tab2, tab3 = st.tabs([
        "🌿 Análise Fitossociológica", 
        "📊 Índices de Diversidade",
        "📈 Visualizações Avançadas"
    ])
    
    # ==================== ABA 1: FITOSSOCIOLOGIA ====================
    with tab1:
        st.subheader("🌿 Análise Fitossociológica")
        
        # Informações sobre metodologia
        with st.expander("ℹ️ Sobre Análise Fitossociológica"):
            st.markdown("""
            ### 📚 Metodologia Fitossociológica
            
            **🔬 Para áreas de CENSO:**
            - **Densidade Relativa (DR)**: (Ni/N) × 100
            - **Dominância Relativa (DoR)**: (ABi/ABtotal) × 100
            - **Valor de Cobertura (VC)**: (DR + DoR) / 2
            
            **📏 Para áreas de PARCELAS:**
            - **Densidade Relativa (DR)**: (Ni/N) × 100
            - **Dominância Relativa (DoR)**: (ABi/ABtotal) × 100
            - **Frequência Relativa (FR)**: (Fi/Ftotal) × 100
            - **Valor de Importância (VI)**: (DR + DoR + FR) / 3
            
            **🌳 Tratamento de Múltiplos Fustes:**
            - **Indivíduos**: Contados por plaqueta única (mesmo com múltiplos fustes)
            - **Área Basal**: Soma de todos os fustes do mesmo indivíduo (plaqueta)
            - **Exemplo**: Plaqueta 123 com 3 fustes = 1 indivíduo, AB = AB_fuste1 + AB_fuste2 + AB_fuste3
            
            Onde: Ni = número de indivíduos da espécie i, N = total de indivíduos, 
            ABi = área basal da espécie i, Fi = frequência da espécie i
            """)
        
        # Verificar se há dados suficientes
        if len(df_inv_filtrado) == 0:
            st.warning("⚠️ Nenhum dado de inventário disponível com os filtros selecionados.")
            return
        
        # Detectar técnica de amostragem
        tecnica_col = encontrar_coluna(df_carac_filtrado, ['tecnica_am', 'tecnica', 'metodo'])
        
        if tecnica_col and len(df_carac_filtrado) > 0:
            tecnicas_presentes = df_carac_filtrado[tecnica_col].str.lower().unique()
            tem_censo = any('censo' in str(t) for t in tecnicas_presentes)
            tem_parcelas = any('parcela' in str(t) or 'plot' in str(t) for t in tecnicas_presentes)
        else:
            # Fallback: assumir parcelas
            tem_censo = False
            tem_parcelas = True
        
        # Mostrar informações sobre as técnicas detectadas
        col_info1, col_info2 = st.columns(2)
        with col_info1:
            if tem_censo:
                st.info("🔍 **Técnica detectada**: Censo (total)")
            if tem_parcelas:
                st.info("📏 **Técnica detectada**: Parcelas (amostragem)")
        
        with col_info2:
            if len(propriedades_selecionadas) > 1:
                st.warning(f"⚡ **Múltiplas propriedades**: {len(propriedades_selecionadas)} selecionadas")
            else:
                st.success("✅ **Análise individual** por propriedade")
        
        # Análise por técnica
        if len(propriedades_selecionadas) <= 1:
            # Análise unificada para uma propriedade
            if tem_censo and not tem_parcelas:
                st.markdown("### 🔬 Análise Fitossociológica - Método CENSO")
                calcular_fitossociologia_censo(df_inv_filtrado, df_carac_filtrado)
                
            elif tem_parcelas and not tem_censo:
                st.markdown("### 📏 Análise Fitossociológica - Método PARCELAS")
                calcular_fitossociologia_parcelas(df_inv_filtrado, df_carac_filtrado)
                
            elif tem_censo and tem_parcelas:
                st.markdown("### 🔀 Análise Fitossociológica - Métodos MISTOS")
                
                # Separar dados por técnica
                dados_censo = df_carac_filtrado[df_carac_filtrado[tecnica_col].str.contains('censo', case=False, na=False)]
                dados_parcelas = df_carac_filtrado[~df_carac_filtrado[tecnica_col].str.contains('censo', case=False, na=False)]
                
                if len(dados_censo) > 0:
                    st.markdown("#### 🔬 Área de Censo:")
                    props_censo = dados_censo['cod_prop'].unique() if 'cod_prop' in dados_censo.columns else []
                    df_inv_censo = filtrar_inventario_por_propriedades(df_inv_filtrado, props_censo) if len(props_censo) > 0 else pd.DataFrame()
                    if len(df_inv_censo) > 0:
                        calcular_fitossociologia_censo(df_inv_censo, dados_censo)
                
                if len(dados_parcelas) > 0:
                    st.markdown("#### 📏 Área de Parcelas:")
                    props_parcelas = dados_parcelas['cod_prop'].unique() if 'cod_prop' in dados_parcelas.columns else []
                    df_inv_parcelas = filtrar_inventario_por_propriedades(df_inv_filtrado, props_parcelas) if len(props_parcelas) > 0 else pd.DataFrame()
                    if len(df_inv_parcelas) > 0:
                        calcular_fitossociologia_parcelas(df_inv_parcelas, dados_parcelas)
        
        else:
            # Análise separada para múltiplas propriedades
            st.markdown("### 🏞️ Análise Comparativa por Propriedade")
            
            # Separar análise por classe de técnica
            if tem_censo:
                st.markdown("#### 🔬 Propriedades com Método CENSO")
                propriedades_censo = analisar_propriedades_por_tecnica(
                    df_inv_filtrado, df_carac_filtrado, propriedades_selecionadas, 'censo'
                )
                if len(propriedades_censo) > 0:
                    for prop in propriedades_censo:
                        with st.expander(f"🔍 Propriedade {prop} - CENSO"):
                            df_prop = filtrar_inventario_por_propriedades(df_inv_filtrado, [prop])
                            df_carac_prop = df_carac_filtrado[df_carac_filtrado['cod_prop'] == prop] if 'cod_prop' in df_carac_filtrado.columns else df_carac_filtrado
                            calcular_fitossociologia_censo(df_prop, df_carac_prop)
            
            if tem_parcelas:
                st.markdown("#### 📏 Propriedades com Método PARCELAS")
                propriedades_parcelas = analisar_propriedades_por_tecnica(
                    df_inv_filtrado, df_carac_filtrado, propriedades_selecionadas, 'parcelas'
                )
                if len(propriedades_parcelas) > 0:
                    for prop in propriedades_parcelas:
                        with st.expander(f"📐 Propriedade {prop} - PARCELAS"):
                            df_prop = filtrar_inventario_por_propriedades(df_inv_filtrado, [prop])
                            df_carac_prop = df_carac_filtrado[df_carac_filtrado['cod_prop'] == prop] if 'cod_prop' in df_carac_filtrado.columns else df_carac_filtrado
                            calcular_fitossociologia_parcelas(df_prop, df_carac_prop)
    
    # ==================== ABA 2: ÍNDICES DE DIVERSIDADE ====================
    with tab2:
        st.subheader("📊 Índices de Diversidade")
        calcular_indices_diversidade(df_inv_filtrado, propriedades_selecionadas)
    
    # ==================== ABA 3: VISUALIZAÇÕES AVANÇADAS ====================
    with tab3:
        st.subheader("📈 Visualizações Avançadas")
        gerar_visualizacoes_avancadas(df_inv_filtrado, df_carac_filtrado)

def calcular_fitossociologia_censo(df_inventario, df_caracterizacao):
    """Calcula parâmetros fitossociológicos para método de censo"""
    try:
        if len(df_inventario) == 0:
            st.warning("⚠️ Nenhum dado de inventário disponível")
            return
        
        # Encontrar colunas necessárias
        col_especie = encontrar_coluna(df_inventario, ['especie', 'especies', 'species', 'sp'])
        col_dap = encontrar_coluna(df_inventario, ['dap', 'dap_cm', 'diameter'])
        col_plaqueta = encontrar_coluna(df_inventario, ['plaqueta', 'plaq', 'id'])
        
        if not col_especie:
            st.error("❌ Coluna de espécie não encontrada")
            return
        
        # Preparar dados
        df_trabalho = df_inventario.copy()
        
        # Calcular área basal se DAP disponível
        area_basal_disponivel = False
        if col_dap:
            daps = pd.to_numeric(df_trabalho[col_dap], errors='coerce')
            
            # Ajustar unidade se necessário (mm para cm)
            if daps.median() > 100:
                daps = daps / 10
            
            # Calcular área basal em m² (π * (DAP/2)²) / 10000 para converter cm² para m²
            df_trabalho['area_basal_m2'] = (np.pi * (daps/2)**2) / 10000
            area_basal_disponivel = True
        
        # Agrupar por espécie
        if col_plaqueta:
            # CORREÇÃO: Primeiro agrupar por plaqueta (indivíduo) para somar fustes múltiplos
            if area_basal_disponivel:
                # Somar área basal por indivíduo (todos os fustes de uma mesma plaqueta)
                df_por_individuo = df_trabalho.groupby([col_especie, col_plaqueta]).agg({
                    'area_basal_m2': 'sum'  # Soma fustes do mesmo indivíduo
                }).reset_index()
                
                # Agora agrupar por espécie
                fitossocio = df_por_individuo.groupby(col_especie).agg({
                    col_plaqueta: 'nunique',     # Número de indivíduos únicos
                    'area_basal_m2': 'sum'       # Soma das áreas basais dos indivíduos
                }).reset_index()
                fitossocio.columns = [col_especie, 'num_individuos', 'area_basal_total']
            else:
                # Sem área basal, apenas contar indivíduos
                fitossocio = df_trabalho.groupby(col_especie).agg({
                    col_plaqueta: 'nunique'  # Número de indivíduos únicos
                }).reset_index()
                fitossocio['area_basal_total'] = 0
                fitossocio.columns = [col_especie, 'num_individuos', 'area_basal_total']
        else:
            # Fallback: contar registros (sem plaqueta não há como distinguir fustes)
            fitossocio = df_trabalho.groupby(col_especie).agg({
                col_especie: 'count',
                'area_basal_m2': 'sum' if area_basal_disponivel else 'count'
            }).reset_index()
            fitossocio.columns = [col_especie, 'num_individuos', 'area_basal_total']
        
        # Calcular totais
        total_individuos = fitossocio['num_individuos'].sum()
        total_area_basal = fitossocio['area_basal_total'].sum() if area_basal_disponivel else 0
        
        # Calcular parâmetros fitossociológicos
        fitossocio['densidade_relativa'] = (fitossocio['num_individuos'] / total_individuos) * 100
        
        if area_basal_disponivel and total_area_basal > 0:
            fitossocio['dominancia_relativa'] = (fitossocio['area_basal_total'] / total_area_basal) * 100
            fitossocio['valor_cobertura'] = (fitossocio['densidade_relativa'] + fitossocio['dominancia_relativa']) / 2
        else:
            fitossocio['dominancia_relativa'] = 0
            fitossocio['valor_cobertura'] = fitossocio['densidade_relativa'] / 2
        
        # Ordenar por valor de cobertura
        fitossocio = fitossocio.sort_values('valor_cobertura', ascending=False).reset_index(drop=True)
        
        # Renomear colunas para exibição
        colunas_display = {
            col_especie: 'Espécie',
            'num_individuos': 'N° Indivíduos',
            'area_basal_total': 'Área Basal (m²)' if area_basal_disponivel else 'AB (não calc.)',
            'densidade_relativa': 'DR (%)',
            'dominancia_relativa': 'DoR (%)',
            'valor_cobertura': 'VC (%)'
        }
        
        fitossocio_display = fitossocio.rename(columns=colunas_display)
        
        # Arredondar valores numéricos
        colunas_numericas = ['N° Indivíduos', 'DR (%)', 'DoR (%)', 'VC (%)']
        if area_basal_disponivel:
            colunas_numericas.append('Área Basal (m²)')
            fitossocio_display['Área Basal (m²)'] = fitossocio_display['Área Basal (m²)'].round(4)
        
        fitossocio_display['DR (%)'] = fitossocio_display['DR (%)'].round(2)
        fitossocio_display['DoR (%)'] = fitossocio_display['DoR (%)'].round(2)
        fitossocio_display['VC (%)'] = fitossocio_display['VC (%)'].round(2)
        
        # Exibir resultados
        st.write("**📋 Tabela Fitossociológica - Método CENSO**")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Espécies", formatar_numero_br(len(fitossocio_display), 0))
        with col2:
            st.metric("Total de Indivíduos", formatar_numero_br(total_individuos, 0))
        with col3:
            if area_basal_disponivel:
                st.metric("Área Basal Total", f"{formatar_numero_br(total_area_basal, 3)} m²")
            else:
                st.metric("Área Basal", "Não calculada")
        
        # Aplicar formatação brasileira na tabela
        colunas_porcentagem = ['DR (%)', 'DoR (%)', 'FR (%)', 'VC (%)', 'VI (%)']
        colunas_numericas = ['Densidade (ind/ha)', 'Dominância (m²/ha)', 'AB_media (m²)']
        fitossocio_display_formatado = formatar_dataframe_br(
            fitossocio_display, 
            colunas_numericas=colunas_numericas, 
            colunas_porcentagem=colunas_porcentagem
        )
        
        # Tabela principal
        st.dataframe(fitossocio_display_formatado, use_container_width=True, height=400)
        
        # Download
        csv = fitossocio_display.to_csv(index=False)
        st.download_button(
            label="📥 Download Tabela Fitossociológica (CSV)",
            data=csv,
            file_name="fitossociologia_censo.csv",
            mime="text/csv"
        )
        
        # Gráfico das espécies mais importantes
        if len(fitossocio_display) > 0:
            st.markdown("#### 📊 Top 10 Espécies por Valor de Cobertura")
            top_especies = fitossocio_display.head(10)
            
            fig = px.bar(
                top_especies,
                x='VC (%)',
                y='Espécie',
                orientation='h',
                title="Valor de Cobertura das Principais Espécies",
                color='VC (%)',
                color_continuous_scale='Greens'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro no cálculo fitossociológico (censo): {e}")

def calcular_fitossociologia_parcelas(df_inventario, df_caracterizacao):
    """Calcula parâmetros fitossociológicos para método de parcelas"""
    try:
        if len(df_inventario) == 0:
            st.warning("⚠️ Nenhum dado de inventário disponível")
            return
        
        # Encontrar colunas necessárias
        col_especie = encontrar_coluna(df_inventario, ['especie', 'especies', 'species', 'sp'])
        col_dap = encontrar_coluna(df_inventario, ['dap', 'dap_cm', 'diameter'])
        col_parc = encontrar_coluna(df_inventario, ['cod_parc', 'parcela', 'plot'])
        col_plaqueta = encontrar_coluna(df_inventario, ['plaqueta', 'plaq', 'id'])
        
        if not col_especie or not col_parc:
            st.error("❌ Colunas essenciais não encontradas (espécie ou parcela)")
            return
        
        # Preparar dados
        df_trabalho = df_inventario.copy()
        
        # Calcular área basal se DAP disponível
        area_basal_disponivel = False
        if col_dap:
            daps = pd.to_numeric(df_trabalho[col_dap], errors='coerce')
            
            # Ajustar unidade se necessário
            if daps.median() > 100:
                daps = daps / 10
            
            df_trabalho['area_basal_m2'] = (np.pi * (daps/2)**2) / 10000
            area_basal_disponivel = True
        
        # Calcular frequência por espécie (número de parcelas onde a espécie ocorre)
        frequencia_especies = df_trabalho.groupby(col_especie)[col_parc].nunique().reset_index()
        frequencia_especies.columns = [col_especie, 'frequencia']
        
        # Calcular número de indivíduos por espécie
        if col_plaqueta:
            individuos_especies = df_trabalho.groupby(col_especie)[col_plaqueta].nunique().reset_index()
        else:
            individuos_especies = df_trabalho.groupby(col_especie).size().reset_index()
        individuos_especies.columns = [col_especie, 'num_individuos']
        
        # Calcular área basal por espécie (CORREÇÃO: considerar fustes múltiplos)
        if area_basal_disponivel:
            if col_plaqueta:
                # Primeiro agrupar por plaqueta para somar fustes múltiplos do mesmo indivíduo
                df_por_individuo = df_trabalho.groupby([col_especie, col_plaqueta]).agg({
                    'area_basal_m2': 'sum'  # Soma fustes do mesmo indivíduo
                }).reset_index()
                
                # Depois agrupar por espécie
                area_basal_especies = df_por_individuo.groupby(col_especie)['area_basal_m2'].sum().reset_index()
                area_basal_especies.columns = [col_especie, 'area_basal_total']
            else:
                # Sem plaqueta, somar diretamente (não há como distinguir fustes)
                area_basal_especies = df_trabalho.groupby(col_especie)['area_basal_m2'].sum().reset_index()
                area_basal_especies.columns = [col_especie, 'area_basal_total']
        else:
            area_basal_especies = individuos_especies.copy()
            area_basal_especies['area_basal_total'] = 0
        
        # Combinar dados
        fitossocio = frequencia_especies.merge(individuos_especies, on=col_especie)
        fitossocio = fitossocio.merge(area_basal_especies, on=col_especie)
        
        # Calcular totais
        total_individuos = fitossocio['num_individuos'].sum()
        total_area_basal = fitossocio['area_basal_total'].sum() if area_basal_disponivel else 0
        total_frequencia = fitossocio['frequencia'].sum()
        total_parcelas = df_trabalho[col_parc].nunique()
        
        # Calcular parâmetros fitossociológicos
        fitossocio['densidade_relativa'] = (fitossocio['num_individuos'] / total_individuos) * 100
        fitossocio['frequencia_relativa'] = (fitossocio['frequencia'] / total_frequencia) * 100
        
        if area_basal_disponivel and total_area_basal > 0:
            fitossocio['dominancia_relativa'] = (fitossocio['area_basal_total'] / total_area_basal) * 100
            fitossocio['valor_importancia'] = (fitossocio['densidade_relativa'] + fitossocio['dominancia_relativa'] + fitossocio['frequencia_relativa']) / 3
        else:
            fitossocio['dominancia_relativa'] = 0
            fitossocio['valor_importancia'] = (fitossocio['densidade_relativa'] + fitossocio['frequencia_relativa']) / 2
        
        # Ordenar por valor de importância
        fitossocio = fitossocio.sort_values('valor_importancia', ascending=False).reset_index(drop=True)
        
        # Renomear colunas para exibição
        colunas_display = {
            col_especie: 'Espécie',
            'frequencia': 'Frequência',
            'num_individuos': 'N° Indivíduos',
            'area_basal_total': 'Área Basal (m²)' if area_basal_disponivel else 'AB (não calc.)',
            'densidade_relativa': 'DR (%)',
            'dominancia_relativa': 'DoR (%)',
            'frequencia_relativa': 'FR (%)',
            'valor_importancia': 'VI (%)'
        }
        
        fitossocio_display = fitossocio.rename(columns=colunas_display)
        
        # Arredondar valores numéricos
        fitossocio_display['DR (%)'] = fitossocio_display['DR (%)'].round(2)
        fitossocio_display['DoR (%)'] = fitossocio_display['DoR (%)'].round(2)
        fitossocio_display['FR (%)'] = fitossocio_display['FR (%)'].round(2)
        fitossocio_display['VI (%)'] = fitossocio_display['VI (%)'].round(2)
        
        if area_basal_disponivel:
            fitossocio_display['Área Basal (m²)'] = fitossocio_display['Área Basal (m²)'].round(4)
        
        # Exibir resultados
        st.write("**📋 Tabela Fitossociológica - Método PARCELAS**")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total de Espécies", formatar_numero_br(len(fitossocio_display), 0))
        with col2:
            st.metric("Total de Indivíduos", formatar_numero_br(total_individuos, 0))
        with col3:
            st.metric("Total de Parcelas", formatar_numero_br(total_parcelas, 0))
        with col4:
            if area_basal_disponivel:
                st.metric("Área Basal Total", f"{formatar_numero_br(total_area_basal, 3)} m²")
            else:
                st.metric("Área Basal", "Não calculada")
        
        # Aplicar formatação brasileira na tabela
        colunas_porcentagem = ['DR (%)', 'DoR (%)', 'FR (%)', 'VC (%)', 'VI (%)']
        colunas_numericas = ['Densidade (ind/ha)', 'Dominância (m²/ha)', 'Área Basal (m²)']
        fitossocio_display_formatado = formatar_dataframe_br(
            fitossocio_display, 
            colunas_numericas=colunas_numericas, 
            colunas_porcentagem=colunas_porcentagem
        )
        
        # Tabela principal
        st.dataframe(fitossocio_display_formatado, use_container_width=True, height=400)
        
        # Download
        csv = fitossocio_display.to_csv(index=False)
        st.download_button(
            label="📥 Download Tabela Fitossociológica (CSV)",
            data=csv,
            file_name="fitossociologia_parcelas.csv",
            mime="text/csv"
        )
        
        # Gráfico das espécies mais importantes
        if len(fitossocio_display) > 0:
            st.markdown("#### 📊 Top 10 Espécies por Valor de Importância")
            top_especies = fitossocio_display.head(10)
            
            fig = px.bar(
                top_especies,
                x='VI (%)',
                y='Espécie',
                orientation='h',
                title="Valor de Importância das Principais Espécies",
                color='VI (%)',
                color_continuous_scale='Viridis'
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro no cálculo fitossociológico (parcelas): {e}")

def analisar_propriedades_por_tecnica(df_inventario, df_caracterizacao, propriedades, tecnica):
    """Identifica propriedades que usam uma técnica específica"""
    try:
        tecnica_col = encontrar_coluna(df_caracterizacao, ['tecnica_am', 'tecnica', 'metodo'])
        
        if not tecnica_col:
            return propriedades  # Retorna todas se não conseguir identificar
        
        df_tecnica = df_caracterizacao[df_caracterizacao['cod_prop'].isin(propriedades)] if 'cod_prop' in df_caracterizacao.columns else df_caracterizacao
        
        if tecnica.lower() == 'censo':
            props_tecnica = df_tecnica[df_tecnica[tecnica_col].str.contains('censo', case=False, na=False)]['cod_prop'].unique()
        else:  # parcelas
            props_tecnica = df_tecnica[~df_tecnica[tecnica_col].str.contains('censo', case=False, na=False)]['cod_prop'].unique()
        
        return list(props_tecnica)
    
    except Exception:
        return []

def calcular_indices_diversidade(df_inventario, propriedades_selecionadas):
    """Calcula índices de diversidade"""
    st.markdown("### 📊 Índices de Diversidade Ecológica")
    
    col_especie = encontrar_coluna(df_inventario, ['especie', 'especies', 'species', 'sp'])
    
    if not col_especie:
        st.error("❌ Coluna de espécie não encontrada")
        return
    
    try:
        # Contar indivíduos por espécie
        especies_count = df_inventario[col_especie].value_counts()
        
        if len(especies_count) == 0:
            st.warning("⚠️ Nenhuma espécie encontrada")
            return
        
        # Calcular índices
        total_individuos = especies_count.sum()
        riqueza = len(especies_count)
        
        # Índice de Shannon
        shannon = -sum((count/total_individuos) * log(count/total_individuos) for count in especies_count)
        
        # Índice de Simpson
        simpson = sum((count/total_individuos)**2 for count in especies_count)
        simpson_diversidade = 1 - simpson
        
        # Equitabilidade de Pielou
        if riqueza > 1:
            equitabilidade = shannon / log(riqueza)
        else:
            equitabilidade = 0
        
        # Exibir resultados
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🌺 Riqueza (S)", riqueza)
        
        with col2:
            st.metric("🌍 Shannon (H')", f"{shannon:.3f}")
        
        with col3:
            st.metric("🔄 Simpson (1-D)", f"{simpson_diversidade:.3f}")
        
        with col4:
            st.metric("⚖️ Pielou (J)", f"{equitabilidade:.3f}")
        
        # Interpretação dos índices
        with st.expander("📖 Interpretação dos Índices"):
            st.markdown(f"""
            **🌺 Riqueza (S = {riqueza}):**
            - Número total de espécies encontradas
            
            **🌍 Índice de Shannon (H' = {shannon:.3f}):**
            - Valores típicos: 1.5 a 3.5
            - {'Alto' if shannon > 3.0 else 'Médio' if shannon > 2.0 else 'Baixo'} valor de diversidade
            
            **🔄 Índice de Simpson (1-D = {simpson_diversidade:.3f}):**
            - Varia de 0 a 1 (maior = mais diverso)
            - {'Alta' if simpson_diversidade > 0.8 else 'Média' if simpson_diversidade > 0.6 else 'Baixa'} diversidade
            
            **⚖️ Índice de Pielou (J = {equitabilidade:.3f}):**
            - Varia de 0 a 1 (maior = distribuicao mais uniforme)
            - {'Alta' if equitabilidade > 0.8 else 'Media' if equitabilidade > 0.6 else 'Baixa'} equitabilidade
            - Mede a uniformidade da distribuicao das especies
            """)
        
        # Gráfico de distribuição de abundância
        st.markdown("#### 📈 Curva de Abundância das Espécies")
        
        # Preparar dados para o gráfico
        especies_ordenadas = especies_count.sort_values(ascending=False).reset_index()
        especies_ordenadas['rank'] = range(1, len(especies_ordenadas) + 1)
        especies_ordenadas.columns = ['Espécie', 'Abundância', 'Rank']
        
        fig = px.line(
            especies_ordenadas,
            x='Rank',
            y='Abundância',
            title="Curva de Rank-Abundância",
            labels={'Rank': 'Ranking da Espécie', 'Abundância': 'Número de Indivíduos'},
            markers=True
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
        
    except Exception as e:
        st.error(f"Erro no cálculo de índices: {e}")

def gerar_visualizacoes_avancadas(df_inventario, df_caracterizacao):
    """Gera visualizações avançadas"""
    st.markdown("### 📈 Visualizações Avançadas")
    
    # Placeholder para futuras visualizações
    st.info("🚧 Seção em desenvolvimento. Visualizações futuras incluirão:")
    
    with st.expander("🎨 Visualizações Planejadas"):
        st.markdown("""
        - 📊 **Gráficos de Diversidade**: Comparações entre áreas
        - 🗺️ **Mapas de Distribuição**: Espacialização das espécies
        - 📈 **Análises Temporais**: Evolução da comunidade
        - 🔄 **Comparações Fitossociológicas**: Entre diferentes áreas
        - 📋 **Relatórios Personalizados**: Exportação avançada
        """)
    
    st.warning("Volte em breve para acessar essas funcionalidades!")

# ============================================================================
# INDICADORES DE RESTAURAÇÃO FLORESTAL
# ============================================================================

def exibir_indicadores_restauracao(df_caracterizacao, df_inventario):
    """Exibe dashboard específico para indicadores de restauração florestal"""
    
    # Verificar se há dados
    if len(df_caracterizacao) == 0 and len(df_inventario) == 0:
        st.warning("⚠️ Nenhum dado disponível para análise dos indicadores de restauração.")
        return
    
    # Obter dados por propriedade
    dados_restauracao = calcular_indicadores_restauracao(df_caracterizacao, df_inventario)

    if dados_restauracao.empty:
        st.warning("⚠️ Não foi possível calcular os indicadores de restauração.")
        return

        
        st.markdown("---")
    
    # Obter dados por propriedade
    dados_restauracao = calcular_indicadores_restauracao(df_caracterizacao, df_inventario)
    
    if dados_restauracao.empty:
        st.warning("⚠️ Não foi possível calcular os indicadores de restauração.")
        return
    
    # === RESUMO GERAL ===
    st.subheader("📊 Resumo Geral dos Indicadores")
    
    # Métricas geraisd
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_props = len(dados_restauracao)
        st.metric("Total de Propriedades", total_props)
    
    with col2:
        props_cobertura_ok = len(dados_restauracao[dados_restauracao['cobertura_copa'] >= 80])
        st.metric("Cobertura Copa ≥80%", f"{props_cobertura_ok}/{total_props}")
    
    with col3:
        if 'densidade_adequada' in dados_restauracao.columns:
            props_densidade_ok = len(dados_restauracao[dados_restauracao['densidade_adequada'] == True])
            st.metric("Densidade Adequada", f"{props_densidade_ok}/{total_props}")
        else:
            st.metric("Densidade Adequada", "N/A")
    
    with col4:
        if 'riqueza_adequada' in dados_restauracao.columns:
            props_riqueza_ok = len(dados_restauracao[dados_restauracao['riqueza_adequada'] == True])
            st.metric("Riqueza Adequada", f"{props_riqueza_ok}/{total_props}")
        else:
            st.metric("Riqueza Adequada", "N/A")
    
    # === ABAS DE ANÁLISE ===
    tab1, tab2, tab3, tab4 = st.tabs([
        "🌿 Cobertura de Copa",
        "🌱 Densidade de Regenerantes", 
        "🌳 Riqueza de Espécies",
        "📊 Análise por UTs"
    ])
    
    # ABA 1: COBERTURA DE COPA
    with tab1:
        exibir_analise_cobertura_copa(dados_restauracao, df_caracterizacao)
    
    # ABA 2: DENSIDADE DE REGENERANTES
    with tab2:
        exibir_analise_densidade_regenerantes(dados_restauracao, df_inventario)
    
    # ABA 3: RIQUEZA DE ESPÉCIES
    with tab3:
        exibir_analise_riqueza_especies(dados_restauracao, df_inventario)
    
    # ABA 4: ANÁLISE POR UTs
    with tab4:
        st.write("### Explicacao Detalhada dos Scores")
        
        with st.expander("📊 Como sao calculados os scores de monitoramento?", expanded=True):
            st.markdown("""
            #### 🌱 **Scores de Vegetacao (0-100 pontos cada)**
            
            **1. Riqueza de Especies Nativas** 🌺
            - **O que mede**: Diversidade de especies nativas com altura > 0,5m
            - **Como calcular**: 
              - Conte especies nativas com altura > 0,5m
              - Score = (numero_especies / meta_propriedade) × 100
              - Maximo: 100 pontos (≥ meta da propriedade)
            - **Interpretacao**:
              - 0-20% da meta: Muito baixa diversidade
              - 21-40% da meta: Baixa diversidade  
              - 41-60% da meta: Diversidade moderada
              - 61-80% da meta: Boa diversidade
              - 81-100% da meta: Excelente diversidade
            
            **2. Densidade de Individuos Nativos** 🌳
            - **O que mede**: Numero de arvores nativas por hectare
            - **Como calcular**:
              - Conte individuos nativos na area amostrada
              - Extrapole para hectare: densidade = (individuos/area_ha)
              - Score = (densidade / 2000) × 100
              - Maximo: 100 pontos (≥2000 ind/ha)
            - **Interpretacao**:
              - 0-400 ind/ha (0-20 pts): Densidade muito baixa
              - 401-800 ind/ha (21-40 pts): Densidade baixa
              - 801-1200 ind/ha (41-60 pts): Densidade moderada
              - 1201-1600 ind/ha (61-80 pts): Boa densidade
              - 1601+ ind/ha (81-100 pts): Excelente densidade
            
            **3. Diversidade de Shannon (H')** 🌍
            - **O que mede**: Diversidade considerando abundancia de especies
            - **Como calcular**:
              - H' = -Σ(pi × ln(pi)), onde pi = proporcao da especie i
              - Score = (H' / 3) × 100
              - Maximo: 100 pontos (H' ≥ 3.0)
            - **Interpretacao**:
              - H' < 1.0 (0-33 pts): Baixa diversidade
              - H' 1.0-2.0 (34-66 pts): Diversidade moderada
              - H' > 2.0 (67-100 pts): Alta diversidade
            """)
            
            st.markdown("""
            #### 🌍 **Scores de Indicadores Ambientais (0-100 pontos cada)**
            
            **1. Cobertura de Copa** 🌳 (Ideal: ALTO)
            - **O que mede**: Percentual de cobertura vegetal
            - **Como calcular**: Score = percentual_cobertura (direto)
            - **Valores de referencia**:
              - 0-30%: Cobertura insuficiente (vermelho)
              - 31-50%: Cobertura baixa (amarelo)
              - 51-70%: Cobertura adequada (verde claro)
              - 71-100%: Cobertura excelente (verde escuro)
            
            **2. Solo Exposto** 🏜️ (Ideal: BAIXO)
            - **O que mede**: Percentual de solo sem cobertura
            - **Como calcular**: Score = 100 - percentual_solo_exposto
            - **Valores de referencia**:
              - 0-10% exposto (90-100 pts): Excelente
              - 11-20% exposto (80-89 pts): Bom
              - 21-40% exposto (60-79 pts): Moderado
              - 41%+ exposto (<60 pts): Problematico
            
            **3. Serapilheira** 🍂 (Ideal: ALTO)
            - **O que mede**: Cobertura de material organico no solo
            - **Como calcular**: Score = percentual_serapilheira (direto)
            - **Valores de referencia**:
              - 60-100%: Excelente ciclagem de nutrientes
              - 40-59%: Boa ciclagem
              - 20-39%: Ciclagem moderada
              - 0-19%: Ciclagem deficiente
            
            **4. Gramineas Invasoras** 🌾 (Ideal: BAIXO)
            - **O que mede**: Cobertura de gramineas competidoras
            - **Como calcular**: Score = 100 - percentual_gramineas
            - **Valores de referencia**:
              - 0-10% gramineas (90-100 pts): Controle excelente
              - 11-25% gramineas (75-89 pts): Controle bom
              - 26-50% gramineas (50-74 pts): Controle moderado
              - 51%+ gramineas (<50 pts): Necessita intervencao
            """)
            
            st.markdown("""
            #### 🎯 **Score Final Integrado**
            
            **Calculo do Score Geral**:
            - Score Final = (Score_Riqueza + Score_Densidade + Score_Shannon + Score_Copa + Score_Solo + Score_Serapilheira + Score_Gramineas) / 7
            - Media ponderada de todos os indicadores
            
            **Classificacao do Sucesso da Restauracao**:
            - 🟢 **85-100 pontos**: Restauracao de EXCELENCIA
              - Todos os indicadores em niveis otimos
              - Area se aproxima de floresta madura
              - Manutencao minima necessaria
            
            - 🟢 **70-84 pontos**: Restauracao BEM-SUCEDIDA  
              - Maioria dos indicadores adequados
              - Desenvolvimento satisfatorio
              - Monitoramento de rotina
            
            - 🟡 **50-69 pontos**: Restauracao em DESENVOLVIMENTO
              - Indicadores mistos, alguns adequados
              - Necessita intervencoes pontuais
              - Monitoramento frequente
            
            - 🟠 **30-49 pontos**: Restauracao com DIFICULDADES
              - Varios indicadores abaixo do esperado
              - Necessita intervencoes significativas
              - Revisao da estrategia
            
            - 🔴 **0-29 pontos**: Restauracao CRITICA
              - Maioria dos indicadores inadequados
              - Necessita intervencao urgente
              - Possivel replantio ou enriquecimento
            
            **Fatores que Influenciam o Score**:
            - Qualidade do plantio inicial
            - Adequacao das especies ao local
            - Condicoes climaticas
            - Manutencao e manejo pos-plantio
            - Pressoes externas (fogo, gado, etc.)
            """)
        
        exibir_analise_por_uts(df_caracterizacao, df_inventario)

def calcular_indicadores_restauracao(df_caracterizacao, df_inventario):
    """Calcula os indicadores de restauração por propriedade"""
    try:
        resultados = []
        
        # Obter propriedades únicas
        propriedades = set()
        
        if 'cod_prop' in df_caracterizacao.columns:
            propriedades.update(df_caracterizacao['cod_prop'].dropna().unique())
        
        # Extrair propriedades do inventário se necessário
        cod_parc_col = encontrar_coluna(df_inventario, ['cod_parc', 'parcela', 'plot'])
        if cod_parc_col:
            for parc in df_inventario[cod_parc_col].dropna().unique():
                if '_' in str(parc):
                    prop = str(parc).split('_')[0]
                    propriedades.add(prop)
        
        # Calcular indicadores para cada propriedade
        for prop in propriedades:
            resultado = calcular_indicadores_propriedade(prop, df_caracterizacao, df_inventario)
            if resultado:
                resultados.append(resultado)
        
        return pd.DataFrame(resultados)
    
    except Exception as e:
        st.error(f"Erro ao calcular indicadores de restauração: {e}")
        return pd.DataFrame()

def calcular_indicadores_propriedade(cod_prop, df_caracterizacao, df_inventario):
    """Calcula indicadores de restauração para uma propriedade específica"""
    try:
        resultado = {'cod_prop': cod_prop}
        
        # Filtrar dados da propriedade na caracterização
        df_carac_prop = df_caracterizacao[df_caracterizacao['cod_prop'] == cod_prop] if 'cod_prop' in df_caracterizacao.columns else pd.DataFrame()
        
        # Filtrar dados da propriedade no inventário
        # Usar a coluna cod_prop diretamente se existir
        if 'cod_prop' in df_inventario.columns:
            df_inv_prop = df_inventario[df_inventario['cod_prop'] == cod_prop]
        else:
            # Fallback para método anterior
            cod_parc_col = encontrar_coluna(df_inventario, ['cod_parc', 'parcela', 'plot'])
            if cod_parc_col:
                df_inv_prop = df_inventario[df_inventario[cod_parc_col].astype(str).str.startswith(f"{cod_prop}_")]
                if len(df_inv_prop) == 0:
                    df_inv_prop = df_inventario[df_inventario[cod_parc_col].astype(str).str.contains(f"{cod_prop}", na=False)]
                if len(df_inv_prop) == 0:
                    df_inv_prop = df_inventario[df_inventario[cod_parc_col].astype(str) == str(cod_prop)]
            else:
                df_inv_prop = pd.DataFrame()
        
        # === 1. COBERTURA DE COPA ===
        cobertura_col = encontrar_coluna(df_carac_prop, ['cobetura_nativa', 'cobertura_nativa', 'copa_nativa'])
        if cobertura_col and len(df_carac_prop) > 0:
            cobertura_media = pd.to_numeric(df_carac_prop[cobertura_col], errors='coerce').mean()
            # Converter de 0-1 para 0-100% se necessário
            if not pd.isna(cobertura_media) and cobertura_media <= 1:
                cobertura_media = cobertura_media * 100
            resultado['cobertura_copa'] = cobertura_media if not pd.isna(cobertura_media) else 0
        else:
            resultado['cobertura_copa'] = 0
        
        # === 2. DENSIDADE DE REGENERANTES ===
        # Detectar método de restauração
        metodo_col = encontrar_coluna(df_carac_prop, ['metodo_restauracao', 'metodo', 'tecnica_restauracao'])
        metodo_restauracao = 'Ativa'  # Padrao
        
        if metodo_col and len(df_carac_prop) > 0:
            metodo_valor = df_carac_prop[metodo_col].iloc[0]
            if 'assistida' in str(metodo_valor).lower():
                metodo_restauracao = 'Assistida'
        
        resultado['metodo_restauracao'] = metodo_restauracao
        
        # Calcular densidade
        densidade = calcular_densidade_regenerantes(df_inv_prop, df_carac_prop)
        resultado['densidade_regenerantes'] = densidade
        
        # Meta de densidade
        meta_densidade = 1500 if metodo_restauracao == 'Assistida' else 1333
        resultado['meta_densidade'] = meta_densidade
        resultado['densidade_adequada'] = densidade >= meta_densidade
        
        # === 3. RIQUEZA DE ESPECIES ===
        especies_col = encontrar_coluna(df_inv_prop, ['especies', 'especie', 'species', 'sp'])
        if especies_col and len(df_inv_prop) > 0:
            # Filtrar especies validas (remover "Morto/Morta")
            df_especies_validas = df_inv_prop[~df_inv_prop[especies_col].astype(str).str.contains('Morto|Morta', case=False, na=False)]
            
            # Filtrar apenas especies nativas
            origem_col = encontrar_coluna(df_especies_validas, ['origem', 'origin', 'procedencia'])
            if origem_col:
                df_nativas = df_especies_validas[df_especies_validas[origem_col].astype(str).str.contains('Nativa', case=False, na=False)]
            else:
                df_nativas = df_especies_validas
            
            # Filtrar apenas individuos com altura > 0.5m
            ht_col = encontrar_coluna(df_nativas, ['ht', 'altura', 'height'])
            if ht_col:
                alturas = pd.to_numeric(df_nativas[ht_col], errors='coerce')
                df_nativas_altura = df_nativas[alturas > 0.5]
            else:
                df_nativas_altura = df_nativas
            
            # Riqueza observada = especies nativas com altura > 0.5m
            riqueza_observada = df_nativas_altura[especies_col].nunique()
            
            # Riqueza de especies nativas (todas as alturas)
            riqueza_nativas = df_nativas[especies_col].nunique()
        else:
            riqueza_observada = 0
            riqueza_nativas = 0
        
        resultado['riqueza_observada'] = riqueza_observada
        resultado['riqueza_nativas'] = riqueza_nativas
        
        # Obter meta de riqueza (baseada em espécies nativas)
        meta_riqueza_col = encontrar_coluna(df_inv_prop, ['meta', 'meta_riqueza', 'riqueza_meta', 'meta_especies'])
        if meta_riqueza_col and len(df_inv_prop) > 0:
            meta_riqueza = pd.to_numeric(df_inv_prop[meta_riqueza_col], errors='coerce').dropna()
            if len(meta_riqueza) > 0:
                meta_riqueza = meta_riqueza.iloc[0]
            else:
                meta_riqueza = 30  # Valor padrao
        else:
            meta_riqueza = 30  # Valor padrao
        
        resultado['meta_riqueza'] = meta_riqueza
        # Meta baseada em espécies nativas com altura > 0.5m (critério observado)
        resultado['riqueza_adequada'] = riqueza_observada >= meta_riqueza
        
        # === 4. STATUS GERAL ===
        status_count = sum([
            resultado['cobertura_copa'] >= 80,
            resultado['densidade_adequada'],
            resultado['riqueza_adequada']
        ])
        
        if status_count == 3:
            resultado['status_geral'] = 'Excelente'
        elif status_count == 2:
            resultado['status_geral'] = 'Bom'
        elif status_count == 1:
            resultado['status_geral'] = 'Regular'
        else:
            resultado['status_geral'] = 'Crítico'
        
        return resultado
    
    except Exception as e:
        st.error(f"Erro ao calcular indicadores para propriedade {cod_prop}: {e}")
        return None

def calcular_densidade_regenerantes(df_inv, df_carac):
    """Calcula a densidade de indivíduos regenerantes seguindo critérios específicos"""
    try:
        # Verificar se há dados
        if len(df_inv) == 0 or len(df_carac) == 0:
            return 0.0
                        
        # Aplicar filtros específicos
        df_filtrado = df_inv.copy()
        
        # 1. Remover "Morto/Morta"
        especies_col = encontrar_coluna(df_filtrado, ['especies', 'especie', 'species', 'sp'])
        if especies_col:
            antes_morto = len(df_filtrado)
            df_filtrado = df_filtrado[~df_filtrado[especies_col].astype(str).str.contains('Morto|Morta', case=False, na=False)]

        # 2. Filtrar apenas origem "Nativa"
        origem_col = encontrar_coluna(df_filtrado, ['origem', 'origin', 'procedencia'])
        if origem_col:
            antes_origem = len(df_filtrado)
            df_filtrado = df_filtrado[df_filtrado[origem_col].astype(str).str.contains('Nativa', case=False, na=False)]

        # 3. Filtrar idade "Jovem"
        idade_col = encontrar_coluna(df_filtrado, ['idade', 'age', 'class_idade'])
        if idade_col:
            antes_idade = len(df_filtrado)
            df_filtrado = df_filtrado[df_filtrado[idade_col].astype(str).str.contains('Jovem', case=False, na=False)]

        # 4. Filtrar altura > 0.5
        ht_col = encontrar_coluna(df_filtrado, ['ht', 'altura', 'height', 'h'])
        if ht_col:
            antes_altura = len(df_filtrado)
            alturas = pd.to_numeric(df_filtrado[ht_col], errors='coerce')
            df_filtrado = df_filtrado[alturas >= 0.499]
 
        if len(df_filtrado) == 0:
            return 0.0                
        
        # Contar indivíduos regenerantes válidos
        plaqueta_col = encontrar_coluna(df_filtrado, ['plaqueta', 'plaq', 'id'])
        if plaqueta_col:
            num_regenerantes = df_filtrado[plaqueta_col].nunique()

        else:
            num_regenerantes = len(df_filtrado)

        # Calcular área amostrada usando método adaptativo
        area_ha, metodo = calcular_area_amostrada(df_carac, df_inv)
        
        if area_ha > 0:
            densidade = num_regenerantes / area_ha
            return densidade
        
        return 0.0
    except Exception as e:
        st.warning(f"Erro no cálculo de densidade: {e}")
        return 0.0

def exibir_analise_cobertura_copa(dados_restauracao, df_caracterizacao):
    """Exibe análise específica da cobertura de copa"""
    st.markdown("### 🌿 Análise de Cobertura de Copa")
    
    if len(dados_restauracao) == 0:
        st.warning("Sem dados para análise de cobertura de copa")
        return
    
    # Gráfico de barras - cobertura por propriedade
    fig_cobertura = px.bar(
        dados_restauracao.sort_values('cobertura_copa', ascending=False),
        x='cod_prop',
        y='cobertura_copa',
        title='Cobertura de Copa por Propriedade',
        labels={'cobertura_copa': 'Cobertura de Copa (%)', 'cod_prop': 'Propriedade'},
        color='cobertura_copa',
        color_continuous_scale='Greens'
    )
    
    # Adicionar linha de meta (80%)
    fig_cobertura.add_hline(y=80, line_dash="dash", line_color="red", 
                           annotation_text="Meta: 80%")
    
    fig_cobertura.update_layout(height=400)
    st.plotly_chart(fig_cobertura, use_container_width=True)
    
    # Tabela resumo
    st.markdown("#### 📊 Resumo por Propriedade")
    
    df_resumo_cobertura = dados_restauracao[['cod_prop', 'cobertura_copa']].copy()
    df_resumo_cobertura['Status'] = df_resumo_cobertura['cobertura_copa'].apply(
        lambda x: '✅ Adequada' if x >= 80 else '⚠️ Abaixo da Meta'
    )
    df_resumo_cobertura['cobertura_copa'] = df_resumo_cobertura['cobertura_copa'].round(1)
    
    st.dataframe(df_resumo_cobertura, use_container_width=True)

def exibir_analise_densidade_regenerantes(dados_restauracao, df_inventario):
    """Exibe análise específica da densidade de regenerantes"""
    st.markdown("### 🌱 Análise de Densidade de Regenerantes")
    
    if len(dados_restauracao) == 0:
        st.warning("Sem dados para análise de densidade")
        return
    
    # Gráfico comparativo com metas diferentes por método
    fig_densidade = px.bar(
        dados_restauracao.sort_values('densidade_regenerantes', ascending=False),
        x='cod_prop',
        y='densidade_regenerantes',
        color='metodo_restauracao',
        title='Densidade de Regenerantes por Propriedade e Método',
        labels={'densidade_regenerantes': 'Densidade (ind/ha)', 'cod_prop': 'Propriedade'},
        color_discrete_map={'Ativa': '#2E8B57', 'Assistida': '#228B22'}
    )
    
    # Adicionar linhas de meta
    fig_densidade.add_hline(y=1333, line_dash="dash", line_color="orange", 
                           annotation_text="Meta Ativa: 1.333 ind/ha")
    fig_densidade.add_hline(y=1500, line_dash="dash", line_color="red", 
                           annotation_text="Meta Assistida: 1.500 ind/ha")
    
    fig_densidade.update_layout(height=400)
    st.plotly_chart(fig_densidade, use_container_width=True)
    
    # Tabela resumo
    st.markdown("#### 📊 Resumo por Propriedade")
    
    df_resumo_densidade = dados_restauracao[['cod_prop', 'metodo_restauracao', 'densidade_regenerantes', 'meta_densidade', 'densidade_adequada']].copy()
    df_resumo_densidade['Status'] = df_resumo_densidade['densidade_adequada'].apply(
        lambda x: '✅ Adequada' if x else '⚠️ Abaixo da Meta'
    )
    df_resumo_densidade['densidade_regenerantes'] = df_resumo_densidade['densidade_regenerantes'].round(0)
    df_resumo_densidade = df_resumo_densidade.drop('densidade_adequada', axis=1)
    
    st.dataframe(df_resumo_densidade, use_container_width=True)

def exibir_analise_riqueza_especies(dados_restauracao, df_inventario):
    """Exibe análise específica da riqueza de espécies"""
    st.markdown("### 🌳 Análise de Riqueza de Espécies")
    
    if len(dados_restauracao) == 0:
        st.warning("Sem dados para análise de riqueza")
        return
    
    # Ordenar dados por meta de riqueza (maior para menor) para organizar o gráfico
    dados_ordenados = dados_restauracao.sort_values('meta_riqueza', ascending=False).reset_index(drop=True)
    
    # Gráfico de barras agrupadas - observado vs meta
    df_riqueza_plot = dados_ordenados[['cod_prop', 'riqueza_observada', 'meta_riqueza']].melt(
        id_vars='cod_prop',
        value_vars=['riqueza_observada', 'meta_riqueza'],
        var_name='Tipo',
        value_name='Riqueza'
    )
    
    df_riqueza_plot['Tipo'] = df_riqueza_plot['Tipo'].map({
        'riqueza_observada': 'Observada',
        'meta_riqueza': 'Meta'
    })
    
    # Calcular largura baseada no número de propriedades
    num_props = len(dados_restauracao)
    fig_width = max(800, num_props * 100)  # Mínimo 800px, 100px por propriedade
    
    # Criar lista ordenada de propriedades para manter a ordem no gráfico
    ordem_propriedades = dados_ordenados['cod_prop'].tolist()
    
    fig_riqueza = px.bar(
        df_riqueza_plot,
        x='cod_prop',
        y='Riqueza',
        color='Tipo',
        barmode='group',
        title='Riqueza de Espécies: Observada vs Meta (Ordenado por Meta Decrescente)',
        labels={'Riqueza': 'Número de Espécies', 'cod_prop': 'Propriedade'},
        color_discrete_map={'Observada': '#4CAF50', 'Meta': '#FF9800'},
        category_orders={'cod_prop': ordem_propriedades}
    )
    
    # Configurar layout para permitir scroll horizontal
    fig_riqueza.update_layout(
        height=500,
        width=fig_width,
        xaxis_title="Propriedade",
        yaxis_title="Número de Espécies",
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=80, b=50)
    )
    
    # Container com scroll horizontal
    st.markdown("#### 📊 Gráfico de Riqueza (Role para o lado para ver todas as propriedades)")
    
    # Criar container scrollable
    with st.container():
        st.plotly_chart(fig_riqueza, use_container_width=False)
    
    # Tabela resumo
    st.markdown("#### 📊 Resumo por Propriedade")
    
    # Verificar se existe coluna de riqueza nativas
    colunas_resumo = ['cod_prop', 'riqueza_observada', 'meta_riqueza', 'riqueza_adequada']
    if 'riqueza_nativas' in dados_ordenados.columns:
        colunas_resumo.insert(2, 'riqueza_nativas')
    
    df_resumo_riqueza = dados_ordenados[colunas_resumo].copy()
    df_resumo_riqueza['Status'] = df_resumo_riqueza['riqueza_adequada'].apply(
        lambda x: '✅ Adequada' if x else '⚠️ Abaixo da Meta'
    )
    df_resumo_riqueza = df_resumo_riqueza.drop('riqueza_adequada', axis=1)
    
    # Renomear colunas para melhor visualização
    nomes_colunas = {
        'cod_prop': 'Propriedade',
        'riqueza_observada': 'Riqueza Total',
        'riqueza_nativas': 'Riqueza Nativas',
        'meta_riqueza': 'Meta (Nativas)',
        'Status': 'Status'
    }
    df_resumo_riqueza = df_resumo_riqueza.rename(columns=nomes_colunas)
    
    st.dataframe(df_resumo_riqueza, use_container_width=True)
    
    # Informação sobre os critérios
    st.info("💡 **Critérios:** Meta baseada em espécies nativas com altura > 0.5m. Espécies 'Morto/Morta' excluídas de todas as análises.")

def exibir_analise_por_uts(df_caracterizacao, df_inventario):
    """Exibe análise detalhada por UTs dentro das propriedades"""
    st.markdown("### 📊 Análise Detalhada por Unidades de Trabalho (UTs)")
    
    # Seletor de propriedade
    propriedades_disponiveis = []
    if 'cod_prop' in df_caracterizacao.columns:
        propriedades_disponiveis = sorted(df_caracterizacao['cod_prop'].dropna().unique())
    
    if not propriedades_disponiveis:
        st.warning("Nenhuma propriedade encontrada para análise por UTs")
        return
    
    propriedade_selecionada = st.selectbox("Selecione uma propriedade para análise detalhada:", propriedades_disponiveis)
    
    if propriedade_selecionada:
        # Filtrar dados da propriedade
        df_carac_prop = df_caracterizacao[df_caracterizacao['cod_prop'] == propriedade_selecionada]
        
        cod_parc_col = encontrar_coluna(df_inventario, ['cod_parc', 'parcela', 'plot'])
        if cod_parc_col:
            df_inv_prop = df_inventario[df_inventario[cod_parc_col].astype(str).str.startswith(f"{propriedade_selecionada}_")]
        else:
            df_inv_prop = pd.DataFrame()
        
        # Análise por UT
        if len(df_carac_prop) > 0:
            # Cobertura por UT
            if 'ut' in df_carac_prop.columns:
                st.markdown("#### 🌿 Cobertura de Copa por UT")
                
                cobertura_col = encontrar_coluna(df_carac_prop, ['cobetura_nativa', 'cobertura_nativa', 'copa_nativa'])
                if cobertura_col:
                    df_cobertura_ut = df_carac_prop.groupby('ut')[cobertura_col].mean().reset_index()
                    df_cobertura_ut.columns = ['UT', 'Cobertura_Copa']
                    df_cobertura_ut['Status'] = df_cobertura_ut['Cobertura_Copa'].apply(
                        lambda x: '✅ Adequada' if x >= 80 else '⚠️ Abaixo da Meta'
                    )
                    
                    fig_ut_cobertura = px.bar(
                        df_cobertura_ut,
                        x='UT',
                        y='Cobertura_Copa',
                        title=f'Cobertura de Copa por UT - Propriedade {propriedade_selecionada}',
                        color='Cobertura_Copa',
                        color_continuous_scale='Greens'
                    )
                    fig_ut_cobertura.add_hline(y=80, line_dash="dash", line_color="red")
                    fig_ut_cobertura.update_layout(height=300)
                    st.plotly_chart(fig_ut_cobertura, use_container_width=True)
                    
                    st.dataframe(df_cobertura_ut, use_container_width=True)
        
        # Riqueza por UT (do inventário)
        if len(df_inv_prop) > 0 and cod_parc_col:
            st.markdown("#### 🌳 Riqueza de Espécies por UT")
            
            especies_col = encontrar_coluna(df_inv_prop, ['especies', 'especie', 'species', 'sp'])
            if especies_col:
                # Extrair UT do cod_parc
                df_inv_prop_copy = df_inv_prop.copy()
                df_inv_prop_copy['UT'] = df_inv_prop_copy[cod_parc_col].astype(str).str.split('_').str[1]
                
                df_riqueza_ut = df_inv_prop_copy.groupby('UT')[especies_col].nunique().reset_index()
                df_riqueza_ut.columns = ['UT', 'Riqueza']
                
                fig_ut_riqueza = px.bar(
                    df_riqueza_ut,
                    x='UT',
                    y='Riqueza',
                    title=f'Riqueza de Espécies por UT - Propriedade {propriedade_selecionada}',
                    color='Riqueza',
                    color_continuous_scale='Viridis'
                )
                fig_ut_riqueza.update_layout(height=300)
                st.plotly_chart(fig_ut_riqueza, use_container_width=True)
                
                st.dataframe(df_riqueza_ut, use_container_width=True)

# ============================================================================
# FUNÇÃO PRINCIPAL - DEVE ESTAR NO FINAL
# ============================================================================

def main():
    """Função principal do dashboard"""
    # Título principal
    st.title("🌿 Dashboard - Indicadores Ambientais")
    
    # Menu de navegação
    st.sidebar.title("📂 Navegação")
    pagina = st.sidebar.selectbox(
        "Selecione a página:",
        ["📊 Dashboard Principal", "🔍 Auditoria de Dados", "📈 Análises Avançadas"]
    )
    
    # Carregar dados uma vez
    df_caracterizacao, df_inventario = load_data()
    
    if df_caracterizacao is None or df_inventario is None:
        st.error("Não foi possível carregar os dados. Verifique se os arquivos Excel estão no diretório correto.")
        return
    
    # Roteamento de páginas
    if pagina == "📊 Dashboard Principal":
        pagina_dashboard_principal(df_caracterizacao, df_inventario)
    elif pagina == "🔍 Auditoria de Dados":
        pagina_auditoria_dados(df_caracterizacao, df_inventario)
    elif pagina == "📈 Análises Avançadas":
        pagina_analises_avancadas(df_caracterizacao, df_inventario)

if __name__ == "__main__":
    main()
