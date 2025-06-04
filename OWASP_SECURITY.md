# OWASP Top 10 Checklist

This project considers the OWASP Top 10 (2021) during development. Review the following guidelines when deploying the application:

1. **Broken Access Control** – ensure that all views and WebSocket consumers enforce authentication and authorization. Review permissions on new endpoints.
2. **Cryptographic Failures** – configure `DJANGO_SECRET_KEY` and database credentials using strong secrets and enable HTTPS.
3. **Injection** – use Django ORM and parameterised queries. Avoid raw SQL when possible.
4. **Insecure Design** – validate input, enable CSRF protection and use Django forms for user input.
5. **Security Misconfiguration** – set `DEBUG` to `False` in production and configure allowed hosts and secure headers as shown in `settings.py`.
6. **Vulnerable and Outdated Components** – keep dependencies in `requirements.txt` updated and monitor for security patches.
7. **Identification and Authentication Failures** – enforce strong passwords with Django's validators and enable rate limiting.
8. **Software and Data Integrity Failures** – use signed packages and review dependency integrity when deploying.
9. **Security Logging and Monitoring Failures** – review log files stored in the `logs/` directory and integrate with monitoring systems.
10. **Server-Side Request Forgery** – validate and sanitize all external URLs and avoid exposing internal services.

These practices help secure the project against common threats.
