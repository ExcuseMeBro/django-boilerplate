#!/bin/sh
set -e

if [ -n "$FIREBASE_CREDENTIALS_JSON" ]; then
  echo "==> Writing Firebase credentials from FIREBASE_CREDENTIALS_JSON..."
  printf '%s' "$FIREBASE_CREDENTIALS_JSON" > /app/firebase-credentials.json
  chmod 600 /app/firebase-credentials.json
  export FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json
elif [ -n "$FIREBASE_CREDENTIALS_BASE64" ]; then
  echo "==> Writing Firebase credentials from FIREBASE_CREDENTIALS_BASE64..."
  printf '%s' "$FIREBASE_CREDENTIALS_BASE64" | base64 -d > /app/firebase-credentials.json
  chmod 600 /app/firebase-credentials.json
  export FIREBASE_CREDENTIALS_PATH=/app/firebase-credentials.json
fi

echo "==> Running migrations..."
python manage.py migrate --noinput

echo "==> Collecting static files..."
python manage.py collectstatic --noinput

echo "==> Starting Daphne..."
exec daphne -b 0.0.0.0 -p 8000 config.asgi:application
