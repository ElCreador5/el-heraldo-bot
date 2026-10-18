# H-03 — Contrato de controlador de despliegue para laboratorio

Fecha: 2026-10-17. Alcance: rama `Pruebas` exclusivamente.

## Objetivo y entregables

Preparar y probar la lógica de rechazo obligatorio antes de conectar respaldos H-03 con un publicador autorizado. Se implementaron `tools/h03_release_controller_contract.py` y `tests/test_h03_release_controller_contract.py`. El contrato es una pieza **offline y solo para laboratorio**: no contiene credenciales, accesos a Railway/GitHub, restablecimiento de SQLite ni mecanismos para desplegar producción. La prueba automática forma parte del descubrimiento habitual del CI de `Pruebas`.

La PR #18 de Codex permanece **en borrador**, sin fusionarse. Sus primitivas `preupdate_gate.guarded_update` y respaldos previos no están todavía integrados en `Pruebas` por el bloqueo de `DECISIONES.md`. Este contrato NO sustituye el controlador confiable obligatorio ni proporciona un status check H-03 productivo.

## Secuencia lógica validable

1. Rechazar todo entorno distinto de `lab`, formatos de SHA inválidos, candidatos idénticos y falta de adaptadores.
2. Consultar la revisión actual y exigir coincidencia con el origen antes de respaldar.
3. Exigir resultado exacto `verified_and_restored` de un adaptador que en integración real debe crear, descargar, autenticar y restaurar el respaldo de esa operación; revalidar SHA.
4. Invocar el adaptador confiable `guarded_update`, que debe repetir la verificación remota, consumir una autorización durable de un solo uso y ejecutar el callback bajo el bloqueo del almacenamiento.
5. Dentro del callback, comprobar otra vez origen, exigir publicación sincrónica confirmada y comprobar que el SHA realmente desplegado es el candidato.
6. Exigir exactamente una invocación del callback y revisar otra vez el SHA tras devolver el control. Toda desviación es bloqueo; ninguna respuesta de encolado basta.

**Limitación deliberada:** las funciones externas son adaptadores inyectados y simulados en tests. La correcta autenticación y resistencia a bypass requieren implementar y auditar dichos adaptadores dentro del servicio propietario del volumen, además de proteger las rutas directas de Railway y GitHub. Un resultado SUCCESS del CI o del contrato no equivale a esto.

## Pruebas

Comando: `python -m unittest discover -s tests -p 'test_h03_release_controller_contract.py' -v`.

Incluye 15 casos: ejecución simulada correcta; rechazo de producción; SHA e ID inválidos; cambio de origen antes/durante/después del respaldo; falta de adaptador; copia no verificada; controlador que no invoca el callback; resultado falso; mera aceptación asíncrona sin revisión desplegada; `True` no auténtico; callback reutilizado; cambio durante autorización; versión final incorrecta e IDs únicos.

La evidencia de CI debe registrarse por ejecución una vez terminada; **no se han efectuado interacciones de Discord**.

## Requisitos anteriores a cualquier activación en producción

- Mantener el bloqueo expreso y el aplazamiento de clave hasta noviembre o nueva autorización específica basada en recuperación independiente efectivamente probada.
- Terminar la verificación de la copia productiva real mediante descarga, descifrado y restauración en aislamiento; separar identidades y políticas de Supabase.
- Conectar un controlador confiable que incluya `preupdate_gate.guarded_update` y verifique el SHA final de GitHub y Railway; asegurar cumplimiento en TODAS las vías de despliegue, no solo PR.
- En `main`, exigir check H-03 obligatorio cuando su origen de confianza esté implementado; conservar revisión aprobatoria y `python-checks`. No alterar `sleepApplication`, secretos, `main` ni servicio productivo antes de autorizar y cumplir esas barreras.
