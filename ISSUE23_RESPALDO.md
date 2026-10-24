# Respaldo productivo #23: evidencia administrativa

Estado: **VERIFICADO**, 24 de octubre de 2026, hora de Republica Dominicana.
Este archivo no contiene claves, filas SQLite, recuentos privados ni manifiestos.

| Comprobacion | Resultado real |
| --- | --- |
| Revision de origen | `41f55654a92fa44c350d2a33d261979bf595deb2` |
| Snapshot online con SQLite backup API | 07:53:44 RD |
| Identificador de operacion | `2300000000000000000001a16dbeff05` |
| Destino externo | Supabase Storage, `heraldo-sqlite-backups`, privado |
| Localizador del objeto | `heraldo-production/20261024/2300000000000000000001a16dbeff05.h03e` |
| Tamano cifrado | 267497 bytes |
| Descarga independiente y restauracion aislada | 07:54:43 RD; correcta, sin red durante la restauracion |
| Integridad, FK, esquema, recuentos y contenido | Correctos en snapshot y SQLite restaurada |
| Clave incorrecta / ciphertext manipulado | Rechazados por autenticacion GCM |
| Descarga anonima / ruta publica | Denegadas |
| Restauracion sobre base activa | No realizada |

SHA-256 de la SQLite del snapshot:
`32ddddcb70fc6bf0c5b0a0a9135bd2dd1d7b71a940f361ba19d00eef50832ed5`.

SHA-256 del objeto cifrado descargado:
`965a06aa3d566b47a0102958126dc4d97a1a4cb250ca344e48267723431d7d38`.

Fuente del ejecutor puntual:
`278927e56e8b598b9aaa2e8ed8194868b3fa2d33b6e87a99ed21039bd3a1186e`.

## Servicio y custodia preservados

- Despliegue de la copia puntual: `e6c948ec-bf5d-4ac6-b9e5-26045f78e77f`, SUCCESS.
- Regreso al arranque habitual: `81d4c369-212c-45f0-95d1-0584ef4e913f`, SUCCESS; Gateway conectado a las 07:56:22 RD.
- Ambos ejecutaron el mismo codigo productivo `41f55654`; no se integro Pruebas ni se cambio main.
- Volumen `heraldo-data` conservado en `/data`; tres variables originales conservadas con valores identicos. Seis variables temporales retiradas sin despliegues intermedios. El proceso del bot tampoco hereda las seis variables temporales del ejecutor.
- No se activo H-03 diario, no se cambio el plan, no se sustituyeron claves ni se borraron generaciones.
- La clave fue recuperada por el propietario desde su KeePass de USB y autentico una copia productiva historica. La clave del cron historico NO descifra esa copia y no se utilizo para cifrar produccion.
- En Windows solo se conserva custodia DPAPI de usuario, ciphertext y recibos administrativos en la carpeta temporal nativa, fuera de Git. La restauracion independiente utiliza SQLite en memoria y no escribe datos descifrados.

Recibos locales de esta sesion, fuera del repositorio:

- Custodia/configuracion DPAPI: `C:/Users/deval/AppData/Local/Temp/ElHeraldoIssue23-32c1dbeab1b74314a63437598e8ebea1`.
- Descarga y verificacion externa: `C:/Users/deval/AppData/Local/Temp/ElHeraldoIssue23-3cdc823267284d7b842a11608834402a`.

No depender exclusivamente de estas carpetas temporales: la copia durable esta en Supabase y la clave existente sigue en la boveda del propietario.

## Recuperacion y rollback

1. Recuperar la clave existente desde su custodia autorizada; no imprimirla ni sustituirla.
2. Descargar el objeto identificado arriba con la identidad tecnica limitada al bucket privado. Verificar SHA-256 del ciphertext antes de descifrar.
3. Autenticar AES-GCM, verificar manifiesto/fecha/revision y restaurar primero en SQLite aislada. Comparar integridad, FK, esquema, recuentos y contenido. El verificador `tools/issue23_verify_external.py` implementa esta comprobacion; su limite de frescura de 24 horas es para aceptar una publicacion nueva, no una prohibicion de recuperar historicos en un procedimiento de emergencia revisado.
4. Para una recuperacion productiva, detener primero la decision de publicacion y preparar un procedimiento especifico con bloqueo exclusivo del servicio, preservacion de la base actual y su WAL, y destino nuevo. **Este trabajo no ejecuta restauraciones sobre la base activa.**
5. El rollback de codigo anterior al port funcional es `41f55654`. No restaurar datos automaticamente por un rollback de codigo: se perderia actividad posterior al snapshot. Conservar todas las generaciones.

Si la aceptacion Lab se retrasa, comprobar frescura antes de publicar. Una nueva copia debe usar otra operacion, conservar el objeto actual y reutilizar la clave recuperada tras validarla; no reintentar una operacion ambigua ni pedir otro inicio de sesion sin comprobar acceso.

## Intentos previos relevantes

SSH/SFTP no disponibles desde el entorno y la red del propietario. La API rechazo el backup nativo de volumen por requerir espacio Pro; no se cambio el plan. En el primer ensayo HTTPS de Test, RLS rechazo un bucket incorrecto; la consulta administrativa confirmo cero objetos de ese intento en produccion. Se corrigio y se anadio regresion de aislamiento antes de ejecutar produccion. El ensayo corregido y la descarga independiente de Test fueron verificados, y su arranque normal fue restaurado.
