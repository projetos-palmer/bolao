# PRD — Sistema de Bolão Online da Copa do Mundo

## 1. Visão geral

O sistema **Bolão Online** será uma aplicação web responsiva para criação, gerenciamento e participação em bolões de jogos da Copa do Mundo. O administrador cadastra partidas, valores de participação, regras de premiação, Pix de recebimento e configurações de e-mail. O usuário se cadastra, confirma seu e-mail, cria senha segura, informa seus dados de Pix, participa dos bolões, acompanha suas apostas e consulta resultados.

O projeto será desenvolvido em **Python + Django**, utilizando **CBV**, banco **SQLite**, frontend com **Tailwind CSS**, telas em **português do Brasil**, templates com **CSRF token**, layout responsivo e experiência visual com tema de futebol.

> Observação importante: como o sistema envolve cobrança, premiação e apostas/bolão com dinheiro, antes de produção real deve haver validação jurídica, fiscal, LGPD e regulatória. No Brasil, apostas de quota fixa exigem autorização prévia da Secretaria de Prêmios e Apostas do Ministério da Fazenda. Para pagamentos Pix automáticos, será necessário usar uma instituição/provedor de pagamento autorizado e APIs homologadas.

---

## 2. Objetivos do produto

### 2.1 Objetivo principal

Criar uma plataforma de bolão online para jogos da Copa do Mundo, permitindo que usuários cadastrados realizem palpites mediante pagamento via Pix, concorram a prêmios configurados pelo administrador e acompanhem seus jogos, resultados e premiações.

### 2.2 Objetivos específicos

- Permitir cadastro seguro de usuários com CPF, nome completo, telefone e e-mail.
- Enviar e-mail de confirmação para ativação da conta.
- Permitir criação de senha somente após confirmação de e-mail.
- Validar CPF, telefone, e-mail e senha forte.
- Permitir que o usuário cadastre seus dados Pix para recebimento.
- Permitir que o administrador cadastre partidas e configure bolões.
- Permitir configuração do valor da participação e percentual de premiação.
- Bloquear palpites após o limite de 5 minutos antes do início da partida.
- Bloquear alteração do palpite após confirmação.
- Permitir múltiplas participações do mesmo usuário no mesmo jogo.
- Confirmar pagamento Pix antes de liberar o palpite no bolão.
- Calcular automaticamente ganhadores e valores de premiação.
- Gerar relatório PDF com total arrecadado, ganhadores, valores e pagamentos.
- Criar interface moderna, responsiva e intuitiva com tema de futebol.

---

## 3. Escopo do sistema

### 3.1 Dentro do escopo

- Projeto Django com pasta principal chamada `bolao`.
- Ambiente virtual `venv`.
- Arquivo `requirements.txt`.
- Arquivo `.gitignore`.
- Banco SQLite.
- Apps separados por responsabilidade.
- Interface responsiva com Tailwind CSS.
- Templates HTML prontos para acesso.
- CBV em todas as telas CRUD e fluxos principais.
- Login, logout, cadastro, confirmação de e-mail e criação de senha.
- Página personalizada de erro 404.
- Painel administrativo customizado para configuração do sistema.
- Cadastro de jogos, bolões, valores, premiações e resultados.
- Cadastro de Pix do administrador.
- Cadastro de Pix do usuário.
- Controle de pagamento por Pix.
- Controle de participação no bolão.
- Relatórios em PDF.
- Mensagens visuais de sucesso, erro, alerta e confirmação.

### 3.2 Fora do escopo inicial

- Aplicativo mobile nativo.
- Streaming de jogos.
- Integração automática com tabela oficial da FIFA no MVP.
- Integração direta com jogadores convocados no MVP, salvo importação manual ou futura API.
- Pagamento Pix automático real sem contratação/homologação de provedor financeiro.
- Operação pública comercial sem análise jurídica e autorização regulatória.

---

