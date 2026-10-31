"""Generate crawlable pages from site settings and numbered chapter text files."""
from pathlib import Path
from html import escape as e
from xml.sax.saxutils import escape as xe
from urllib.parse import urlsplit, quote, unquote, urlencode
from chapter_source import load_chapters
import json, os, re, shutil

ROOT = Path(__file__).parent
D = json.loads((ROOT / 'content/site.json').read_text())
for work in D['works']:
    if work.get('chapters_directory'):
        work['chapters'] = load_chapters(ROOT / work['chapters_directory'])
    else:
        for chapter in work['chapters']:
            chapter['demo'] = bool(chapter.get('notice'))
HAS_DEMO = any(c.get('demo') for w in D['works'] for c in w['chapters'])
ALL_DEMO = all(c.get('demo') for w in D['works'] for c in w['chapters'])
OUT = Path(os.environ.get('OUTPUT_DIR', str(ROOT / 'dist'))).resolve()
OUT.mkdir(exist_ok=True)
(OUT / 'feed.xml').unlink(missing_ok=True)
for name in ('assets', 'works', 'read', 'about', 'manage'):
    if (OUT / name).exists(): shutil.rmtree(OUT / name)
(OUT / 'assets').mkdir()
for name in ('style.css', 'app.js', 'favicon.svg'):
    shutil.copy(ROOT / name, OUT / 'assets' / name)
(OUT / 'assets/fonts').mkdir()
for name in ('Orbitron-Variable.ttf', 'OFL.txt'):
    shutil.copy(ROOT / 'fonts' / name, OUT / 'assets/fonts' / name)
ORIGIN = (os.environ.get('SITE_URL') or D.get('origin') or 'http://localhost:8000').rstrip('/')
parsed_origin = urlsplit(ORIGIN)
if parsed_origin.scheme not in ('http', 'https') or not parsed_origin.netloc or parsed_origin.query or parsed_origin.fragment:
    raise ValueError('SITE_URL must be an absolute HTTP(S) site URL without query or fragment')
BASE = parsed_origin.path.rstrip('/')
pages = []
def words(ch): return sum(len(p) for p in ch['paragraphs'])
def url(path): return ORIGIN + quote(path, safe='/%')
def write(path, body):
    if BASE:
        body = re.sub(r'(href|src|data-path)="(/(?!/)[^"]*)"', lambda m: m[1]+'="'+BASE+m[2]+'"', body)
    p = OUT / unquote(path.lstrip('/'))
    if path.endswith('/'): p = p / 'index.html'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(body)
    if path not in ('/404.html', '/manage/'): pages.append(path)
def header(active='', quiet=False):
    return f'''<a class="skip" href="#main">跳到正文</a><header class="header {'quiet' if quiet else ''}"><a class="brand" href="/" aria-label="{e(D['name'])}首页"><span class="brand-mark" aria-hidden="true">d.</span><span>{e(D['name'])}</span></a><nav aria-label="主导航"><a {'aria-current="page"' if active=='works' else ''} href="/works/">作品目录</a><a class="nav-index" href="/works/#chapters" aria-label="浏览所有章节">目录 </a></nav></header>'''
def footer():
    return f'''<footer class="footer"><a class="footer-brand" href="/">{e(D['name'])}</a><span>Baby just say YES</span><div><a class="author-mark" href="/manage/" aria-label="章节管理" data-label="章节管理"><span aria-hidden="true"></span></a></div><small>© 2026 {e(D['name'])}</small></footer>'''
def page(title, description, path, body, active='', reader=False, structured=None, notfound=False):
    ld = structured or {'@context':'https://schema.org','@type':'WebSite','name':D['name'],'url':url('/')}
    return f'''<!doctype html><html lang="zh-CN" data-theme="light" data-base="{e(BASE,quote=True)}"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(title)} · {e(D['name'])}</title><meta name="description" content="{e(description,quote=True)}"><meta name="color-scheme" content="dark light"><meta name="theme-color" content="#ffffff"><meta name="robots" content="{'noindex' if notfound else 'index,follow'}"><link rel="canonical" href="{e(url(path))}"><meta property="og:type" content="{'article' if reader else 'website'}"><meta property="og:title" content="{e(title,quote=True)} · {e(D['name'])}"><meta property="og:description" content="{e(description,quote=True)}"><meta property="og:url" content="{e(url(path))}"><link rel="icon" type="image/svg+xml" href="/assets/favicon.svg"><link rel="stylesheet" href="/assets/style.css"><script type="application/ld+json">{json.dumps(ld,ensure_ascii=False).replace('<','\\u003c')}</script><script src="/assets/app.js" defer></script></head><body class="{'reading' if reader else ''}">{header(active, reader)}{body}{footer()}<div id="toast" role="status" aria-live="polite"></div></body></html>'''
