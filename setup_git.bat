@echo off
echo Inicializando repositorio Git...
git init

echo Adicionando arquivos ao Git...
git add .

echo Fazendo commit inicial...
git commit -m "Initial commit: Dashboard Indicadores Ambientais"

echo.
echo ============================================
echo PROXIMO PASSO: CRIAR REPOSITORIO NO GITHUB
echo ============================================
echo.
echo 1. Va para https://github.com/new
echo 2. Crie um novo repositorio chamado 'dashboard-indicadores'
echo 3. Execute os comandos:
echo    git remote add origin https://github.com/SEU_USUARIO/dashboard-indicadores.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo PARA DEPLOY NO STREAMLIT CLOUD:
echo 1. Va para https://share.streamlit.io
echo 2. Conecte com sua conta GitHub
echo 3. Selecione o repositorio 'dashboard-indicadores'
echo 4. Defina app_indicadores.py como arquivo principal
echo.
pause
