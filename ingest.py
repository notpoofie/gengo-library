#!/usr/bin/env python3
"""
Gengo Library — Pipeline d'ingestion
=====================================
Convertit un fichier .epub japonais en JSON tokenisé prêt pour la
bibliothèque en ligne.

Usage:
    python ingest.py chemin/vers/livre.epub
    python ingest.py chemin/vers/livre.epub --id kokoro-soseki --level advanced

Le pipeline:
  1. Décompresse l'EPUB (un EPUB est un ZIP)
  2. Lit le manifeste OPF pour trouver les chapitres et métadonnées
  3. Pour chaque chapitre, extrait le texte brut
  4. Tokenise chaque paragraphe avec SudachiPy
  5. Convertit les lectures de katakana en hiragana
  6. Écrit un dossier books/<id>/ avec:
       - meta.json       : titre, auteur, etc.
       - chapter-XXX.json: un fichier par chapitre tokenisé
  7. Met à jour catalog.json avec ce livre

Les classes grammaticales restent en japonais dans le JSON; la traduction
fr/en/zh se fait côté client via le système i18n.
"""

import argparse
import hashlib
import json
import re
import sys
import unicodedata
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.etree import ElementTree as ET

# Windows consoles default to cp932 (when Japanese locale) or cp1252 (French),
# neither of which can encode every character we print. Reconfiguring stdout
# to UTF-8 fixes this — print() works, the file system isn't affected.
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, Exception):
        pass

from sudachipy import dictionary, tokenizer


# ============================================================
# Helpers
# ============================================================

# EPUB XML namespaces
NS = {
    'opf': 'http://www.idpf.org/2007/opf',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'container': 'urn:oasis:names:tc:opendocument:xmlns:container',
}


def katakana_to_hiragana(s: str) -> str:
    """Décalage Unicode standard : katakana → hiragana (-0x60).
    Les caractères qui ne sont pas du katakana sont laissés intacts."""
    out = []
    for ch in s:
        code = ord(ch)
        # Katakana block (excluding the half-width forms)
        if 0x30A1 <= code <= 0x30F6:
            out.append(chr(code - 0x60))
        else:
            out.append(ch)
    return ''.join(out)


def slugify(text: str) -> str:
    """Génère un id court basé sur le titre. Conserve les caractères
    japonais (l'id est l'URL du livre dans le catalogue)."""
    # Take first ~30 chars, drop punctuation, lowercase ascii letters
    cleaned = re.sub(r'[^\w\u3040-\u30FF\u4E00-\u9FFF\-]', '', text)[:30]
    if not cleaned:
        cleaned = 'book'
    return cleaned.lower()


