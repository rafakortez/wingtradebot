import fs from "fs";
import path from "path";

// Simple file logger with basic rotation
const LOG_FILE = "app.log";
const MAX_LOG_SIZE = 10 * 1024 * 1024; // 10MB
const ERROR_LOG_FILE = "error.log";

// Format timestamp
function formatTimestamp(): string {
  const now = new Date();
  const day = String(now.getDate()).padStart(2, '0');
  const month = String(now.getMonth() + 1).padStart(2, '0');
  const year = now.getFullYear();
  const hours = String(now.getHours()).padStart(2, '0');
  const minutes = String(now.getMinutes()).padStart(2, '0');
  const seconds = String(now.getSeconds()).padStart(2, '0');
  return `${day}/${month}/${year}, ${hours}:${minutes}:${seconds}`;
}

// Check and rotate log file if needed
function checkLogRotation(logFile: string): void {
  try {
    if (fs.existsSync(logFile)) {
      const stats = fs.statSync(logFile);
      if (stats.size > MAX_LOG_SIZE) {
        // Delete old file (simple rotation)
        fs.unlinkSync(logFile);
      }
    }
  } catch (error) {
    // Ignore rotation errors
  }
}

// Write to log file
function writeToFile(logFile: string, message: string): void {
  try {
    checkLogRotation(logFile);
    const timestamp = formatTimestamp();
    const logLine = `${timestamp} | ${message}\n`;
    fs.appendFileSync(logFile, logLine, 'utf8');
  } catch (error) {
    // Fallback to console if file write fails
    console.error(`Failed to write to log file: ${error}`);
  }
}

// Simple logger implementation
class SimpleLogger {
  private logLevel: string;

  constructor(level: string = 'info') {
    this.logLevel = process.env.NODE_ENV === 'production' ? 'error' : level;
  }

  info(message: string): void {
    if (this.logLevel === 'error') return; // Skip info in production
    const msg = `INFO: ${message}`;
    console.log(msg);
    writeToFile(LOG_FILE, msg);
  }

  warn(message: string): void {
    const msg = `WARN: ${message}`;
    console.warn(msg);
    writeToFile(LOG_FILE, msg);
  }

  error(message: string): void {
    const msg = `ERROR: ${message}`;
    console.error(msg);
    writeToFile(LOG_FILE, msg);
    writeToFile(ERROR_LOG_FILE, msg); // Also write to error log
  }

  debug(message: string): void {
    if (this.logLevel === 'error') return; // Skip debug in production
    const msg = `DEBUG: ${message}`;
    console.debug(msg);
    writeToFile(LOG_FILE, msg);
  }
}

// Trade logger - always logs to file
class TradeLogger {
  info(message: string): void {
    const msg = `TRADE: ${message}`;
    console.log(msg);
    writeToFile(LOG_FILE, msg);
  }

  warn(message: string): void {
    const msg = `TRADE_WARN: ${message}`;
    console.warn(msg);
    writeToFile(LOG_FILE, msg);
  }

  error(message: string): void {
    const msg = `TRADE_ERROR: ${message}`;
    console.error(msg);
    writeToFile(LOG_FILE, msg);
    writeToFile(ERROR_LOG_FILE, msg);
  }

  debug(message: string): void {
    // No-op for debug in trade logger
  }
}

// Create logger instances
const mainLogger = new SimpleLogger('error');
const winstonTradeLogger = new TradeLogger();

// Clean trade logging functions
export const logTrade = {
  placed: (type: string, symbol: string, side: string, amount: number, price: number, account: string) => {
    winstonTradeLogger.info(`TRADE_${type}: ${side} ${symbol} | ${amount} @ ${price} | Acc:${account}`);
  },
  priceCalculation: (symbol: string, account: string, data: any) => {
    winstonTradeLogger.info(`PRICE_CALC: ${symbol} | ${JSON.stringify(data)} | Acc:${account}`);
  },
  webhookReceived: (symbol: string, action: string, size: number, tp: number, sl: number, account: string, alertId: string) => {
    winstonTradeLogger.info(`WEBHOOK_RECEIVED: ${action} ${symbol} | Size:${size} TP:${tp} SL:${sl} | Acc:${account} | ID:${alertId}`);
  },
  apiRequest: (symbol: string, account: string, endpoint: string, data: any) => {
    winstonTradeLogger.info(`API_REQUEST: ${endpoint} | ${symbol} | Acc:${account} | Data:${JSON.stringify(data)}`);
  },
  duplicate: (symbol: string, action: string, account: string, alertId: string) => {
    winstonTradeLogger.info(`DUPLICATE: ${action} ${symbol} | Acc:${account} | ID:${alertId}`);
  },
  spread: (symbol: string, status: string, currentSpread: number, maxAllowed: number, condition: string, attempt: number, maxAttempts?: number) => {
    const specs = symbol.includes('US100') || symbol.includes('US500') || symbol.includes('US30') ? { pipValue: 1, type: 'index' } : { pipValue: 0.0001, type: 'forex' };
    const spreadInPips = currentSpread / specs.pipValue;
    const unit = specs.type === 'index' ? 'pts' : 'pips';
    const attemptInfo = maxAttempts ? `${attempt}/${maxAttempts}` : `${attempt}`;
    winstonTradeLogger.info(`SPREAD_${status}: ${symbol} | ${spreadInPips.toFixed(1)}${unit} (max:${maxAllowed}${unit}) | ${condition} | Attempt:${attemptInfo}`);
  }
};

export const logError = {
  trade: (symbol: string, side: string, message: string, account: string) => {
    const errorMsg = `TRADE_ERROR: ${side} ${symbol} | ${message} | Acc:${account}`;
    mainLogger.error(errorMsg);
    winstonTradeLogger.error(errorMsg);
  },
  api: (operation: string, message: string, account?: string) => {
    const errorMsg = `API_ERROR: ${operation} | ${message}${account ? ` | Acc:${account}` : ''}`;
    mainLogger.error(errorMsg);
  },
  system: (operation: string, message: string) => {
    mainLogger.error(`ERROR: ${operation} | ${message}`);
  },
  detailed: (operation: string, error: any, context?: any) => {
    const contextStr = context ? ` | Context:${JSON.stringify(context)}` : '';
    const errorMsg = `ERROR: ${operation} | ${error.message || error}${contextStr}`;
    mainLogger.error(errorMsg);
  }
};

export const logApp = {
  modeChange: (account: string, mode: string) => {
    mainLogger.info(`MODE_CHANGE: ${account} | ${mode}`);
  }
};

export const logQuote = (symbol: string, bid: number, ask: number) => {
  // Minimal quote logging - no-op to reduce log noise
};

export const logger = mainLogger;
export const tradeLogger = winstonTradeLogger;
export const quoteLogger = mainLogger;
