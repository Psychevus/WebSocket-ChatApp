# Scaling WebSocket ChatApp

This document outlines common approaches for horizontally scaling the chat application and securing deployments for enterprise environments. The container and Kubernetes manifests use **Daphne** as the ASGI server to maximise concurrency for WebSocket traffic.

## Horizontal Pod Autoscaling
- Deploy the application on Kubernetes using the provided Helm chart or Kustomize overlays.
- Enable a HorizontalPodAutoscaler to automatically adjust the number of Daphne worker pods based on CPU or custom metrics.
- Redis and MySQL can be run in managed services like Amazon ElastiCache and RDS for better reliability.

## Database and Cache
- Use a managed MySQL cluster with primary/replica topology.
- Configure Redis in a highly available mode with persistence enabled.

## Security Considerations
- Enforce HTTPS everywhere and terminate TLS with a modern cipher suite.
- Rotate secrets using your cloud provider's secret manager.
- Review [`OWASP_SECURITY.md`](../OWASP_SECURITY.md) for a checklist of common hardening steps.

## Observability
- Export metrics to Prometheus as shown in `prometheus.yml` and visualise them with Grafana.
- Enable tracing via OpenTelemetry for deeper insights into latency bottlenecks.

When running multiple Daphne instances, route traffic through a load balancer that supports sticky sessions or configure Redis as the channel layer's backend for shared state. These guidelines provide a baseline for operating the application at scale in production environments.
