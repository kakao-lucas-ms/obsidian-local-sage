# Release Process

This project uses GitHub Actions for automated releases.

## Obsidian Plugin Release

### Prerequisites

- Push access to the repository
- Git installed locally

### Creating a Release

1. **Update version** (if needed):
   ```bash
   cd packages/obsidian-plugin
   # Edit manifest.json and update version field
   ```

2. **Commit changes**:
   ```bash
   git add .
   git commit -m "chore: bump version to X.Y.Z"
   git push origin main
   ```

3. **Create and push tag**:
   ```bash
   # Use 'plugin-' prefix for Obsidian plugin releases
   git tag plugin-0.1.0
   git push origin plugin-0.1.0
   ```

4. **Automated workflow**:
   - GitHub Actions automatically builds the plugin
   - Creates a GitHub Release with assets:
     - `main.js`
     - `manifest.json`
     - `styles.css`
     - `sage-ai-X.Y.Z.zip` (bundled package)
   - Generates release notes

### Tag Format

- **Plugin releases**: `plugin-X.Y.Z` (e.g., `plugin-0.1.0`)
  - Triggers: `.github/workflows/plugin-release.yml`
  - Builds and releases Obsidian plugin

## Python CLI Release

Python CLI is published to PyPI automatically when a GitHub Release is created.

### Creating a Release

1. **Update version**:
   ```bash
   cd packages/cli
   poetry version X.Y.Z
   ```

2. **Commit and push**:
   ```bash
   git add .
   git commit -m "chore: bump CLI version to X.Y.Z"
   git push origin main
   ```

3. **Create GitHub Release** (via web UI):
   - Go to https://github.com/kakao-lucas-ms/obsidian-local-sage/releases
   - Click "Draft a new release"
   - Tag: `vX.Y.Z` (e.g., `v0.1.0`)
   - Title: Release description
   - Click "Publish release"

4. **Automated workflow**:
   - Publishes to PyPI using trusted publishing (OIDC)
   - No API token needed

## CI/CD Workflows

### `.github/workflows/ci.yml`
- **Trigger**: Every push to `main` and pull requests
- **Purpose**: Lint and build verification
- **Jobs**:
  - Build Obsidian plugin
  - Run CLI linter (flake8)
  - Run CLI tests (pytest)

### `.github/workflows/plugin-release.yml`
- **Trigger**: Tags matching `plugin-*`
- **Purpose**: Build and release Obsidian plugin
- **Assets**: main.js, manifest.json, styles.css, zip bundle

### `.github/workflows/publish.yml`
- **Trigger**: GitHub Release created
- **Purpose**: Publish CLI to PyPI
- **Method**: Trusted publishing (no API token)

## Version Numbering

Follow [Semantic Versioning](https://semver.org/):
- **Major** (X.0.0): Breaking changes
- **Minor** (0.X.0): New features, backward compatible
- **Patch** (0.0.X): Bug fixes, backward compatible

## Examples

### Release plugin version 0.2.0
```bash
# 1. Update version in manifest.json
cd packages/obsidian-plugin
# Edit manifest.json: "version": "0.2.0"

# 2. Commit and tag
git add manifest.json
git commit -m "chore: bump plugin version to 0.2.0"
git push origin main
git tag plugin-0.2.0
git push origin plugin-0.2.0
```

### Release CLI version 1.0.0
```bash
# 1. Update version with poetry
cd packages/cli
poetry version 1.0.0

# 2. Commit
git add pyproject.toml
git commit -m "chore: bump CLI version to 1.0.0"
git push origin main

# 3. Create GitHub Release via web UI
# Tag: v1.0.0
# This triggers PyPI publish
```
