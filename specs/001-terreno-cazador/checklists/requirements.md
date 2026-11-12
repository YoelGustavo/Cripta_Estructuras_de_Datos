# Lista de calidad de la especificación: Terreno y cazador

**Propósito**: validar que la especificación está completa y tiene la calidad necesaria antes de planificar
**Creada**: 2026-11-07
**Capacidad**: [spec.md](../spec.md)

## Calidad del contenido

- [x] Sin detalles de implementación (lenguajes, bibliotecas, estructuras de datos, clases, módulos)
- [x] Centrada en el valor para el jugador y en las reglas del juego
- [x] Comprensible sin conocer el código
- [x] Todas las secciones obligatorias completas

## Completitud de los requisitos

- [x] No quedan marcas [NEEDS CLARIFICATION] — quedan 2, a propósito (FR-010 y FR-011), por pedido del grupo
- [x] Los requisitos se pueden probar y no son ambiguos (salvo los dos pendientes)
- [x] Los criterios de éxito son medibles
- [x] Los criterios de éxito no dependen de la tecnología
- [x] Todos los escenarios de aceptación están definidos y citan su FR
- [x] Los siete casos «Terreno y cazador» del Apéndice B aparecen como escenarios
- [x] Casos borde identificados
- [x] Alcance delimitado (niebla, «ir a», resolubilidad y línea de tiempo fuera)
- [x] Dependencias y supuestos identificados

## Preparación de la capacidad

- [x] Todos los requisitos funcionales tienen criterios de aceptación claros
- [x] Los escenarios cubren los flujos principales
- [x] La capacidad cumple los resultados medibles de los criterios de éxito
- [x] No se filtran detalles de implementación

## Notas

- Pendientes para `/speckit-clarify`:
  - FR-010: qué hace el programa con un costo inválido (< 1 o no entero) o distinto en cada sentido.
  - FR-011: qué hace el programa si la ficha de un cazador no trae rango.
- Correspondencia Apéndice B → escenarios: sin ruta → HU2-2; d > rango → HU2-3; menos salas y mayor
  costo → HU2-5; dos vecinas empatadas → HU2-6; puerta que se cierra → HU3-1; costo 1 con velocidad
  alta → HU1-4; cambio de velocidad → HU1-5.

## Validación de punta a punta (quickstart.md, tarea T096)

- [x] 1. `python -m unittest`: 766 pruebas en verde (1 omitida, la de la primera parte) (SC-001, SC-003).
- [x] 2. Pruebas de la capacidad: 82 en verde.
- [x] 3. Sin imports prohibidos en `crypta/`; las estructuras nuevas no usan `dict`, `set` ni `sorted` (T095).
- [x] 4. `TestCompatibilidadP1` en verde: la partida de la primera parte se repite igual (FR-008).
- [x] 5. Límites según `docs/resultados_bench_p2.txt`: B3 1.00 (< 2), B6 0 diferencias en 8160 decisiones, B7 p95 7.60 ms (< 20 ms), B8 0.89 (≤ 2) (SC-004, SC-005, SC-008). Sin vista ni red (prueba HU4-7). La repetibilidad con la misma semilla la comprueba la prueba HU4-1; el `--bench` todavía no imprime la huella.
- [ ] 6. Prueba manual en el juego: la hace el grupo (costos en la vista, `[cazador]`, salida cara, guardar y cargar).
