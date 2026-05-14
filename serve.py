#!/usr/bin/env python3
"""
serve.py — Mini serveur HTTP local avec en-têtes CORS permissifs.

Sert le dossier `public/` sur le port donné (par défaut 8766) en ajoutant
les en-têtes CORS que Cloudflare Pages ajoute automatiquement. Utile pour
tester l'app cliente en local contre cette bibliothèque locale, sans avoir
encore déployé sur Cloudflare.

Usage :
    python serve.py
    python serve.py --port 8000

L'app cliente cherche par défaut la bibliothèque à
    https://gengo-library.pages.dev/
Pour pointer ailleurs en local, ouvre la console du navigateur dans l'app
et tape :
    localStorage.setItem('gengoLibraryUrl', 'http://localhost:8766/');
    location.reload();
"""
import argparse
import http.server
import socketserver
import sys
from pathlib import Path


class CORSHandler(http.server.SimpleHTTPRequestHandler):
    """Permissive CORS so any origin (incl. file:// and localhost:*) can
    fetch from this server. Mirrors what Cloudflare Pages does by default
    for static assets."""

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        # No-cache during dev so changes show up immediately
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--port', type=int, default=8766)
    ap.add_argument('--dir', type=Path, default=Path(__file__).resolve().parent / 'public')
    args = ap.parse_args()

    if not args.dir.exists():
        print(f"Dossier introuvable : {args.dir}", file=sys.stderr)
        print("Lance d'abord `python aozora.py --preset starter` pour générer les livres.")
        return 1

    import os
    os.chdir(args.dir)

    with socketserver.ThreadingTCPServer(('', args.port), CORSHandler) as httpd:
        print(f"Bibliothèque servie sur http://localhost:{args.port}/")
        print(f"  Dossier : {args.dir}")
        print("Ctrl+C pour arrêter.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nArrêt.")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
