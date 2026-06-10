# Changelog

All notable changes to **vSphere Compliance Manager** are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Initial public release

---

## [1.0.0] — 2024-01-01

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

[Unreleased]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/DavoudTeimouri/vsphere-compliance-manager/releases/tag/v1.0.0
