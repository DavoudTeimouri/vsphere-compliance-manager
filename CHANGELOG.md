## [Unreleased]

---

## [1.3.6-beta] — 2026-06-24

### Fixed
- **Critical startup crash:** `CREATE TYPE userrole AS ENUM` failed with
  `UniqueViolation` when PostgreSQL volume already existed from a previous run.
  Root cause: SQLAlchemy `create_all()` does not check if ENUM types already
  exist in PostgreSQL. Fixed by:
  1. All `Column(Enum(...))` changed to `Column(ENUM(..., create_type=False))`
     in `models.py` — tells SQLAlchemy never to emit `CREATE TYPE`
  2. New `create_enums()` function in `database.py` uses PostgreSQL
     `DO $$ BEGIN CREATE TYPE ... EXCEPTION WHEN duplicate_object THEN NULL END $$`
     — idempotent, safe on every startup whether DB is new or existing
  3. `init_db()` replaces bare `create_all()` in `main.py` lifespan
- Remove obsolete `version:` field from all docker-compose files
  (caused warning: "the attribute version is obsolete")

## [1.3.5-beta] — 2026-06-19

### Fixed
- **Password (root cause):** `auth.py` login path rewritten with separated
  LDAP and local branches, explicit logging at each failure point so the
  exact reason for 401 is visible in container logs
- `reset_admin.py` now accepts `--verify` flag to confirm bcrypt roundtrip
  works after setting the password
- `seed_initial_data()` logs `"Admin user created"` on startup so you can
  confirm in logs that seeding ran

### Added
- `app/core/logging_config.py` — structured logging module:
  - `JSONFormatter` for production (one JSON object per line)
  - `HumanFormatter` with ANSI colors for development
  - `setup_logging()` called at startup in `main.py`
  - `get_logger(name)` helper for all modules
  - Request timing middleware: every HTTP request logged with method,
    path, status code, and duration in ms
  - Global exception handler: unhandled 500s logged with path and error
  - Noisy third-party loggers (uvicorn.access, apscheduler, sqlalchemy)
    silenced to WARNING
- `app/worker.py` — standalone background worker entry point
- `app/schemas/schemas.py` — all Pydantic request/response models
- `app/utils/helpers.py` — paginate(), sanitize_regex(), mask_secret(),
  fingerprint()

### Changed
- `docker-compose.yml` — production compose restructured:
  - Redis now uses `--appendonly yes` for persistence
  - `PGDATA` set explicitly to avoid data loss on upgrade
  - All volumes have explicit `name:` and `driver: local`
  - `POSTGRES_PASSWORD` extracted to env variable
- `docker-compose.dev.yml` — dev compose restructured:
  - Uses build targets instead of images
  - Adds pgAdmin and RedisInsight for debugging
- `docs/vcsim/docker-compose.vcsim.yml` — test environment mirrors
  production structure (named volumes, Redis persistence, PGDATA)
- `.env.example` — `POSTGRES_PASSWORD` added as separate variable
- `k8s/overlays/dev/` and `k8s/overlays/staging/` — created
- Stale `k8s/base/volumes.yaml` and `secrets-template.yaml` removed
- README TOC: all `#` comments removed from code blocks (root cause
  of scroll-to-top bug); zero broken anchors verified programmatically

## [1.3.4-beta] — 2026-06-19

### Changed
- README completely rewritten with clean structure:
  - All headings are real Markdown headings, no bash comment headings inside code blocks
  - TOC uses H2-only anchors — all 19 links verified correct
  - Added Volumes and Data section with Docker and Kubernetes details
  - Added Logging section with Docker and Kubernetes commands
  - Added Scaling section with HPA details and manual commands
  - Added Documentation table linking all guides
  - All GitHub links lowercased (github.com/davoudteimouri)
  - GHCR image links remain lowercase (davoudteimouri)
- CI workflow: Docker build job removed — images built only by release.yml on tag push
- Kubernetes manifests restructured:
  - PostgreSQL and Redis use StatefulSet with volumeClaimTemplates
  - Volumes split: k8s/base/volumes/pvc-uploads.yaml, pvc-postgres.yaml, pvc-redis.yaml
  - Backend adds HPA (min 2, max 6) and initContainer
  - Frontend Ingress adds /uploads path
- All GitHub repo links in docs converted to lowercase
- Version pinned to 1.3.4-beta in all compose files and k8s overlays

# Changelog

All notable changes to **vSphere Compliance Manager** are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Status:** This project is currently in **active development**.
> No stable release has been published yet.
> All releases prior to `v1.0.0` are considered pre-release / beta.

---

## [1.3.4-beta] — 2026-06-19

### Changed
- **CI workflow:** Removed Docker build job entirely — images are now built
  ONLY by `release.yml` on tag push, preventing unversioned `:main` images
  from being pushed to GHCR on every commit
- **README TOC:** Simplified to H2-only links — sub-items caused scroll
  failures in some browsers
