#!/usr/bin/env python3
"""
Script para verificação rápida das áreas amostradas por cod_prop e UT
Execute no terminal: python verificar_areas.py
"""

import pandas as pd
import numpy as np
from pathlib import Path

def limpar_e_padronizar_dados(df):
    """Limpa e padroniza os dados do DataFrame"""
    df_limpo = df.copy()
    
    # Limpar strings: remover espaços extras e converter para minúsculas
    for col in df_limpo.select_dtypes(include=['object']).columns:
        if df_limpo[col].dtype == 'object':
            df_limpo[col] = df_limpo[col].astype(str).str.strip().str.lower()
    
    return df_limpo

def encontrar_coluna(df, nomes_possiveis):
    """Encontra uma coluna no DataFrame baseado em uma lista de nomes possíveis"""
    colunas_df = [col.lower().strip() for col in df.columns]
    
    for nome in nomes_possiveis:
        nome_limpo = nome.lower().strip()
        if nome_limpo in colunas_df:
            # Retorna o nome original da coluna
            idx = colunas_df.index(nome_limpo)
            return df.columns[idx]
    
    return None

def calcular_area_amostrada_inventario(df_inventario, cod_prop_filtrado=None, ut_filtrada=None):
    """
    Calcula a área amostrada usando o BD_inventário.
    Como cada UT tem área repetida para cada indivíduo, fazemos desduplicação por UT.
    """
    df_trabalho = df_inventario.copy()
    
    # Encontrar colunas necessárias
    col_parc = encontrar_coluna(df_trabalho, ['cod_parc', 'codigo_parcela', 'parcela'])
    col_area = encontrar_coluna(df_trabalho, ['area_ha', 'area'])
    
    if not col_parc or not col_area:
        return 0, f"Colunas não encontradas - parcela: {col_parc}, area: {col_area}"
    
    # Converter para string para garantir compatibilidade
    df_trabalho[col_parc] = df_trabalho[col_parc].astype(str)
    
    # Verificar se já existem as colunas extraídas ou se precisamos extrair
    if 'cod_prop_extraido' not in df_trabalho.columns or 'ut_extraido' not in df_trabalho.columns:
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
                return 0, "Não foi possível identificar cod_prop e UT"
    
    # Aplicar filtros se fornecidos
    if cod_prop_filtrado:
        df_trabalho = df_trabalho[df_trabalho['cod_prop_extraido'] == cod_prop_filtrado.lower()]
    
    if ut_filtrada:
        df_trabalho = df_trabalho[df_trabalho['ut_extraido'] == ut_filtrada.lower()]
    
    if df_trabalho.empty:
        return 0, "Dados filtrados resultaram em conjunto vazio"
    
    # Desduplicar por UT - pegar apenas um registro por UT (já que área se repete)
    df_unico = df_trabalho.groupby(['cod_prop_extraido', 'ut_extraido']).agg({
        col_area: 'first',  # Pega o primeiro valor (todos são iguais)
        col_parc: 'count'   # Conta quantos indivíduos tem na UT
    }).reset_index()
    
    # Calcular área total
    area_total = df_unico[col_area].sum()
    num_uts = len(df_unico)
    num_individuos = df_unico[col_parc].sum()
    
    metodo = f"BD_Inventário ({num_uts} UTs, {num_individuos} indivíduos total)"
    
    return area_total, metodo

