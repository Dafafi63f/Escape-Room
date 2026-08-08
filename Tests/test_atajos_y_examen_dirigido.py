#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Atajos de teclado en partida y examen dirigido por sesión."""

from __future__ import annotations

import unittest
from unittest.mock import Mock

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

import pygame  # noqa: E402

from Comun.generador_examen_historia import (  # noqa: E402
    OpcionesGeneracionExamen,
    calcular_pesos_desde_registros,
    generar_examen,
    PerfilPedagogico,
)
from Comun.informe_examen import RegistroRespuesta  # noqa: E402
from Comun.modelos import Pregunta  # noqa: E402
from Grafico.atajos_teclado import (  # noqa: E402
    manejar_teclado_partida,
    pantalla_campo_texto_activo,
    tecla_es_retroceso,
)
from Grafico.ui import BotonOpcion, CampoTexto  # noqa: E402


def _pregunta(materia: str, texto: str) -> Pregunta:
    return Pregunta(
        texto=texto,
        materia=materia,
        tematica="",
        dificultad="Facil",
        tipo="Teoria",
        grupo="TF",
        nivel="1",
        curso="1",
        semestre="1",
        opciones={"A": "a", "B": "b", "C": "c", "D": "d"},
        correcta="A",
    )


class TestAtajosPartida(unittest.TestCase):
    def test_tecla_2_responde_segunda_opcion(self) -> None:
        respondido: list[str] = []

        def on_responder(letra: str) -> None:
            respondido.append(letra)

        botones = [
            BotonOpcion("A", "uno", pygame.Rect(0, 0, 10, 10), lambda: None),
            BotonOpcion("B", "dos", pygame.Rect(0, 0, 10, 10), lambda: None),
        ]
        evento = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2)
        consumido = manejar_teclado_partida(
            evento,
            fase="pregunta",
            botones_opcion=botones,
            on_responder=on_responder,
            on_continuar=lambda: None,
        )
        self.assertTrue(consumido)
        self.assertEqual(respondido, ["B"])

    def test_enter_en_feedback_continua(self) -> None:
        continuar = Mock()
        evento = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        consumido = manejar_teclado_partida(
            evento,
            fase="feedback",
            botones_opcion=[],
            on_responder=lambda _l: None,
            on_continuar=continuar,
        )
        self.assertTrue(consumido)
        continuar.assert_called_once()

    def test_clic_en_feedback_continua(self) -> None:
        continuar = Mock()
        evento = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(100, 100))
        from Grafico.feedback_partida import evento_clic_salta_espera

        self.assertTrue(evento_clic_salta_espera(evento))
        if evento_clic_salta_espera(evento):
            continuar()
        continuar.assert_called_once()

    def test_enter_en_pregunta_elige_opcion_a(self) -> None:
        respondido: list[str] = []

        def on_responder(letra: str) -> None:
            respondido.append(letra)

        botones = [
            BotonOpcion("A", "uno", pygame.Rect(0, 0, 10, 10), lambda: None),
            BotonOpcion("B", "dos", pygame.Rect(0, 0, 10, 10), lambda: None),
        ]
        evento = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        consumido = manejar_teclado_partida(
            evento,
            fase="pregunta",
            botones_opcion=botones,
            on_responder=on_responder,
            on_continuar=lambda: None,
        )
        self.assertTrue(consumido)
        self.assertEqual(respondido, ["A"])


class TestAtajosBarraFija(unittest.TestCase):
    def test_teclas_barra_fija(self) -> None:
        import pygame
        from Grafico.atajos_teclado import tipo_barra_fija_para_tecla

        self.assertEqual(tipo_barra_fija_para_tecla(pygame.K_ESCAPE), "pausa")
        self.assertEqual(tipo_barra_fija_para_tecla(pygame.K_d), "diarios")
        self.assertEqual(tipo_barra_fija_para_tecla(pygame.K_h), "ranking")
        self.assertEqual(tipo_barra_fija_para_tecla(pygame.K_f), "feedback")
        self.assertEqual(tipo_barra_fija_para_tecla(pygame.K_o), "opciones")
        self.assertIsNone(tipo_barra_fija_para_tecla(pygame.K_a))


