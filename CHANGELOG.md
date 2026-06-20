# Changelog

All notable changes to **vSphere Compliance Manager** are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Status:** This project is currently in **active development**.
> No stable release has been published yet.
> All releases prior to `v1.0.0` are considered pre-release / beta.

---

## [Unreleased]

---

## [1.3.2-beta] — 2026-06-19

### Changed
- Add `org.opencontainers.image.source`, `.description`, and `.licenses` labels
  to all Docker images in both CI and Release workflows — this links Packages
  to the repository automatically on GHCR so they appear under the repo's
  Packages sidebar
  library calls — `passlib 1.7.4` is incompatible with `bcrypt 4.x` and silently
  fails password verification, causing all logins to return 401
- Remove `passlib` from requirements entirely; `security.py` now uses
  `bcrypt.checkpw()` and `bcrypt.hashpw()` directly
- Upgrade `bcrypt` to `4.1.3` (latest stable)
- Admin user and default patterns now created automatically on first startup
  via `seed_initial_data()` inside FastAPI lifespan — no manual seed step needed
- Fix broken `#documentation` anchor in README header → `#api-reference`
- Fix vcsim image to `vmware/vcsim:latest` (Docker Hub Verified Publisher)
- Fix vcsim startup flag from deprecated `-httptest.serve` to `-l`

---

## [1.3.1-beta] — 2026-06-19

### Fixed
- Remove duplicate `scripts/seed_vcsim.py` (canonical location: `docs/vcsim/seed_vcsim.py`)
- Remove duplicate `docker-compose.test.yml` (superseded by `docs/vcsim/docker-compose.vcsim.yml`)
- Remove stale `backend/tests/vcsim/` directory (live vcsim tests moved to `backend/tests/unit/test_vcsim.py`)
- Fix vcsim image address across all files: use `vmware/vcsim:latest` (Docker Hub, Verified Publisher) instead of incorrect `ghcr.io/vmware/govmomi/vcsim:latest`
- Fix vcsim startup flag: `-httptest.serve` → `-l` (current govmomi API)
- All GHCR image references now use lowercase `davoudteimouri` (Docker registry is case-sensitive)

### Changed
- Release workflow now produces downloadable assets attached to every GitHub Release:
  - `vcm-deployment-{version}.zip` / `.tar.gz` — Docker Compose bundle with pinned image version
  - `vcm-vcsim-test-{version}.zip` — vcsim test environment bundle
  - Both bundles contain `seed_vcsim.py`, `.env.example`, and `README.md`
- Release body now includes compatibility table and links to all documentation

---

## [1.3.0-beta] — 2026-06-17

### Added
- `docs/vcsim/README.md` — complete vcsim testing guide (English)
- `docs/vcsim/seed_vcsim.py` — randomized VM naming script for vcsim
  - `--seed` flag for reproducible inventory
  - `--prefixes` and `--envs` flags for different test scenarios
  - `--dry-run` flag to preview renames before applying
  - Automatic Datastore renaming
  - Full inventory summary after seeding
- `docs/vcsim/docker-compose.vcsim.yml` — full test stack using published GHCR images
  - Supports `BACKEND_TAG` and `FRONTEND_TAG` environment variables
  - Covers vcsim + PostgreSQL + Redis + Backend + Frontend
- Test scenarios documented: DRS, Storage, Full Analysis with Apply, randomized regression
- Release workflow now includes Docker image tags and pull commands in release body

### Changed
- All documentation converted to English
- Removed `docs/vcsim-testing.md` (merged into `docs/vcsim/README.md`)

### Fixed
- Release workflow: Docker job outputs now correctly passed to Release body
  so image tags appear in the GitHub Release page
- `docker-compose.vcsim.yml` uses `BACKEND_TAG` / `FRONTEND_TAG` env vars
  defaulting to `main` branch image

---

## [1.2.5-beta] — 2026-06-17

### Fixed
- Replace `npm ci` with `npm install` in frontend Dockerfile
- Upgrade frontend Docker base image from `node:20-alpine` to `node:22-alpine`

---

## [1.2.4-beta] — 2026-06-17

### Fixed
- `AttributeError: 'NoneType' has no attribute 'host'` in auth login endpoint
  under TestClient (request.client is None in test environment)
- Add `src/vite-env.d.ts` to fix `Property 'env' does not exist on type 'ImportMeta'`
- Revert SHA-pinned actions to simple version tags

---

## [1.2.3-beta] — 2026-06-17

