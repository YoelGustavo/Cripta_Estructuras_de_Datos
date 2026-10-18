from crypta.estructuras.Cola import Cola

FORMATO_REGISTRO = 1

MARCA = "# CRIPTA registro de partida"
SEPARADOR = "---"


class ErrorRegistro(Exception):
    """El archivo no es un registro de partida válido (o es de otro formato)."""


class Encabezado:
    
    def __init__(self, cripta_id, version_cripta, version_catalogo, semilla,
                 jugador="", formato=FORMATO_REGISTRO):
        self.cripta_id = cripta_id
        self.version_cripta = version_cripta
        self.version_catalogo = version_catalogo
        self.semilla = semilla
        self.jugador = jugador
        self.formato = formato

    def __repr__(self):
        return (f"Encabezado({self.cripta_id}, cripta {self.version_cripta}, "
                f"catálogo {self.version_catalogo}, semilla {self.semilla})")


class RegistroPartida:
    
    def __init__(self, ruta):
        self.ruta = ruta

    @classmethod
    def crear(cls, ruta, encabezado):
        for valor in (encabezado.cripta_id, encabezado.version_cripta,
                      encabezado.version_catalogo, encabezado.jugador):
            _revisar_una_linea(str(valor))

        with open(ruta, "w", encoding="utf-8") as archivo:
            archivo.write(f"{MARCA}\n")
            archivo.write(f"formato {encabezado.formato}\n")
            archivo.write(f"cripta {encabezado.cripta_id}\n")
            archivo.write(f"version_cripta {encabezado.version_cripta}\n")
            archivo.write(f"version_catalogo {encabezado.version_catalogo}\n")
            archivo.write(f"semilla {encabezado.semilla}\n")
            archivo.write(f"jugador {encabezado.jugador}\n")
            archivo.write(f"{SEPARADOR}\n")

        return cls(ruta)

    def anotar(self, comando):
        _revisar_una_linea(comando)

        with open(self.ruta, "a", encoding="utf-8") as archivo:
            archivo.write(comando.strip() + "\n")


def leer_registro(ruta):
    try:
        archivo = open(ruta, encoding="utf-8")
    except OSError as error:
        raise ErrorRegistro(f"No se pudo abrir el registro {ruta}: {error}")

    with archivo:
        if archivo.readline().rstrip("\n") != MARCA:
            raise ErrorRegistro(f"{ruta} no es un registro de partida de CRIPTA")

        formato = cripta_id = version_cripta = version_catalogo = semilla = None
        jugador = ""

        while True:
            linea = archivo.readline()

            if linea == "":
                raise ErrorRegistro("El registro termina antes del separador '---'")

            linea = linea.rstrip("\n")

            if linea == SEPARADOR:
                break

            clave, _, valor = linea.partition(" ")

            if clave == "formato":
                formato = valor
            elif clave == "cripta":
                cripta_id = valor
            elif clave == "version_cripta":
                version_cripta = valor
            elif clave == "version_catalogo":
                version_catalogo = valor
            elif clave == "semilla":
                semilla = valor
            elif clave == "jugador":
                jugador = valor
            else:
                raise ErrorRegistro(f"Dato desconocido en el encabezado: '{clave}'")

        if formato != str(FORMATO_REGISTRO):
            raise ErrorRegistro(
                f"El registro es del formato {formato}; este programa lee el "
                f"formato {FORMATO_REGISTRO}"
            )

        for nombre, valor in (("cripta", cripta_id), ("version_cripta", version_cripta),
                              ("version_catalogo", version_catalogo), ("semilla", semilla)):
            if not valor:
                raise ErrorRegistro(f"Al encabezado le falta '{nombre}'")

        try:
            semilla = int(semilla)
        except ValueError:
            raise ErrorRegistro(f"La semilla no es un número: '{semilla}'")

        encabezado = Encabezado(cripta_id, version_cripta, version_catalogo,
                                semilla, jugador, int(formato))

        comandos = Cola()

        for linea in archivo:
            linea = linea.strip()

            if linea:
                comandos.encolar(linea)

    return encabezado, comandos


def _revisar_una_linea(texto):
    if "\n" in texto or "\r" in texto:
        raise ValueError("Un comando o dato del encabezado no puede tener saltos de línea")