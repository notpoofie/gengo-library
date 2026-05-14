# Déploiement sur Cloudflare Pages

Ce dossier `public/` est le **dossier racine du site web**. Tout ce qui s'y trouve est servi tel quel par Cloudflare Pages.

## Première mise en ligne (étape par étape)

### 1. Pousser le code sur GitHub

Si ce n'est pas déjà fait :

```bash
cd gengo-library
git add -A
git commit -m "Site web statique pour la bibliothèque"
# Crée un repo vide sur https://github.com/notpoofie/gengo-library
git remote add origin https://github.com/notpoofie/gengo-library.git
git push -u origin main
```

### 2. Créer un compte Cloudflare (gratuit)

Va sur https://dash.cloudflare.com/sign-up et crée un compte avec ton adresse `philippecrepeau1@duck.com`. Tu n'as pas besoin de donner une carte de crédit pour le plan gratuit.

### 3. Créer un projet Cloudflare Pages

1. Une fois connecté, va dans **Workers & Pages** dans le menu de gauche
2. Clique sur **Create application** → **Pages** → **Connect to Git**
3. Autorise Cloudflare à voir tes dépôts GitHub
4. Sélectionne le dépôt `gengo-library`
5. Configuration du build :

   | Champ | Valeur |
   |---|---|
   | Project name | `gengo-library` (ou ce que tu veux) |
   | Production branch | `main` |
   | Framework preset | `None` |
   | Build command | *(laisse vide)* |
   | Build output directory | `public` |

   ⚠️ Le **Build output directory** est la seule case critique. Mets `public` (sans slash).

6. Clique sur **Save and Deploy**

### 4. Attendre la fin du déploiement

Cloudflare clone ton repo, voit qu'il n'y a rien à compiler, et publie directement le contenu de `public/`. Ça prend 30 secondes à 2 minutes.

Une fois fini, tu auras une URL du genre `https://gengo-library-XXX.pages.dev`. C'est l'URL publique du site.

### 5. Visiter le site

Ouvre l'URL dans ton navigateur. Tu devrais voir :
- La page d'accueil avec le catalogue (vide ou avec tes livres si tu as poussé `public/books/`)
- Le sélecteur de langue (FR / EN / 中)
- Si tu cliques un livre → page du livre avec table des matières
- Si tu cliques un chapitre → lecteur interactif mot-à-mot

### 6. (Optionnel) Domaine personnalisé

Si tu veux `gengo.notpoofie.com` au lieu de `gengo-library-XXX.pages.dev` :

1. Dans le dashboard de ton projet Pages → onglet **Custom domains**
2. Add custom domain → entre ton domaine
3. Cloudflare te donne les enregistrements DNS à configurer

## Mises à jour ultérieures

À chaque `git push origin main`, Cloudflare détecte le changement et redéploie automatiquement le site en 30-60 secondes. Pas d'action manuelle requise.

Cycle typique pour ajouter un livre :

```bash
# Ingérer un nouveau livre
python aozora.py --url https://... --id mon-livre ...

# Vérifier le résultat localement
cd public
python3 -m http.server 8000
# Ouvre http://localhost:8000

# Pousser
cd ..
git add public/
git commit -m "Ajout du livre X"
git push
```

## Limites du plan gratuit Cloudflare Pages

- **500 builds/mois** : largement suffisant (1 build par push)
- **20 000 requêtes/jour gratuites** : très large pour un projet personnel
- **100 Go de bande passante/mois** : énorme pour du JSON statique
- **Taille des fichiers : max 25 Mo par fichier** : aucun chapitre tokenisé ne s'approche de ça

Tu n'auras à payer que si le projet devient viral. Ce qui est un problème agréable à avoir.

## Test local avant déploiement

```bash
cd public
python3 -m http.server 8000
# Ouvre http://localhost:8000
```

Le serveur Python servira exactement ce que Cloudflare servira, donc si ça marche en local, ça marchera en ligne.
