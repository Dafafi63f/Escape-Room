#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from Tests.support import ensure_juego_path

ensure_juego_path()

from Comun.compatibilidad_reglas_libre import (
    MIN_PREGUNTAS_CALIFICACION,
    opciones_reglas_libre,
    sanitizar_reglas_libre,
)
from Consola.configuracion_reglas_libre import alcance_para_contexto
from Consola.politica_reglas import ContextoPartida, validar_reglas
from Comun.reglas_partida import ReglasPartida, SistemaPuntuacion


class TestCompatibilidadReglasLibre(unittest.TestCase):
    def test_con_vidas_solo_arcade(self) -> None:
        opts = opciones_reglas_libre(
            modo_infinito=False,
            n_preguntas=10,
            sin_vidas=False,
            sistema=SistemaPuntuacion.ARCADE,
        )
        self.assertEqual(opts.sistemas, (SistemaPuntuacion.ARCADE,))
        self.assertTrue(opts.permitir_con_vidas)
        self.assertTrue(opts.permitir_dificultad_progresiva)

    def test_sin_vidas_bloque_largo_permite_nota(self) -> None:
        opts = opciones_reglas_libre(
            modo_infinito=False,
            n_preguntas=MIN_PREGUNTAS_CALIFICACION,
            sin_vidas=True,
            sistema=SistemaPuntuacion.NOTA,
        )
        self.assertIn(SistemaPuntuacion.NOTA, opts.sistemas)
        self.assertFalse(opts.permitir_con_vidas)
        self.assertFalse(opts.permitir_dificultad_progresiva)

    def test_infinito_solo_arcade(self) -> None:
        opts = opciones_reglas_libre(
            modo_infinito=True,
            n_preguntas=10,
            sin_vidas=True,
            sistema=SistemaPuntuacion.NOTA,
        )
        self.assertEqual(opts.sistemas, (SistemaPuntuacion.ARCADE,))

    def test_pocas_preguntas_sin_nota(self) -> None:
        opts = opciones_reglas_libre(
            modo_infinito=False,
            n_preguntas=2,
            sin_vidas=True,
            sistema=SistemaPuntuacion.NOTA,
        )
        self.assertEqual(opts.sistemas, (SistemaPuntuacion.ARCADE,))

    def test_sanitizar_nota_con_vidas_fuerza_arcade(self) -> None:
        reglas = ReglasPartida(
            vidas=3,
            sistema_puntuacion=SistemaPuntuacion.NOTA,
        )
        out = sanitizar_reglas_libre(reglas, modo_infinito=False, n_preguntas=10)
        self.assertEqual(out.vidas, 3)
        self.assertEqual(out.sistema_puntuacion, SistemaPuntuacion.ARCADE)

    def test_validar_fuerza_arcade_con_vidas(self) -> None:
        reglas = ReglasPartida(
            vidas=2,
            sistema_puntuacion=SistemaPuntuacion.PORCENTAJE,
        )
        out = validar_reglas(
            reglas,
            ContextoPartida.LIBRE_BLOQUE_NORMAL,
            n_preguntas=10,
        )
        self.assertEqual(out.vidas, 2)
        self.assertEqual(out.sistema_puntuacion, SistemaPuntuacion.ARCADE)

    def test_alcance_en_todos_los_contextos_libres(self) -> None:
        for ctx in (
            ContextoPartida.LIBRE_BLOQUE_NORMAL,
            ContextoPartida.LIBRE_BLOQUE_CORTO,
            ContextoPartida.LIBRE_UNA_PREGUNTA,
            ContextoPartida.LIBRE_INFINITO,
        ):
            self.assertIsNotNone(alcance_para_contexto(ctx))


if __name__ == "__main__":
    unittest.main()
