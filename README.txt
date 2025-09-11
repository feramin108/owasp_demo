# DevSecOps Insecure Demo App

**Purpose:** A deliberately insecure Flask application designed to demonstrate how DevSecOps pipelines can surface blind spots tied to OWASP A04 (Insecure Design), A05 (Security Misconfiguration), and A06 (Vulnerable & Outdated Components).

> **DO NOT** deploy this application in production. This repository is for educational/demo use only.

## What's included
- `app/app.py` — insecure Flask app (weak login, broken transfer logic, hardcoded secret, debug enabled).
- `requirements.txt` — intentionally outdated packages.
- `Jenkinsfile` — sample CI pipeline with security scanning stages (Bandit, Safety, Gitleaks, Semgrep).
- `.gitignore`

## Local run (for demo)
```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python app/app.py
# browse http://localhost:5000
