# Modelo de datos: Verificación de resolubilidad

**Capacidad**: 003 — `003-resolubilidad` | **Plan**: [plan.md](plan.md) | **Decisiones**:
[research.md](research.md)

Nada de esto es estado del juego (FR-327): no se guarda en el archivo de partida, no va a
`partida.log` ni al historial de retroceso. Solo la respuesta de llaves se persiste, en la copia
local de la cripta (FR-323).

## Entidades de entrada

### UbicacionLlave (`crypta/Modelo/UbicacionLlaves.py`)

| Campo | Tipo | Regla (FR-319) |
|---|---|---|
| `id_llave` | `str` | obligatorio, texto no vacío |
| `id_sala` | `int` | obligatorio, entero (no `bool`), sala existente en el esqueleto |
| `indice_sala` | `int` | índice denso de esa sala en el `Mapa` (D2) |
| `enemigo` | `str` o None | opcional; si viene, texto |
| `numero_llave` | `int` | rango del id en la `NumeracionLlaves` (D1); lo asigna la verificación |

`leer_ubicaciones(respuesta_json, mapa) -> Vector[UbicacionLlave]`: valida toda la respuesta antes de
devolver nada; ante el primer problema lanza `DatosInvalidos` con la posición de la entrada, el id si
lo tiene y el motivo. Una misma llave puede tener varias entradas.

### Lo que usa del esqueleto (ya existe)

`Mapa` (`sala_por_indice`, `obtener_sala`, `cantidad_salas`), `Sala` (`indice`, `id`,
`obtener_puerta(d)` en N, S, E, O, `entradas`) y `Puerta` (`cerrada`, `llave`, `sala_destino_ref`),
más `sala_inicial`, `sala_salida` y `llave_salida` de los datos generales. Solo se leen.

## Estructuras

### NumeracionLlaves (`crypta/estructuras/NumeracionLlaves.py`) — decisión D1

- Se construye con un `Vector` de ids (con repetidos, en cualquier orden).
- Interno: `_ids` (`Vector` ordenado sin repetidos, número → id) y `_arbol`
  (`ArbolBusqueda.desde_ordenados` de pares (id, número)).
- `numero(id) -> int | None` en O(log K); `id_de(n) -> str` en O(1); `__len__`.
- Propiedad: `numero(a) < numero(b)` ⇔ `a < b` como texto.

Alternativa solo para el bench (R5), con la misma interfaz `numero`/`id_de`/`__len__`:
`NumeracionPorInsercion` (`ArbolBusqueda.insertar` en orden de llegada; expone `altura()` del
árbol). En ella el número es el orden de llegada. La tabla hash queda solo como alternativa
analizada en research D1, sin implementar.

### Recorrido (`crypta/Modelo/Verificador.py`) — decisiones D3, D4, D5

Estado interno de una verificación (se crea y se descarta en cada llamada):

| Nombre | Estructura | Tamaño | Significado |
|---|---|---|---|
| `ronda_sala` | `Vector[int]` | V | −1 fuera de la región; r = entró en la ronda r |
| `ronda_llave` | `Vector[int]` | K | −1 no obtenible (aún); r = obtenida en la ronda r |
| `abre` | `Vector[bool]` | K | la llave ya cruza puertas (se activa al cerrar su ronda) |
| `llaves_en_sala` | `Vector[Vector[int] \| None]` | V | números de llaves ubicadas en cada sala |
| `estacionadas` | `Vector[Vector[(int, int, int)] \| None]` | K | puertas (origen, dirección, destino) que esperan la llave |
| `pendientes` | `Cola[int]` | ≤ V | salas de la ronda (o del grupo de la capa) en curso |
| `nuevas` | `Vector[int]` | ≤ K | llaves obtenidas en la ronda en curso |
| `capa_sala`, `origen_sala` | `Vector[int]` | V | etiqueta (capa, origen) fuera de la región; −1 sin marcar |
| `dependencia` | `Vector[int]` | K | número de la llave de la que depende; −1 ninguna |
| `semillas` | `Vector[(int, int)]` | ≤ E | (origen, destino) de la capa siguiente; se ordena por origen |
| `estado_ciclo` | `Vector[int]` | K | 0/1/2 para la detección de ciclos |
| `inicio_ubic` | `Vector[int]` | K+1 | dónde empiezan las ubicaciones de cada llave en el vector ordenado |

Las direcciones se guardan como índice 0..3 de `DIRECCIONES` (N, S, E, O).

Transiciones de una sala: `fuera` → `en región (ronda r)` (D3) o `fuera` → `marcada (capa c,
origen k)` (D4, solo si no es resoluble). Ninguna vuelve atrás.

Transiciones de una llave: `sin obtener` → `obtenida en la ronda r` → `abre` (al cerrar la ronda r);
o `sin obtener` para siempre → con `dependencia` o sin ella, y quizá en un ciclo.

## Entidades de salida (`crypta/Modelo/ResultadoVerificacion.py`)

### ResultadoVerificacion

| Campo | Tipo | Cuándo |
|---|---|---|
| `resoluble` | `bool` | siempre |
| `rondas` | `Vector[Vector[str]]` | siempre (las rondas de llaves obtenibles); se muestra si es resoluble (FR-306) |
| `reporte` | `Reporte` o None | solo si no es resoluble |

### Reporte

| Campo | Tipo | FR |
|---|---|---|
| `falta_sala_salida`, `falta_llave_salida` | `bool` | FR-318 |
| `no_obtenibles` | `Vector[str]`, por id | FR-309 |
| `frontera` | `Vector[PuertaFrontera]`, por (id origen, N S E O) | FR-310 |
| `ubicaciones_frontera` | `Vector[(str, Vector[(int, str \| None)])]`, por id de llave; vector vacío = no está en la cripta | FR-311 |
| `dependencias` | `Vector[Dependencia]`, por id de la llave | FR-312, FR-314 |
| `ciclos` | `Vector[Vector[str]]`, cada uno desde su menor id, ordenados por esa llave | FR-315 |
| `salida_sin_puerta` | `bool` (llave_salida obtenible pero ninguna puerta que la pide lleva a sala_salida desde la región) | FR-317 |

### PuertaFrontera

`id_origen: int`, `direccion: str`, `id_destino: int`, `llave: str`.

### Dependencia

`llave: str`; `depende_de: str | None`; `motivo: None | "no está en la cripta" | "su sala no se
alcanza ni abriendo todas las puertas"` (solo cuando `depende_de` es None).

### NoVerificable (motivo de FR-324)

`motivo: str` (sin conexión y sin copia, falla de red, presupuesto agotado). Se trata como no
resoluble para decidir si inicia (FR-325) pero termina con código 1 (FR-329).

## Persistencia (copia local de la cripta)

El JSON de `cache/<cripta>.json` agrega un campo; el resto no cambia:

```json
{
  "version": "…",
  "esqueleto": [ … ],
  "contenidos": [ … ],
  "datos_generales": { … },
  "llaves": { "llaves": [ { "id": "itm_llave_bronce", "sala": 4 } ] }
}
```

`llaves` es la respuesta del servicio tal cual; vale mientras `version` coincida (FR-323). No cambia
el formato del archivo de partida (`FORMATO_GUARDADO` y `FORMATO_JSON` siguen igual).
