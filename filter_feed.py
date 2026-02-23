#!/usr/bin/env python3
"""
Shoptet Feed Filter - Removes products with fewer than 3 available sizes
Runs automatically via GitHub Actions every night
"""

import xml.etree.ElementTree as ET
import urllib.request
from collections import defaultdict
import sys

# CONFIGURATION
FEED_URL = "https://www.mariinabotarna.cz/google/export/products.xml?hash=tJxTlRu3qAmtYrStZym5T1ZE"
OUTPUT_FILE = "products_filtered.xml"
MIN_SIZES = 3  # Minimum number of available sizes to keep product


def download_feed(url):
    print(f"Stahuji feed z {url}...")
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "text/xml,application/xml,application/xhtml+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "cs-CZ,cs;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "Cache-Control": "no-cache"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            return response.read()
    except Exception as e:
        print(f"Chyba při stahování feedu: {e}")
        sys.exit(1)


def parse_feed(xml_content):
    print("Parsuju XML feed...")
    try:
        root = ET.fromstring(xml_content)
        return root
    except Exception as e:
        print(f"Chyba při parsování XML: {e}")
        sys.exit(1)


def group_products_by_item_group_id(root):
    namespace = {'g': 'http://base.google.com/ns/1.0'}
    products_by_group = defaultdict(list)
    items = root.findall('.//item') or root.findall('.//{http://base.google.com/ns/1.0}item')

    print(f"Nalezeno {len(items)} produktů celkem")

    for item in items:
        item_group_id = None

        for tag in ['item_group_id', '{http://base.google.com/ns/1.0}item_group_id', 'g:item_group_id']:
            elem = item.find(tag, namespace) or item.find(tag)
            if elem is not None:
                item_group_id = elem.text
                break

        if not item_group_id:
            id_elem = (
                item.find('id')
                or item.find('{http://base.google.com/ns/1.0}id')
                or item.find('g:id', namespace)
            )
            if id_elem is not None:
                item_group_id = id_elem.text

        availability = None
        for tag in ['availability', '{http://base.google.com/ns/1.0}availability', 'g:availability']:
            elem = item.find(tag, namespace) or item.find(tag)
            if elem is not None:
                availability = elem.text
                break

        is_in_stock = availability and 'in stock' in availability.lower()

        if item_group_id and is_in_stock:
            products_by_group[item_group_id].append(item)

    return products_by_group


def filter_products(root, min_sizes=3):
    print(f"\nFiltruju produkty s méně než {min_sizes} dostupnými velikostmi...")

    products_by_group = group_products_by_item_group_id(root)

    items_to_remove = []
    kept_groups = 0
    removed_groups = 0

    for group_id, variants in products_by_group.items():
        if len(variants) < min_sizes:
            items_to_remove.extend(variants)
            removed_groups += 1
        else:
            kept_groups += 1

    channel = root.find('.//channel') or root.find('.//{http://base.google.com/ns/1.0}channel')
    if channel is None:
        for child in root:
            if child.findall('.//item'):
                channel = child
                break

    if channel is not None:
        for item in items_to_remove:
            try:
                channel.remove(item)
            except ValueError:
                for parent in root.iter():
                    try:
                        parent.remove(item)
                        break
                    except ValueError:
                        continue

    print(f"\nVýsledky:")
    print(f"  Skupiny produktů zachovány: {kept_groups}")
    print(f"  Skupiny produktů odstraněny: {removed_groups}")
    print(f"  Celkem odstraněno variant: {len(items_to_remove)}")

    return root


def save_feed(root, output_file):
    print(f"\nUkládám filtrovaný feed do {output_file}...")
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    try:
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        print("✓ Feed úspěšně uložen!")
        return True
    except Exception as e:
        print(f"Chyba při ukládání: {e}")
        return False


def main():
    print("=" * 60)
    print("Shoptet Feed Filter")
    print("=" * 60)

    xml_content = download_feed(FEED_URL)
    root = parse_feed(xml_content)
    filtered_root = filter_products(root, MIN_SIZES)
    success = save_feed(filtered_root, OUTPUT_FILE)

    if not success:
        sys.exit(1)

    print("\n✓ Hotovo!")


if __name__ == "__main__":
    main()
