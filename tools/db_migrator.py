#!/usr/bin/env python3
"""
WingTradeBot — Database Migration Tool
=======================================
Pulls the SQLite database from the live server via SSH/SFTP and migrates
all data to a target PostgreSQL database (AWS RDS, GCP Cloud SQL, or Azure).

USAGE:
    # Option A: Direct connection (requires DB publicly accessible or firewall rule for your IP)
    python tools/db_migrator.py --target aws --db-host <RDS_ENDPOINT> \
        --db-user wingbot --db-name wingtradebot --db-password <PASSWORD>

    # Option B: SSH Tunnel (recommended — DB stays private)
    # The tool SSHes into a jump host (e.g., the cloud VM) and tunnels through it
    python tools/db_migrator.py --target aws --db-host <INTERNAL_RDS_ENDPOINT> \
        --db-user wingbot --db-name wingtradebot --db-password <PASSWORD> \
        --ssh-tunnel --ssh-host <VM_PUBLIC_IP> --ssh-user root --ssh-port 2277

    # Option C: Use a local SQLite file you already have:
    python tools/db_migrator.py --target aws --db-host <HOST> \
        --db-user wingbot --db-name wingtradebot --db-password <PASSWORD> \
        --local-db ./sfx_historical_orders.db

Requirements:
    pip install -r tools/requirements.txt
"""

import argparse
import os
import socket
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import paramiko
    import psycopg2
    import psycopg2.extras
    from sshtunnel import SSHTunnelForwarder  # For easy SSH tunneling
except ImportError:
    print("ERROR: Missing dependencies. Run: pip install -r tools/requirements.txt")
    sys.exit(1)


# ─── Configuration ────────────────────────────────────────────────────────────

# Live server SSH connection details
# These match the live server's current configuration
LIVE_SERVER_HOST = os.getenv("LIVE_SERVER_HOST", "138.197.231.228")
LIVE_SERVER_PORT = int(os.getenv("LIVE_SERVER_PORT", "2277"))
LIVE_SERVER_USER = os.getenv("LIVE_SERVER_USER", "root")
LIVE_SERVER_SSH_KEY = os.getenv("LIVE_SERVER_SSH_KEY", os.path.expanduser("~/.ssh/id_rsa"))
LIVE_DB_PATH = os.getenv("LIVE_DB_PATH", "/root/wingtradebot/sfx_historical_orders.db")

# Tables to migrate (in order — respects foreign key dependencies)
TABLES_TO_MIGRATE = [
    "sfx_historical_orders",
    "account_settings",
    "processed_webhook_ids",
    "webhook_outcomes",
]

# Batch size for INSERT operations (prevents memory issues with large tables)
BATCH_SIZE = 500


# ─── SSH / SFTP Download ──────────────────────────────────────────────────────

def download_db_from_live_server(local_path: str) -> bool:
    """
    SSH into the live server and download the SQLite database file via SFTP.
    Returns True on success, False on failure.
    """
    print(f"\n[SSH] Connecting to live server {LIVE_SERVER_HOST}:{LIVE_SERVER_PORT}...")
    print(f"[SSH] User: {LIVE_SERVER_USER}")
    print(f"[SSH] Key: {LIVE_SERVER_SSH_KEY}")
    print(f"[SSH] Remote DB: {LIVE_DB_PATH}")

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(
            hostname=LIVE_SERVER_HOST,
            port=LIVE_SERVER_PORT,
            username=LIVE_SERVER_USER,
            key_filename=LIVE_SERVER_SSH_KEY,
            timeout=30,
        )
        print("[SSH] ✓ Connected successfully")

        # Check that the remote file exists
        stdin, stdout, stderr = client.exec_command(f"ls -lh {LIVE_DB_PATH}")
        output = stdout.read().decode().strip()
        error = stderr.read().decode().strip()

        if error or not output:
            print(f"[SSH] ERROR: Remote file not found: {LIVE_DB_PATH}")
            print(f"[SSH] stderr: {error}")
            return False

        print(f"[SSH] Remote file: {output}")

        # Download via SFTP
        sftp = client.open_sftp()
        print(f"[SFTP] Downloading to {local_path}...")
        sftp.get(LIVE_DB_PATH, local_path)
        sftp.close()

        size_mb = os.path.getsize(local_path) / (1024 * 1024)
        print(f"[SFTP] ✓ Downloaded {size_mb:.2f} MB")
        return True

    except paramiko.AuthenticationException:
        print(f"[SSH] ERROR: Authentication failed. Check your SSH key: {LIVE_SERVER_SSH_KEY}")
        return False
    except paramiko.SSHException as e:
        print(f"[SSH] ERROR: SSH connection failed: {e}")
        return False
    except Exception as e:
        print(f"[SSH] ERROR: {e}")
        return False
    finally:
        client.close()


