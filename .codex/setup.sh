#!/usr/bin/env bash
# Entorno de desarrollo de El Heraldo. No inicia el bot ni modifica datos de Discord.
set -Eeuo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "[El Heraldo] Comprobando repositorio..."
git status --short
CURRENT="$(git rev-parse HEAD)"
echo "Rama local: $(git branch --show-current)"
echo "HEAD local: $CURRENT"
if [[ -n "$(git status --porcelain)" ]]; then
  echo "Hay cambios locales; no se prepara el entorno para evitar pisar trabajo." >&2
  exit 1
fi

# Una rama 'work' de Codex es válida si su contenido proviene de Pruebas.
# Nunca cambiar de rama automáticamente ni hacer reset/merge/push.
if git remote get-url origin >/dev/null 2>&1; then
  if git fetch --no-tags origin refs/heads/Pruebas; then
    TARGET="$(git rev-parse FETCH_HEAD)"
    echo "Pruebas remota: $TARGET"
    if [[ "$CURRENT" != "$TARGET" ]]; then
      echo "AVISO: la copia local no coincide con Pruebas. Sincronizarla de manera segura antes de desarrollar." >&2
      exit 2
    fi
  else
    echo "No se pudo consultar Pruebas; no se instalará sobre una base no verificada." >&2
    exit 3
  fi
else
  echo "No hay origen Git configurado; verifica manualmente la base de la tarea." >&2
  exit 4
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m pip install --upgrade pip
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m compileall -q bot.py
echo "[El Heraldo] Dependencias instaladas y compilación correcta. Bot NO iniciado."
