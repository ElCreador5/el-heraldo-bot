# Verificación del candidato de PR #19 — 18/10/2026

## Automatización ejecutada

`python -m unittest test_member_logs test_regressions test_release_report_only test_honeypot_selective_main test_honeypot_runtime -q`

91 pruebas aprobadas en Python 3.13.16 dentro de una carpeta temporal de Railway
Test, sin credenciales en el proceso de pruebas y con SQLite desechable.
`compileall` y `pip check` aprobados. Los 34 casos nuevos también pasaron en
Windows/Python 3.12. Código final `bot.py` SHA-256:
`e47e6e72396bb1610d9ed4e00cbd4813bfa0a4a090db75c002a088520dc87fcd`.

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
Las modificaciones posteriores afectan confirmación de creación, seguimiento
de baneos y huella de imágenes del aviso. La corrección de imágenes se comprobó
también con el código final y la API real: imagen añadida al aviso de ensayo,
lectura de metadatos devueltos por Discord y recuperación del mismo ID mediante
recibo persistente. El fallo de ID ausente se inyectó exclusivamente en la
SQLite temporal del ensayo. No se provocó una caída del servicio ni se afirma
haber observado un fallo real de red. Al terminar, el aviso original quedó
restaurado, fijado y único; el proceso y la SQLite activos permanecieron intactos.

La huella excluye metadatos de medios añadidos por el servidor, conforme a la
[estructura oficial de embeds](https://docs.discord.com/developers/resources/message#embed-object).
Pruebas negativas verifican que otra imagen y varias coincidencias impiden
conciliar automáticamente y no provocan reenvíos.
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

Última lectura Railway: producción conserva despliegue
`b2426f15-4826-4e22-9cd1-90ff3573d41b` SUCCESS de `main@c6a5c164`, volumen
`heraldo-data` en `/data`, sin cambios preparados. Test conserva despliegue
`c447c30d-fcb5-46d8-9908-f29747b69d91` SUCCESS de `Pruebas@b90e3a6`.
