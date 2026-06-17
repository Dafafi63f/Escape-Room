#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas de la barra de estado con iconos."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_JUEGO = Path(__file__).resolve().parents[2] / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Comun.linea_estado_ui import formatear_linea_estado, segmentos_linea_estado  # noqa: E402
from Comun.motor_nucleo import EstadoPartida, linea_estado  # noqa: E402
from Comun.reglas_partida import preset_libre_arcade  # noqa: E402


class TestBarraEstado(unittest.TestCase):
    def test_segmentos_modo_libre(self) -> None:
        reglas = preset_libre_arcade()
        estado = EstadoPartida(nombre="Ana", reglas=reglas, vidas_restantes=3)
        segs = segmentos_linea_estado(estado, "Pregunta 1/inf")
        textos = [s.texto for s in segs]
        self.assertIn("Pregunta 1/∞", textos)
        self.assertIn("3/3", textos)
        self.assertIn("0", textos)
        self.assertEqual(segs[0].emoji, "📝")
        self.assertEqual(segs[1].emoji, "❤️")
        self.assertEqual(segs[2].emoji, "⭐")

    def test_formato_texto_con_emojis(self) -> None:
        reglas = preset_libre_arcade()
        estado = EstadoPartida(nombre="Ana", reglas=reglas, vidas_restantes=3)
        texto = formatear_linea_estado(
            segmentos_linea_estado(estado, "Pregunta 1/inf"),
            usar_emojis=True,
        )
        self.assertIn("📝", texto)
        self.assertIn("❤️", texto)
        self.assertIn("⭐", texto)
        self.assertIn("∞", texto)
        self.assertIn("·", texto)

    def test_linea_estado_motor_usa_emojis(self) -> None:
        reglas = preset_libre_arcade()
        estado = EstadoPartida(nombre="Ana", reglas=reglas, vidas_restantes=2)
        texto = linea_estado(estado, "Pregunta 3/10")
        self.assertIn("📝", texto)
        self.assertIn("❤️", texto)

    def test_segmentos_racha_resistencia(self) -> None:
        reglas = preset_libre_arcade()
        estado = EstadoPartida(nombre="Bob", reglas=reglas, vidas_restantes=1)
        estado.puntos_arcade = 120
        segs = segmentos_linea_estado(
            estado, "Racha 12 · #13", segundos_pregunta_restantes=8
        )
        self.assertEqual(segs[0].emoji, "🔥")
        self.assertTrue(any(s.id == "tiempo_preg" for s in segs))


if __name__ == "__main__":
    unittest.main()