W = D['works'][0]
def chapter_label(c): return '演示章节' if c.get('demo') else '正文'
def chapter_suffix(c): return '（演示）' if c.get('demo') else ''
def date_label(c): return c.get('date', '')[5:].replace('-', '.')
DEMO_NOTICE = '<div class="demo-notice">含演示章节；标有“演示”的内容可在章节管理中替换。</div>' if HAS_DEMO else ''
def wp(w): return '/works/' + quote(w['slug'], safe='') + '/'
def cp(w,c): return '/read/' + quote(w['slug'], safe='') + '/' + quote(c['slug'], safe='') + '/'
def cover(w, compact=False):
    return f'''<div class="book-cover {'compact' if compact else ''}" role="img" aria-label="{e(w['title'])}：{e(w['subtitle'])}，{e(D['author'])}"><div class="cover-top">DASWOHLTEMPERIERTE / 001<span>SERIAL FICTION</span></div><div class="cover-light" aria-hidden="true"></div><div class="cover-rule" aria-hidden="true"></div><div class="cover-title"><small>A NOVEL / IN SERIAL</small><strong class="cover-book-title">{e(w['title'].upper())}</strong><span class="cover-subtitle">{e(w['subtitle'])}</span><span class="cover-author">{e(D['author'])}</span></div><div class="cover-bottom"><span>FICTION — IN SERIAL</span><span>第一卷</span></div></div>'''
def rows(w, limit=None):
    chapters = w['chapters'][:limit] if limit else w['chapters']
    rendered = []
    for i, c in enumerate(chapters, 1):
        meta = ' / ' + date_label(c) if c.get('date') else ''
        if c.get('demo'): meta += ' · 演示'
        newest = '<em>最新</em>' if i == len(w['chapters']) else ''
        rendered.append(f'<a class="chapter-row" data-search="{e(c["title"])} {i:02d}" href="{cp(w,c)}"><span class="chapter-num">{i:02d}</span><span class="chapter-name">{e(c["title"])}{newest}</span><span class="chapter-meta">{words(c):,} 字 <span>{e(meta)}</span></span><span class="row-arrow">查看</span></a>')
    return ''.join(rendered)
