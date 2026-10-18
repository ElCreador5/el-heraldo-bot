# Continuidad — PR #19

Rama autorizada: `release/honeypot-selective-20261018`. Base de trabajo:
`9fc47d5bc1e77f6d44c0c72781a42044e783e72e`. Recuperar HEAD remoto antes de continuar;
los SHA históricos no autorizan sobrescritura. No crear otra rama/PR.

Cambios: `bot.py`, pruebas funcionales y CI; documentación de esta rama
selectiva. Resultados y límites completos en [PRUEBAS_DISCORD.md](PRUEBAS_DISCORD.md).
91 pruebas, dependencias y compilación aprobadas en Railway Test. API real de
avisos/purga comprobada. Copia productiva nueva recuperada el 18/10/2026.

Commits de continuación: `be742f3` (controles, privacidad, purgas y sanciones;
CI aprobada), seguido por la corrección de huella de imágenes de Discord.
Consultar el comentario de entrega en PR #19 para HEAD y CI definitivos.

No fusionar todavía: falta revisor independiente, recuperación de clave desde
Bitwarden y controlador H-03 no eludible. Falta aceptación humana del candidato
en Discord. No iniciar otro bot con token productivo ni sustituir el worker
Test sin revisar sus funciones de Pruebas y preservar su SQLite.

La bóveda está bloqueada en el navegador disponible; no hay CLI `bw` disponible.
La herramienta de navegador devolvió fallo de revisión automática por límite
de uso. No hubo rechazo por inseguridad y no se intentó eludirlo.

Siguiente intervención del propietario: desbloquear su sesión de Bitwarden
para verificar la recuperación del elemento existente «El Heraldo - H-03
produccion - clave de recuperacion», sin volver a importarlo ni enviar la clave
al chat. Después continúan revisión independiente y cierre de las otras puertas.

Herramientas operativas y recibos privados se conservan fuera del repositorio.
No repetir la generación del 18/10 ni subir otro objeto para ocultar un fallo.
No quedan cambios autorizados en `main`; no se ha desplegado el candidato.
