# Modo Custodio — configuración de IA para laboratorio (2026-10-24)

## Estado actual confirmado
Se añadieron `custodio_ai_config.py` y `tests/test_custodio_ai_config.py` en `Pruebas`.
**Esto no instala Qwen, no descarga modelos ni cambia el /setup real.** Son contratos de configuración seguros y pruebas aisladas.

## Política decidida
- IA únicamente para proponer aclaraciones de **Server Rules ambiguas**.
- Activación del análisis **solo** al pulsar manualmente «Analizar reglas» en «Reglas del servidor».
- Reglas del servidor activas son requisito previo.
- Las sugerencias nunca modifican normas sin validación e incorporación administrativa.
- IA no accede a mensajes, perfiles, sanciones ni ejecuta moderación.
- Sin proveedor local verificado: opción **desactivada** y revisión humana.
- Honeypot y producción fuera del alcance.

## Configuración por defecto del contrato
`CustodioAIConfig(enabled=False, provider="none", model="", purpose="server_rule_ambiguity_only", trigger="administrator_manual_analyze_rules", require_human_approval=True, allow_messages=False, allow_user_profiles=False, allow_sanctions=False, allow_auto_rule_edit=False, allow_background_analysis=False)`.

Límites propuestos de prueba: 6000 caracteres por solicitud, timeout 30 segundos; ambos son topes de contrato, no garantías de latencia de un modelo no conectado.

## Pasos que faltan antes de considerarla configurada operacionalmente
1. Verificar memoria, CPU, almacenamiento y costo efectivo del entorno de prueba.
2. Evaluar un modelo abierto en equipo aislado con reglas ficticias en español, medir falsos positivos, respuestas y recursos.
3. Añadir adaptador de inferencia desacoplado con timeout, aislamiento, sin permisos disciplinarios y filtro de datos.
4. Conectar el disparador manual a «Reglas del servidor» y respuesta dentro del panel sin «Interaction failed».
5. Asegurar borradores Guardar/Descartar y que las propuestas no sean normas hasta aprobación.
6. Ejecutar tests, CI y validación humana con SHA de laboratorio; habilitar la IA solo entonces.

## Comandos de comprobación
```sh
python -m unittest discover -s tests -p 'test_custodio*.py' -v
python -m py_compile custodio_ai_config.py custodio_dry_run.py
```

**No se acreditan resultados de estos comandos sin una ejecución registrada.**