def resume(w): return f'<a class="button secondary resume" href="{cp(w,w["chapters"][0])}" data-resume="{w["slug"]}" hidden>继续阅读 </a>'
home = f'''<main id="main"><section class="hero"><div class="hero-intro"><div class="eyebrow hero-kicker"><span class="live-dot"></span>McLaren</div><h1 class="hero-codes" aria-label="OP81 LN4"><span class="code-line">OP81</span><span class="code-line code-orange">LN4</span></h1><p class="hero-desc hero-manifesto">ALL THE FANTASIES</p><a class="text-link" href="{wp(W)}">进入连载 </a></div><div class="hero-aside"><span class="vertical-note">READ AT YOUR OWN PACE</span><a class="cover-link" href="{wp(W)}">{cover(W)}</a><div class="cover-caption"><span>01 / 当前作品</span><span>{e(W['status'])} <span class="live-dot"></span></span></div></div><div class="hero-bottom"><span>FICTION / WORDS / AFTER HOURS</span><a href="#current">向下阅读 </a><span>SCROLL TO EXPLORE</span></div></section><section id="current" class="section current"><div class="section-heading"><div><span class="eyebrow">01 / THE SERIAL</span><h2>连载中</h2></div><span class="muted">一个故事，一次相逢。</span></div><div class="work-summary"><div><div class="tags"><span class="accent">{e(W['status'])}</span>{''.join('<span>'+e(t)+'</span>' for t in W.get('tags',[]))}</div><h3><a href="{wp(W)}">{e(W['title'])}</a></h3><p>{e(W['subtitle'])}</p><p class="muted work-description">{e(W['description'])}</p><div class="button-row"><a class="button" href="{cp(W,W['chapters'][0])}">从第一章开始 </a>{resume(W)}</div></div><div class="work-data"><div><strong>01—{len(W['chapters']):02d}</strong><span>章节 / 按顺序阅读</span></div><div><strong>{sum(words(c) for c in W['chapters']):,}<small>字</small></strong><span>正文总字数</span></div><a class="text-link" href="{wp(W)}">作品详情与目录 </a></div></div></section><section class="section latest"><div class="section-heading"><div><span class="eyebrow">02 / THE CHAPTERS</span><h2>章节一览</h2></div><a class="text-link" href="{wp(W)}#chapters">查看全部 </a></div><div class="chapter-table">{rows(W)}</div>{DEMO_NOTICE}</section><section class="closing driver-signature" aria-label="Oscar Piastri and Lando Norris"><p><span>Oscar Piastri</span><span class="driver-norris">Lando Norris</span></p></section></main>'''
write('/',page('首页',D['description'],'/',home))
workbody=f'''<main id="main"><div class="breadcrumb"><a href="/">首页</a><span>/</span><a href="/works/">作品</a><span>/</span><span>{e(W['title'])}</span></div><section class="work-hero"><div class="work-cover">{cover(W,True)}</div><div class="work-info"><span class="eyebrow">THE SERIAL / 001</span><div class="tags"><span class="accent">{e(W['status'])}</span>{''.join('<span>'+e(t)+'</span>' for t in W.get('tags',[]))}</div><h1>{e(W['title'])}</h1><p class="subtitle">{e(W['subtitle'])}</p><p class="work-description">{e(W['description'])}</p><div class="work-facts"><span>{len(W['chapters'])} 章</span><span>{sum(words(c) for c in W['chapters']):,} 字正文</span><span>{e(D['author'])}</span></div><div class="button-row"><a class="button" href="{cp(W,W['chapters'][0])}">开始阅读 </a>{resume(W)}</div></div></section><section id="chapters" class="section contents"><div class="section-heading"><div><span class="eyebrow">TABLE OF CONTENTS</span><h2>章节目录 <small>/ {len(W['chapters']):02d}</small></h2></div><div class="catalog-tools"><label class="search"><span aria-hidden="true">⌕</span><input id="chapter-search" type="search" placeholder="搜索章节" aria-label="搜索章节标题"></label><button class="sort-button" id="sort" aria-label="切换章节排列顺序" aria-pressed="false">正序</button></div></div><p class="volume-label">第一卷 <span>{'· 含演示章节' if HAS_DEMO else ''}</span></p><div class="chapter-table" id="chapter-list">{rows(W)}</div><p id="no-results" class="empty-state" hidden>没有找到这章。试试其他标题或章节号。</p><p id="search-status" class="sr-only" role="status" aria-live="polite"></p>{DEMO_NOTICE}</section></main>'''
write(wp(W),page(W['title']+' · 作品与目录',W['description'],wp(W),workbody,'works'))
archive = f'''<main id="main" class="archive-page"><div class="breadcrumb"><a href="/">首页</a><span>/</span><span>作品目录</span></div><div class="page-title"><span class="eyebrow">THE COLLECTION / 01</span><h1>作品目录<span class="accent">.</span></h1><p class="muted">故事各有去处，在这里找到起点。</p></div><a class="archive-work" href="{wp(W)}"><div>{cover(W,True)}</div><div><div class="tags"><span class="accent">{e(W['status'])}</span><span>{e(' / '.join(W.get('tags',[])))}</span></div><h2>{e(W['title'])}</h2><p>{e(W['subtitle'])}</p><p class="muted">{e(W['description'])}</p><span class="text-link">{len(W['chapters'])} 个章节 · 进入作品 </span></div></a><section id="chapters" class="section"><div class="section-heading"><h2>全部章节</h2><span class="muted">{e(W['title'])}{' / 含演示章节' if HAS_DEMO else ''}</span></div>{rows(W)}</section></main>'''
write('/works/',page('作品目录','浏览长篇连载、作品介绍与章节目录。','/works/',archive,'works'))
for idx,c in enumerate(W['chapters']):
    path=cp(W,c)
    prev = f'<a href="{cp(W,W["chapters"][idx-1])}"> 上一章</a>' if idx else '<span class="muted">已是第一章</span>'
    nex = f'<a href="{cp(W,W["chapters"][idx+1])}">下一章 </a>' if idx+1<len(W['chapters']) else '<span class="muted">已读至最新章节</span>'
    options=''.join(f'<a {"aria-current=\"page\"" if x==c else ""} href="{cp(W,x)}"><span>{i:02d}</span>{e(x["title"])}</a>' for i,x in enumerate(W['chapters'],1))
    body=f'''<div class="reading-progress" aria-hidden="true"><span id="progress-bar"></span></div><main id="main" data-work="{W['slug']}" data-chapter="{c['slug']}" data-title="{e(c['title'])}" data-path="{path}"><div class="reader-top"><a href="{wp(W)}"> {e(W['title'])} / 目录</a><span>CHAPTER {idx+1:02d} / {len(W['chapters']):02d}</span></div><div class="reader-layout"><aside class="reader-sidebar"><span class="eyebrow">本卷目录</span><h2>{e(W['title'])}</h2><nav aria-label="章节目录">{options}</nav><p>慢慢读。<br>故事会在这里等你。</p></aside><div class="reader-column"><header class="chapter-heading"><span class="eyebrow">CHAPTER {idx+1:02d}</span><h1>{e(c['title'])}</h1><p>{(e(c['date'].replace('-','.'))+' <span> / </span>') if c.get('date') else ''}{words(c)} 字 <span> / </span>{chapter_label(c)}</p></header><div class="reader-toolbar" aria-label="阅读设置"><div><button id="smaller" aria-label="缩小正文" title="缩小正文">A−</button><span id="font-size" aria-live="polite">20</span><button id="larger" aria-label="放大正文" title="放大正文">A＋</button><span class="toolbar-line"></span><button id="font-toggle" aria-label="切换正文字体" aria-pressed="false">宋体</button></div><div><button class="theme-dot night" data-theme-choice="dark" aria-label="夜间阅读" aria-pressed="false"></button><button class="theme-dot paper" data-theme-choice="paper" aria-label="暖纸阅读" aria-pressed="false"></button><button class="theme-dot light" data-theme-choice="light" aria-label="白底阅读" aria-pressed="true"></button><button id="bookmark" aria-label="收藏本章到此浏览器" aria-pressed="false" title="收藏本章">☆</button></div></div><article id="chapter-text" class="prose" aria-label="章节正文">{('<p class="sample-note">'+e(c['notice'])+'</p>') if c.get('notice') else ''}{''.join(f'<p>{e(p)}</p>' for p in c['paragraphs'])}</article><div class="chapter-end"><span>— 本章完 —</span><button class="text-link" id="copy-link">复制本章链接 </button></div><nav class="chapter-navigation" aria-label="翻页">{prev}<a href="{wp(W)}#chapters">章节目录</a>{nex}</nav><div class="reader-note">阅读位置与收藏仅保存在当前浏览器。</div></div></div><button class="back-top" id="back-top" aria-label="返回顶部">顶部</button></main>'''
    ld={'@context':'https://schema.org','@type':'Chapter','name':c['title']+chapter_suffix(c),'url':url(path),'inLanguage':'zh-CN','position':idx+1,'isPartOf':{'@type':'Book','name':W['title'],'url':url(wp(W))}}
    write(path,page(c['title']+' · '+W['title'],c['paragraphs'][0],path,body,reader=True,structured=ld))
