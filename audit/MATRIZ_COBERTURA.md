# Matriz de cobertura verificable

Estado: 2026-10-11, rama de auditoría basada en PR #12. **Todas las filas tienen validación interactiva Discord pendiente para este lote.** `P` significa cobertura offline parcial observada en pruebas, `L` lectura de código sin prueba dedicada acreditada y `—` no comprobado. Ninguna celda P acredita todos los caminos. El inventario enlaza funciones y pruebas exactas por archivo/línea; no se asume cobertura por semejanza de nombres.

| Módulo y origen principal | Funcionamiento | Permisos | Guardar/cancelar | Persistencia/reinicio | Errores/concurrencia | Evidencia y vacío prioritario |
| --- | --- | --- | --- | --- | --- | --- |
| /setup, HeraldoSetupView | P | P | P | L | P | test_reaction_reports_ux: navegación real de siete secciones y serialización; faltan todos los controles internos |
| Configuración general, ConfigurationConfirmView | P | P | P | P | P | test_safety_regressions: originales obsoletos, revocación, SQLite; latencia Discord pendiente |
| Plantillas propias, message_payload/editor | P | P | P | P | P | test_message_payload/editors: límites, variables, borradores cerrados y concurrentes; render real pendiente |
| Mensajes oficiales, DefaultMessageStudioView | L | P | P | L | L | Familias actuales localizadas; sin recorrido exhaustivo de todos los editores |
| Embeds y kits | P | P | P | P | P | tests de formato, importación y reemplazo; falta enlace/ID y diferencia por campo |
| Componentes, message_components | P | P | P | P | P | test_message_editors: fallo parcial/auditoría/cooldown; reinicio Gateway y menús reales pendientes |
| Reaction Roles | P | P | P | L | P | test_regressions: añadir/quitar/invertir, límite y simultaneidad; recuperación real pendiente |
| Reportes por reacción | P | P | P | P | P | Nuevas pruebas de selector, etiquetas, permiso y ledger; crash después de sanción sin cubrir |
| Condenas/perdón | P | P | P | P | P | test_safety_regressions: rol real, bloqueo, caducidad, snapshot; tarjeta/DM/caso completo pendiente |
| Roles pendientes | P | P | P | P | P | PR #11: aislamiento, cancelar, asignación parcial; defer, error API y revocación durante consulta probados; estado incierto pendiente |
| Evidencias | P | P | — | L | P | Pruebas runtime de denegación y copia parcial/completa; retención y descarga real pendientes |
| Purgas | L | L | L | — | L | No hay validación integral de archivo de cada mensaje eliminado; no probar en contenido real |
| Honeypot | P | P | P | P | P | Cancelar add/create/remove/exención/setup; flujo captura-sanción-retención completo pendiente |
| Raid Protection | P | P | P | L | P | setup confirmado y mocks de rol; ráfagas/reingreso/reinicio pendientes |
| Verificación | P | P | P | P | L | Avisos y setup; eventos completos, caducidad y reingreso pendientes |
| Orientación | L | P | P | L | L | Modal y cola localizados; no acreditar prueba integral de expulsión/restauración |
| Join Roles | P | P | P | P | P | Cola SQLite, demora, reglas, fallo API; desconexión real y eventos no recibidos pendientes |
| Sugerencias | P | P | P | P | L | Cancelar destinatarios/panel sin publicación; ciclo completo de revisión pendiente |
| Logs administrativos/miembros | P | P | P | P | P | test_member_logs, categorías, incertidumbre/auditoría; salidas por canal reales pendientes |
| Actividad/Miembro de la Semana | L | P | P | L | L | Cancelar horario y canal; ranking, empate, reinicio y premios sin acreditar |
| Programación, message_automation | P | P | P | P | P | Zona horaria, envío incierto, aislamiento; publicación real pendiente |
| Autorespuestas | P | P | P | P | P | Coincidencia, usuario, bot/webhook ignorado, frecuencia; Message Content real pendiente |
| Sticky | P | P | P | P | P | Autoría, actividad concurrente y reposición; eliminación/envío reales pendientes |
| Webhooks | P | P | P | L | P | Propietario, permisos y propuesta obsoleta; credenciales no persistidas; fallo incierto real pendiente |
| Plantilla/copia del servidor | L | L | L | L | L | Sincroniza plantilla Discord y DM; **no constituye backup SQLite** |
| SQLite/migraciones | P | — | P | P | L | Pruebas con BD temporales; falta restauración de copia y migración desde varios esquemas históricos |
| Casos, advertencias, silencios, ban/kick | L | L | L | L | L | Comandos y bucle de expiración inventariados; cobertura específica insuficiente |
| Variables, perfiles, historiales y utilidades | P | L | L | L | L | Variables de Mensajes probadas; utilidades restantes requieren casos propios |

Las pruebas estáticas de seguridad preexistentes se mantienen, pero se añadieron pruebas de ejecución del archivo de evidencia para evitar presentar búsquedas de texto como demostración de efectos secundarios.
