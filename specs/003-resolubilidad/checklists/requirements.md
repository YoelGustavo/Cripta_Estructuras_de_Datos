# Checklist de calidad de la especificación: Verificación de resolubilidad

**Propósito**: validar que la especificación está completa y tiene calidad antes de planificar
**Creada**: 2026-11-12
**Capacidad**: [spec.md](../spec.md)

## Calidad del contenido

- [x] Sin detalles de implementación (lenguajes, estructuras, clases, módulos)
- [x] Centrada en el valor para el jugador y en las reglas del juego
- [x] Redactada para quien no conoce el código
- [x] Todas las secciones obligatorias completas

## Completitud de los requisitos

- [x] No quedan marcadores [NEEDS CLARIFICATION]
- [x] Los requisitos son verificables y sin ambigüedad
- [x] Los criterios de éxito son medibles
- [x] Los criterios de éxito no dependen de la tecnología
- [x] Todos los escenarios de aceptación están definidos (incluye los 4 casos de «Resolubilidad»
      del Apéndice B: HU2-1, HU1-3, HU1-2, HU3-1)
- [x] Casos borde identificados
- [x] Alcance delimitado (sin niebla, «ir a» ni línea de tiempo)
- [x] Dependencias y supuestos identificados

## Preparación de la capacidad

- [x] Todo requisito funcional tiene criterios de aceptación claros
- [x] Las historias cubren los flujos principales (verificar, reportar, iniciar, --verificar, --bench)
- [x] La capacidad cumple los resultados medibles de los criterios de éxito
- [x] No se filtran detalles de implementación

## Notas

- Numeración FR-301…FR-335 y SC-301…SC-308 para no chocar con la 001.
- Pendiente: resolver el marcador de FR-303 antes de `/speckit-plan`.

## Validación de punta a punta (quickstart.md, tarea T056)

- [x] 1. `python -m unittest`: 849 pruebas en verde (1 omitida, la de la primera parte), incluidas
      las de P1 y la 001 (SC-301, SC-307). Pruebas de la capacidad: 83 en verde.
- [x] 2. `--verificar` en línea con las 5 criptas publicadas: cripta-02, 03, 04 y 06 dan código 0;
      cripta-05 da código 2 (ciclo `itm_llave_hierro -> itm_llave_negra -> itm_llave_hierro`). La
      copia local queda con `llaves` y su versión (HU4-1, HU4-2, HU4-5; FR-323). Lo hizo el grupo.
- [x] 3. `--offline --verificar`: mismo resultado sin solicitudes (HU3-6, FR-324). Lo hizo el grupo.
- [x] 4. Inicio de partida: no resoluble sin `--forzar` (código 2, sin `partida.log`), con
      `--forzar`, resoluble, sin conexión sin llaves y `--replay` de una partida forzada, en
      `tests/test_verificacion_inicio.py` (HU3-1 a HU3-11).
- [x] 5. `--bench` según `docs/resultados_bench_003.txt`: R2 máximo 123.00 ms con 2000 salas y 500
      llaves y 4.40 ms con cripta-06 (< 200 ms); R3 cocientes 2.04 a 2.24 (≤ 3); R4 0 diferencias
      (SC-302 a SC-304). Sin vista ni red (prueba HU5-6). La repetibilidad con la misma semilla la
      comprueba la prueba HU5-1.
- [x] 6. Sin imports prohibidos en `crypta/`; las estructuras nuevas no usan `dict`, `set` ni
      `sorted`; ningún id de llave en el código fuera de `crypta/bench` (T055).
