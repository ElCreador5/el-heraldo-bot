# Revisión del PR #7

## Estado y entorno

El PR integra correcciones de moderación y amplía Mensajes sobre `Pruebas`. El laboratorio sigue en `34fa94f` hasta integrar y desplegar este PR. `main@6f9f9ee` y producción no forman parte de esta revisión. No hay pruebas interactivas acreditadas para este lote.

## Recorrido propuesto en el laboratorio

1. Registrar el commit del despliegue, comprobar conexión Gateway y autoprueba de setup. Usar únicamente el bot de laboratorio y cuentas de prueba manejadas por personas.
2. `/setup`: cancelar un formulario, confirmar otro y retirar Administrar servidor antes de confirmar un tercero. Verificar aislamiento entre administradores y rechazo de propuestas obsoletas.
3. Crear una plantilla y abrir `/editar_plantilla`: texto independiente, dos embeds, campos, miniatura, autor y pie. Previsualizar, cancelar, volver a editar y confirmar. Guardar no debe publicar. Para descripciones de más de 4000 caracteres usar JSON: el formulario no las recorta.
4. Adjuntar el JSON del ejemplo a `/componentes_mensaje`. Publicar la plantilla con el bot. Confirmar/cancelar una selección, comprobar destinos y resultados; retirar permisos al creador antes de otra ejecución. Un error detiene las acciones restantes y muestra las ya realizadas; no hay deshacer automático. Repetir la pulsación dentro de quince segundos debe rechazarse.
5. Probar condena/perdón con un miembro de prueba y roles ordinarios. Subir un rol sobre el bot antes del perdón: comprobar resultado parcial y registro. Simular archivo privado inaccesible: no debe purgarse la evidencia vinculada. Revisar tarjeta, DM, roles y caso; no asumir que un DM cerrado invalida la liberación.
6. Logs: ingreso, salida, expulsión, baneo, advertencia y auditoría inaccesible. Revisar categoría, canal, actor y tratamiento de incertidumbre.
7. Join Roles y Reaction Roles: aceptación de reglas, demora, reinicio, rol administrado/superior, condena activa y permisos revocados. Verificación y reportes: autorizaciones, canal, duplicados y persistencia tras reinicio.
8. Programación, autorespuesta, sticky y webhook: confirmar/cancelar, reiniciar durante espera, retirar permisos antes de ejecutar, verificar destinos y ausencia de bucles. Un envío incierto requiere inspeccionar el canal antes de reintentar.

Registrar por caso: commit, acción, resultado esperado, resultado real y error reproducible. No guardar credenciales, transcripciones privadas ni evidencias sensibles en GitHub.

## Ejemplo de componentes

Guarde este bloque como un archivo JSON. Primero cree las plantillas `Ayuda` y `Información`. Los IDs de roles y canales se configuran exclusivamente con recursos del laboratorio.

```json
[
  {
    "tipo": "menu",
    "etiqueta": "Consultar información",
    "maximo": 2,
    "opciones": [
      {"etiqueta": "Ayuda privada", "acciones": [
        {"tipo": "respuesta", "plantilla": "Ayuda", "efimera": true}
      ]},
      {"etiqueta": "Información por mensaje directo", "acciones": [
        {"tipo": "respuesta", "plantilla": "Ayuda", "efimera": true},
        {"tipo": "dm", "plantilla": "Información"}
      ]}
    ]
  }
]
```

Acciones admitidas: `añadir_rol`, `quitar_rol`, `alternar_rol` con `rol` como ID de texto; `respuesta`, `dm`, `editar` con `plantilla`; `canal` con `plantilla` y `canal` como ID de texto; `eliminar` sin destino, siempre sobre el mensaje original del bot. Las acciones públicas exigen Administrar mensajes al ejecutor y al autor de la configuración en el destino. Los roles con permisos privilegiados se rechazan. Máximo cuatro componentes, cinco acciones por opción y veinticinco acciones por plantilla.

## Pendientes que impiden declarar el alcance total completo

- Revisar exhaustivamente las rutas heredadas de configuración que aún escriben directamente (por ejemplo `/honeypot setup`, reanudación y `/condenar_setup`). Los dos formularios de texto/diseño Honeypot ya requieren confirmación.
- Archivo integral y retención de todos los mensajes de una purga amplia; la protección actual de copia íntegra se aplica a la evidencia vinculada. Revisar accesos por roles/miembros del canal de archivo, además de `@everyone`.
- Recuperación operativa de restauraciones parciales y reconciliación tras interrupción entre cambios remotos y SQLite. La copia previa de roles reduce pérdida de información, pero no convierte ambas operaciones en una transacción.
- Catálogo completo con Raw/restauración uniforme por evento; importación segura por enlace/ID, comparación de kits por campo, editor visual de acciones y conservación de selección por miembro.
- Pruebas reales de Discord y reinicios del laboratorio. No se declara paridad completa con Sapphire ni aptitud para producción.
