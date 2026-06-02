#!/bin/bash
# =============================================================================
# deploy.sh — Deploy do Bolão na Oracle Cloud (Ubuntu)
# Domínio : bolao.ddns.net
# IP      : 147.15.121.9
# HTTPS   : Let's Encrypt (Certbot)
# =============================================================================

set -e  # Para na primeira falha

# ---------------------------------------------------------------------------
# Configurações — edite se necessário
# ---------------------------------------------------------------------------
DOMAIN="bolao.ddns.net"
APP_USER="ubuntu"
APP_DIR="/home/${APP_USER}/bolao"
VENV_DIR="${APP_DIR}/venv"
GUNICORN_SOCKET="/run/gunicorn.sock"
DJANGO_MODULE="bolao.wsgi:application"
WORKERS=3

# ---------------------------------------------------------------------------
# Cores para output
# ---------------------------------------------------------------------------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${GREEN}[INFO]${NC} $1"; }
warning() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error()   { echo -e "${RED}[ERRO]${NC} $1"; exit 1; }

# ---------------------------------------------------------------------------
# 0. Verificações iniciais
# ---------------------------------------------------------------------------
info "Verificando usuário..."
[ "$(id -u)" -eq 0 ] || error "Execute este script como root: sudo bash deploy.sh"

info "Verificando conexão com a internet..."
curl -s --max-time 5 https://google.com > /dev/null || error "Sem conexão com a internet."

# ---------------------------------------------------------------------------
# 1. Atualizar sistema e instalar dependências
# ---------------------------------------------------------------------------
info "Atualizando pacotes do sistema..."
apt-get update -y && apt-get upgrade -y

info "Instalando dependências..."
apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    nginx \
    certbot \
    python3-certbot-nginx \
    git \
    curl \
    build-essential \
    libssl-dev \
    libffi-dev \
    sqlite3

# ---------------------------------------------------------------------------
# 2. Copiar arquivos do projeto
# ---------------------------------------------------------------------------
info "Preparando diretório do projeto em ${APP_DIR}..."

# Se o diretório já existe, faz backup do banco e atualiza
if [ -d "${APP_DIR}" ]; then
    warning "Diretório ${APP_DIR} já existe. Atualizando projeto..."
    # Preservar banco de dados existente
    if [ -f "${APP_DIR}/db.sqlite3" ]; then
        cp "${APP_DIR}/db.sqlite3" "/tmp/db_backup_$(date +%Y%m%d_%H%M%S).sqlite3"
        info "Backup do banco salvo em /tmp/"
    fi
    # Preservar .env existente
    if [ -f "${APP_DIR}/.env" ]; then
        cp "${APP_DIR}/.env" "/tmp/.env_backup"
        info "Backup do .env salvo em /tmp/.env_backup"
    fi
else
    mkdir -p "${APP_DIR}"
fi

# Copia todos os arquivos do projeto (exceto venv, .env e banco)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rsync -av --exclude='venv/' \
          --exclude='.env' \
          --exclude='db.sqlite3' \
          --exclude='__pycache__/' \
          --exclude='*.pyc' \
          --exclude='.git/' \
          --exclude='staticfiles/' \
          "${SCRIPT_DIR}/" "${APP_DIR}/"

# Restaurar .env preservado se existia
if [ -f "/tmp/.env_backup" ]; then
    cp "/tmp/.env_backup" "${APP_DIR}/.env"
    info ".env restaurado."
fi

# ---------------------------------------------------------------------------
# 3. Configurar arquivo .env de produção
# ---------------------------------------------------------------------------
if [ ! -f "${APP_DIR}/.env" ]; then
    info "Criando arquivo .env de produção..."

    # Gerar SECRET_KEY aleatória
    SECRET_KEY=$(python3 -c "import secrets, string; print(''.join(secrets.choice(string.ascii_letters + string.digits + '!@#%^&*(-_=+)') for _ in range(50)))")

    cat > "${APP_DIR}/.env" <<EOF
# ============================================================
# Configurações de Produção — NÃO compartilhe este arquivo
# ============================================================

SECRET_KEY=${SECRET_KEY}
DEBUG=False
ALLOWED_HOSTS=147.15.121.9,${DOMAIN},www.${DOMAIN}

# Banco de dados (SQLite — padrão)
# Para PostgreSQL, ajuste as configurações em settings.py

