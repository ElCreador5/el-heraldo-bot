# Comandos consolidados de El Heraldo — Pruebas, 02/11/2026

Base remota auditada: `d3984074ba7a42ad1028577f2abb43a85249978b`. Registro final ejecutado localmente: **42 comandos raíz y 45 comandos invocables**. El único grupo restante es `/list`, con cuatro consultas. `main` no se modifica.

## Sustituciones verificadas en el árbol de discord.py

| Entradas retiradas del registro | Acceso único y destino |
|---|---|
| `/joinroles status`, `sync`, `add`, `remove`, `user_add`, `user_remove` | `/roles_ingreso` → mismo panel Roles de ingreso de Setup, con subpaneles General, Usuarios, Bots y Sincronización |
| `/suggestions panel`, `setup`, `revisor_add`, `revisor_remove`, `lista` | `/sugerencias` → mismo editor de Sugerencias de Setup → Moderación |
| `/programar crear`, `listar`, `editar`, `pausar`, `reanudar`, `silenciar`, `mover`, `eliminar`, `configurar` | `/anuncios` → editor y gestor existentes; se conserva el mismo motor y los datos |
| `/heraldo_log_channel` | `/registros` → mismo panel de Registros |
| `/verify_setup` | `/verificacion` → Verificación → Edad |
| `/verify_texts`, `/verify_dm_texts` | `/mensajes` → editores existentes de Verificación y DM de bienvenida |
| `/motw_set_schedule`, `/motw_set_channel` | `/miembro_semana` → mismo editor que Anuncios → Miembro de la Semana |
| `/condenar_setup`, `/condenar_template` | `/moderacion` → Condenas y `/mensajes` → Condenas, respectivamente |
| `/server_template_setup` | `/estructura_servidor` → mismo módulo añadido a Setup; conserva las claves del planificador histórico |

Las implementaciones heredadas siguen disponibles internamente para compatibilidad y pruebas; no se añaden al árbol que se sincroniza con Discord. Los anteriores grupos de Embed, Honeypot y Raid tampoco se registran. Las acciones y consultas directas se conservan deliberadamente y se clasifican en el catálogo.

## Inventario completo del código final

| Tipo | Módulo | Comando | Función |
|---|---|---|---|
| Configuración | Anuncios | `/anuncios` | Abre la configuración de Anuncios. |
| Configuración | Anuncios | `/miembro_semana` | Configura el anuncio de Miembro de la Semana. |
| Configuración | AutoMod | `/automod` | Abre la configuración de AutoMod. |
| Configuración | AutoMod | `/honeypot` | Abrir el panel de Honeypot. |
| Configuración | AutoMod | `/raid` | Abrir el panel de protección anti-raid. |
| Configuración | General | `/formato_fecha` | Configura el formato de fecha. |
| Configuración | General | `/language` | Configura el idioma de El Heraldo en este servidor. |
| Configuración | General | `/setup` | Configura las opciones generales de El Heraldo en este servidor. |
| Configuración | Registros | `/registros` | Abre la configuración de Registros. |
| Configuración | Mensajes | `/embed` | Administrar embeds desde un panel único. |
| Configuración | Mensajes | `/mensajes` | Editar los paneles y mensajes visuales personalizables de El Heraldo. |
| Configuración | Moderación | `/moderacion` | Abre el panel de Moderación. |
| Configuración | Moderación | `/sugerencias` | Abre la configuración de Sugerencias. |
| Configuración | Roles | `/roles_ingreso` | Configura los roles de ingreso. |
| Configuración | Roles | `/roles_reaccion` | Configura los roles por reacción. |
| Configuración | Estructura del servidor | `/estructura_servidor` | Configura el respaldo de la estructura del servidor. |
| Configuración | Verificación | `/verificacion` | Abre la configuración de Verificación. |
| Acciones | Anuncios | `/motw_test` | Probar el anuncio de Miembro de la Semana ahora mismo, sin resetear los contadores reales. |
| Acciones | Moderación | `/ban` | Banea a un miembro y crea un caso de Moderación. |
| Acciones | Moderación | `/caseclose` | Cierra un caso y revierte el castigo reversible cuando corresponde. |
| Acciones | Moderación | `/casedelete` | Elimina definitivamente un caso de Moderación. |
| Acciones | Moderación | `/caseupdate` | Actualiza motivo, duración o notas de un caso. |
| Acciones | Moderación | `/condenar` | Condenar a un miembro: guarda sus roles, los retira y aplica Condenado. |
| Acciones | Moderación | `/kick` | Expulsa a un miembro y crea un caso de Moderación. |
| Acciones | Moderación | `/liberar` | Levantar una condena y devolver los roles guardados. |
| Acciones | Moderación | `/mute` | Aplica timeout y crea un caso de Moderación. |
| Acciones | Moderación | `/purge` | Borrar mensajes de un usuario: todos, una cantidad o un rango de tiempo. |
| Acciones | Moderación | `/setproof` | Establece o reemplaza la prueba de un caso. |
| Acciones | Moderación | `/warn` | Advierte a un miembro y crea un caso de Moderación. |
| Acciones | Estructura del servidor | `/fusionar_canales` | Fusionar dos canales de texto mediante una migración segura de mensajes. |
| Acciones | Verificación | `/heraldo_check` | Fuerza la evaluación inmediata de un miembro (sin esperar el timer de 10 min). |
| Acciones | Verificación | `/heraldo_check_all` | Fuerza la evaluación inmediata de TODOS los miembros que tengan Tentad@. |
| Acciones | Verificación | `/verify` | Publicar el panel de verificación (botón) en un canal. |
| Acciones | Verificación | `/verify_dm_preview` | Mostrar en el canal de logs una vista previa del DM de bienvenida. |
| Consultas | General | `/list comandos` | Ver comandos agrupados por categoría y tipo. |
| Consultas | General | `/profile` | Muestra tu perfil o el de otro miembro. |
| Consultas | Mensajes | `/list embeds` | Ver los embeds personalizados guardados por nombre. |
| Consultas | Mensajes | `/list variables` | Ver todas las variables disponibles para textos y embeds. |
| Consultas | Mensajes | `/variables` | Probar un texto con las variables de El Heraldo. |
| Consultas | Moderación | `/advertencias` | Consulta el historial de advertencias de un miembro. |
| Consultas | Moderación | `/caseinfo` | Muestra la información de un caso de Moderación. |
| Consultas | Moderación | `/caselist` | Lista los casos más recientes de Moderación. |
| Consultas | Moderación | `/list condenados` | Ver todas las condenas activas del servidor. |
| Administración | Moderación | `/restaurar_roles_pendientes` | Reintentar los roles que no se pudieron devolver al levantar una condena. |
| Administración | Estructura del servidor | `/template_sync` | Sincronizar ahora la plantilla del servidor y ver su enlace. |

