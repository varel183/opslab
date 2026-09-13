output "managed_namespace" {
  description = "Namespace where Terraform installed infrastructure controls."
  value       = var.namespace
}

output "resource_quota_name" {
  description = "Name of the quota created by Terraform."
  value       = kubernetes_resource_quota_v1.opslab.metadata[0].name
}

