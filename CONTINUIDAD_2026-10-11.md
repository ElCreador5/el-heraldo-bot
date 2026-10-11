# Informe de continuidad — El Heraldo — 2026-10-11

## Rama, objetivo y estado
- Desarrollo integrado en **Pruebas**: `647f8a0d352fe5239240a8339eb73e3a2a89290a` antes de este informe.
- Producción `main@6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667`: **no modificada ni desplegada**.
- Objetivo: cerrar problemas de confirmación administrativa (A), restauración parcial de roles (B) y privacidad inicial de evidencias (C), manteniendo El Heraldo Test independiente.

## Cambios reales guardados y PR
- **PR #10 (fusionado)**, merge `d190c11a95a7a2f3f3d124434727e046f2aebe0c`, incorporó también PR #7. `bot.py`: confirmación al configurar honeypot (incluidas trampas/exenciones), Raid, verificación, Join Roles, sugerencias, canal de logs, condenas y Miembro de la Semana; revalidaciones de permisos y concurrencia; filtro conservador de privacidad del archivo de evidencias y registro de roles fallidos. Pruebas añadidas/ajustadas en `test_regressions.py`, `tests/test_safety_regressions.py` y `tests/test_evidence_access_regressions.py`.
- **PR #11 (fusionado)**, merge `647f8a0d352fe5239240a8339eb73e3a2a89290a`: persistencia de roles pendientes por servidor/miembro tras liberar condena; comando `/restaurar_roles_pendientes` con confirmación, chequeos de jerarquía y permisos, rechazo durante condena activa y tests offline.
- No se han realizado commits o cambios locales pendientes fuera del repositorio con estas tareas.

## Verificaciones automáticas comprobadas
- GitHub Actions `Heraldo Lab - Python regressions` y `Mensajes - verificación de regresiones`: **SUCCESS** sobre el merge PR #10 `d190c11a95` y también sobre el merge PR #11 `647f8a0d35`.
- En auditoría, ejecución `38146125476`: matriz Python 3.11/3.12/3.13 correcta (35 tests de raíz, 85 de tests y 4 de logs en el job consultado). El PR #11 añadió 4 pruebas y superó CI antes de su merge.
- Estas comprobaciones no equivalen a pruebas interactivas.

## Railway y Discord
- Proyecto separado **El Heraldo Test**, servicio `worker`: despliegue de `Pruebas@647f8a0d35` **SUCCESS**, con volumen de datos aislado; logs: conexión a Discord Gateway, autoprueba `/setup` correcta en Heraldo's Lab y cuenta del bot de prueba conectada.
- **Pruebas reales en Discord: NO REALIZADAS** mediante clics/comandos de un administrador humano en esta etapa. No inventar resultados.
- Producción Railway: no modificada.

## Riesgos y tareas pendientes
1. Probar con una cuenta administradora autorizada en Heraldo's Lab todos los flujos de guardar/cancelar, permisos retirados antes del clic, concurrencia y reinicios. Confirmar mensajes efímeros, botones y publicación de paneles.
2. Ensayar condenas, perdón, roles pendientes y restauración sobre miembros **de prueba autorizados**, DMs y tarjetas, sin efectos sobre miembros reales.
3. Validar política de acceso y retención de evidencias: la comprobación conservadora actual impide el archivo cuando roles ordinarios pueden ver el canal, incluso si serían moderadores; al fallar archivo debe impedir la purga correspondiente. Probar adjuntos y canales inexistentes.
4. Completar funciones avanzadas de Mensajes y Reaction Roles pendientes en `PLAN_MENSAJES.md`; no afirmar paridad con Sapphire.
5. Revisar PR #8 de documentación de Obsidian, aún separado de `Pruebas`, y comprobar compatibilidad antes de integrarlo.
6. Tras pruebas y revisión, hacer copia de seguridad SQLite, preparar rollback y obtener **autorización explícita específica** antes de modificar `main`.

## Paso siguiente concreto
Pedir al administrador abrir Heraldo's Lab y ejecutar **/setup**: navegar Mensajes, Logs y Condenas, abrir una edición segura, pulsar **Cancelar** y comprobar que no cambió; después guardar de manera controlada. Registrar el resultado en `PRUEBAS_DISCORD.md`. Continuar con el resto de la matriz. Sin esa verificación, no promover a producción.


## Adenda: auditoría integral de Codex
La información anterior es histórica. Estado remoto vuelto a comprobar: Pruebas a659b28, main 6f9f9ee, PR #12 a260fec8 abierto; Test despliega a659b28. Trabajo nuevo en codex/auditoria-integral-20261011 con cuatro correcciones y 144 pruebas offline aprobadas. Inventario reproducible, matriz y riesgos en audit/AUDITORIA_2026-10-11.md; propuestas y servidor real en audit/PROPUESTAS_Y_PLAN_REAL.md. No hubo interacciones Discord ni despliegue nuevo. Comparar cualquier avance concurrente antes de integrar. Consultar el PR de auditoría para SHA/CI remoto final. No se completó aún la auditoría funcional de todas las superficies.


## Adenda: captura de expulsión duplicada
El propietario aportó una captura con dos registros del mismo evento de verificación. PR #13 se amplía para coordinar los temporizadores principal y Sin Verificar, con 11 regresiones nuevas y 155 pruebas offline totales aprobadas. Documentos e inventario actualizados; todavía sin integración/despliegue de esta corrección ni validación humana de la nueva versión. Ver PRUEBAS_DISCORD.md para reproducción y recorrido de aceptación.
