# API Reference

The full interactive API documentation is available at `/docs` (Swagger UI) and `/redoc` when the backend is running.

## Authentication

All protected endpoints require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Obtain a token via `POST /api/auth/login`.

---

## Endpoints

### Auth

| Method | Path | Role | Description |
|--------|------|------|-------------|
| `POST` | `/api/auth/login` | Public | Local or LDAP login, returns JWT |
| `POST` | `/api/auth/logout` | Any | Invalidate token |
| `GET` | `/api/auth/me` | Any | Current user profile |
| `PUT` | `/api/auth/me/password` | Any | Change own password |

### Users

| Method | Path | Role | Description |
|--------|------|------|-------------|
| `GET` | `/api/users/` | Admin | List all users |
| `POST` | `/api/users/` | Admin | Create a local user |
| `PUT` | `/api/users/{id}` | Admin | Update user (role, active) |
| `DELETE` | `/api/users/{id}` | Admin | Deactivate user |

### vCenter

| Method | Path | Role | Description |
|--------|------|------|-------------|
| `GET` | `/api/vcenter/` | Any | List vCenter connections |
| `POST` | `/api/vcenter/` | Admin | Add a new vCenter connection |
| `PUT` | `/api/vcenter/{id}` | Admin | Update connection |
| `DELETE` | `/api/vcenter/{id}` | Admin | Remove connection |
| `POST` | `/api/vcenter/{id}/test` | Admin | Test connectivity |
| `GET` | `/api/vcenter/{id}/inventory` | Operator+ | Get live inventory snapshot |

### Analysis

| Method | Path | Role | Description |
|--------|------|------|-------------|
| `GET` | `/api/analysis/` | Any | List analysis runs (paginated) |
| `POST` | `/api/analysis/run` | Operator+ | Trigger a new analysis |
| `GET` | `/api/analysis/{id}` | Any | Get analysis run details |
| `GET` | `/api/analysis/{id}/findings` | Any | Get findings for a run |
| `POST` | `/api/analysis/{id}/apply-drs` | Operator+ | Apply DRS rule changes |
| `POST` | `/api/analysis/{id}/approve-storage/{finding_id}` | Operator+ | Approve a storage move proposal |

### Reports

| Method | Path | Role | Description |
|--------|------|------|-------------|
| `GET` | `/api/reports/` | Any | List reports |
| `GET` | `/api/reports/{id}` | Any | Get report details |
| `GET` | `/api/reports/{id}/export` | Any | Export report (`?format=pdf\|csv\|json`) |

### Settings

| Method | Path | Role | Description |
|--------|------|------|-------------|
| `GET` | `/api/settings/` | Admin | Get all settings |
| `PUT` | `/api/settings/` | Admin | Update settings (batch) |
| `GET` | `/api/settings/patterns` | Any | List Regex patterns |
| `POST` | `/api/settings/patterns` | Admin | Create pattern |
| `PUT` | `/api/settings/patterns/{id}` | Admin | Update pattern |
| `DELETE` | `/api/settings/patterns/{id}` | Admin | Delete pattern |
| `POST` | `/api/settings/ldap/test` | Admin | Test LDAP connection |
| `POST` | `/api/settings/logo` | Admin | Upload custom logo |

### Dashboard

| Method | Path | Role | Description |
|--------|------|------|-------------|
| `GET` | `/api/dashboard/summary` | Any | KPI counts and last-run status |
| `GET` | `/api/dashboard/recent-findings` | Any | Last 10 findings |
| `GET` | `/api/dashboard/audit-log` | Admin | Recent audit events |

---

## Response Format

All responses follow:

```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 100
  }
}
```

Errors:
```json
{
  "detail": "Human-readable error message",
  "code": "ERROR_CODE"
}
```

## Pagination

Paginated endpoints accept `?page=1&per_page=20`.

## Filtering

List endpoints accept `?search=`, `?status=`, `?severity=`, `?vcenter_id=` where applicable.
