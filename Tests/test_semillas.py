#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "Juego") not in sys.path:
    sys.path.insert(0, str(_ROOT / "Juego"))

from Comun.semillas import (  # noqa: E402
    RngPartida,
    crear_rng_partida,
    formatear_semilla_diaria,
    resolver_semillas_partida,
    semilla_diaria,
    semilla_estable_texto,
    semilla_partida_aleatoria,
)


class TestSemillaDiaria(unittest.TestCase):
    def test_formato_ddmmaaaa(self) -> None:
        self.assertEqual(semilla_diaria(date(2026, 6, 22)), 22_06_2026)
        self.assertEqual(formatear_semilla_diaria(1_01_2026), "01012026")


class TestSemillaEstable(unittest.TestCase):
    def test_reproducible(self) -> None:
        a = semilla_estable_texto("Ana|libre")
        b = semilla_estable_texto("Ana|libre")
        self.assertEqual(a, b)
        self.assertNotEqual(a, semilla_estable_texto("otro"))

    def test_partida_escape_semilla_aleatoria(self) -> None:
        from Comun.escape_room import semilla_partida_escape

        semillas = {semilla_partida_escape() for _ in range(12)}
        self.assertGreater(len(semillas), 1)

    def test_partida_aleatoria_distinta_cada_llamada(self) -> None:
        semillas = {semilla_partida_aleatoria() for _ in range(12)}
        self.assertGreater(len(semillas), 1)


class TestResolverSemillasPartida(unittest.TestCase):
    def test_examen_dia_orden_variar_usa_semilla_nueva(self) -> None:
        from Comun.config_historia import ConfigPresetHistoria

        with patch(
            "Comun.semillas.semilla_partida_aleatoria",
            return_value=777,
        ):
            semilla = resolver_semillas_partida(
                preset_id="examen_fijo",
                cfg=ConfigPresetHistoria(valores={"origen_semilla": "diario"}),
                orden_preguntas="variar",
            )
        self.assertEqual(semilla, 777)

    def test_examen_dia_orden_fijo_usa_semilla_diaria(self) -> None:
        from Comun.config_historia import ConfigPresetHistoria

        semilla = resolver_semillas_partida(
            preset_id="examen_fijo",
            cfg=ConfigPresetHistoria(valores={"origen_semilla": "diario"}),
            orden_preguntas="materia",
        )
        self.assertEqual(semilla, semilla_diaria())

    def test_resto_modos_una_sola_semilla(self) -> None:
        from Comun.config_historia import ConfigPresetHistoria

        semilla = resolver_semillas_partida(
            preset_id="simulacro_grado",
            cfg=ConfigPresetHistoria(),
        )
        self.assertGreater(semilla, 0)

        semilla2 = resolver_semillas_partida(
            preset_id="examen_fijo",
            cfg=ConfigPresetHistoria(valores={"origen_semilla": "aleatorio"}),
            orden_preguntas="dificultad",
        )
        self.assertGreater(semilla2, 0)


class TestRngPartida(unittest.TestCase):
    def test_misma_semilla_avanza_en_una_instancia(self) -> None:
        rng = RngPartida.desde_semilla(42)
        a = rng.random()
        b = rng.random()
        self.assertNotEqual(a, b)

    def test_recrear_instancia_reinicia_secuela(self) -> None:
        primero = RngPartida.desde_semilla(42).random()
        otro = RngPartida.desde_semilla(42).random()
        self.assertEqual(primero, otro)

    def test_continuar_conserva_estado(self) -> None:
        import random as random_mod

        rng = RngPartida.desde_semilla(99)
        ref = random_mod.Random(99)
        self.assertEqual(rng.random(), ref.random())
        seguidor = RngPartida.continuar(99, rng.interno)
        self.assertEqual(seguidor.random(), ref.random())

    def test_crear_rng_partida_devuelve_rng_partida(self) -> None:
        self.assertIsInstance(crear_rng_partida(7), RngPartida)

    def test_shuffle_opciones_distinto_cada_vez(self) -> None:
        from Comun.modelos import Pregunta
        from Comun.motor_nucleo import presentacion_opciones_pantalla

        p = Pregunta(
            texto="¿2+2?",
            materia="M",
            tematica="",
            dificultad="Facil",
            tipo="Teoria",
            grupo="",
            nivel="",
            curso="1",
            semestre="1",
            opciones={"A": "3", "B": "4", "C": "5", "D": "6"},
            correcta="B",
        )
        rng = RngPartida.desde_semilla(123)
        filas_a = presentacion_opciones_pantalla(p, rng=rng).filas
        filas_b = presentacion_opciones_pantalla(p, rng=rng).filas
        self.assertNotEqual(filas_a, filas_b)
