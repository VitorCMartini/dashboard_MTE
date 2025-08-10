import pandas as pd
import numpy as np

# Simular dados com problemas
data_test = {
    'especie': ['   MIMOSA pudica  ', 'cecropia HOLOLEUCA   ', '  EUGENIA uniflora'],
    'origem': ['NATIVA  ', '  exotica', 'NATIVA   '],
    'idade': ['  jovem ', 'ADULTA  ', '  Jovem  '],
    'altura': [1.5, 2.8, 0.3]
}

df_test = pd.DataFrame(data_test)

print("DADOS ORIGINAIS:")
print(df_test)
print("\nTipos de dados:")
print(df_test.dtypes)

# Aplicar função de limpeza
def limpar_e_padronizar_dados(df):
    """
    Limpa e padroniza os dados do DataFrame:
    1. Remove espaços desnecessários
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

df_limpo = limpar_e_padronizar_dados(df_test)

print("\n" + "="*50)
print("DADOS APÓS LIMPEZA:")
print(df_limpo)
print("\nTipos de dados:")
print(df_limpo.dtypes)
