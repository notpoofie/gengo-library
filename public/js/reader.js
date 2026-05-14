// ============================================================
// reader.js — Render tokenized chapters as interactive HTML and show
// word popups on click. Used by the library site (and conceptually
// shared with the app's EPUB reader).
// ============================================================
(function () {
  'use strict';

  const HAS_KANJI = /[\u4E00-\u9FFF\u3400-\u4DBF]/;
  const KANA_OR_KANJI = /[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\u3400-\u4DBF]/;

  // Render an array of {tokens:[...]} paragraphs into `container`.
  // Each Japanese word becomes a clickable <span class="word"> with
  // a <ruby> showing furigana that the user can toggle on/off.
  function renderParagraphs(container, paragraphs) {
    const frag = document.createDocumentFragment();
    for (const para of paragraphs) {
      const p = document.createElement('p');
      for (const tok of para.tokens) {
        if (!tok.surface) continue;
        const isJp = KANA_OR_KANJI.test(tok.surface);
        if (isJp) {
          const span = document.createElement('span');
          span.className = 'word';
          span.dataset.lemma = tok.lemma || tok.surface;
          span.dataset.reading = tok.reading || '';
          span.dataset.pos = tok.pos || '';
          if (HAS_KANJI.test(tok.surface) && tok.reading &&
              tok.reading !== tok.surface) {
            const ruby = document.createElement('ruby');
            ruby.appendChild(document.createTextNode(tok.surface));
            const rt = document.createElement('rt');
            rt.textContent = tok.reading;
            ruby.appendChild(rt);
            span.appendChild(ruby);
          } else {
            span.textContent = tok.surface;
          }
          p.appendChild(span);
        } else {
          p.appendChild(document.createTextNode(tok.surface));
        }
      }
      frag.appendChild(p);
    }
    container.innerHTML = '';
    container.appendChild(frag);
  }

  // ---------- furigana toggle ----------
  function getFuriganaOn() {
    try { return localStorage.getItem('furigana') === '1'; }
    catch (e) { return false; }
  }
  function setFuriganaOn(on) {
    try { localStorage.setItem('furigana', on ? '1' : '0'); } catch (e) {}
    document.body.classList.toggle('furigana-on', on);
  }

  // ---------- word popup ----------
  let _popupBackdrop = null;
  function closePopup() {
    if (_popupBackdrop) {
      _popupBackdrop.remove();
      _popupBackdrop = null;
    }
    document.removeEventListener('keydown', onPopupKey);
  }
  function onPopupKey(e) {
    if (e.key === 'Escape') closePopup();
  }

  function showPopup(info, anchorEl) {
    closePopup();
    const t = (window.GengoI18n && window.GengoI18n.t) || (s => s);

    const backdrop = document.createElement('div');
    backdrop.className = 'popup-backdrop';
    backdrop.addEventListener('click', e => {
      if (e.target === backdrop) closePopup();
    });
    _popupBackdrop = backdrop;

    const pop = document.createElement('div');
    pop.className = 'word-popup';
    pop.setAttribute('role', 'dialog');

    const close = document.createElement('button');
    close.type = 'button';
    close.className = 'word-popup-close';
    close.setAttribute('aria-label', t('popup.close'));
    close.textContent = '✕';
    close.addEventListener('click', closePopup);
    pop.appendChild(close);

    // Surface with ruby
    const surfaceWrap = document.createElement('div');
    surfaceWrap.className = 'word-popup-surface';
    if (info.reading && info.reading !== info.surface && HAS_KANJI.test(info.surface)) {
      const ruby = document.createElement('ruby');
      ruby.appendChild(document.createTextNode(info.surface));
      const rt = document.createElement('rt');
      rt.textContent = info.reading;
      ruby.appendChild(rt);
      surfaceWrap.appendChild(ruby);
    } else {
      surfaceWrap.textContent = info.surface;
    }
    pop.appendChild(surfaceWrap);

    // Separate reading line (when surface has no kanji)
    if (info.reading && info.reading !== info.surface && !HAS_KANJI.test(info.surface)) {
      const r = document.createElement('div');
      r.className = 'word-popup-reading';
      r.textContent = info.reading;
      pop.appendChild(r);
    }

    // Metadata: lemma + POS
    const meta = document.createElement('dl');
    meta.className = 'word-popup-meta';
    if (info.lemma && info.lemma !== info.surface) {
      const dt = document.createElement('dt');
      dt.textContent = t('popup.dictionary_form');
      const dd = document.createElement('dd');
      dd.className = 'word-popup-lemma';
      dd.textContent = info.lemma;
      meta.appendChild(dt);
      meta.appendChild(dd);
    }
    if (info.pos) {
      const dt = document.createElement('dt');
      dt.textContent = t('popup.class');
      const dd = document.createElement('dd');
      // Translate POS via i18n if available
      const localized = t('pos.' + info.pos);
      dd.textContent = (localized !== 'pos.' + info.pos)
        ? localized + ' · ' + info.pos
        : info.pos;
      meta.appendChild(dt);
      meta.appendChild(dd);
    }
    if (meta.children.length) pop.appendChild(meta);

    // Jisho link
    const actions = document.createElement('div');
    actions.className = 'word-popup-actions';
    const link = document.createElement('a');
    link.href = 'https://jisho.org/search/' + encodeURIComponent(info.lemma);
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.className = 'word-popup-jisho';
    link.textContent = t('popup.see_on_jisho');
    actions.appendChild(link);
    pop.appendChild(actions);

    backdrop.appendChild(pop);
    document.body.appendChild(backdrop);
    positionNear(pop, anchorEl);
    document.addEventListener('keydown', onPopupKey);
  }

  function positionNear(pop, anchor) {
    requestAnimationFrame(() => {
      const margin = 12;
      const rect = anchor.getBoundingClientRect();
      const pw = pop.offsetWidth;
      const ph = pop.offsetHeight;
      const vw = window.innerWidth;
      const vh = window.innerHeight;
      let left = rect.left + rect.width / 2 - pw / 2;
      if (left < margin) left = margin;
      if (left + pw > vw - margin) left = vw - margin - pw;
      let top;
      if (vh - rect.bottom >= ph + margin) top = rect.bottom + margin;
      else if (rect.top >= ph + margin) top = rect.top - ph - margin;
      else top = Math.max(margin, vh - ph - margin);
      pop.style.left = left + 'px';
      pop.style.top = top + 'px';
    });
  }

  // ---------- click delegation ----------
  function bindReaderClicks(container) {
    container.addEventListener('click', e => {
      const word = e.target.closest('.word');
      if (!word) return;
      showPopup({
        surface: word.textContent.trim(),
        lemma: word.dataset.lemma || word.textContent.trim(),
        reading: word.dataset.reading || '',
        pos: word.dataset.pos || '',
      }, word);
    });
  }

  // Public API
  window.GengoReader = {
    renderParagraphs,
    bindReaderClicks,
    getFuriganaOn,
    setFuriganaOn,
    closePopup,
  };

  // Apply saved furigana state on body when DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => setFuriganaOn(getFuriganaOn()));
  } else {
    setFuriganaOn(getFuriganaOn());
  }
})();
