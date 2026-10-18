# H-03 — Puertas de salida, dependencias y riesgos ocultos

Fecha de revisión: 2026-10-18. Fuente principal: código de `Pruebas`, PR #18 de Codex, Railway y metadatos de Supabase. **No implica activación de producción.**

## 1. Qué puede comprobarse ya

- El cron `heraldo-h03-lab-cron` crea SQLite **sintética**, genera copia AES-GCM, la descarga y verifica restauración; no tiene `DB_PATH` ni `DISCORD_TOKEN`, y usa volumen propio. No protege por sí solo la SQLite del servicio `worker`.
- El servicio `worker` tiene otra SQLite en su volumen, configuración de almacenamiento H-03 y `sleepApplication=true`. No hay ejecución autorizada/verificada del motor contra esa SQLite. Sus secretos deben permanecer fuera del repositorio y los logs.
- `Pruebas` contiene un contrato offline de publicador (`tools/h03_release_controller_contract.py`, 15 tests), **no** un controlador real conectado a GitHub/Railway; la PR #18 contiene `preupdate_gate.py`, copias preupdate independientes y 22 tests, **pero sigue en borrador**. El bloqueo explícito de `DECISIONES.md` prevalece: no fusionar #18 ni H-03 en `main` hasta las condiciones aprobadas.
- El bucket `heraldo-sqlite-backups` es privado. Metadatos vistos el 18/10: cinco generaciones bajo `lab/`, última el 18/10 06:15 UTC; **una sola** generación `heraldo-production/`, del 13/10 22:09 UTC. No se ha repetido la descarga, descifrado ni restauración de la producción real.
- Las dos políticas RLS para `storage.objects` restringen INSERT y SELECT al bucket y a una identidad técnica; **no filtran por prefijo**. Separar la identidad y RLS de producción y laboratorio antes de activar H-03 oficial, conservando lectura de copias antiguas.

## 2. Matriz completa de requisitos antes de activar el oficial

| Puerta | Cómo demostrarla | Estado comprobado |
|---|---|---|
| Recuperación de la clave original desde custodia independiente | Sesión/dispositivo aislado, sin mostrar clave, y descifrado de la generación anterior | BLOQUEADA por decisión de noviembre 2026 |
| Identidades y RLS separadas | Política específica de prefijo e identidad; pruebas ALLOW/REJECT para ambos entornos y generaciones heredadas | PENDIENTE |
| Control de capacidad y disponibilidad | SQLite real, WAL, espacio disponible, volumen y límites de Supabase; prueba sin purgas | PENDIENTE |
| Recuperación efectiva | Instantánea consistente del servicio dueño del volumen, descarga, verificación AES-GCM y restauración aislada | PENDIENTE en producción |
| Control de despliegue completo | Guard de un solo uso que compruebe SHA origen/candidato, resultado final de GitHub y Railway, timeout y rollback sin restaurar datos sobre DB viva | PENDIENTE |
| Rutas de evasión | Asegurar despliegue desde GitHub, Railway manual/API, cambios variables, restart/redeploy e imágenes fuera del controlador | PENDIENTE |
| Seguridad de ramas | Revisión ≥1, checks python-checks + H03 cuando exista y ausencia de bypass | Revisión/python-checks comprobados; H03 pendiente |
| Entrega de avisos | Confirmación del canal y prueba de fallo de respaldo, silencio, retraso y límite de almacenamiento | PENDIENTE |
| Continuidad del programador | Horario 06:15 UTC, servicio activo, efecto de sleepApplication y reanudación; comprobar al menos un ciclo | PENDIENTE en producción |
| Retención y restauración | Ventana/coste, no borrar copias antes de garantizar otra recuperación; plan de ejercicios periódicos | PENDIENTE |
| Integridad de evidencias | H03 SQLite NO incluye necesariamente adjuntos/evidencias guardadas en disco; inventariar respaldos de esos ficheros por separado | PENDIENTE |
| Control de cambios de esquema | Migraciones, reversión de código sin sobrescribir SQLite más reciente, compatibilidad tras downgrade | PENDIENTE |
| Ensayos destructivos | Solo Test o datos sintéticos; nunca expulsar usuarios reales ni sobrescribir SQLite | PENDIENTE |
| Custodia de credenciales | Secretos específicos producción en gestor privado, controles de rotación/revocación y pruebas sin revelar valores | PENDIENTE |

## 3. Secuencia segura y finita

**Ahora en desarrollo:** (a) cubrir con ensayos sintéticos la autenticación de respaldo, manipulación y restauración, (b) auditar el PR #18 y aislar tests sin fusionarla hasta que el bloqueo lo permita, (c) definir la barrera real de despliegue y sus pruebas de evasión, (d) decidir expresamente si se requiere conservar la SQLite real del bot Test y crear entonces un respaldo de solo lectura desde el proceso con su volumen, sin copiar el archivo SQLite activo a ciegas ni exponer registros sensibles.

**Después del desbloqueo acordado:** (e) custodia independiente original y restauración histórica, (f) secretos/RLS por entorno verificados, (g) respaldo productivo nuevo y restauración aislada, (h) despliegue autorizado de código revisado con rollback y comprobación de gateway, (i) activar y observar el primer cron productivo y monitorización confiable, (j) acreditar un check H03 que no pueda eludirse.

## 4. Riesgos de promesas incorrectas

- Un archivo remoto por sí solo no demuestra que se pueda restaurar.
- `SUCCESS` de Railway no confirma el funcionamiento de Discord ni la integridad de SQLite.
- Un check GitHub exitoso no protege despliegues directos en Railway.
- Una prueba con SQLite sintética no equivale a respaldar la SQLite real de Test.
- Respaldar SQLite no garantiza preservar ficheros adjuntos, evidencias o secretos necesarios para reconstruir el servicio.
- Si un estado queda `needs_manual_review`, no borrar recibos para forzar reintentos; reconciliar primero el destino.
- Las métricas de Storage no deben publicarse con rutas privadas, IDs de usuarios ni manifiestos.

**Bloqueo vigente:** `DECISIONES.md` impide modificar `main`, activar H-03 productivo, añadir sus secretos y desactivar `sleepApplication` mientras faltan condiciones, sin alterar la fecha acordada de noviembre. **No se realizaron pruebas interactivas de Discord ni se modificaron datos de producción en esta auditoría.**
