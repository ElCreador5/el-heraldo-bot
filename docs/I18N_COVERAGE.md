# El Heraldo — cobertura obligatoria de idiomas

## Decisiones aprobadas
- Idioma por servidor; una sola preferencia en SQLite.
- Entradas: `/setup → Idioma` y `/language`.
- Textos públicos, interacciones, errores, registros, sanciones y DMs generados por el bot deben traducirse.
- No se traducen las personalizaciones ni los expedientes antiguos.
- **No publicar `en-US` o `pt-BR` hasta alcanzar 100 % de cobertura real**.
- No utilizar español como respaldo invisible al operar en otro idioma.
- Los textos internos, claves y nombres de comandos siguen estables.

## Estado actual
El motor `heraldo_i18n.py` y los catálogos están preparados y validados
para los textos del selector de idioma, pero **no constituyen traducción del
bot completo**. El único idioma habilitado continúa siendo `es-419`.
El código de los otros módulos aún necesita integrarse con el motor central.

## Puertas de publicación
1. Inventariar cada texto visible emitido desde `bot.py` y demás módulos.
2. Reemplazar todas las cadenas visibles por claves estables del catálogo.
3. Comparar claves y variables de los tres catálogos en CI.
4. Probar ramas dinámicas, menús, errores, botones, permisos, logs y DMs.
5. Verificar que cambiar la preferencia de un servidor no afecta otros.
6. No activar un idioma hasta la aceptación real en Discord Test.

El número de claves actualmente presentes en los tres catálogos no debe
interpretarse como el porcentaje de cobertura del bot entero.

## Cambio aprobado: idiomas disponibles con estado parcial
Inglés (`en-US`) y portugués brasileño (`pt-BR`) aparecen en el selector con la pista **Estado: parcial**. Pueden seleccionarse y guardarse por servidor. Los textos todavía no integrados continuarán temporalmente en español; el panel debe advertirlo de forma explícita. La cobertura integral sigue pendiente; no declarar ninguno de estos idiomas completo.