## 4. Stack técnica

### 4.1 Backend

- Python 3.12 ou superior.
- Django 6.0 ou superior.
- SQLite para desenvolvimento e primeira versão.
- Django CBV.
- Django Auth customizado.
- Django messages.
- Django forms.
- Django admin apenas como apoio interno.
- Painel administrativo próprio para o gestor do bolão.

### 4.2 Frontend

- HTML5.
- Tailwind CSS.
- JavaScript leve para máscaras, alertas, contadores e animações.
- Ícones com Lucide, Heroicons, Font Awesome ou biblioteca equivalente.
- Animações CSS com tema de futebol.
- Layout mobile first.

### 4.3 Bibliotecas sugeridas

Arquivo `requirements.txt`:

```txt
Django>=6.0,<6.1
python-decouple>=3.8
Pillow>=11.0.0
reportlab>=4.2.0
weasyprint>=62.0
validate-docbr>=1.10.0
django-widget-tweaks>=1.5.0
django-tailwind>=3.8.0
django-browser-reload>=1.13.0
qrcode>=7.4.2
requests>=2.32.0
```

Observações:

- `validate-docbr`: validação de CPF.
- `reportlab` ou `weasyprint`: geração de PDF.
- `qrcode`: geração de QR Code Pix.
- `requests`: futura integração com APIs de pagamento.
- `python-decouple`: variáveis sensíveis em `.env`.

---

## 5. Estrutura sugerida do projeto

```txt
bolao/
├── venv/
├── manage.py
├── requirements.txt
├── .gitignore
├── .env
├── bolao/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── contas/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── tokens.py
│   └── admin.py
├── usuarios/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── jogos/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── boloes/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── services.py
│   └── admin.py
├── pagamentos/
│   ├── models.py
│   ├── forms.py
│   ├── views.py
│   ├── urls.py
│   ├── pix.py
│   └── admin.py
├── relatorios/
│   ├── views.py
│   ├── urls.py
│   └── services.py
├── painel/
│   ├── views.py
│   ├── urls.py
│   └── admin.py
├── templates/
│   ├── base.html
│   ├── 404.html
│   ├── contas/
│   │   ├── login.html
│   │   ├── logout.html
│   │   ├── cadastro.html
│   │   ├── confirmar_email.html
│   │   ├── criar_senha.html
│   │   └── email_confirmacao.html
│   ├── usuarios/
│   │   ├── perfil.html
│   │   └── pix_form.html
│   ├── jogos/
│   │   ├── jogo_list.html
│   │   ├── jogo_form.html
│   │   └── jogo_detail.html
│   ├── boloes/
│   │   ├── bolao_list.html
│   │   ├── bolao_detail.html
│   │   ├── participar.html
│   │   ├── meus_jogos.html
│   │   └── resultado.html
│   ├── pagamentos/
│   │   ├── pagamento_pix.html
│   │   └── pagamento_confirmado.html
│   ├── painel/
│   │   ├── dashboard.html
│   │   ├── configuracao_pix.html
│   │   └── configuracao_email.html
│   └── relatorios/
│       └── relatorio_bolao.html
├── static/
│   ├── css/
│   ├── js/
│   ├── img/
│   │   ├── campo.svg
│   │   ├── bola.svg
│   │   ├── gol.svg
│   │   ├── rede.svg
│   │   └── selecoes/
│   └── icons/
└── media/
```

---

## 6. Arquivo `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtualenv
venv/
.env
.env.*

# Django
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
media/
staticfiles/

# IDEs
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Node/Tailwind
node_modules/
package-lock.json
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# PDF/exports temporários
exports/
relatorios_gerados/
*.pdf
```

---

## 7. Comandos iniciais do projeto

```bash
mkdir bolao
cd bolao
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

pip install --upgrade pip
pip install Django python-decouple Pillow reportlab weasyprint validate-docbr django-widget-tweaks django-tailwind django-browser-reload qrcode requests
pip freeze > requirements.txt

