/**
 * WingTradeBot — Configuration Template
 *
 * HOW TO USE:
 *   1. Copy this file to src/config.ts
 *   2. Create a .env file in the project root (see .env.example)
 *   3. All sensitive values are read from environment variables — NEVER hardcode secrets here
 *
 * LOCAL DEV:  values fall back to safe defaults when env vars are not set
 * PRODUCTION: all values MUST be set via .env or systemd EnvironmentFile
 */

// ─── Helper: parse comma-separated env var into string array ─────────────────
function parseList(envVar: string | undefined, fallback: string[] = []): string[] {
  if (!envVar) return fallback;
  return envVar.split(',').map(s => s.trim()).filter(Boolean);
}

// ─── Core Config Object ───────────────────────────────────────────────────────
export const config = {
  // Server
  PORT: parseInt(process.env.PORT || '443'),
  DEBUG_LEVEL: (process.env.DEBUG_LEVEL || 'normal') as 'normal' | 'verbose',
  SERVER_IP: process.env.SERVER_IP || '',

  // IP Allowlist — comma-separated in env, e.g. "52.89.214.238,34.212.75.30"
  // TradingView webhook IPs + your server IP + localhost
  ALLOWED_IPS: parseList(process.env.ALLOWED_IPS, [
    '52.89.214.238',
    '34.212.75.30',
    '54.218.53.128',
    '52.32.178.7',
    '127.0.0.1',
    '::ffff:127.0.0.1',
    '::1'
  ]),

  // SimpleFX API — Primary credentials
  SIMPLEFX_API_KEY: process.env.SIMPLEFX_API_KEY || '',
  SIMPLEFX_API_SECRET: process.env.SIMPLEFX_API_SECRET || '',

  // SimpleFX API — Secondary credentials (optional, for secondary accounts)
  SIMPLEFX_API_KEY2: process.env.SIMPLEFX_API_KEY2 || '',
  SIMPLEFX_API_SECRET2: process.env.SIMPLEFX_API_SECRET2 || '',

  // SimpleFX API endpoints (not secrets — safe to keep as defaults)
  SIMPLEFX_API_URL: 'https://rest.simplefx.com/api/v3',
  SIMPLEFX_QUOTES_URL: 'https://web-quotes-core.simplefx.com',

  // Circuit breaker parameters
  CIRCUIT_BREAKER: {
    FAILURE_THRESHOLD: parseInt(process.env.CB_FAILURE_THRESHOLD || '5'),
    RESET_TIMEOUT: parseInt(process.env.CB_RESET_TIMEOUT || '60000'),       // ms
    HALF_OPEN_TIMEOUT: parseInt(process.env.CB_HALF_OPEN_TIMEOUT || '30000') // ms
  },

  // Rate limiting parameters
  RATE_LIMIT: {
    MAX_REQUESTS: parseInt(process.env.RATE_LIMIT_MAX || '10'),
    TIME_WINDOW: parseInt(process.env.RATE_LIMIT_WINDOW || '60000') // ms
  },

  // Bybit (optional — leave empty if not used)
  BYBIT_API_KEY: process.env.BYBIT_API_KEY || '',
  BYBIT_API_SECRET: process.env.BYBIT_API_SECRET || '',
  BYBIT_TESTNET: process.env.BYBIT_TESTNET !== 'false', // default true (safe)

  BYBIT: {
    API_KEY: process.env.BYBIT_API_KEY || '',
    API_SECRET: process.env.BYBIT_API_SECRET || '',
    TESTNET: process.env.BYBIT_TESTNET !== 'false',
  },

  // Dashboard authentication
  STATUS_AUTH: {
    USERNAME: process.env.STATUS_AUTH_USERNAME || 'admin',
    PASSWORD: process.env.STATUS_AUTH_PASSWORD || ''
  },

  STATUS_AUTH2: {
    USERNAME: process.env.STATUS_AUTH2_USERNAME || 'admin',
    PASSWORD: process.env.STATUS_AUTH2_PASSWORD || ''
  },

  // Cron job configuration
  CRON: {
    ORDER_SYNC_INTERVAL: parseInt(process.env.ORDER_SYNC_INTERVAL || '30'),
    ENABLE_ORDER_SYNC: process.env.ENABLE_ORDER_SYNC !== 'false'
  },

  // Spread limits configuration (pips / points)
  SPREAD_LIMITS: {
    forex: {
      normal: 15,
      news: 25,
      overnight: 20,
      lowVolatility: 8
    },
    indices: {
      normal: 300,
      news: 500,
      overnight: 400,
      lowVolatility: 150
    }
  },

  // Spread validation settings
  SPREAD_VALIDATION: {
    maxRetries: 5,
    retryDelayMs: 2000,
    backoffMultiplier: 1.5
  },

  // Database
  // DB_TYPE: 'sqlite' for local dev, 'postgres' for cloud deployments
  DB_TYPE: (process.env.DB_TYPE || 'sqlite') as 'sqlite' | 'postgres',
  // DATABASE_URL: only required when DB_TYPE=postgres
  // Format: postgres://user:password@host:5432/dbname
  DATABASE_URL: process.env.DATABASE_URL || '',
  // DB_FILE: SQLite file path (only used when DB_TYPE=sqlite)
  DB_FILE: process.env.DB_FILE || './sfx_historical_orders.db',

  // FastAPI microservice URL (used when Node.js delegates to FastAPI)
  FASTAPI_URL: process.env.FASTAPI_URL || 'http://localhost:8000',
};

// ─── Account Configuration ────────────────────────────────────────────────────

// Primary account number
export const DEFAULT_ACCOUNT_NUMBER = process.env.DEFAULT_ACCOUNT_NUMBER || '';

// All accounts to monitor — comma-separated in env
// e.g. ALL_MONITORED_ACCOUNTS=3028761,3028450
export const ALL_MONITORED_ACCOUNTS: string[] = parseList(
  process.env.ALL_MONITORED_ACCOUNTS,
  DEFAULT_ACCOUNT_NUMBER ? [DEFAULT_ACCOUNT_NUMBER] : []
);

// Accounts that use the secondary SimpleFX API credentials
// e.g. SECONDARY_API_ACCOUNTS=3979937
export const SECONDARY_API_ACCOUNTS: string[] = parseList(
  process.env.SECONDARY_API_ACCOUNTS,
  []
);

// ─── Startup Validation ───────────────────────────────────────────────────────
export function validateConfig(): { valid: boolean; errors: string[] } {
  const errors: string[] = [];

  if (!config.SIMPLEFX_API_KEY) {
    errors.push('SIMPLEFX_API_KEY is not set');
  }
  if (!config.SIMPLEFX_API_SECRET) {
    errors.push('SIMPLEFX_API_SECRET is not set');
  }
  if (!config.STATUS_AUTH.PASSWORD) {
    errors.push('STATUS_AUTH_PASSWORD is not set — dashboard will be unprotected');
  }
  if (ALL_MONITORED_ACCOUNTS.length === 0) {
    errors.push('ALL_MONITORED_ACCOUNTS is empty — no accounts will be monitored');
  }
  if (config.DB_TYPE === 'postgres' && !config.DATABASE_URL) {
    errors.push('DB_TYPE=postgres but DATABASE_URL is not set');
  }

  return { valid: errors.length === 0, errors };
}
