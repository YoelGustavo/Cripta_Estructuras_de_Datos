# Checklist de calidad de la especificación: Línea de tiempo

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
- [x] Todos los escenarios de aceptación están definidos (incluye los 6 casos de «Línea de tiempo»
      del Apéndice B: HU1-2, HU2-1, HU1-3, HU1-8, HU3-2, HU4-3)
- [x] Casos borde identificados
- [x] Alcance delimitado (el mapa conocido lo define la 002)
- [x] Dependencias y supuestos identificados

## Preparación de la capacidad

- [x] Todo requisito funcional tiene criterios de aceptación claros
- [x] Las historias cubren los flujos principales (historia, pergamino, --replay --hasta,
      persistencia, puntos de control y --bench)
- [x] La capacidad cumple los resultados medibles de los criterios de éxito
- [x] No se filtran detalles de implementación

## Notas

- Numeración FR-401…FR-434 y SC-401…SC-408 para no chocar con la 001 ni la 003.
- Dependencia: el mapa conocido del resumen (FR-406) depende de la capacidad 002.