# E-mail (configure com seu provedor SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seuemail@gmail.com
EMAIL_HOST_PASSWORD=sua_senha_de_app
DEFAULT_FROM_EMAIL=Bolão Copa <seuemail@gmail.com>
EOF

    warning "=========================================================="
    warning " ATENÇÃO: Edite o arquivo ${APP_DIR}/.env"
    warning " e configure as credenciais de e-mail antes de usar!"
    warning "=========================================================="
else
    info ".env já existe — mantendo configurações atuais."
    # Garantir que ALLOWED_HOSTS está correto
    sed -i "s/^ALLOWED_HOSTS=.*/ALLOWED_HOSTS=147.15.121.9,${DOMAIN},www.${DOMAIN}/" "${APP_DIR}/.env"
    sed -i "s/^DEBUG=.*/DEBUG=False/" "${APP_DIR}/.env"
fi

# ---------------------------------------------------------------------------
# 4. Configurar ambiente virtual Python
# ---------------------------------------------------------------------------
info "Configurando ambiente virtual Python..."
if [ ! -d "${VENV_DIR}" ]; then
    python3 -m venv "${VENV_DIR}"
fi

source "${VENV_DIR}/bin/activate"

info "Atualizando pip..."
pip install --upgrade pip wheel setuptools

info "Instalando dependências Python..."
pip install -r "${APP_DIR}/requirements.txt"

info "Instalando Gunicorn e Whitenoise..."
pip install gunicorn whitenoise

deactivate

# ---------------------------------------------------------------------------
# 5. Configurar permissões
# ---------------------------------------------------------------------------
info "Ajustando permissões..."
chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"
chmod -R 755 "${APP_DIR}"
chmod 600 "${APP_DIR}/.env"

# ---------------------------------------------------------------------------
# 6. Django: migrations, collectstatic
# ---------------------------------------------------------------------------
info "Rodando migrations..."
sudo -u "${APP_USER}" "${VENV_DIR}/bin/python" "${APP_DIR}/manage.py" migrate --noinput

info "Coletando arquivos estáticos..."
sudo -u "${APP_USER}" "${VENV_DIR}/bin/python" "${APP_DIR}/manage.py" collectstatic --noinput --clear

info "Ajustando permissões dos arquivos estáticos..."
chmod -R 755 "${APP_DIR}/staticfiles/"
chmod 755 "/home/${APP_USER}/"

# ---------------------------------------------------------------------------
# 7. Configurar Gunicorn como serviço systemd
# ---------------------------------------------------------------------------
info "Configurando serviço Gunicorn..."

cat > /etc/systemd/system/gunicorn.socket <<EOF
[Unit]
Description=Gunicorn Socket

[Socket]
ListenStream=${GUNICORN_SOCKET}

[Install]
WantedBy=sockets.target
EOF

cat > /etc/systemd/system/gunicorn.service <<EOF
[Unit]
Description=Gunicorn — Bolão Django
Requires=gunicorn.socket
After=network.target

[Service]
Type=notify
User=${APP_USER}
Group=www-data
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${VENV_DIR}/bin/gunicorn \\
          --access-logfile /var/log/gunicorn_access.log \\
          --error-logfile  /var/log/gunicorn_error.log \\
          --workers ${WORKERS} \\
          --bind unix:${GUNICORN_SOCKET} \\
          ${DJANGO_MODULE}
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable gunicorn.socket gunicorn.service
systemctl start gunicorn.socket

# ---------------------------------------------------------------------------
# 8. Configurar Nginx (HTTP temporário para obter certificado SSL)
# ---------------------------------------------------------------------------
info "Configurando Nginx (HTTP)..."

cat > /etc/nginx/sites-available/bolao <<EOF
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN} 147.15.121.9;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias ${APP_DIR}/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /media/ {
        alias ${APP_DIR}/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:${GUNICORN_SOCKET};
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
    }
}
EOF

# Ativar site e remover default
ln -sf /etc/nginx/sites-available/bolao /etc/nginx/sites-enabled/bolao
rm -f /etc/nginx/sites-enabled/default

nginx -t || error "Configuração do Nginx inválida!"
systemctl enable nginx
systemctl restart nginx

# ---------------------------------------------------------------------------
# 9. Abrir portas no firewall Oracle Cloud (via iptables / ufw)
# ---------------------------------------------------------------------------
info "Configurando firewall local..."
if command -v ufw &>/dev/null; then
    ufw allow 22/tcp
    ufw allow 80/tcp
    ufw allow 443/tcp
    ufw --force enable
else
    # iptables (fallback para Oracle Linux / Ubuntu sem ufw)
    iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80  -j ACCEPT
    iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
    iptables-save > /etc/iptables/rules.v4 2>/dev/null || true
fi