### Fixed
- Pin `bcrypt==4.0.1` — passlib incompatibility with newer bcrypt versions
- Add `frontend/index.html` — Vite entry point was missing
- Add `src/main.tsx`, `App.tsx`, `index.css`, `tailwind.config.js`, `postcss.config.js`
- Add stub pages: Dashboard, Analysis, Reports, Settings, Users
- Add `authStore.ts`, `api.ts`, Layout, ProtectedRoute, LoginPage, favicon

---

## [1.2.2-beta] — 2026-06-17

### Fixed
- Remove version pinning from GitHub Actions
- Remove `cache:` from `setup-python` and `setup-node` (Cache 400 errors)

### Added
- Pure-Python vCenter inventory simulator (`tests/fixtures/vcenter_sim.py`)
- `test_vcsim.py` — 14 randomized tests for DRS and storage engine
- `conftest.py` — project-wide fixture availability
- `docs/testing/README.md` — testing guide

---

## [1.2.1-beta] — 2026-06-17

### Fixed
- Replace `python-ldap` with `ldap3` (pure Python, no C compiler required)
- Remove `libldap2-dev` and `libsasl2-dev` from Dockerfile
- Rewrite `ldap_service.py` using ldap3 library
- Upgrade all GitHub Actions to Node.js 24 compatible versions

---

## [1.2.0-beta] — 2026-06-17

### Added
- Complete CI workflow: backend lint, unit tests, integration tests, coverage
- Complete Release workflow: builds Docker images then creates GitHub Release
- Docker images published to GHCR with `latest`, branch, semver, and sha tags
- Backend unit tests: `test_analysis_engine.py` (15 cases), `test_security.py` (12 cases)
- Backend integration tests: `test_api.py` covering auth, users, dashboard, patterns
- `pytest.ini` configuration
- Frontend test setup: Vitest + jsdom + Testing Library
- Frontend utility tests: `utils.test.ts` (14 cases)
- `vitest.config.ts` with coverage reporting

---

## [1.1.0-beta] — 2026-06-17

### Added
- All backend API routers: `auth`, `users`, `vcenter`, `analysis`, `reports`, `settings`, `dashboard`
- Core modules: `config.py`, `database.py`, `deps.py`, `scheduler.py`
- Alembic migration setup (`alembic.ini` + `alembic/env.py`)
- Database seed script with default admin user and patterns
- JWT + LDAP dual authentication
- DRS apply endpoint via pyVmomi
- Storage move approval workflow
- Report export (JSON, CSV)
- Logo upload and LDAP test endpoints
- AES-256 encryption for stored credentials
- Frontend scaffold: React 18, Vite, TypeScript, Tailwind CSS

### Fixed
- Removed broken `github.io` Helm repo reference from README
- Replaced all email addresses with GitHub Issues links
- Replaced all `your-org` placeholders with `DavoudTeimouri`
- Fixed logo path to `docs/screenshots/logo.svg` at 400×400

---

## [1.0.0-beta] — 2026-06-17

### Added
- Core FastAPI backend with PostgreSQL persistence
- React 18 frontend with role-aware UI
- vCenter integration via pyVmomi (v6.x–v8.x)
- DRS Anti-Affinity compliance engine with Regex-based VM grouping
- Storage placement compliance engine (per-disk, ISO-aware)
- Scattered VM detection and consolidation proposals
- RBAC: Admin / Operator / Viewer roles
- Local authentication (bcrypt) + LDAP/AD integration
- JWT session tokens with configurable expiry
- AES-256 encryption for all stored credentials
- Full analysis history and audit log
- Scheduled analysis via APScheduler
- Docker Compose, Kubernetes manifests (Kustomize + overlays)
- GitHub Actions CI/CD pipeline
- Swagger UI and ReDoc API documentation
- Custom logo upload (white-labeling)

---

[Unreleased]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.3.2-beta...HEAD
[1.3.2-beta]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.3.1-beta...v1.3.2-beta
[1.3.1-beta]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.3.0-beta...v1.3.1-beta
[1.3.0-beta]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.2.5-beta...v1.3.0-beta
[1.2.5-beta]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.2.4-beta...v1.2.5-beta
[1.2.4-beta]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.2.3-beta...v1.2.4-beta
[1.2.3-beta]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.2.2-beta...v1.2.3-beta
[1.2.2-beta]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.2.1-beta...v1.2.2-beta
[1.2.1-beta]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.2.0-beta...v1.2.1-beta
[1.2.0-beta]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.1.0-beta...v1.2.0-beta
[1.1.0-beta]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.0.0-beta...v1.1.0-beta
[1.0.0-beta]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/releases/tag/v1.0.0-beta
