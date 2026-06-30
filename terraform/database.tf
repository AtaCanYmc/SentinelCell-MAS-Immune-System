# Özel IP bloğu ayrılması (Private Service Connection için)
resource "google_compute_global_address" "private_ip_alloc" {
  name          = "sentinel-private-ip-alloc"
  purpose       = "VPC_PEERING"
  address_type  = "INTERNAL"
  prefix_length = 16
  network       = google_compute_network.sentinel_vpc.id
}

# Özel Ağ Bağlantısı (Service Networking Connection)
resource "google_service_networking_connection" "private_vpc_connection" {
  network                 = google_compute_network.sentinel_vpc.id
  service                 = "servicenetworking.googleapis.com"
  reserved_peering_ranges = [google_compute_global_address.private_ip_alloc.name]
}

# Cloud SQL PostgreSQL Instance (PostgreSQL 16)
resource "google_sql_database_instance" "postgres" {
  name             = "sentinel-postgres-instance"
  database_version = "POSTGRES_16"
  region           = var.region

  depends_on = [google_service_networking_connection.private_vpc_connection]

  settings {
    tier = "db-f1-micro" # Geliştirme/test için micro (production için db-custom-x veya db-g1-small önerilir)

    ip_configuration {
      ipv4_enabled    = false # Genel internet erişimini devre dışı bırakır
      private_network = google_compute_network.sentinel_vpc.id
    }

    database_flags {
      name  = "shared_preload_libraries"
      value = "pgvector" # pgvector eklentisini yükler
    }
  }
}

# Veritabanı
resource "google_sql_database" "database" {
  name     = "sentinel_db"
  instance = google_sql_database_instance.postgres.name
}

# Veritabanı Kullanıcısı
resource "google_sql_user" "db_user" {
  name     = "sentinel"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}
