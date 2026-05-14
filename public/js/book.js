// ============================================================
// book.js — Loads a single book's meta.json and renders the
// summary + table of contents.
// ============================================================
(function () {
  'use strict';

  document.addEventListener('gengo-i18n-ready', init);

  function init() {
    setupLangSwitcher();
    const params = new URLSearchParams(window.location.search);
    const id = params.get('id');
    if (!id) {
      document.getElementById('book-content').textContent = '?';
      return;
    }
    // Make back-link preserve the lang param
    const lang = window.GengoI18n.currentLang();
    const back = document.getElementById('back-link');
    if (back && lang !== 'fr') back.href = 'index.html?lang=' + lang;
    loadBook(id);
  }

  function setupLangSwitcher() {
    const lang = window.GengoI18n.currentLang();
    document.querySelectorAll('.lang-switcher button').forEach(btn => {
      if (btn.dataset.lang === lang) btn.classList.add('active');
      btn.addEventListener('click', () => window.GengoI18n.setLang(btn.dataset.lang));
    });
  }

  async function loadBook(id) {
    const root = document.getElementById('book-content');
    try {
      const res = await fetch('books/' + encodeURIComponent(id) + '/meta.json');
      if (!res.ok) throw new Error('meta missing');
      const meta = await res.json();
      render(root, meta);
      document.title = (meta.title?.ja || id) + ' — Gengo';
    } catch (e) {
      console.error('[book] failed to load', e);
      root.classList.remove('loading');
      root.textContent = '?';
    }
  }

  function render(root, meta) {
    root.classList.remove('loading');
    root.innerHTML = '';
    const t = window.GengoI18n.t;
    const lang = window.GengoI18n.currentLang();

    // Header block
    const header = document.createElement('div');
    header.className = 'book-page-header';

    const titleJa = document.createElement('h1');
    titleJa.className = 'book-page-title-ja';
    titleJa.textContent = meta.title?.ja || meta.id;
    header.appendChild(titleJa);

    const titleTr = meta.title?.[lang];
    if (titleTr && titleTr !== titleJa.textContent) {
      const trEl = document.createElement('div');
      trEl.className = 'book-page-title-tr';
      trEl.textContent = titleTr;
      header.appendChild(trEl);
    }

    const author = meta.author?.[lang] || meta.author?.ja;
    if (author) {
      const a = document.createElement('div');
      a.className = 'book-page-author';
      a.textContent = t('book.by_author', { author });
      header.appendChild(a);
    }

    // Meta badges
    const meta1 = document.createElement('div');
    meta1.className = 'book-meta';
    if (meta.level) {
      const lvl = document.createElement('span');
      lvl.className = 'badge badge-level-' + meta.level;
      lvl.textContent = t('level.' + meta.level);
      meta1.appendChild(lvl);
    }
    if (meta.tokens_count) {
      const tk = document.createElement('span');
      tk.className = 'badge badge-tokens';
      tk.textContent = t('book.tokens', { n: meta.tokens_count.toLocaleString() });
      meta1.appendChild(tk);
    }
    if (meta.chapters_count) {
      const ch = document.createElement('span');
      ch.className = 'badge badge-tokens';
      ch.textContent = t('book.chapters', { n: meta.chapters_count });
      meta1.appendChild(ch);
    }
    header.appendChild(meta1);
    root.appendChild(header);

    // Summary
    const summary = meta.summary?.[lang];
    if (summary) {
      const h2 = document.createElement('h2');
      h2.textContent = t('book.summary');
      root.appendChild(h2);
      const p = document.createElement('div');
      p.className = 'book-page-summary';
      p.textContent = summary;
      root.appendChild(p);
    }

    // Table of contents
    if (meta.chapters && meta.chapters.length) {
      const h2 = document.createElement('h2');
      h2.textContent = t('book.toc');
      root.appendChild(h2);

      const ul = document.createElement('ul');
      ul.className = 'toc-list';
      for (const ch of meta.chapters) {
        const li = document.createElement('li');
        const a = document.createElement('a');
        const params = new URLSearchParams();
        params.set('id', meta.id);
        params.set('ch', ch.index);
        if (lang !== 'fr') params.set('lang', lang);
        a.href = 'read.html?' + params.toString();

        const num = document.createElement('span');
        num.className = 'toc-num';
        num.textContent = ch.index + '.';
        a.appendChild(num);

        const title = document.createElement('span');
        title.className = 'toc-title';
        title.textContent = ch.title || ('Chapitre ' + ch.index);
        a.appendChild(title);

        if (ch.paragraphs_count) {
          const stats = document.createElement('span');
          stats.className = 'toc-stats';
          stats.textContent = ch.paragraphs_count + ' ¶';
          a.appendChild(stats);
        }

        li.appendChild(a);
        ul.appendChild(li);
      }
      root.appendChild(ul);
    }
  }
})();
