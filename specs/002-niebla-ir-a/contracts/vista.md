# Contrato: lo que se muestra (FR-207 a FR-210, FR-221, FR-228)

Todo sale del mapa conocido y de lo que hay en la sala del jugador (FR-207, FR-209). Los textos los
arman funciones puras de `crypta/Vista`; `VistaConsola` solo los imprime.

## Vista de la sala (`mostrar_estado`)

Sin cambios de formato. La sección SALIDAS lee el estado de cada salida de `recordada`, no del
estado real:

```text
SALIDAS
  N: sala 3 (Cerrada, necesita itm_llave, costo 100)
  E: sala 4 (Abierta, costo 250)
```

- El destino se muestra solo por su id (FR-207).
- Como el jugador observa su sala antes de cada decisión (FR-204), en pantalla coincide con el
  estado real. Las pruebas de la 001 sobre este texto siguen valiendo.
- «necesita <llave>» se mantiene en las salidas cerradas con llave, como en P1 (FR-207).

## Mapa

`crypta/Vista/FormatoMapa.formatear_mapa(mapa_resumido)` → `str`, terminado en salto de línea.

```text
MAPA CONOCIDO (<E> exploradas, <A> avistadas)
Exploradas:
  <id> <nombre>
    <dir>: sala <destino>, costo <costo>, <abierta|cerrada>
    ...
  ...
Avistadas: <id>, <id>, ... | ninguna
```

Reglas:

- Exploradas y avistadas ordenadas por id (FR-210); las salidas en orden N, S, E, O.
- `<abierta|cerrada>` es el estado recordado. Una salida explorada siempre fue observada, así que
  nunca aparece «sin observar».
- Una sala avistada nunca muestra su nombre; una desconocida no aparece (FR-203).
- Los números van sin separador de miles.

## Motivos de parada

`crypta/Vista/FormatoMapa.texto_motivo(viaje)` (o en el mismo módulo de la vista):

| Motivo | Texto |
|---|---|
| `LLEGADA` | `Llegaste a la sala <id> en <n> pasos.` |
| `ENEMIGOS` | `El viaje se detuvo: hay enemigos en esta sala (<n> pasos).` |
| `DANIO` | `El viaje se detuvo: recibiste daño (<n> pasos).` |
| `SIN_RUTA` | `El viaje se detuvo: ya no conoces una ruta abierta hasta la sala <id> (<n> pasos).` |
| `PASO_IMPOSIBLE` | `El viaje se detuvo: no se pudo cargar la sala siguiente (<n> pasos). <detalle>` |
| `FIN_PARTIDA` | `El viaje terminó con la partida (<n> pasos).` |

## Bitácora (FR-208)

Solo lo que pasa en la sala del jugador o le pasa al jugador. El pergamino no borra los mensajes ya
mostrados, como en P1 (caso borde de la spec). Cambian tres avisos:

| Aviso | Antes | Ahora |
|---|---|---|
| «Una puerta se cierra automáticamente.» | siempre | solo si la puerta es una salida de la sala del jugador (alguna salida de la sala comparte su estado); una salida sin vuelta que llega a la sala del jugador no avisa |
| «<enemigo> regenera vida.» | siempre | solo si el enemigo está en la sala del jugador |
| «Una trampa vuelve a estar armada.» | siempre | solo si la trampa está en la sala del jugador |

## Resumen de `historia` y `--replay … --hasta` (capacidad 004, FR-406; FR-228; T057)

Reemplaza la línea fija «Mapa conocido: no disponible (capacidad 002)» de
`specs/004-linea-de-tiempo/contracts/resumen.md`:

```text
Mapa conocido: <E> exploradas, <A> avistadas
  <id> <nombre>
    <dir>: sala <destino>, costo <costo>, <abierta|cerrada>
  ...
  Avistadas: <id>, <id>, ... | ninguna
```

Son las mismas líneas de `formatear_mapa` sin su encabezado, con dos espacios más de sangría. Muestra
el mapa conocido **del estado consultado**, no el actual (HU1-11 de la 004, HU4-5 de esta). Al
implementar, se actualiza también `contracts/resumen.md` de la 004 y `tests/test_resumen.py`.

## Ayuda

`mostrar_ayuda` agrega:

```text
  mapa                Ver el mapa conocido
  ir a <sala>         Viajar a una sala explorada
```
