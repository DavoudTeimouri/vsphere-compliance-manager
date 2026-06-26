# Changelog

All notable changes to **vSphere Compliance Manager** are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

> **Status:** This project is currently in **active development**.
> No stable release has been published yet.
> All releases prior to `v1.0.0` are considered pre-release / beta.

---

## [Unreleased]

### In Progress
- Frontend rewrite with full API integration (analysis, reports, settings, dashboard)
- Backend API hardening and additional test coverage

---

## [1.3.8-beta] — 2026-06-26

### Fixed
- **Build:** Removed unused imports causing TypeScript TS6133 build failure in CI
  - `AnalysisPage.tsx`: removed `useEffect`, `CheckCircle`, `XCircle`
  - `SettingsPage.tsx`: removed `Upload`
- **README:** Complete rewrite with cleaner structure, concise layout, proper heading hierarchy
- **ReportsPage:** Separated list and detail views with proper routing

### Added
- `AnalysisPage`: Full vCenter connection management (add, test, delete) with modal dialogs
- `AnalysisPage`: Run Analysis form with vCenter/type selection wired to API
- `SettingsPage`: Full pattern CRUD with modal, LDAP connection test button
- `ReportDetailPage`: Findings table with severity filtering, DRS apply, storage move approval
- `App.tsx`: Added `/reports/:id` route for report detail view

---

## [1.3.7-beta] — 2026-06-26

### Fixed
- **Security:** Removed hardcoded credentials from `docker-compose.dev.yml` — passwords now use `${ENV_VAR:-default}` pattern
- **Security:** Removed hardcoded `SECRET_KEY`, `ADMIN_PASSWORD`, `ADMIN_USERNAME` from dev compose — must be set via `.env` file
- **CI workflow:** Fixed duplicate `SECRET_KEY` and `REDIS_URL` env vars in `backend-test` job that caused YAML parse error
- **K8s overlays:** Updated `prod` overlay from `1.3.3-beta` → `1.3.6-beta` to match current release
- **K8s overlays:** Updated `dev` and `staging` overlays from `1.3.4-beta` → `1.3.6-beta`
- **CHANGELOG.md:** Removed duplicate `1.3.4-beta` and `1.3.3-beta` sections that corrupted the file
- **Config:** Added missing `ADMIN_USERNAME` and `ADMIN_PASSWORD` settings to `config.py` (were used in `main.py` but not defined)
- **Version consistency:** Updated all references to `1.3.4-beta` → `1.3.6-beta` across README, docs, and compose files
- **README:** Updated Docker Images section, Quick Start, and Helm references to `1.3.6-beta`
- **Docs:** Updated deployment guide and vcsim testing guide to `1.3.6-beta`

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

---

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

---

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

## [1.3.2-beta] — 2026-06-19

### Changed
- Add `org.opencontainers.image.source`, `.description`, and `.licenses` labels
  to all Docker images in both CI and Release workflows — this links Packages
  to the repository automatically on GHCR so they appear under the repo's
  Packages sidebar
- Replace `passlib` with direct bcrypt calls in `security.py` — `passlib 1.7.4` is
  incompatible with `bcrypt 4.x` and silently fails password verification
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

---

## [1.3.0-beta] — 2026-06-19

### Added
- Initial release of vSphere Compliance Manager
- vCenter integration with AES-256 credential encryption
- DRS compliance engine with regex-based VM grouping
- Storage compliance engine with separation proposals
- Role-based access control (Admin, Operator, Viewer)
- Analysis history with export (PDF, CSV, JSON)
- Scheduled analysis via APScheduler
- Kubernetes deployment with Kustomize overlays
- Docker Compose production and development configurations
- vcsim-based testing environment
