"""Check generated links, canonical URLs and feeds before publishing."""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import urlsplit, unquote
import json
import os
import xml.etree.ElementTree as ET

ROOT = Path(__file__).parent
OUT = Path(os.environ.get('OUTPUT_DIR', str(ROOT / 'dist'))).resolve()
config = json.loads((ROOT / 'content/site.json').read_text())
SITE = (os.environ.get('SITE_URL') or config.get('origin') or 'http://localhost:8000').rstrip('/')
BASE = urlsplit(SITE).path.rstrip('/')

class Page(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.ids = set()
        self.links = []
        self.h1 = 0
        self.seo = set()
        self.inscript = False
        self.script = ''
        self.canonical = None
        self.base = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get('id'): self.ids.add(a['id'])
        if tag == 'html': self.base = a.get('data-base')
        if tag == 'h1': self.h1 += 1
        if tag == 'title': self.seo.add('title')
        if tag == 'meta' and a.get('name') == 'description': self.seo.add('description')
        if tag == 'link' and a.get('rel') == 'canonical':
            self.seo.add('canonical')
            self.canonical = a.get('href')
        for key in ('href', 'src', 'data-path'):
            if a.get(key): self.links.append(a[key])
        if tag == 'script' and a.get('type') == 'application/ld+json':
            self.inscript = True
            self.script = ''

    def handle_data(self, data):
        if self.inscript: self.script += data

    def handle_endtag(self, tag):
        if tag == 'script' and self.inscript:
            json.loads(self.script)
            self.inscript = False

pages = {p: Page(p.read_text()) for p in OUT.rglob('*.html')}
assert pages, 'No HTML pages found; run build.py first'
for file, page in pages.items():
    assert page.h1 == 1, (file, 'one h1 required')
    assert len(page.seo) == 3, (file, 'missing search metadata')
    assert page.base == BASE, (file, 'wrong reader base path')
    relative = '/' + file.relative_to(OUT).as_posix()
    if relative.endswith('/index.html'): relative = relative[:-10]
    assert page.canonical == SITE + relative, (file, 'wrong canonical', page.canonical)
    for raw in page.links:
        link = urlsplit(raw)
        if link.scheme or link.netloc: continue
        if not link.path:
            target = file
        else:
            assert link.path.startswith(BASE + '/'), (file, 'unprefixed link', raw)
            local = link.path[len(BASE):]
            target = OUT / local.lstrip('/')
            if local.endswith('/'): target = target / 'index.html'
        assert target.exists(), (file, 'broken link', raw)
        if link.fragment and target in pages and link.fragment != 'resume':
            assert unquote(link.fragment) in pages[target].ids, (file, 'missing anchor', raw)

sitemap = ET.parse(OUT / 'sitemap.xml')
for element in sitemap.getroot().iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc'):
    assert element.text.startswith(SITE + '/'), ('wrong sitemap URL', element.text)
feed = ET.parse(OUT / 'feed.xml')
for element in feed.getroot().iter('link'):
    assert element.text.startswith(SITE + '/'), ('wrong feed URL', element.text)
assert 'Sitemap: ' + SITE + '/sitemap.xml' in (OUT / 'robots.txt').read_text()
assert (OUT / '.nojekyll').exists()
assert not any('chatgpt.site' in p.read_text() for p in OUT.rglob('*') if p.suffix in ('.html','.xml','.txt','.js'))
print(f'PASS: {len(pages)} pages, internal links, reader paths, search metadata and XML feeds for {SITE}')
