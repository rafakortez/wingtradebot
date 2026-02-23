import { config } from "./config";

export function calculateDurationInMinutes(
  openTime: number,
  closeTime: number,
): number {
  const open = new Date(openTime);
  const close = new Date(closeTime);
  const durationMs = close.getTime() - open.getTime();
  return Math.round(durationMs / (1000 * 60));
}

export function getTradingSessionForTimestamp(
  timestamp: number,
): string | null {
  if (!timestamp) return null;

  try {
    // Create a date object from the timestamp (which is in UTC)
    const date = new Date(timestamp);

    // Convert to ET (Eastern Time)
    // Note: This is a more accurate conversion that accounts for timezone offsets
    const etOffset = -5 * 60 * 60 * 1000; // UTC-5 for ET (adjust for DST if needed)
    const etDate = new Date(date.getTime() + etOffset);

    const hours = etDate.getUTCHours(); // Use UTC hours since we've already adjusted the time

    // Check which session the hour falls into
    if (hours >= 17 || hours < 1) {
      return "asia_session";
    } else if (hours >= 1 && hours < 6) {
      return "london_session";
    } else if (hours >= 6 && hours < 14) {
      return "new_york_session";
    } else if (hours >= 14 && hours < 17) {
      return "limbo_session";
    }

    return null; // Should never happen if times are defined correctly
  } catch (error) {
    console.error(
      `Error determining trading session for timestamp ${timestamp}:`,
      error,
    );
    return null;
  }
}
export function getInstrumentSpecs(symbol: string) {
  // Clean symbol from exchange prefix (e.g., "SIMPLEFX:US100" -> "US100")
  const cleanSymbol = symbol.replace(/^[A-Z]+:/, "").toUpperCase();

  const forexPairs = [
    "EURUSD",
    "GBPUSD",
    "USDJPY",
    "AUDUSD",
    "USDCAD",
    "NZDUSD",
    "EURGBP",
    "EURJPY",
    "GBPJPY",
  ];
  const indices = [
    "US100",
    "US30",
    "NAS100",
    "SPX500",
    "GER40",
    "UK100",
    "JPN225",
    "US500",
    "TECH100",
  ];

  if (indices.includes(cleanSymbol)) {
    return {
      type: "index",
      pipValue: 1,
      minDistance: 20, // Increased from 5 to 20 points for indices
      decimals: 1, // SimpleFX uses 1 decimal for indices
      minTPDistance: 20, // Minimum TP distance in points
      minSLDistance: 20, // Minimum SL distance in points
    };
  } else if (forexPairs.includes(cleanSymbol)) {
    const isJPYPair = cleanSymbol.includes("JPY");
    return {
      type: "forex",
      pipValue: isJPYPair ? 0.01 : 0.0001,
      minDistance: isJPYPair ? 0.1 : 0.001, // 10 pips minimum
      decimals: isJPYPair ? 3 : 5,
      minTPDistance: 10, // Minimum 10 pips
      minSLDistance: 10, // Minimum 10 pips
    };
  } else {
    // Default to forex
    return {
      type: "forex",
      pipValue: 0.0001,
      minDistance: 0.001,
      decimals: 5,
      minTPDistance: 10,
      minSLDistance: 10,
    };
  }
}

function calculatePriceLevels(
  side: string,
  entryPrice: number,
  takeProfitPips: number,
  stopLossPips: number | null,
  specs: any,
) {
  const isBuy = side === "BUY" || side === "B";

  // Calculate TP/SL prices directly from entry price
  let takeProfitPrice: number;
  let stopLossPrice: number | null = null;

  if (isBuy) {
    takeProfitPrice = entryPrice + takeProfitPips * specs.pipValue;
    if (stopLossPips) {
      stopLossPrice = entryPrice - stopLossPips * specs.pipValue;
    }
  } else {
    takeProfitPrice = entryPrice - takeProfitPips * specs.pipValue;
    if (stopLossPips) {
      stopLossPrice = entryPrice + stopLossPips * specs.pipValue;
    }
  }

  // Format prices properly
  if (specs.type === "index") {
    takeProfitPrice = Math.round(takeProfitPrice * 10) / 10;
    if (stopLossPrice) stopLossPrice = Math.round(stopLossPrice * 10) / 10;
  } else {
    takeProfitPrice = Number(takeProfitPrice.toFixed(specs.decimals));
    if (stopLossPrice)
      stopLossPrice = Number(stopLossPrice.toFixed(specs.decimals));
  }

  return { takeProfitPrice, stopLossPrice };
}

