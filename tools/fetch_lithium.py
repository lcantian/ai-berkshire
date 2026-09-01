#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Fetch lithium project news/announcements from multiple sources."""
import sys
import io
import urllib.request
import gzip
import io as _io
from urllib.error import URLError, HTTPError

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def fetch(url, timeout=30):
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-US,en;q=0.9",
        })
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = resp.read()
            if resp.info().get("Content-Encoding") == "gzip":
                data = gzip.decompress(data)
            # try detect encoding
            ct = resp.info().get("Content-Type", "")
            enc = "utf-8"
            if "charset=" in ct:
                enc = ct.split("charset=")[-1].strip()
            try:
                text = data.decode(enc, errors="replace")
            except (LookupError, TypeError):
                text = data.decode("utf-8", errors="replace")
            return text
    except (HTTPError, URLError, TimeoutError) as e:
        return f"FETCH_ERROR: {type(e).__name__}: {e}"
    except Exception as e:
        return f"ERROR: {type(e).__name__}: {e}"


def extract_text(html, max_chars=8000):
    """Crude HTML to text extraction using regex."""
    import re
    if not html or html.startswith("FETCH_ERROR") or html.startswith("ERROR"):
        return html
    # remove scripts and styles
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<noscript[^>]*>.*?</noscript>", " ", html, flags=re.DOTALL | re.IGNORECASE)
    # remove tags
    text = re.sub(r"<[^>]+>", " ", html)
    # decode entities
    text = text.replace("&nbsp;", " ").replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'")
    # collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_chars]


if __name__ == "__main__":
    urls = sys.argv[1:]
    for url in urls:
        print("=" * 80)
        print(f"URL: {url}")
        print("=" * 80)
        html = fetch(url)
        text = extract_text(html, max_chars=10000)
        print(text)
        print()
