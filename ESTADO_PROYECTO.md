# Candidato selectivo Honeypot — PR #19

Estado comprobado el 18/10/2026. Rama `release/honeypot-selective-20261018`,
base de este trabajo `9fc47d5bc1e77f6d44c0c72781a42044e783e72e`.
`main` permanece en `c6a5c1642d84b776e522473d62cf92c60e018cb3`.
No se ha fusionado ni desplegado el candidato en producción.

Se corrigieron privacidad de la caché en trampas, permisos al confirmar,
guardados atómicos, cancelación y actualización del panel, publicaciones
ambiguas, creación concurrente de canales, purgas de hilos privados/archivados
y conservación del vencimiento de baneos ante fallos. Las rutas ajenas a
Honeypot conservan sus evidencias y sus políticas de purga.

32 pruebas funcionales nuevas; 89 regresiones completas aprobadas en Railway
Test con SQLite temporal. Avisos y purgas también comprobados con la API real
de El Heraldo Test en Heraldo's Lab. Alcance y límites en [PRUEBAS_DISCORD.md](PRUEBAS_DISCORD.md).

Copia SQLite productiva nueva del 18/10 a las 14:55:44 UTC: descarga cifrada,
autenticación y recuperación aislada verificadas. No acredita recuperación
independiente desde Bitwarden; esa condición sigue pendiente.

Integración bloqueada por aprobación independiente ausente, custodia
independiente aún sin verificar y controlador H-03 no eludible pendiente.
También falta aceptación humana de botones/modales del candidato y ensayo
Kick/Ban con cuentas de laboratorio designadas. No se han usado personas reales
como objetivos de prueba. CI del commit publicado debe comprobarse en PR #19.

Los documentos generales fueron consultados desde `Pruebas@b90e3a6`; no se
copió su código ni su documentación histórica completa a esta rama selectiva.
