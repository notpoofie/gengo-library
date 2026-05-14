// ============================================================
// catalog.js — Loads catalog.json and renders book cards.
// ============================================================
(function () {
  'use strict';

  document.addEventListener('gengo-i18n-ready', init);
  if (!document.querySelector('script[src*="i18n.js"]')) init();

  function init() {
    setupLangSwitcher();
    loadCatalog();
    setupFilter();
  }

  function setupLangSwitcher() {
    const lang = window.GengoI18n.currentLang();
    document.querySelectorAll('.lang-switcher button').forEach(btn => {
      if (btn.dataset.lang === lang) btn.classList.add('active');
      btn.addEventListener('click', () => {
        window.GengoI18n.setLang(btn.dataset.lang);
      });
    });
  }

  let _books = [];
  let _currentFilter = 'all';

  async function loadCatalog() {
    const grid = document.getElementById('book-grid');
    try {
      const res = await fetch('catalog.json');
      if (!res.ok) throw new Error('catalog.json missing');
      const data = await res.json();
      _books = Array.isArray(data.books) ? data.books : [];
    } catch (e) {
      console.error('[catalog] failed to load', e);
      grid.innerHTML = '';
      const p = document.createElement('p');
      p.className = 'empty';
      p.textContent = window.GengoI18n.t('catalog.empty');
      grid.appendChild(p);
      return;
    }
    renderGrid();
  }

  function setupFilter() {
    const bar = document.getElementById('filter-bar');
    if (!bar) return;
    bar.addEventListener('click', e => {
      const btn = e.target.closest('button[data-level]');
      if (!btn) return;
      _currentFilter = btn.dataset.level;
      bar.querySelectorAll('button').forEach(b =>
        b.classList.toggle('active', b === btn));
      renderGrid();
    });
  }

  function renderGrid() {
    const grid = document.getElementById('book-grid');
    const t = window.GengoI18n.t;
    const lang = window.GengoI18n.currentLang();

    let books = _books;
    if (_currentFilter !== 'all') {
      books = books.filter(b => b.level === _currentFilter);
    }

    grid.innerHTML = '';
    if (books.length === 0) {
      const p = document.createElement('p');
      p.className = 'empty';
      p.textContent = t('catalog.empty');
      grid.appendChild(p);
      return;
    }

    for (const book of books) {
      const card = document.createElement('a');
      card.className = 'book-card';
      // Preserve current lang when navigating
      const params = new URLSearchParams();
      params.set('id', book.id);
      if (lang !== 'fr') params.set('lang', lang);
      card.href = 'book.html?' + params.toString();

      // Japanese title (always shown)
      const titleJa = document.createElement('div');
      titleJa.className = 'book-title-ja';
      titleJa.textContent = book.title?.ja || book.id;
      card.appendChild(titleJa);

      // Translated title (in current language if available)
      const titleTr = book.title?.[lang];
      if (titleTr && titleTr !== titleJa.textContent) {
        const trEl = document.createElement('div');
        trEl.className = 'book-title-tr';
        trEl.textContent = titleTr;
        card.appendChild(trEl);
      }

      // Author
      const author = book.author?.[lang] || book.author?.ja;
      if (author) {
        const authorEl = document.createElement('div');
        authorEl.className = 'book-author';
        authorEl.textContent = t('book.by_author', { author });
        card.appendChild(authorEl);
      }

      // Meta badges
      const meta = document.createElement('div');
      meta.className = 'book-meta';
      if (book.level) {
        const lvl = document.createElement('span');
        lvl.className = 'badge badge-level-' + book.level;
        lvl.textContent = t('level.' + book.level);
        meta.appendChild(lvl);
      }
      if (book.tokens_count) {
        const tk = document.createElement('span');
        tk.className = 'badge badge-tokens';
        tk.textContent = t('book.tokens', { n: book.tokens_count.toLocaleString() });
        meta.appendChild(tk);
      }
      card.appendChild(meta);

      grid.appendChild(card);
    }
  }
})();
