#!/usr/bin/env python3
"""
VMware Download Link Collector
Collects download links for VMware Workstation and Fusion products.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# VMware product URLs
VMWARE_PRODUCTS = {
    "workstation-pro": {
        "name": "VMware Workstation Pro",
        "url": "https://www.vmware.com/products/workstation-pro.html",
        "download_page": "https://www.vmware.com/go/tryworkstation-pro",
        "platforms": ["Windows", "Linux"],
    },
    "workstation-player": {
        "name": "VMware Workstation Player",
        "url": "https://www.vmware.com/products/workstation-player.html",
        "download_page": "https://www.vmware.com/go/tryworkstation-player",
        "platforms": ["Windows", "Linux"],
    },
    "fusion-pro": {
        "name": "VMware Fusion Pro",
        "url": "https://www.vmware.com/products/fusion.html",
        "download_page": "https://www.vmware.com/go/tryfusion-pro",
        "platforms": ["macOS"],
    },
    "fusion-player": {
        "name": "VMware Fusion Player",
        "url": "https://www.vmware.com/products/fusion.html",
        "download_page": "https://www.vmware.com/go/tryfusion-player",
        "platforms": ["macOS"],
    },
}

# Known download URL patterns (these are examples, actual URLs may vary)
VMWARE_DOWNLOAD_PATTERNS = {
    "workstation-pro": "https://www.vmware.com/go/getworkstation-pro",
    "workstation-player": "https://www.vmware.com/go/getworkstation-player",
    "fusion-pro": "https://www.vmware.com/go/getfusion-pro",
    "fusion-player": "https://www.vmware.com/go/getfusion-player",
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}


def get_page_content(url: str) -> str | None:
    """Fetch page content with error handling."""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}", file=sys.stderr)
        return None


def extract_version_info(html: str) -> dict:
    """Extract version information from HTML content."""
    soup = BeautifulSoup(html, "html.parser")
    version_info = {}

    # Look for version patterns in text
    version_pattern = r"(\d+\.\d+(?:\.\d+)?)"
    text = soup.get_text()

    # Find version numbers
    versions = re.findall(version_pattern, text)
    if versions:
        version_info["versions_found"] = list(set(versions))[:5]  # Limit to 5 unique versions

    return version_info


def check_download_page(product_key: str) -> dict:
    """Check a product's download page for information."""
    product = VMWARE_PRODUCTS[product_key]
    result = {
        "product": product["name"],
        "key": product_key,
        "platforms": product["platforms"],
        "product_url": product["url"],
        "download_page": product["download_page"],
        "direct_download": VMWARE_DOWNLOAD_PATTERNS.get(product_key, ""),
        "checked_at": datetime.utcnow().isoformat(),
        "status": "unknown",
    }

    # Check product page
    html = get_page_content(product["url"])
    if html:
        version_info = extract_version_info(html)
        result.update(version_info)
        result["status"] = "available"

        # Check for specific version mentions
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text().lower()

        # Look for version mentions
        if "workstation" in product_key:
            ws_match = re.search(r"workstation\s*(?:pro|player)?\s*(\d+(?:\.\d+)*)", text)
            if ws_match:
                result["latest_version"] = ws_match.group(1)
        elif "fusion" in product_key:
            fusion_match = re.search(r"fusion\s*(?:pro|player)?\s*(\d+(?:\.\d+)*)", text)
            if fusion_match:
                result["latest_version"] = fusion_match.group(1)
    else:
        result["status"] = "unreachable"

    return result


def collect_all_downloads() -> list[dict]:
    """Collect download information for all VMware products."""
    results = []
    for product_key in VMWARE_PRODUCTS:
        print(f"Checking {VMWARE_PRODUCTS[product_key]['name']}...")
        result = check_download_page(product_key)
        results.append(result)
    return results


def save_to_json(results: list[dict], output_path: Path) -> None:
    """Save results to JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "collected_at": datetime.utcnow().isoformat(),
                "products": results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"Saved JSON to {output_path}")


def generate_readme(results: list[dict], readme_path: Path) -> None:
    """Generate README.md with download links."""
    lines = [
        "# VMware Download Links",
        "",
        f"Auto-collected VMware download links. Last updated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Products",
        "",
    ]

    for result in results:
        lines.append(f"### {result['product']}")
        lines.append("")
        lines.append(f"- **Platforms**: {', '.join(result['platforms'])}")

        if "latest_version" in result:
            lines.append(f"- **Latest Version**: {result['latest_version']}")

        lines.append(f"- **Product Page**: [{result['product']}]({result['product_url']})")
        lines.append(f"- **Download Page**: [Download]({result['download_page']})")

        if result.get("direct_download"):
            lines.append(f"- **Direct Download**: [Get {result['product']}]({result['direct_download']})")

        lines.append(f"- **Status**: {result['status']}")
        lines.append("")

    lines.extend(
        [
            "## Notes",
            "",
            "- VMware downloads may require a Broadcom account (free)",
            "- Direct download links redirect to the VMware Customer Connect portal",
            "- This repository is auto-updated via GitHub Actions",
            "",
            "## License",
            "",
            "This project is for educational purposes. VMware products are subject to their own licensing terms.",
        ]
    )

    readme_path.parent.mkdir(parents=True, exist_ok=True)
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Generated README at {readme_path}")


def main() -> int:
    """Main entry point."""
    print("VMware Download Link Collector")
    print("=" * 40)

    # Collect downloads
    results = collect_all_downloads()

    # Determine output paths
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    json_path = repo_root / "data" / "vmware_downloads.json"
    readme_path = repo_root / "README.md"

    # Save results
    save_to_json(results, json_path)
    generate_readme(results, readme_path)

    # Print summary
    print("\n" + "=" * 40)
    print("Summary:")
    for result in results:
        status = "✓" if result["status"] == "available" else "✗"
        print(f"  {status} {result['product']}: {result['status']}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
