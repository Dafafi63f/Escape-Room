#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas de textos de ayuda (tooltips) del modo gráfico."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_JUEGO = Path(__file__).resolve().parents[2] / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Grafico.tooltips_ui import (  # noqa: E402
    TOOLTIP_PAUSA,
    tooltip_filtro_principal,
    tooltip_menu_principal,
    tooltip_opcion_ciclo_historia,
    tooltip_opcion_ciclo_libre,
    tooltips_menu_pausa,
)


class TestTooltipsUi(unittest.TestCase):
    def test_menu_principal_tiene_texto(self) -> None:
        for oid in ("libre", "historia", "feedback", "salir"):
            self.assertTrue(tooltip_menu_principal(oid))

    def test_filtros_tienen_texto(self) -> None:
        for codigo in ("todas", "tematica", "semestre", "tipo"):
            texto = tooltip_filtro_principal(codigo)
            self.assertIsNotNone(texto)
            self.assertGreater(len(texto or ""), 10)

    def test_opcion_ciclo_libre(self) -> None:
        self.assertIsNone(tooltip_opcion_ciclo_libre("vidas", "3"))
        self.assertIsNone(tooltip_opcion_ciclo_libre("tiempo_pregunta", "90"))
        self.assertIsNotNone(tooltip_opcion_ciclo_libre("banco", "dataset"))
        self.assertIsNotNone(tooltip_opcion_ciclo_libre("sistema", "arcade"))
        self.assertIsNotNone(tooltip_opcion_ciclo_libre("n_preguntas", "infinito"))
        self.assertIsNone(tooltip_opcion_ciclo_libre("n_preguntas", "10"))

    def test_pausa_no_vacia(self) -> None:
        self.assertGreater(len(TOOLTIP_PAUSA), 20)
        tips = tooltips_menu_pausa(en_partida=False)
        self.assertEqual(len(tips), 3)
        self.assertTrue(all(len(t) > 10 for t in tips))
        tips_partida = tooltips_menu_pausa(en_partida=True)
        self.assertNotEqual(tips[0], tips_partida[0])

    def test_opcion_ciclo_historia(self) -> None:
        self.assertIsNotNone(
            tooltip_opcion_ciclo_historia("curso", "curso", "", etiqueta_opcion="Curso")
        )
        self.assertIsNotNone(
            tooltip_opcion_ciclo_historia(
                "estrategia_materias",
                "eleccion",
                "debilidades",
            )
        )
        self.assertIsNotNone(
            tooltip_opcion_ciclo_historia(
                "tiempo_total_min",
                "entero",
                "0",
            )
        )

    def test_navegacion_y_abandono_tienen_texto(self) -> None:
        from Grafico.tooltips_ui import (
            TOOLTIP_ABANDONAR_HISTORIA,
            TOOLTIP_ABANDONAR_LIBRE,
            TOOLTIP_ABANDONAR_RESISTENCIA,
            TOOLTIP_ATRAS,
            TOOLTIP_CONTINUAR,
            TOOLTIP_DIFICULTAD_PROGRESIVA,
            TOOLTIP_EMPEZAR,
            TOOLTIP_GUARDAR_INFORME,
            TOOLTIP_SIGUIENTE,
            TOOLTIP_VER_RANKING,
        )

        for texto in (
            TOOLTIP_ATRAS,
            TOOLTIP_SIGUIENTE,
            TOOLTIP_EMPEZAR,
            TOOLTIP_CONTINUAR,
            TOOLTIP_DIFICULTAD_PROGRESIVA,
            TOOLTIP_ABANDONAR_LIBRE,
            TOOLTIP_ABANDONAR_HISTORIA,
            TOOLTIP_ABANDONAR_RESISTENCIA,
            TOOLTIP_GUARDAR_INFORME,
            TOOLTIP_VER_RANKING,
        ):
            self.assertGreater(len(texto), 15, msg=texto[:30])

    def test_tiempo_modo_y_sistema_libre(self) -> None:
        self.assertIn("cronómetro", tooltip_opcion_ciclo_libre("tiempo_modo", "ninguno") or "")
        self.assertIn("Puntos", tooltip_opcion_ciclo_libre("sistema", "arcade") or "")


if __name__ == "__main__":
    unittest.main()