# ─── SQLite Reader ────────────────────────────────────────────────────────────

def get_sqlite_tables(sqlite_path: str) -> List[str]:
    """Return list of tables that exist in the SQLite database."""
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables


def get_sqlite_row_count(sqlite_path: str, table: str) -> int:
    """Return the number of rows in a SQLite table."""
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.execute(f"SELECT COUNT(*) FROM {table}")
    count = cursor.fetchone()[0]
    conn.close()
    return count


def read_sqlite_table(sqlite_path: str, table: str) -> Tuple[List[str], List[tuple]]:
    """
    Read all rows from a SQLite table.
    Returns (column_names, rows).
    """
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(f"SELECT * FROM {table}")
    columns = [description[0] for description in cursor.description]
    rows = [tuple(row) for row in cursor.fetchall()]
    conn.close()
    return columns, rows


# ─── PostgreSQL Writer ────────────────────────────────────────────────────────

def connect_postgres(host: str, port: int, user: str, password: str, dbname: str):
    """Connect to PostgreSQL and return connection."""
    print(f"\n[PG] Connecting to PostgreSQL at {host}:{port}...")
    print(f"[PG] Database: {dbname}, User: {user}")

    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=dbname,
        connect_timeout=30,
        sslmode="require",  # All managed cloud PostgreSQL requires SSL
    )
    conn.autocommit = False
    print("[PG] ✓ Connected successfully")
    return conn


def apply_schema(pg_conn, schema_path: str):
    """Apply the SQL schema file to the PostgreSQL database."""
    print(f"\n[SCHEMA] Applying schema from {schema_path}...")
    with open(schema_path, "r") as f:
        schema_sql = f.read()

    cursor = pg_conn.cursor()
    cursor.execute(schema_sql)
    pg_conn.commit()
    print("[SCHEMA] ✓ Schema applied successfully")


def quote_column(col: str) -> str:
    """
    Quote column names that are camelCase (SQLite allows them, PostgreSQL needs quoting).
    The schema.sql uses quoted names for: findObType, filterFvgs, fvgDistance, lineHeight, filterFractal
    """
    camel_case_cols = {"findObType", "filterFvgs", "fvgDistance", "lineHeight", "filterFractal"}
    if col in camel_case_cols:
        return f'"{col}"'
    return col


