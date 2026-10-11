# Auditoría integral de El Heraldo — primer corte verificable

## Recuperación y responsabilidad

Responsable técnico de este trabajo: Codex. Se trabajó directamente, sin delegación ni nuevas conexiones. GitHub conserva la continuidad. El propietario decide cambios de producto, servidor real y producción; ChatGPT coordina esas decisiones. El archivo de instrucciones recibido termina en «- Com»; no se infiere contenido posterior.

Estado remoto comprobado el 2026-10-11:

- `main`: `6f9f9ee0a7ed1c7b7e6c48a13817b9b5f3a5b667`, intacta.
- `Pruebas`: `a659b286330c3d16d97d5fb4c8dc05396af71b2c`; incorpora PR #7, #10 y #11. Diferencia de ascendencia con main: 0 commits exclusivos de main y 100 exclusivos de Pruebas. No representa conflicto por sí misma.
- PR #12: borrador abierto `fix/ux-reportes-20261011@a260fec8c47100b45409ea7198b2eb540e501e6a`, base Pruebas. CI 38157090799 correcta, pero la auditoría reprodujo un fallo que esa suite no detectaba.
- PR #9: borrador antiguo sobre roles no restaurados; su intención ya está cubierta en buena parte por #10/#11. Su diff fue inspeccionado: solo añade IDs al log; esa función ya está en la rama actual mediante missing_role_ids y unrestored_note. No aporta recuperación adicional. No se cerró ni sobrescribió.
- PR #8: documentación de Obsidian separada. No se integró ni se considera necesaria para ejecutar el bot. Queda revisión específica de su contenido.
- La rama local anterior `Pruebas@93c1a0c` se conservó. El trabajo nuevo vive en `codex/auditoria-integral-20261011`, basada exactamente en PR #12, para no reintroducir commits equivalentes ni sobrescribir el trabajo de otros agentes.

Railway Test: despliegue `a8314dd2-3607-48f4-8c10-784720ed94c6`, SUCCESS sobre `a659b28`. Arranque con volumen montado, Gateway conectado y autoprueba `/setup` correcta. No se reinició ni desplegó durante esta auditoría. Los registros de actividad existentes no se consideran ensayos controlados ni se copian datos de miembros a este informe.

## Inventario y alcance real

`python tools/audit_inventory.py` produce `INVENTARIO.json` y `INVENTARIO.md` sin importar el bot. Incluye 1241 definiciones, 82 funciones decoradas como comandos, 103 vistas/modales, 200 callbacks decorados, 19 eventos, 9 bucles periódicos y 418 sitios de construcción/registro dinámico. Son cantidades estáticas; no se deben confundir con número de comandos raíz registrados ni con cobertura. El JSON conserva también funciones auxiliares y callbacks dinámicos, no solo las entradas visibles del menú.

Se localizaron 144 pruebas: 39 de raíz/Logs y 105 en tests después de las ampliaciones. La línea base de PR #12 tenía 132. La matriz adjunta expresa cobertura parcial por módulo y aspectos no comprobados; no hay porcentaje de cobertura de ramas calculado.

## Defectos reproducidos y corregidos en esta rama

1. **Alta: selección de `/setup` rota en PR #12.** `select_module` llamaba a `self.configure(interaction, None)`, pero el decorador de Discord convertía `configure` en Button. Resultado reproducido: `TypeError: 'Button' object is not callable`. La prueba anterior sustituía el atributo por AsyncMock. Se conservó el método de navegación sin decorador; no se reintrodujo el botón redundante. Nueva prueba ejecuta el recorrido real y otra recorre las siete secciones visibles.
2. **Media: una regla de aislamiento no aceptaba su propio valor inicial.** El modal inicializaba «Timeout / mute», ausente de sus alias aceptados. Se añadió compatibilidad con ese valor y una prueba de ida y vuelta para las cinco acciones. No se cambiaron códigos internos ni reglas guardadas.
3. **Media: permisos del formulario de reportes no revalidados al enviarlo.** Ahora se consulta `parent_view.interaction_check` antes de mutar el borrador. Se verifica que la denegación conserva el borrador. Esta corrección no pretende acreditar todas las rutas de todos los modales.

4. **Alta: respuesta inicial tardía en restauración pendiente.** Se añadió defer antes de consultar/asignar miembros. Los mensajes posteriores usan seguimiento o edición de la respuesta original; se revalidan permisos después de consultar el miembro. Pruebas de error API, revocación y cancelación durante la consulta conservan pendientes y no otorgan roles. Se comprueba de nuevo el borrador y el permiso del bot después de la espera.

Ampliaciones sin cambio de comportamiento: pruebas de ejecución del archivo de evidencias (roles ordinarios, excepción individual, adjunto demasiado grande y copia privada completa); persistencia del recuento de reportes entre conexiones, deduplicación de reportante y aislamiento entre servidores.

