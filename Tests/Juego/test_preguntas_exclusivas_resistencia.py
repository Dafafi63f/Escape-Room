#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas de preguntas exclusivas del modo resistencia."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_JUEGO = Path(__file__).resolve().parents[2] / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Comun.datos import cargar_materias, cargar_preguntas  # noqa: E402
from Comun.modelos import Pregunta  # noqa: E402
from Comun.preguntas_resistencia import (  # noqa: E402
    cargar_preguntas_exclusivas_resistencia,
    construir_pool_resistencia,
)
from Comun.resistencia_historia import (  # noqa: E402
    crear_seleccion_resistencia,
    elegir_indice_resistencia,
    escalada_para_pregunta,
    probabilidad_pregunta_exclusiva,
)
from Comun.rutas import (  # noqa: E402
    resolver_dataset,
    resolver_listado_materias,
    resolver_preguntas_resistencia,
)


class TestPreguntasExclusivasResistencia(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.materias_meta = cargar_materias(resolver_listado_materias())
        cls.preguntas = cargar_preguntas(resolver_dataset(), cls.materias_meta)
        cls.exclusivas = cargar_preguntas_exclusivas_resistencia(cls.materias_meta)
        cls.pool = construir_pool_resistencia(cls.preguntas, cls.materias_meta)

    def test_archivo_exclusivas_cargado(self) -> None:
        self.assertTrue(resolver_preguntas_resistencia().exists())
        self.assertGreaterEqual(len(self.exclusivas), 20)
        for p in self.exclusivas:
            self.assertTrue(p.exclusiva_resistencia)
            self.assertGreaterEqual(p.racha_minima_resistencia, 100)

    def test_pool_incluye_exclusivas(self) -> None:
        n_exc = sum(1 for p in self.pool if p.exclusiva_resistencia)
        self.assertEqual(n_exc, len(self.exclusivas))

    def test_exclusivas_no_en_modo_normal(self) -> None:
        """El dataset principal no marca preguntas como exclusivas."""
        for p in self.preguntas:
            self.assertFalse(p.exclusiva_resistencia)

    def test_no_salen_con_pregunta_baja(self) -> None:
        sel = crear_seleccion_resistencia(self.pool)
        numero = 51
        escalada = escalada_para_pregunta(numero)
        for _ in range(30):
            idx = elegir_indice_resistencia(self.pool, sel, escalada, numero_pregunta=numero)
            self.assertIsNotNone(idx)
            self.assertFalse(self.pool[idx].exclusiva_resistencia)

    def test_pueden_salir_con_pregunta_alta(self) -> None:
        sel = crear_seleccion_resistencia(self.pool)
        numero = 601
        escalada = escalada_para_pregunta(numero)
        visto_exclusiva = False
        for _ in range(80):
            idx = elegir_indice_resistencia(self.pool, sel, escalada, numero_pregunta=numero)
            self.assertIsNotNone(idx)
            if self.pool[idx].exclusiva_resistencia:
                visto_exclusiva = True
                break
        self.assertTrue(visto_exclusiva)

    def test_probabilidad_exclusiva_crece(self) -> None:
        self.assertEqual(probabilidad_pregunta_exclusiva(50), 0.0)
        self.assertLess(
            probabilidad_pregunta_exclusiva(150),
            probabilidad_pregunta_exclusiva(800),
        )

    def test_tiers_desbloqueo(self) -> None:
        t4 = min(p.racha_minima_resistencia for p in self.exclusivas if p.tier_resistencia == 4)
        self.assertGreaterEqual(t4, 750)


if __name__ == "__main__":
    unittest.main()
