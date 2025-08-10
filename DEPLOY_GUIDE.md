# 🚀 Guia de Deploy - Dashboard Indicadores Ambientais

## Passo 1: Criar Repositório no GitHub

1. Acesse [GitHub](https://github.com) e faça login
2. Clique em "New repository" ou vá para https://github.com/new
3. Configure o repositório:
   - **Repository name**: `dashboard-indicadores`
   - **Description**: `Dashboard interativo para análise de indicadores ambientais`
   - **Visibility**: Public (recomendado para Streamlit Cloud gratuito)
   - **Initialize**: Não marque nenhuma opção (já temos os arquivos)

4. Clique em "Create repository"

## Passo 2: Conectar Repositório Local com GitHub

Execute os seguintes comandos no terminal (substitua `SEU_USUARIO` pelo seu username do GitHub):

```bash
git remote add origin https://github.com/SEU_USUARIO/dashboard-indicadores.git
git branch -M main
git push -u origin main
```

## Passo 3: Deploy no Streamlit Cloud

1. Acesse [Streamlit Cloud](https://share.streamlit.io)
2. Clique em "Sign in with GitHub" e autorize a conexão
3. Clique em "New app"
4. Configure o deploy:
   - **Repository**: Selecione `SEU_USUARIO/dashboard-indicadores`
   - **Branch**: `main`
   - **Main file path**: `app_indicadores.py`
   - **App URL** (opcional): `dashboard-indicadores` ou escolha outro nome

5. Clique em "Deploy!"

## Passo 4: Aguardar Deploy

- O Streamlit Cloud irá:
  1. Clonar o repositório
  2. Instalar as dependências do `requirements.txt`
  3. Executar a aplicação
  4. Fornecer uma URL pública

## 🔧 Solução de Problemas

### Erro: "File not found"
- Verifique se os arquivos Excel estão no repositório
- Confirme que o nome dos arquivos está correto

### Erro: "Module not found"
- Verifique se todas as dependências estão no `requirements.txt`
- Confirme as versões das bibliotecas

### Erro: "Permission denied"
- Verifique se o repositório é público
- Confirme as permissões de acesso no GitHub

## 📊 URLs Importantes

Após o deploy, você terá:
- **URL do Dashboard**: `https://SEU_APP_NAME.streamlit.app`
- **Repositório GitHub**: `https://github.com/SEU_USUARIO/dashboard-indicadores`
- **Logs do Deploy**: Disponíveis no painel do Streamlit Cloud

## 🔄 Atualizações

Para fazer mudanças no dashboard:
1. Edite os arquivos localmente
2. Faça commit das mudanças: `git add . && git commit -m "Sua mensagem"`
3. Faça push: `git push origin main`
4. O Streamlit Cloud fará redeploy automaticamente

## 📱 Compartilhamento

Após o deploy, você pode compartilhar o dashboard através da URL pública gerada pelo Streamlit Cloud.
