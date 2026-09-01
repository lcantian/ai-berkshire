import re, html, os, sys, io, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def strip_html(text):
    text = re.sub(r'<script[^>]*>.*?</script>', ' ', text, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<style[^>]*>.*?</style>', ' ', text, flags=re.DOTALL|re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = html.unescape(text)
    text = re.sub(r'\s+', ' ', text)
    return text

files = [r'D:\AI\ai-berkshire\.tmp_research\sq2_377430.html', r'D:\AI\ai-berkshire\.tmp_research\sq2_93de0c.html', r'D:\AI\ai-berkshire\.tmp_research\sq2_188aab.html']
keywords = ['46105', '46160', '4695', '4680', '奔驰', '宝马', '奥迪', '保时捷', '装车', '六万', '6万', '出货', 'GWh', '良率', '客户', '定点']
window = 220
for fp in files:
    if not os.path.exists(fp): continue
    raw = None
    for enc in ['utf-8', 'gb18030']:
        try:
            with open(fp,'r',encoding=enc) as f:
                raw = f.read()
            break
        except: pass
    if not raw: continue
    text = strip_html(raw)
    print(f"\n{'='*70}\n{os.path.basename(fp)}\n{'='*70}")
    seen = set()
    for kw in keywords:
        for m in re.finditer(re.escape(kw), text, re.IGNORECASE):
            s = max(0, m.start()-window); e = min(len(text), m.end()+window)
            snip = text[s:e].strip()
            snip = ''.join(c if c.isprintable() or c in '\n\t' else ' ' for c in snip)
            key = m.start()//250
            if key in seen: continue
            seen.add(key)
            if len(snip)<60: continue
            print(f"[{kw}] ...{snip}...")
