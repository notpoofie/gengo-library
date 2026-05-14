// ============================================================
// i18n.js — Lightweight trilingual support (fr / en / zh).
// ============================================================
// Decides the active language from (in priority order):
//   1. ?lang= query parameter
//   2. localStorage('lang')
//   3. Default: 'fr' (the user is French-speaking, project lang)
//
// Once chosen, the matching i18n/<lang>.json is fetched. A `data-i18n="key"`
// attribute on any DOM element causes that element's textContent to be
// replaced with the translation. Attributes use `data-i18n-attr="key:val"`.
// ============================================================
(function () {
  'use strict';

  const SUPPORTED = ['fr', 'en', 'zh'];
  const DEFAULT = 'fr';

  let _dict = {};
  let _currentLang = DEFAULT;

  function pickLang() {
    // 1. Query string
    const params = new URLSearchParams(window.location.search);
    const fromQuery = params.get('lang');
    if (fromQuery && SUPPORTED.includes(fromQuery)) {
      try { localStorage.setItem('lang', fromQuery); } catch (e) {}
      return fromQuery;
    }
    // 2. localStorage
    try {
      const saved = localStorage.getItem('lang');
      if (saved && SUPPORTED.includes(saved)) return saved;
    } catch (e) {}
    // 3. Default
    return DEFAULT;
  }

  async function loadLang(lang) {
    const url = 'i18n/' + lang + '.json';
    const res = await fetch(url);
    if (!res.ok) throw new Error('Failed to load i18n: ' + url);
    return res.json();
  }

  // Replace {placeholder} occurrences with values from `vars`
  function interpolate(s, vars) {
    if (!vars) return s;
    return s.replace(/\{(\w+)\}/g, (_, k) =>
      Object.prototype.hasOwnProperty.call(vars, k) ? String(vars[k]) : '{' + k + '}'
    );
  }

  function t(key, vars) {
    const raw = _dict[key];
    if (raw === undefined) {
      // Don't throw — return the key itself so missing strings are visible
      // but the site keeps working.
      return key;
    }
    return interpolate(raw, vars);
  }

  // Apply translations to all elements with data-i18n attributes
  function applyTo(root) {
    root = root || document;
    root.querySelectorAll('[data-i18n]').forEach(el => {
      const key = el.getAttribute('data-i18n');
      el.textContent = t(key);
    });
    root.querySelectorAll('[data-i18n-attr]').forEach(el => {
      // Format: data-i18n-attr="title:key1,placeholder:key2"
      const spec = el.getAttribute('data-i18n-attr');
      for (const pair of spec.split(',')) {
        const [attr, key] = pair.split(':').map(s => s.trim());
        if (attr && key) el.setAttribute(attr, t(key));
      }
    });
  }

  async function init() {
    _currentLang = pickLang();
    document.documentElement.lang = _currentLang;
    try {
      _dict = await loadLang(_currentLang);
    } catch (e) {
      console.warn('[i18n] falling back to default', e);
      try {
        _dict = await loadLang(DEFAULT);
        _currentLang = DEFAULT;
      } catch (e2) {
        console.error('[i18n] failed to load any language', e2);
        _dict = {};
      }
    }
    applyTo();
    document.dispatchEvent(new CustomEvent('gengo-i18n-ready', {
      detail: { lang: _currentLang },
    }));
  }

  function currentLang() { return _currentLang; }

  function setLang(lang) {
    if (!SUPPORTED.includes(lang) || lang === _currentLang) return;
    try { localStorage.setItem('lang', lang); } catch (e) {}
    // Preserve the page but update the query string
    const url = new URL(window.location.href);
    url.searchParams.set('lang', lang);
    window.location.href = url.toString();
  }

  // Public API
  window.GengoI18n = {
    init,
    t,
    applyTo,
    currentLang,
    setLang,
    supported: SUPPORTED,
  };

  // Auto-init on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