django-admin startproject bolao .
python manage.py startapp contas
python manage.py startapp usuarios
python manage.py startapp jogos
python manage.py startapp boloes
python manage.py startapp pagamentos
python manage.py startapp relatorios
python manage.py startapp painel

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

---

## 8. Configurações gerais do Django

### 8.1 Idioma e timezone

```python
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True
```

### 8.2 Segurança

- Todos os formulários HTML devem usar `{% csrf_token %}`.
- Usar variáveis sensíveis em `.env`.
- Validar permissões por usuário.
- Proteger páginas internas com `LoginRequiredMixin`.
- Proteger páginas administrativas com `UserPassesTestMixin` ou permissões específicas.
- Sanitizar uploads e entradas do usuário.
- Usar HTTPS em produção.

---

## 9. Perfis de usuários

### 9.1 Usuário comum

Pode:

- Criar cadastro.
- Confirmar e-mail.
- Criar senha.
- Fazer login e logout.
- Cadastrar dados Pix de recebimento.
- Visualizar bolões disponíveis.
- Participar de bolões.
- Realizar pagamento Pix.
- Acompanhar status do pagamento.
- Conferir meus jogos.
- Ver resultados e premiações.

Não pode:

- Alterar palpite após salvo.
- Participar após o horário limite.
- Acessar painel administrativo.
- Alterar valores dos bolões.

### 9.2 Administrador

Pode:

- Configurar e-mail remetente do sistema.
- Configurar Pix/banco de recebimento.
- Cadastrar seleções.
- Cadastrar jogos.
- Cadastrar bolões.
- Definir valor de participação.
- Definir percentual de premiação de 0% a 100%.
- Confirmar pagamentos.
- Encerrar partidas.
- Informar resultado final.
- Gerar ganhadores.
- Realizar pagamentos aos ganhadores via integração Pix.
- Gerar relatórios em PDF.

---

## 10. Regras de cadastro do usuário

### 10.1 Campos obrigatórios

- CPF.
- Nome completo.
- Telefone.
- E-mail.

### 10.2 Validações

CPF:

- Obrigatório.
- Único.
- Formato: `000.000.000-00`.
- Deve ser CPF válido.

Telefone:

- Obrigatório.
- Formato: `(00) 99999-9999`.

E-mail:

- Obrigatório.
- Único.
- Deve receber link de confirmação.

Nome completo:

- Obrigatório.
- Mínimo de duas palavras.

### 10.3 Fluxo de ativação

1. Usuário preenche cadastro.
2. Sistema salva usuário como inativo.
3. Sistema envia e-mail com link seguro de confirmação.
4. Usuário clica no link.
5. Sistema redireciona para tela de criação de senha.
6. Usuário cria senha forte.
7. Sistema ativa conta.
8. Usuário pode fazer login.

### 10.4 Regra de senha

A senha deve ter:

- No mínimo 6 caracteres.
- Pelo menos 1 letra maiúscula.
- Pelo menos 1 letra minúscula.
- Pelo menos 1 número.

---

## 11. Login, logout e autenticação

### 11.1 Tela de login

Campos:

- E-mail ou CPF.
- Senha.

Ações:

- Entrar.
- Criar conta.
- Esqueci minha senha.

### 11.2 Logout

- Deve encerrar a sessão.
- Redirecionar para tela de login.
- Exibir mensagem: `Você saiu da plataforma com segurança.`

### 11.3 Páginas protegidas

Todas as páginas internas devem exigir login:

- Painel do usuário.
- Meus jogos.
- Participar do bolão.
- Dados Pix.
- Pagamentos.
- Resultados pessoais.

---

## 12. Cadastro de Pix do usuário

### 12.1 Campos obrigatórios

- Tipo de chave Pix.
- Chave Pix.
- Nome do recebedor.
- Banco.