function validatePriceLevels(
  side: string,
  entryPrice: number,
  takeProfitPrice: number,
  stopLossPrice: number | null,
  specs: any,
): { valid: boolean; error?: string } {
  const isBuy = side === "BUY" || side === "B";

  // Calculate distances in pips/points
  const tpDistance = Math.abs(takeProfitPrice - entryPrice) / specs.pipValue;
  const slDistance = stopLossPrice
    ? Math.abs(stopLossPrice - entryPrice) / specs.pipValue
    : null;

  // Check minimum distances
  const minRequired = specs.type === "index" ? 20 : 10;

  if (tpDistance < minRequired) {
    return {
      valid: false,
      error: `TP distance (${tpDistance.toFixed(1)} ${specs.type === "index" ? "points" : "pips"}) is below minimum ${minRequired}`,
    };
  }

  if (slDistance !== null && slDistance < minRequired) {
    return {
      valid: false,
      error: `SL distance (${slDistance.toFixed(1)} ${specs.type === "index" ? "points" : "pips"}) is below minimum ${minRequired}`,
    };
  }

  // Validate direction
  if (isBuy) {
    if (takeProfitPrice <= entryPrice) {
      return { valid: false, error: "BUY TP must be above entry price" };
    }
    if (stopLossPrice && stopLossPrice >= entryPrice) {
      return { valid: false, error: "BUY SL must be below entry price" };
    }
  } else {
    if (takeProfitPrice >= entryPrice) {
      return { valid: false, error: "SELL TP must be below entry price" };
    }
    if (stopLossPrice && stopLossPrice <= entryPrice) {
      return { valid: false, error: "SELL SL must be above entry price" };
    }
  }

  return { valid: true };
}

/**
 * Determines the current market condition based on time and volatility
 */
function getCurrentMarketCondition():
  | "normal"
  | "news"
  | "overnight"
  | "lowVolatility" {
  const now = new Date();
  const utcHour = now.getUTCHours();
  const utcMinute = now.getMinutes();

  // Convert to EST/EDT (approximate - doesn't handle DST perfectly)
  const estHour = (utcHour - 5 + 24) % 24;

  // News times (major economic releases typically at 8:30 AM, 10:00 AM EST)
  // Check for news window: 8:15-8:45 AM and 9:45-10:15 AM EST
  if (
    (estHour === 8 && utcMinute >= 15 && utcMinute <= 45) ||
    (estHour === 9 && utcMinute >= 45) ||
    (estHour === 10 && utcMinute <= 15)
  ) {
    return "news";
  }

  // Overnight/low liquidity: 10 PM - 6 AM EST
  if (estHour >= 22 || estHour <= 6) {
    return "overnight";
  }

  // Low volatility periods: 12 PM - 2 PM EST (lunch time)
  if (estHour >= 12 && estHour <= 14) {
    return "lowVolatility";
  }

  // Normal market hours
  return "normal";
}

/**
 * Gets the maximum allowed spread for a symbol based on current market conditions
 */
function getMaxAllowedSpread(symbol: string): number {
  const specs = getInstrumentSpecs(symbol);
  const condition = getCurrentMarketCondition();

  const limits =
    specs.type === "index"
      ? config.SPREAD_LIMITS.indices
      : config.SPREAD_LIMITS.forex;

  return limits[condition];
}

/**
 * Validates if the current spread is acceptable for trading
 */
function validateSpread(
  symbol: string,
  currentSpread: number,
  marketCondition?: string,
): { valid: boolean; error?: string; maxAllowed: number; condition: string } {
  const specs = getInstrumentSpecs(symbol);
  const condition = marketCondition || getCurrentMarketCondition();
  const maxAllowed = getMaxAllowedSpread(symbol);

  // Convert spread to pips/points for comparison
  const spreadInPips = currentSpread / specs.pipValue;

  const result = {
    valid: spreadInPips <= maxAllowed,
    maxAllowed,
    condition,
    error: undefined as string | undefined,
  };

  if (!result.valid) {
    const unit = specs.type === "index" ? "points" : "pips";
    result.error = `Spread too high for ${symbol}: ${spreadInPips.toFixed(1)} ${unit} (max: ${maxAllowed} ${unit} during ${condition} conditions)`;
  }

  return result;
}
