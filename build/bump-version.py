#!/usr/bin/env python3
"""Version bump script for Rogue Signal Protocol.

Updates version strings in static files that can't read from game_rules.json.

The game_rules.json "version" field is the source of truth. Python code reads it
via game_version.py. This script updates:
  - game_rules.json (source of truth)
  - README files (static documentation)
  - Linux packaging files (PKGBUILD, metainfo, etc.)

Usage:
    python build/bump-version.py 0.9.1 0.9.2 beta
    python build/bump-version.py 0.9.2 1.0.0 release
    python build/bump-version.py --check  # verify consistency only

Arguments:
    old_version: Current version number (e.g., 0.9.1)
    new_version: New version number (e.g., 0.9.2)
    type: Build type - alpha, beta, or release (default: beta)
"""

import sys
from datetime import date
from pathlib import Path


class VersionBumper:
    """Handles version string updates across static project files."""

    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.changes: list[tuple[str, int, str, str]] = []  # (file, count, old, new)
        self.errors: list[str] = []

    def version_formats(self, version: str, build_type: str) -> dict[str, str]:
        """Generate all version format variants."""
        if build_type.lower() == "release":
            suffix = ""
            suffix_title = ""
        else:
            suffix = build_type.lower()
            suffix_title = build_type.title()

        formats = {
            "full": f"{version} {suffix_title}".strip(),  # "0.9.2 Beta" or "1.0.0"
            "hyphen": f"{version}-{suffix}".strip("-"),  # "0.9.2-beta" or "1.0.0"
            "underscore": f"{version}_{suffix}".strip("_"),  # "0.9.2_beta" or "1.0.0"
            "number": version,  # "0.9.2"
            "url_encoded": f"{version}%20{suffix_title}".rstrip("%20"),  # "0.9.2%20Beta"
        }

        if not suffix:
            formats["url_encoded"] = version

        return formats

    def replace_in_file(
        self,
        rel_path: str,
        patterns: list[tuple[str, str]],
        encoding: str = "utf-8",
    ) -> int:
        """Replace patterns in a file. Returns count of replacements."""
        file_path = self.project_root / rel_path
        if not file_path.exists():
            self.errors.append(f"File not found: {rel_path}")
            return 0

        try:
            content = file_path.read_text(encoding=encoding)
            original = content
            total_count = 0

            for old_pattern, new_pattern in patterns:
                count = content.count(old_pattern)
                if count > 0:
                    content = content.replace(old_pattern, new_pattern)
                    total_count += count
                    self.changes.append((rel_path, count, old_pattern, new_pattern))

            if content != original:
                file_path.write_text(content, encoding=encoding)

            return total_count

        except Exception as e:
            self.errors.append(f"Error processing {rel_path}: {e}")
            return 0

    def bump(self, old_ver: str, new_ver: str, build_type: str) -> bool:
        """Perform version bump across static files."""
        old = self.version_formats(old_ver, build_type)
        new = self.version_formats(new_ver, build_type)
        today = date.today().isoformat()

        # Source of truth - game_rules.json line 2
        self.replace_in_file(
            "game_rules.json",
            [(f'"version": "{old["full"]}"', f'"version": "{new["full"]}"')],
        )

        # README files
        for readme in ["README.md", "docs/README_DEV.md"]:
            self.replace_in_file(
                readme,
                [
                    (f"Version {old['full']}", f"Version {new['full']}"),
                    (f"version-{old['url_encoded']}", f"version-{new['url_encoded']}"),
                ],
            )

        self.replace_in_file(
            "README.txt",
            [(f"Version {old['full']}", f"Version {new['full']}")],
        )

        # Wiki
        self.replace_in_file(
            "docs/wiki/Home.md",
            [(f"**Current Version:** {old['full']}", f"**Current Version:** {new['full']}")],
        )

        # Linux packaging - PKGBUILD
        self.replace_in_file(
            "packaging/linux/PKGBUILD",
            [
                (f"pkgver={old['underscore']}", f"pkgver={new['underscore']}"),
                (f"_vertag={old['hyphen']}", f"_vertag={new['hyphen']}"),
            ],
        )

        # Linux packaging - .SRCINFO
        self.replace_in_file(
            "packaging/linux/.SRCINFO",
            [
                (f"pkgver = {old['underscore']}", f"pkgver = {new['underscore']}"),
                (old["hyphen"], new["hyphen"]),
            ],
        )

        # Linux packaging - AppImageBuilder.yml
        self.replace_in_file(
            "packaging/linux/AppImageBuilder.yml",
            [(f"version: {old['hyphen']}", f"version: {new['hyphen']}")],
        )

        # Linux packaging - metainfo.xml (add new release entry)
        metainfo_path = "packaging/linux/info.aforster.roguesignalprotocol.metainfo.xml"
        metainfo_file = self.project_root / metainfo_path
        if metainfo_file.exists():
            content = metainfo_file.read_text()
            old_release = f'<release version="{old["hyphen"]}"'
            new_release = f'<release version="{new["hyphen"]}" date="{today}" type="development">\n      <description>\n        <p>New release</p>\n      </description>\n    </release>\n    {old_release}'
            if old_release in content and new_release.split("\n")[0] not in content:
                content = content.replace(old_release, new_release)
                metainfo_file.write_text(content)
                self.changes.append((metainfo_path, 1, "Added new release entry", new["hyphen"]))

        # Linux packaging - Flatpak yml
        self.replace_in_file(
            "packaging/linux/info.aforster.roguesignalprotocol.yml",
            [(old["hyphen"], new["hyphen"])],
        )

        # Linux packaging - README
        self.replace_in_file(
            "packaging/linux/README.md",
            [(old["hyphen"], new["hyphen"])],
        )

        return len(self.errors) == 0

    def check_consistency(self, version: str, build_type: str) -> list[str]:
        """Check that key files have consistent version strings."""
        expected = self.version_formats(version, build_type)
        issues = []

        # Check source of truth and main README
        check_files = [
            ("game_rules.json", expected["full"]),
            ("README.md", expected["full"]),
            ("README.txt", expected["full"]),
        ]

        for rel_path, expected_ver in check_files:
            file_path = self.project_root / rel_path
            if file_path.exists():
                content = file_path.read_text()
                if expected_ver not in content:
                    issues.append(f"{rel_path}: expected '{expected_ver}' not found")

        return issues

    def print_summary(self):
        """Print summary of changes made."""
        if self.changes:
            print("\nChanges made:")
            print("-" * 60)
            for file, count, old, new in self.changes:
                print(f"  {file}: {count}x")
                if len(old) < 50 and len(new) < 50:
                    print(f"    '{old}' -> '{new}'")

        if self.errors:
            print("\nErrors:")
            print("-" * 60)
            for error in self.errors:
                print(f"  [!] {error}")

        total = sum(c[1] for c in self.changes)
        print(f"\nTotal: {total} replacements in {len(set(c[0] for c in self.changes))} files")


