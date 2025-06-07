# Disaster Recovery with RDS

This project can use Amazon RDS to host the MySQL database. Automated backups provide a simple way to recover from data loss.

## Automated Snapshots

Set `backup_retention_period` to control how many days of automated backups are kept. The provided Terraform module configures seven days of retention and sets `preferred_backup_window` to `02:00-03:00` UTC so RDS creates a snapshot every day at that time.

## Restoring a Snapshot

You can trigger a manual snapshot at any time:

```bash
aws rds create-db-snapshot --db-snapshot-identifier chatapp-manual-$(date +%F) \
  --db-instance-identifier chatapp-db
```

Restoring from a snapshot creates a new database instance:

```bash
aws rds restore-db-instance-from-db-snapshot --db-instance-identifier chatapp-restore \
  --db-snapshot-identifier chatapp-manual-2024-01-01
```

## Point-in-Time Recovery

RDS also supports restoring to any second within the retention window. Specify the desired UTC time:

```bash
aws rds restore-db-instance-to-point-in-time --source-db-instance-identifier chatapp-db \
  --target-db-instance-identifier chatapp-pitr \
  --restore-time 2024-01-01T02:30:00Z
```

The new instance will contain data as it existed at that moment.