### 12.2 Tipos de chave Pix permitidos

- Chave aleatória.
- CPF.
- Telefone.
- E-mail.

### 12.3 Validações

CPF:

- Formato: `000.000.000-00`.
- CPF válido.

Telefone:

- Formato: `(00) 99999-9999`.

E-mail:

- Deve ser válido.
- Interface pode sugerir domínios como `@gmail.com`, `@hotmail.com`, `@outlook.com`, `@yahoo.com.br`.

Chave aleatória:

- Deve aceitar UUID ou string compatível.

---

## 13. Configuração de Pix do administrador

### 13.1 Campos obrigatórios

- Tipo de chave Pix.
- Chave Pix.
- Nome do recebedor.
- Banco.
- Documento do recebedor.
- Status ativo/inativo.

### 13.2 Uso no sistema

O Pix do administrador será exibido ao usuário no momento do pagamento da participação.

O sistema deve gerar:

- Código Pix copia e cola.
- QR Code Pix.
- Valor exato do bolão.
- Prazo de pagamento de 3 minutos.
- Instruções claras para o usuário.

---

## 14. Cadastro de jogos

### 14.1 Campos

- Seleção mandante.
- Seleção visitante.
- Data da partida.
- Hora da partida.
- Estádio.
- Cidade.
- Grupo/fase.
- Status da partida.
- Placar mandante.
- Placar visitante.

### 14.2 Status da partida

- Agendada.
- Aberta para bolão.
- Bloqueada para apostas.
- Em andamento.
- Encerrada.
- Resultado informado.
- Premiação gerada.
- Pagamentos realizados.

### 14.3 Regra de bloqueio

O sistema deve bloquear novas apostas automaticamente quando faltar 5 minutos para o início da partida.

Exemplo:

- Jogo: 16:00.
- Limite para apostar: 15:55.

---

## 15. Cadastro de bolões

### 15.1 Campos

- Jogo.
- Nome do bolão.
- Valor de participação.
- Percentual de premiação.
- Valor total arrecadado.
- Valor total do prêmio.
- Status.
- Data/hora de abertura.
- Data/hora de fechamento.

### 15.2 Percentual de premiação

O administrador deve configurar uma escala de 0 a 100%.

Exemplo:

- Total arrecadado: R$ 1.000,00.
- Percentual de premiação: 70%.
- Valor de prêmio: R$ 700,00.
- Valor retido pela administração: R$ 300,00.

Esse percentual deve ficar muito destacado para o usuário antes da participação.

### 15.3 Regras

- Um jogo pode ter um ou mais bolões.
- Um usuário pode participar mais de uma vez do mesmo bolão.
- Cada participação gera um palpite independente.
- Após salvar o palpite, o usuário não pode editar.
- O usuário deve confirmar que entende essa regra antes de salvar.

Mensagem obrigatória antes de salvar:

`Atenção: após salvar o placar, você não poderá alterar este palpite. Deseja continuar?`

---

## 16. Participação no bolão

### 16.1 Fluxo

1. Usuário acessa bolões disponíveis.
2. Escolhe um bolão.
3. Visualiza regras, valor, prêmio estimado e prazo.
4. Informa placar.
5. Confirma alerta de irreversibilidade.
6. Sistema gera cobrança Pix.
7. Usuário tem até 3 minutos para pagar.
8. Sistema aguarda confirmação.
9. Após confirmação, participação fica ativa.

### 16.2 Campos do palpite

- Placar da seleção mandante.
- Placar da seleção visitante.

### 16.3 Status da participação

- Aguardando pagamento.
- Pagamento expirado.
- Pagamento confirmado.
- Palpite válido.
- Palpite vencedor.
- Palpite não premiado.
- Pagamento do prêmio realizado.

---

## 17. Pagamentos Pix

### 17.1 Pagamento de participação

No MVP, o sistema pode iniciar com confirmação manual pelo administrador.

