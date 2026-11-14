"""--bench de resolubilidad (capacidad 003): secciones R1 a R5 de
specs/003-resolubilidad/contracts/bench.md.

- Generador de criptas sintéticas con llaves encadenadas (T046, FR-330): la
  cripta es una cadena de zonas; la puerta de la zona i a la i+1 pide la
  llave i, que está en la zona i. Cada llave abre una región entera y hay
  una ronda por llave: el peor caso de repetir el recorrido por llave.
- R1 a R3 miden el recorrido incremental (Verificador) frente a la
  alternativa ingenua (VerificadorIngenuo) y el límite de 200 ms
  (FR-331, FR-334, FR-335; principio VI).
- R4 compara el texto completo de las dos alternativas (FR-332).
- R5 mide la numeración de llaves (research D1).

No instancia la vista ni usa la red (FR-333); R2 lee la copia local de la
cripta publicada más grande, si existe. Los dict y list de este archivo son
el JSON del esqueleto y de la ubicación de las llaves, igual que el que
entrega el servicio, y las filas de las tablas (principio I).
"""

import hashlib
import json
import os
import random

from crypta.bench.medicion import cronometrar, formato_tiempo, medir, tabla
from crypta.estructuras.NumeracionLlaves import (NumeracionLlaves,
                                                  NumeracionPorInsercion)
from crypta.estructuras.Vector import Vector
from crypta.estructuras.ordenamiento import ordenar
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.UbicacionLlaves import leer_ubicaciones
from crypta.Modelo.Verificador import verificar
from crypta.Modelo.VerificadorIngenuo import verificar_ingenuo
from crypta.Vista.FormatoVerificacion import texto_resultado


SEMILLA = 2026
LIMITE_MS = 200          # principio VI: verificación de resolubilidad
COCIENTE_MAXIMO = 3      # FR-335: al duplicar, no más de 3 veces
CARPETA_COPIAS = "cache"
LLAVE_SALIDA = "itm_llave_salida"


# ======================================================================
# Generador (FR-330)
# ======================================================================

def id_llave(i):
    return f"itm_llave_{i:05d}"


