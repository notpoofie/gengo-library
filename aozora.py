#!/usr/bin/env python3
"""
Gengo Library — Téléchargeur Aozora Bunko
==========================================
Télécharge une œuvre depuis Aozora Bunko, la convertit en EPUB propre,
et la passe au pipeline d'ingestion (ingest.py).

Aozora Bunko sert ses textes en Shift-JIS avec un balisage maison
(ruby annotations entre parenthèses japonaises, références graphiques,
notes de bas de page). On nettoie tout ça avant de générer l'EPUB.

Usage:
    python aozora.py --preset starter
    # ou
    python aozora.py --url https://www.aozora.gr.jp/cards/000879/files/92_14545.html \\
        --id kumonoito --title-fr "Le Fil de l'araignée" --author-fr "Akutagawa Ryūnosuke" \\
        --level beginner
"""

import argparse
import io
import os
import re
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

# Windows consoles default to cp932 / cp1252 which can't encode every
# character we print. Force UTF-8 so emojis and accents work.
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, Exception):
        pass


# ============================================================
# Recommandations « starter » — les 5 livres pour démarrer
# ============================================================
# Chaque entrée est un dict avec :
#   url        : URL XHTML directe sur Aozora
#   id         : slug pour le book id
#   level      : beginner / intermediate / advanced
#   title_*    : titres traduits (à remplir par toi si tu veux affiner)
#   author_*   : auteur dans chaque langue (japonais transcrit)
#   summary_*  : résumé court dans chaque langue

STARTER_BOOKS = [
    {
        # Conte de Momotarō version Kusuyama Masao
        # https://www.aozora.gr.jp/cards/000329/card18376.html
        'url': 'https://www.aozora.gr.jp/cards/000329/files/18376_12100.html',
        'id': 'momotaro-kusuyama',
        'level': 'beginner',
        'title_ja': '桃太郎',
        'title_fr': 'Momotarō',
        'title_en': 'Momotarō',
        'title_zh': '桃太郎',
        'author_ja': '楠山正雄',
        'author_fr': 'Kusuyama Masao',
        'author_en': 'Kusuyama Masao',
        'author_zh': '楠山正雄',
        'summary_fr': "Le conte populaire le plus connu du Japon : un petit garçon né d'une pêche part combattre les démons de l'île d'Oni avec ses compagnons animaux.",
        'summary_en': "Japan's most beloved folk tale: a small boy born from a peach sets out with animal companions to defeat the demons of Onigashima.",
        'summary_zh': "日本最著名的民间故事：从桃中诞生的小男孩与他的动物伙伴们一起前往鬼岛打败恶魔。",
    },
    {
        # Le Fil de l'araignée
        # https://www.aozora.gr.jp/cards/000879/card92.html
        'url': 'https://www.aozora.gr.jp/cards/000879/files/92_14545.html',
        'id': 'kumo-no-ito',
        'level': 'beginner',
        'title_ja': '蜘蛛の糸',
        'title_fr': "Le Fil de l'araignée",
        'title_en': "The Spider's Thread",
        'title_zh': '蜘蛛之丝',
        'author_ja': '芥川龍之介',
        'author_fr': 'Akutagawa Ryūnosuke',
        'author_en': 'Ryūnosuke Akutagawa',
        'author_zh': '芥川龙之介',
        'summary_fr': "Bouddha offre une seconde chance à un brigand damné en enfer en lui tendant un fil d'araignée.",
        'summary_en': "The Buddha offers a damned thief a chance at salvation by lowering a spider's thread from paradise.",
        'summary_zh': "释迦牟尼向地狱中的恶人递下一根蜘蛛丝，给予他改过自新的机会。",
    },
    {
        # Le Restaurant aux nombreuses commandes — Miyazawa Kenji
        # https://www.aozora.gr.jp/cards/000081/card1927.html
        'url': 'https://www.aozora.gr.jp/cards/000081/files/1927_17906.html',
        'id': 'chumon-no-oi-ryoriten',
        'level': 'intermediate',
        'title_ja': '注文の多い料理店',
        'title_fr': 'Le Restaurant aux nombreuses commandes',
        'title_en': 'The Restaurant of Many Orders',
        'title_zh': '要求众多的餐厅',
        'author_ja': '宮沢賢治',
        'author_fr': 'Miyazawa Kenji',
        'author_en': 'Kenji Miyazawa',
        'author_zh': '宫泽贤治',
        'summary_fr': "Deux chasseurs perdus dans la montagne tombent sur un restaurant occidental étrange dont les exigences se font de plus en plus inquiétantes.",
        'summary_en': "Two hunters lost in the mountains stumble upon a strange Western-style restaurant whose demands grow ever more disquieting.",
        'summary_zh': "两个迷失在山中的猎人偶然发现一家奇怪的西式餐厅，其要求愈发令人不安。",
    },
    {
        # Cours, Melos ! — Dazai Osamu
        # https://www.aozora.gr.jp/cards/000035/card1567.html
        'url': 'https://www.aozora.gr.jp/cards/000035/files/1567_14913.html',
        'id': 'hashire-melos',
        'level': 'intermediate',
        'title_ja': '走れメロス',
        'title_fr': 'Cours, Melos !',
        'title_en': 'Run, Melos!',
        'title_zh': '奔跑吧，梅勒斯',
        'author_ja': '太宰治',
        'author_fr': 'Dazai Osamu',
        'author_en': 'Osamu Dazai',
        'author_zh': '太宰治',
        'summary_fr': "Melos doit traverser la campagne et revenir avant le coucher du soleil pour sauver la vie de son ami otage du tyran.",
        'summary_en': "Melos must race across the countryside and return before sunset to save his friend, held hostage by a tyrant.",
        'summary_zh': "梅勒斯必须穿越乡野，在日落之前归来，以救出被暴君扣为人质的朋友。",
    },
    {
        # Botchan — Natsume Sōseki
        # https://www.aozora.gr.jp/cards/000148/card752.html
        'url': 'https://www.aozora.gr.jp/cards/000148/files/752_14964.html',
        'id': 'botchan',
        'level': 'advanced',
        'title_ja': '坊っちゃん',
        'title_fr': 'Botchan',
        'title_en': 'Botchan',
        'title_zh': '哥儿',
        'author_ja': '夏目漱石',
        'author_fr': 'Natsume Sōseki',
        'author_en': 'Natsume Sōseki',
        'author_zh': '夏目漱石',
        'summary_fr': "Un jeune Tokyoïte impétueux part enseigner les mathématiques dans une école de campagne à Shikoku — et y croise des collègues plus retors les uns que les autres.",
        'summary_en': "A hot-headed young man from Tokyo takes a math-teaching post at a country school in Shikoku — and finds his colleagues more devious than expected.",
        'summary_zh': "一名出身东京的莽撞青年前往四国乡村学校任数学教师，却发现同事一个比一个狡猾。",
    },
]