Fluxo manual:

1. Sistema gera QR Code Pix.
2. Usuário realiza pagamento.
3. Administrador confirma pagamento no painel.
4. Participação é liberada.

Fluxo automatizado futuro:

1. Sistema cria cobrança Pix via API de provedor.
2. Provedor retorna QR Code, copia e cola e identificador.
3. Webhook confirma pagamento.
4. Sistema ativa participação automaticamente.

### 17.2 Prazo de pagamento

- O usuário terá 3 minutos para realizar o Pix.
- Após 3 minutos, o pagamento expira.
- Se expirar, o palpite não participa do bolão.

### 17.3 Pagamento de premiação

Fluxo desejado:

1. Administrador informa resultado da partida.
2. Sistema calcula ganhadores.
3. Sistema mostra valor que cada usuário deve receber.
4. Administrador clica em `Realizar pagamento`.
5. Sistema dispara pagamentos via API Pix.
6. Sistema salva comprovantes e status.
7. Sistema gera relatório PDF.

Observação técnica:

- Pagamento Pix automático exige integração com provedor financeiro autorizado.
- Deve existir ambiente sandbox antes de produção.
- Deve haver logs, auditoria, idempotência e tratamento de falhas.

---

## 18. Regras de resultado e ganhadores

### 18.1 Regra principal

Vence quem acertar exatamente o placar final do jogo.

Exemplo:

- Resultado: Brasil 2 x 1 Japão.
- Palpite vencedor: Brasil 2 x 1 Japão.

### 18.2 Divisão do prêmio

Se houver mais de um ganhador, o prêmio será dividido igualmente.

Exemplo:

- Prêmio total: R$ 700,00.
- Ganhadores: 2.
- Valor por ganhador: R$ 350,00.

### 18.3 Sem ganhadores

O administrador poderá escolher uma regra configurável:

- Acumular para próximo bolão.
- Devolver valores.
- Manter valor retido.
- Distribuir por critério alternativo.

Para o MVP, recomenda-se usar: `Acumular para próximo bolão`, configurável pelo administrador.

---

## 19. Relatórios

### 19.1 Relatório de bolão

Deve conter:

- Nome do bolão.
- Jogo.
- Data/hora da partida.
- Valor da participação.
- Total de participações.
- Valor total arrecadado.
- Percentual de premiação.
- Valor total do prêmio.
- Valor retido pela administração.
- Lista de participantes.
- Lista de palpites.
- Resultado final.
- Lista de ganhadores.
- Valor devido a cada ganhador.
- Status do pagamento de cada ganhador.
- Data/hora de geração.

### 19.2 Exportação

- PDF para download.
- Futuramente CSV e Excel.

---

## 20. Telas do sistema

### 20.1 Públicas

- Página inicial.
- Login.
- Cadastro.
- Confirmação de e-mail.
- Criar senha.
- Esqueci minha senha.
- Página 404 personalizada.

### 20.2 Usuário logado

- Dashboard do usuário.
- Bolões disponíveis.
- Detalhes do bolão.
- Participar do bolão.
- Pagamento Pix.
- Meus jogos.
- Meus palpites.
- Meus prêmios.
- Cadastro/edição de Pix.
- Perfil.

### 20.3 Administrador

- Dashboard administrativo.
- Configuração de e-mail.
- Configuração de Pix de recebimento.
- Cadastro de seleções.
- Cadastro de jogos.
- Cadastro de bolões.
- Confirmação de pagamentos.
- Registro de resultados.
- Geração de ganhadores.
- Pagamento de prêmios.
- Relatórios.

---

## 21. UI/UX

### 21.1 Diretrizes visuais

- Layout mobile first.
- Cores inspiradas em futebol: verde campo, branco, amarelo, azul e preto.
- Cards grandes e fáceis de tocar no celular.
- Botões com alto contraste.
- Ícones de bola, gol, campo, rede e troféu.
- Bandeiras/ícones das seleções.
- Destaque visual para valor do bolão, prêmio estimado e prazo.

