import unittest
 
from crypta.Modelo.Actor import Actor
from crypta.Modelo.Enemigo import Enemigo
from crypta.Modelo.Mapa import Mapa
from crypta.Modelo.Sala import Sala
 
 
def ficha_rata():
    # La misma ficha de ejemplo del §3.3.
    return {"id": "ent_rata_gigante", "clase": "enemigo", "nombre": "Rata gigante",
            "vida_max": 12, "ataque": 5, "defensa": 1, "velocidad": 150,
            "comportamiento": "rastreador", "suelta": ["itm_pocion_menor"]}
 
 
def ids(vector):
    return [vector.obtener(i).id_instancia for i in range(len(vector))]
 
 
def contenido_sala_2():
    # El ejemplo de /contenido del §3.3 (la sala 2 con dos ratas).
    return {"sala": 2,
            "enemigos": [{"instancia": "e-202", "tipo": "ent_rata_gigante", "vida": 12},
                         {"instancia": "e-201", "tipo": "ent_rata_gigante", "vida": 7}],
            "objetos": ["itm_daga_oxidada"],
            "trampas": [{"instancia": "t-17", "tipo": "trp_dardos"}]}
 
 
# ----------------------------------------------------------------------
# Actor.intervalo (§2.3)
# ----------------------------------------------------------------------
 
class TestIntervalo(unittest.TestCase):
    def test_ejemplos_del_enunciado(self):
        self.assertEqual(Actor("a", 100).intervalo(100), 100)
        self.assertEqual(Actor("b", 150).intervalo(100), 66)
 
    def test_siempre_es_entero(self):
        resultado = Actor("b", 150).intervalo(100)
        self.assertIsInstance(resultado, int)      # 66, no 66.666...
 
    def test_otros_costos(self):
        self.assertEqual(Actor("a", 100).intervalo(25), 25)    # recoger
        self.assertEqual(Actor("a", 100).intervalo(50), 50)    # equipar
        self.assertEqual(Actor("c", 80).intervalo(50), 62)     # 5000 // 80
 
    def test_minimo_es_1(self):
        self.assertEqual(Actor("rapido", 100000).intervalo(25), 1)
 
    def test_sin_velocidad_falla(self):
        with self.assertRaises(ValueError):
            Actor("roto", 0).intervalo(100)
        with self.assertRaises(ValueError):
            Enemigo("e-1", "ent_rata_gigante").intervalo(100)   # dormido
 
 
# ----------------------------------------------------------------------
# Enemigo
# ----------------------------------------------------------------------
 
class TestEnemigoDormido(unittest.TestCase):
    def test_nace_dormido(self):
        rata = Enemigo("e-201", "ent_rata_gigante", 12)
        self.assertFalse(rata.esta_activo())
        self.assertTrue(rata.esta_vivo())
        self.assertEqual(rata.velocidad, 0)
        self.assertIsNone(rata.comportamiento)
        self.assertEqual(rata.objetos_que_suelta(), ())
 
    def test_es_un_actor(self):
        self.assertIsInstance(Enemigo("e-1", "ent_rata_gigante"), Actor)
 
    def test_no_se_puede_herir_dormido(self):
        with self.assertRaises(RuntimeError):
            Enemigo("e-1", "ent_rata_gigante").recibir_danio(3)
 
 
class TestActivar(unittest.TestCase):
    def test_copia_la_ficha(self):
        rata = Enemigo("e-201", "ent_rata_gigante")
        rata.activar(ficha_rata())
        self.assertTrue(rata.esta_activo())
        self.assertEqual(rata.nombre, "Rata gigante")
        self.assertEqual((rata.vida, rata.vida_max), (12, 12))
        self.assertEqual((rata.ataque, rata.defensa, rata.velocidad), (5, 1, 150))
        self.assertEqual(rata.comportamiento, "rastreador")
        self.assertEqual(rata.intervalo(100), 66)    # §2.4: activada en 0 -> 66
 
    def test_vida_inicial_menor(self):
        rata = Enemigo("e-201", "ent_rata_gigante", vida_inicial=7)
        rata.activar(ficha_rata())
        self.assertEqual((rata.vida, rata.vida_max), (7, 12))
 
    def test_vida_inicial_nunca_supera_vida_max(self):
        rata = Enemigo("e-201", "ent_rata_gigante", vida_inicial=50)
        rata.activar(ficha_rata())
        self.assertEqual(rata.vida, 12)
 
    def test_ficha_de_otro_tipo_falla(self):
        rata = Enemigo("e-201", "ent_rata_gigante")
        otra = ficha_rata()
        otra["id"] = "ent_guardian_oseo"
        with self.assertRaises(ValueError):
            rata.activar(otra)
        self.assertFalse(rata.esta_activo())
 
    def test_ficha_que_no_es_enemigo_falla(self):
        daga = Enemigo("e-9", "itm_daga_oxidada")
        with self.assertRaises(ValueError):
            daga.activar({"id": "itm_daga_oxidada", "clase": "arma", "peso": 2})
 
    def test_activar_dos_veces_no_cura(self):
        """Uno que ya estaba activo (p. ej. llegó caminando) no se reinicia."""
        rata = Enemigo("e-201", "ent_rata_gigante")
        rata.activar(ficha_rata())
        rata.recibir_danio(5)
        rata.activar(ficha_rata())
        self.assertEqual(rata.vida, 7)
 
    def test_ficha_sin_comportamiento_ni_suelta(self):
        ficha = ficha_rata()
        del ficha["comportamiento"], ficha["suelta"]
        rata = Enemigo("e-201", "ent_rata_gigante")
        rata.activar(ficha)
        self.assertIsNone(rata.comportamiento)
        self.assertEqual(rata.objetos_que_suelta(), ())
 
    def test_suelta(self):
        rata = Enemigo("e-201", "ent_rata_gigante")
        rata.activar(ficha_rata())
        self.assertEqual(list(rata.objetos_que_suelta()), ["itm_pocion_menor"])
 
    def test_desactivar_para_deshacer(self):
        rata = Enemigo("e-201", "ent_rata_gigante", vida_inicial=7)
        rata.activar(ficha_rata())
        rata.asignar_evento("evento")
        rata.desactivar()
        self.assertFalse(rata.esta_activo())
        self.assertIsNone(rata.evento_siguiente)
        rata.activar(ficha_rata())                 # al reactivarlo queda igual
        self.assertEqual(rata.vida, 7)
 
 
