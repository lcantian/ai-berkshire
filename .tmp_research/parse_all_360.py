import re, html, os, sys, io, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def strip_html(text):
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text

files = sorted(glob.glob(r'D:\AI\ai-berkshire\.tmp_research\sq_*.html')) + sorted(glob.glob(r'D:\AI\ai-berkshire\.tmp_research\so360_eve*.html'))

keywords = ['大圆柱', '46系', '46950', '46105', '46160', '46140', '4680', '良率', 'GWh', 'TWh', '产能', '投产', '量产', '定点', '宝马', '奔驰', '保时捷', '小鹏', '特斯拉', '宁德', '荆门', '沈阳', '成都', '惠州', '匈牙利', '马来西亚', '出货', 'Neue Klasse', 'Rimac', 'BMW', 'Mercedes', 'Porsche', 'Tesla', 'CATL']

window = 240
agg = {}
for fp in files:
    raw = None
    for enc in ['utf-8', 'gb18030']:
        try:
            with open(fp, 'r', encoding=enc) as f:
                raw = f.read()
            break
        except:
            pass
    if not raw: continue
    text = strip_html(raw)
    for kw in keywords:
        for m in re.finditer(re.escape(kw), text, re.IGNORECASE):
            s = max(0, m.start()-window)
            e = min(len(text), m.end()+window)
            snip = text[s:e].strip()
            snip = ''.join(c if c.isprintable() or c in '\n\t' else ' ' for c in snip)
            # require minimum density: at least 2 keyword hits in window OR very informative
            kc = sum(1 for k in keywords if k.lower() in snip.lower())
            if kc < 2 and len(snip) < 100: continue
            key = (fp, m.start() // 280)
            if key in agg: continue
            agg[key] = (kw, snip)

# output
out = []
last_fp = None
for fp in sorted(agg.keys()):
    if fp[0] != last_fp:
        out.append(f"\n{'='*80}\nFILE: {os.path.basename(fp[0])}\n{'='*80}")
        last_fp = fp[0]
    kw, snip = agg[fp]
    out.append(f"\n[{kw}] ...{snip}...")

with open(r'D:\AI\ai-berkshire\.tmp_research\all_360_parsed.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print(f"Files: {len(files)}; Snippets: {len(agg)}")
