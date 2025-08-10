# Dashboard Indicadores Ambientais 🌿

Este projeto é um dashboard interativo criado com Streamlit para análise de dados ambientais de caracterização e inventário.

## 📋 Funcionalidades

### 🧹 **Limpeza e Padronização de Dados**
- **Padronização automática**: Remove espaços desnecessários e corrige formatação
- **Capitalização consistente**: Primeira letra maiúscula, demais minúsculas
- **Tratamento de valores nulos**: Identificação e tratamento adequado de células vazias

### 📊 **Análises Específicas**
- **Estatísticas Descritivas Personalizadas**: 
  - BD_Caracterização: Parcelas, área amostrada, cobertura de copa
  - BD_Inventário: Riqueza, densidade de regenerantes, altura média
- **Indicadores Ambientais**: Análise de cobertura vegetal e distúrbios
- **Distribuição por Categorias**: Grupos funcionais, sucessão, endemismo, etc.

### 🔧 **Filtros Interativos Hierárquicos**
- **Filtros principais**: `cod_prop`, `tecnica`, `UT` (afetam ambos os bancos)
- **Filtros específicos do inventário**: `origem`, `regeneracao`, `idade`
- **Conexão inteligente**: Filtros principais conectam os bancos via `cod_parc`

### 📈 **Visualizações**
- Contagem de plaquetas únicas no BD_inventário
- Gráficos de barras comparativos
- Distribuição por filtros aplicados
- Métricas em tempo real

### 📁 **Exportação e Dados**
- Download dos dados filtrados em CSV
- Visualização de dados brutos
- Interface responsiva e intuitiva

## 🚀 Como executar localmente

1. Clone o repositório:
```bash
git clone <seu-repositorio>
cd dashboard_indicadores
```

2. Crie um ambiente virtual:
```bash
python -m venv .venv
```

3. Ative o ambiente virtual:
- Windows: `.venv\Scripts\activate`
- Linux/Mac: `source .venv/bin/activate`

4. Instale as dependências:
```bash
pip install -r requirements.txt
```

5. Execute o dashboard:
```bash
streamlit run app_indicadores.py
```

## 📊 Estrutura dos Dados

### BD_caracterizacao.xlsx
- Contém dados de caracterização ambiental
- Principais colunas: `cod_prop`, `tecnica`, `UT`, etc.
- Total de registros: ~30.923

### BD_inventario.xlsx
- Contém dados de inventário
- Inclui informações sobre plaquetas, origem, regeneração e idade

## 🌐 Deploy no Streamlit Cloud

1. Faça push do código para o GitHub
2. Acesse [share.streamlit.io](https://share.streamlit.io)
3. Conecte seu repositório GitHub
4. Configure o arquivo principal como `app_indicadores.py`
5. O deploy será feito automaticamente

## 📁 Estrutura do Projeto

```
dashboard_indicadores/
├── app_indicadores.py      # Aplicação principal Streamlit
├── requirements.txt        # Dependências Python
├── README.md              # Este arquivo
├── BD_caracterizacao.xlsx # Banco de dados de caracterização
└── BD_inventario.xlsx     # Banco de dados de inventário
```

## 🛠️ Tecnologias Utilizadas

- **Streamlit**: Framework para criação do dashboard
- **Pandas**: Manipulação e análise de dados
- **Plotly**: Visualizações interativas
- **NumPy**: Computação científica
- **OpenPyXL**: Leitura de arquivos Excel

## 📝 Observações

- Certifique-se de que os arquivos Excel estão no mesmo diretório que o script
- O dashboard detecta automaticamente as colunas disponíveis nos dados
- Os filtros são aplicados dinamicamente conforme a seleção do usuário
