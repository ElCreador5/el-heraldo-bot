# Verificación del candidato de PR #19 — 18/10/2026

## Automatización ejecutada

`python -m unittest test_member_logs test_regressions test_release_report_only test_honeypot_selective_main test_honeypot_runtime -q`

89 pruebas aprobadas en Python 3.13.16 dentro de una carpeta temporal de Railway
Test, sin credenciales en el proceso de pruebas y con SQLite desechable.
`compileall` y `pip check` aprobados. Los 32 casos nuevos también pasaron en
Windows/Python 3.12. Código final `bot.py` SHA-256:
`ab98013705784579f654816e8ce0c28ee830fa39d8bc66923fdaafa6a98646ba`.

Los casos ejecutan clases/callbacks reales de discord.py y persistencia SQLite:
propiedad de panel, permisos revocados, borradores, Guardar/Cancelar/Descartar,
modales desactualizados, confirmaciones concurrentes, actualización del panel,
errores parciales, envío ambiguo/reinicio, autor y periodo de purga, hilos
privados, mínimo de 24 horas, jerarquía y exenciones, ban sin purga implícita,
expediente y vencimiento, reintento de desbaneo, baneo ajeno posterior,
antifallos por servidor, Solo registrar y conservación de evidencia ajena.

## Discord real ejecutado

API oficial del bot Test, servidor cuyo nombre exacto es `Heraldo's Lab`.
Carpeta/SQLite temporal del candidato; no se importó sobre la base viva.
Canal privado de ensayo `pr19-validacion-20261018`, retenido para inspección.

- Publicación, fijado y actualización del mismo aviso: comprobados con nueva
  lectura desde Discord; sin duplicación, incluso recreando el estado en memoria.
- Mensaje del autor seleccionado eliminado y mensaje de otro autor conservado:
  comprobados por lecturas API. Ambos fueron fixtures creados expresamente por
  bot/webhook, no contenido previo de personas.
- Hilos públicos y privados archivados encontrados y purgados: comprobados.
  El primer ensayo detectó que Discord impedía borrar mientras estaban archivados.
  Se corrigió y comprobó desarchivar únicamente durante la operación y rearchivar.
- Webhook temporal eliminado después del ensayo; no se conserva su credencial.
- Worker Test mantuvo el mismo proceso y `Pruebas@b90e3a6`; no se cambió su rama.

Las operaciones API se comprobaron con hash de bot
`d93a2f039ca046cc9969fcd6193ed1a845ce1a9e134a3840c47d1f2cc7b94f4a`.
Las modificaciones posteriores afectan confirmación de creación y seguimiento
de baneos, no las funciones de aviso/purga comprobadas en Discord.
NO realizadas: interacción humana con botones/modales; Kick/Ban real de cuentas
de prueba designadas. Los dobles automatizados no se presentan como esos ensayos.

## Copia productiva real

18/10/2026 14:55:44 UTC, origen `main@c6a5c164`, SQLite de 671744 bytes,
WAL activo, instantánea mediante SQLite backup API en el volumen propietario.
Cifrado AES-GCM: 186164 bytes. Subida sin sobrescritura a Supabase privado,
descarga autenticada, SHA-256, integridad, claves foráneas, esquema, recuentos
y contenido de restauración aislada correctos. Clave errónea y ciphertext
alterado rechazados. Cinco archivos previos del volumen conservados y mismo
proceso productivo antes/después. Nunca se restauró sobre la base activa.

Se usó la clave ORIGINAL desde la custodia local con ACL limitadas a propietario
y SYSTEM. Recuperación independiente de Bitwarden: PENDIENTE, no acreditada
por esta prueba. Los objetos, claves, manifiestos privados y datos no se publican.

## Condiciones pendientes

GitHub mantiene una aprobación obligatoria y `python-checks`, sin bypass.
No hay aprobación independiente. Railway producción sigue `main`, con
`checkSuites=false`, sin controlador H-03 universal ni check H-03 obligatorio.
No se alteraron esas protecciones/configuraciones para forzar publicación.
La PR continúa en borrador y no se ha desplegado Honeypot en producción.
