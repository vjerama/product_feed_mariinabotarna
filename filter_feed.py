#!/usr/bin/env python3
"""
Shoptet Feed Filter - Removes products with fewer than 3 available sizes
OPRAVENÁ VERZE: odstraňuje VŠECHNY varianty produktu (i vyprodané),
pokud má produkt méně než 3 velikosti skladem.
"""

import xml.etree.ElementTree as ET
import urllib.request
from collections import defaultdict
import sys

FEED_URL = "https://www.mariinabotarna.cz/google/export/products.xml?hash=tJxTlRu3qAmtYrStZym5T1ZE"
OUTPUT_FILE = "products_filtered.xml"
MIN_SIZES = 3


def download_feed(url):
    print(f"Stahuji feed z {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "text/xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "cs-CZ,cs;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache"
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            return response.read()
    except Exception as e:
        print(f"Chyba při stahování: {e}")
        sys.exit(1)


def parse_feed(xml_content):
    print("Parsuju XML...")
    try:
        return ET.fromstring(xml_content)
    except Exception as e:
        print(f"Chyba při parsování: {e}")
        sys.exit(1)


def get_text(item, tags):
    for tag in tags:
        elem = item.find(tag)
        if elem is not None and elem.text:
            return elem.text.strip()
    return None


def filter_products(root, min_sizes=3):
    print(f"Filtruju produkty s méně než {min_sizes} velikostmi skladem...")

    items = root.findall('.//item')
    print(f"Celkem produktů: {len(items)}")

    # Seskup všechny varianty a spočítej skladem dostupné
    groups = defaultdict(lambda: {'all': [], 'in_stock': 0})

    for item in items:
        group_id = get_text(item, [
            '{http://base.google.com/ns/1.0}item_group_id',
            'item_group_id'
        ])
        if not group_id:
            group_id = get_text(item, [
                '{http://base.google.com/ns/1.0}id',
                'id'
            ])
        if not group_id:
            continue

        availability = get_text(item, [
            '{http://base.google.com/ns/1.0}availability',
            'availability'
        ]) or ''

        groups[group_id]['all'].append(item)
        if 'in stock' in availability.lower():
            groups[group_id]['in_stock'] += 1

    # Odstraň VŠECHNY varianty produktů s méně než min_sizes kusů skladem
    channel = root.find('.//channel')
    removed_groups = 0
    kept_groups = 0
    removed_items = 0

    for group_id, data in groups.items():
        if data['in_stock'] < min_sizes:
            for item in data['all']:
                try:
                    channel.remove(item)
                    removed_items += 1
                except ValueError:
                    pass
            removed_groups += 1
        else:
            kept_groups += 1

    print(f"Zachováno skupin: {kept_groups}")
    print(f"Odstraněno skupin: {removed_groups}")
    print(f"Odstraněno variant celkem: {removed_items}")
    return root


def save_feed(root, output_file):
    print(f"Ukládám do {output_file}...")
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    try:
        tree.write(output_file, encoding='utf-8', xml_declaration=True)
        print("✓ Uloženo!")
        return True
    except Exception as e:
        print(f"Chyba: {e}")
        return False


def main():
    print("=" * 50)
    print("Shoptet Feed Filter v2")
    print("=" * 50)
    xml_content = download_feed(FEED_URL)
    root = parse_feed(xml_content)
    filtered_root = filter_products(root, MIN_SIZES)
    if not save_feed(filtered_root, OUTPUT_FILE):
        sys.exit(1)
    print("✓ Hotovo!")


if __name__ == "__main__":
    main()
