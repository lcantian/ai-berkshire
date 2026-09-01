#!/usr/bin/env python
# -*- coding: utf-8 -*-
import re, sys, os, io
from html import unescape

# Open output file directly
BASE = r'D:\AI\ai-berkshire\.tmp_research'
OUT = open(BASE + r'\multi.txt', 'w', encoding='utf-8')
def p(*args):
    OUT.write(' '.join(str(a) for a in args) + '\n')
    OUT.flush()

def strip_tags(s):
    s = re.sub(r'<[^>]+>', ' ', s)
    s = unescape(s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def parse_google(fp):
    data = open(fp, 'r', encoding='utf-8', errors='ignore').read()
    # Google results: <div class="ZINbbc xpd O9g5cc uUPGi"><div class="kCrYT"><a href="/url?q=...
    # Or simpler: extract <a href="/url?q=URL&..."> with text
    p('--- GOOGLE ---')
    # extract links with their text snippets
    results = re.findall(r'<div class="[^"]*xpd[^"]*"[^>]*>(.*?)</div>(?=<div class="[^"]*xpd|$)', data, re.S)
    if not results:
        # fallback - look for /url?q= patterns
        urls = re.findall(r'/url\?q=([^&]+)&[^"]+', data)
        for u in urls[:15]:
            if 'google.' not in u and 'youtube' not in u:
                p(f'  URL: {u[:160]}')
    count = 0
    for r in results[:20]:
        link_m = re.search(r'<a[^>]+href="(/url\?q=[^"]+|https?://[^"]+)"', r)
        if not link_m:
            continue
        link = link_m.group(1)
        if link.startswith('/url?q='):
            link = re.search(r'q=([^&]+)', link).group(1)
        if 'google.' in link or 'youtube' in link or 'gstatic' in link:
            continue
        # Title and snippet
        spans = re.findall(r'<span[^>]*>(.*?)</span>', r, re.S)
        texts = [strip_tags(s) for s in spans if len(strip_tags(s)) > 20]
        if texts:
            count += 1
            if count <= 12:
                p(f'  [{count}] {texts[0][:140]}')
                p(f'      URL: {link[:180]}')
                if len(texts) > 1:
                    snip = ' '.join(texts[1:3])[:300]
                    p(f'      SNIP: {snip}')

def parse_sogou(fp):
    data = open(fp, 'r', encoding='utf-8', errors='ignore').read()
    p('--- SOGOU ---')
    # sogou results: <div class="vrwrap"> ... <h3>...<a href=...>title</a></h3> ... <p class="str_time..."> or <div class="fz-mid...">
    blocks = re.findall(r'<div[^>]*class="vrwrap[^"]*"[^>]*>(.*?)</div>(?=<div[^>]*class="vrwrap|$)', data, re.S)
    count = 0
    for r in blocks[:25]:
        title_m = re.search(r'<h3[^>]*>(.*?)</h3>', r, re.S)
        if not title_m: continue
        title = strip_tags(title_m.group(1))
        link_m = re.search(r'<a[^>]+href="([^"]+)"', title_m.group(1))
        link = link_m.group(1) if link_m else ''
        # snippet - look for text in p or div with class
        snip = ''
        for pat in [r'<p[^>]*class="[^"]*str[^"]*"[^>]*>(.*?)</p>',
                    r'<div[^>]*class="[^"]*fz-mid[^"]*"[^>]*>(.*?)</div>',
                    r'<p[^>]*>(.*?)</p>']:
            m = re.search(pat, r, re.S)
            if m:
                snip = strip_tags(m.group(1))
                if len(snip) > 30: break
        if title:
            count += 1
            if count <= 12:
                p(f'  [{count}] {title[:140]}')
                if link: p(f'      URL: {link[:180]}')
                if snip: p(f'      SNIP: {snip[:240]}')

def parse_360(fp):
    data = open(fp, 'r', encoding='utf-8', errors='ignore').read()
    p('--- 360 ---')
    # 360 results: <li class="res-list"><div class="res-tab"><h3><a href=...>title</a></h3><p>snippet</p>
    blocks = re.findall(r'<li[^>]*class="[^"]*res-list[^"]*"[^>]*>(.*?)</li>', data, re.S)
    if not blocks:
        blocks = re.findall(r'<div[^>]*class="[^"]*res[^"]*"[^>]*>(.*?)(?=<li|<div[^>]*class="[^"]*res[^"]*")', data, re.S)
    count = 0
    for r in blocks[:25]:
        title_m = re.search(r'<h3[^>]*>(.*?)</h3>', r, re.S)
        if not title_m: continue
        title = strip_tags(title_m.group(1))
        link_m = re.search(r'<a[^>]+href="([^"]+)"[^>]*>(?:<[^>]+>)*([^<]+)', title_m.group(1))
        link = link_m.group(1) if link_m else ''
        # snippet
        snip = ''
        after_h3 = r.split('</h3>', 1)[-1]
        snip = strip_tags(after_h3)[:240]
        if title:
            count += 1
            if count <= 12:
                p(f'  [{count}] {title[:140]}')
                if link: p(f'      URL: {link[:180]}')
                if snip and len(snip)>20: p(f'      SNIP: {snip[:240]}')

# Main
SEARCH_DIR = BASE
for fn, parser in [('sogou1.html', parse_sogou),
                   ('so1.html', parse_360),
                   ('google1.html', parse_google),
                   ('tt1.html', None)]:
    fp = os.path.join(SEARCH_DIR, fn)
    if os.path.exists(fp) and parser:
        p(f'\n=========={fn}==========')
        try: parser(fp)
        except Exception as e: p('ERR:', e)
OUT.close()
