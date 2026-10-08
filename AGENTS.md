# Instrucciones compartidas para asistentes — El Heraldo

Este archivo es el punto de entrada para ChatGPT, Codex, Claude y cualquier agente que trabaje sobre este repositorio. Leer antes de tocar código.

## Fuentes de verdad
1. `ESTADO_PROYECTO.md`: estado comprobado, prioridades, pendientes y entorno.
2. `DECISIONES.md`: criterios de producto y restricciones acordadas.
3. `PRUEBAS_DISCORD.md`: cobertura, resultados y fallos reproducibles.
4. Código y pruebas automatizadas: fuente final del comportamiento implementado. Nunca asumir que una afirmación documental reemplaza la comprobación del código.
5. `PLAN_MENSAJES.md`: plan específico de Mensajes; actualizar cuando avance.

## Flujo obligatorio
- Trabajar en `Pruebas`; nunca desplegar, fusionar ni modificar `main` sin aprobación explícita.
- Comenzar con `git fetch` / `git pull` de la rama correcta; no sobrescribir cambios remotos ni forzar pushes.
- Usar el bot de pruebas y el servidor de laboratorio; evitar acciones de prueba en servidores reales.
- Antes de alterar una función, inspeccionar código existente, dependencias y tests; no borrar capacidades silenciosamente.
- Mantener mensajes del bot en español formal y sin emojis decorativos; usar emojis únicamente si son funcionalmente necesarios.
- Cualquier modificación de configuración debe requerir confirmación explícita del administrador; cancelar no debe guardar.
- Comprobar permisos, jerarquía de roles, aislamiento por servidor, persistencia y fallos en interacciones.
- Ejecutar compilación y regresiones; diferenciar claramente pruebas automáticas de pruebas realmente realizadas en Discord.
- Cada sesión debe finalizar con commit descriptivo, archivos afectados, pruebas realizadas, errores y próximos pasos.
- Actualizar los tres documentos de coordinación en el mismo trabajo cuando cambie su información.
- No registrar tokens, credenciales, IDs secretos, datos de usuarios, transcripciones privadas ni evidencias sensibles.
- No automatizar una cuenta personal de Discord con tokens de usuario/self-bots; preferir bot oficial y cuentas de prueba autorizadas.
- Si hay cambios concurrentes, reconciliar primero mediante commits y PR; no dar por válida una versión antigua de los documentos.

## Informe de cierre (plantilla)
**Rama y commit:** ...
**Objetivo:** ...
**Cambios:** ...
**Verificación automática:** comandos y resultados ...
**Verificación real en Discord:** acciones y resultados, o «no realizada» ...
**Errores / riesgos:** ...
**Documentos actualizados:** ...
**Siguiente paso:** ...

Estado inicial documentado el 2026-10-08. Estas instrucciones se aplican también a agentes que operen desde otra cuenta o sesión si tienen acceso al repositorio.