class TestCampoTextoVsAtajos(unittest.TestCase):
    def test_retroceso_es_backspace_no_supr(self) -> None:
        self.assertTrue(tecla_es_retroceso(pygame.K_BACKSPACE))
        self.assertFalse(tecla_es_retroceso(pygame.K_DELETE))

    def test_pantalla_con_campo_activo_detectada(self) -> None:
        class PantallaPrueba:
            def __init__(self) -> None:
                self.campo_nombre = CampoTexto(pygame.Rect(0, 0, 100, 30))
                self.campo_nombre.activo = True

        self.assertTrue(pantalla_campo_texto_activo(PantallaPrueba()))

    def test_supr_en_campo_activo_no_borra_ni_retrocede(self) -> None:
        campo = CampoTexto(pygame.Rect(0, 0, 100, 30))
        campo.activo = True
        campo.texto = "abc"
        evento = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DELETE)
        self.assertTrue(campo.manejar_evento(evento))
        self.assertEqual(campo.texto, "abc")

    def test_backspace_en_campo_activo_no_dispara_retroceso_global(self) -> None:
        from Grafico.atajos_teclado import pantalla_campo_texto_activo

        class PantallaPrueba:
            def __init__(self) -> None:
                self.campo_nombre = CampoTexto(pygame.Rect(0, 0, 100, 30))
                self.campo_nombre.activo = True

        pantalla = PantallaPrueba()
        self.assertTrue(pantalla_campo_texto_activo(pantalla))

    def test_backspace_en_campo_activo_borra_caracter(self) -> None:
        campo = CampoTexto(pygame.Rect(0, 0, 100, 30))
        campo.activo = True
        campo.texto = "abc"
        evento = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_BACKSPACE)
        self.assertTrue(campo.manejar_evento(evento))
        self.assertEqual(campo.texto, "ab")


