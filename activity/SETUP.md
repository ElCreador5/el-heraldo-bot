# El Heraldo Test — Activity «Crear mensaje»

Estado: frontend y backend implementados en `Pruebas`, servidos por el **worker de Lab** en `https://worker-lab.up.railway.app`. No se ha tocado producción ni se ha creado una segunda base de datos.

## Activación imprescindible en Discord

1. Abrir el [Discord Developer Portal](https://discord.com/developers/applications) y seleccionar **la aplicación de El Heraldo Test** (no la oficial).
2. **Activities → URL Mappings:** asignar el prefijo `/` al destino `worker-lab.up.railway.app` (sin `https://`).
3. **Activities → Settings:** habilitar **Enable Activities**.
4. **OAuth2 → Redirects:** añadir `https://127.0.0.1`, como indica la documentación oficial de Activities.
5. Copiar el **Client Secret** de la aplicación de pruebas. Guardarlo **únicamente** en Railway Test → `worker` → Variables, con nombre `DISCORD_ACTIVITY_CLIENT_SECRET`. No pegarlo en Discord, GitHub ni ChatGPT. Railway ya tiene `DISCORD_ACTIVITY_WEB_ENABLED=1` y `PORT=8080`.
6. Reiniciar/republicar el worker de Lab tras establecer esa variable. No modificar `main` ni la aplicación oficial.

## Uso

`/setup → Mensajes → Crear mensaje` invoca `InteractionResponse.launch_activity()` (Discord API 2.6+). La Activity abre el formulario completo dentro de Discord: canal, texto, constructor de embed desplegable, fecha opcional, rol de aviso, recurrencia y confirmación.

La API se autentica vía OAuth2 de Discord y verifica membresía y `manage_guild`, permisos del canal y restricciones de menciones en **cada solicitud**. El envío inmediato utiliza `message_publish`; los programados utilizan `message_autofeeds.persist_schedule` y la SQLite existente. No se cambia el footer global: producción emplea nombre e icono del servidor; en Lab se muestra «El Heraldo's Labs 🧪». Sin secretos en el frontend.

## Límites y pendientes

- Sin `DISCORD_ACTIVITY_CLIENT_SECRET`, el formulario es solo vista previa; no se puede publicar.
- No se considera validado dentro de Discord hasta probar el flujo con Activities habilitadas.
- El SDK oficial se suministra desde el mismo origen mediante una pasarela a una versión fijada del paquete `@discord/embedded-app-sdk`.
- No borrar configuraciones antiguas ni deshabilitar el control previo de Custodio. Si el chequeo externo de IA bloquea un despliegue, no supone un fallo de Crear mensaje.
