# 🔧 Pre-commit Hooks

Reusable [pre-commit](https://pre-commit.com/) hooks for OpenSCAD projects.

Published on PyPI as [`kellerlab-pre-commit-hooks`](https://pypi.org/project/kellerlab-pre-commit-hooks/).

## 📌 What

Two hooks for OpenSCAD-based 3D printing projects:

| Hook | Description |
|------|-------------|
| `flatten-validate` | Runs `scadm flatten --all` and fails if flattened files have uncommitted changes |
| `optimize-images` | Resizes oversized JPEGs/PNGs, compresses them, and strips metadata (privacy) |

## 🔧 Usage

Add to your `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/kellerlabs/pre-commit-hooks
  rev: v0.1.0  # use latest tag
  hooks:
    - id: flatten-validate
    - id: optimize-images
```

### `flatten-validate`

Flattens OpenSCAD files via [scadm](https://pypi.org/project/scadm/) and validates that the output is committed. Reads flatten config from `scadm.json` automatically.

```yaml
- id: flatten-validate
  # Override trigger pattern (default: always_run)
  always_run: false
  files: '^(scadm\.json|models/.*\.scad)'
```

**Options:**

| Arg | Default | Description |
|-----|---------|-------------|
| `--flatten-dir` | Read from `scadm.json` | Override flatten output dirs (list of paths/globs) |

### `optimize-images`

Resizes JPEGs and PNGs exceeding max width, compresses them, and strips metadata. EXIF data (including GPS coordinates) is removed from JPEGs; text metadata chunks are removed from PNGs.

```yaml
- id: optimize-images
  args: [--max-width=1920, --quality=85]
```

**Options:**

| Arg | Default | Description |
|-----|---------|-------------|
| `--max-width` | `1920` | Maximum image width in pixels |
| `--quality` | `85` | JPEG compression quality (1-95, ignored for PNG) |

Both hooks **fail when files are modified**, printing instructions to `git add` the changes. Re-run `git commit` after staging.

## 🏗️ Used In

- [kellerlabs/homeracker](https://github.com/kellerlabs/homeracker) — HomeRacker Core
- [kellerlabs/homeracker-exclusive](https://github.com/kellerlabs/homeracker-exclusive) — HomeRacker MakerWorld models

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).

## 📜 License

MIT
