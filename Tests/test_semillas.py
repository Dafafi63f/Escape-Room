#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
import unittest
from datetime import date
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT / "Juego") not in sys.path:
    sys.path.insert(0, str(_ROOT / "Juego"))

from Comun.semillas import (  # noqa: E402
    formatear_semilla_diaria,
    rng_desde_semilla,
    semilla_derivada,
    semilla_diaria,
    semilla_estable_texto,
    semilla_orden_opciones,
    semilla_partida_aleatoria,
    semilla_partida_libre,
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

    def test_partida_libre_por_nombre(self) -> None:
        self.assertEqual(
            semilla_partida_libre(nombre="  Ana "),
            semilla_partida_libre(nombre="Ana"),
        )


class TestSemillaDerivada(unittest.TestCase):
    def test_orden_opciones(self) -> None:
        self.assertEqual(
            semilla_orden_opciones(semilla_base=10, numero_turno=2, indice_pregunta=1),
            10 + 2 * 1_009 + 1 * 7_919,
        )
        self.assertEqual(
            semilla_orden_opciones(semilla_base=None, numero_turno=1),
            1_009,
        )

    def test_rng_reproducible(self) -> None:
        self.assertEqual(
            rng_desde_semilla(42, 7).random(),
            rng_desde_semilla(42, 7).random(),
        )
        self.assertNotEqual(
            rng_desde_semilla(42, 7).random(),
            rng_desde_semilla(42, 8).random(),
        )

    def test_derivada_con_texto(self) -> None:
        self.assertEqual(
            semilla_derivada(5, "sala", 3),
            semilla_derivada(5, "sala", 3),
        )
