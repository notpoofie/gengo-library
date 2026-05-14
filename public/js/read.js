// ============================================================
// read.js — Loads a book's meta + a specific chapter, renders the
// tokenized text with reader.js, wires the chapter navigation.
// ============================================================
(function () {
  'use strict';

  document.addEventListener('gengo-i18n-ready', init);

  let _meta = null;
  let _bookId = null;
  let _chapterIdx = 1;

  async function init() {
    setupLangSwitcher();
    const params = new URLSearchParams(window.location.search);
    _bookId = params.get('id');
    _chapterIdx = parseInt(params.get('ch') || '1', 10) || 1;

    if (!_bookId) {
      document.getElementById('reader-root').textContent = '?';
      return;
    }
    await loadMeta();
    await loadChapter(_chapterIdx);
  }

  function setupLangSwitcher() {
    const lang = window.GengoI18n.currentLang();
    document.querySelectorAll('.lang-switcher button').forEach(btn => {
      if (btn.dataset.lang === lang) btn.classList.add('active');
      btn.addEventListener('click', () => window.GengoI18n.setLang(btn.dataset.lang));
    });
  }

  async function loadMeta() {
    try {
      const res = await fetch('books/' + encodeURIComponent(_bookId) + '/meta.json');
      _meta = await res.json();
      document.title = (_meta.title?.ja || _bookId) + ' — Gengo';
      renderToolbar();
    } catch (e) {
      console.error('[read] failed to load meta', e);
    }
  }

  function renderToolbar() {
    const root = document.getElementById('reader-root');
    const t = window.GengoI18n.t;
    const lang = window.GengoI18n.currentLang();

    root.innerHTML = '';

    // Toolbar
    const toolbar = document.createElement('div');
    toolbar.className = 'reader-toolbar';

    const backLink = document.createElement('a');
    const backParams = new URLSearchParams();
    backParams.set('id', _bookId);
    if (lang !== 'fr') backParams.set('lang', lang);
    backLink.href = 'book.html?' + backParams.toString();
    backLink.textContent = t('reader.back_to_book');
    backLink.style.fontSize = '0.85rem';
    backLink.style.color = 'var(--subtle)';
    backLink.style.textDecoration = 'none';
    backLink.style.padding = '6px 12px';
    toolbar.appendChild(backLink);

    // Chapter selector
    if (_meta && _meta.chapters && _meta.chapters.length > 1) {
      const sel = document.createElement('select');
      sel.id = 'chapter-select';
      for (const ch of _meta.chapters) {
        const opt = document.createElement('option');
        opt.value = ch.index;
        opt.textContent = ch.index + '. ' + (ch.title || 'Chapitre ' + ch.index);
        sel.appendChild(opt);
      }
      sel.value = String(_chapterIdx);
      sel.addEventListener('change', () => goToChapter(parseInt(sel.value, 10)));
      toolbar.appendChild(sel);
    }

    // Prev / progress / next
    const prev = document.createElement('button');
    prev.type = 'button';
    prev.textContent = '◀';
    prev.setAttribute('aria-label', t('reader.prev'));
    prev.addEventListener('click', () => goToChapter(_chapterIdx - 1));
    toolbar.appendChild(prev);

    const progress = document.createElement('span');
    progress.className = 'progress';
    progress.id = 'chapter-progress';
    toolbar.appendChild(progress);

    const next = document.createElement('button');
    next.type = 'button';
    next.textContent = '▶';
    next.setAttribute('aria-label', t('reader.next'));
    next.addEventListener('click', () => goToChapter(_chapterIdx + 1));
    toolbar.appendChild(next);

    // Furigana toggle
    const furi = document.createElement('button');
    furi.type = 'button';
    furi.className = 'furigana-toggle';
    furi.textContent = 'あ';
    furi.setAttribute('aria-label', t('reader.furigana_toggle'));
    furi.setAttribute('title', t('reader.furigana_toggle'));
    if (window.GengoReader.getFuriganaOn()) furi.classList.add('active');
    furi.addEventListener('click', () => {
      const on = !window.GengoReader.getFuriganaOn();
      window.GengoReader.setFuriganaOn(on);
      furi.classList.toggle('active', on);
    });
    toolbar.appendChild(furi);

    const spacer = document.createElement('span');
    spacer.className = 'spacer';
    toolbar.appendChild(spacer);

    root.appendChild(toolbar);

    // Chapter content placeholder
    const content = document.createElement('article');
    content.id = 'chapter-content';
    content.className = 'chapter-content';
    content.innerHTML = '<p class="loading">…</p>';
    root.appendChild(content);

    // Bottom nav
    const nav = document.createElement('div');
    nav.className = 'chapter-nav';
    const prev2 = document.createElement('button');
    prev2.id = 'nav-prev';
    prev2.type = 'button';
    prev2.textContent = '◀ ' + t('reader.prev');
    prev2.addEventListener('click', () => goToChapter(_chapterIdx - 1));
    nav.appendChild(prev2);

    const next2 = document.createElement('button');
    next2.id = 'nav-next';
    next2.type = 'button';
    next2.textContent = t('reader.next') + ' ▶';
    next2.addEventListener('click', () => goToChapter(_chapterIdx + 1));
    nav.appendChild(next2);
    root.appendChild(nav);

    window.GengoReader.bindReaderClicks(content);
    updateNavState();
  }

  function updateNavState() {
    const total = _meta?.chapters_count || 1;
    const progress = document.getElementById('chapter-progress');
    if (progress) progress.textContent = _chapterIdx + ' / ' + total;
    const sel = document.getElementById('chapter-select');
    if (sel) sel.value = String(_chapterIdx);

    document.querySelectorAll('.reader-toolbar button[aria-label]').forEach(b => {
      if (b.getAttribute('aria-label') === window.GengoI18n.t('reader.prev')) {
        b.disabled = _chapterIdx <= 1;
      }
      if (b.getAttribute('aria-label') === window.GengoI18n.t('reader.next')) {
        b.disabled = _chapterIdx >= total;
      }
    });
    const navPrev = document.getElementById('nav-prev');
    const navNext = document.getElementById('nav-next');
    if (navPrev) navPrev.disabled = _chapterIdx <= 1;
    if (navNext) navNext.disabled = _chapterIdx >= total;
  }

  async function loadChapter(idx) {
    if (!_meta) return;
    const total = _meta.chapters_count || 1;
    if (idx < 1 || idx > total) return;
    _chapterIdx = idx;
    updateNavState();

    const content = document.getElementById('chapter-content');
    if (content) content.innerHTML = '<p class="loading">…</p>';

    // Find chapter file
    const chapterInfo = _meta.chapters.find(c => c.index === idx);
    if (!chapterInfo) return;
    const file = chapterInfo.file || ('chapter-' + String(idx).padStart(3, '0') + '.json');

    try {
      const res = await fetch('books/' + encodeURIComponent(_bookId) + '/' + file);
      const data = await res.json();
      renderChapter(content, data);
    } catch (e) {
      console.error('[read] failed to load chapter', e);
      content.innerHTML = '<p class="empty">?</p>';
    }
  }

  function renderChapter(container, chapter) {
    container.innerHTML = '';
    // Chapter title heading
    if (chapter.title) {
      const h1 = document.createElement('h1');
      h1.textContent = chapter.title;
      container.appendChild(h1);
    }
    // Body wrapper that reader.js fills
    const body = document.createElement('div');
    container.appendChild(body);
    window.GengoReader.renderParagraphs(body, chapter.paragraphs || []);
    window.GengoReader.bindReaderClicks(body);

    // Scroll to top of content
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }

  function goToChapter(idx) {
    // Close any open popup
    if (window.GengoReader && window.GengoReader.closePopup) {
      window.GengoReader.closePopup();
    }
    // Update URL without full page reload
    const params = new URLSearchParams(window.location.search);
    params.set('ch', String(idx));
    history.replaceState(null, '', '?' + params.toString());
    loadChapter(idx);
  }

  // Keyboard navigation: arrow keys
  document.addEventListener('keydown', e => {
    // Ignore if user is typing in a field
    if (e.target.matches('input, textarea, select')) return;
    if (e.key === 'ArrowRight') goToChapter(_chapterIdx + 1);
    else if (e.key === 'ArrowLeft') goToChapter(_chapterIdx - 1);
  });
})();