def main():
    """Função principal para verificar as áreas amostradas"""
    
    print("=" * 80)
    print("VERIFICAÇÃO DE ÁREAS AMOSTRADAS")
    print("=" * 80)
    
    # Carregar dados
    try:
        caracterizacao = pd.read_excel('BD_caracterizacao.xlsx')
        inventario = pd.read_excel('BD_inventario.xlsx')
        print(f"✓ BD_caracterizacao carregado: {len(caracterizacao)} registros")
        print(f"✓ BD_inventario carregado: {len(inventario)} registros")
    except Exception as e:
        print(f"❌ Erro ao carregar dados: {e}")
        return
    
    # Limpar e padronizar dados
    caracterizacao = limpar_e_padronizar_dados(caracterizacao)
    inventario = limpar_e_padronizar_dados(inventario)
    
    print("\n" + "=" * 80)
    print("RESUMO GERAL POR PROPRIEDADE")
    print("=" * 80)
    
    # Obter lista única de propriedades do BD_inventário
    col_parc = encontrar_coluna(inventario, ['cod_parc', 'codigo_parcela', 'parcela'])
    
    if not col_parc:
        print("❌ Erro: Coluna de código da parcela não encontrada no inventário")
        return
    
    # Extrair propriedades do cod_parc (formato: PROP_UT)
    # Primeiro converter para string para garantir que funcione com .str
    inventario[col_parc] = inventario[col_parc].astype(str)
    
    # Verificar se o formato tem underscore (PROP_UT) ou se é apenas código
    amostra_parc = inventario[col_parc].iloc[0] if len(inventario) > 0 else ""
    
    if '_' in str(amostra_parc):
        # Formato PROP_UT
        inventario['cod_prop_extraido'] = inventario[col_parc].str.split('_').str[0]
        inventario['ut_extraido'] = inventario[col_parc].str.split('_').str[1]
    else:
        # Se não tem underscore, pode ser que cod_parc seja apenas o código da propriedade
        # ou que tenha um formato diferente
        print(f"⚠️  Formato de cod_parc não reconhecido. Exemplo: {amostra_parc}")
        print("   Tentando outras abordagens...")
        
        # Verificar se existe uma coluna separada para UT
        col_ut = encontrar_coluna(inventario, ['ut', 'unidade_trabalho', 'UT'])
        col_prop = encontrar_coluna(inventario, ['cod_prop', 'codigo_propriedade', 'propriedade'])
        
        if col_prop and col_ut:
            print(f"   ✓ Encontradas colunas separadas: {col_prop} e {col_ut}")
            inventario['cod_prop_extraido'] = inventario[col_prop].astype(str)
            inventario['ut_extraido'] = inventario[col_ut].astype(str)
        else:
            print(f"   ❌ Não foi possível identificar cod_prop e UT no inventário")
            print(f"   Colunas disponíveis: {list(inventario.columns)}")
            return
    
    props_inventario = set(inventario['cod_prop_extraido'].unique())
    todas_props = sorted(props_inventario)
    
    resultado_geral = []
    
    for prop in todas_props:
        print(f"\n📊 PROPRIEDADE: {prop.upper()}")
        print("-" * 50)
        
        # Dados do inventário para esta propriedade
        dados_prop = inventario[inventario['cod_prop_extraido'] == prop]
        
        if dados_prop.empty:
            print(f"   ⚠️  Sem dados de inventário para {prop}")
            continue
        
        # Obter UTs únicas desta propriedade
        uts_unicas = sorted(dados_prop['ut_extraido'].unique())
        
        area_total_prop = 0
        
        for ut in uts_unicas:
            area_ut, metodo = calcular_area_amostrada_inventario(inventario, prop, ut)
            area_total_prop += area_ut
            
            print(f"   UT {ut.upper()}: {area_ut:.4f} ha ({metodo})")
            
            resultado_geral.append({
                'cod_prop': prop.upper(),
                'ut': ut.upper(),
                'area_amostrada_ha': area_ut,
                'metodo_calculo': metodo
            })
        
        print(f"   💡 TOTAL PROPRIEDADE {prop.upper()}: {area_total_prop:.4f} ha")
    
    print("\n" + "=" * 80)
    print("ANÁLISE DE CONSISTÊNCIA DO BD_INVENTÁRIO")
    print("=" * 80)
    
    # Verificar se as áreas são consistentes dentro de cada UT
    col_area = encontrar_coluna(inventario, ['area_ha', 'area'])
    if col_area and col_parc:
        print("\n🔍 Verificando consistência de áreas por UT:")
        
        # Agrupar por UT e verificar se todas as áreas são iguais
        verificacao = inventario.groupby(['cod_prop_extraido', 'ut_extraido']).agg({
            col_area: ['min', 'max', 'count', 'nunique']
        }).round(8)
        
        verificacao.columns = ['area_min', 'area_max', 'num_individuos', 'valores_unicos']
        verificacao['consistente'] = verificacao['valores_unicos'] == 1
        
        inconsistentes = verificacao[~verificacao['consistente']]
        
        if len(inconsistentes) > 0:
            print(f"   ⚠️  ATENÇÃO: {len(inconsistentes)} UTs com áreas inconsistentes:")
            for (prop, ut), row in inconsistentes.iterrows():
                print(f"      {prop}_{ut}: min={row['area_min']:.8f}, max={row['area_max']:.8f}")
        else:
            print(f"   ✓ Todas as {len(verificacao)} UTs têm áreas consistentes")
        
        print(f"\n📊 Resumo total:")
        print(f"   Total de indivíduos: {verificacao['num_individuos'].sum()}")
        print(f"   Total de UTs: {len(verificacao)}")
        print(f"   Área total: {verificacao['area_min'].sum():.4f} ha")
    
    print("\n" + "=" * 80)
    print("DETALHAMENTO POR PROPRIEDADE")
    print("=" * 80)
    
    # Mostrar detalhes por propriedade
    for prop in todas_props:
        dados_prop = inventario[inventario['cod_prop_extraido'] == prop]
        if not dados_prop.empty:
            print(f"\n🏠 {prop.upper()}:")
            uts_prop = dados_prop.groupby('ut_extraido').agg({
                col_parc: 'count',
                col_area: 'first'
            }).round(4)
            uts_prop.columns = ['num_individuos', 'area_ha']
            
            for ut, row in uts_prop.iterrows():
                print(f"   UT {ut}: {row['num_individuos']} indivíduos, {row['area_ha']} ha")
            
            print(f"   TOTAL: {uts_prop['num_individuos'].sum()} indivíduos, {uts_prop['area_ha'].sum():.4f} ha")
    
    # Remover as seções antigas que dependiam do BD_caracterização
    
    # Salvar resultado em CSV para análise posterior
    if resultado_geral:
        df_resultado = pd.DataFrame(resultado_geral)
        df_resultado.to_csv('relatorio_areas_verificacao.csv', index=False, encoding='utf-8-sig')
        print(f"\n💾 Relatório salvo em: relatorio_areas_verificacao.csv")
        print(f"   Total de registros: {len(df_resultado)}")
    
    print("\n" + "=" * 80)
    print("VERIFICAÇÃO CONCLUÍDA!")
    print("=" * 80)

if __name__ == "__main__":
    main()