### 21.2 Animações sugeridas

- Bola rolando no carregamento.
- Gol animado ao confirmar palpite.
- Rede balançando ao exibir vencedor.
- Confete ao mostrar prêmio.
- Campo com linhas suaves no fundo.
- Placar animado nos cards dos jogos.

### 21.3 Componentes principais

- Card de jogo.
- Card de bolão.
- Componente de placar.
- Componente de prêmio.
- Badge de status.
- Timer de fechamento.
- Modal de confirmação de palpite.
- Toast de sucesso/erro.
- QR Code Pix.

---

## 22. Modelos principais sugeridos

### 22.1 Usuario

Campos:

- `cpf`.
- `nome_completo`.
- `telefone`.
- `email`.
- `email_confirmado`.
- `data_cadastro`.
- `ativo`.

### 22.2 PixUsuario

Campos:

- `usuario`.
- `tipo_chave`.
- `chave_pix`.
- `nome_recebedor`.
- `banco`.
- `ativo`.

### 22.3 ConfiguracaoEmail

Campos:

- `servidor_smtp`.
- `porta`.
- `usuario_email`.
- `senha_email`.
- `usar_tls`.
- `email_remetente`.
- `ativo`.

### 22.4 ConfiguracaoPixAdministrador

Campos:

- `tipo_chave`.
- `chave_pix`.
- `nome_recebedor`.
- `banco`.
- `documento_recebedor`.
- `ativo`.

### 22.5 Selecao

Campos:

- `nome`.
- `sigla`.
- `bandeira`.
- `icone`.

### 22.6 JogadorConvocado

Campos opcionais para fase futura:

- `selecao`.
- `nome`.
- `posicao`.
- `numero_camisa`.
- `foto`.

### 22.7 Jogo

Campos:

- `selecao_mandante`.
- `selecao_visitante`.
- `data_hora`.
- `estadio`.
- `cidade`.
- `fase`.
- `status`.
- `placar_mandante`.
- `placar_visitante`.

### 22.8 Bolao

Campos:

- `jogo`.
- `nome`.
- `valor_participacao`.
- `percentual_premiacao`.
- `status`.
- `data_abertura`.
- `data_fechamento`.

### 22.9 ParticipacaoBolao

Campos:

- `usuario`.
- `bolao`.
- `placar_mandante`.
- `placar_visitante`.
- `data_palpite`.
- `status`.
- `codigo_identificador`.
- `bloqueado_para_edicao`.

### 22.10 Pagamento

Campos:

- `participacao`.
- `valor`.
- `status`.
- `txid`.
- `qr_code`.
- `pix_copia_cola`.
- `data_criacao`.
- `data_expiracao`.
- `data_confirmacao`.

### 22.11 Premio

Campos:

- `bolao`.
- `usuario`.
- `valor`.
- `status_pagamento`.
- `data_pagamento`.
- `comprovante`.

---

## 23. CBVs obrigatórias

### Contas

- `CadastroUsuarioView`.
- `ConfirmarEmailView`.
- `CriarSenhaView`.
- `LoginUsuarioView`.
- `LogoutUsuarioView`.

### Usuários

- `PerfilUsuarioView`.
- `PixUsuarioUpdateView`.

### Jogos

- `JogoListView`.
- `JogoDetailView`.
- `JogoCreateView`.
- `JogoUpdateView`.
- `JogoDeleteView`.

### Bolões

- `BolaoListView`.
- `BolaoDetailView`.
- `BolaoCreateView`.
- `BolaoUpdateView`.
- `ParticiparBolaoView`.
- `MeusJogosListView`.
- `ResultadoBolaoView`.

### Pagamentos

