# Contrato: línea de comandos (FR-325 a FR-329)

## Banderas nuevas en `crypta/main.py`

| Bandera | Argumento | Efecto |
|---|---|---|
| `--verificar` | `CRIPTA` (id) | Solo verifica e imprime el resultado; no instancia la vista, no crea partida ni `partida.log` (FR-328). |
| `--forzar` | — | Al iniciar partida: si no es resoluble o no se pudo verificar, inicia igual (FR-325). Sin efecto con datos inválidos. |

Combinaciones: `--verificar` con `--offline` usa la copia local. `--verificar` con `--replay` o
`--bench` es error de uso (código 1, mismo estilo que `--bench` con `--replay`). `--forzar` se ignora
con `--replay` (que no verifica, FR-326) y con `--verificar`.

## Flujo del inicio de partida

1. Cargar la cripta (esqueleto: copia local o red) y fijar el presupuesto — como hoy.
2. Obtener la ubicación de las llaves: copia local con la misma versión, o `GET
   /criptas/<id>/llaves` (cuenta en el presupuesto). Si falla → «no se pudo verificar».
3. Validar la ubicación (FR-319). Si es inválida → mensaje, **código 1**, no inicia (ni con
   `--forzar`).
4. Verificar e imprimir el texto (contracts/reporte.md).
5. Decidir:
   - resoluble → seguir;
   - no resoluble o no verificable, sin `--forzar` → imprimir la línea de decisión, guardar la copia
     local si se está en línea, terminar con **código 2** (no resoluble) o **1** (no verificable),
     sin vista ni `partida.log`;
   - con `--forzar` → imprimir la línea de decisión y seguir.
6. Crear repositorio de fichas, partida, `partida.log`, vista y controlador — como hoy.

El mapa conocido (capacidad 002) no se toca en ningún paso.

## Códigos de salida

| Situación | Inicio de partida | `--verificar` |
|---|---|---|
| Resoluble | juega; código actual al terminar | 0 |
| No resoluble | 2 (sin `--forzar`) | 2 |
| No verificable (sin conexión sin copia, red, presupuesto) | 1 (sin `--forzar`) | 1 |
| Ubicación de llaves inválida | 1 (siempre) | 1 |
| Esqueleto inválido (001) | 1 | 1 |

## Sin verificación

- `--replay ARCHIVO`: no pide llaves, no verifica, no imprime nada de la verificación (FR-326).
- Cargar una partida guardada desde el juego: no verifica (FR-326).
- `--listar` y `--bench`: no cambian (el bench usa criptas sintéticas).
