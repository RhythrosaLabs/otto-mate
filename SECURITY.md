# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly.

**DO NOT** open a public GitHub issue for security vulnerabilities.

Instead, please email security concerns to the repository owner through GitHub's private vulnerability reporting feature.

## Security Best Practices

When deploying Otto:

1. **Never commit `.env` files** — They are in `.gitignore` by default
2. **Use strong API keys** — Rotate keys regularly
3. **Use HTTPS** — Always deploy behind a reverse proxy with SSL
4. **Set rate limits** — Enable `RATE_LIMIT_ENABLED=true`
5. **Restrict CORS** — Don't use `*` in production
6. **Bind to localhost** — Use a reverse proxy instead of exposing directly

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest  | ✅        |
