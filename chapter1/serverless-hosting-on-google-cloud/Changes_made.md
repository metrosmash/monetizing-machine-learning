## Changes made to serverless-hosting-on-google-cloud
- app.yaml
  - runtime: python27 → runtime: python311 — Python 2.7 standard environment was shut down by Google in January 2024
  - Removed api_version: 1 and threadsafe: true — both are Python 2-only directives that cause deploy errors on Python 3
  - Removed the libraries: block (ssl) — the SSL library shim was only needed for Python 2.7; Python 3 handles it natively
  - script: main.app → script: auto — the old script: handler pointing to a Python module is deprecated; auto tells App Engine to use your WSGI app automatically via gunicorn

- appengine_config.py — Deleted. The google.appengine.ext.vendor API was Python 2 only. In Python 3 standard environment, packages in requirements.txt are installed automatically at deploy time — no lib/ folder or vendor shim needed.

- main.py — No logic changes needed; the code was already clean. Minor formatting only.

- requirements.txt — Pinned Flask to >=2.3.0,<3.0 with an explicit Werkzeug pin to prevent version mismatch errors (a common gotcha with Flask 2.x).
