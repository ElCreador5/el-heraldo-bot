# Aceptacion interactiva pendiente del encargo #23

El respaldo productivo esta verificado. Las regresiones automaticas y el arranque de Test no sustituyen interacciones reales. Issue #23 exige validar en Lab antes del port; AGENTS UX-05 exige registrar lo no probado y detener su aceptacion. No hay herramienta disponible para manejar los clics de Discord; no usar tokens de una cuenta personal.

Ejecutar un recorrido de aceptacion **solo con El Heraldo Test en Heraldo's Lab**. Registrar fecha y commit desplegado de Test, observado en Railway, junto a cada resultado. Conservar los valores iniciales y no usar usuarios productivos como objetivos.

| Area | Recorrido real | Estado |
| --- | --- | --- |
| Edad | Abrir su panel desde `/setup`; preparar cambio de plazo y cancelar; reabrir y comprobar que no guardo. Ampliar el plazo, guardar con confirmacion, reabrir y comprobar persistencia; devolver el valor inicial con confirmacion. | PENDIENTE |
| Personalidad | Abrir panel; comprobar selectores de canal/roles y que los cambios de borrador no escriben al cancelar. Comprobar resumen de plazo separado, obligatoriedad/opcionalidad y navegacion Volver. Guardar un cambio seguro, reabrir y restaurar configuracion inicial. | PENDIENTE |
| Comentarios de salida | En la configuracion del evento de salida, abrir **Comentarios de salida**. Comprobar estado inicial, cancelar un borrador y reabrir. Si se ensaya activar, hacerlo unicamente con canal privado valido y confirmacion; restaurar estado inicial al terminar. | PENDIENTE |
| Flujo voluntario | Solo con cuenta de pruebas autorizada que pueda salir voluntariamente de Lab: comprobar DM, boton/modal, comentario vinculado a la tarjeta original y ausencia de logs duplicados. No solicitar salida al propietario de un servidor ni provocar sanciones sobre usuarios productivos. | PENDIENTE; requiere cuenta de pruebas |
| Reinicio | Con una solicitud de prueba pendiente, comprobar que el boton/modal sigue funcionando tras reinicio controlado de Test; no crear una segunda tarjeta. | PENDIENTE |

Los escenarios de permisos revocados, exenciones, CAS/rollback, plazos antiguos, sanciones fallidas, auditoria incierta y privacidad tienen cobertura automatica. Los vencimientos y sanciones no se presentan como ensayados en Discord; si se requiere su ensayo real, identificar previamente una cuenta de pruebas autorizada y preservar su acceso a Lab.

El propietario puede registrar cada resultado aqui o comunicarlo en la conversacion. Si falta cuenta de pruebas o acceso al cliente Discord, conservar ese bloqueo exacto y no marcar la funcionalidad como aceptada. No volver a pedir claves: su recuperacion ya se completo.
