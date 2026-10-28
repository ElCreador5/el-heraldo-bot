# El Heraldo Test — Activity «Crear mensaje»

Estado de implementación: la Activity y su servidor están en `Pruebas`, con cambio de autenticación a **OAuth2 PKCE (cliente público)**. No hace falta conocer, revelar, recuperar ni restablecer el Client Secret. Las publicaciones siguen protegidas mediante identidad OAuth, membresía y `manage_guild`; los datos persistentes permanecen en la SQLite original. El despliegue y la prueba de extremo a extremo deben verificarse antes de declarar la Activity operativa.

## Activación imprescindible en Discord

1. Abrir el [Discord Developer Portal](https://discord.com/developers/applications) y seleccionar **la aplicación de El Heraldo Test** (no la oficial).
2. **Activities → URL Mappings:** asignar el prefijo `/` al destino `worker-lab.up.railway.app` (sin `https://`).
3. **Activities → Settings:** habilitar **Enable Activities**.
4. **OAuth2 → Redirects:** añadir `https://127.0.0.1`, como indica la documentación oficial de Activities.
5. En **OAuth2**, conservar activado **Cliente público (Public Client)**; era el ajuste existente. El cliente usa `code_challenge` con `S256` y el backend intercambia el código con `code_verifier` y `client_id`, **sin Client Secret**.
6. En Railway Lab, mantener `DISCORD_ACTIVITY_WEB_ENABLED=1` y `PORT=8080`. No añadir `DISCORD_ACTIVITY_CLIENT_SECRET`; no modificar `main`, las credenciales actuales ni la aplicación oficial.

## Uso

`/setup → Mensajes → Crear mensaje` invoca `InteractionResponse.launch_activity()` (Discord API 2.6+). La Activity abre el formulario completo dentro de Discord: canal, texto, constructor de embed desplegable, fecha opcional, rol de aviso, recurrencia y confirmación.

La API se autentica vía OAuth2 de Discord y verifica membresía y `manage_guild`, permisos del canal y restricciones de menciones en **cada solicitud**. El envío inmediato utiliza `message_publish`; los programados utilizan `message_autofeeds.persist_schedule` y la SQLite existente. No se cambia el footer global: producción emplea nombre e icono del servidor; en Lab se muestra «El Heraldo's Labs 🧪». Sin secretos en el frontend.

## Límites y pendientes

- PKCE no requiere `DISCORD_ACTIVITY_CLIENT_SECRET`. La autorización real depende de que **Public Client**, Activities, URL Mapping y Redirect URI estén correctamente configurados en la aplicación de pruebas.
- No se considera validado dentro de Discord hasta probar el flujo con Activities habilitadas.
- El SDK oficial se suministra desde el mismo origen mediante una pasarela a una versión fijada del paquete `@discord/embedded-app-sdk`.
- No borrar configuraciones antiguas ni deshabilitar el control previo de Custodio. Si el chequeo externo de IA bloquea un despliegue, no supone un fallo de Crear mensaje.

## Referencias oficiales

- [Discord Embedded App SDK](https://discord.com/developers/docs/developer-tools/embedded-app-sdk) — `authorize()` admite `code_challenge` y `code_challenge_method: 'S256'`.
- [Discord OAuth2](https://discord.com/developers/docs/topics/oauth2) — autorización por código y recomendación de PKCE.