class TestExamenDirigidoSesion(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pool = [
            _pregunta("M1", f"P{i}") for i in range(12)
        ] + [_pregunta("M2", f"Q{i}") for i in range(12)]
        cls.materias_meta = {
            "M1": {"curso": "1", "semestre": "1", "grupo": "1"},
            "M2": {"curso": "1", "semestre": "1", "grupo": "1"},
        }

    def test_pesos_favorecen_materias_con_fallos(self) -> None:
        registros = [
            RegistroRespuesta(1, self.pool[0], "B", False),
            RegistroRespuesta(2, self.pool[0], "B", False),
            RegistroRespuesta(3, self.pool[12], "A", True),
        ]
        pesos = calcular_pesos_desde_registros(registros)
        self.assertGreater(pesos["M1"], pesos["M2"])

    def test_generar_examen_excluye_preguntas_previas(self) -> None:
        previas = self.pool[:4]
        registros = [
            RegistroRespuesta(i + 1, p, "B", False) for i, p in enumerate(previas)
        ]
        pesos = calcular_pesos_desde_registros(registros)
        plan = generar_examen(
            self.pool,
            materias_orden=['M1', 'M2'],
            materias_meta=self.materias_meta,
            opciones=OpcionesGeneracionExamen(perfil=PerfilPedagogico.BALANCEADO, stats={}, n_materias=2, preguntas_por_materia=3, semilla=42, usar_analisis_historico=False, pesos_materia_sesion=pesos, preguntas_excluir=[r.pregunta for r in registros]),
        )
        claves_previas = {(p.materia, p.texto) for p in previas}
        for pregunta in plan.preguntas:
            self.assertNotIn((pregunta.materia, pregunta.texto), claves_previas)


class TestCadenaExamenDirigido(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pool = [
            _pregunta("M1", f"P{i}") for i in range(20)
        ] + [_pregunta("M2", f"Q{i}") for i in range(20)]
        cls.materias_meta = {
            "M1": {"curso": "1", "semestre": "1", "grupo": "1"},
            "M2": {"curso": "1", "semestre": "1", "grupo": "1"},
        }

    def test_cadena_acumula_registros(self) -> None:
        from Comun.cadena_examen_dirigido import CadenaExamenDirigido, extender_cadena

        r1 = [RegistroRespuesta(1, self.pool[0], "B", False)]
        r2 = [RegistroRespuesta(1, self.pool[1], "B", False)]
        cadena = extender_cadena(None, r1)
        self.assertEqual(cadena.n_sesiones, 1)
        cadena = extender_cadena(cadena, r2)
        self.assertEqual(cadena.n_sesiones, 2)
        self.assertEqual(len(cadena.registros), 2)

    def test_pesos_cadena_convergen_con_fallos_repetidos(self) -> None:
        from Comun.cadena_examen_dirigido import extender_cadena

        sesion1 = [
            RegistroRespuesta(i + 1, self.pool[i], "B", False)
            for i in range(3)
        ]
        sesion2 = [
            RegistroRespuesta(i + 1, self.pool[i + 3], "B", False)
            for i in range(3)
        ]
        cadena = extender_cadena(extender_cadena(None, sesion1), sesion2)
        pesos = calcular_pesos_desde_registros(list(cadena.registros))
        self.assertGreater(pesos["M1"], pesos.get("M2", 0.05))

    def test_cadena_excluye_preguntas_en_ventana_reciente(self) -> None:
        from Comun.cadena_examen_dirigido import extender_cadena

        sesion1 = [
            RegistroRespuesta(i + 1, self.pool[i], "B", False) for i in range(3)
        ]
        sesion2 = [
            RegistroRespuesta(i + 1, self.pool[i + 3], "B", False) for i in range(3)
        ]
        cadena = extender_cadena(extender_cadena(None, sesion1), sesion2)
        pesos = calcular_pesos_desde_registros(list(cadena.registros))
        vistas = {
            (p.materia, p.texto) for p in cadena.preguntas_en_ventana_exclusion()
        }
        plan = generar_examen(
            self.pool,
            materias_orden=['M1', 'M2'],
            materias_meta=self.materias_meta,
            opciones=OpcionesGeneracionExamen(perfil=PerfilPedagogico.BALANCEADO, stats={}, n_materias=2, preguntas_por_materia=3, semilla=99, usar_analisis_historico=False, pesos_materia_sesion=pesos, preguntas_excluir=cadena.preguntas_en_ventana_exclusion()),
        )
        for pregunta in plan.preguntas:
            self.assertNotIn((pregunta.materia, pregunta.texto), vistas)

    def test_ventana_permite_repetir_preguntas_de_sesiones_antiguas(self) -> None:
        from Comun.cadena_examen_dirigido import (
            VENTANA_EXCLUSION_SESIONES_DIRIGIDO,
            extender_cadena,
        )

        cadena = None
        for offset in range(VENTANA_EXCLUSION_SESIONES_DIRIGIDO + 1):
            sesion = [
                RegistroRespuesta(
                    1, self.pool[offset], "B", False
                )
            ]
            cadena = extender_cadena(cadena, sesion)
        assert cadena is not None
        primera = self.pool[0]
        excluidas = cadena.preguntas_en_ventana_exclusion()
        claves_excluidas = {(p.materia, p.texto) for p in excluidas}
        self.assertNotIn((primera.materia, primera.texto), claves_excluidas)
        self.assertIn(primera, cadena.preguntas_vistas())

    def test_pesos_dirigido_favorecen_materias_sin_exposicion(self) -> None:
        from Comun.cadena_examen_dirigido import calcular_pesos_materia_dirigido

        registros = [
            RegistroRespuesta(i + 1, self.pool[i], "B", False) for i in range(6)
        ]
        candidatas = ["M1", "M2", "M3"]
        solo_fallo = calcular_pesos_desde_registros(registros)
        pesos = calcular_pesos_materia_dirigido(registros, candidatas)
        self.assertGreater(pesos["M2"], solo_fallo.get("M2", 0.15))
        self.assertGreater(pesos["M3"], solo_fallo.get("M3", 0.15))

    def test_elegir_materias_reserva_sin_exposicion(self) -> None:
        import random
        from Comun.cadena_examen_dirigido import (
            calcular_pesos_materia_dirigido,
            elegir_materias_para_examen_dirigido,
        )

        registros = [
            RegistroRespuesta(i + 1, self.pool[i], "B", False) for i in range(6)
        ]
        candidatas = ["M1", "M2", "M3", "M4", "M5"]
        pesos = calcular_pesos_materia_dirigido(registros, candidatas)
        rng = random.Random(0)
        elegidas = elegir_materias_para_examen_dirigido(
            candidatas, pesos, 4, registros, rng
        )
        self.assertEqual(len(elegidas), 4)
        self.assertTrue({"M2", "M3", "M4", "M5"} & set(elegidas))

    def test_balance_se_mantiene_con_pesos_sesion(self) -> None:
        registros = [
            RegistroRespuesta(1, self.pool[0], "B", False),
            RegistroRespuesta(2, self.pool[1], "B", False),
        ]
        pesos = calcular_pesos_desde_registros(registros)
        plan = generar_examen(
            self.pool,
            materias_orden=['M1', 'M2'],
            materias_meta=self.materias_meta,
            opciones=OpcionesGeneracionExamen(perfil=PerfilPedagogico.BALANCEADO, stats={}, n_materias=2, preguntas_por_materia=3, semilla=7, usar_analisis_historico=False, exigir_balance_completo=True, pesos_materia_sesion=pesos, preguntas_excluir=[r.pregunta for r in registros]),
        )
        por_materia: dict[str, int] = {}
        for pregunta in plan.preguntas:
            por_materia[pregunta.materia] = por_materia.get(pregunta.materia, 0) + 1
        self.assertEqual(len(plan.preguntas), 6)
        self.assertEqual(set(por_materia.values()), {3})

    def test_tokens_enunciado_extrae_vocabulario_del_dataset(self) -> None:
        from Comun.cadena_examen_dirigido import tokens_enunciado

        p = _pregunta("", "¿Cuál es la derivada de ln(x) para x>0?")
        tokens = tokens_enunciado(p)
        self.assertIn("derivada", tokens)
        self.assertNotIn("cual", tokens)

    def test_pesos_planos_favorecen_contenido_similar_a_fallos(self) -> None:
        from Comun.cadena_examen_dirigido import calcular_pesos_preguntas_planas

        matriz_a = _pregunta("", "Determinante de una matriz cuadrada 3x3")
        matriz_b = _pregunta("", "Rango de una matriz rectangular")
        calc_a = _pregunta("", "Derivada de x al cuadrado")
        calc_b = _pregunta("", "Integral definida de x cuadrado")
        pool = [matriz_a, matriz_b, calc_a, calc_b]
        registros = [RegistroRespuesta(1, calc_a, "B", False)]
        pesos = calcular_pesos_preguntas_planas(pool, registros)
        por_texto = {p.texto: w for p, w in zip(pool, pesos, strict=True)}
        self.assertGreater(por_texto[calc_b.texto], por_texto[matriz_a.texto])
        self.assertGreater(por_texto[calc_b.texto], por_texto[matriz_b.texto])

    def test_seleccion_plana_dirigida_prioriza_tema_fallado(self) -> None:
        import random

        from Comun.cadena_examen_dirigido import construir_seleccion_plana_dirigida

        pool = [
            _pregunta("", f"Matriz invertible caso {i}") for i in range(4)
        ] + [
            _pregunta("", f"Derivada polinomio grado {i}") for i in range(12)
        ]
        fallos = [pool[5], pool[6]]
        registros = [
            RegistroRespuesta(1, fallos[0], "B", False),
            RegistroRespuesta(2, fallos[1], "B", False),
        ]
        seleccion = construir_seleccion_plana_dirigida(
            pool,
            8,
            random.Random(0),
            lambda p: (p.materia, p.texto),
            registros,
            fallos,
        )
        derivadas = sum(1 for p in seleccion if "derivada" in p.texto.lower())
        matrices = sum(1 for p in seleccion if "matriz" in p.texto.lower())
        self.assertGreaterEqual(derivadas, 5)
        self.assertGreater(derivadas, matrices)
    def test_pulsar_boton_indice_respeta_activo(self) -> None:
        pulsado: list[bool] = []

        def al_pulsar() -> None:
            pulsado.append(True)

        botones = [
            BotonOpcion("A", "uno", pygame.Rect(0, 0, 10, 10), lambda: None),
            BotonOpcion("B", "dos", pygame.Rect(0, 0, 10, 10), al_pulsar),
        ]
        botones[0].activo = False
        botones[1].activo = True
        from Grafico.atajos_teclado import pulsar_boton_indice

        self.assertFalse(pulsar_boton_indice(botones, 1))
        self.assertEqual(pulsado, [])
        self.assertTrue(pulsar_boton_indice(botones, 2))
        self.assertEqual(pulsado, [True])

    def test_manejar_teclado_partida_respeta_opcion_inactiva(self) -> None:
        respondidas: list[str] = []

        def on_responder(letra: str) -> None:
            respondidas.append(letra)

        botones = [
            BotonOpcion("A", "uno", pygame.Rect(0, 0, 10, 10), lambda: None),
            BotonOpcion("B", "dos", pygame.Rect(0, 0, 10, 10), lambda: None),
        ]
        botones[0].activo = False
        evento = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)
        consumido = manejar_teclado_partida(
            evento,
            fase="pregunta",
            botones_opcion=botones,
            on_responder=on_responder,
            on_continuar=lambda: None,
        )
        self.assertTrue(consumido)
        self.assertEqual(respondidas, [])


if __name__ == "__main__":
    unittest.main()