- `PagamentoPixDetailView`.
- `ConfirmarPagamentoView`.
- `RealizarPagamentoPremioView`.

### Relatórios

- `RelatorioBolaoPDFView`.

### Painel

- `DashboardAdministradorView`.
- `ConfiguracaoEmailUpdateView`.
- `ConfiguracaoPixUpdateView`.

---

## 24. Regras de segurança

- Usar CSRF em todos os formulários.
- Usar `LoginRequiredMixin` em páginas internas.
- Usar permissões administrativas nas páginas de gestão.
- Não salvar senhas de e-mail em texto puro no banco em produção.
- Não expor chaves Pix de usuários sem necessidade.
- Registrar logs de pagamentos e alterações críticas.
- Impedir alteração de palpite após salvo.
- Impedir participação após prazo.
- Impedir confirmação duplicada de pagamento.
- Usar idempotência em chamadas de pagamento.
- Gerar relatórios com trilha de auditoria.

---

## 25. Regras de automação

### 25.1 Fechamento automático de bolão

O sistema deve verificar se faltam 5 minutos para o jogo e bloquear novas participações.

### 25.2 Expiração de pagamento

O sistema deve verificar se o pagamento passou de 3 minutos sem confirmação e marcar como expirado.

### 25.3 Geração de ganhadores

Após o administrador informar o resultado:

- Buscar participações pagas e válidas.
- Comparar placar informado com resultado final.
- Identificar ganhadores.
- Calcular prêmio total.
- Dividir prêmio entre ganhadores.
- Gerar registros de prêmio.

### 25.4 Pagamento de prêmios

Ao clicar em `Realizar pagamento`:

- Validar Pix dos ganhadores.
- Enviar pagamentos via API Pix.
- Atualizar status.
- Salvar comprovantes.
- Gerar PDF.

---

## 26. Mensagens importantes do sistema

### Palpite salvo

`Palpite salvo com sucesso. Agora realize o pagamento Pix para confirmar sua participação.`

### Palpite irreversível

`Atenção: após salvar o placar, você não poderá alterar este palpite.`

### Prazo encerrado

`Este bolão foi encerrado para novas apostas. O prazo limite era 5 minutos antes do início da partida.`

### Pagamento expirado

`O prazo de 3 minutos para pagamento expirou. Faça uma nova participação se o bolão ainda estiver aberto.`

### Pagamento confirmado

`Pagamento confirmado. Seu palpite está participando do bolão.`

### Vencedor

`Parabéns! Você acertou o placar e está entre os ganhadores deste bolão.`

---

## 27. Página 404

A página 404 deve ter:

- Mensagem amigável.
- Tema de futebol.
- Ilustração de bola fora do campo.
- Botão para voltar ao início.
- Botão para meus jogos, se estiver logado.

Texto sugerido:

`Ops! Essa jogada saiu pela linha de fundo. A página que você tentou acessar não existe.`

---

## 28. Critérios de aceite

### Cadastro

- Usuário não pode cadastrar CPF inválido.
- Usuário não pode cadastrar CPF duplicado.
- Usuário não pode login antes de confirmar e-mail e criar senha.
- Usuário recebe e-mail de confirmação.

### Bolão

- Administrador consegue cadastrar jogos e bolões.
- Percentual de premiação aparece destacado para o usuário.
- Usuário consegue realizar mais de uma participação no mesmo jogo.
- Usuário recebe alerta antes de salvar palpite.
- Usuário não consegue editar palpite salvo.
- Usuário não consegue apostar após 5 minutos antes do jogo.

### Pagamento

- Sistema gera QR Code Pix e copia e cola.
- Sistema controla prazo de 3 minutos.
- Sistema só libera participação após pagamento confirmado.

### Resultado

- Administrador informa resultado final.
- Sistema calcula ganhadores automaticamente.
- Sistema divide prêmio corretamente.
- Sistema gera PDF do relatório.

### Responsividade

