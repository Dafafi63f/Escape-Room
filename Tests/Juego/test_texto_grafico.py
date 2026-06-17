#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas de renderizado de texto (wrap de títulos, etc.)."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_JUEGO = Path(__file__).resolve().parents[2] / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))


class TestTextoGrafico(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        import pygame

        from Grafico.fuentes import invalidar_cache_fuentes

        pygame.init()
        pygame.display.set_mode((960, 720))
        invalidar_cache_fuentes()

    @classmethod
    def tearDownClass(cls) -> None:
        import pygame

        from Grafico.fuentes import invalidar_cache_fuentes

        invalidar_cache_fuentes()
        if pygame.get_init():
            pygame.quit()

    def test_partir_lineas_titulo_largo(self) -> None:
        from Grafico.texto import _partir_lineas_centro

        titulo = "Pregunta 18 — Ranking — resistencia infinita"
        lineas = _partir_lineas_centro(titulo, 40, 400, bold=True)
        self.assertGreater(len(lineas), 1)
        for linea in lineas:
            self.assertTrue(linea)

    def test_partir_lineas_corta_una_sola(self) -> None:
        from Grafico.texto import _partir_lineas_centro

        lineas = _partir_lineas_centro("FIN DE PARTIDA", 40, 880, bold=True)
        self.assertEqual(lineas, ["FIN DE PARTIDA"])

    def test_dibujar_texto_centro_con_ancho_max_multilinea(self) -> None:
        import pygame

        from Grafico.texto import dibujar_texto_centro
        from Grafico.tema import ANCHO, MARGEN

        titulo = "Pregunta 18 — Ranking — resistencia infinita"
        ancho_max = ANCHO - 2 * MARGEN
        superficie = pygame.Surface((ANCHO, 160))
        rect = dibujar_texto_centro(
            superficie,
            titulo,
            (ANCHO // 2, 80),
            40,
            (255, 255, 255),
            bold=True,
            ancho_max=ancho_max,
        )
        self.assertLessEqual(rect.width, ancho_max + 4)
        self.assertGreater(rect.height, 45)

    def test_dibujar_texto_centro_sin_ancho_max_igual_que_antes(self) -> None:
        import pygame

        from Grafico.texto import dibujar_texto_centro
        from Grafico.tema import ANCHO

        superficie = pygame.Surface((ANCHO, 80))
        rect = dibujar_texto_centro(
            superficie,
            "Corto",
            (ANCHO // 2, 40),
            40,
            (255, 255, 255),
            bold=True,
        )
        self.assertGreater(rect.width, 0)
        self.assertGreater(rect.height, 0)


if __name__ == "__main__":
    unittest.main()
