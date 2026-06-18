# Changelog

All notable changes to **vSphere Compliance Manager** are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

---

## [1.2.4] — 2026-06-17

### Fixed
- Fix `AttributeError: 'NoneType' has no attribute 'host'` in auth login endpoint
  when running under TestClient (request.client is None in test environment)
- Add `src/vite-env.d.ts` — fixes `Property 'env' does not exist on type 'ImportMeta'`
- Revert SHA-pinned actions back to simple version tags (`@v4`, `@v5`, `@v6`)
  SHA pinning caused `unable to find version` errors for upload-artifact
- Node.js 20 deprecation warnings are informational only — GitHub forces Node 24
  automatically, so `@v4` tags work correctly despite the warning

---

## [1.2.3] — 2026-06-17

### Fixed
- Pin `bcrypt==4.0.1` in requirements.txt — newer bcrypt removed `__about__` attribute
  causing passlib to fail with `ValueError: password cannot be longer than 72 bytes`
- Add `frontend/index.html` — Vite entry point was missing, causing build failure
  `Could not resolve entry module "index.html"`
- Add `src/main.tsx`, `src/App.tsx`, `src/index.css` — React entry files
- Add `tailwind.config.js` and `postcss.config.js` for Tailwind CSS
- Add stub pages (Dashboard, Analysis, Reports, Settings, Users) so build passes
- Add `src/store/authStore.ts`, `src/utils/api.ts`, layout and route components
- Add `public/favicon.svg`
- Pin all GitHub Actions by full commit SHA for guaranteed Node.js 24 compatibility:
  - `actions/checkout` → `11bd719...` (v4.2.2)
  - `actions/setup-python` → `0b93645...` (v5.3.0)
  - `actions/setup-node` → `39370e3...` (v4.1.0)
  - `docker/login-action` → `9780b0c...` (v3.3.0)
  - `docker/setup-buildx-action` → `f7ce87c...` (v3.9.0)
  - `docker/metadata-action` → `369eb59...` (v5.6.1)
  - `docker/build-push-action` → `ca052bb...` (v6.14.0)
  - `actions/upload-artifact` → `65c4c4a...` (v4.6.0)
  - `softprops/action-gh-release` → `da05d55...` (v2.2.1)
- Remove govmomi vcsim from CI — requires Go 1.25 (not yet stable)

---

## [1.2.2] — 2026-06-18

### Fixed
- Remove `cache` option from `setup-python` and `setup-node` in CI — fixes `Cache service 400` error caused by missing `package-lock.json`
- Replace pinned action patch versions with major-only tags (e.g. `@v4`, `@v5`) to avoid Node.js 20 deprecation warnings
- Remove `|| true` suppression from lint steps — lint now properly fails the job on errors
- Add `continue-on-error: true` only on codecov upload (non-critical)

### Added
- vcsim integration test suite (`tests/vcsim/`)
- `conftest.py` with `vcenter_service`, `inventory`, `random_patterns`, `session_seed` fixtures
- `test_vcsim.py`: 13 tests across connectivity, DRS compliance, and storage compliance
- Randomized VM pattern selection per test session for broader scenario coverage
- `docs/vcsim-testing.md` — full guide for local and CI vcsim usage
- vcsim job added to CI pipeline using Go install + background process
- vcsim section added to README development guide

---

## [1.2.2] — 2026-06-17

### Fixed
- Remove version pinning from GitHub Actions — use major tags (`@v4`, `@v5`, `@v6`)
  to always get latest Node.js 24 compatible runner
- Remove `cache:` from `setup-python` and `setup-node` (was causing Cache 400 errors
  because `package-lock.json` doesn't exist until `npm install` runs)
- Switch `npm ci` → `npm install` in frontend CI jobs (no lock file yet)
- Switch frontend Node.js from 22 back to latest via `node-version: "22"` without cache

### Added
- Pure-Python vCenter inventory simulator (`tests/fixtures/vcenter_sim.py`)
  - Generates randomized realistic vCenter inventory each test run
  - Covers: clusters, hosts, VM groups, datastores, DS clusters, scattered VMs, ISO mounts
  - Configurable seed for reproducing failures
- `test_vcsim.py` — 14 randomized tests covering DRS and storage engine
- `conftest.py` — auto-imports all fixtures project-wide
- `docs/testing/README.md` — full testing guide including vcsim and govmomi Docker usage

---

## [1.2.1] — 2026-06-17

### Fixed
- Replace `python-ldap` (requires C compiler + system libs) with `ldap3` (pure Python)
- Remove `libldap2-dev` and `libsasl2-dev` from Dockerfile — Docker build now succeeds
- Upgrade all GitHub Actions to Node.js 24 compatible versions:
  - `actions/checkout` → v4.2.2
  - `actions/setup-python` → v5.3.0
  - `actions/setup-node` → v4.2.0
  - `actions/upload-artifact` → v4.6.0
  - `docker/login-action` → v3.3.0
  - `docker/setup-buildx-action` → v3.9.0
  - `docker/metadata-action` → v5.6.1
  - `docker/build-push-action` → v6.14.0
  - `codecov/codecov-action` → v5.1.2
  - `softprops/action-gh-release` → v2.2.1
- Switch frontend Node.js from 20 (deprecated) to 22 in CI

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

[Unreleased]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.2.4...HEAD
[1.2.4]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.2.3...v1.2.4
[1.2.3]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.2.2...v1.2.3
[1.2.2]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.2.1...v1.2.2
[1.2.1]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.2.0...v1.2.1
[1.2.0]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.1.0...v1.2.0
[1.1.0]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.0.0...v1.1.0
[1.0.0]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/releases/tag/v1.0.0
