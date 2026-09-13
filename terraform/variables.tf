variable "namespace" {
  description = "Existing Kubernetes namespace for OpsLab infrastructure controls."
  type        = string
  default     = "opslab"
}

variable "kube_context" {
  description = "kubectl context used by the Kubernetes provider."
  type        = string
  default     = "kind-opslab"
}
