# -*- coding: utf-8 -*-
"""Inspect Bing HTML structure to find actual result container class."""
import sys
from bs4 import BeautifulSoup
sys.stdout.reconfigure(encoding='utf-8')

path = r"D:\AI\ai-berkshire\.tmp_research\bing_eve_consumer.html"
with open(path, 'r', encoding='utf-8', errors='ignore') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
for s in soup(['script', 'style', 'noscript']):
    s.decompose()

# Bing search query in title
print("TITLE:", soup.title.get_text(strip=True) if soup.title else "")

# Find main results container
main = soup.select_one('#b_results')
if main:
    print("\n--- All <li> with class attribute inside #b_results ---")
    seen = set()
    for li in main.find_all('li'):
        cls = li.get('class', [])
        key = tuple(cls)
        if key not in seen:
            seen.add(key)
            # Print first 300 chars of text
            txt = li.get_text(' ', strip=True)[:400]
            print(f"li class={cls}: {txt}")
            print('---')
    print(f"\nTotal <li>: {len(main.find_all('li'))}")

# Check for cite tags (URLs)
print("\n--- All <cite> tags (URL indicators) ---")
for c in main.find_all('cite')[:15]:
    print(f"  cite: {c.get_text(' ', strip=True)}")

# Find all h2 (titles)
print("\n--- All <h2> tags ---")
for h in main.find_all('h2')[:15]:
    a = h.find('a')
    href = a.get('href','') if a else ''
    print(f"  h2: {h.get_text(' ', strip=True)} | href: {href}")
