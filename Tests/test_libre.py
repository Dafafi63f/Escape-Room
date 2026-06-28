#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Modo libre: compatibilidad de reglas, wizard y complejidad progresiva.

Secciones:
- test_compatibilidad_reglas_libre.py
- test_configuracion_libre.py
- test_rango_complejidad_libre.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

# --- test_compatibilidad_reglas_libre.py ---

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Comun.reglas import (
    MIN_PREGUNTAS_CALIFICACION,
    alcance_para_contexto,
    opciones_reglas_libre,
    sanitizar_reglas_libre,
)
from Comun.reglas import ContextoPartida, validar_reglas
from Comun.reglas import ReglasPartida, SistemaPuntuacion


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
            n_preguntas=4,
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
            ContextoPartida.LIBRE_INFINITO,
        ):
            self.assertIsNotNone(alcance_para_contexto(ctx))

# --- test_configuracion_libre.py ---

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Comun.reglas import sanitizar_reglas_libre
from Comun.reglas import ContextoPartida, validar_reglas
from Comun.reglas import ReglasPartida, SistemaPuntuacion


class TestConfiguracionLibre(unittest.TestCase):
    def test_arcade_sin_vidas_se_mantiene(self) -> None:
        reglas = ReglasPartida(
            vidas=None,
            sistema_puntuacion=SistemaPuntuacion.ARCADE,
        )
        out = validar_reglas(reglas, ContextoPartida.LIBRE_BLOQUE_NORMAL, n_preguntas=10)
        self.assertIsNone(out.vidas)
        self.assertEqual(out.sistema_puntuacion, SistemaPuntuacion.ARCADE)

    def test_nota_sin_vidas_en_bloque_largo(self) -> None:
        reglas = ReglasPartida(
            vidas=None,
            sistema_puntuacion=SistemaPuntuacion.NOTA,
        )
        out = validar_reglas(reglas, ContextoPartida.LIBRE_BLOQUE_NORMAL, n_preguntas=10)
        self.assertIsNone(out.vidas)
        self.assertEqual(out.sistema_puntuacion, SistemaPuntuacion.NOTA)

    def test_correccion_al_final_se_anula_en_libre(self) -> None:
        reglas = ReglasPartida(
            vidas=None,
            sistema_puntuacion=SistemaPuntuacion.NOTA,
            correccion_al_final=True,
        )
        out = validar_reglas(reglas, ContextoPartida.LIBRE_BLOQUE_NORMAL, n_preguntas=10)
        self.assertFalse(out.correccion_al_final)

# --- test_rango_complejidad_libre.py ---

from Comun.reglas import (  # noqa: E402
    complejidad_pregunta,
    normalizar_niveles_seleccionados,
    techo_complejidad_partida,
)
from Comun.modelos import Pregunta  # noqa: E402
from Comun.pool_libre import crear_estado_seleccion, elegir_indice_siguiente  # noqa: E402


def _pregunta_nivel(nivel: str, dificultad: str = "Media") -> Pregunta:
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
            _pregunta_nivel("1", "Facil"),
            _pregunta_nivel("2", "Facil"),
            _pregunta_nivel("2", "Media"),
            _pregunta_nivel("3", "Media"),
            _pregunta_nivel("4", "Dificil"),
        ]

    def test_normalizar_seleccion_vacia_usa_todos(self) -> None:
        niveles = normalizar_niveles_seleccionados(set(), self.pool)
        self.assertEqual(niveles, frozenset({1, 2, 3, 4, 6}))

    def test_solo_niveles_no_contiguos(self) -> None:
        seleccion = frozenset({1, 3})
        pool = [
            _pregunta_nivel("1", "Facil"),
            _pregunta_nivel("2", "Media"),
            _pregunta_nivel("3", "Media"),
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

    def test_seleccion_reproducible_con_semilla(self) -> None:
        import random

        pool = self.pool
        secuencia_a: list[int] = []
        secuencia_b: list[int] = []
        for rng in (random.Random(42), random.Random(42)):
            estado = crear_estado_seleccion(len(pool))
            turnos: list[int] = []
            for respondidas in range(5):
                idx = elegir_indice_siguiente(
                    pool,
                    estado,
                    modo_infinito=True,
                    dificultad_progresiva=False,
                    niveles_complejidad=frozenset({1, 2, 3, 4, 6}),
                    respondidas=respondidas,
                    rng=rng,
                )
                self.assertIsNotNone(idx)
                turnos.append(idx)  # type: ignore[arg-type]
            if not secuencia_a:
                secuencia_a = turnos
            else:
                secuencia_b = turnos
        self.assertEqual(secuencia_a, secuencia_b)

if __name__ == "__main__":
    unittest.main()
