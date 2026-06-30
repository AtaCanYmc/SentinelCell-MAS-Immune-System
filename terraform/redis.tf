# Memorystore for Redis Instance
resource "google_redis_instance" "redis" {
  name               = "sentinel-redis"
  tier               = "BASIC"
  memory_size_gb     = 1
  region             = var.region
  authorized_network = google_compute_network.sentinel_vpc.id

  redis_version = "REDIS_7_0"
  display_name  = "SentinelCell Message Queue and Cache"

  depends_on = [google_project_service.apis]
}
