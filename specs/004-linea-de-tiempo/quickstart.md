# Guía de validación: Línea de tiempo

**Capacidad**: 004 — `004-linea-de-tiempo` | **Plan**: [plan.md](plan.md)

Cómo comprobar, de punta a punta, que la capacidad funciona. Los comandos se ejecutan desde la raíz
del repositorio.

## Requisitos previos

- Python 3.11 o superior y `pip install -r requirements.txt`.
- Para las pruebas sin conexión, la copia local en `cache/`.

## 1. Pruebas automatizadas

```text
python -m unittest
```

Tiene que pasar completo, incluidas las pruebas de P1, de la 001 y de la 003 (SC-408). Las de esta
capacidad:

- `tests/test_linea_tiempo.py`: HU1, HU2 y casos borde (plan.md, «Pruebas por FR»).
- `tests/test_equivalencia_linea.py`: SC-402. Al menos 20 partidas por semilla, con pergaminos,
  y K = 1, 10, 22 y el de la alternativa sin puntos de control; cada resumen se compara con el
  tomado de la partida viva mientras se jugaba.
- `tests/test_replay_hasta.py`: HU3.
- `tests/test_persistencia.py`: HU4 y el formato 3.

## 2. Consultar durante la partida

```text
python -m crypta.main --offline --semilla 7
```

Juega unas cuantas acciones y escribe:

- `historia 0`, `historia #1` y `historia #<n+1>`. El último da el mismo texto que el estado
  actual en los campos de FR-406.
- `historia <reloj+1>` y `historia #0`: se rechazan y nada cambia (`estado` muestra lo mismo).
- Usa un `pergamino` y repite `historia #<n>`: la numeración es la de las acciones que quedaron.

Al terminar, `partida.log` no tiene ninguna línea `historia` (FR-407).

## 3. Reproducir hasta un instante

```text
python -m crypta.main --replay partida.log --hasta 500
python -m crypta.main --replay partida.log --hasta 999999
python -m crypta.main --hasta 500
```

- El primero imprime el mismo texto que dio `historia 500` en la partida.
- El segundo imprime el último estado con su aviso y termina con código 0.
- El tercero es un error de argumentos.

## 4. Guardar y cargar

En una partida con historia, `guardar`, `historia #5`, `cargar` y otra vez `historia #5`: los dos
textos son iguales.

Cargar un archivo de formato 2 se rechaza con «formato incompatible». Al iniciar con
`--checkpoint-cada 7` y cargar una partida guardada con otro K, aparece el aviso de FR-418.

## 5. Medición

```text
python -m crypta.main --bench
```

Las secciones L1 a L8 (contracts/bench.md):

- L1: p95 < 50 ms con el K por defecto en la cripta del tamaño de la de referencia. La fila de
  escala se reporta sin límite.
- L3: 0 diferencias.
- L4: p95 del ciclo < 20 ms.
- L5: cocientes ≤ 2,5 y < 1/3.

Los resultados se guardan en `docs/resultados_bench_004.txt` y se citan en `DECISIONES.md` §5.5.
