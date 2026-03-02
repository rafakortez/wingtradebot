terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  credentials = file(var.gcp_credentials_file)
  project     = var.gcp_project
  region      = var.region
  zone        = var.zone
}

# ─── Static IP ────────────────────────────────────────────────────────────────
resource "google_compute_address" "trading" {
  name   = "wingtradebot-ip"
  region = var.region
}

# ─── Firewall Rules ───────────────────────────────────────────────────────────
resource "google_compute_firewall" "allow_web" {
  name    = "wingtradebot-allow-web"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = ["80", "443"]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["wingtradebot"]
}

resource "google_compute_firewall" "allow_ssh" {
  name    = "wingtradebot-allow-ssh"
  network = "default"

  allow {
    protocol = "tcp"
    ports    = [tostring(var.ssh_port)]
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["wingtradebot"]
}

resource "google_compute_firewall" "allow_icmp" {
  name    = "wingtradebot-allow-icmp"
  network = "default"

  allow {
    protocol = "icmp"
  }

  source_ranges = ["0.0.0.0/0"]
  target_tags   = ["wingtradebot"]
}

# ─── VM Instance ──────────────────────────────────────────────────────────────
resource "google_compute_instance" "trading" {
  name         = "wingtradebot-test"
  machine_type = var.machine_type
  zone         = var.zone
  tags         = ["wingtradebot"]

  boot_disk {
    initialize_params {
      image = "ubuntu-os-cloud/ubuntu-2404-lts-amd64"
      size  = 20 # GB
    }
  }

  network_interface {
    network = "default"

    access_config {
      # Attach the static IP
      nat_ip = google_compute_address.trading.address
    }
  }

  metadata = {
    ssh-keys = "root:${var.ssh_public_key}"
  }
}

# ─── Cloud SQL PostgreSQL ─────────────────────────────────────────────────────
# Uses free trial credits ($300). Smallest instance: db-f1-micro (0.6 GB RAM).
# NOTE: Cloud SQL has no permanent free tier — it uses your $300 trial credits.
# After credits are exhausted, db-f1-micro costs ~$7/month.
resource "google_sql_database_instance" "trading" {
  name             = "wingtradebot-db"
  database_version = "POSTGRES_16"
  region           = var.region

  settings {
    tier              = "db-f1-micro"  # Smallest available, uses trial credits
    availability_type = "ZONAL"        # Single zone (cheaper than REGIONAL)
    disk_size         = 10             # GB minimum
    disk_type         = "PD_SSD"

    ip_configuration {
      ipv4_enabled = true  # Public IP so migration tool can connect

      # Allow the VM to connect
      authorized_networks {
        name  = "wingtradebot-vm"
        value = "${google_compute_address.trading.address}/32"
      }

      # Allow your local machine to connect for migration
      # Replace with your actual IP: curl ifconfig.me
      authorized_networks {
        name  = "migration-tool-local"
        value = var.migration_tool_ip
      }
    }

    backup_configuration {
      enabled = true
    }
  }

  # Prevent accidental deletion
  deletion_protection = false
}

resource "google_sql_database" "trading" {
  name     = "wingtradebot"
  instance = google_sql_database_instance.trading.name
}

resource "google_sql_user" "trading" {
  name     = var.db_username
  instance = google_sql_database_instance.trading.name
  password = var.db_password
}
