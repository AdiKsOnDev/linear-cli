#!/usr/bin/env python3
"""
Release preparation script for Linearator.

This script updates version numbers across the codebase and prepares
a new release entry in the changelog.
"""

import argparse
import json
import re
import sys
import urllib.request
from datetime import datetime
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    script_dir = Path(__file__).parent
    return script_dir.parent


def validate_version(version: str) -> bool:
    """Validate semantic version format (e.g., 1.2.3)."""
    pattern = r'^\d+\.\d+\.\d+$'
    return bool(re.match(pattern, version))


def get_pypi_checksum(package_name: str, version: str) -> str | None:
    """
    Get SHA256 checksum for a PyPI package version.
    
    Args:
        package_name: Name of the package on PyPI
        version: Version to get checksum for
        
    Returns:
        SHA256 checksum string or None if not found
    """
    try:
        url = f"https://pypi.org/pypi/{package_name}/{version}/json"
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode())

        # Find the source distribution
        for file_info in data['urls']:
            if file_info['packagetype'] == 'sdist':
                return file_info['digests']['sha256']

        print(f"⚠️  No source distribution found for {package_name} {version}")
        return None

    except Exception as e:
        print(f"⚠️  Failed to get checksum from PyPI: {e}")
        return None


def update_pyproject_toml(root_dir: Path, new_version: str) -> bool:
    """Update version in pyproject.toml."""
    pyproject_file = root_dir / "pyproject.toml"

    if not pyproject_file.exists():
        print(f"❌ {pyproject_file} not found")
        return False

    content = pyproject_file.read_text()

    # Update version line
    updated_content = re.sub(
        r'^version = "[^"]*"',
        f'version = "{new_version}"',
        content,
        flags=re.MULTILINE
    )

    if updated_content == content:
        print(f"⚠️  No version found in {pyproject_file}")
        return False

    pyproject_file.write_text(updated_content)
    print(f"✅ Updated version in {pyproject_file}")
    return True


def update_init_py(root_dir: Path, new_version: str) -> bool:
    """Update version in src/linear_cli/__init__.py."""
    init_file = root_dir / "src" / "linear_cli" / "__init__.py"

    if not init_file.exists():
        print(f"❌ {init_file} not found")
        return False

    content = init_file.read_text()

    # Update __version__ line
    updated_content = re.sub(
        r'^__version__ = "[^"]*"',
        f'__version__ = "{new_version}"',
        content,
        flags=re.MULTILINE
    )

    if updated_content == content:
        print(f"⚠️  No __version__ found in {init_file}")
        return False

    init_file.write_text(updated_content)
    print(f"✅ Updated __version__ in {init_file}")
    return True


def make_version_test_dynamic(root_dir: Path) -> bool:
    """Make the version test dynamic by importing __version__ instead of hardcoding."""
    test_file = root_dir / "tests" / "unit" / "test_cli_basic.py"

    if not test_file.exists():
        print(f"❌ {test_file} not found")
        return False

    content = test_file.read_text()

    # Check if already dynamic
    if 'from linear_cli import __version__' in content:
        print(f"ℹ️  Version test already dynamic in {test_file}")
        return True

    # Add import at the top if not present
    if 'from linear_cli import __version__' not in content:
        lines = content.split('\n')
        # Find the right place to add import (after existing imports)
        import_index = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_index = i + 1
            elif line.strip() == '' and import_index > 0:
                break

        lines.insert(import_index, 'from linear_cli import __version__')
        content = '\n'.join(lines)

    # Replace hardcoded version with dynamic import
    pattern = r'(def test_cli_version\(self\):.*?assert\s+)"[0-9]+\.[0-9]+\.[0-9]+"(\s+in\s+result\.output)'
    updated_content = re.sub(
        pattern,
        r'\1__version__\2',
        content,
        flags=re.DOTALL
    )

    # Also handle simpler patterns
    pattern2 = r'(assert\s+)"[0-9]+\.[0-9]+\.[0-9]+"(\s+in\s+result\.output)'
    lines = updated_content.split('\n')
    updated_lines = []
    inside_version_test = False

    for line in lines:
        if 'def test_cli_version(' in line:
            inside_version_test = True
        elif inside_version_test and line.strip().startswith('def '):
            inside_version_test = False

        if inside_version_test and re.search(pattern2, line):
            line = re.sub(pattern2, r'\1__version__\2', line)

        updated_lines.append(line)

    updated_content = '\n'.join(updated_lines)

    if updated_content != content:
        test_file.write_text(updated_content)
        print(f"✅ Made version test dynamic in {test_file}")
        return True
    else:
        print(f"ℹ️  No changes needed in {test_file}")
        return True


