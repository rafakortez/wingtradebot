-- WingTradeBot — Unified PostgreSQL Schema
-- 
-- This file is the single source of truth for the database schema.
-- It is used by:
--   - tools/db_migrator.py  (creates tables before importing data)
--   - infrastructure/ansible/roles/db_init/tasks/main.yml  (runs on server via psql)
--
-- Compatible with: AWS RDS PostgreSQL, GCP Cloud SQL, Azure Database for PostgreSQL
-- Equivalent to the SQLite schema in: src/database.ts
--
-- Run manually:
--   PGPASSWORD=yourpass psql -h HOST -U wingbot -d wingtradebot -f schema.sql

-- ─── sfx_historical_orders ────────────────────────────────────────────────────
-- Primary trade history table. Mirrors the SQLite schema exactly.
-- SQLite INTEGER (0/1) booleans → PostgreSQL SMALLINT (compatible with existing data)
-- SQLite REAL → PostgreSQL DOUBLE PRECISION

CREATE TABLE IF NOT EXISTS sfx_historical_orders (
    order_id              VARCHAR(64)       PRIMARY KEY,
    login                 VARCHAR(32),
    symbol                VARCHAR(16),
    side                  VARCHAR(8),
    volume                DOUBLE PRECISION,
    open_price            DOUBLE PRECISION,
    close_price           DOUBLE PRECISION,
    take_profit           DOUBLE PRECISION,
    stop_loss             DOUBLE PRECISION,
    open_time             BIGINT,
    close_time            BIGINT,
    profit                DOUBLE PRECISION,
    swap                  DOUBLE PRECISION,
    commission            DOUBLE PRECISION,
    reality               VARCHAR(16),
    leverage              INTEGER,
    margin                DOUBLE PRECISION,
    margin_rate           DOUBLE PRECISION,
    request_id            VARCHAR(64),
    is_fifo               SMALLINT,                    -- 0 or 1 (SQLite INTEGER bool)
    ob_reference_price    DOUBLE PRECISION,
    real_sl_pips          DOUBLE PRECISION,
    real_tp_pips          DOUBLE PRECISION,
    bid_at_open           DOUBLE PRECISION,
    ask_at_open           DOUBLE PRECISION,
    spread_at_open        DOUBLE PRECISION,
    consider_ob_reference SMALLINT,                    -- 0 or 1 (SQLite INTEGER bool)
    max_size              DOUBLE PRECISION,
    duration_in_minutes   INTEGER,
    last_update_time      BIGINT,
    alert_id              VARCHAR(128),
    maxobalert            INTEGER,
    alert_threshold       DOUBLE PRECISION,
    diff_op_ob            DOUBLE PRECISION,
    timeframe             VARCHAR(16),
    exchange              VARCHAR(32),
    "findObType"          VARCHAR(32),                 -- quoted: camelCase column name
    "filterFvgs"          SMALLINT,                    -- quoted: camelCase column name
    "fvgDistance"         DOUBLE PRECISION,            -- quoted: camelCase column name
    "lineHeight"          VARCHAR(32),                 -- quoted: camelCase column name
    "filterFractal"       VARCHAR(32)                  -- quoted: camelCase column name
);

-- ─── account_settings ─────────────────────────────────────────────────────────
-- Per-account trading configuration (trading mode, session filters).

CREATE TABLE IF NOT EXISTS account_settings (
    login               INTEGER           PRIMARY KEY,
    trading_mode        VARCHAR(32)       NOT NULL DEFAULT 'NORMAL',
    asia_session        SMALLINT          DEFAULT 1,   -- 0 or 1
    london_session      SMALLINT          DEFAULT 1,
    new_york_session    SMALLINT          DEFAULT 1,
    limbo_session       SMALLINT          DEFAULT 1,
    exclusive_mode      SMALLINT          DEFAULT 0,
    last_updated        BIGINT            NOT NULL
);

-- ─── processed_webhook_ids ────────────────────────────────────────────────────
-- Permanent deduplication store for TradingView webhook alert IDs.
-- Prevents the same alert from being processed twice.

CREATE TABLE IF NOT EXISTS processed_webhook_ids (
    id              SERIAL            PRIMARY KEY,     -- AUTOINCREMENT equivalent
    alert_id        VARCHAR(128)      NOT NULL,
    account_number  VARCHAR(32)       NOT NULL,
    processed_at    BIGINT            NOT NULL,
    UNIQUE(alert_id, account_number)
);

-- ─── webhook_outcomes ─────────────────────────────────────────────────────────
-- Audit log of every webhook processing result (success, failure, skip).

CREATE TABLE IF NOT EXISTS webhook_outcomes (
    id              SERIAL            PRIMARY KEY,
    alert_id        VARCHAR(128)      NOT NULL,
    account_number  VARCHAR(32)       NOT NULL,
    symbol          VARCHAR(16)       NOT NULL,
    action          VARCHAR(16)       NOT NULL,
    size            DOUBLE PRECISION  NOT NULL,
    outcome         VARCHAR(32)       NOT NULL,
    reason          TEXT,
    order_id        VARCHAR(64),
    processed_at    BIGINT            NOT NULL
);

-- ─── Indexes ──────────────────────────────────────────────────────────────────

CREATE INDEX IF NOT EXISTS idx_orders_login
    ON sfx_historical_orders(login);

CREATE INDEX IF NOT EXISTS idx_orders_open_time
    ON sfx_historical_orders(open_time DESC);

CREATE INDEX IF NOT EXISTS idx_orders_symbol
    ON sfx_historical_orders(symbol);

CREATE INDEX IF NOT EXISTS idx_webhook_ids_lookup
    ON processed_webhook_ids(alert_id, account_number);

CREATE INDEX IF NOT EXISTS idx_webhook_outcomes_account
    ON webhook_outcomes(account_number, outcome, processed_at);
