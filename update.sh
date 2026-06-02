#!/bin/bash
# =============================================================================
# update.sh — Atualiza o Bolão no servidor sem conflitos de git
# =============================================================================

set -e

APP_DIR="/home/ubuntu/bolao"
VENV_DIR="${APP_DIR}/venv"

GREEN='\033[0;32m'
NC='\033[0m'
info() { echo -e "${GREEN}[INFO]${NC} $1"; }

cd "${APP_DIR}"

info "Baixando atualizações do repositório..."
git fetch origin master
git reset --hard origin/master

info "Instalando dependências Python..."
source "${VENV_DIR}/bin/activate"
pip install -r requirements.txt --quiet

info "Rodando migrations..."
python manage.py migrate --noinput

info "Coletando arquivos estáticos..."
python manage.py collectstatic --noinput --clear

deactivate

info "Ajustando permissões..."
chmod -R 755 "${APP_DIR}/staticfiles/"
chmod 755 "/home/ubuntu/"

info "Reiniciando Gunicorn..."
systemctl restart gunicorn

info "✅ Atualização concluída!"
