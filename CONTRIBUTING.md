# Contributing

## 🚀 Quick Start

```bash
git clone https://github.com/kellerlabs/pre-commit-hooks.git
cd pre-commit-hooks

python3 -m venv .venv
# Windows:
source .venv/Scripts/activate
# macOS/Linux:
source .venv/bin/activate

pip install -e .
pip install pre-commit pytest
pre-commit install --install-hooks -t commit-msg -t pre-commit
```

## 🧪 Testing

```bash
pytest tests/ -v
```

## 📝 Commit Conventions

[Conventional Commits](https://www.conventionalcommits.org/) format:

| Type | Description |
|------|-------------|
| `feat:` | New feature (minor bump) |
| `fix:` | Bug fix (patch bump) |
| `feat!:` / `fix!:` | Breaking change (major bump) |
| `docs:` | Documentation |
| `test:` | Tests |
| `chore:` | Maintenance |
| `refactor:` | Code restructuring |

## 🔄 Release Process

Automated via [release-please](https://github.com/googleapis/release-please):
- Conventional commits on `main` → release PR created automatically
- Release PR merged → GitHub Release → PyPI publish

## 📂 Project Structure

```
src/pre_commit_hooks/
  ├── flatten_validate.py   # scadm flatten + git validation
  └── optimize_images.py    # JPEG resize/compress/EXIF strip
tests/
  ├── test_flatten_validate.py
  └── test_optimize_images.py
```

## 📜 License

MIT
