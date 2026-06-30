output "gateway_url" {
  description = "FastAPI Gateway Cloud Run adresi"
  value       = google_cloud_run_v2_service.fastapi_gateway.uri
}

output "dashboard_url" {
  description = "Dashboard Frontend Cloud Run adresi"
  value       = google_cloud_run_v2_service.dashboard.uri
}

output "redis_host" {
  description = "Memorystore Redis IP adresi"
  value       = google_redis_instance.redis.host
}

output "postgres_private_ip" {
  description = "Cloud SQL Postgres Özel IP adresi"
  value       = google_sql_database_instance.postgres.private_ip_address
}
