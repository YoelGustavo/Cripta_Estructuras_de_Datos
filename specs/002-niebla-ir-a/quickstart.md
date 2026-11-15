# Guía de validación: Niebla de guerra e «ir a»

Cómo comprobar de punta a punta que la capacidad funciona. Los detalles están en
[contracts/](contracts/) y [data-model.md](data-model.md).

## Requisitos

- Python 3.11 o superior, `requirements.txt` instalado.
- Para jugar sin red: una copia local en `cache/` (`--offline`).
- Las pruebas nunca usan `cache/`: arman criptas sintéticas y usan un `AlmacenDisco` en una carpeta
  temporal.

## 1. Pruebas automáticas

```text
python -m unittest
python -m unittest tests.test_niebla tests.test_ir_a tests.test_equivalencia_niebla
```

Resultado esperado: todo en verde, incluidas las pruebas de P1, 001, 003 y 004 (SC-207). Solo
cambian:

- las del formato del archivo de partida (3 → 4);
- la línea «Mapa conocido» del resumen (T057 de la 004);
- las que esperaban avisos de la bitácora sobre otras salas (FR-208).

Cada prueba ajustada lleva un comentario que cita FR-208 (si aplica) y SC-207. Las pruebas de
`--bench` usan una carpeta de copias vacía (sintética de 300 salas) y nunca leen `cache/`.

## 2. Niebla a mano (HU1, HU2)

1. `python -m crypta.main --offline …` y escribir `mapa`: aparece solo la sala inicial explorada y
   sus vecinas como avistadas (solo id).
2. `mover` a una vecina y `mapa` otra vez: esa sala pasa a explorada y sus destinos a avistados.
3. Esperar junto a una puerta con cierre automático: en la siguiente decisión la vista la muestra
   cerrada. Alejarse y volver: el mapa recuerda lo último que se vio.
4. `mapa 3` → comando inválido. `mapa` no cambia el reloj ni aparece en `partida.log`.
5. Encender una antorcha (`usar`) y entrar a una sala: sus vecinas quedan exploradas sin que sus
   enemigos despierten. Las solicitudes del reporte final son las mismas que sin antorcha.

## 3. «ir a» (HU3)

1. `ir a <sala avistada>` → «No conoces la sala …». `ir a 99999` → el mismo texto.
2. `ir a <sala explorada lejana>` → el jugador avanza paso a paso y la vista dice por qué se
   detuvo.
3. Abrir `partida.log`: una línea `# ir a <id>` seguida de un `mover` por paso.
4. `python -m crypta.main --replay partida.log` → la misma partida (mismo reloj, sala y vida).
5. `pergamino` después del viaje → se revierte solo el último paso.

## 4. Estado del juego (HU4)

1. Explorar, `guardar`, `cargar` y `mapa`: el mismo mapa conocido.
2. Intentar cargar un archivo del formato 3 (004) → «Formato incompatible …».
3. `historia <t>` de un instante en que una puerta se recordaba abierta → el resumen la muestra
   abierta aunque hoy se recuerde cerrada (T057 de la 004).

## 5. Medición (HU5)

```text
python -m crypta.bench.bench niebla_n1 niebla_n2 niebla_n3 niebla_n4 --guardar docs/resultados_bench_002.txt
```

Esperado: N1 y N2 con cociente ≤ 2 en la elegida; N3 con p95 < 5 ms en (a) y (c), el primer paso
reportado aparte y la fracción de pasos que buscaron; N4 con 0 diferencias. Una segunda ejecución
con la misma semilla da la misma huella. Si el primer paso o el p95 no cumplen en este equipo, va a
Límites de `DECISIONES.md` §5.3.
