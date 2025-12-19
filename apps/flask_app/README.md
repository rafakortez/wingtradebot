# Flask Dashboard - WingTradeBot

Dashboard web desenvolvido com Flask para monitoramento em tempo real de trades e contas SimpleFX.

## Características

- **Dashboard Interativo**: Interface React com 3 abas (Dashboard, Resumo, Charts)
- **Tempo Real**: WebSockets via Flask-SocketIO para atualizações ao vivo
- **Gráficos**: Visualização de P&L diário e candlesticks com posições
- **Exportação**: Exportação de dados em CSV e Excel
- **Multi-Conta**: Suporte para múltiplas contas de trading
- **Filtros**: Filtros de data para análise histórica

## Requisitos

- Python 3.10+
- Serviço FastAPI rodando (para integração SimpleFX)
- Navegador moderno com suporte a WebSockets

## Instalação

1. **Criar ambiente virtual**:
```bash
cd apps/flask_app
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
FLASK_SECRET_KEY=your-secret-key-here
FASTAPI_URL=http://localhost:8000
FLASK_PORT=5000
```

## Execução

**Desenvolvimento**:
```bash
python app.py
```

Ou usando Flask CLI:
```bash
export FLASK_APP=app.py
export FLASK_ENV=development
flask run
```

**Produção** (com Gunicorn):
```bash
gunicorn -k eventlet -w 1 --bind 0.0.0.0:5000 app:app
```

## Estrutura do Projeto

```
flask_app/
├── app.py                 # Aplicação Flask principal
├── routes/                # Blueprints (opcional)
│   ├── dashboard.py
│   └── api.py
├── templates/            # Templates Jinja2
│   └── index.html        # Dashboard React
├── static/               # Arquivos estáticos
│   ├── css/
│   └── js/
├── services/             # Serviços (chamadas FastAPI)
├── requirements.txt      # Dependências
└── README.md            # Esta documentação
```

## Endpoints

### GET `/`
Dashboard principal com interface React.

### GET `/api/status/<login_number>`
Obtém status completo da conta (proxy para FastAPI).

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
  },
  "serverTime": "2024-01-01T12:00:00"
}
```

### GET `/api/recent-db-orders/<login_number>`
Obtém ordens recentes do banco de dados SQLite.

### GET `/api/webhook-outcomes/<login_number>`
Obtém resultados de webhooks processados.

### GET `/api/recent-logs`
Obtém logs recentes do sistema.

**Query Parameters**:
- `account` (opcional): Filtrar por conta

### GET `/api/simplefx-chart-data`
Obtém dados de gráfico (proxy para FastAPI).

**Query Parameters**:
- `symbol`: Símbolo (padrão: "EURUSD")
- `timeframe`: Timeframe (padrão: "1h")
- `account`: Número da conta

## WebSockets

O dashboard usa Flask-SocketIO para atualizações em tempo real:

```javascript
const socket = io();
socket.on('connect', function() {
    console.log('Connected to Flask-SocketIO server');
});
```

## Funcionalidades do Dashboard

### Aba Dashboard
- **Overview**: Balance, Equity, Margin, Leverage
- **Results**: P&L Realizado e Não Realizado
- **Daily P&L Chart**: Gráfico de barras com P&L diário
- **Logs**: Logs do sistema em tempo real
- **Active Orders**: Tabela de ordens ativas com sorting
- **Closed Orders**: Histórico de ordens fechadas com filtros de data

### Aba Resumo
- Resumo de todas as contas
- Cálculo de variação percentual
- Filtros de data

### Aba Charts
- Gráfico de candlesticks interativo
- Visualização de posições abertas (SL/TP)
- Múltiplos timeframes (1m, 5m, 15m, 1h, 4h, 1d)
- WebSocket para atualizações de preço em tempo real

## Exportação de Dados

O dashboard permite exportar dados em:
- **CSV**: Formato compatível com Excel
- **Excel**: Arquivo .xlsx com formatação

## Integração com FastAPI

O Flask app faz proxy para o serviço FastAPI. Certifique-se de que o FastAPI está rodando antes de iniciar o Flask:

```python
# Em app.py
FASTAPI_URL = os.getenv('FASTAPI_URL', 'http://localhost:8000')
```

## Segurança

Para produção, configure:
- Autenticação HTTP Basic para o dashboard
- HTTPS/SSL
- Rate limiting
- CORS apropriado

Exemplo de autenticação básica:
```python
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    return username == 'admin' and password == 'secret'

@app.route('/')
@auth.login_required
def index():
    return render_template('index.html')
```

## Desenvolvimento

**Hot Reload**:
```bash
export FLASK_ENV=development
flask run --reload
```

**Debug Mode**:
```python
app.run(debug=True, host='0.0.0.0', port=5000)
```

## Troubleshooting

**Erro de conexão com FastAPI**:
- Verifique se o FastAPI está rodando
- Confirme a URL em `FASTAPI_URL`
- Verifique firewall/portas

**WebSocket não conecta**:
- Verifique se Flask-SocketIO está instalado
- Confirme que o cliente está usando a URL correta
- Verifique logs do servidor

## Próximos Passos

- Adicionar autenticação de usuários
- Implementar cache Redis
- Adicionar testes automatizados
- Melhorar tratamento de erros
- Adicionar métricas e monitoring


