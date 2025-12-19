# FastAPI Service - WingTradeBot SimpleFX Integration

Serviço FastAPI assíncrono para integração com a corretora SimpleFX. Este microserviço fornece endpoints para executar trades, consultar status de contas, obter ordens e dados de gráficos.

## Características

- **API Assíncrona**: Endpoints assíncronos usando FastAPI e httpx
- **Gerenciamento de Tokens**: Cache automático de tokens de autenticação SimpleFX
- **Multi-Conta**: Suporte para API primária e secundária
- **Validação**: Modelos Pydantic para validação de requisições
- **Documentação Automática**: Swagger UI em `/docs`

## Requisitos

- Python 3.10+
- Conta SimpleFX com acesso à API
- Credenciais de API (chaves primária e secundária)

## Instalação

1. **Criar ambiente virtual**:
```bash
cd apps/fastapi_service
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
Crie um arquivo `.env` na raiz do projeto com:
```env
SIMPLEFX_API_KEY=your_primary_api_key
SIMPLEFX_API_SECRET=your_primary_api_secret
SIMPLEFX_API_KEY2=your_secondary_api_key
SIMPLEFX_API_SECRET2=your_secondary_api_secret
DEFAULT_ACCOUNT_NUMBER=your_account_number
DEFAULT_ACCOUNT_NUMBER2=your_secondary_account_number
FASTAPI_PORT=8000
```

## Execução

**Desenvolvimento**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Produção**:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## Endpoints

### GET `/api/simplefx/status/{login_number}`
Obtém o status de uma conta de trading.

**Parâmetros**:
- `login_number` (path): Número da conta
- `reality` (query, opcional): "LIVE" ou "DEMO"
- `use_secondary_api` (query, opcional): true/false

**Resposta**:
```json
{
  "data": {
    "balance": 1000.0,
    "equity": 1050.0,
    "margin": 50.0,
    ...
  },
  "success": true
}
```

### GET `/api/simplefx/orders/active/{login_number}`
Obtém ordens ativas de uma conta.

**Parâmetros**:
- `login_number` (path): Número da conta
- `page` (query, opcional): Número da página (padrão: 1)
- `limit` (query, opcional): Limite de resultados (padrão: 100)

### GET `/api/simplefx/orders/closed/{login_number}`
Obtém histórico de ordens fechadas.

**Parâmetros**:
- `login_number` (path): Número da conta
- `time_from` (query, opcional): Timestamp inicial em milissegundos
- `time_to` (query, opcional): Timestamp final em milissegundos

### GET `/api/simplefx/chart-data`
Obtém dados de candlestick para gráficos.

**Parâmetros**:
- `symbol` (query): Símbolo do instrumento (ex: "EURUSD")
- `timeframe` (query): Timeframe ("1m", "5m", "15m", "1h", "4h", "1d")
- `account` (query): Número da conta
- `time_from` (query, opcional): Timestamp inicial
- `time_to` (query, opcional): Timestamp final

### POST `/api/simplefx/trade`
Executa um trade via SimpleFX API.

**Body**:
```json
{
  "side": "BUY",
  "amount": 0.1,
  "login_number": "3979937",
  "take_profit_price": 1.0900,
  "stop_loss_price": 1.0800,
  "reality": "LIVE",
  "symbol": "EURUSD",
  "use_secondary_api": false
}
```

### GET `/health`
Health check endpoint.

## Documentação Interativa

Acesse a documentação Swagger em:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Integração com Flask/Django

Este serviço pode ser chamado de aplicações Flask ou Django:

```python
import requests

response = requests.get(
    "http://localhost:8000/api/simplefx/status/3979937",
    params={"reality": "LIVE"}
)
data = response.json()
```

## Estrutura do Projeto

```
fastapi_service/
├── main.py              # Aplicação FastAPI principal
├── models.py            # Modelos Pydantic
├── config.py            # Configurações
├── requirements.txt     # Dependências
└── README.md           # Esta documentação
```

## Testes

```bash
# Teste básico de health check
curl http://localhost:8000/health

# Teste de status
curl http://localhost:8000/api/simplefx/status/3979937?reality=LIVE
```

## Notas de Desenvolvimento

- Os tokens de autenticação são cacheados por 1 hora
- Retry automático em caso de token expirado (401)
- Suporte para múltiplas contas com diferentes API keys
- Validação de volume mínimo baseada no tipo de instrumento

## Próximos Passos

- Adicionar rate limiting
- Implementar circuit breaker
- Adicionar logging estruturado
- Criar testes unitários e de integração


