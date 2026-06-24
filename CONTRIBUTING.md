# Contributing to vSphere Compliance Manager

Thank you for investing your time in contributing to this project! 🎉

---

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Commit Convention](#commit-convention)
- [Branch Strategy](#branch-strategy)
- [Pull Request Process](#pull-request-process)
- [Testing Guidelines](#testing-guidelines)
- [Documentation](#documentation)

---

## Code of Conduct

This project follows the [Contributor Covenant](CODE_OF_CONDUCT.md). By participating, you agree to uphold it.

---

## Getting Started

1. **Fork** the repository on GitHub
2. **Clone** your fork locally:
   ```bash
   git clone https://github.com/davoudteimouri/vsphere-compliance-manager.git
   cd vsphere-compliance-manager
   ```
3. Add the upstream remote:
   ```bash
   git remote add upstream https://github.com/davoudteimouri/vsphere-compliance-manager.git
   ```
4. Create a feature branch off `develop`:
   ```bash
   git checkout develop
   git pull upstream develop
   git checkout -b feat/your-feature-name
   ```

---

## Development Environment

See the [Development section in README.md](README.md#development) for full setup instructions.

Quick checklist:
- [ ] Python 3.11+, Node.js 20+, Docker Compose v2
- [ ] Pre-commit hooks installed: `pre-commit install`
- [ ] Tests pass: `pytest tests/unit/` and `npm test`
- [ ] Linter clean: `ruff check .` and `npm run lint`

---

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(scope): <short description>

[optional body]

[optional footer]
```

### Types

| Type | Description |
|------|-------------|
| `feat` | A new feature |
| `fix` | A bug fix |
| `docs` | Documentation only changes |
| `style` | Code style changes (formatting, missing semicolons, etc.) |
| `refactor` | Code change that neither fixes a bug nor adds a feature |
| `perf` | Performance improvement |
| `test` | Adding missing tests or correcting existing tests |
| `build` | Changes affecting the build system or external dependencies |
| `ci` | CI/CD configuration changes |
| `chore` | Other changes that don't modify source or test files |

### Examples

```
feat(analysis): add support for VM affinity rules
fix(auth): handle LDAP timeout gracefully
docs(api): update analysis endpoint examples
feat!: drop support for vCenter 5.x (BREAKING CHANGE)
```

---

## Branch Strategy

| Branch | Description | Merges into |
|--------|-------------|-------------|
| `main` | Stable production releases. Tagged. | — |
| `develop` | Main integration branch. | `main` (via release branch) |
| `feat/*` | New features | `develop` |
| `fix/*` | Non-critical bug fixes | `develop` |
| `hotfix/*` | Critical production fixes | `main` AND `develop` |
| `release/*` | Release preparation (version bump, CHANGELOG) | `main` AND `develop` |

---

## Pull Request Process

1. Ensure your branch is up to date with `develop`:
   ```bash
   git fetch upstream
   git rebase upstream/develop
   ```
2. Make sure all tests pass and coverage does not decrease.
3. Fill in the [Pull Request template](.github/PULL_REQUEST_TEMPLATE/pull_request_template.md).
4. Request a review from at least **one maintainer**.
5. Address all review comments.
6. A maintainer will squash-merge after approval.

### PR Title Format

Follow the same Conventional Commits format:
```
feat(storage): add disk consolidation dry-run mode
```

---

## Testing Guidelines

- **Unit tests** go in `backend/tests/unit/` — no external dependencies, mock everything.
- **Integration tests** go in `backend/tests/integration/` — requires running DB/Redis via Docker.
- **Frontend tests** go in `frontend/tests/` — use Vitest + Testing Library.
- Every new feature must include tests.
- Bug fixes must include a regression test.
- Minimum coverage threshold: **80%** (enforced in CI).

---

## Documentation

- Update `README.md` if you change configuration options, environment variables, or public API behavior.
- Add or update API docs in `docs/api/` for new or changed endpoints.
- Update `CHANGELOG.md` under the `[Unreleased]` section.

---

Thank you for helping make VCM better! 🚀
