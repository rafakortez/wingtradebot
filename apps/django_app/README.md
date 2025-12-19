# Django Dashboard - WingTradeBot

Dashboard web robusto desenvolvido com Django para monitoramento e gerenciamento de trades SimpleFX, com interface administrativa integrada.

## Características

- **Framework Completo**: Django com ORM, Admin, e sistema de autenticação
- **REST API**: Django REST Framework para endpoints de API
- **WebSockets**: Django Channels para atualizações em tempo real
- **Admin Interface**: Interface administrativa para gerenciar dados
- **Escalável**: Arquitetura preparada para produção
- **Dashboard React**: Interface moderna com React via CDN

## Requisitos

- Python 3.10+
- Serviço FastAPI rodando (para integração SimpleFX)
- PostgreSQL (opcional, SQLite por padrão)

## Instalação

1. **Criar ambiente virtual**:
```bash
cd apps/django_app
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows
```

2. **Instalar dependências**:
```bash
pip install -r requirements.txt
```

3. **Configurar variáveis de ambiente**:
Crie um arquivo `.env` na raiz do projeto:
```env
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
FASTAPI_URL=http://localhost:8000
```

4. **Executar migrações**:
```bash
python manage.py migrate
```

5. **Criar superusuário** (para acessar admin):
```bash
python manage.py createsuperuser
```

## Execução

**Desenvolvimento**:
```bash
python manage.py runserver
```

O servidor estará disponível em `http://localhost:8000`

**Produção** (com Gunicorn e Daphne):
```bash
# Para HTTP
gunicorn wingtradebot.wsgi:application --bind 0.0.0.0:8000

# Para WebSockets (ASGI)
daphne -b 0.0.0.0 -p 8000 wingtradebot.asgi:application
```

## Estrutura do Projeto

```
django_app/
├── manage.py              # Script de gerenciamento Django
├── wingtradebot/         # Projeto Django
│   ├── settings.py        # Configurações
│   ├── urls.py           # URLs principais
│   ├── wsgi.py           # WSGI application
│   └── asgi.py           # ASGI application (WebSockets)
├── dashboard/            # App Django
│   ├── models.py         # Modelos ORM
│   ├── views.py         # Views
│   ├── urls.py          # URLs do app
│   ├── admin.py         # Configuração admin
│   ├── api/             # API REST
│   │   ├── views.py
│   │   └── urls.py
│   ├── consumers.py     # WebSocket consumers
│   ├── routing.py       # WebSocket routing
│   └── templates/       # Templates
│       └── dashboard/
│           └── index.html
├── requirements.txt      # Dependências
└── README.md           # Esta documentação
```

## URLs Principais

- **Dashboard**: `http://localhost:8000/`
- **Admin**: `http://localhost:8000/admin/`
- **API Status**: `http://localhost:8000/api/status/<login_number>/`
- **API Chart Data**: `http://localhost:8000/api/simplefx-chart-data/`

## Admin Interface

Acesse `http://localhost:8000/admin/` com o superusuário criado.

A interface admin permite:
- Visualizar e editar modelos (quando implementados)
- Gerenciar usuários e permissões
- Acessar logs e configurações

## API Endpoints (Django REST Framework)

### GET `/api/status/<login_number>/`
Obtém status completo da conta.

**Resposta**:
```json
{
  "accountStatus": {...},
  "activeOrders": {...},
  "closedOrders": {...},
  "unrealizedPnL": 50.0,
  "realizedPnL": 100.0,
  "orderCounts": {
    "buyVolume": 0.5,
    "sellVolume": 0.3
  }
}
```

### GET `/api/recent-db-orders/<login_number>/`
Obtém ordens recentes do banco de dados.

### GET `/api/webhook-outcomes/<login_number>/`
Obtém resultados de webhooks.

### GET `/api/recent-logs/`
Obtém logs recentes.

**Query Parameters**:
- `account` (opcional): Filtrar por conta

### GET `/api/simplefx-chart-data/`
Obtém dados de gráfico.

**Query Parameters**:
- `symbol`: Símbolo (padrão: "EURUSD")
- `timeframe`: Timeframe (padrão: "1h")
- `account`: Número da conta

## WebSockets (Django Channels)

O dashboard usa Django Channels para WebSockets:

**Cliente JavaScript**:
```javascript
const ws = new WebSocket('ws://localhost:8000/ws/dashboard/');
ws.onmessage = function(event) {
    const data = JSON.parse(event.data);
    console.log('Received:', data);
};
```

**Consumer** (servidor):
```python
# dashboard/consumers.py
class DashboardConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
```

## Migrações

Criar novas migrações:
```bash
python manage.py makemigrations
```

Aplicar migrações:
```bash
python manage.py migrate
```

## Testes

```bash
# Executar todos os testes
python manage.py test

# Teste específico
python manage.py test dashboard
```

## Configuração de Banco de Dados

**SQLite (padrão)**:
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

**PostgreSQL (produção)**:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'wingtradebot',
        'USER': 'user',
        'PASSWORD': 'password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

## Segurança

**Configurações importantes para produção**:
```python
# settings.py
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## Static Files

Coletar arquivos estáticos:
```bash
python manage.py collectstatic
```

## Integração com FastAPI

O Django app faz proxy para o serviço FastAPI. Configure em `settings.py`:

```python
FASTAPI_URL = os.getenv('FASTAPI_URL', 'http://localhost:8000')
```

## Desenvolvimento

**Shell interativo**:
```bash
python manage.py shell
```

**Criar novo app**:
```bash
python manage.py startapp nome_do_app
```

## Troubleshooting

**Erro de migrações**:
```bash
python manage.py migrate --run-syncdb
```

**Limpar cache**:
```bash
python manage.py clear_cache
```

**Problemas com Channels**:
- Verifique se `channels` está em `INSTALLED_APPS`
- Confirme que `ASGI_APPLICATION` está configurado
- Use `InMemoryChannelLayer` para desenvolvimento

## Próximos Passos

- Implementar modelos Django ORM completos
- Adicionar sistema de autenticação de usuários
- Criar testes unitários e de integração
- Implementar cache Redis para Channels
- Adicionar logging estruturado
- Configurar CI/CD
- Adicionar monitoring e métricas

## Comparação com Flask

**Vantagens do Django**:
- ORM robusto
- Admin interface integrada
- Sistema de autenticação completo
- Melhor para projetos grandes
- Mais recursos built-in

**Quando usar Django**:
- Projetos que precisam de admin interface
- Aplicações com modelos complexos
- Necessidade de sistema de usuários
- Projetos de longo prazo


