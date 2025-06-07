# RDS Module

This Terraform module provisions an Amazon RDS instance with a 7 day backup retention period and schedules automated backups for 02:00‑03:00 UTC.

```hcl
module "chatapp_db" {
  source = "./terraform/rds"

  identifier           = "chatapp-db"
  username             = "admin"
  password             = "changeme"
  db_subnet_group_name = "rds-subnet-group"
  vpc_security_group_ids = ["sg-12345678"]
}
```
