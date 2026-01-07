# Terraform (AWS)

This is a minimal EKS + S3 + GPU node group scaffold.

## Usage

```bash
terraform init
terraform apply \
  -var 's3_bucket_name=your-unique-bucket-name'
```

After apply:

```bash
aws eks update-kubeconfig --region us-west-2 --name montecarlo-eks
```

Adjust variables in `variables.tf` or via `-var` flags for region, instance type, and node counts.
