#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas de selección de niveles de complejidad en el modo libre."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_JUEGO = Path(__file__).resolve().parents[2] / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Comun.dificultad import (  # noqa: E402
    complejidad_pregunta,
    normalizar_niveles_seleccionados,
    techo_complejidad_partida,
)
from Comun.modelos import Pregunta  # noqa: E402
from Comun.pool_libre import crear_estado_seleccion, elegir_indice_siguiente  # noqa: E402


def _pregunta(nivel: str, dificultad: str = "Media") -> Pregunta:
    return Pregunta(
        texto="?",
        materia="M",
        tematica="T",
        grupo="G",
        nivel=nivel,
        curso="1",
        semestre="1",
        dificultad=dificultad,
        tipo="test",
        opciones={"A": "a", "B": "b", "C": "c", "D": "d"},
        correcta="A",
        fuente="dataset",
    )


class TestNivelesComplejidadLibre(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.pool = [
            _pregunta("1", "Facil"),
            _pregunta("2", "Facil"),
            _pregunta("2", "Media"),
            _pregunta("3", "Media"),
            _pregunta("4", "Dificil"),
        ]

    def test_normalizar_seleccion_vacia_usa_todos(self) -> None:
        niveles = normalizar_niveles_seleccionados(set(), self.pool)
        self.assertEqual(niveles, frozenset({1, 2, 3, 4, 6}))

    def test_solo_niveles_no_contiguos(self) -> None:
        seleccion = frozenset({1, 3})
        pool = [
            _pregunta("1", "Facil"),
            _pregunta("2", "Media"),
            _pregunta("3", "Media"),
        ]
        estado = crear_estado_seleccion(len(pool))
        for _ in range(12):
            idx = elegir_indice_siguiente(
                pool,
                estado,
                modo_infinito=True,
                dificultad_progresiva=False,
                niveles_complejidad=seleccion,
                respondidas=0,
            )
            self.assertIsNotNone(idx)
            self.assertIn(complejidad_pregunta(pool[idx]), seleccion)

    def test_progresiva_sigue_orden_marcado(self) -> None:
        seleccion = frozenset({1, 3, 6})
        self.assertEqual(
            techo_complejidad_partida(
                dificultad_progresiva=True,
                respondidas=0,
                niveles_seleccion=seleccion,
            ),
            1,
        )
        self.assertEqual(
            techo_complejidad_partida(
                dificultad_progresiva=True,
                respondidas=40,
                niveles_seleccion=seleccion,
            ),
            3,
        )
        self.assertEqual(
            techo_complejidad_partida(
                dificultad_progresiva=True,
                respondidas=80,
                niveles_seleccion=seleccion,
            ),
            6,
        )


if __name__ == "__main__":
    unittest.main()