# ============================================================
# Téléchargement et nettoyage
# ============================================================

def fetch_aozora(url: str) -> str:
    """Télécharge un fichier Aozora HTML, le décode depuis Shift-JIS,
    retourne du HTML UTF-8."""
    print(f"  Téléchargement : {url}")
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0 (gengo-library/1.0)'
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        raw = resp.read()
    # Aozora utilise Shift-JIS, parfois CP932 (sur-ensemble)
    for enc in ('cp932', 'shift_jis'):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    # Fallback brutal
    return raw.decode('cp932', errors='replace')


def extract_aozora_body(html: str) -> tuple[str, str]:
    """Extrait le titre et le contenu principal d'une page Aozora.
    Retourne (title, body_html).
    La structure Aozora typique :
       <div class="metadata">
          <h1 class="title">タイトル</h1>
          <h2 class="author">著者</h2>
       </div>
       <div class="main_text">
          ... contenu ...
       </div>
       <div class="bibliographical_information"> ... </div>
    """
    # Title
    m = re.search(r'<h1[^>]*class="title"[^>]*>(.*?)</h1>', html, re.DOTALL)
    title = re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ''
    # Main body
    m = re.search(
        r'<div[^>]*class="main_text"[^>]*>(.*?)</div>\s*(?:<div[^>]*class="(?:bibliographical_information|notation_notes)|<hr)',
        html, re.DOTALL
    )
    if m:
        body = m.group(1)
    else:
        # Fallback: look for the section between the first h1 and the
        # bibliography div
        body_match = re.search(
            r'</h2>(.*?)<div[^>]*class="bibliographical_information"',
            html, re.DOTALL,
        )
        body = body_match.group(1) if body_match else html
    return title, body


