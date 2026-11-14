# Guía de validación: Verificación de resolubilidad

**Capacidad**: 003 — `003-resolubilidad` | **Plan**: [plan.md](plan.md)

Cómo comprobar, una vez implementada, que la capacidad cumple la spec. No contiene implementación.

## Requisitos previos

- Python 3.11 o superior; dependencias de `requirements.txt` (sin agregar ninguna).
- Desde la raíz del repositorio.

## 1. Pruebas automatizadas

```text
python -m unittest
```

Todo en verde, incluidas las pruebas de P1 y de la 001 (SC-307). Las de esta capacidad citan su FR
(lista en [plan.md](plan.md#pruebas-por-fr)):

```text
python -m unittest tests.test_resolubilidad tests.test_equivalencia_resolubilidad tests.test_numeracion_llaves tests.test_verificacion_inicio
```

Esperado: los escenarios HU1 a HU5 pasan; la comparación con la alternativa ingenua sobre ≥ 200
criptas por semilla da 0 diferencias y cada orden se puede seguir paso a paso (SC-302).

## 2. `--verificar` contra el servicio

```text
python -m crypta.main --verificar cripta-01
echo %ERRORLEVEL%        (PowerShell: $LASTEXITCODE)
```

Esperado: imprime el texto de [contracts/reporte.md](contracts/reporte.md); código 0 si es
resoluble, 2 si no. No aparece la vista; `partida.log` no cambia (comparar fecha antes y después).
`cache/cripta-01.json` queda con el campo `llaves` y la misma `version`.

Repetir el comando: no hace una segunda solicitud de llaves (SC-306); el texto es idéntico
(guardar ambas salidas y compararlas con `fc` o `Compare-Object`, SC-305).

## 3. Sin conexión

```text
python -m crypta.main --offline --verificar cripta-01
```

Con la copia local del paso 2: mismo texto, ninguna solicitud. Con una cripta cuya copia no tenga
`llaves`: aviso «no se pudo verificar» y código 1.

## 4. Inicio de partida

- Cripta no resoluble sin `--forzar`: se muestra el reporte, la línea «La partida no inicia…», no
  se crea `partida.log`, código 2 (Apéndice B).
- La misma con `--forzar`: reporte, «Se inicia la partida por --forzar.», la partida empieza y las
  salas del reporte siguen desconocidas en el mapa conocido.
- Cripta resoluble: se muestra el orden por rondas y la partida empieza.
- `--replay partida.log` de la partida forzada: no muestra nada de la verificación y da la misma
  partida.

Las criptas no resolubles para probar a mano se arman en `tests/` con las ayudas de
`tests/ayudas_cripta.py`; las del servicio cambian de versión.

## 5. Medición

```text
python -m crypta.main --bench
```

En las secciones R1–R5 ([contracts/bench.md](contracts/bench.md)):

- R2: verificación de 2 000 salas y 500 llaves < 200 ms → «¿cumple? sí».
- R3: cocientes de la incremental ≤ 3; la ingenua muestra el crecimiento mayor.
- R4: 0 diferencias; el `--bench` termina con código 0.
- Dos ejecuciones: las huellas de las criptas sintéticas son iguales.

Los números van a la sección «Resolubilidad» de `DECISIONES.md`, que dice si la decisión final
coincide con [research.md](research.md).
