import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def parse(fn):
    with open(fn, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    # 360: <li class="res-list ..."> ... <h3 class="res-title"><a href="...">title</a></h3> ... <p class="res-desc"...>snippet</p>
    # split by res-list
    blocks = re.split(r'<li[^>]*class="[^"]*res-list', html)[1:]
    out = []
    for b in blocks:
        mt = re.search(r'<h3[^>]*class="[^"]*res-title[^"]*"[^>]*>(.*?)</h3>', b, re.DOTALL)
        if not mt: continue
        title_html = mt.group(1)
        ma = re.search(r'<a[^>]*href="([^"]+)"', title_html)
        url = ma.group(1) if ma else ''
        # data-mdurl attribute holds the real url
        mmdu = re.search(r'data-mdurl="([^"]+)"', title_html)
        if mmdu: url = mmdu.group(1)
        title = re.sub(r'<[^>]+>','',title_html).strip()
        # snippet
        snip = ''
        for pat in [r'<p[^>]*class="[^"]*res-desc[^"]*"[^>]*>(.*?)</p>',
                    r'<span[^>]*class="[^"]*res-desc[^"]*"[^>]*>(.*?)</span>',
                    r'<p[^>]*class="[^"]*news-summary[^"]*"[^>]*>(.*?)</p>',
                    r'<div[^>]*class="[^"]*res-rich[^"]*"[^>]*>(.*?)</div>\s*</div>']:
            ms = re.search(pat, b, re.DOTALL)
            if ms:
                cand = re.sub(r'<[^>]+>',' ', ms.group(1))
                cand = re.sub(r'\s+',' ', cand).strip()
                if len(cand) > len(snip):
                    snip = cand
        out.append((title, url, snip))
    return out

for fn in sys.argv[1:]:
    print('========', fn, '========')
    res = parse(fn)
    print(f'Results: {len(res)}')
    for i,(t,u,s) in enumerate(res[:15]):
        print(f'[{i+1}] {t[:140]}')
        print(f'    URL: {u[:250]}')
        print(f'    SNIP: {s[:500]}')
        print()