def migrate_table(pg_conn, sqlite_path: str, table: str, dry_run: bool = False) -> int:
    """
    Migrate all rows from a SQLite table to PostgreSQL.
    Uses INSERT ... ON CONFLICT DO UPDATE (upsert) to be idempotent.
    Returns the number of rows migrated.
    """
    columns, rows = read_sqlite_table(sqlite_path, table)

    if not rows:
        print(f"[MIGRATE] Table '{table}': 0 rows — skipping")
        return 0

    total = len(rows)
    print(f"[MIGRATE] Table '{table}': {total} rows to migrate...")

    if dry_run:
        print(f"[DRY RUN] Would migrate {total} rows from '{table}'")
        return total

    # Build the INSERT ... ON CONFLICT DO UPDATE statement
    quoted_cols = [quote_column(c) for c in columns]
    col_list = ", ".join(quoted_cols)
    placeholders = ", ".join(["%s"] * len(columns))

    # Determine the conflict column (primary key)
    pk_map = {
        "sfx_historical_orders": "order_id",
        "account_settings": "login",
        "processed_webhook_ids": "id",
        "webhook_outcomes": "id",
    }
    pk_col = pk_map.get(table)

    if pk_col and pk_col in columns:
        # Build SET clause for all non-PK columns
        update_cols = [c for c in columns if c != pk_col]
        if update_cols:
            set_clause = ", ".join([f"{quote_column(c)} = EXCLUDED.{quote_column(c)}" for c in update_cols])
            upsert_sql = (
                f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
                f"ON CONFLICT ({quote_column(pk_col)}) DO UPDATE SET {set_clause}"
            )
        else:
            upsert_sql = (
                f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) "
                f"ON CONFLICT ({quote_column(pk_col)}) DO NOTHING"
            )
    else:
        # No known PK — use plain INSERT (may fail on duplicates if run twice)
        upsert_sql = f"INSERT INTO {table} ({col_list}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

    cursor = pg_conn.cursor()
    migrated = 0

    # Insert in batches
    for i in range(0, total, BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        try:
            psycopg2.extras.execute_batch(cursor, upsert_sql, batch, page_size=BATCH_SIZE)
            pg_conn.commit()
            migrated += len(batch)
            pct = (migrated / total) * 100
            print(f"[MIGRATE]   {migrated}/{total} rows ({pct:.0f}%)", end="\r")
        except Exception as e:
            pg_conn.rollback()
            print(f"\n[MIGRATE] ERROR in batch {i}-{i+len(batch)}: {e}")
            print(f"[MIGRATE] First row of failed batch: {batch[0]}")
            raise

    print(f"\n[MIGRATE] ✓ '{table}': {migrated} rows migrated")
    return migrated


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Migrate WingTradeBot SQLite data to cloud PostgreSQL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--target", choices=["aws", "gcp", "azure"], required=True,
                        help="Target cloud provider")
    parser.add_argument("--db-host", required=True,
                        help="PostgreSQL hostname (from terraform output db_host or db_fqdn)")
    parser.add_argument("--db-port", type=int, default=5432,
                        help="PostgreSQL port (default: 5432)")
    parser.add_argument("--db-user", required=True,
                        help="PostgreSQL username")
    parser.add_argument("--db-name", required=True,
                        help="PostgreSQL database name")
    parser.add_argument("--db-password",
                        help="PostgreSQL password (or set PG_PASSWORD env var)")
    parser.add_argument("--local-db",
                        help="Path to a local SQLite file (skips SSH download)")
    parser.add_argument("--schema", default="infrastructure/db/schema.sql",
                        help="Path to schema.sql (default: infrastructure/db/schema.sql)")
    parser.add_argument("--tables", nargs="+", default=TABLES_TO_MIGRATE,
                        help="Tables to migrate (default: all)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be migrated without actually writing")
    parser.add_argument("--skip-schema", action="store_true",
                        help="Skip applying schema.sql (tables already exist)")

    # SSH Tunnel options for connecting to private databases
    parser.add_argument("--ssh-tunnel", action="store_true",
                        help="Use SSH tunnel to connect to DB (for private DBs)")
    parser.add_argument("--tunnel-host",
                        help="SSH host for tunnel (e.g., the cloud VM IP)")
    parser.add_argument("--tunnel-port", type=int, default=22,
                        help="SSH port for tunnel (default: 22)")
    parser.add_argument("--tunnel-user", default="root",
                        help="SSH user for tunnel (default: root)")
    parser.add_argument("--tunnel-key",
                        help="SSH private key for tunnel (default: same as --ssh-key)")

    parser.add_argument("--ssh-host", default=LIVE_SERVER_HOST,
                        help=f"Live server SSH host (default: {LIVE_SERVER_HOST})")
    parser.add_argument("--ssh-port", type=int, default=LIVE_SERVER_PORT,
                        help=f"Live server SSH port (default: {LIVE_SERVER_PORT})")
    parser.add_argument("--ssh-user", default=LIVE_SERVER_USER,
                        help=f"Live server SSH user (default: {LIVE_SERVER_USER})")
    parser.add_argument("--ssh-key", default=LIVE_SERVER_SSH_KEY,
                        help=f"Path to SSH private key (default: {LIVE_SERVER_SSH_KEY})")

    args = parser.parse_args()

    # Get password
    db_password = args.db_password or os.getenv("PG_PASSWORD")
    if not db_password:
        import getpass
        db_password = getpass.getpass(f"PostgreSQL password for {args.db_user}@{args.db_host}: ")

    print(f"\n{'='*60}")
    print(f"  WingTradeBot Database Migration Tool")
    print(f"  Target: {args.target.upper()} PostgreSQL")
    print(f"  Host:   {args.db_host}:{args.db_port}")
    print(f"  DB:     {args.db_name}")
    print(f"  Tables: {', '.join(args.tables)}")
    if args.dry_run:
        print(f"  MODE:   DRY RUN (no data will be written)")
    print(f"{'='*60}\n")

    # Step 1: Get the SQLite file
    if args.local_db:
        sqlite_path = args.local_db
        if not os.path.exists(sqlite_path):
            print(f"ERROR: Local SQLite file not found: {sqlite_path}")
            sys.exit(1)
        print(f"[INFO] Using local SQLite file: {sqlite_path}")
        size_mb = os.path.getsize(sqlite_path) / (1024 * 1024)
        print(f"[INFO] File size: {size_mb:.2f} MB")
    else:
        # Download from live server
        global LIVE_SERVER_HOST, LIVE_SERVER_PORT, LIVE_SERVER_USER, LIVE_SERVER_SSH_KEY
        LIVE_SERVER_HOST = args.ssh_host
        LIVE_SERVER_PORT = args.ssh_port
        LIVE_SERVER_USER = args.ssh_user
        LIVE_SERVER_SSH_KEY = args.ssh_key

        # Save to a temp file
        tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        sqlite_path = tmp.name
        tmp.close()

        success = download_db_from_live_server(sqlite_path)
        if not success:
            print("\nERROR: Failed to download database from live server.")
            print("TIP: Use --local-db if you already have a local copy.")
            sys.exit(1)

    # Step 2: Inspect SQLite
    available_tables = get_sqlite_tables(sqlite_path)
    print(f"\n[SQLITE] Tables found: {', '.join(available_tables)}")

    tables_to_migrate = [t for t in args.tables if t in available_tables]
    skipped = [t for t in args.tables if t not in available_tables]
    if skipped:
        print(f"[SQLITE] Tables not found (will skip): {', '.join(skipped)}")

    for table in tables_to_migrate:
        count = get_sqlite_row_count(sqlite_path, table)
        print(f"[SQLITE]   {table}: {count} rows")

    # Step 3: Connect to PostgreSQL
    pg_conn = connect_postgres(
        host=args.db_host,
        port=args.db_port,
        user=args.db_user,
        password=db_password,
        dbname=args.db_name,
    )

    # Step 4: Apply schema
    if not args.skip_schema:
        schema_path = args.schema
        if not os.path.exists(schema_path):
            print(f"ERROR: Schema file not found: {schema_path}")
            print("TIP: Run from the project root directory.")
            sys.exit(1)
        apply_schema(pg_conn, schema_path)

    # Step 5: Migrate each table
    start_time = time.time()
    total_rows = 0

    for table in tables_to_migrate:
        try:
            rows = migrate_table(pg_conn, sqlite_path, table, dry_run=args.dry_run)
            total_rows += rows
        except Exception as e:
            print(f"\n[ERROR] Migration failed for table '{table}': {e}")
            pg_conn.close()
            sys.exit(1)

    elapsed = time.time() - start_time

    # Step 6: Summary
    print(f"\n{'='*60}")
    print(f"  Migration Complete!")
    print(f"  Total rows migrated: {total_rows}")
    print(f"  Time elapsed: {elapsed:.1f}s")
    print(f"  Target: {args.target.upper()} — {args.db_host}")
    print(f"{'='*60}")
    print(f"\nNext step: Copy the DATABASE_URL to your .env file:")
    print(f"  DATABASE_URL=postgres://{args.db_user}:<password>@{args.db_host}:{args.db_port}/{args.db_name}")
    print(f"\nOr get it from Terraform:")
    print(f"  cd infrastructure/terraform/{args.target} && terraform output database_url")

    pg_conn.close()

    # Clean up temp file
    if not args.local_db and os.path.exists(sqlite_path):
        os.unlink(sqlite_path)


if __name__ == "__main__":
    main()