def clean_aozora_html(body: str) -> str:
    """Retire le balisage Aozora-specific et garde du XHTML propre :
       - <ruby><rb>漢字</rb><rp>（</rp><rt>ふりがな</rt><rp>）</rp></ruby>
         devient juste 漢字 (on regénère les lectures avec le tokenizer)
       - Notes <span class="notes">...</span> retirées
       - Gaiji (caractères encodés en image) traités au mieux
       - <br/> deviennent des sauts de ligne
       - <div class="jisage_X"> (indentation) retirés
    """
    text = body

    # Strip ruby annotations — keep only the base text (rb)
    # Pattern: <ruby><rb>X</rb><rp>(</rp><rt>Y</rt><rp>)</rp></ruby>
    text = re.sub(r'<rt[^>]*>.*?</rt>', '', text, flags=re.DOTALL)
    text = re.sub(r'<rp[^>]*>.*?</rp>', '', text, flags=re.DOTALL)
    text = re.sub(r'</?(ruby|rb)[^>]*>', '', text)

    # Aozora source files sometimes also include the furigana as
    # full-width parentheses after the kanji, like "漢字（かんじ）".
    # These are visible to readers but redundant for us — the tokenizer
    # regenerates the readings. Strip "（kana）" sequences when they
    # immediately follow a kanji character.
    # We allow full-width and half-width parentheses; readings are
    # hiragana/katakana only.
    text = re.sub(
        r'([\u4E00-\u9FFF\u3400-\u4DBF])[（(]['
        r'\u3040-\u309F\u30A0-\u30FFー]+[）)]',
        r'\1',
        text,
    )

    # Strip <span class="notes">...</span> — those are editor annotations
    # like 「※」 or character clarification
    text = re.sub(
        r'<span[^>]*class="notes"[^>]*>.*?</span>',
        '', text, flags=re.DOTALL,
    )

    # Aozora "gaiji" images: <img class="gaiji" src="..." alt="X"/>
    # Replace with the alt text (usually a description like "※[…]")
    text = re.sub(
        r'<img[^>]*class="gaiji"[^>]*alt="([^"]*)"[^>]*/?>',
        '', text,
    )

    # Strip jisage divs (indentation hints) but keep their content
    text = re.sub(r'<div[^>]*class="jisage_\d+"[^>]*>', '', text)
    text = re.sub(r'<div[^>]*class="chitsuki_\d+"[^>]*>', '', text)
    text = re.sub(r'<div[^>]*class="midashi"[^>]*>', '', text)
    # Closing divs: hard to match selectively, so we remove ALL bare </div>
    # at the end (they pair with the ones we removed above).
    text = re.sub(r'</div>', '', text)

    # Normalize <br/> styles
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)

    return text


def split_into_chapters(body: str) -> list[tuple[str, str]]:
    """Découpe le corps en chapitres si on détecte des <h3>/<h4> Aozora.
    Retourne une liste de (titre, contenu_xhtml). Si aucune subdivision
    n'est détectée, retourne un seul chapitre."""
    # Aozora wraps headers like:  <h3 class="o-midashi"><a class="midashi_anchor" id="midashi10">一</a></h3>
    parts = re.split(
        r'<h[3-5][^>]*>(.*?)</h[3-5]>',
        body, flags=re.DOTALL,
    )
    # parts alternates: preamble, title1, body1, title2, body2, ...
    if len(parts) <= 1:
        return [('', body.strip())]

    chapters = []
    # If there's content before the first heading, we may want to drop
    # it (often empty whitespace) or use it as a prologue.
    # Anything in parts[0] before the first heading title is dropped.
    for i in range(1, len(parts), 2):
        if i + 1 >= len(parts):
            break
        raw_title = parts[i]
        clean_title = re.sub(r'<[^>]+>', '', raw_title).strip()
        section_body = parts[i + 1].strip()
        if not section_body:
            continue
        chapters.append((clean_title, section_body))

    return chapters if chapters else [('', body.strip())]


# ============================================================
# Construction de l'EPUB
# ============================================================

CONTAINER_XML = '''<?xml version="1.0"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
'''

