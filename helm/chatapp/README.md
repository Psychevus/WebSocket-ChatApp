# ChatApp Helm Chart

This directory contains additional configuration for running the chart with Redis high availability.

Deploy using the HA values file:

```bash
helm upgrade chatapp ./deploy/helm --install \
  --values helm/chatapp/values-ha.yaml
```

After deployment, run the chart's tests:

```bash
helm test chatapp
```