class TestVida(unittest.TestCase):
    def setUp(self):
        self.rata = Enemigo("e-201", "ent_rata_gigante", vida_inicial=7)
        self.rata.activar(ficha_rata())
 
    def test_danio_y_muerte(self):
        self.rata.recibir_danio(5)
        self.assertEqual(self.rata.vida, 2)
        self.assertTrue(self.rata.esta_vivo())
        self.rata.recibir_danio(10)
        self.assertEqual(self.rata.vida, 0)        # no queda negativa
        self.assertFalse(self.rata.esta_vivo())
 
    def test_curar_tope_vida_max(self):
        self.rata.curar(100)
        self.assertEqual(self.rata.vida, 12)
 
    def test_negativos_fallan(self):
        with self.assertRaises(ValueError):
            self.rata.recibir_danio(-1)
        with self.assertRaises(ValueError):
            self.rata.curar(-1)
 
    def test_dos_ratas_son_independientes(self):
        """§2.2: comparten ficha, pero cada una tiene su propia vida."""
        ficha = ficha_rata()
        a, b = Enemigo("e-201", "ent_rata_gigante"), Enemigo("e-202", "ent_rata_gigante")
        a.activar(ficha)
        b.activar(ficha)
        a.recibir_danio(4)
        self.assertEqual((a.vida, b.vida), (8, 12))
        self.assertEqual(ficha["vida_max"], 12)    # la ficha no se tocó
 
 
# ----------------------------------------------------------------------
# Sala con enemigos
# ----------------------------------------------------------------------
 
