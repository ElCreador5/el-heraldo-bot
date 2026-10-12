#!/usr/bin/env bash
# Prepara dependencias de Codex sin cambiar la rama de la tarea.
# Sin inicio del bot, sin despliegues, sin modificaciones a SQLite.
set -Eeuo pipefail
cd "$(git rev-parse --show-toplevel)"

echo "[El Heraldo] Rama de tarea: $(git branch --show-current)"
echo "[El Heraldo] HEAD: $(git rev-parse HEAD)"
# En Codex Cloud, 'work' puede ser la rama interna normal. No exigir igualdad
# con origin/Pruebas: una tarea válida puede contener commits propios.
# Mostrar la referencia remota cuando esté disponible, sin modificar el checkout.
if git remote get-url origin >/dev/null 2>&1; then
  if git fetch --no-tags origin refs/heads/Pruebas; then
    target="$(git rev-parse FETCH_HEAD)"
    echo "[El Heraldo] Pruebas remota: $target"
    if git merge-base --is-ancestor "$target" HEAD; then
      echo "[El Heraldo] HEAD contiene la base remota de Pruebas."
    elif git merge-base --is-ancestor HEAD "$target"; then
      echo "AVISO: la tarea parte de una revisión anterior a Pruebas; actualizar la base antes de integrar el PR." >&2
    else
      echo "AVISO: historiales divergentes; revisar la base y los conflictos antes del PR." >&2
    fi
  else
    echo "AVISO: no se pudo consultar Pruebas; verificar la base antes de integrar el PR." >&2
  fi
else
  echo "AVISO: sin remoto origin; verificar la base del PR antes de integrar." >&2
fi

PYTHON_BIN="${PYTHON_BIN:-python3}"
"$PYTHON_BIN" -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m compileall -q bot.py
echo "[El Heraldo] Dependencias preparadas y compilación correcta; bot NO iniciado."
