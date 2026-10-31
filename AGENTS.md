# Codex development guidance

Read README.md, docs/SPEC.md, docs/DEPLOY.md and docs/TEST_REPORT.md first.
This is a Japanese single-company construction app for up to 10 active users.

- Use Django 5.2 and PostgreSQL in production. SQLite is local development only.
- Every page/export/mutation must check server-side role permissions. Do not expose financial values to site users.
- Preserve CSRF protection, DB-backed sessions, decimal currency, optimistic edit version checks, transaction audit records, and the SeatLock row for user capacity changes.
- Never commit real customer data, databases, credentials, uploads or backups. Tests use fictional values only.
- Add migrations for model changes. Do not reuse the old prototype SQLite DB.
- Run `python manage.py test` and `python manage.py makemigrations --check --dry-run` with DEBUG=1 and a disposable SECRET_KEY of at least 50 characters. PostgreSQL tests run in CI.
- No cloud provisioning, paid services or real customer-data insertion without explicit authorization.
- Do not claim load, browser, PostgreSQL, Docker or cloud tests passed unless actually run. Update docs/TEST_REPORT.md with evidence and remaining limits.
