from crypta.Modelo.Inventario import Inventario


def mostrar(inventario):
    print("Orden real:")

    for objeto in inventario.orden_real():
        print(" -", objeto["nombre"])


def main():
    inventario = Inventario(3)

    antorcha = {
        "id": "itm_antorcha",
        "nombre": "Antorcha",
        "peso": 1,
        "valor": 5
    }

    daga = {
        "id": "itm_daga_oxidada",
        "nombre": "Daga oxidada",
        "peso": 2,
        "valor": 15
    }

    coraza = {
        "id": "itm_coraza_cuero",
        "nombre": "Coraza de cuero",
        "peso": 4,
        "valor": 20
    }

    pocion = {
        "id": "itm_pocion_menor",
        "nombre": "Poción menor",
        "peso": 1,
        "valor": 10
    }

    print("=== RECOGER ===")

    print("Antorcha:", inventario.recoger(antorcha))
    print("Daga:", inventario.recoger(daga))
    print("Coraza:", inventario.recoger(coraza))

    mostrar(inventario)

    print(
        "Cantidad:",
        len(inventario),
        "/",
        inventario.capacidad()
    )

    print("\n=== INVENTARIO LLENO ===")

    print(
        "Intentar recoger poción:",
        inventario.recoger(pocion)
    )

    print("\n=== NAVEGACIÓN ===")

    print("Actual:", inventario.actual()["nombre"])

    inventario.avanzar()
    print("Avanzar:", inventario.actual()["nombre"])

    inventario.avanzar()
    print("Avanzar:", inventario.actual()["nombre"])

    inventario.retroceder()
    print("Retroceder:", inventario.actual()["nombre"])

    print("\n=== EQUIPAR ===")

    print(
        "Equipando:",
        inventario.actual()["nombre"]
    )

    inventario.equipar_actual()

    mostrar(inventario)

    print("\n=== SOLTAR ACTUAL ===")

    soltado = inventario.soltar_actual()

    print("Soltado:", soltado["nombre"])

    mostrar(inventario)

    print(
        "Cantidad:",
        len(inventario),
        "/",
        inventario.capacidad()
    )

    print("\n=== RECOGER DESPUÉS DE LIBERAR ESPACIO ===")

    print(
        "Poción:",
        inventario.recoger(pocion)
    )

    mostrar(inventario)

    print("\n=== VISTAS ORDENADAS ===")

    for criterio in ("peso", "valor", "nombre"):

        vista, algoritmo = inventario.vista_ordenada(
            criterio
        )

        print(
            "\nOrdenado por",
            criterio,
            "- algoritmo:",
            algoritmo
        )

        for i in range(len(vista)):
            objeto = vista.obtener(i)

            print(
                objeto["nombre"],
                "- peso:",
                objeto["peso"],
                "- valor:",
                objeto["valor"]
            )

    print("\n=== ORDEN REAL DESPUÉS DE LAS VISTAS ===")

    mostrar(inventario)


if __name__ == "__main__":
    main()