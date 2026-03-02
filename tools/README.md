# WingTradeBot — Database Migration Tool

This tool migrates the live server's SQLite database to a managed PostgreSQL
database on AWS, GCP, or Azure.

## Prerequisites

1. **Python 3.9+** installed on your local machine
2. **SSH key** that can access the live server (port 2277)
3. **PostgreSQL database** already created via Terraform (see below)
4. **Your local IP** to allow the migration tool to connect to the cloud DB

---

## Step 1: Install Dependencies

```bash
pip install -r tools/requirements.txt
```

---

## Step 2: Provision the Cloud Database (Terraform)

Run Terraform for your target cloud provider. This creates the VM **and** the
managed PostgreSQL database.

### AWS (RDS PostgreSQL — Free Tier)

```bash
cd infrastructure/terraform/aws

# 1. Copy and fill in your values
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: add aws_access_key, aws_secret_key, db_password, migration_tool_ip

# 2. Initialize and apply
terraform init
terraform plan    # Review what will be created
terraform apply   # Type 'yes' to confirm

# 3. Note the outputs — you'll need them in Step 3
terraform output db_host        # RDS hostname
terraform output migration_command  # Ready-to-run migration command
```

> **Free Tier Note:** AWS RDS `db.t3.micro` is free for 12 months on new accounts.
> After 12 months it costs ~$15/month. Set `db_publicly_accessible = false` after migration.

### GCP (Cloud SQL — Free Trial Credits)

```bash
cd infrastructure/terraform/gcp

# 1. Download your GCP Service Account JSON key
# GCP Console > IAM & Admin > Service Accounts > Create Key (JSON)
# Save as: infrastructure/terraform/gcp/gcp-credentials.json

# 2. Copy and fill in your values
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: add gcp_project, db_password, migration_tool_ip

# 3. Initialize and apply
terraform init
terraform plan
terraform apply

# 4. Note the outputs
terraform output db_public_ip
terraform output migration_command
```

> **Free Trial Note:** GCP Cloud SQL uses your $300 free trial credits.
> `db-f1-micro` costs ~$7/month after credits are exhausted.

### Azure (PostgreSQL Flexible Server — Free Trial Credits)

```bash
cd infrastructure/terraform/azure

# 1. Create a Service Principal
az login
az ad sp create-for-rbac --name "wingtradebot-terraform" --role Contributor \
  --scopes /subscriptions/YOUR_SUBSCRIPTION_ID
# Note the appId (client_id), password (client_secret), tenant

# 2. Copy and fill in your values
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars: add subscription_id, tenant_id, client_id, client_secret,
#                         db_password, migration_tool_start_ip, migration_tool_end_ip

# 3. Initialize and apply
terraform init
terraform plan
terraform apply

# 4. Note the outputs
terraform output db_fqdn
terraform output migration_command
```

> **Free Trial Note:** Azure PostgreSQL Flexible Server uses your $200 free trial credits.
> `B_Standard_B1ms` costs ~$12/month after credits are exhausted.

---

## Step 3: Run the Migration

The migration tool will:
1. SSH into the live server (port 2277)
2. Download `sfx_historical_orders.db` via SFTP
3. Apply the PostgreSQL schema (`infrastructure/db/schema.sql`)
4. Migrate all rows using upsert (safe to run multiple times)

### AWS

```bash
# From the project root directory:
python tools/db_migrator.py \
  --target aws \
  --db-host <RDS_ENDPOINT_FROM_TERRAFORM_OUTPUT> \
  --db-user wingbot \
  --db-name wingtradebot \
  --db-password <YOUR_DB_PASSWORD>
```

### GCP

```bash
python tools/db_migrator.py \
  --target gcp \
  --db-host <CLOUD_SQL_IP_FROM_TERRAFORM_OUTPUT> \
  --db-user wingbot \
  --db-name wingtradebot \
  --db-password <YOUR_DB_PASSWORD>
```

### Azure

```bash
python tools/db_migrator.py \
  --target azure \
  --db-host <FQDN_FROM_TERRAFORM_OUTPUT> \
  --db-user wingbot \
  --db-name wingtradebot \
  --db-password <YOUR_DB_PASSWORD>
```

### Using a Local SQLite File (Skip SSH Download)

If you already have a local copy of the database:

```bash
python tools/db_migrator.py \
  --target aws \
  --db-host <HOST> \
  --db-user wingbot \
  --db-name wingtradebot \
  --db-password <PASSWORD> \
  --local-db ./sfx_historical_orders.db
```

### Dry Run (Preview Without Writing)

```bash
python tools/db_migrator.py \
  --target aws \
  --db-host <HOST> \
  --db-user wingbot \
  --db-name wingtradebot \
  --db-password <PASSWORD> \
  --dry-run
```

---

## Step 4: Verify the Migration

Connect to your PostgreSQL database and verify the data:

```bash
# AWS
PGPASSWORD=<password> psql -h <RDS_ENDPOINT> -U wingbot -d wingtradebot \
  -c "SELECT COUNT(*) FROM sfx_historical_orders;"

# GCP
PGPASSWORD=<password> psql -h <CLOUD_SQL_IP> -U wingbot -d wingtradebot \
  -c "SELECT COUNT(*) FROM sfx_historical_orders;"

# Azure
PGPASSWORD=<password> psql -h <FQDN> -U wingbot -d wingtradebot \
  -c "SELECT COUNT(*) FROM sfx_historical_orders;"
```

The row count should match the live server's SQLite database.

---

## Step 5: Update Your Application Config

After migration, update your `.env` (or Ansible `vars/main.yml`) with the
`DATABASE_URL` from Terraform output:

```bash
# Get the DATABASE_URL (sensitive — won't show in plain text)
cd infrastructure/terraform/aws
terraform output -raw database_url
```

Add to your `.env`:
```
DB_TYPE=postgres
DATABASE_URL=postgres://wingbot:<password>@<host>:5432/wingtradebot
```

---

## Step 6: Lock Down the Database (After Migration)

Once migration is complete and the app is running:

**AWS:** Set `db_publicly_accessible = false` in `terraform.tfvars` and run `terraform apply`.

**GCP:** Remove the `migration-tool-local` authorized network from `terraform.tfvars` and run `terraform apply`.

**Azure:** Remove the `migration_tool_start_ip` / `migration_tool_end_ip` firewall rule from `terraform.tfvars` and run `terraform apply`.

---

## Troubleshooting

| Error | Solution |
|---|---|
| `Authentication failed` | Check `--ssh-key` path. Try `ssh -p 2277 root@<host>` manually first. |
| `Connection refused` (PostgreSQL) | Check that `migration_tool_ip` in `terraform.tfvars` matches your current IP (`curl ifconfig.me`). |
| `SSL connection required` | The tool uses `sslmode=require` by default — all managed cloud DBs require SSL. |
| `column "findObType" does not exist` | The schema uses quoted camelCase columns. Make sure you applied `infrastructure/db/schema.sql` first. |
| `could not connect to server` (RDS) | RDS may take 5-10 minutes to become available after `terraform apply`. |

---

## Environment Variables (Alternative to CLI Args)

```bash
export LIVE_SERVER_HOST=138.197.231.228
export LIVE_SERVER_PORT=2277
export LIVE_SERVER_USER=root
export LIVE_SERVER_SSH_KEY=~/.ssh/id_rsa
export LIVE_DB_PATH=/root/wingtradebot/sfx_historical_orders.db
export PG_PASSWORD=your_db_password
```
