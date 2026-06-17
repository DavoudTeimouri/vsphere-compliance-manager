# Changelog

All notable changes to **vSphere Compliance Manager** are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [1.2.0] — 2026-06-17

### Added
- Complete CI workflow with backend lint, unit tests, integration tests, and coverage report
- Complete Release workflow: builds Docker images with version tags then creates GitHub Release
- Docker images published to GHCR with `latest`, `semver`, `branch`, and `sha` tags
- SBOM and provenance attestation on all Docker images
- Backend unit tests: `test_analysis_engine.py` (15 cases), `test_security.py` (12 cases)
- Backend integration tests: `test_api.py` covering auth, users, dashboard, patterns
- `pytest.ini` configuration
- Frontend test setup with Vitest + jsdom + Testing Library
- Frontend utility tests: `utils.test.ts` (14 cases)
- `vitest.config.ts` with coverage reporting

---

## [1.1.0] — 2026-06-17

### Added
- All backend API routers: `auth`, `users`, `vcenter`, `analysis`, `reports`, `settings`, `dashboard`
- Core modules: `config.py`, `database.py`, `deps.py`, `scheduler.py`
- Alembic migration setup (`alembic.ini` + `alembic/env.py`)
- Database seed script with default admin user and sample patterns
- JWT + LDAP dual authentication flow in auth router
- DRS apply endpoint — creates Anti-Affinity rules via pyVmomi
- Storage move approval workflow with audit trail
- Report export in JSON and CSV formats
- Logo upload endpoint (PNG, JPEG, SVG)
- LDAP connection test endpoint
- AES-256 encryption for all sensitive settings stored in DB
- Frontend scaffold: `package.json`, `vite.config.ts`, `tsconfig.json`

### Fixed
- Removed broken `github.io` Helm repo reference from README
- Replaced all email addresses with GitHub Issues links (SECURITY.md, CODE_OF_CONDUCT.md)
- Replaced all `your-org` placeholders with `DavoudTeimouri`
- Fixed logo path to `docs/screenshots/logo.svg` at 400×400

---

## [1.0.0] — 2026-01-01

### Added
- Core FastAPI backend with PostgreSQL persistence
- React 18 frontend with role-aware UI
- vCenter integration via pyVmomi (v6.x – v8.x support)
- DRS Anti-Affinity compliance engine with Regex-based VM grouping
- Storage placement compliance engine (per-disk, ISO-aware)
- Scattered VM detection and consolidation proposals
- RBAC: Admin / Operator / Viewer roles
- Local authentication with bcrypt password hashing
- LDAP / Active Directory integration with group-to-role mapping
- JWT session tokens with configurable expiry
- AES-256 encryption for all stored credentials and sensitive settings
- Analysis history with full finding details
- DRS rule create/delete history per cluster
- Storage move approval workflow with audit trail
- Scheduled analysis (cron-based via APScheduler)
- PDF, CSV, and JSON report export
- Custom logo upload (white-labeling)
- Docker Compose setup for single-node deployment
- Kubernetes manifests (Kustomize base + overlays)
- Helm chart with configurable values
- GitHub Actions CI pipeline (lint, test, build, push)
- Swagger UI and ReDoc API documentation

---

[Unreleased]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.2.0...HEAD
[1.2.0]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/releases/tag/v1.0.0