# The author entry links to GitHub's authenticated editor; this Site stores no tokens.
REPOSITORY = D.get('repository', 'azzure0216-netizen/daswohltemperierte')
REPO_URL = 'https://github.com/' + REPOSITORY
SOURCE_DIRECTORY = W.get('chapters_directory', 'chapters')
NEXT_NUMBER = max(int(c['slug']) for c in W['chapters']) + 1
NEW_URL = REPO_URL + '/new/main/' + quote(SOURCE_DIRECTORY, safe='/') + '?' + urlencode({'filename': f'{NEXT_NUMBER:02d}.md'})
manage_rows = []
for i, c in enumerate(W['chapters'], 1):
    source_path = SOURCE_DIRECTORY + '/' + c.get('source_file', c['slug'] + '.md')
    edit_url = REPO_URL + '/edit/main/' + quote(source_path, safe='/')
    badge = '<em>演示</em>' if c.get('demo') else ''
    manage_rows.append(f'<a class="chapter-row" href="{e(edit_url, quote=True)}" target="_blank" rel="noopener"><span class="chapter-num">{i:02d}</span><span class="chapter-name">{e(c["title"])}{badge}</span><span class="chapter-meta">粘贴／修改正文</span><span class="row-arrow">编辑</span></a>')
manage_body = f'''<main id="main" class="about-page manage-page"><div class="breadcrumb"><a href="/">首页</a><span>/</span><span>章节管理</span></div><div class="page-title"><span class="eyebrow">WRITE &amp; PUBLISH</span><h1>章节管理<span class="accent">.</span></h1><p class="muted">选一章，粘贴完整正文，再提交发布。</p></div><div class="author-note"><p>编辑和保存将在 GitHub 中完成，需要登录拥有本仓库写入权限的账号。提交到 main 后，网站会自动发布更新。</p><p>当前标注“演示”的章节可以全选替换；第一行写标题，下面直接粘贴正文。</p></div><div class="button-row"><a class="button" href="{e(NEW_URL,quote=True)}" target="_blank" rel="noopener">新增第 {NEXT_NUMBER} 章 </a><a class="button secondary" href="{REPO_URL}/actions" target="_blank" rel="noopener">查看发布进度 </a></div><section class="section"><div class="section-heading"><h2>{e(W['title'])}</h2><span class="muted">{len(W['chapters'])} 个章节文件</span></div><div class="chapter-table">{''.join(manage_rows)}</div></section><section class="section paste-help"><h2>直接按这个格式粘贴</h2><pre>第一章 你的章节标题

这是第一段正文。

这是第二段正文。</pre><p>正文按换行分段，空行可有可无。第一行也可以写成“# 第一章 你的章节标题”。</p><p>修改已有章节：打开后全选文件内容，粘贴完整章节，点击 Commit changes，提交到 main。</p><p>新增章节：入口已填好下一个编号的文件名。保持文件名为数字加 .md，例如 {NEXT_NUMBER:02d}.md，然后粘贴标题和正文。以后尽量保留已发布文件的编号。</p><p>可选：在标题下方写“日期：2026-10-31”；日期不填也可以发布。</p><p>保存后到“查看发布进度”等待绿色勾号，再回网站刷新。没有提交的编辑不会出现在网站上。</p></section><div class="button-row"><a class="text-link" href="{wp(W)}">返回作品目录 </a></div></main><style>.manage-page{{padding-bottom:65px}}.author-note{{color:var(--muted);font-size:13px;line-height:2}}.author-note p+p{{margin-top:12px}}.paste-help h2{{font-size:24px;font-family:serif;margin-bottom:25px}}.paste-help pre{{white-space:pre-wrap;overflow-wrap:anywhere;background:var(--surface);border:1px solid var(--line);padding:22px;font:14px/2 sans-serif;margin-bottom:25px}}.paste-help p{{font-size:13px;line-height:2;color:var(--muted);margin:15px 0}}.manage-page .section-heading>.muted{{display:block}}.manage-page .chapter-name{{overflow-wrap:anywhere}}@media(max-width:700px){{.manage-page{{margin-left:24px;margin-right:24px}}.manage-page .button-row{{align-items:stretch}}.manage-page .button{{gap:12px}}.manage-page .section-heading>.muted{{font-size:10px;white-space:nowrap}}}}</style>'''
write('/manage/', page('章节管理', '选择章节，进入 GitHub 编辑器粘贴正文并发布。', '/manage/', manage_body, notfound=True))
write('/404.html',page('这一页暂时没有故事','页面不存在，请回到作品目录。','/404.html','<main id="main" class="not-found"><span class="eyebrow">404 / PAGE NOT FOUND</span><h1>这一页，<br>还没有故事。</h1><p>地址可能有误，也可能是章节尚未发布。</p><a class="button" href="/works/">回到作品目录 </a></main>',notfound=True))
(OUT/'robots.txt').write_text('User-agent: *\nAllow: /\nSitemap: '+url('/sitemap.xml')+'\n')
(OUT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+xe(url(p))+'</loc></url>' for p in pages)+'</urlset>')
(OUT/'.nojekyll').touch()
print(f'Generated {len(pages)} pages + 404, sitemap, robots.txt at {ORIGIN}')
