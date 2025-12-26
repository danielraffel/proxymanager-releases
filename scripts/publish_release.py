#!/usr/bin/env python3
"""
GitHub Release Publisher
Creates GitHub releases and uploads artifacts.
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import List, Optional
import version_manager


class PublishError(Exception):
    """Raised when publishing fails"""
    pass


class GitHubPublisher:
    """Publishes releases to GitHub"""

    def __init__(self, repo: str, token: Optional[str] = None):
        """
        Initialize publisher.

        Args:
            repo: GitHub repository (e.g., "username/repo")
            token: GitHub personal access token (or use gh CLI auth)
        """
        self.repo = repo
        self.token = token or os.getenv('GITHUB_TOKEN')

        # Verify gh CLI is available
        if not self._check_gh_cli():
            raise PublishError("GitHub CLI (gh) not found. Install: brew install gh")

        # Verify authentication
        if not self._check_auth():
            raise PublishError("Not authenticated with GitHub. Run: gh auth login")

    def _check_gh_cli(self) -> bool:
        """Check if gh CLI is installed"""
        try:
            subprocess.run(['gh', '--version'], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def _check_auth(self) -> bool:
        """Check if authenticated with GitHub"""
        try:
            result = subprocess.run(
                ['gh', 'auth', 'status'],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except subprocess.CalledProcessError:
            return False

    def create_release(
        self,
        version: version_manager.Version,
        artifacts: List[str],
        release_notes: str,
        prerelease: bool = False
    ) -> str:
        """
        Create a GitHub release and upload artifacts.

        Args:
            version: Version object
            artifacts: List of file paths to upload
            release_notes: Markdown release notes
            prerelease: Mark as prerelease

        Returns:
            GitHub release URL
        """
        tag = f"v{version.to_string(include_channel=True)}"
        title = f"ProxyManager {version.to_string()}"

        # Check if artifacts exist
        for artifact in artifacts:
            if not Path(artifact).exists():
                raise PublishError(f"Artifact not found: {artifact}")

        print(f"📦 Creating GitHub release: {tag}")
        print(f"   Repository: {self.repo}")
        print(f"   Artifacts: {len(artifacts)}")

        # Build gh release create command
        cmd = [
            'gh', 'release', 'create', tag,
            '--repo', self.repo,
            '--title', title,
            '--notes', release_notes
        ]

        if prerelease or version.channel != version_manager.Channel.RELEASE:
            cmd.append('--prerelease')

        # Add artifacts
        cmd.extend(artifacts)

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            release_url = result.stdout.strip()
            print(f"✅ Release created: {release_url}")
            return release_url

        except subprocess.CalledProcessError as e:
            raise PublishError(f"Failed to create release: {e.stderr}")

    def update_release_notes(self, tag: str, release_notes: str):
        """Update release notes for an existing release"""
        try:
            subprocess.run(
                ['gh', 'release', 'edit', tag,
                 '--repo', self.repo,
                 '--notes', release_notes],
                capture_output=True,
                text=True,
                check=True
            )
            print(f"✅ Updated release notes for {tag}")
        except subprocess.CalledProcessError as e:
            raise PublishError(f"Failed to update release notes: {e.stderr}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Publish GitHub releases')
    parser.add_argument('--version', required=True, help='Version string (e.g., 1.0.0)')
    parser.add_argument('--channel', choices=['debug', 'release', 'prod'],
                        default='release', help='Release channel')
    parser.add_argument('--repo', required=True, help='GitHub repository (user/repo)')
    parser.add_argument('--artifacts', nargs='+', required=True,
                        help='Paths to artifacts to upload')
    parser.add_argument('--notes', type=str, help='Release notes (markdown)')
    parser.add_argument('--notes-file', type=Path, help='Release notes file')
    parser.add_argument('--prerelease', action='store_true',
                        help='Mark as prerelease')

    args = parser.parse_args()

    # Parse version
    channel_map = {
        'debug': version_manager.Channel.DEBUG,
        'release': version_manager.Channel.RELEASE,
        'prod': version_manager.Channel.PROD
    }
    version = version_manager.Version.from_string(args.version, channel_map[args.channel])

    # Get release notes
    release_notes = args.notes
    if args.notes_file:
        with open(args.notes_file, 'r') as f:
            release_notes = f.read()
    elif not release_notes:
        release_notes = f"Release {version.to_string()}"

    try:
        publisher = GitHubPublisher(repo=args.repo)
        release_url = publisher.create_release(
            version=version,
            artifacts=args.artifacts,
            release_notes=release_notes,
            prerelease=args.prerelease
        )
        print(f"\n🎉 Release published: {release_url}")

    except PublishError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
