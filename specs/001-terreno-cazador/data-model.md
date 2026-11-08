# Modelo de datos (fase 1): Terreno y cazador

**Capacidad**: 001 — `001-terreno-cazador` | **Plan**: [plan.md](plan.md) |
**Decisiones**: [research.md](research.md)

Se marca con **(nuevo)** lo que no existe hoy y con **(cambia)** lo que se modifica. «Estado del
juego» significa que se guarda en el archivo de partida y se revierte con el pergamino.

## Salida — `EstadoPuerta` compartido (cambia)

| Campo | Tipo | Estado del juego | Origen / regla |
|---|---|---|---|
| `cerrada` | bool | Sí | Igual que en P1. Pasa a ser propiedad: al cambiar de valor avisa al observador (si hay). |
| `llave` | texto o None | Sí (fijo) | Igual que en P1. |
| `cierre_automatico` | entero o None | Sí (fijo) | Igual que en P1. |
| `costo` **(nuevo)** | entero ≥ 1 | Sí (fijo; se guarda) | Esqueleto. Regla de FR-001/FR-010: ambos lados iguales, uno solo, o 100 si ninguno. |
| `extremos` **(nuevo)** | (Sala, Sala) | No | Lo arma `Mapa` al compartir puertas; sirve para saber si un cambio toca la región asentada (research D4). |
| `observador` **(nuevo)** | referencia o None | No | La búsqueda compartida vigente. |

`Puerta` expone `costo` como propiedad de solo lectura sobre su `EstadoPuerta`.

**Validación al cargar** (lanza `DatosInvalidos` con sala, dirección y problema):
- un lado declara `costo` que no es entero JSON (rechaza `bool`, `float` y texto) o es < 1;
- los dos lados declaran costos distintos.

## Sala (cambia)

| Campo | Tipo | Estado del juego | Regla |
|---|---|---|---|
| `indice` **(nuevo)** | entero 0..V−1 | No | Posición de la sala en el recorrido en orden del mapa. Fijo durante la partida. |
| `entradas` **(nuevo)** | `Vector` de (Puerta, Sala origen) | No | Salidas y→x de otras salas que llegan a esta. Se arma una vez al cargar; O(V + E). |

## Enemigo (cambia)

| Campo | Tipo | Estado del juego | Regla |
|---|---|---|---|
| `comportamiento` | texto | Sí (vía ficha) | Acepta `"cazador"` además de `"errante"` y `"rastreador"`. |
| `rango` **(nuevo)** | entero ≥ 0 o None | No se escribe; sale de la ficha | Solo para cazadores. Se toma de la ficha en `activar`; al cargar una partida se vuelve a leer de la ficha de la misma versión de catálogo. |

Transiciones (sin cambios respecto a P1 §2.4): dormido → activo al entrar el jugador a su sala; activo
→ muerto con vida 0. Los cazadores derrotados no deciden ni cuentan como «activos».

## Ficha de cazador (catálogo, solo lectura)

`{"id", "clase": "enemigo", "nombre", "vida_max", "ataque", "defensa", "velocidad",
"comportamiento": "cazador", "rango", "suelta"}`. Regla: `rango` presente, entero (no `bool`) y ≥ 0;
si no, `DatosInvalidos` (FR-011). El `dict` que entrega `json` solo se lee (principio I).

## Búsqueda de distancias limitada — `DistanciasLimitadas` (nuevo, en `crypta/estructuras`)

Estructura genérica sobre índices densos; no conoce `Sala` ni `Puerta`. Recibe la cantidad de nodos y
una función que recorre las entradas abiertas de un nodo como pares (nodo origen, costo).

| Campo | Tipo | Significado |
|---|---|---|
| `_dist` | `Vector` de V enteros | Distancia tentativa o definitiva. |
| `_marca` | `Vector` de V enteros | Id del cálculo en que se tocó el nodo; si no es el vigente, el valor no vale. |
| `_asentada` | `Vector` de V enteros | Id del cálculo en que se asentó el nodo. |
| `_frontera` | `MonticuloMin` de (dist, nodo) | Entradas pendientes; inserción perezosa. |
| `_calculo` | entero | Id del cálculo vigente; empezar de nuevo = sumarle 1. |
| `_origen` | entero o None | Nodo de origen del cálculo vigente. |
| `_hasta` | entero | Mayor distancia asentada (ρ). |
| contadores | enteros | Búsquedas iniciadas y nodos asentados (para `--bench`). |

Operaciones y complejidad:

| Operación | Complejidad |
|---|---|
| `reiniciar(origen)` | O(1) |
| `extender_hasta(limite, objetivo=None)` | O((ΔV + ΔE) log E_r) para lo nuevo que se asienta; se detiene al asentar `objetivo` o cuando el mínimo de la frontera supera `limite` |
| `distancia(nodo)` / `esta_asentada(nodo)` | O(1) |

## Búsqueda por cazador — `RutaPorCazador` (nuevo, en `crypta/estructuras`)

Misma idea, con etiqueta (distancia, primer paso) en orden lexicográfico y origen en la sala del
cazador; recorre salidas de ida. Solo para la alternativa medida en `--bench` (FR-031) y como
segundo verificador en las pruebas. Mismos `Vector` con marca.

## Perseguidor — reglas del cazador (nuevo, en `crypta/Modelo`)

Une el juego con las búsquedas. Tiene una `DistanciasLimitadas` compartida para la partida, recibe
los avisos de las puertas y decide.

| Operación | Regla |
|---|---|
| `decidir(cazador, sala_jugador)` | Devuelve una `Decision`, siguiendo research D3. Antes compara el origen guardado con `sala_jugador`; si difiere, reinicia. |
| `puerta_cambio(estado)` | Modo selectivo: invalida si algún extremo está asentado. Modo total: invalida siempre. Modo sin reutilización: no aplica (recalcula en cada decisión). |
| `invalidar()` | La llaman el pergamino y la creación de una partida cargada. |

## Decision (nuevo)

| Campo | Valores |
|---|---|
| `accion` | `atacar`, `esperar`, `mover` |
| `puerta` | La salida atravesada si `accion = mover`; si no, None |
| `costo` | 100 para atacar y esperar; `puerta.costo` para mover |

No usa el generador aleatorio (FR-021). El daño del ataque se tira después en `Partida`, como hoy.

## DatosInvalidos (nuevo, en `crypta/Modelo`)

Excepción propia, **no** hereda de `ValueError`, para que el `Controlador` no la confunda con un
comando inválido. Lleva un mensaje que nombra la salida o la ficha y el problema.

## Archivo de partida (cambia)

- `FORMATO_GUARDADO`: 1 → 2. Cada puerta escrita agrega `costo` (entero).
- No se agrega nada por cazador (sala, vida y evento ya se guardan como en cualquier enemigo; el rango
  sale de la ficha).
- Detalle en [contracts/guardado.md](contracts/guardado.md).
