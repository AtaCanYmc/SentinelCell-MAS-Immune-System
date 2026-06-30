# Özel VPC Ağı
resource "google_compute_network" "sentinel_vpc" {
  name                    = "sentinel-vpc"
  auto_create_subnetworks = false
  depends_on              = [google_project_service.apis]
}

# Özel Subnet
resource "google_compute_subnetwork" "sentinel_subnet" {
  name          = "sentinel-subnet"
  ip_cidr_range = "10.0.0.0/24"
  region        = var.region
  network       = google_compute_network.sentinel_vpc.id
}

# Serverless VPC Access Connector (Cloud Run'ın VPC içine erişebilmesi için)
resource "google_vpc_access_connector" "connector" {
  name          = "sentinel-connector"
  region        = var.region
  ip_cidr_range = "10.8.0.0/28"
  network       = google_compute_network.sentinel_vpc.name
  depends_on    = [google_project_service.apis]
}