def update_test_version(root_dir: Path, new_version: str) -> bool:
    """Update version assertion in test files."""
    test_file = root_dir / "tests" / "unit" / "test_cli_basic.py"

    if not test_file.exists():
        print(f"❌ {test_file} not found")
        return False

    content = test_file.read_text()

    # Only update the specific version test that checks --version output
    # Look for the test_cli_version method and update only the version assertion
    pattern = r'(def test_cli_version\(self\):.*?assert\s+)"[0-9]+\.[0-9]+\.[0-9]+"(\s+in\s+result\.output)'
    updated_content = re.sub(
        pattern,
        f'\\1"{new_version}"\\2',
        content,
        flags=re.DOTALL
    )

    if updated_content == content:
        # Try alternative pattern for different test format
        pattern = r'(assert\s+)"[0-9]+\.[0-9]+\.[0-9]+"(\s+in\s+result\.output)'
        lines = content.split('\n')
        updated_lines = []
        found_version_test = False
        inside_version_test = False

        for line in lines:
            if 'def test_cli_version(' in line:
                inside_version_test = True
            elif inside_version_test and line.strip().startswith('def '):
                inside_version_test = False

            if inside_version_test and re.search(pattern, line):
                line = re.sub(pattern, f'\\1"{new_version}"\\2', line)
                found_version_test = True

            updated_lines.append(line)

        if found_version_test:
            test_file.write_text('\n'.join(updated_lines))
            print(f"✅ Updated CLI version test assertion in {test_file}")
            return True
        else:
            print(f"ℹ️  No hardcoded version found in {test_file} - tests are version-agnostic")
            return True
    else:
        test_file.write_text(updated_content)
        print(f"✅ Updated CLI version test assertion in {test_file}")
        return True


def get_current_version(root_dir: Path) -> str | None:
    """Get current version from pyproject.toml."""
    pyproject_file = root_dir / "pyproject.toml"

    if not pyproject_file.exists():
        return None

    content = pyproject_file.read_text()
    match = re.search(r'^version = "([^"]*)"', content, re.MULTILINE)

    return match.group(1) if match else None


def update_pkgbuild(root_dir: Path, new_version: str, checksum: str | None = None) -> bool:
    """
    Update PKGBUILD file for AUR.
    
    Args:
        root_dir: Project root directory
        new_version: New version string
        checksum: SHA256 checksum (will fetch from PyPI if None)
        
    Returns:
        True if successful, False otherwise
    """
    pkgbuild_file = root_dir / "PKGBUILD"

    if not pkgbuild_file.exists():
        print(f"⚠️  {pkgbuild_file} not found - skipping PKGBUILD update")
        return True  # Don't fail if PKGBUILD doesn't exist

    # Get checksum if not provided
    if checksum is None:
        print("🔍 Fetching SHA256 checksum from PyPI...")
        checksum = get_pypi_checksum("linearator", new_version)
        if checksum is None:
            print("❌ Cannot update PKGBUILD without checksum")
            return False

    content = pkgbuild_file.read_text()

    # Update version
    updated_content = re.sub(
        r'^pkgver=.*',
        f'pkgver={new_version}',
        content,
        flags=re.MULTILINE
    )

    # Reset pkgrel to 1 for new version
    updated_content = re.sub(
        r'^pkgrel=.*',
        'pkgrel=1',
        updated_content,
        flags=re.MULTILINE
    )

    # Update checksum
    updated_content = re.sub(
        r'^sha256sums=\([\'"][^\'\"]*[\'\"]\)',
        f"sha256sums=('{checksum}')",
        updated_content,
        flags=re.MULTILINE
    )

    if updated_content == content:
        print(f"⚠️  No changes made to {pkgbuild_file}")
        return False

    pkgbuild_file.write_text(updated_content)
    print("✅ Updated PKGBUILD version and checksum")
    return True


def generate_srcinfo(root_dir: Path) -> bool:
    """
    Generate .SRCINFO file from PKGBUILD using makepkg.
    
    Args:
        root_dir: Project root directory
        
    Returns:
        True if successful, False otherwise
    """
    import subprocess

    pkgbuild_file = root_dir / "PKGBUILD"
    srcinfo_file = root_dir / ".SRCINFO"

    if not pkgbuild_file.exists():
        print("⚠️  PKGBUILD not found - skipping .SRCINFO generation")
        return True

    try:
        # Generate .SRCINFO using makepkg
        result = subprocess.run(
            ["makepkg", "--printsrcinfo"],
            cwd=root_dir,
            capture_output=True,
            text=True,
            check=True
        )

        srcinfo_file.write_text(result.stdout)
        print("✅ Generated .SRCINFO from PKGBUILD")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to generate .SRCINFO: {e}")
        return False
    except FileNotFoundError:
        print("⚠️  makepkg not found - .SRCINFO not generated (install on Arch Linux)")
        return True  # Don't fail if makepkg is not available


