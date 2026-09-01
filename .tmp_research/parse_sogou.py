import sys, io, re, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def parse(fn):
    with open(fn, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    # find vrwrap blocks
    blocks = re.split(r'<div class="vrwrap"', html)[1:]
    out = []
    for b in blocks:
        # title in h3
        mh = re.search(r'<h3[^>]*class="[^"]*vr-title[^"]*"[^>]*>(.*?)</h3>', b, re.DOTALL)
        if not mh: continue
        title_html = mh.group(1)
        ma = re.search(r'<a[^>]*href="([^"]+)"', title_html)
        url = ma.group(1) if ma else ''
        # clean em/comment tags
        title = re.sub(r'<!--.*?-->','',title_html)
        title = re.sub(r'<[^>]+>','',title).strip()
        # snippet: <div class="space-txt" or str_text_info or attr-ol
        snip = ''
        for pat in [r'<div class="[^"]*str_text_info[^"]*"[^>]*>(.*?)</div>\s*</div>',
                    r'<div class="[^"]*fz-mil[^"]*"[^>]*>(.*?)</div>',
                    r'<div class="[^"]*space-txt[^"]*"[^>]*>(.*?)</div>',
                    r'<p class="str_time_info[^"]*"[^>]*>(.*?)</p>',
                    r'<div class="[^"]*attr-ol[^"]*"[^>]*>(.*?)</div>']:
            ms = re.search(pat, b, re.DOTALL)
            if ms:
                cand = ms.group(1)
                cand = re.sub(r'<!--.*?-->','',cand)
                cand = re.sub(r'<[^>]+>',' ',cand)
                cand = re.sub(r'\s+',' ',cand).strip()
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
