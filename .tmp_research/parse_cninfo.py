import re, html, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
with open(r'D:\AI\ai-berkshire\.tmp_research\cninfo_300014.html','r',encoding='utf-8',errors='ignore') as f:
    raw=f.read()
text=re.sub(r'<script[^>]*>.*?</script>',' ',raw,flags=re.DOTALL|re.I)
text=re.sub(r'<style[^>]*>.*?</style>',' ',text,flags=re.DOTALL|re.I)
text=re.sub(r'<[^>]+>',' ',text)
text=html.unescape(text)
text=re.sub(r'\s+',' ',text)
print(text[:6000])
