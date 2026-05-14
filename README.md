# Gengo Library

La bibliothèque publique de livres japonais pour Gengo.

Ce dépôt contient :
- Le **pipeline d'ingestion** : un script Python qui prend un .epub japonais et produit du JSON tokenisé prêt à être servi en ligne.
- Les **livres déjà traités** (dossier `books/`) et leur **catalogue** (`catalog.json`).
- (Plus tard) le site web qui sert ces livres.

## Installation (Windows / Mac / Linux)

Tu as juste besoin de Python 3.10+. Aucune dépendance native, aucun compilateur, rien à installer en dehors de pip.

```bash
# 1. Cloner le dépôt
git clone https://github.com/notpoofie/gengo-library.git
cd gengo-library

# 2. Installer les dépendances Python
pip install -r requirements.txt
```

C'est tout. La première installation télécharge ~72 Mo (le dictionnaire japonais SudachiDict) mais ne demande aucun compilateur.

## Utilisation

```bash
# Ingérer un livre EPUB
python ingest.py chemin/vers/kokoro.epub --id kokoro-soseki --level advanced

# Le script crée :
#   books/kokoro-soseki/meta.json           ← métadonnées du livre
#   books/kokoro-soseki/chapter-001.json    ← un fichier par chapitre, tokenisé
#   books/kokoro-soseki/chapter-002.json
#   ...
#   catalog.json                            ← index global mis à jour
```

### Options

| Option | Description | Défaut |
|---|---|---|
| `--id` | Identifiant du livre (slug URL). | dérivé du titre |
| `--level` | `beginner`, `intermediate`, `advanced` | `intermediate` |
| `--license` | `public_domain`, `cc_by`, `original`... | `public_domain` |
| `--out` | Dossier racine de la bibliothèque | dossier du script |

### Après l'ingestion

Le script laisse les **traductions de titres et résumés vides** (français, anglais, mandarin). Tu dois les remplir manuellement dans `books/<id>/meta.json` avant de publier le livre. C'est une étape volontairement séparée pour garder le contrôle de la qualité éditoriale.

## Format des fichiers générés

### `catalog.json`

L'index principal de la bibliothèque. Une seule ressource à charger côté client pour découvrir tous les livres disponibles.

```json
{
  "version": 1,
  "updated_at": "2026-05-13T...",
  "books": [
    {
      "id": "kokoro-soseki",
      "title": { "ja": "こころ", "fr": "Le Pauvre cœur des hommes", "en": "Kokoro", "zh": "心" },
      "author": { "ja": "夏目漱石", "fr": "Natsume Sōseki", ... },
      "summary": { "fr": "...", "en": "...", "zh": "..." },
      "level": "advanced",
      "license": "public_domain",
      "language": "ja",
      "chapters_count": 110,
      "tokens_count": 142503,
      "path": "books/kokoro-soseki/meta.json"
    }
  ]
}
```

### `books/<id>/meta.json`

Tout ce qu'il faut pour afficher la page du livre et naviguer les chapitres.

### `books/<id>/chapter-NNN.json`

Le contenu d'un chapitre tokenisé. Format compact :

```json
{
  "id": "ch1",
  "index": 1,
  "title": "上 一",
  "paragraphs": [
    {
      "tokens": [
        { "surface": "私", "reading": "わたくし", "lemma": "私", "pos": "代名詞" },
        { "surface": "は", "reading": "は", "lemma": "は", "pos": "助詞" },
        ...
      ]
    },
    ...
  ]
}
```

- **surface** : le mot tel qu'écrit dans le texte
- **reading** : la lecture en hiragana
- **lemma** : la forme de dictionnaire (à envoyer à Jisho)
- **pos** : la classe grammaticale en japonais (traduite côté client via le système i18n)

## Sources de livres

Pour la version publique de la bibliothèque, on utilise uniquement des **livres du domaine public**. Sources recommandées :

- **[Aozora Bunko](https://www.aozora.gr.jp/)** — Le « Project Gutenberg japonais ». Des milliers de classiques (Sōseki, Akutagawa, Dazai, Tanizaki...) en téléchargement libre. La plupart ne sont pas en .epub mais en .zip de texte brut — il faudra un convertisseur ou un autre outil pour ceux-là.
- **[Standard Ebooks](https://standardebooks.org/)** — Ne couvre pas vraiment le japonais mais le format epub est de bonne qualité.
- **Tes propres écrits** ou ceux d'auteur·rice·s qui t'autorisent à les inclure.

⚠️ Ne **jamais** ingérer un livre sous copyright actif pour publication. Pour ton usage personnel via l'app client (import EPUB), aucun problème — ça reste chez toi.

## Pourquoi SudachiPy plutôt que MeCab ?

| | SudachiPy | MeCab |
|---|---|---|
| Installation Windows | `pip install` (1 commande) | Demande un compilateur C++ |
| Taille | ~72 Mo | ~5-50 Mo selon dico |
| Précision | Très bonne | Excellente |
| Vitesse | ~bonne | Plus rapide |
| Dictionnaire | Tenu à jour, moderne | Multiples options, parfois datées |

On a choisi SudachiPy pour la facilité d'installation cross-platform. Si plus tard on passe à du gros volume, on peut basculer sur MeCab côté Linux/CI.
