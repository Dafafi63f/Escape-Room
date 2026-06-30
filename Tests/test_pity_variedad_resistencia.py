#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests del pity de variedad entre partidas cortas de resistencia."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Comun.informe_examen import CierreInformePartida, RegistroRespuesta  # noqa: E402
from Comun.modelos import Pregunta  # noqa: E402
from Comun.motor_nucleo import EstadoPartida  # noqa: E402
from Comun.reglas import preset_resistencia  # noqa: E402


def _pregunta(**kwargs) -> Pregunta:
    base = dict(
        texto="¿2+2?",
        materia="MAT",
        tematica="",
        dificultad="Facil",
        tipo="Teoria",
        grupo="g1",
        nivel="1",
        curso="1",
        semestre="1",
        opciones={"A": "3", "B": "4", "C": "5", "D": "6"},
        correcta="B",
        fuente="dataset",
    )
    base.update(kwargs)
    return Pregunta(**base)


class TestPityVariedadResistencia(unittest.TestCase):
    def test_persistencia_entre_partidas(self) -> None:
        from Comun.pity_variedad_resistencia import (
            PityVariedadResistencia,
            cargar_pity_variedad_resistencia,
            guardar_pity_variedad_resistencia,
        )

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "estadisticas_jugador.json"
            with patch(
                "Comun.estadisticas_jugador.resolver_path_estadisticas_jugador",
                return_value=path,
            ):
                pity = PityVariedadResistencia()
                pity.registrar_partida({"bloque"})
                guardar_pity_variedad_resistencia(pity)
                cargado = cargar_pity_variedad_resistencia()
                self.assertEqual(cargado.partidas, 1)
                self.assertEqual(cargado.partidas_sin("bloque"), 0)
                self.assertEqual(cargado.partidas_sin("jefe"), 1)

    def test_tres_partidas_cortas_acumulan_sin_ver(self) -> None:
        from Comun.estadisticas_jugador import registrar_cierre_partida
        from Comun.pity_variedad_resistencia import cargar_pity_variedad_resistencia

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "estadisticas_jugador.json"
            with patch(
                "Comun.estadisticas_jugador.resolver_path_estadisticas_jugador",
                return_value=path,
            ):
                estado = EstadoPartida(
                    nombre="T",
                    reglas=preset_resistencia(),
                    vidas_restantes=3,
                )
                for visto in ({"bloque"}, {"jefe"}, {"maldicion"}):
                    cierre = CierreInformePartida(
                        registros=[
                            RegistroRespuesta(
                                1,
                                _pregunta(),
                                "B",
                                True,
                            )
                        ],
                        titulo="R",
                        total_previsto=1,
                        prefijo="resistencia",
                        meta={
                            "tipo_actividad": "resistencia",
                            "resistencia_variedad_vista": sorted(visto),
                        },
                    )
                    registrar_cierre_partida(estado, cierre)
                pity = cargar_pity_variedad_resistencia()
                self.assertEqual(pity.partidas, 3)
                self.assertEqual(pity.partidas_sin("bloque"), 2)
                self.assertEqual(pity.partidas_sin("jefe"), 1)
                self.assertEqual(pity.partidas_sin("maldicion"), 0)
                self.assertEqual(pity.partidas_sin("evento_si_no"), 3)

    def test_soft_pity_bloque_fuerza_generacion(self) -> None:
        from Comun.resistencia_motor import EstadoResistencia, _generar_bloque_filtro

        er = EstadoResistencia(semilla_partida=42)
        er.preguntas_sin_bloque = 14
        pool = [
            _pregunta(texto=f"P{i}", materia="MAT", tipo="Teoria", grupo="g1")
            for i in range(12)
        ]
        bloque = _generar_bloque_filtro(pool, 20, er)
        self.assertIsNotNone(bloque)
        self.assertIn("bloque", er.variedad_vista)

    def test_cross_session_baja_umbral_jefe(self) -> None:
        from Comun.pity_variedad_resistencia import (
            PityVariedadResistencia,
            min_pregunta_jefe_resistencia,
            preguntas_hard_pity_jefe_resistencia,
        )

        pity = PityVariedadResistencia(sin_por_categoria={"jefe": 2})
        self.assertEqual(min_pregunta_jefe_resistencia(pity), 15)
        self.assertEqual(preguntas_hard_pity_jefe_resistencia(pity), 17)

    def test_soft_pity_maldicion_en_partida_corta(self) -> None:
        from Comun.maldiciones_partida import (
            PityMaldicionesResistencia,
            debe_forzar_maldicion_resistencia,
        )

        pity = PityMaldicionesResistencia(preguntas_sin_maldicion=28)
        self.assertTrue(debe_forzar_maldicion_resistencia(pity, 28))

    def test_evento_si_no_hard_pity(self) -> None:
        from Comun.eventos_partida import elegir_evento_si_no
        from Comun.pity_variedad_resistencia import debe_forzar_evento_si_no_resistencia
        from Comun.resistencia_motor import EstadoResistencia

        er = EstadoResistencia(semilla_partida=1)
        er.preguntas_sin_evento_si_no = 11
        self.assertTrue(debe_forzar_evento_si_no_resistencia(er))
        estado = EstadoPartida(
            nombre="T",
            reglas=preset_resistencia(),
            vidas_restantes=3,
            puntos_arcade=500,
        )
        evento = elegir_evento_si_no(20, er, estado)
        self.assertIsNotNone(evento)
        self.assertIn("evento_si_no", er.variedad_vista)


if __name__ == "__main__":
    unittest.main()