# ---------------------------------------------------------------------------
# 10. Obter certificado SSL com Certbot (Let's Encrypt)
# ---------------------------------------------------------------------------
info "Obtendo certificado SSL para ${DOMAIN}..."
warning "Certifique-se de que o DNS bolao.ddns.net aponta para 147.15.121.9 antes de continuar."
echo ""
read -rp "O DNS já está propagado e aponta para 147.15.121.9? (s/n): " DNS_OK
DNS_OK=$(echo "${DNS_OK}" | tr '[:upper:]' '[:lower:]')

if [ "${DNS_OK}" = "s" ]; then
    certbot --nginx \
            -d "${DOMAIN}" \
            --non-interactive \
            --agree-tos \
            --email "seuemail@gmail.com" \
            --redirect

    info "Certificado SSL obtido com sucesso!"

    # Renovação automática
    systemctl enable certbot.timer 2>/dev/null || \
    (crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet && systemctl reload nginx") | crontab -

    info "Renovação automática do SSL configurada."
else
    warning "Pulando SSL por agora. Rode manualmente depois:"
    warning "  sudo certbot --nginx -d ${DOMAIN} --email seuemail@gmail.com --redirect"
fi

# ---------------------------------------------------------------------------
# 11. Configuração HTTPS final do Nginx (reescreve após certbot)
# ---------------------------------------------------------------------------
if [ "${DNS_OK}" = "s" ]; then
    info "Atualizando Nginx com configuração HTTPS completa..."

    cat > /etc/nginx/sites-available/bolao <<EOF
# Redirecionar HTTP → HTTPS
server {
    listen 80;
    server_name ${DOMAIN} www.${DOMAIN};
    return 301 https://\$host\$request_uri;
}

# HTTPS
server {
    listen 443 ssl;
    server_name ${DOMAIN} www.${DOMAIN};

    ssl_certificate     /etc/letsencrypt/live/${DOMAIN}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/${DOMAIN}/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    # Segurança
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options            DENY                                  always;
    add_header X-Content-Type-Options     nosniff                               always;
    add_header Referrer-Policy            "strict-origin-when-cross-origin"     always;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias ${APP_DIR}/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    location /media/ {
        alias ${APP_DIR}/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:${GUNICORN_SOCKET};
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_read_timeout 60s;
    }

    # Tamanho máximo de upload
    client_max_body_size 10M;
}
EOF

    nginx -t && systemctl reload nginx
fi

# ---------------------------------------------------------------------------
# 12. Reiniciar serviços
# ---------------------------------------------------------------------------
info "Reiniciando serviços..."
systemctl restart gunicorn.socket gunicorn.service
systemctl reload nginx

# ---------------------------------------------------------------------------
# 13. Status final
# ---------------------------------------------------------------------------
echo ""
echo -e "${GREEN}============================================================${NC}"
echo -e "${GREEN}  Deploy concluído com sucesso!${NC}"
echo -e "${GREEN}============================================================${NC}"
echo ""
echo -e "  Projeto   : ${APP_DIR}"
echo -e "  Site HTTP : http://${DOMAIN}"
if [ "${DNS_OK}" = "s" ]; then
echo -e "  Site HTTPS: https://${DOMAIN}  ✓"
fi
echo ""
echo -e "  Logs do Gunicorn:"
echo -e "    Acesso : /var/log/gunicorn_access.log"
echo -e "    Erros  : /var/log/gunicorn_error.log"
echo ""
echo -e "  Comandos úteis:"
echo -e "    sudo systemctl status gunicorn"
echo -e "    sudo systemctl restart gunicorn"
echo -e "    sudo systemctl status nginx"
echo -e "    sudo journalctl -u gunicorn --no-pager -n 50"
echo ""
warning "LEMBRE-SE: Edite ${APP_DIR}/.env com suas credenciais de e-mail reais!"
echo ""

# ---------------------------------------------------------------------------
# NOTAS IMPORTANTES — Oracle Cloud
# ---------------------------------------------------------------------------
# Além do firewall do SO, você DEVE abrir as portas 80 e 443 nas
# "Security Lists" (ou "Network Security Groups") da Oracle Cloud:
#
#   Oracle Cloud Console → Networking → Virtual Cloud Networks
#   → sua VCN → Security Lists → Default Security List
#   → Add Ingress Rules:
#       Source CIDR: 0.0.0.0/0  |  Protocol: TCP  |  Port: 80
#       Source CIDR: 0.0.0.0/0  |  Protocol: TCP  |  Port: 443
# ---------------------------------------------------------------------------