class TestSalaEnemigos(unittest.TestCase):
    def test_sala_nueva_sin_enemigos(self):
        sala = Sala(1, "Celda", None)
        self.assertEqual(sala.cantidad_enemigos(), 0)
        self.assertEqual(len(sala.enemigos_dormidos()), 0)
 
    def test_contenido_crea_enemigos_dormidos(self):
        sala = Sala(2, "Pasillo", None)
        sala.asignar_contenido(contenido_sala_2())
        self.assertEqual(sala.cantidad_enemigos(), 2)
        for i in range(2):
            enemigo = sala.enemigo_en(i)
            self.assertIsInstance(enemigo, Enemigo)
            self.assertFalse(enemigo.esta_activo())      # §2.4: cargar no activa
            self.assertEqual(enemigo.sala_actual, 2)
        self.assertEqual(sala.cantidad_objetos(), 1)
        self.assertEqual(sala.cantidad_trampas(), 1)
 
    def test_contenido_sin_listas(self):
        """Las listas pueden no venir en el JSON."""
        sala = Sala(3, "Vacía", None)
        sala.asignar_contenido({"sala": 3})
        self.assertTrue(sala.contenido_cargado())
        self.assertEqual(sala.cantidad_enemigos(), 0)
 
    def test_vida_inicial_del_contenido(self):
        sala = Sala(2, "Pasillo", None)
        sala.asignar_contenido(contenido_sala_2())
        e201 = sala.enemigos_dormidos().obtener(0)
        e201.activar(ficha_rata())
        self.assertEqual(e201.vida, 7)
 
    def test_dormidos_en_orden_de_id(self):
        sala = Sala(2, "Pasillo", None)
        sala.asignar_contenido(contenido_sala_2())     # vienen e-202, e-201
        self.assertEqual(ids(sala.enemigos_dormidos()), ["e-201", "e-202"])
 
    def test_dormidos_no_incluye_activos(self):
        sala = Sala(2, "Pasillo", None)
        sala.asignar_contenido(contenido_sala_2())
        sala.enemigos_dormidos().obtener(0).activar(ficha_rata())     # e-201
        self.assertEqual(ids(sala.enemigos_dormidos()), ["e-202"])
 
    def test_enemigo_que_llega_antes_del_contenido(self):
        """§2.4: una sala puede tener a la vez dormidos y activos que llegaron.
        Los del contenido quedan delante del que llegó caminando."""
        errante = Enemigo("e-900", "ent_rata_gigante")
        errante.activar(ficha_rata())
        sala = Sala(2, "Pasillo", None)
        sala.agregar_enemigo(errante)                  # llegó caminando
        sala.asignar_contenido(contenido_sala_2())     # luego llega el contenido
        self.assertEqual(sala.cantidad_enemigos(), 3)
        self.assertIs(sala.enemigo_en(2), errante)     # no se borró
        self.assertEqual(ids(sala.enemigos_dormidos()), ["e-201", "e-202"])

    def test_el_orden_no_depende_de_cuando_llega_el_contenido(self):
        """§4.11: al jugar, el contenido llega cuando llega; al reproducir,
        quizá desde una copia local. El orden de la sala debe ser el mismo."""
        def errante():
            enemigo = Enemigo("e-900", "ent_rata_gigante")
            enemigo.activar(ficha_rata())
            return enemigo

        antes = Sala(2, "Pasillo", None)
        antes.asignar_contenido(contenido_sala_2())    # el contenido primero...
        antes.agregar_enemigo(errante())               # ...y luego llega caminando

        despues = Sala(2, "Pasillo", None)
        despues.agregar_enemigo(errante())             # llega caminando...
        despues.asignar_contenido(contenido_sala_2())  # ...y luego el contenido

        orden = ["e-202", "e-201", "e-900"]
        self.assertEqual([antes.enemigo_en(i).id_instancia for i in range(3)], orden)
        self.assertEqual([despues.enemigo_en(i).id_instancia for i in range(3)], orden)
        for i in range(3):
            self.assertEqual(despues.enemigo_en(i).sala_actual, 2)
 
    def test_contenido_dos_veces_no_duplica(self):
        sala = Sala(2, "Pasillo", None)
        sala.asignar_contenido(contenido_sala_2())
        sala.quitar_objeto(0)                          # el jugador recogió la daga
        sala.asignar_contenido(contenido_sala_2())     # llega una respuesta tarde
        self.assertEqual(sala.cantidad_enemigos(), 2)
        self.assertEqual(sala.cantidad_objetos(), 0)   # la daga no revive
 
    def test_quitar_por_identidad(self):
        """Dos ratas del mismo tipo: se quita la que es, no la primera igual."""
        sala = Sala(2, "Pasillo", None)
        sala.asignar_contenido(contenido_sala_2())
        segunda = sala.enemigo_en(1)
        posicion = sala.quitar_enemigo(segunda)
        self.assertEqual(posicion, 1)
        self.assertEqual(sala.cantidad_enemigos(), 1)
        self.assertIsNot(sala.enemigo_en(0), segunda)
 
    def test_quitar_e_insertar_deshace(self):
        sala = Sala(2, "Pasillo", None)
        sala.asignar_contenido(contenido_sala_2())
        primera = sala.enemigo_en(0)
        posicion = sala.quitar_enemigo(primera)
        sala.insertar_enemigo(posicion, primera)
        self.assertIs(sala.enemigo_en(0), primera)
        self.assertEqual(sala.cantidad_enemigos(), 2)
 
    def test_quitar_uno_que_no_esta_falla(self):
        with self.assertRaises(ValueError):
            Sala(1, "Celda", None).quitar_enemigo(Enemigo("e-1", "ent_rata_gigante"))
 
    def test_mover_enemigo_entre_salas(self):
        origen, destino = Sala(1, "A", None), Sala(2, "B", None)
        rata = Enemigo("e-201", "ent_rata_gigante")
        origen.agregar_enemigo(rata)
        origen.quitar_enemigo(rata)
        destino.agregar_enemigo(rata)
        self.assertEqual(rata.sala_actual, 2)
        self.assertEqual((origen.cantidad_enemigos(), destino.cantidad_enemigos()), (0, 1))
 
 
class TestMapaConEnemigos(unittest.TestCase):
    def test_asignar_contenidos_del_mapa(self):
        mapa = Mapa()
        mapa.cargar_desde_json([
            {"id": 1, "nombre": "Entrada", "salidas": {"E": {"sala": 2}}},
            {"id": 2, "nombre": "Pasillo", "salidas": {"O": {"sala": 1}}},
        ])
        mapa.asignar_contenidos([{"sala": 1}, contenido_sala_2()])
        self.assertEqual(mapa.obtener_sala(1).cantidad_enemigos(), 0)
        self.assertEqual(ids(mapa.obtener_sala(2).enemigos_dormidos()), ["e-201", "e-202"])
 
 
if __name__ == "__main__":
    unittest.main()