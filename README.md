# Gengo Library

La bibliothèque publique de littérature japonaise classique pour Gengo.

Ce dépôt contient deux choses :

- Un **pipeline d'ingestion Python** (`ingest.py`, `aozora.py`) qui télécharge des textes du domaine public depuis Aozora Bunko, les tokenise, et produit du JSON prêt à servir.
- Un **site web statique** (dans `public/`) qui sert ces livres avec un lecteur interactif mot-à-mot, en trois langues (français, anglais, mandarin).

## Structure du dépôt

```
gengo-library/
├── ingest.py              ← Pipeline EPUB → JSON tokenisé
├── aozora.py              ← Téléchargeur Aozora Bunko
├── requirements.txt
├── DEPLOY.md              ← Guide déploiement Cloudflare
├── README.md              ← Ce fichier
└── public/                ← Le site web (servi tel quel par Cloudflare)
    ├── index.html         ← Page d'accueil avec catalogue
    ├── book.html          ← Page d'un livre (résumé + table des matières)
    ├── read.html          ← Lecteur de chapitre
    ├── catalog.json       ← Index global des livres
    ├── books/             ← Dossier par livre
    │   └── <id>/
    │       ├── meta.json
    │       ├── chapter-001.json
    │       └── ...
    ├── css/
    │   └── site.css
    ├── js/
    │   ├── i18n.js        ← Système trilingue
    │   ├── catalog.js     ← Logique de la page d'accueil
    │   ├── book.js        ← Logique de la page livre
    │   ├── read.js        ← Logique du lecteur
    │   └── reader.js      ← Rendu mot-à-mot et popups
    └── i18n/
        ├── fr.json
        ├── en.json
        └── zh.json
```

## Installation (cross-platform : Windows, Mac, Linux)

```bash
git clone https://github.com/notpoofie/gengo-library.git
cd gengo-library
pip install -r requirements.txt
# Premier lancement : télécharge ~72 Mo de dictionnaire japonais
```

## Utilisation

### Démarrage rapide : importer les 5 livres recommandés

```bash
python aozora.py --preset starter
```

Télécharge et ingère les 5 livres recommandés. Les fichiers JSON apparaissent dans `public/books/`.

### Tester le site localement

```bash
cd public
python3 -m http.server 8000
# Ouvre http://localhost:8000 dans ton navigateur
```

### Ajouter un livre Aozora Bunko

```bash
python aozora.py \
    --url https://www.aozora.gr.jp/cards/000879/files/92_14545.html \
    --id kumo-no-ito \
    --level beginner \
    --title-fr "Le Fil de l'araignée" \
    --author-fr "Akutagawa Ryūnosuke"
```

### Ajouter ton propre EPUB

```bash
python ingest.py /chemin/vers/livre.epub --id mon-livre --level intermediate
```

Le pipeline crée un dossier `public/books/mon-livre/` avec le contenu tokenisé. Les traductions des métadonnées (titre, auteur, résumé dans chaque langue) sont laissées vides — tu dois les compléter manuellement dans `public/books/mon-livre/meta.json`.

### Déployer en ligne sur Cloudflare Pages

Voir [DEPLOY.md](DEPLOY.md).

## Sources autorisées

⚠️ **Seuls les textes du domaine public** peuvent être hébergés publiquement.

| Source | Statut | Notes |
|---|---|---|
| Aozora Bunko (auteur † avant 1955) | ✅ Domaine public | Source principale du projet |
| Wikipédia japonais | ✅ Creative Commons | Articles utilisables avec attribution |
| Vos propres écrits | ✅ Selon votre choix | À vous de mettre une licence claire |
| Auteurs récents (Mishima, Kawabata, Murakami…) | ❌ Sous copyright | Usage personnel uniquement, pas d'hébergement |

Règle simple : **l'auteur doit être mort depuis plus de 70 ans** pour que le texte soit du domaine public au Japon.

## Format JSON

### `catalog.json` (racine)

```json
{
  "version": 1,
  "updated_at": "2026-05-14T...",
  "books": [
    {
      "id": "kumo-no-ito",
      "title": { "ja": "蜘蛛の糸", "fr": "Le Fil de l'araignée", "en": "The Spider's Thread", "zh": "蜘蛛之丝" },
      "author": { "ja": "芥川龍之介", "fr": "Akutagawa Ryūnosuke", ... },
      "summary": { "fr": "...", "en": "...", "zh": "..." },
      "level": "beginner",
      "license": "public_domain",
      "chapters_count": 2,
      "tokens_count": 1808,
      "path": "books/kumo-no-ito/meta.json"
    }
  ]
}
```

### `books/<id>/chapter-NNN.json`

```json
{
  "id": "ch1",
  "index": 1,
  "title": "一",
  "paragraphs": [
    {
      "tokens": [
        { "surface": "ある", "reading": "ある", "lemma": "ある", "pos": "連体詞" },
        { "surface": "日", "reading": "ひ", "lemma": "日", "pos": "名詞" }
      ]
    }
  ]
}
```

- `surface` : le mot tel qu'écrit dans le texte
- `reading` : la lecture en hiragana
- `lemma` : la forme du dictionnaire (envoyée à Jisho au clic)
- `pos` : la classe grammaticale en japonais (traduite côté client)

## Architecture du site

Le site est **100% statique** — pas de serveur, pas de base de données. Tout est servi tel quel par Cloudflare Pages.

- `index.html` charge `catalog.json` pour afficher la grille de livres
- `book.html?id=X` charge `books/X/meta.json` pour afficher la page d'un livre
- `read.html?id=X&ch=N` charge `books/X/chapter-NNN.json` et le rend mot-à-mot

Le système i18n cherche `?lang=` dans l'URL puis dans localStorage, sinon utilise le français par défaut. Le choix est préservé entre les pages.

## Pourquoi pas de tokenizer côté serveur web ?

Les livres sont **pré-tokenisés** par le pipeline Python avant publication. Le site web n'a pas besoin de tokenizer JavaScript — il sert juste du JSON déjà préparé. C'est plus rapide à charger (~10 Ko par chapitre) et tout marche hors-ligne après le premier chargement.

L'app cliente Gengo (séparée de ce dépôt) embarque kuromoji.js pour tokeniser les EPUB importés par l'utilisateur en local, mais pour les livres du catalogue elle se contente de charger les JSON depuis cette bibliothèque.
