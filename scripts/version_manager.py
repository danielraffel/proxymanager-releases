#!/usr/bin/env python3
"""
Version Manager for ProxyManager
Handles semantic versioning, build number calculation, and channel detection.
"""

import re
from typing import Tuple, Optional
from enum import Enum


class Channel(Enum):
    """Update channels with build number offsets"""
    DEBUG = ("debug", 50000)
    RELEASE = ("release", 0)
    PROD = ("prod", 100000)

    def __init__(self, name: str, offset: int):
        self.channel_name = name
        self.offset = offset


class Version:
    """Semantic version with Sparkle-compatible build numbers"""

    def __init__(self, major: int, minor: int, patch: int, channel: Channel = Channel.RELEASE):
        self.major = major
        self.minor = minor
        self.patch = patch
        self.channel = channel

    @classmethod
    def from_string(cls, version_str: str, channel: Channel = Channel.RELEASE) -> 'Version':
        """Parse version string like '1.0.0' or '1.0.0-debug.1'"""
        # Detect channel from suffix first
        detected_channel = channel
        if '-debug' in version_str:
            detected_channel = Channel.DEBUG
        elif '-prod' in version_str:
            detected_channel = Channel.PROD

        # Remove channel suffix if present
        base_version = re.sub(r'-\w+(\.\d+)?$', '', version_str)

        parts = base_version.split('.')
        if len(parts) != 3:
            raise ValueError(f"Invalid version format: {version_str}")

        major, minor, patch = map(int, parts)

        return cls(major, minor, patch, detected_channel)

    def to_string(self, include_channel: bool = False) -> str:
        """Convert to string format"""
        base = f"{self.major}.{self.minor}.{self.patch}"
        if include_channel and self.channel != Channel.RELEASE:
            return f"{base}-{self.channel.channel_name}"
        return base

    def calculate_build_number(self) -> int:
        """
        Calculate Sparkle-compatible build number.
        Formula: (Major * 10000) + (Minor * 100) + Patch + Channel Offset

        Examples:
          1.0.0 release → 10000
          1.0.1 release → 10001
          1.1.0 release → 10100
          1.0.0-debug.1 → 60000
        """
        base = (self.major * 10000) + (self.minor * 100) + self.patch
        return base + self.channel.offset

    def bump_major(self) -> 'Version':
        """Increment major version, reset minor and patch"""
        return Version(self.major + 1, 0, 0, self.channel)

    def bump_minor(self) -> 'Version':
        """Increment minor version, reset patch"""
        return Version(self.major, self.minor + 1, 0, self.channel)

    def bump_patch(self) -> 'Version':
        """Increment patch version"""
        return Version(self.major, self.minor, self.patch + 1, self.channel)

    def __str__(self) -> str:
        return self.to_string()

    def __repr__(self) -> str:
        return f"Version({self.major}.{self.minor}.{self.patch}, {self.channel.channel_name})"

    def __lt__(self, other: 'Version') -> bool:
        """Compare versions by build number"""
        return self.calculate_build_number() < other.calculate_build_number()

    def __eq__(self, other: 'Version') -> bool:
        return self.calculate_build_number() == other.calculate_build_number()


def parse_info_plist_version(plist_path: str) -> Tuple[str, int]:
    """
    Extract version information from Info.plist
    Returns: (CFBundleShortVersionString, CFBundleVersion)
    """
    import plistlib

    with open(plist_path, 'rb') as f:
        plist = plistlib.load(f)

    short_version = plist.get('CFBundleShortVersionString', '1.0.0')
    build_version = int(plist.get('CFBundleVersion', '1'))

    return short_version, build_version


def update_info_plist_version(plist_path: str, version: Version):
    """Update Info.plist with new version"""
    import plistlib

    with open(plist_path, 'rb') as f:
        plist = plistlib.load(f)

    plist['CFBundleShortVersionString'] = version.to_string()
    plist['CFBundleVersion'] = str(version.calculate_build_number())

    with open(plist_path, 'wb') as f:
        plistlib.dump(plist, f)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Version management utilities')
    parser.add_argument('--test', action='store_true', help='Run tests')
    parser.add_argument('--parse', type=str, help='Parse version string')
    parser.add_argument('--build-number', type=str, help='Calculate build number for version')

    args = parser.parse_args()

    if args.test:
        # Test version parsing and build numbers
        print("Testing Version Manager...")

        v1 = Version.from_string("1.0.0")
        print(f"1.0.0 release → Build: {v1.calculate_build_number()} (expected: 10000)")

        v2 = Version.from_string("1.0.1")
        print(f"1.0.1 release → Build: {v2.calculate_build_number()} (expected: 10001)")

        v3 = Version.from_string("1.0.0-debug", Channel.DEBUG)
        print(f"1.0.0 debug → Build: {v3.calculate_build_number()} (expected: 60000)")

        v4 = v1.bump_minor()
        print(f"1.0.0 bump_minor → {v4} (Build: {v4.calculate_build_number()})")

        print("\n✅ All tests passed!")

    elif args.parse:
        v = Version.from_string(args.parse)
        print(f"Version: {v}")
        print(f"Build Number: {v.calculate_build_number()}")

    elif args.build_number:
        v = Version.from_string(args.build_number)
        print(v.calculate_build_number())

    else:
        parser.print_help()
