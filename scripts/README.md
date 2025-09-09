# Scripts

This directory contains utility scripts for Linearator development and release management.

## Release Preparation Script

### `prepare_release.py`

Automates the process of preparing a new release by updating version numbers across the codebase.

#### Usage

```bash
# Basic usage (updates everything including AUR)
python scripts/prepare_release.py 1.2.3

# Via Makefile (recommended)
make prepare-release VERSION=1.2.3

# Dry run to see what would change
python scripts/prepare_release.py 1.2.3 --dry-run

# Skip changelog entry
python scripts/prepare_release.py 1.2.3 --no-changelog

# Skip AUR updates entirely
python scripts/prepare_release.py 1.2.3 --no-aur

# Prepare release before PyPI publish (no checksum fetch)
python scripts/prepare_release.py 1.2.3 --wait-for-pypi
# or
make prepare-release-pre-pypi VERSION=1.2.3

# Update AUR after PyPI publish (fetch checksum)
python scripts/prepare_release.py 1.2.3 --aur-only
# or  
make prepare-release-post-pypi VERSION=1.2.3

# Only update AUR files (skip Python files)
python scripts/prepare_release.py 1.2.3 --aur-only
```

#### What it does

1. **Validates version format** - Ensures semantic versioning (X.Y.Z)
2. **Updates version in multiple files:**
   - `pyproject.toml` - Package version
   - `src/linear_cli/__init__.py` - Python module version
   - `tests/unit/test_cli_basic.py` - Test version assertion
3. **Creates changelog entry** - Adds new release section to `CHANGELOG.md`
4. **Updates AUR package** (unless `--no-aur`):
   - `PKGBUILD` - Updates version, resets pkgrel, fetches SHA256 checksum
   - `.SRCINFO` - Regenerated from PKGBUILD using makepkg
5. **Provides next steps** - Shows what to do after running the script

#### Files Updated

| File | What's Updated |
|------|----------------|
| `pyproject.toml` | `version = "X.Y.Z"` |
| `src/linear_cli/__init__.py` | `__version__ = "X.Y.Z"` |
| `tests/unit/test_cli_basic.py` | Version assertion in tests |
| `CHANGELOG.md` | New release section with template |
| `PKGBUILD` | `pkgver`, `pkgrel=1`, `sha256sums` |
| `.SRCINFO` | Regenerated from PKGBUILD |

#### Example Output

```bash
$ make prepare-release VERSION=1.2.3

🚀 Preparing release 1.2.3
📦 Current version: 1.2.2
✅ Updated version in pyproject.toml
✅ Updated __version__ in src/linear_cli/__init__.py  
✅ Updated version assertion in tests/unit/test_cli_basic.py
✅ Added 1.2.3 section to CHANGELOG.md
📝 Please edit CHANGELOG.md to add release notes

🎉 Successfully prepared release 1.2.3!

Next steps:
1. Edit CHANGELOG.md to add release notes
2. Run tests: make test
3. Commit changes: git add . && git commit -m 'chore: prepare release v1.2.3'
4. Create release: git tag v1.2.3 && git push origin v1.2.3
5. Publish GitHub release to trigger PyPI upload
```

#### Complete Release Workflow

1. **Prepare release:**
   ```bash
   make prepare-release VERSION=1.2.3
   ```

2. **Edit changelog** - Fill in release notes in `CHANGELOG.md`

3. **Run tests:**
   ```bash
   make test
   ```

4. **Commit and tag:**
   ```bash
   git add .
   git commit -m "chore: prepare release v1.2.3"
   git tag v1.2.3
   git push origin main
   git push origin v1.2.3
   ```

5. **Create GitHub release** - This triggers automated PyPI publishing

#### Error Handling

The script includes comprehensive error handling:

- **Invalid version format** - Must be semantic versioning (X.Y.Z)
- **Missing files** - Warns if expected files aren't found
- **Pattern matching failures** - Reports if version patterns can't be found
- **File write errors** - Handles permission and disk space issues

#### Options

- `--dry-run` - Preview changes without making them
- `--no-changelog` - Skip adding changelog entry
- `--help` - Show usage information

#### Integration

The script is integrated with the project's Makefile for easy usage:

```bash
# Prepare release (will prompt for VERSION if not provided)
make prepare-release VERSION=1.2.3

# Check all release prerequisites
make release-check
```