## Hallazgos abiertos y decisiones

| Prioridad | Hallazgo sustentado en código | Acción siguiente |
| --- | --- | --- |
| Alta | `execute_moderation_report_action` permite `report` con purga configurada; la etiqueta «Solo reportar» puede ocultar un efecto destructivo | Proponer al propietario separar «Registrar reporte» de «Eliminar contenido»; conservar configuración mientras decide, advertirlo en recorrido de laboratorio |
| Alta | Archivo seguro de condena protege la evidencia vinculada; `run_purge_job` y `hp_start_purge` pueden abarcar otros mensajes sin copia íntegra individual | Revisar diseño de retención y alcance antes de ensayos destructivos; no habilitar purgas sobre contenido real |
| Media | Restauración pendiente ya difiere la interacción antes de fetch/asignación en esta rama | Pendiente ensayo real de latencia, resultado parcial y reintento idempotente |
| Alta | Reportes usan un bloqueo en memoria y marcan ejecutado después de la acción remota | Probar interrupción entre API y SQLite; definir estado incierto persistente antes de prometer no repetición tras reinicio |
| Alta | `run_scheduled_template_backup` sincroniza una plantilla Discord; no respalda SQLite ni mensajes/evidencias | Preparar copia consistente SQLite y probar restauración aislada antes de una promoción a producción |
| Media | Filtro conservador de evidencias rechaza todos los roles no administradores con acceso, incluidos potencialmente roles administrados del propio bot | Revisar canal de evidencias dedicado y política de acceso sin exigir Administrador al bot; no relajar acceso automáticamente |
| Media | Códigos de expediente aleatorios de siete caracteres proceden de `moderation_case_code`; el título incorpora tipos internos como CONDEMN | Mantener el identificador trazable; proponer tipo legible y código en campo «Expediente», sin cambiar el identificador |
| Media | Formato Honeypot con bloque de código ya se corrigió en PR #12; `log_embed` imprime título/descripción en consola | No atribuir todos los «códigos extraños» a la misma causa; revisar mensajes concretos con el propietario y minimizar datos en registros de alojamiento |
| Media | Descripciones de funciones y pies conservan textos informales, nombres ingleses y marcas de un servidor concreto | Proponer migración visual compatible, sin borrar valores elegidos por administradores |
| Media | PR #12 elimina un log duplicado de reporte, pero una sanción puede producir tarjeta, DM, resultado de reporte y log propio | Clasificar cada salida por destinatario y propósito; comprobar duplicado efectivo por canal antes de suprimir avisos de seguridad |
| Media | Catálogo oficial aún no ofrece todas las familias como editores independientes (Perdón, Advertencia, etc.) | Propuesta de catálogo estable en PROPUESTAS_Y_PLAN_REAL.md; conservar claves y plantillas existentes |

## Orden de continuación y puertas de avance

1. Fase 1 realizada para ramas/PR prioritarios y Railway; queda comparación residual de #8/#9. No se recuperó una identidad inequívoca del antiguo Agent AVD; sí se recuperó trabajo compartido de los agentes en commits/PR.
2. Fase 2: inventario completo de definiciones Python disponible y matriz por módulos. La verificación funcional de cada superficie continúa pendiente; un inventario no es una auditoría funcional completa.
3. Fases 3–4: línea base ejecutada, cuatro defectos corregidos con regresiones y cobertura de evidencia ampliada. Continúa la auditoría de riesgos de la tabla; no declarar cerradas estas fases globalmente.
4. Fase 5: PR de auditoría para revisión, dependiente de #12. No integrar #12 sin la corrección del selector. Tras revisión y autorización de integración, ejecutar CI sobre la versión integrada, desplegar exclusivamente Test y registrar commit/Gateway/autoprueba. No se atribuyen clics humanos a la autoprueba.
5. Fases 6–8: plan y propuestas preparados; servidor real sin nombre ni autorización. La preparación documental no ejecuta esa fase.
6. Fase 9: no autorizada. Requiere pruebas, respaldo restaurable, rollback y aprobación explícita de producción.

No se enviaron mensajes a otros chats/agentes ni se realizaron acciones sobre miembros, roles, mensajes o configuración Discord.

## Verificación final local

`python -m unittest test_regressions.py test_member_logs.py`: 39 correctas. `python -m unittest discover -s tests -p test_*.py`: 105 correctas. Compilación, pip check y git diff --check correctos en Python 3.12.10 / discord.py 2.7.1. Ejecución aislada, sin Gateway. Los fallos iniciales del selector y etiqueta timeout se reprodujeron antes de corregirlos; no se ocultan como pruebas pasadas. La CI del nuevo PR debe comprobarse sobre su SHA final.
