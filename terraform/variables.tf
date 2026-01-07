variable "aws_region" {
  type        = string
  description = "AWS region"
  default     = "us-west-2"
}

variable "cluster_name" {
  type        = string
  description = "EKS cluster name"
  default     = "montecarlo-eks"
}

variable "vpc_cidr" {
  type        = string
  description = "VPC CIDR block"
  default     = "10.0.0.0/16"
}

variable "gpu_instance_type" {
  type        = string
  description = "GPU node instance type"
  default     = "g5.2xlarge"
}

variable "desired_gpu_nodes" {
  type        = number
  description = "Desired GPU node count"
  default     = 2
}

variable "s3_bucket_name" {
  type        = string
  description = "S3 bucket for results"
  default     = "montecarlo-results-example"
}
