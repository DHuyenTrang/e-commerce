# SQL Mock Data Import

Run after Docker Compose services and migrations are up:

```powershell
.\scripts\import_mock_data.ps1
```

The runner copies SQL files into `ecom_postgres` and executes them with `psql`.
Each domain table in the implemented services gets at least 10 mock records.
Django core tables such as `auth_user`, `auth_group`, `django_session`, and `django_admin_log` are also seeded in every service database.