def strip_html_to_paragraphs(xhtml: str) -> list[str]:
    """Convertit un chapitre XHTML en liste de paragraphes texte.
    Préserve les sauts de paragraphe (chaque <p>, <h*>, <br> est un break)."""
    # Parse as XML if possible, fall back to regex stripping
    text = xhtml
    # Strip the document head entirely (we don't want <title>, <meta>, etc.)
    text = re.sub(r'<head[^>]*>.*?</head>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Remove style/script
    text = re.sub(r'<(style|script)[^>]*>.*?</\1>', '', text, flags=re.DOTALL | re.IGNORECASE)
    # Add explicit paragraph breaks for block elements before stripping
    text = re.sub(r'<(p|h[1-6]|div|li|blockquote|br/?)[^>]*>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'</(p|h[1-6]|div|li|blockquote)>', '\n', text, flags=re.IGNORECASE)
    # Strip ruby tags but keep base text (drop the furigana, since we regenerate it)
    text = re.sub(r'<rt[^>]*>.*?</rt>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'<rp[^>]*>.*?</rp>', '', text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r'</?(ruby|rb)[^>]*>', '', text, flags=re.IGNORECASE)
    # Strip all remaining tags
    text = re.sub(r'<[^>]+>', '', text)
    # HTML entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'").replace('&nbsp;', ' ')
    # Aozora-style fallback: kanji followed by hiragana in parentheses,
    # like "御釈迦様（おしゃかさま）". Strip the parenthetical reading
    # so the tokenizer doesn't see it as separate words.
    text = re.sub(
        r'([\u4E00-\u9FFF\u3400-\u4DBF])[（(]['
        r'\u3040-\u309F\u30A0-\u30FFー]+[）)]',
        r'\1',
        text,
    )
    # Normalize whitespace per paragraph
    paragraphs = []
    for line in text.split('\n'):
        line = line.strip()
        # Collapse internal whitespace but keep ideographic full-width spaces
        line = re.sub(r'[ \t]+', ' ', line)
        if line:
            paragraphs.append(line)
    return paragraphs


# ============================================================
# EPUB reader
# ============================================================

def read_epub(epub_path: Path) -> dict:
    """Ouvre un EPUB, retourne {meta, chapters} où chapters est la liste
    ordonnée de tuples (chapter_id, title, list_of_paragraphs)."""
    with zipfile.ZipFile(epub_path, 'r') as zf:
        names = zf.namelist()

        # 1. Find the OPF via META-INF/container.xml
        container_path = 'META-INF/container.xml'
        if container_path not in names:
            raise ValueError(f"EPUB invalide: {container_path} manquant")
        container = ET.fromstring(zf.read(container_path))
        rootfile_el = container.find('.//{urn:oasis:names:tc:opendocument:xmlns:container}rootfile')
        if rootfile_el is None:
            raise ValueError("container.xml: rootfile introuvable")
        opf_path = rootfile_el.get('full-path')
        if not opf_path:
            raise ValueError("container.xml: full-path manquant")

        # 2. Parse the OPF
        opf = ET.fromstring(zf.read(opf_path))
        opf_dir = '/'.join(opf_path.split('/')[:-1])

        # 3. Metadata (Dublin Core)
        def dc(tag: str) -> str:
            el = opf.find(f'.//{{{NS["dc"]}}}{tag}')
            return (el.text or '').strip() if el is not None else ''

        meta = {
            'title_ja': dc('title') or epub_path.stem,
            'author_ja': dc('creator'),
            'language': dc('language') or 'ja',
            'identifier': dc('identifier'),
        }

        # 4. Manifest: id → relative href
        manifest = {}
        for item in opf.findall(f'.//{{{NS["opf"]}}}item'):
            item_id = item.get('id')
            href = item.get('href')
            media_type = item.get('media-type', '')
            if item_id and href:
                manifest[item_id] = {'href': href, 'media_type': media_type}

        # 5. Spine: ordered list of chapter idrefs
        spine_refs = []
        for itemref in opf.findall(f'.//{{{NS["opf"]}}}itemref'):
            idref = itemref.get('idref')
            if idref:
                spine_refs.append(idref)

        # 6. Extract each chapter
        chapters = []
        for idref in spine_refs:
            m = manifest.get(idref)
            if not m:
                continue
            if 'html' not in m['media_type'] and 'xml' not in m['media_type']:
                continue
            chapter_path = f"{opf_dir}/{m['href']}" if opf_dir else m['href']
            # Some EPUBs use no opf_dir
            if chapter_path not in names and m['href'] in names:
                chapter_path = m['href']
            if chapter_path not in names:
                print(f"  ! chapitre manquant dans le ZIP: {chapter_path}", file=sys.stderr)
                continue
            try:
                xhtml = zf.read(chapter_path).decode('utf-8', errors='replace')
            except Exception as e:
                print(f"  ! erreur lecture {chapter_path}: {e}", file=sys.stderr)
                continue
            paragraphs = strip_html_to_paragraphs(xhtml)
            if not paragraphs:
                continue
            # Detect a heading on the first paragraph: short, no terminal
            # punctuation, no full-width ideographic comma. If it looks like
            # a heading, use it as the title AND remove it from the body so
            # the chapter doesn't display its title twice.
            first = paragraphs[0]
            looks_like_heading = (
                len(first) <= 40
                and not first.endswith(('。', '.', '！', '？', '!', '?'))
                and '、' not in first
            )
            if looks_like_heading:
                title = first
                paragraphs = paragraphs[1:]
            else:
                title = f"Chapitre {len(chapters) + 1}"
            if not paragraphs:
                # Heading-only chapter (e.g. cover page) — skip
                continue
            chapters.append((idref, title, paragraphs))

        return {'meta': meta, 'chapters': chapters}


# ============================================================
# Tokenizer
# ============================================================

class JapaneseTokenizer:
    """Wrapper SudachiPy. Mode C = découpage maximal en mots
    composés (plus naturel pour la lecture)."""

    def __init__(self):
        self.tok = dictionary.Dictionary(dict='core').create()
        self.mode = tokenizer.Tokenizer.SplitMode.C

    def tokenize_paragraph(self, text: str) -> list[dict]:
        out = []
        for m in self.tok.tokenize(text, self.mode):
            surface = m.surface()
            reading_kata = m.reading_form()
            # For pure-kana surfaces, the "reading" is sometimes the surface
            # itself; that's fine. For punctuation/symbols, reading == surface.
            reading_hira = katakana_to_hiragana(reading_kata) if reading_kata else surface
            lemma = m.dictionary_form() or surface
            pos = m.part_of_speech()[0]  # first level only (名詞, 動詞, etc.)
            out.append({
                'surface': surface,
                'reading': reading_hira,
                'lemma': lemma,
                'pos': pos,
            })
        return out


# ============================================================
# Pipeline
# ============================================================

def process_book(
    epub_path: Path,
    out_root: Path,
    book_id: str | None = None,
    level: str = 'intermediate',
    license_tag: str = 'public_domain',
) -> dict:
    """Pipeline complet pour un livre. Retourne l'entrée de catalogue
    à insérer dans catalog.json."""
    print(f"\n=== {epub_path.name} ===")
    print("Lecture de l'EPUB...")
    data = read_epub(epub_path)
    meta = data['meta']
    chapters = data['chapters']

    if not chapters:
        raise RuntimeError("Aucun chapitre extrait de l'EPUB")

    # Pick the id
    if not book_id:
        book_id = slugify(meta['title_ja'] or epub_path.stem)
    print(f"  ID du livre : {book_id}")
    print(f"  Titre japonais : {meta['title_ja']}")
    print(f"  Auteur : {meta['author_ja']}")
    print(f"  Chapitres : {len(chapters)}")

    # Prepare output dir
    book_dir = out_root / 'books' / book_id
    book_dir.mkdir(parents=True, exist_ok=True)

    # Tokenize chapter by chapter
    print("Tokenisation...")
    tok = JapaneseTokenizer()
    total_tokens = 0
    chapter_index = []
    for i, (chap_id, chap_title, paragraphs) in enumerate(chapters):
        chap_filename = f'chapter-{i + 1:03d}.json'
        tokenized_paragraphs = []
        for para in paragraphs:
            tokens = tok.tokenize_paragraph(para)
            if tokens:
                tokenized_paragraphs.append({'tokens': tokens})
                total_tokens += len(tokens)
        chap_data = {
            'id': chap_id,
            'index': i + 1,
            'title': chap_title,
            'paragraphs': tokenized_paragraphs,
        }
        (book_dir / chap_filename).write_text(
            json.dumps(chap_data, ensure_ascii=False, separators=(',', ':')),
            encoding='utf-8',
        )
        chapter_index.append({
            'index': i + 1,
            'title': chap_title,
            'file': chap_filename,
            'paragraphs_count': len(tokenized_paragraphs),
        })
        if (i + 1) % 10 == 0 or i == len(chapters) - 1:
            print(f"  ... chapitre {i + 1}/{len(chapters)}")

    # Write the book's manifest (meta.json)
    # Translations en/zh are left empty here — they're filled in manually
    # or via a separate translation pass.
    book_meta = {
        'id': book_id,
        'title': {
            'ja': meta['title_ja'],
            'fr': '',
            'en': '',
            'zh': '',
        },
        'author': {
            'ja': meta['author_ja'],
            'fr': meta['author_ja'],   # Default to JA for authors
            'en': meta['author_ja'],
            'zh': meta['author_ja'],
        },
        'summary': {
            'fr': '',
            'en': '',
            'zh': '',
        },
        'language': meta['language'],
        'level': level,
        'license': license_tag,
        'identifier': meta['identifier'],
        'chapters_count': len(chapter_index),
        'tokens_count': total_tokens,
        'ingested_at': datetime.now(timezone.utc).isoformat(),
        'chapters': chapter_index,
    }
    (book_dir / 'meta.json').write_text(
        json.dumps(book_meta, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    print(f"  [OK] {total_tokens:,} tokens écrits dans {book_dir.relative_to(out_root)}")

    # Catalog entry (smaller version of book_meta for the index)
    catalog_entry = {
        'id': book_id,
        'title': book_meta['title'],
        'author': book_meta['author'],
        'summary': book_meta['summary'],
        'level': level,
        'license': license_tag,
        'language': meta['language'],
        'chapters_count': len(chapter_index),
        'tokens_count': total_tokens,
        'path': f'books/{book_id}/meta.json',
    }
    return catalog_entry


def update_catalog(out_root: Path, entry: dict):
    """Add or replace a book entry in catalog.json."""
    catalog_path = out_root / 'catalog.json'
    if catalog_path.exists():
        catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    else:
        catalog = {
            'version': 1,
            'updated_at': '',
            'books': [],
        }

    # Remove any existing entry with the same id, then append
    catalog['books'] = [b for b in catalog['books'] if b['id'] != entry['id']]
    catalog['books'].append(entry)
    catalog['books'].sort(key=lambda b: b['id'])
    catalog['updated_at'] = datetime.now(timezone.utc).isoformat()

    catalog_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    print(f"  [OK] catalog.json mis à jour ({len(catalog['books'])} livre(s) au total)")


# ============================================================
# Entry point
# ============================================================

def main():
    ap = argparse.ArgumentParser(
        description="Ingère un EPUB japonais dans la bibliothèque Gengo."
    )
    ap.add_argument('epub', type=Path, help='Chemin vers le fichier .epub')
    ap.add_argument('--id', help='ID du livre (sinon dérivé du titre)')
    ap.add_argument(
        '--level',
        choices=['beginner', 'intermediate', 'advanced'],
        default='intermediate',
        help='Niveau de difficulté indicatif',
    )
    ap.add_argument(
        '--license',
        default='public_domain',
        help='Licence (public_domain, cc_by, original, etc.)',
    )
    ap.add_argument(
        '--out',
        type=Path,
        default=Path(__file__).resolve().parent,
        help='Dossier racine de la bibliothèque (par défaut : ce dossier)',
    )
    args = ap.parse_args()

    if not args.epub.exists():
        print(f"Fichier introuvable : {args.epub}", file=sys.stderr)
        return 1

    try:
        entry = process_book(
            args.epub,
            args.out,
            book_id=args.id,
            level=args.level,
            license_tag=args.license,
        )
        update_catalog(args.out, entry)
    except Exception as e:
        print(f"\nÉCHEC : {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

    print("\nTerminé. Pense à compléter les traductions des titres/résumés ")
    print(f"dans books/{entry['id']}/meta.json avant de publier.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
