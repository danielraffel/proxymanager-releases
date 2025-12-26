#!/usr/bin/env python3
"""
Sparkle Appcast Generator for ProxyManager
Generates Sparkle 2.x compatible RSS feeds from release artifacts.
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
from xml.etree import ElementTree as ET
from xml.dom import minidom
import version_manager


class ReleaseItem:
    """Represents a single release in the appcast"""

    def __init__(
        self,
        version: version_manager.Version,
        dmg_path: str,
        dmg_size: int,
        ed_signature: str,
        release_notes_html: str,
        pub_date: datetime,
        minimum_system_version: str = "13.0",
        download_url_base: str = ""
    ):
        self.version = version
        self.dmg_path = dmg_path
        self.dmg_size = dmg_size
        self.ed_signature = ed_signature
        self.release_notes_html = release_notes_html
        self.pub_date = pub_date
        self.minimum_system_version = minimum_system_version
        self.download_url_base = download_url_base

    @property
    def download_url(self) -> str:
        """Construct full download URL"""
        dmg_filename = os.path.basename(self.dmg_path)
        version_str = self.version.to_string(include_channel=True)
        return f"{self.download_url_base}/releases/{self.version.channel.channel_name}/v{version_str}/{dmg_filename}"


class AppcastGenerator:
    """Generates Sparkle 2.x appcast XML files"""

    SPARKLE_NS = "http://www.andymatuschak.org/xml-namespaces/sparkle"

    def __init__(
        self,
        channel: version_manager.Channel,
        base_url: str,
        releases_dir: Path
    ):
        self.channel = channel
        self.base_url = base_url
        self.releases_dir = releases_dir

    def scan_releases(self) -> List[ReleaseItem]:
        """Scan releases directory for artifacts"""
        releases = []
        channel_dir = self.releases_dir / self.channel.channel_name

        if not channel_dir.exists():
            return releases

        for version_dir in sorted(channel_dir.iterdir(), reverse=True):
            if not version_dir.is_dir() or not version_dir.name.startswith('v'):
                continue

            # Find DMG file
            dmg_files = list(version_dir.glob("*.dmg"))
            if not dmg_files:
                continue

            dmg_path = dmg_files[0]
            sig_path = dmg_path.with_suffix('.dmg.sig')

            if not sig_path.exists():
                print(f"⚠️  Skipping {dmg_path.name}: no signature file found")
                continue

            # Read signature
            with open(sig_path, 'r') as f:
                ed_signature = f.read().strip()

            # Get file size
            dmg_size = dmg_path.stat().st_size

            # Parse version from directory name
            version_str = version_dir.name[1:]  # Remove 'v' prefix
            version = version_manager.Version.from_string(version_str)

            # Read release notes
            changelog_path = version_dir / "CHANGELOG.md"
            release_notes_html = self._load_release_notes(changelog_path)

            # Get publication date from file modification time
            pub_date = datetime.fromtimestamp(dmg_path.stat().st_mtime)

            item = ReleaseItem(
                version=version,
                dmg_path=str(dmg_path),
                dmg_size=dmg_size,
                ed_signature=ed_signature,
                release_notes_html=release_notes_html,
                pub_date=pub_date,
                download_url_base=self.base_url
            )

            releases.append(item)

        return releases

    def _load_release_notes(self, changelog_path: Path) -> str:
        """Load and convert release notes to HTML"""
        if not changelog_path.exists():
            return "<p>No release notes available.</p>"

        with open(changelog_path, 'r') as f:
            markdown_content = f.read()

        # Simple markdown to HTML conversion (basic implementation)
        # For production, consider using a proper markdown library
        html = markdown_content.replace('\n\n', '</p><p>')
        html = html.replace('\n- ', '<li>')
        html = html.replace('# ', '<h2>').replace('\n', '</h2>\n')
        html = f"<p>{html}</p>"
        html = html.replace('<p><li>', '<ul><li>').replace('</p>', '</ul></p>')

        return html

    def generate_xml(self, releases: List[ReleaseItem]) -> str:
        """Generate Sparkle 2.x compatible XML"""
        # Create RSS root
        rss = ET.Element('rss', {
            'version': '2.0',
            'xmlns:sparkle': self.SPARKLE_NS
        })

        channel_elem = ET.SubElement(rss, 'channel')

        # Channel metadata
        ET.SubElement(channel_elem, 'title').text = f"ProxyManager {self.channel.channel_name.title()} Channel"
        ET.SubElement(channel_elem, 'link').text = f"{self.base_url}/appcast/{self.channel.channel_name}.xml"
        ET.SubElement(channel_elem, 'description').text = f"Software updates for ProxyManager ({self.channel.channel_name} channel)"
        ET.SubElement(channel_elem, 'language').text = "en"

        # Add release items
        for release in releases:
            item = ET.SubElement(channel_elem, 'item')

            ET.SubElement(item, 'title').text = f"Version {release.version.to_string()}"
            ET.SubElement(item, 'link').text = f"{self.base_url}/releases/tag/v{release.version.to_string(include_channel=True)}"

            # Sparkle-specific elements
            ET.SubElement(item, f'{{{self.SPARKLE_NS}}}version').text = str(release.version.calculate_build_number())
            ET.SubElement(item, f'{{{self.SPARKLE_NS}}}shortVersionString').text = release.version.to_string()
            ET.SubElement(item, f'{{{self.SPARKLE_NS}}}minimumSystemVersion').text = release.minimum_system_version

            # Release notes
            description = ET.SubElement(item, 'description')
            description.text = f"<![CDATA[{release.release_notes_html}]]>"

            # Publication date (RFC 2822 format)
            pub_date_str = release.pub_date.strftime("%a, %d %b %Y %H:%M:%S +0000")
            ET.SubElement(item, 'pubDate').text = pub_date_str

            # Enclosure (the actual download)
            ET.SubElement(item, 'enclosure', {
                'url': release.download_url,
                f'{{{self.SPARKLE_NS}}}edSignature': release.ed_signature,
                'length': str(release.dmg_size),
                'type': 'application/octet-stream'
            })

        # Pretty print XML
        xml_str = ET.tostring(rss, encoding='unicode')
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ")

    def save_appcast(self, xml_content: str, output_path: Path):
        """Save appcast XML to file"""
        with open(output_path, 'w') as f:
            f.write(xml_content)
        print(f"✅ Generated: {output_path}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Generate Sparkle appcast files')
    parser.add_argument('--releases-dir', type=str, default='releases',
                        help='Directory containing release artifacts')
    parser.add_argument('--output-dir', type=str, default='appcast',
                        help='Output directory for appcast files')
    parser.add_argument('--base-url', type=str,
                        default='https://danielraffel.github.io/proxymanager-releases',
                        help='Base URL for downloads')
    parser.add_argument('--channel', type=str, choices=['debug', 'release', 'prod'],
                        help='Generate for specific channel (default: all)')

    args = parser.parse_args()

    releases_dir = Path(args.releases_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)

    # Determine which channels to generate
    channels_to_process = []
    if args.channel:
        channel_map = {
            'debug': version_manager.Channel.DEBUG,
            'release': version_manager.Channel.RELEASE,
            'prod': version_manager.Channel.PROD
        }
        channels_to_process = [channel_map[args.channel]]
    else:
        channels_to_process = [
            version_manager.Channel.DEBUG,
            version_manager.Channel.RELEASE,
            version_manager.Channel.PROD
        ]

    # Generate appcast for each channel
    for channel in channels_to_process:
        print(f"\n📡 Generating appcast for {channel.channel_name} channel...")

        generator = AppcastGenerator(
            channel=channel,
            base_url=args.base_url,
            releases_dir=releases_dir
        )

        releases = generator.scan_releases()
        if not releases:
            print(f"⚠️  No releases found for {channel.channel_name} channel")
            continue

        print(f"   Found {len(releases)} release(s)")

        xml_content = generator.generate_xml(releases)
        output_path = output_dir / f"{channel.channel_name}.xml"
        generator.save_appcast(xml_content, output_path)

    # Generate channel metadata
    metadata = {
        "channels": {
            "debug": {
                "name": "Debug",
                "description": "Bleeding edge builds with debug symbols",
                "feed": f"{args.base_url}/appcast/debug.xml"
            },
            "release": {
                "name": "Release",
                "description": "Stable releases (recommended)",
                "feed": f"{args.base_url}/appcast/release.xml"
            },
            "prod": {
                "name": "Production",
                "description": "Production builds for critical deployments",
                "feed": f"{args.base_url}/appcast/prod.xml"
            }
        },
        "last_updated": datetime.now().isoformat()
    }

    metadata_path = output_dir / "channels.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"\n✅ Generated: {metadata_path}")


if __name__ == '__main__':
    main()
