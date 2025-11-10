"""
Link Validator Module
Validates URLs in markdown files and provides archive.org fallback options
"""

import re
import requests
from pathlib import Path
from urllib.parse import urlparse
from typing import List, Dict, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


class LinkValidator:
    def __init__(self, timeout: int = 10, max_workers: int = 10):
        """
        Initialize LinkValidator

        Args:
            timeout: Request timeout in seconds
            max_workers: Maximum concurrent requests
        """
        self.timeout = timeout
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def extract_links_from_file(self, file_path: Path) -> List[Tuple[str, int]]:
        """
        Extract all URLs from a markdown file

        Args:
            file_path: Path to markdown file

        Returns:
            List of tuples (url, line_number)
        """
        links = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    # Match markdown links [text](url)
                    markdown_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', line)
                    for _, url in markdown_links:
                        # Skip anchors and relative paths
                        if url.startswith(('http://', 'https://')):
                            links.append((url, line_num))

                    # Match bare URLs
                    bare_links = re.findall(r'https?://[^\s\)]+', line)
                    for url in bare_links:
                        # Clean trailing punctuation
                        url = url.rstrip('.,;:!?)')
                        links.append((url, line_num))

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

        return links

    def extract_all_links(self, skill_path: Path) -> Dict[str, List[Tuple[str, int]]]:
        """
        Extract all links from all markdown files in skill directory

        Args:
            skill_path: Path to skill directory

        Returns:
            Dictionary mapping file paths to list of (url, line_number) tuples
        """
        all_links = {}

        # Check SKILL.md
        skill_md = skill_path / "SKILL.md"
        if skill_md.exists():
            all_links[str(skill_md)] = self.extract_links_from_file(skill_md)

        # Check references directory
        references_dir = skill_path / "references"
        if references_dir.exists():
            for md_file in references_dir.rglob("*.md"):
                links = self.extract_links_from_file(md_file)
                if links:
                    all_links[str(md_file)] = links

        return all_links

    def check_url(self, url: str) -> Tuple[str, bool, str]:
        """
        Check if a URL is accessible

        Args:
            url: URL to check

        Returns:
            Tuple of (url, is_valid, error_message)
        """
        try:
            response = self.session.head(url, timeout=self.timeout, allow_redirects=True)

            # Some servers don't support HEAD, try GET
            if response.status_code == 405:
                response = self.session.get(url, timeout=self.timeout, allow_redirects=True, stream=True)

            if response.status_code == 200:
                return (url, True, "OK")
            else:
                return (url, False, f"HTTP {response.status_code}")

        except requests.exceptions.Timeout:
            return (url, False, "Timeout")
        except requests.exceptions.SSLError:
            return (url, False, "SSL Error")
        except requests.exceptions.ConnectionError:
            return (url, False, "Connection Error")
        except requests.exceptions.TooManyRedirects:
            return (url, False, "Too Many Redirects")
        except Exception as e:
            return (url, False, f"Error: {str(e)[:50]}")

    def check_archive_org(self, url: str) -> Tuple[bool, str]:
        """
        Check if URL is available on archive.org

        Args:
            url: Original URL

        Returns:
            Tuple of (is_available, archive_url)
        """
        try:
            archive_api = f"https://archive.org/wayback/available?url={url}"
            response = self.session.get(archive_api, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                if data.get('archived_snapshots', {}).get('closest', {}).get('available'):
                    archive_url = data['archived_snapshots']['closest']['url']
                    return (True, archive_url)

        except Exception:
            pass

        return (False, "")

    def validate_all_links(self, all_links: Dict[str, List[Tuple[str, int]]]) -> Dict:
        """
        Validate all links concurrently

        Args:
            all_links: Dictionary of file paths to links

        Returns:
            Validation results dictionary
        """
        # Collect unique URLs
        url_to_locations = {}
        for file_path, links in all_links.items():
            for url, line_num in links:
                if url not in url_to_locations:
                    url_to_locations[url] = []
                url_to_locations[url].append((file_path, line_num))

        total_links = len(url_to_locations)
        valid_links = []
        broken_links = []

        print(f"\n🔍 Checking {total_links} unique URLs...")

        # Check URLs concurrently
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_url = {
                executor.submit(self.check_url, url): url
                for url in url_to_locations.keys()
            }

            completed = 0
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                url_result, is_valid, error_msg = future.result()
                completed += 1

                # Progress indicator
                if completed % 10 == 0 or completed == total_links:
                    print(f"   Progress: {completed}/{total_links}", end='\r')

                if is_valid:
                    valid_links.append(url)
                else:
                    # Check archive.org for broken links
                    archive_available, archive_url = self.check_archive_org(url)

                    broken_links.append({
                        'url': url,
                        'error': error_msg,
                        'locations': url_to_locations[url],
                        'archive_available': archive_available,
                        'archive_url': archive_url
                    })

        print()  # New line after progress

        return {
            'total': total_links,
            'valid': len(valid_links),
            'broken': len(broken_links),
            'valid_links': valid_links,
            'broken_links': broken_links,
            'percentage': round(len(valid_links) / total_links * 100, 1) if total_links > 0 else 0
        }


def validate_skill_links(skill_path: str) -> Dict:
    """
    Main function to validate all links in a skill

    Args:
        skill_path: Path to skill directory

    Returns:
        Validation results dictionary
    """
    skill_path = Path(skill_path)

    if not skill_path.exists():
        return {'error': f"Path does not exist: {skill_path}"}

    validator = LinkValidator()

    # Extract all links
    print(f"📂 Scanning {skill_path}...")
    all_links = validator.extract_all_links(skill_path)

    total_files = len(all_links)
    total_link_instances = sum(len(links) for links in all_links.values())

    print(f"   Found {total_link_instances} links in {total_files} files")

    if total_link_instances == 0:
        return {
            'total': 0,
            'valid': 0,
            'broken': 0,
            'valid_links': [],
            'broken_links': [],
            'percentage': 0
        }

    # Validate all links
    results = validator.validate_all_links(all_links)

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python link_validator.py <skill_path>")
        sys.exit(1)

    skill_path = sys.argv[1]
    results = validate_skill_links(skill_path)

    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        sys.exit(1)

    # Print results
    print(f"\n{'='*60}")
    print(f"📊 Link Validation Results")
    print(f"{'='*60}")
    print(f"✅ Valid Links: {results['valid']}/{results['total']} ({results['percentage']}%)")

    if results['broken']:
        print(f"\n❌ Broken Links ({len(results['broken_links'])}):")
        for broken in results['broken_links'][:10]:  # Show first 10
            print(f"   • {broken['url']}")
            print(f"     Error: {broken['error']}")
            if broken['archive_available']:
                print(f"     ✓ Archive: {broken['archive_url']}")
            for file_path, line_num in broken['locations'][:2]:
                print(f"     Location: {file_path}:{line_num}")
            print()
