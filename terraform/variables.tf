variable "project_id" {
  description = "Google Cloud Proje ID'si"
  type        = string
}

variable "region" {
  description = "Kaynakların kurulacağı GCP Bölgesi (Region)"
  type        = string
  default     = "europe-west3" # Frankfurt
}

variable "db_password" {
  description = "PostgreSQL sentinel kullanıcısı şifresi"
  type        = string
  sensitive   = true
}

variable "gateway_image" {
  description = "FastAPI Gateway Docker Image adresi (örn. ghcr.io veya GCR/AR adresi)"
  type        = string
  default     = "gcr.io/my-project/sentinelcell-backend:latest"
}

variable "worker_image" {
  description = "Redis Worker Docker Image adresi"
  type        = string
  default     = "gcr.io/my-project/sentinelcell-backend:latest"
}

variable "dashboard_image" {
  description = "Dashboard Frontend Docker Image adresi"
  type        = string
  default     = "gcr.io/my-project/sentinelcell-dashboard:latest"
}