def add_changelog_entry(root_dir: Path, new_version: str) -> bool:
    """Add new release entry to CHANGELOG.md."""
    changelog_file = root_dir / "CHANGELOG.md"

    if not changelog_file.exists():
        print(f"❌ {changelog_file} not found")
        return False

    content = changelog_file.read_text()

    # Find the [Unreleased] section
    unreleased_pattern = r'## \[Unreleased\]'
    match = re.search(unreleased_pattern, content)

    if not match:
        print("⚠️  No [Unreleased] section found in CHANGELOG.md")
        return False

    # Insert new version section before [Unreleased]
    today = datetime.now().strftime("%Y-%m-%d")
    new_section = f"""## [{new_version}] - {today}

### Added
- 

### Changed
- 

### Fixed
- 

### Security
- 

## [Unreleased]"""

    # Replace [Unreleased] with new section + [Unreleased]
    updated_content = re.sub(
        r'## \[Unreleased\]',
        new_section,
        content,
        count=1
    )

    changelog_file.write_text(updated_content)
    print(f"✅ Added {new_version} section to {changelog_file}")
    print(f"📝 Please edit {changelog_file} to add release notes")
    return True


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Prepare Linearator release by updating version numbers"
    )
    parser.add_argument(
        "version",
        help="New version number (e.g., 1.2.3)"
    )
    parser.add_argument(
        "--no-changelog",
        action="store_true",
        help="Skip adding changelog entry"
    )
    parser.add_argument(
        "--no-aur",
        action="store_true",
        help="Skip AUR PKGBUILD and .SRCINFO updates"
    )
    parser.add_argument(
        "--wait-for-pypi",
        action="store_true",
        help="Update PKGBUILD but don't fetch checksum (for pre-PyPI release prep)"
    )
    parser.add_argument(
        "--aur-only",
        action="store_true",
        help="Only update AUR files (PKGBUILD and .SRCINFO)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without making changes"
    )
    parser.add_argument(
        "--dynamic-version-test",
        action="store_true",
        help="Make version test dynamic by importing __version__ (recommended)"
    )

    args = parser.parse_args()

    # Validate version format
    if not validate_version(args.version):
        print(f"❌ Invalid version format: {args.version}")
        print("Version must be in format: X.Y.Z (e.g., 1.2.3)")
        sys.exit(1)

    root_dir = get_project_root()
    current_version = get_current_version(root_dir)

    print(f"🚀 Preparing release {args.version}")
    if current_version:
        print(f"📦 Current version: {current_version}")

    if args.dry_run:
        print("🔍 DRY RUN - No changes will be made")
        print("\nFiles that would be updated:")
        if not args.aur_only:
            print(f"  - {root_dir / 'pyproject.toml'}")
            print(f"  - {root_dir / 'src' / 'linear_cli' / '__init__.py'}")
            print(f"  - {root_dir / 'tests' / 'unit' / 'test_cli_basic.py'}")
            if not args.no_changelog:
                print(f"  - {root_dir / 'CHANGELOG.md'}")
        if not args.no_aur:
            print(f"  - {root_dir / 'PKGBUILD'}")
            print(f"  - {root_dir / '.SRCINFO'}")
        return

    # Update version in all files
    success = True

    # Update Python files unless --aur-only is specified
    if not args.aur_only:
        success &= update_pyproject_toml(root_dir, args.version)
        success &= update_init_py(root_dir, args.version)

        # Handle test version updates based on flag
        if args.dynamic_version_test:
            success &= make_version_test_dynamic(root_dir)
        else:
            success &= update_test_version(root_dir, args.version)

        if not args.no_changelog:
            success &= add_changelog_entry(root_dir, args.version)

    # Handle AUR updates
    if not args.no_aur:
        if args.wait_for_pypi:
            print("⏳ Skipping PyPI checksum fetch (--wait-for-pypi flag)")
            print("📝 You'll need to update PKGBUILD checksum manually after PyPI release")
        else:
            success &= update_pkgbuild(root_dir, args.version)
            success &= generate_srcinfo(root_dir)

    if success:
        print(f"\n🎉 Successfully prepared release {args.version}!")
        print("\nNext steps:")
        print("1. Edit CHANGELOG.md to add release notes")
        print("2. Run tests: make test")
        print(f"3. Commit changes: git add . && git commit -m 'chore: prepare release v{args.version}'")
        print(f"4. Create release: git tag v{args.version} && git push origin v{args.version}")
        print("5. Publish GitHub release to trigger PyPI upload")

        if not args.no_aur and not args.wait_for_pypi:
            print("\nAUR Release Steps:")
            print("6. After PyPI release, update AUR repository:")
            print("   git clone ssh://aur@aur.archlinux.org/linear-cli.git (if not done)")
            print("   cp PKGBUILD .SRCINFO linear-cli/")
            print("   cd linear-cli")
            print("   git add PKGBUILD .SRCINFO")
            print(f"   git commit -m 'Update to version {args.version}'")
            print("   git push origin master")
        elif not args.no_aur and args.wait_for_pypi:
            print("\nAUR Release Steps (after PyPI publishing):")
            print("6. Update PKGBUILD checksum:")
            print(f"   python scripts/prepare_release.py {args.version} --no-changelog")
            print("7. Then commit and push AUR changes")
    else:
        print("\n❌ Some updates failed. Please check the errors above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
