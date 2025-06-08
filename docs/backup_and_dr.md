# Backup and Disaster Recovery

This runbook outlines how to create manual snapshots and perform point-in-time restores for the production database.

## Manual Snapshot

Create a snapshot of the RDS instance:

```bash
aws rds start-db-snapshot --db-snapshot-identifier chatapp-manual-$(date +%F) \
  --db-instance-identifier chatapp-db
```

## Point-in-Time Restore

To restore to a specific moment within the retention window:

```bash
aws rds restore-db-instance-to-point-in-time \
  --source-db-instance-identifier chatapp-db \
  --target-db-instance-identifier chatapp-pitr \
  --restore-time 2024-01-01T02:30:00Z
```

Follow the AWS console prompts to promote the restored instance once validated.
