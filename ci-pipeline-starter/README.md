# ci-pipeline-starter

> A production-ready GitHub Actions CI/CD template with Python, automated testing,
> code quality checks, and release automation — ready to drop into any Python project.

![CI](https://github.com/YOUR_USERNAME/ci-pipeline-starter/actions/workflows/ci.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## What this repo demonstrates

This project showcases a **complete CI/CD workflow** built from real-world experience
running integration pipelines on production software teams:

| Practice | Implementation |
|---|---|
| Multi-stage pipeline | Lint → Test → Build (with `needs:` dependency chain) |
| Matrix testing | Runs on Python 3.10, 3.11, and 3.12 in parallel |
| Code quality gates | `flake8` linting + `black` formatting check |
| Test coverage | `pytest-cov` with 80% minimum threshold |
| Pre-commit hooks | Consistent style enforced before every commit |
| Release automation | Tag-triggered release with auto-generated changelog |
| Clean package structure | `src/` layout with `pyproject.toml` |

---

## Project: `build_report` library

The example Python package included here (`src/build_report`) parses CI build logs
and generates structured Markdown, plain-text, or JSON reports — a real-world utility
useful when aggregating results across pipelines.

```python
from build_report import parser, formatter

log_text = open("my_build.log").read()
result = parser.parse_log(log_text)

print(formatter.to_markdown(result))
# ## Build Report
# **Overall:** ✅ `PASSED`
# | Step | Status | Duration | ...
```

---

## Quick start

```bash
# Clone
git clone https://github.com/YOUR_USERNAME/ci-pipeline-starter.git
cd ci-pipeline-starter

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate      # Windows
# source .venv/bin/activate  # Linux/macOS

# Install dev dependencies
pip install -r requirements-dev.txt
pip install -e .

# Run tests
pytest

# Run with coverage
pytest --cov=src --cov-report=term-missing

# Lint & format
flake8 src/ tests/
black src/ tests/
```

---

## CI Pipeline overview

```
push / pull_request
       │
       ▼
  ┌─────────┐      ┌──────────────────────┐      ┌─────────┐
  │  Lint   │ ───► │  Test (3.10/3.11/3.12)│ ───► │  Build  │
  │ flake8  │      │  pytest + coverage    │      │  check  │
  │ black   │      └──────────────────────┘      └─────────┘
  └─────────┘

push tag v*.*.*
       │
       ▼
  ┌──────────────────────────────────┐
  │  Release (tests → build → tag)  │
  └──────────────────────────────────┘
```

---

## How to adapt this template for your project

1. Replace `src/build_report/` with your own Python package
2. Update `pyproject.toml` with your package name and metadata
3. Add your own tests under `tests/`
4. Adjust the `python-version` matrix in `.github/workflows/ci.yml` as needed
5. Replace `YOUR_USERNAME` in badge URLs with your GitHub username

---

## Repository structure

```
ci-pipeline-starter/
├── .github/
│   └── workflows/
│       ├── ci.yml          # Main CI: lint → test → build
│       └── release.yml     # Tag-based release automation
├── src/
│   └── build_report/
│       ├── __init__.py
│       ├── parser.py       # Parse build log text → BuildResult
│       └── formatter.py    # Render BuildResult as Markdown/text/JSON
├── tests/
│   ├── test_parser.py
│   └── test_formatter.py
├── .pre-commit-config.yaml
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── requirements-dev.txt
```

---

## Background

Built from real-world CI/CD experience on large-scale software integration projects —
where reliable automated pipelines reduced late-stage integration bugs by ~25% and
cut manual testing effort by ~50%.

---

## License

MIT — use freely, adapt for your team.
