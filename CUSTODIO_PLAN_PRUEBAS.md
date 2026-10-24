# Custodio — preparación segura para pruebas (24/10/2026)

## Alcance actual
- Rama de desarrollo: `Pruebas`. Producción (`main`) no debe alterarse.
- `tests/test_custodio_contract_spec.py`: verifica coherencia de once escenarios **de diseño**.
- `custodio_dry_run.py`: simulador de decisión **aislado** que falla de forma segura ante reglas ambiguas, inactivas, falta de permiso o exenciones.
- `tests/test_custodio_dry_run.py`: prueba el simulador sin Discord, SQLite, Railway ni modelos IA.

## Ejecutar localmente
Desde la raíz del repositorio:

```sh
python -m unittest tests/test_custodio_contract_spec.py tests/test_custodio_dry_run.py -v
python -m unittest discover -s tests -p 'test_custodio*.py' -v
```

No se necesitan tokens, base de datos, red ni permisos de Discord para estas pruebas. El test `test_live_custodio_engine_contract` está intencionalmente omitido hasta que exista integración real.

## Regla de seguridad
**No conectar este simulador al gateway ni al almacenamiento real.** Los resultados `Decision` son propuestas de prueba, no órdenes disciplinarias. No activar Modo Custodio en Lab basándose únicamente en estas pruebas.

## Puertas antes de pruebas reales
1. Identificar el motor de Custodio efectivamente implementado, si existe, y definir un adaptador solo-lectura para escenarios.
2. Probar persistencia central de Advertencias con SQLite temporal; comprobar idempotencia, anulación, vencimiento y estado cumplido sin tocar la SQLite del bot.
3. Probar permisos, exenciones, Server Rules activas, la doble advertencia autorizada y el comportamiento sin IA contextual.
4. Verificar ACK de todos los botones en `/setup` y su convivencia con estas rutas.
5. Ejecutar suite completa y CI al SHA exacto; luego aceptar manualmente en Discord Test sin sancionar personas reales.
6. Mantener Honeypot sin modificaciones y seguir NH.

## Estado honesto
Código del simulador y los tests versionados en `Pruebas`. Ninguna prueba del motor real, despliegue Test o interacción de Discord se acredita con este documento.