OPF_TEMPLATE = '''<?xml version="1.0"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">{identifier}</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:language>ja</dc:language>
  </metadata>
  <manifest>
{manifest_items}  </manifest>
  <spine>
{spine_items}  </spine>
</package>
'''

CHAPTER_TEMPLATE = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
  <head><title>{title}</title></head>
  <body>
    <h1>{title}</h1>
{paragraphs}
  </body>
</html>
'''


def xml_escape(s: str) -> str:
    return (s.replace('&', '&amp;')
             .replace('<', '&lt;')
             .replace('>', '&gt;'))


def paragraphs_to_xhtml(body: str) -> str:
    """Convert cleaned Aozora body text into <p>...</p> XHTML paragraphs."""
    # Split by remaining <br/> / newlines / </p>
    body = re.sub(r'</p>', '\n', body, flags=re.IGNORECASE)
    body = re.sub(r'<p[^>]*>', '', body, flags=re.IGNORECASE)
    body = re.sub(r'<[^>]+>', '', body)  # strip any remaining inline tags

    out = []
    for line in body.split('\n'):
        line = line.strip()
        # Drop indentation markers Aozora sometimes leaves as full-width spaces
        line = line.lstrip('\u3000 \t')
        if line:
            out.append(f'    <p>{xml_escape(line)}</p>')
    return '\n'.join(out)


def build_epub(out_path: Path, title: str, author: str, identifier: str,
               chapters: list[tuple[str, str]]):
    """Builds an EPUB from a list of (chapter_title, paragraphs_xhtml)."""
    chapter_files = []
    for i, (chap_title, chap_paragraphs) in enumerate(chapters, start=1):
        if not chap_title:
            chap_title = f'第{i}章'
        fname = f'ch{i:03d}.xhtml'
        chapter_files.append((fname, chap_title, chap_paragraphs))

    manifest_items = '\n'.join(
        f'    <item id="ch{i}" href="{fname}" media-type="application/xhtml+xml"/>'
        for i, (fname, _, _) in enumerate(chapter_files, start=1)
    )
    spine_items = '\n'.join(
        f'    <itemref idref="ch{i}"/>'
        for i in range(1, len(chapter_files) + 1)
    )

    opf = OPF_TEMPLATE.format(
        identifier=xml_escape(identifier),
        title=xml_escape(title),
        author=xml_escape(author),
        manifest_items=manifest_items + '\n',
        spine_items=spine_items + '\n',
    )

    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.writestr('mimetype', 'application/epub+zip',
                    compress_type=zipfile.ZIP_STORED)
        zf.writestr('META-INF/container.xml', CONTAINER_XML)
        zf.writestr('OEBPS/content.opf', opf)
        for fname, chap_title, paragraphs in chapter_files:
            chap_html = CHAPTER_TEMPLATE.format(
                title=xml_escape(chap_title),
                paragraphs=paragraphs,
            )
            zf.writestr(f'OEBPS/{fname}', chap_html)


# ============================================================
# Pipeline complet
# ============================================================

def process_one(book: dict, work_dir: Path, repo_root: Path):
    """Télécharge, nettoie, encode en EPUB, lance ingest.py, met à jour
    les traductions dans meta.json."""
    print(f"\n--- {book['title_ja']} ({book['id']}) ---")

    # 1. Download
    html = fetch_aozora(book['url'])

    # 2. Extract main body
    _, body = extract_aozora_body(html)
    if not body.strip():
        raise RuntimeError("Aucun contenu extrait de la page Aozora")
    print(f"  HTML brut : {len(body):,} caractères")

    # 3. Clean
    body = clean_aozora_html(body)
    print(f"  Après nettoyage : {len(body):,} caractères")

    # 4. Split into chapters
    chapters_raw = split_into_chapters(body)
    print(f"  Chapitres détectés : {len(chapters_raw)}")

    # 5. Convert each chapter body to <p> paragraphs
    chapters = [
        (title, paragraphs_to_xhtml(content))
        for (title, content) in chapters_raw
    ]
    # Drop chapters that ended up empty after cleaning
    chapters = [(t, c) for (t, c) in chapters if c.strip()]
    if not chapters:
        raise RuntimeError("Aucun chapitre non vide après nettoyage")

    # 6. Build EPUB
    epub_path = work_dir / f"{book['id']}.epub"
    build_epub(
        epub_path,
        title=book['title_ja'],
        author=book['author_ja'],
        identifier=f"aozora-{book['id']}",
        chapters=chapters,
    )
    print(f"  EPUB construit : {epub_path}")

    # 7. Run ingest.py
    print("  Lancement du pipeline d'ingestion...")
    # Force UTF-8 in the subprocess too, otherwise on Windows the child
    # process's stdout may use cp932/cp1252 and crash on the first emoji
    # or accented character it tries to print.
    env = dict(os.environ, PYTHONIOENCODING='utf-8', PYTHONUTF8='1')
    result = subprocess.run(
        [sys.executable, str(repo_root / 'ingest.py'),
         str(epub_path),
         '--id', book['id'],
         '--level', book['level'],
         '--out', str(repo_root)],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
        env=env,
    )
    # Always show the subprocess output so we see what ingest.py reported
    if result.stdout:
        for line in result.stdout.splitlines():
            print(f"    {line}")
    if result.returncode != 0:
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        raise RuntimeError("ingest.py a échoué")

    # 8. Fill in the translations in meta.json (now under public/)
    meta_path = repo_root / 'public' / 'books' / book['id'] / 'meta.json'
    import json
    meta = json.loads(meta_path.read_text(encoding='utf-8'))
    meta['title']['fr'] = book['title_fr']
    meta['title']['en'] = book['title_en']
    meta['title']['zh'] = book['title_zh']
    meta['author']['fr'] = book['author_fr']
    meta['author']['en'] = book['author_en']
    meta['author']['zh'] = book['author_zh']
    meta['summary']['fr'] = book['summary_fr']
    meta['summary']['en'] = book['summary_en']
    meta['summary']['zh'] = book['summary_zh']
    meta_path.write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    # 9. Also update the catalog entry with the new translations
    catalog_path = repo_root / 'public' / 'catalog.json'
    catalog = json.loads(catalog_path.read_text(encoding='utf-8'))
    for entry in catalog['books']:
        if entry['id'] == book['id']:
            entry['title'] = meta['title']
            entry['author'] = meta['author']
            entry['summary'] = meta['summary']
    catalog_path.write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    print(f"  [OK] Métadonnées trilingues écrites pour {book['id']}")


# ============================================================
# Entry point
# ============================================================

def main():
    ap = argparse.ArgumentParser(
        description="Télécharge un livre Aozora Bunko et l'ingère dans la bibliothèque Gengo."
    )
    ap.add_argument(
        '--preset',
        choices=['starter'],
        help="'starter' = télécharge les 5 livres recommandés en une seule commande",
    )
    ap.add_argument('--url', help="URL XHTML directe sur aozora.gr.jp")
    ap.add_argument('--id', help="Slug du livre (obligatoire si --url)")
    ap.add_argument('--level', default='intermediate',
                    choices=['beginner', 'intermediate', 'advanced'])
    ap.add_argument('--title-fr')
    ap.add_argument('--title-en')
    ap.add_argument('--title-zh')
    ap.add_argument('--author-fr')
    args = ap.parse_args()

    repo_root = Path(__file__).resolve().parent
    work_dir = repo_root / '.epub-cache'
    work_dir.mkdir(exist_ok=True)

    if args.preset == 'starter':
        for book in STARTER_BOOKS:
            try:
                process_one(book, work_dir, repo_root)
            except Exception as e:
                print(f"  [ECHEC] Échec pour {book['id']}: {e}", file=sys.stderr)
                import traceback
                traceback.print_exc()
        print(f"\nTerminé. Vérifie les résultats dans {repo_root / 'public' / 'books'}/")
        return 0

    if args.url and args.id:
        # Custom one-shot
        book = {
            'url': args.url,
            'id': args.id,
            'level': args.level,
            'title_ja': args.id,
            'author_ja': '',
            'title_fr': args.title_fr or args.id,
            'title_en': args.title_en or args.id,
            'title_zh': args.title_zh or args.id,
            'author_fr': args.author_fr or '',
            'author_en': args.author_fr or '',
            'author_zh': '',
            'summary_fr': '', 'summary_en': '', 'summary_zh': '',
        }
        process_one(book, work_dir, repo_root)
        return 0

    ap.print_help()
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
