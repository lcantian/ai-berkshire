#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Download a PDF and extract its text."""
import sys, io, urllib.request, gzip
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

def download(url, timeout=60):
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept": "application/pdf,*/*",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "en-US,en;q=0.9",
    })
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read()
        if resp.info().get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
    return data

if __name__ == "__main__":
    url = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    data = download(url)
    if out:
        with open(out, "wb") as f:
            f.write(data)
        print(f"Saved {len(data)} bytes to {out}")
    else:
        import pdfplumber, tempfile, os
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tf:
            tf.write(data)
            tmp = tf.name
        try:
            with pdfplumber.open(tmp) as pdf:
                for i, page in enumerate(pdf.pages):
                    text = page.extract_text() or ""
                    print(f"--- Page {i+1} ---")
                    print(text)
        finally:
            os.unlink(tmp)
