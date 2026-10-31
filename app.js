(() => {
  'use strict';
  const BASE = document.documentElement.dataset.base || '';
  const KEY = 'nightfolio-v1:' + (BASE || '/');
  const read = () => { try { return JSON.parse(localStorage.getItem(KEY)) || {}; } catch { return {}; } };
  const save = data => { try { localStorage.setItem(KEY, JSON.stringify(data)); return true; } catch { return false; } };
  const $ = s => document.querySelector(s);
  let timer;
  function toast(text) { const t = $('#toast'); t.textContent = text; t.classList.add('visible'); clearTimeout(timer); timer = setTimeout(() => t.classList.remove('visible'), 2600); }
  for (const link of document.querySelectorAll('[data-resume]')) {
    const progress = read().progress?.[link.dataset.resume];
    if (progress && typeof progress.path === 'string' && progress.path.startsWith(BASE + '/read/') && /^\/read\/[^/?#\\]+\/[^/?#\\]+\/$/.test(progress.path.slice(BASE.length))) {
      link.hidden = false; link.href = progress.path + '#resume'; link.textContent = '继续阅读 · ' + progress.title + ' ↗';
    }
  }
  const search = $('#chapter-search');
  if (search) {
    const list = $('#chapter-list'), rows = [...list.querySelectorAll('.chapter-row')];
    search.addEventListener('input', () => {
      const q = search.value.trim().toLocaleLowerCase(); let n = 0;
      rows.forEach(row => { row.hidden = !row.dataset.search.toLocaleLowerCase().includes(q); if (!row.hidden) n++; });
      $('#no-results').hidden = n > 0; $('#search-status').textContent = `找到 ${n} 个章节`;
    });
    let reversed = false;
    $('#sort').addEventListener('click', () => {
      reversed = !reversed;
      [...rows].sort((a,b) => reversed ? rows.indexOf(b)-rows.indexOf(a) : rows.indexOf(a)-rows.indexOf(b)).forEach(row => list.appendChild(row));
      $('#sort').textContent = reversed ? '倒序 ↑' : '正序 ↓'; $('#sort').setAttribute('aria-pressed', String(reversed));
    });
  }
  const main = document.querySelector('[data-chapter]');
  if (main) {
    const work = main.dataset.work, chapter = main.dataset.chapter, bookmarkKey = work + '/' + chapter;
    const prefs = read().prefs || {};
    let size = Number.isFinite(prefs.size) ? Math.min(28, Math.max(16, prefs.size)) : 20;
    let font = prefs.font === 'sans' ? 'sans' : 'serif';
    let theme = ['dark','paper','light'].includes(prefs.theme) ? prefs.theme : 'light';
    function applyPrefs(persist = false) {
      document.documentElement.style.setProperty('--reader-size', size + 'px');
      document.documentElement.style.setProperty('--reader-font', font === 'serif' ? '"Songti SC","Noto Serif CJK SC","Source Han Serif SC",SimSun,serif' : '"PingFang SC","Microsoft YaHei",sans-serif');
      document.body.dataset.readerTheme = theme;
      $('#font-size').textContent = size; $('#smaller').disabled = size <= 16; $('#larger').disabled = size >= 28;
      $('#font-toggle').textContent = font === 'serif' ? '宋体' : '黑体'; $('#font-toggle').setAttribute('aria-pressed', String(font === 'sans'));
      document.querySelectorAll('[data-theme-choice]').forEach(b => b.setAttribute('aria-pressed', String(b.dataset.themeChoice === theme)));
      document.querySelector('meta[name="theme-color"]').content = theme === 'dark' ? '#1c1714' : theme === 'paper' ? '#f6eadb' : '#ffffff';
      if (persist) { const data = read(); data.prefs = {size,font,theme}; if (!save(data)) toast('当前浏览器无法保存设置'); }
    }
    applyPrefs();
    $('#smaller').addEventListener('click', () => { size = Math.max(16, size-2); applyPrefs(true); });
    $('#larger').addEventListener('click', () => { size = Math.min(28, size+2); applyPrefs(true); });
    $('#font-toggle').addEventListener('click', () => { font = font === 'serif' ? 'sans' : 'serif'; applyPrefs(true); });
    document.querySelectorAll('[data-theme-choice]').forEach(b => b.addEventListener('click', () => { theme = b.dataset.themeChoice; applyPrefs(true); }));
    function paintBookmark() { const enabled = !!read().bookmarks?.[bookmarkKey]; $('#bookmark').textContent = enabled ? '★' : '☆'; $('#bookmark').setAttribute('aria-pressed', String(enabled)); $('#bookmark').setAttribute('aria-label', enabled ? '取消本章收藏' : '收藏本章到此浏览器'); }
    paintBookmark();
    $('#bookmark').addEventListener('click', () => {
      const data = read(); data.bookmarks ||= {};
      if (data.bookmarks[bookmarkKey]) delete data.bookmarks[bookmarkKey]; else data.bookmarks[bookmarkKey] = {path:main.dataset.path,title:main.dataset.title};
      if (!save(data)) { toast('当前浏览器无法保存收藏'); return; }
      paintBookmark(); toast(data.bookmarks[bookmarkKey] ? '本章已收藏到此浏览器' : '已取消本章收藏');
    });
    $('#copy-link').addEventListener('click', async () => {
      try { await navigator.clipboard.writeText(location.origin + location.pathname); toast('本章链接已复制'); }
      catch { toast('请复制浏览器地址栏中的本章网址'); }
    });
    $('#back-top').addEventListener('click', () => window.scrollTo({top:0,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth'}));
    const article = $('#chapter-text');
    function articleRange() { return {start:article.getBoundingClientRect().top+window.scrollY, end:article.getBoundingClientRect().bottom+window.scrollY-innerHeight*.55}; }
    let restoreDone = false;
    const old = read().progress?.[work];
    function restore() {
      if (location.hash === '#resume' && old?.chapter === chapter) {
        const r = articleRange(); window.scrollTo({top:Math.max(0,r.start + Math.max(0,r.end-r.start) * Math.min(1, Math.max(0,Number(old.fraction)||0))),behavior:'instant'});
        toast('已回到上次阅读位置');
      }
      restoreDone = true; update();
    }
    function update() {
      if (!restoreDone) return;
      const r=articleRange(), fraction=Math.min(1,Math.max(0,(scrollY-r.start)/Math.max(1,r.end-r.start)));
      $('#progress-bar').style.width = (fraction*100).toFixed(1)+'%';
      const data=read(); data.progress ||= {}; data.progress[work]={chapter,path:main.dataset.path,title:main.dataset.title,fraction}; save(data);
    }
    let ticking=false;
    window.addEventListener('scroll', () => { if (!ticking) { ticking=true; requestAnimationFrame(() => { ticking=false; update(); }); } }, {passive:true});
    window.addEventListener('pagehide',update);
    window.addEventListener('resize',update);
    if (document.readyState === 'complete') restore(); else window.addEventListener('load',restore,{once:true});
  }
  $('#clear-data')?.addEventListener('click', () => {
    try { localStorage.removeItem(KEY); $('#clear-status').textContent='已清除本浏览器的阅读进度、收藏与排版偏好。'; toast('阅读记录已清除'); }
    catch { $('#clear-status').textContent='当前浏览器不允许访问本地存储。'; }
  });
})();
