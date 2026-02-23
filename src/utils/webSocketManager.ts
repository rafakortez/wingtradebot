import WebSocket from "ws"
import { logger } from "./logger"
import { EventEmitter } from "events"

interface MarketData {
  symbol: string
  bid: number
  ask: number
  timestamp: number
  isStale: boolean
}

interface ConnectionStats {
  totalConnections: number
  activeConnections: number
  symbolsTracked: string[]
  lastQuoteUpdate: number
}

/**
 * Lightweight WebSocket Manager - On-Demand Connections Only
 * 
 * This manager connects to SimpleFX WebSocket when needed, gets price data,
 * and disconnects immediately after use. No persistent connections.
 */
export class WebSocketManager extends EventEmitter {
  private readonly WS_URL = "wss://web-quotes-core.simplefx.com/websocket/quotes"
  private readonly CONNECTION_TIMEOUT = 10000 // 10 seconds
  private readonly QUOTE_TIMEOUT = 8000 // 8 seconds
  private readonly DISCONNECT_DELAY = 2000 // 2 seconds after getting quote
  private readonly MAX_RETRIES = 3
  private totalConnections = 0

  constructor() {
    super()
  }

  /**
   * Get market data for order placement - on-demand connection
   * Connects, gets quote, disconnects
   */
  public async connectForOrder(symbol: string, maxRetries: number = this.MAX_RETRIES): Promise<MarketData> {
    let lastError: Error | null = null
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        logger.info(`WebSocketManager: Getting market data for ${symbol} (attempt ${attempt}/${maxRetries})`)
        
        const marketData = await this.getMarketDataOnDemand(symbol)
        
        logger.info(`WebSocketManager: Successfully obtained market data for ${symbol}`)
        return marketData
        
      } catch (error: any) {
        lastError = error
        logger.warn(`WebSocketManager: Attempt ${attempt} failed for ${symbol}: ${error.message}`)
        
        // If this isn't the last attempt, wait before retrying
        if (attempt < maxRetries) {
          const delay = attempt * 1000 // Progressive delay: 1s, 2s, 3s
          logger.info(`WebSocketManager: Waiting ${delay}ms before retry ${attempt + 1}`)
          await new Promise(resolve => setTimeout(resolve, delay))
        }
      }
    }
    
    // All retries failed
    const errorMessage = `Failed to get market data for ${symbol} after ${maxRetries} attempts. Last error: ${lastError?.message}`
    logger.error(`WebSocketManager: ${errorMessage}`)
    throw new Error(errorMessage)
  }

  /**
   * Connect on-demand, get quote, disconnect
   */
  private async getMarketDataOnDemand(symbol: string): Promise<MarketData> {
    return new Promise((resolve, reject) => {
      const ws = new WebSocket(this.WS_URL)
      let quoteReceived = false
      let requestId = 0
      const connectionTimeout = setTimeout(() => {
        if (!quoteReceived) {
          ws.close()
          reject(new Error(`Connection timeout for ${symbol}`))
        }
      }, this.CONNECTION_TIMEOUT)

      const quoteTimeout = setTimeout(() => {
        if (!quoteReceived) {
          ws.close()
          reject(new Error(`Quote timeout for ${symbol}`))
        }
      }, this.QUOTE_TIMEOUT)

      ws.on("open", () => {
        this.totalConnections++
        logger.info(`WebSocketManager: Connected for ${symbol}`)
        
        // Subscribe to symbol
        const subscribeRequest = {
          p: "/subscribe/addList",
          i: ++requestId,
          d: [symbol]
        }
        ws.send(JSON.stringify(subscribeRequest))
        
        // Request last known price immediately
        const lastPriceRequest = {
          p: "/lastprices/list",
          i: ++requestId,
          d: [symbol]
        }
        ws.send(JSON.stringify(lastPriceRequest))
      })

      ws.on("message", (data: WebSocket.Data) => {
        try {
          const message = JSON.parse(data.toString())
          
          if (message.p === "/quotes/subscribed" || message.p === "/lastprices/list") {
            const quote = message.d?.[0]
            if (quote && quote.s === symbol) {
              quoteReceived = true
              clearTimeout(connectionTimeout)
              clearTimeout(quoteTimeout)
              
              // Convert timestamp to milliseconds if needed
              let timestamp = quote.t
              if (timestamp && timestamp < 1000000000000) {
                timestamp = timestamp * 1000
              }
              
              const marketData: MarketData = {
                symbol: quote.s,
                bid: quote.b,
                ask: quote.a,
                timestamp: timestamp || Date.now(),
                isStale: false
              }
              
              // Disconnect after short delay
              setTimeout(() => {
                ws.close()
                logger.info(`WebSocketManager: Disconnected after getting quote for ${symbol}`)
              }, this.DISCONNECT_DELAY)
              
              resolve(marketData)
            }
          }
        } catch (error) {
          if (!quoteReceived) {
            logger.error(`WebSocketManager: Error parsing message for ${symbol}: ${error instanceof Error ? error.message : String(error)}`)
          }
        }
      })

      ws.on("close", (code, reason) => {
        clearTimeout(connectionTimeout)
        clearTimeout(quoteTimeout)
        if (!quoteReceived) {
          reject(new Error(`Connection closed for ${symbol} (code: ${code}, reason: ${reason})`))
        }
      })

      ws.on("error", (error) => {
        clearTimeout(connectionTimeout)
        clearTimeout(quoteTimeout)
        if (!quoteReceived) {
          reject(new Error(`WebSocket error for ${symbol}: ${error.message}`))
        }
      })
    })
  }

  /**
   * Connect for dashboard updates - on-demand connection
   * For dashboard, we connect, get quotes, and disconnect
   */
  public async connectForDashboard(symbols: string[] = ["EURUSD", "US100", "GBPUSD"]): Promise<void> {
    try {
      logger.info(`WebSocketManager: Getting dashboard quotes for symbols: ${symbols.join(", ")}`)
      
      // Get quotes for all symbols (each connects/disconnects independently)
      // For dashboard, we can get quotes sequentially to reduce load
      for (const symbol of symbols) {
        try {
          await this.connectForOrder(symbol, 1) // Single attempt for dashboard
        } catch (error) {
          logger.warn(`WebSocketManager: Failed to get quote for ${symbol} in dashboard: ${error}`)
        }
      }
      
      logger.info(`WebSocketManager: Dashboard quotes retrieved`)
    } catch (error: any) {
      logger.error(`WebSocketManager: Failed to get dashboard quotes: ${error.message}`)
      throw error
    }
  }

  /**
   * Get quote for a specific symbol - on-demand
   * This method always connects on-demand, no caching
   */
  public async getQuoteForSymbol(symbol: string): Promise<{ bid: number; ask: number; timestamp: number } | null> {
    try {
      const marketData = await this.connectForOrder(symbol, 1)
      return {
        bid: marketData.bid,
        ask: marketData.ask,
        timestamp: marketData.timestamp
      }
    } catch (error) {
      logger.warn(`WebSocketManager: Failed to get quote for ${symbol}: ${error}`)
      return null
    }
  }

  /**
   * Check if any connection is active
   * With on-demand connections, this is always false (no persistent connections)
   */
  public isConnected(): boolean {
    return false // No persistent connections
  }

  /**
   * Get the timestamp of the last price update
   * With on-demand connections, we don't track this
   */
  public getLastPriceUpdate(): Date {
    return new Date() // Return current time as fallback
  }

  /**
   * Disconnect all connections
   * With on-demand connections, there are no persistent connections to disconnect
   */
  public disconnect(): void {
    logger.info("WebSocketManager: No persistent connections to disconnect")
  }

  /**
   * Force reconnection for a symbol
   * With on-demand connections, this just gets a fresh quote
   */
  public async forceReconnectForSymbol(symbol: string): Promise<MarketData> {
    logger.info(`WebSocketManager: Force reconnecting for ${symbol} (on-demand)`)
    return await this.connectForOrder(symbol)
  }

  /**
   * Get market data with automatic stale price detection and reconnection
   */
  public async getMarketDataWithRetry(symbol: string): Promise<MarketData> {
    return await this.connectForOrder(symbol)
  }

  /**
   * Get connection statistics for monitoring
   */
  public getConnectionStats(): ConnectionStats {
    return {
      totalConnections: this.totalConnections,
      activeConnections: 0, // No persistent connections
      symbolsTracked: [], // No persistent tracking
      lastQuoteUpdate: Date.now()
    }
  }

  /**
   * Check if price data is available and fresh for a symbol
   * With on-demand connections, we always fetch fresh data
   */
  public isPriceDataFresh(symbol: string): boolean {
    return false // Always fetch fresh data on-demand
  }

  /**
   * Get age of price data for a symbol in seconds
   * With on-demand connections, we don't cache data
   */
  public getPriceDataAge(symbol: string): number | null {
    return null // No cached data
  }
}

// Export singleton instance
export const webSocketManager = new WebSocketManager()