- **Kubernetes manifests completely restructured:**
  - PostgreSQL converted from Deployment to `StatefulSet` with
    `volumeClaimTemplates` — Kubernetes manages PVCs automatically
  - Redis converted from Deployment to `StatefulSet` with
    `volumeClaimTemplates` and persistence enabled (`appendonly yes`)
  - Volumes split into separate files under `k8s/base/volumes/`:
    `pvc-uploads.yaml`, `pvc-postgres.yaml`, `pvc-redis.yaml`
  - Backend manifest adds `HorizontalPodAutoscaler` (min 2, max 6 replicas)
    and `initContainer` to wait for PostgreSQL before starting
  - Frontend manifest adds `/uploads` path to Ingress
  - All image paths lowercased (`davoudteimouri` not `DavoudTeimouri`)
  - `kustomization.yaml` updated to include all new resources
  - Prod overlay patches for StorageClass, replica counts, and hostname
- **Deployment guide completely rewritten** with:
  - Volume details and backup/restore commands for both Docker and K8s
  - Upgrade procedure for both Compose and Kubernetes
  - Production checklist
  - Admin password reset instructions

---

## [1.3.3-beta] — 2026-06-19

### Fixed
- All Docker image references now use pinned release tag `1.3.3-beta` instead
  of `main` — `main` is a branch tag that changes with every push and pulls
  potentially broken images
- All GHCR image paths converted to lowercase (`davoudteimouri` not `DavoudTeimouri`)
  — Docker registry is case-sensitive and uppercase paths silently fail on some hosts
- `docker-compose.yml` now uses GHCR images with `VCM_VERSION` variable
  (default `1.3.3-beta`) instead of building from source
- `docker-compose.vcsim.yml` uses `VCM_VERSION` variable consistently
- All volumes now have explicit `name:` fields to prevent name collisions
- `k8s/base/backend.yaml` and `k8s/base/frontend.yaml` image paths lowercased
- `k8s/overlays/prod/kustomization.yaml` image tags pinned to `1.3.3-beta`
- `docs/deployment/README.md` Helm tag updated to `1.3.3-beta`
- `docs/vcsim/README.md` pull commands updated to `1.3.3-beta`
- Add `scripts/reset_admin.py` — resets or creates admin user from inside container:
  ```bash
  docker exec vcm-test-backend python scripts/reset_admin.py
  docker exec vcm-test-backend python scripts/reset_admin.py --password "NewPass@123"
  ```
- `scripts/seed.py` updated with verbose output visible in container logs
- Add OCI image labels to CI and Release workflows — links packages to repository
  on GHCR automatically

### Changed
- Image tag strategy: `VCM_VERSION` env var controls which image is pulled;
  update this variable on every upgrade instead of editing individual files

---

## [1.3.3-beta] — 2026-06-19

### Fixed
- Add `scripts/reset_admin.py` — resets admin password or creates admin user
  from inside the container when login fails:
  ```bash
  docker exec vcm-test-backend python scripts/reset_admin.py
  docker exec vcm-test-backend python scripts/reset_admin.py --password "NewPass@123"
  ```
- Update `scripts/seed.py` with verbose output so startup issues are visible in logs
- Add `scripts/__init__.py`

### Changed
- Add OCI image labels to CI and Release workflows so packages appear
  linked under repository sidebar on GHCR

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

[Unreleased]: https://github.com/davoudteimouri/vsphere-compliance-manager/compare/v1.3.4-beta...HEAD
[1.3.4-beta]: https://github.com/davoudteimouri/vsphere-compliance-manager/compare/v1.3.3-beta...v1.3.4-beta
[1.3.3-beta]: https://github.com/davoudteimouri/vsphere-compliance-manager/compare/v1.3.2-beta...v1.3.3-beta
[1.3.2-beta]: https://github.com/davoudteimouri/vsphere-compliance-manager/compare/v1.3.1-beta...v1.3.2-beta
[1.3.1-beta]: https://github.com/davoudteimouri/vsphere-compliance-manager/compare/v1.3.0-beta...v1.3.1-beta
[1.3.0-beta]: https://github.com/davoudteimouri/vsphere-compliance-manager/compare/v1.2.5-beta...v1.3.0-beta
[1.2.5-beta]: https://github.com/davoudteimouri/vsphere-compliance-manager/compare/v1.2.4-beta...v1.2.5-beta
[1.2.4-beta]: https://github.com/davoudteimouri/vsphere-compliance-manager/compare/v1.2.3-beta...v1.2.4-beta
[1.2.3-beta]: https://github.com/davoudteimouri/vsphere-compliance-manager/compare/v1.2.2-beta...v1.2.3-beta
[1.2.2-beta]: https://github.com/davoudteimouri/vsphere-compliance-manager/compare/v1.2.1-beta...v1.2.2-beta
[1.2.1-beta]: https://github.com/davoudteimouri/vsphere-compliance-manager/compare/v1.2.0-beta...v1.2.1-beta
[1.2.0-beta]: https://github.com/davoudteimouri/vsphere-compliance-manager/compare/v1.1.0-beta...v1.2.0-beta
[1.1.0-beta]: https://github.com/davoudteimouri/vsphere-compliance-manager/compare/v1.0.0-beta...v1.1.0-beta
[1.0.0-beta]: https://github.com/davoudteimouri/vsphere-compliance-manager/releases/tag/v1.0.0-beta
