# 1. FastAPI Gateway (Cloud Run Service)
resource "google_cloud_run_v2_service" "fastapi_gateway" {
  name     = "fastapi-gateway"
  location = var.region

  template {
    containers {
      image = var.gateway_image

      # Gunicorn ile production portu 8000 yerine Cloud Run default portu 8080 yapılabilir
      # ya da environment variable / command ile ezilebilir.
      command = ["gunicorn", "src.gateways.fastapi_gateway:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "-b", "0.0.0.0:8080"]

      ports {
        container_port = 8080
      }

      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.redis.host}:${google_redis_instance.redis.port}/0"
      }
      env {
        name  = "POSTGRES_URI"
        value = "postgresql://${google_sql_user.db_user.name}:${var.db_password}@${google_sql_database_instance.postgres.private_ip_address}:5432/${google_sql_database.database.name}"
      }
      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
    }

    # VPC Connector Bağlantısı
    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "ALL_TRAFFIC"
    }
  }
}

# 2. Redis Worker (Cloud Run Service)
resource "google_cloud_run_v2_service" "redis_worker" {
  name     = "redis-worker"
  location = var.region

  template {
    containers {
      image   = var.worker_image
      command = ["python", "-m", "src.gateways.ingress_mq"]

      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.redis.host}:${google_redis_instance.redis.port}/0"
      }
      env {
        name  = "POSTGRES_URI"
        value = "postgresql://${google_sql_user.db_user.name}:${var.db_password}@${google_sql_database_instance.postgres.private_ip_address}:5432/${google_sql_database.database.name}"
      }
      env {
        name  = "ENVIRONMENT"
        value = "production"
      }
    }

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "ALL_TRAFFIC"
    }
  }
}

# 3. Dashboard Frontend (Cloud Run Service)
resource "google_cloud_run_v2_service" "dashboard" {
  name     = "dashboard"
  location = var.region

  template {
    containers {
      image = var.dashboard_image

      ports {
        container_port = 8080
      }
    }

    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "ALL_TRAFFIC"
    }
  }
}

# --- Yetkilendirmeler (Public Access) ---

# Gateway için genel erişim izni
resource "google_cloud_run_v2_service_iam_member" "gateway_public" {
  name     = google_cloud_run_v2_service.fastapi_gateway.name
  location = google_cloud_run_v2_service.fastapi_gateway.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Dashboard için genel erişim izni
resource "google_cloud_run_v2_service_iam_member" "dashboard_public" {
  name     = google_cloud_run_v2_service.dashboard.name
  location = google_cloud_run_v2_service.dashboard.location
  role     = "roles/run.invoker"
  member   = "allUsers"
}
