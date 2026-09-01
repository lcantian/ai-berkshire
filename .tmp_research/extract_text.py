import sys, io, re
from html.parser import HTMLParser
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.skip = 0
        self.text = []
    def handle_starttag(self, tag, attrs):
        if tag in ('script','style','noscript','iframe','svg'):
            self.skip += 1
        if tag in ('p','div','br','li','td','tr','h1','h2','h3','h4','h5','h6'):
            self.text.append('\n')
    def handle_endtag(self, tag):
        if tag in ('script','style','noscript','iframe','svg'):
            self.skip -= 1
        if tag in ('p','div','li','td','tr','h1','h2','h3','h4','h5','h6'):
            self.text.append('\n')
    def handle_data(self, data):
        if self.skip == 0:
            self.text.append(data)

def extract(fn, max_chars=8000):
    with open(fn, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    p = TextExtractor()
    try:
        p.feed(html)
    except Exception:
        pass
    text = ''.join(p.text)
    # clean
    text = re.sub(r'&nbsp;|&#160;|&ensp;|&emsp;', ' ', text)
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'&#\d+;', ' ', text)
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n+', '\n\n', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    # show middle section where article body usually is
    return text.strip()

for fn in sys.argv[1:]:
    print('======', fn, '======')
    t = extract(fn)
    print(f'[Total length: {len(t)}]')
    # print middle chunk (skip nav)
    print(t[:7000])
    print('...')
