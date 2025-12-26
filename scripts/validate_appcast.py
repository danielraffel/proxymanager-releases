#!/usr/bin/env python3
"""
Appcast Validator
Validates Sparkle appcast XML files for correctness.
"""

import sys
from pathlib import Path
from xml.etree import ElementTree as ET
from typing import List, Tuple
import urllib.request
import urllib.error


class ValidationError(Exception):
    """Raised when validation fails"""
    pass


class AppcastValidator:
    """Validates Sparkle appcast files"""

    SPARKLE_NS = "http://www.andymatuschak.org/xml-namespaces/sparkle"

    def __init__(self, appcast_path: str):
        self.appcast_path = Path(appcast_path)
        if not self.appcast_path.exists():
            raise ValidationError(f"Appcast file not found: {appcast_path}")

    def validate(self, check_urls: bool = False) -> List[str]:
        """
        Validate appcast file.

        Returns:
            List of warnings (empty if valid)
        """
        warnings = []

        try:
            tree = ET.parse(self.appcast_path)
            root = tree.getroot()

            # Check root element
            if root.tag != 'rss':
                raise ValidationError("Root element must be <rss>")

            if root.get('version') != '2.0':
                warnings.append("RSS version should be 2.0")

            # Check Sparkle namespace
            ns_attr = f'{{http://www.w3.org/2000/xmlns/}}sparkle'
            if root.get(ns_attr) != self.SPARKLE_NS:
                raise ValidationError("Missing Sparkle XML namespace")

            # Check channel
            channel = root.find('channel')
            if channel is None:
                raise ValidationError("Missing <channel> element")

            # Validate channel metadata
            if not channel.find('title'):
                warnings.append("Missing <title> in channel")
            if not channel.find('link'):
                warnings.append("Missing <link> in channel")

            # Validate items
            items = channel.findall('item')
            if not items:
                warnings.append("No release items found")

            for i, item in enumerate(items, 1):
                item_warnings = self._validate_item(item, check_urls)
                warnings.extend([f"Item {i}: {w}" for w in item_warnings])

        except ET.ParseError as e:
            raise ValidationError(f"XML parsing error: {e}")

        return warnings

    def _validate_item(self, item: ET.Element, check_urls: bool) -> List[str]:
        """Validate a single release item"""
        warnings = []

        # Required elements
        required = ['title', 'enclosure']
        for elem_name in required:
            if item.find(elem_name) is None:
                warnings.append(f"Missing <{elem_name}>")

        # Sparkle version
        sparkle_version = item.find(f'{{{self.SPARKLE_NS}}}version')
        if sparkle_version is None:
            warnings.append("Missing <sparkle:version>")
        elif not sparkle_version.text.isdigit():
            warnings.append(f"Invalid sparkle:version (must be numeric): {sparkle_version.text}")

        # Short version string
        short_version = item.find(f'{{{self.SPARKLE_NS}}}shortVersionString')
        if short_version is None:
            warnings.append("Missing <sparkle:shortVersionString>")

        # Enclosure validation
        enclosure = item.find('enclosure')
        if enclosure is not None:
            # Check required attributes
            url = enclosure.get('url')
            if not url:
                warnings.append("Missing 'url' attribute in enclosure")
            elif check_urls:
                if not self._check_url_exists(url):
                    warnings.append(f"URL not accessible: {url}")

            ed_sig = enclosure.get(f'{{{self.SPARKLE_NS}}}edSignature')
            if not ed_sig:
                warnings.append("Missing edSignature in enclosure")

            length = enclosure.get('length')
            if not length or not length.isdigit():
                warnings.append("Missing or invalid 'length' attribute")

        return warnings

    def _check_url_exists(self, url: str) -> bool:
        """Check if URL is accessible (HEAD request)"""
        try:
            req = urllib.request.Request(url, method='HEAD')
            with urllib.request.urlopen(req, timeout=5) as response:
                return response.status == 200
        except (urllib.error.URLError, urllib.error.HTTPError):
            return False


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Validate Sparkle appcast files')
    parser.add_argument('appcast', help='Path to appcast XML file')
    parser.add_argument('--check-urls', action='store_true',
                        help='Verify download URLs are accessible')
    parser.add_argument('--strict', action='store_true',
                        help='Treat warnings as errors')

    args = parser.parse_args()

    try:
        validator = AppcastValidator(args.appcast)
        warnings = validator.validate(check_urls=args.check_urls)

        if warnings:
            print(f"⚠️  Validation warnings for {args.appcast}:")
            for warning in warnings:
                print(f"   - {warning}")

            if args.strict:
                print("\n❌ Validation failed (strict mode)")
                sys.exit(1)
        else:
            print(f"✅ Appcast is valid: {args.appcast}")

    except ValidationError as e:
        print(f"❌ Validation error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
