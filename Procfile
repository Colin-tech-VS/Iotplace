release: python scripts/release_check.py
web: gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