def main():
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    if sys.argv[1] == "--check":
        if len(sys.argv) < 4:
            print("Usage: bump-version.py --check <version> <type>")
            print("Example: bump-version.py --check 0.9.2 beta")
            sys.exit(1)
        version = sys.argv[2]
        build_type = sys.argv[3]

        bumper = VersionBumper(project_root)
        issues = bumper.check_consistency(version, build_type)

        if issues:
            print("Version inconsistencies found:")
            for issue in issues:
                print(f"  [!] {issue}")
            sys.exit(1)
        else:
            print(f"All files consistent with version {version} {build_type}")
            sys.exit(0)

    if len(sys.argv) < 3:
        print("Usage: bump-version.py <old_version> <new_version> [type]")
        print("Example: bump-version.py 0.9.1 0.9.2 beta")
        sys.exit(1)

    old_version = sys.argv[1]
    new_version = sys.argv[2]
    build_type = sys.argv[3] if len(sys.argv) > 3 else "beta"

    print(f"Bumping version: {old_version} -> {new_version} ({build_type})")
    print(f"Project root: {project_root}")

    bumper = VersionBumper(project_root)
    success = bumper.bump(old_version, new_version, build_type)
    bumper.print_summary()

    if not success:
        print("\nVersion bump completed with errors!")
        sys.exit(1)

    print("\nVersion bump complete!")
    print("\nReminder: Manually update these files:")
    print("  - CHANGELOG.md (add new version section)")
    print("  - packaging/linux/.SRCINFO (regenerate with makepkg --printsrcinfo)")
    print("  - packaging/linux/PKGBUILD sha256sums (after new release tarball)")


if __name__ == "__main__":
    main()