- Layout deve funcionar em celular, tablet e computador.
- Cards devem ser legíveis e fáceis de tocar em telas pequenas.

---

## 29. Roadmap sugerido

### Fase 1 — Base do projeto

- Criar projeto Django.
- Criar apps.
- Configurar SQLite.
- Configurar Tailwind.
- Criar base HTML.
- Criar login, logout e página 404.

### Fase 2 — Usuários

- Cadastro com CPF, telefone e e-mail.
- Confirmação de e-mail.
- Criação de senha.
- Perfil do usuário.
- Cadastro de Pix do usuário.

### Fase 3 — Jogos e bolões

- Cadastro de seleções.
- Cadastro de jogos.
- Cadastro de bolões.
- Listagem de bolões disponíveis.
- Participação com palpite bloqueado após salvar.

### Fase 4 — Pagamentos

- Configuração Pix do administrador.
- Geração de QR Code Pix.
- Expiração em 3 minutos.
- Confirmação manual de pagamento.

### Fase 5 — Resultados e relatórios

- Informar resultado.
- Calcular ganhadores.
- Calcular valores.
- Gerar PDF.

### Fase 6 — Integração Pix real

- Contratar provedor autorizado.
- Implementar cobrança Pix via API.
- Implementar webhook de confirmação.
- Implementar pagamento automático de prêmios.
- Implementar logs e auditoria.

### Fase 7 — Melhorias visuais

- Animações de bola, gol, rede e campo.
- Ícones de seleções.
- Jogadores convocados.
- Ranking de usuários.
- Histórico da Copa.

---

## 30. Prompt sugerido para Claude Sonnet 4.6 ou Codex

```txt
Você é um desenvolvedor sênior especialista em Django, segurança, arquitetura limpa, UI/UX responsivo e sistemas financeiros.

Crie um sistema de bolão online para jogos da Copa do Mundo seguindo o PRD abaixo.

Regras obrigatórias:
- Projeto em Python + Django na versão mais atual estável.
- Banco SQLite.
- Pasta principal do projeto chamada bolao.
- Criar ambiente virtual venv.
- Criar requirements.txt.
- Criar .gitignore completo.
- Usar Tailwind CSS no frontend.
- Usar Class Based Views em todo CRUD e telas principais.
- Usar templates HTML com csrf_token em todos os formulários.
- Sistema inteiro em português do Brasil.
- Nomes de variáveis, comentários, apps, models, forms e views em português do Brasil.
- Usar aspas simples em strings Python, exemplo: print ('jogo realizado').
- Criar login, logout, cadastro, confirmação de e-mail, criação de senha e página 404.
- Criar apps separados: contas, usuarios, jogos, boloes, pagamentos, relatorios e painel.
- Criar migrations e deixar o sistema pronto para executar com migrate.
- Layout responsivo para celular, tablet e computador.
- UI/UX com tema de futebol: bola, gol, rede, campo, troféu, bandeiras e seleções.
- Validar CPF, telefone, e-mail e senha forte.
- Usuário só pode apostar até 5 minutos antes do jogo.
- Usuário pode participar mais de uma vez no mesmo bolão.
- Palpite não pode ser alterado após salvo.
- Pix do usuário é obrigatório para receber prêmio.
- Pix do administrador deve ser configurável por interface gráfica.
- Pagamento inicial pode ser manual, mas a arquitetura deve permitir integração Pix real por API e webhook.
- Gerar relatório PDF de resultado, ganhadores e pagamentos.

Entregue o projeto com arquivos organizados, código limpo, PEP8, comentários úteis e instruções de execução.
```

---

## 31. Observações finais

Este PRD define a base funcional, técnica e visual do sistema. A recomendação é começar pelo MVP com pagamento Pix manual, confirmação administrativa e relatórios em PDF. Depois, avançar para integração Pix real com provedor autorizado, webhooks, automação de pagamento e auditoria completa.