class CriptaLlaves:
    """Cripta sintética de resolubilidad.

    `generales` (sala_inicial, sala_salida, llave_salida), `esqueleto` (JSON
    como el del servicio), `llaves_ordenadas` y `llaves_barajadas` (la misma
    respuesta de ubicación en orden de id y barajada con la semilla)."""

    def __init__(self, semilla, salas, llaves, resoluble=True):
        self.semilla = semilla
        self.llaves = max(2, llaves)
        self.resoluble = resoluble
        self._azar = random.Random(semilla)
        self._salidas = {}
        self._ubicaciones = []

        zonas = self.llaves + 1
        columnas = max(2, salas // (2 * zonas))
        self._columnas = columnas
        self._siguiente_id = 1
        self._zonas = [self._zona() for _ in range(zonas)]
        self._unir_zonas()
        self._ubicar_llaves()

        if not resoluble:
            self._romper()

        self.esqueleto = [{"id": id_sala, "nombre": f"Sala {id_sala}",
                           "salidas": self._salidas[id_sala]}
                          for id_sala in range(1, self._siguiente_id)]
        self.generales = {"id": f"sintetica-{semilla}", "sala_inicial": 1,
                          "sala_salida": self._sala_salida,
                          "llave_salida": LLAVE_SALIDA}

        ordenadas = Vector(len(self._ubicaciones))
        for entrada in self._ubicaciones:
            ordenadas.agregar(entrada)
        ordenar(ordenadas, clave=lambda entrada: entrada["id"])
        self.llaves_ordenadas = {"llaves": [ordenadas.obtener(i)
                                            for i in range(len(ordenadas))]}
        barajadas = list(self.llaves_ordenadas["llaves"])
        self._azar.shuffle(barajadas)
        self.llaves_barajadas = {"llaves": barajadas}

    # -- piezas ----------------------------------------------------------

    def _nueva_sala(self):
        id_sala = self._siguiente_id
        self._siguiente_id += 1
        self._salidas[id_sala] = {}
        return id_sala

    def _unir(self, x, dx, y, dy, **puerta):
        self._salidas[x][dx] = dict({"sala": y}, **puerta)
        self._salidas[y][dy] = dict({"sala": x}, **puerta)

    def _zona(self):
        """Dos filas de `columnas` salas: arriba unidas E-O (siempre de ida
        y vuelta), abajo también; entre filas, N-S abiertas, cerradas sin
        llave o sin vuelta (solo de arriba hacia abajo). Toda sala se
        alcanza desde la de arriba a la izquierda."""
        arriba = [self._nueva_sala() for _ in range(self._columnas)]
        abajo = [self._nueva_sala() for _ in range(self._columnas)]

        for fila in (arriba, abajo):
            for c in range(self._columnas - 1):
                self._unir(fila[c], "E", fila[c + 1], "O")

        for c in range(self._columnas):
            tipo = self._azar.random()

            if tipo < 0.6:
                self._unir(arriba[c], "S", abajo[c], "N")
            elif tipo < 0.8:
                self._unir(arriba[c], "S", abajo[c], "N", cerrada=True)
            else:
                self._salidas[arriba[c]]["S"] = {"sala": abajo[c]}

        return (arriba, abajo)

    def _unir_zonas(self):
        """La puerta de la zona i a la i+1 pide la llave i; la última, a
        `sala_salida`, pide `llave_salida`. Abajo, puertas distractoras que
        piden la llave i o una posterior: no abren la zona i+1 antes que la
        puerta de la cadena, pero agregan puertas bloqueadas a la frontera."""
        for i in range(len(self._zonas) - 1):
            arriba, abajo = self._zonas[i]
            arriba_sig, abajo_sig = self._zonas[i + 1]
            self._unir(arriba[-1], "E", arriba_sig[0], "O",
                       cerrada=True, llave=id_llave(i))

            if self._azar.random() < 0.5:
                self._unir(abajo[-1], "E", abajo_sig[0], "O", cerrada=True,
                           llave=id_llave(self._azar.randrange(
                               i, self.llaves)))

        self._sala_salida = self._nueva_sala()
        self._unir(self._zonas[-1][0][-1], "E", self._sala_salida, "O",
                   cerrada=True, llave=LLAVE_SALIDA)

    def _sala_de_zona(self, zona):
        arriba, abajo = self._zonas[zona]
        return self._azar.choice(arriba + abajo)

    def _ubicar(self, llave, sala):
        entrada = {"id": llave, "sala": sala}

        if self._azar.random() < 0.2:
            entrada["enemigo"] = f"e-{len(self._ubicaciones):05d}"

        self._ubicaciones.append(entrada)

    def _ubicar_llaves(self):
        for i in range(self.llaves):
            self._ubicar(id_llave(i), self._sala_de_zona(i))

        self._ubicar(LLAVE_SALIDA, self._sala_de_zona(self.llaves))

        # Llaves que ninguna puerta pide: rondas con varias llaves.
        for j in range(max(1, self.llaves // 10)):
            zona = self._azar.randrange(len(self._zonas))
            self._ubicar(f"itm_llave_extra_{j:04d}", self._sala_de_zona(zona))

    def _colgar(self, zona, columna, llave):
        """Una sala nueva debajo de la fila de abajo, detrás de una puerta
        que pide `llave`."""
        sala = self._nueva_sala()
        self._unir(self._zonas[zona][1][columna], "S", sala, "N",
                   cerrada=True, llave=llave)
        return sala

    def _romper(self):
        """La llave r queda detrás de su propia puerta, o en un ciclo de 2 o
        3 llaves, y hay una puerta que pide una llave sin ubicación."""
        r = self._azar.randrange(max(1, self.llaves // 2), self.llaves)
        propia = id_llave(r)
        self._ubicaciones = [u for u in self._ubicaciones if u["id"] != propia]
        largo = self._azar.choice((1, 2, 3))

        if largo == 1:
            self._ubicar(propia, self._sala_de_zona(r + 1))
        else:
            ciclo = [f"itm_llave_ciclo_{k}" for k in range(largo - 1)]
            # propia -> ciclo_0 -> ... -> propia
            self._ubicar(propia, self._colgar(r, 0, ciclo[0]))

            for k in range(len(ciclo)):
                if k + 1 < len(ciclo):
                    self._ubicar(ciclo[k],
                                 self._colgar(r - 1, 0, ciclo[k + 1]))
                else:
                    self._ubicar(ciclo[k], self._sala_de_zona(r + 1))

        self._colgar(r, 1, "itm_llave_perdida")

    @property
    def cantidad_salas(self):
        return len(self.esqueleto)

    def mapa(self):
        mapa = Mapa()
        mapa.cargar_desde_json(self.esqueleto)
        return mapa


def generar_cripta_llaves(semilla, salas, llaves, resoluble=True):
    """(datos generales, esqueleto, respuesta ordenada, respuesta
    barajada), deterministas por semilla (FR-330)."""
    cripta = CriptaLlaves(semilla, salas, llaves, resoluble)
    return (cripta.generales, cripta.esqueleto, cripta.llaves_ordenadas,
            cripta.llaves_barajadas)


def huella(generales, esqueleto, llaves):
    """Resumen de una cripta generada: salas, salidas y ubicaciones
    serializadas en orden (HU5-1)."""
    texto = json.dumps({"generales": generales, "esqueleto": esqueleto,
                        "llaves": llaves}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


# ======================================================================
# Medición
# ======================================================================

def texto_incremental(mapa, generales, llaves):
    """La verificación completa que mide FR-334: desde el esqueleto ya
    cargado y la ubicación en memoria hasta el texto."""
    return texto_resultado(verificar(mapa, generales,
                                     leer_ubicaciones(llaves, mapa)))


def texto_ingenuo(mapa, generales, llaves, ingenuo=verificar_ingenuo):
    return texto_resultado(ingenuo(mapa, generales,
                                   leer_ubicaciones(llaves, mapa)))


def _cripta(salas, llaves, resoluble, semilla=SEMILLA):
    cripta = CriptaLlaves(semilla, salas, llaves, resoluble)
    return cripta, cripta.mapa()


def _tamanos_r1(rapido):
    return ((60, 15), (120, 30)) if rapido else (
        (500, 125), (1000, 250), (2000, 500))


def ejecutar_ingenua(rapido=False):
    """R1 (FR-331): incremental frente a repetir el recorrido por llave."""
    filas = []
    tamanos = _tamanos_r1(rapido)

    for salas, llaves in tamanos:
        for resoluble in (True, False):
            cripta, mapa = _cripta(salas, llaves, resoluble)
            incremental = medir(lambda: texto_incremental(
                mapa, cripta.generales, cripta.llaves_barajadas), 3)
            # La ingenua del tamaño mayor, una sola vez (contracts/bench.md).
            repeticiones = 1 if (salas, llaves) == tamanos[-1] else 3
            ingenua = medir(lambda: texto_ingenuo(
                mapa, cripta.generales, cripta.llaves_barajadas), repeticiones)
            filas.append((str(cripta.cantidad_salas), str(llaves),
                          "sí" if resoluble else "no",
                          formato_tiempo(incremental), formato_tiempo(ingenua),
                          f"{ingenua / incremental:.1f}"))

    return tabla(
        "R1 RESOLUBILIDAD (FR-331): recorrido incremental frente a repetir "
        "el recorrido por llave",
        ("salas", "llaves", "resoluble", "incremental", "ingenua",
         "ingenua / incremental"),
        filas,
        "Mejor de 3 (la ingenua del tamaño mayor, una sola vez). Llaves "
        "encadenadas: una ronda por llave.")


def _percentil(valores, p):
    ordenados = Vector(len(valores))
    for valor in valores:
        ordenados.agregar(valor)
    ordenar(ordenados)
    indice = min(len(ordenados) - 1, int(round(p / 100 * (len(ordenados) - 1))))
    return ordenados.obtener(indice)


def _fila_limite(nombre, salas, llaves, esqueleto, generales, respuesta,
                 repeticiones):
    carga = []

    for _ in range(repeticiones):
        carga.append(cronometrar(lambda: Mapa().cargar_desde_json(esqueleto)))

    mapa = Mapa()
    mapa.cargar_desde_json(esqueleto)
    tiempos = []

    for _ in range(repeticiones):
        tiempos.append(cronometrar(
            lambda: texto_incremental(mapa, generales, respuesta)))

    media = sum(tiempos) / len(tiempos)
    maximo = max(tiempos)
    return (nombre, str(salas), str(llaves), formato_tiempo(media),
            formato_tiempo(_percentil(tiempos, 95)), formato_tiempo(maximo),
            formato_tiempo(sum(carga) / len(carga)),
            "sí" if maximo * 1000 < LIMITE_MS else "NO")


def copia_mas_grande(carpeta=None):
    """(id, datos) de la copia local con más salas que tenga la ubicación
    de las llaves, o None. Así R2 mide la cripta publicada más grande sin
    escribir su id en el código (principio IV)."""
    carpeta = carpeta if carpeta is not None else CARPETA_COPIAS

    if not os.path.isdir(carpeta):
        return None

    mejor = None

    for nombre in os.listdir(carpeta):
        if not nombre.endswith(".json") or nombre == "catalogo.json":
            continue

        try:
            with open(os.path.join(carpeta, nombre), encoding="utf-8") as archivo:
                datos = json.load(archivo)
        except (OSError, ValueError):
            continue

        if (not isinstance(datos, dict) or datos.get("llaves") is None
                or not datos.get("esqueleto") or not datos.get("datos_generales")):
            continue

        clave = (-len(datos["esqueleto"]), nombre)   # empate: por nombre

        if mejor is None or clave < mejor[2]:
            mejor = (nombre[:-len(".json")], datos, clave)

    return None if mejor is None else mejor[:2]


def ejecutar_limite(rapido=False, carpeta=None):
    """R2 (FR-334, SC-303): verificación completa < 200 ms con 2 000 salas
    y 500 llaves encadenadas, y con la cripta publicada más grande."""
    salas, llaves = (200, 50) if rapido else (2000, 500)
    repeticiones = 3 if rapido else 20
    filas = []

    for resoluble in (True, False):
        cripta = CriptaLlaves(SEMILLA, salas, llaves, resoluble)
        filas.append(_fila_limite(
            "sintética " + ("resoluble" if resoluble else "no resoluble"),
            cripta.cantidad_salas, llaves, cripta.esqueleto, cripta.generales,
            cripta.llaves_barajadas, repeticiones))

    oficial = copia_mas_grande(carpeta)
    nota = "La medición empieza con el esqueleto cargado y las llaves en " \
           "memoria (FR-334); la carga del esqueleto se reporta aparte, sin " \
           "límite. ¿cumple? mira el máximo."

    if oficial is None:
        nota += " No hay copia local de una cripta publicada con llaves."
    else:
        cripta_id, datos = oficial
        filas.append(_fila_limite(
            f"{cripta_id} (publicada)", len(datos["esqueleto"]),
            len(datos["llaves"].get("llaves") or ()), datos["esqueleto"],
            datos["datos_generales"], datos["llaves"], repeticiones))

    return tabla(
        f"R2 RESOLUBILIDAD (FR-334): límite de {LIMITE_MS} ms",
        ("cripta", "salas", "llaves", "media", "p95", "máximo",
         "cargar esqueleto", "¿cumple?"),
        filas, nota)


def ejecutar_crecimiento(rapido=False):
    """R3 (FR-335, SC-304): al duplicar el tamaño, el tiempo de la
    incremental no pasa de 3 veces el anterior."""
    if rapido:
        tamanos, con_ingenua = (50, 100, 200), (50, 100, 200)
    else:
        tamanos, con_ingenua = (500, 1000, 2000, 4000, 8000), (500, 1000, 2000)

    filas = []
    anterior_inc = anterior_ing = None
    cumple = True

    for salas in tamanos:
        llaves = salas // 4
        cripta, mapa = _cripta(salas, llaves, True)
        incremental = medir(lambda: texto_incremental(
            mapa, cripta.generales, cripta.llaves_barajadas), 3)
        cociente_inc = ("—" if anterior_inc is None
                        else f"{incremental / anterior_inc:.2f}")

        if anterior_inc is not None and incremental / anterior_inc > COCIENTE_MAXIMO:
            cumple = False

        anterior_inc = incremental

        if salas in con_ingenua:
            repeticiones = 1 if salas == con_ingenua[-1] else 3
            ingenua = medir(lambda: texto_ingenuo(
                mapa, cripta.generales, cripta.llaves_barajadas), repeticiones)
            texto_ing = formato_tiempo(ingenua)
            cociente_ing = ("—" if anterior_ing is None
                            else f"{ingenua / anterior_ing:.2f}")
            anterior_ing = ingenua
        else:
            texto_ing = cociente_ing = "—"

        filas.append((str(cripta.cantidad_salas), str(llaves),
                      formato_tiempo(incremental), cociente_inc, texto_ing,
                      cociente_ing))

    return tabla(
        "R3 RESOLUBILIDAD (FR-335): crecimiento al duplicar el tamaño",
        ("salas", "llaves", "incremental", "cociente", "ingenua", "cociente"),
        filas,
        f"¿cumple? (cociente de la incremental ≤ {COCIENTE_MAXIMO} en cada "
        f"duplicación): {'sí' if cumple else 'NO'}. Lo lineal da cerca de 2; "
        f"repetir el recorrido por llave, cerca de 4. La ingenua solo hasta "
        f"{con_ingenua[-1]} salas.")


def _criptas_igualdad(rapido):
    """Las criptas de los tamaños de R1 y 50 pequeñas variadas por semilla
    (las de 4 000 y 8 000 salas no: la ingenua tardaría minutos)."""
    criptas = []

    for salas, llaves in _tamanos_r1(rapido):
        for resoluble in (True, False):
            criptas.append((f"{salas} salas", CriptaLlaves(
                SEMILLA, salas, llaves, resoluble)))

    azar = random.Random(SEMILLA)

    for i in range(10 if rapido else 50):
        salas = azar.randint(20, 200)
        llaves = azar.randint(2, max(2, salas // 6))
        criptas.append((f"pequeña {i}", CriptaLlaves(
            SEMILLA + 1 + i, salas, llaves, resoluble=i % 2 == 0)))

    return criptas


def ejecutar_igualdad(rapido=False, ingenuo=verificar_ingenuo):
    """R4 (FR-332): el texto completo del verificador y el de la ingenua
    deben ser iguales. Devuelve (texto, errores)."""
    filas = []
    errores = []
    criptas = _criptas_igualdad(rapido)
    pequenas = 0

    for nombre, cripta in criptas:
        mapa = cripta.mapa()

        for orden, respuesta in (("ordenada", cripta.llaves_ordenadas),
                                 ("barajada", cripta.llaves_barajadas)):
            a = texto_incremental(mapa, cripta.generales, respuesta)
            b = texto_ingenuo(mapa, cripta.generales, respuesta, ingenuo)

            if a != b:
                errores.append(f"{nombre} ({orden}): el texto de la ingenua "
                               f"es distinto")

        if nombre.startswith("pequeña"):
            pequenas += 1
        else:
            filas.append((nombre, "sí" if cripta.resoluble else "no", "2"))

    filas.append((f"{pequenas} pequeñas", "mitad y mitad", str(2 * pequenas)))

    texto = tabla(
        "R4 RESOLUBILIDAD (FR-332): mismo resultado que la alternativa ingenua",
        ("criptas", "resoluble", "comparaciones"),
        filas,
        f"Total: {len(errores)} diferencias (texto completo: orden o reporte, "
        f"con la ubicación ordenada y barajada).")

    for error in errores[:20]:
        texto += f"\nERROR: {error}"

    return texto, len(errores)


def ejecutar_numeracion(rapido=False):
    """R5 (research D1): pasar del id de una llave a un número."""
    tamanos = (200, 500) if rapido else (500, 2000, 8000)
    maximo_ordenado = 500 if rapido else 2000
    filas = []

    for k in tamanos:
        ids = [id_llave(i) for i in range(k)]
        barajados = list(ids)
        random.Random(SEMILLA + k).shuffle(barajados)
        busquedas = Vector(2 * k)
        azar = random.Random(SEMILLA - k)

        for _ in range(2 * k):
            busquedas.agregar(ids[azar.randrange(k)])

        def medir_variante(clase, entrada):
            vector = Vector(k)
            for valor in entrada:
                vector.agregar(valor)
            hecha = []

            def correr():
                numeracion = clase(vector)
                for i in range(len(busquedas)):
                    numeracion.numero(busquedas.obtener(i))
                hecha.append(numeracion)

            tiempo = medir(correr, 3)
            return formato_tiempo(tiempo), str(hecha[-1].altura())

        filas.append((str(k), "ordenar + desde_ordenados", "ordenados",
                      *medir_variante(NumeracionLlaves, ids)))
        filas.append((str(k), "insertar", "barajados",
                      *medir_variante(NumeracionPorInsercion, barajados)))

        if k <= maximo_ordenado:
            filas.append((str(k), "insertar", "ordenados",
                          *medir_variante(NumeracionPorInsercion, ids)))
        else:
            filas.append((str(k), "insertar", "ordenados", "—", "—"))

    return tabla(
        "R5 RESOLUBILIDAD (research D1): id de llave → número",
        ("K", "construcción", "ids", "construir + 2K búsquedas", "altura"),
        filas,
        f"Con ids que llegan ordenados, insertar degenera en una lista (P1 "
        f"§4.4): O(K²); no se mide con más de {maximo_ordenado} ids. La tabla "
        f"hash queda como alternativa analizada, sin medir (research D1).")
