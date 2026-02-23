name: Update Product Feed

on:
  schedule:
    - cron: '0 2 * * *'
  workflow_dispatch:

jobs:
  update-feed:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Run filter script
        run: python filter_feed.py

      - name: Commit and push updated feed
        run: |
          git config --global user.name "Feed Bot"
          git config --global user.email "bot@feed.local"
          git fetch origin main
          git reset --soft origin/main
          git add products_filtered.xml
          git diff --staged --quiet || git commit -m "Aktualizace feedu $(date +'%Y-%m-%d %H:%M')"
          git push origin main
