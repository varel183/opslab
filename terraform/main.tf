provider "kubernetes" {
  config_path    = "~/.kube/config"
  config_context = var.kube_context
}

resource "kubernetes_resource_quota_v1" "opslab" {
  metadata {
    name      = "opslab-quota"
    namespace = var.namespace
  }

  spec {
    hard = {
      "requests.cpu"    = "2"
      "requests.memory" = "2Gi"
      "limits.cpu"      = "4"
      "limits.memory"   = "4Gi"
      "pods"            = "15"
    }
  }
}

resource "kubernetes_config_map_v1" "infra_metadata" {
  metadata {
    name      = "opslab-infra-metadata"
    namespace = var.namespace
  }

  data = {
    managed_by  = "terraform"
    environment = "local-learning"
  }
}