## Controles y comprobaciones

- `/mensajes` y los nuevos accesos reutilizan las vistas de Setup. El catálogo `/list comandos` filtra por tipo y módulo, mantiene selecciones y utiliza las descripciones del idioma guardado por servidor.
- Se reconstruyó `locales/command_schema.json` con las 102 descripciones/opciones reales. La base fallaba en `command_schema_changed:automod.description`; la sincronización se comprobó con transporte simulado en los tres idiomas.
- Cerrar se incorpora al renderizar sesiones administrativas, incluidos subpaneles con editor/padre, con control de identidad/permisos y sin escrituras. Los paneles públicos persistentes sin sesión administrativa no se alteran.
- Corregido `HoneypotExemptSelector`: asignaba dos valores a tres atributos. Cancelar una exención devuelve al selector y conserva su selección.
- Los botones de raid abren confirmación antes de actuar. Crear un embed propone un borrador confirmado; elegir el canal prepara vista previa y requiere Confirmar envío. No se ejecutaron sanciones ni publicaciones reales durante las pruebas.
- Nuevo editor de respaldo de estructura: selección y modal no guardan; confirmación con comparación transaccional de configuración y marcadores; cancelar/cerrar no escribe. Sin migraciones de esquema ni cambios deliberados en SQLite real.

## Validación y límites

- Python 3.12.14 y discord.py 2.7.1: importación nueva sin token ni Gateway, compilación completa y `pip check` correctos.
- 122 pruebas específicas de comandos/paneles/idiomas/seguridad: correctas; tres pruebas adicionales de claves y paneles en los tres idiomas: correctas; 36 regresiones de raíz/logs: correctas.
- Batería completa de componentes: 1 247 ejecutadas, 1 235 correctas, dos omitidas y diez incidencias heredadas (siete fallos y tres errores), reproducidas en la base: siete de Anuncios, una de fixture de identidad Enzonic, una de auditoría global de literales y una de selección del recordatorio tras cambio externo de idioma. No se eliminaron ni omitieron para dar verde.
- No hay verificación real de Enzonic ni clics reales en Discord en esta sesión: el conector de navegador carece del contexto de origen y el navegador disponible no tiene pestañas abiertas. No se declaró despliegue automático confirmado ni acceso a una consola autenticada.
- Antes de aceptación visual: comprobar el SHA desplegado, conexión Gateway y COMMAND_SYNC real; ejecutar los nuevos accesos en Heraldo's Lab y comprobar que no aparezcan los grupos retirados. Mantener el constructor personal público y la auditoría integral de idiomas como trabajos separados aún no validados.
