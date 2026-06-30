#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Estadísticas locales agregadas del jugador."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Comun.estadisticas_jugador import (  # noqa: E402
    formatear_panel_estadisticas,
    registrar_cierre_partida,
    vaciar_estadisticas_jugador,
)
from Comun.informe_examen import CierreInformePartida, RegistroRespuesta, meta_cierre_libre  # noqa: E402
from Comun.modelos import Pregunta  # noqa: E402
from Comun.motor_nucleo import EstadoPartida  # noqa: E402
from Comun.reglas import ReglasPartida, SistemaPuntuacion  # noqa: E402


def _pregunta(materia: str = "Algebra", tipo: str = "Teoria") -> Pregunta:
    return Pregunta(
        texto="¿2+2?",
        materia=materia,
        tematica="",
        dificultad="Facil",
        tipo=tipo,
        grupo="",
        nivel="1",
        curso="1",
        semestre="1",
        opciones={"A": "3", "B": "4", "C": "5", "D": "6"},
        correcta="B",
    )


def _estado(nombre: str = "Tester") -> EstadoPartida:
    return EstadoPartida(
        nombre=nombre,
        reglas=ReglasPartida(sistema_puntuacion=SistemaPuntuacion.ARCADE),
        vidas_restantes=3,
        aciertos=2,
        respondidas=3,
        puntos_arcade=120,
    )


def _cierre_libre(*, aciertos: int = 2, total: int = 3) -> CierreInformePartida:
    p = _pregunta()
    if aciertos == 1 and total == 2:
        registros = [
            RegistroRespuesta(1, p, "A", True),
            RegistroRespuesta(2, p, "B", False),
        ]
    else:
        registros = [
            RegistroRespuesta(1, p, "A", True),
            RegistroRespuesta(2, p, "A", True),
            RegistroRespuesta(3, p, "C", False),
        ][:total]
    return CierreInformePartida(
        registros=registros,
        titulo="FIN",
        total_previsto=total,
        prefijo="partida_libre",
        meta=meta_cierre_libre(
            banco="dataset",
            filtro="todas",
            infinito=False,
            n_preguntas=total,
        ),
    )


class TestEstadisticasJugador(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._path = Path(self._tmpdir.name) / "estadisticas_jugador.json"
        self._patch = patch(
            "Comun.estadisticas_jugador.resolver_path_estadisticas_jugador",
            return_value=self._path,
        )
        self._patch.start()
        vaciar_estadisticas_jugador()

    def tearDown(self) -> None:
        self._patch.stop()
        self._tmpdir.cleanup()

    def test_registrar_y_totales(self) -> None:
        registrar_cierre_partida(_estado(), _cierre_libre())
        texto = formatear_panel_estadisticas()
        self.assertIn("Partidas jugadas: 1", texto)
        self.assertIn("Tiempo en partida: 0 s", texto)
        self.assertIn("Preguntas respondidas: 3", texto)
        self.assertIn("Libre:", texto)

    def test_dos_sesiones_acumulan(self) -> None:
        registrar_cierre_partida(_estado(), _cierre_libre())
        registrar_cierre_partida(_estado(), _cierre_libre(aciertos=1, total=2))
        texto = formatear_panel_estadisticas()
        self.assertIn("Partidas jugadas: 2", texto)
        self.assertIn("Preguntas respondidas: 5", texto)

    def test_duracion_partida_en_json_y_panel(self) -> None:
        import json
        import time

        estado = _estado()
        estado.inicio_total = time.monotonic() - 125
        registrar_cierre_partida(estado, _cierre_libre())
        texto = formatear_panel_estadisticas()
        self.assertIn("Tiempo en partida:", texto)
        self.assertIn("2 min 5 s", texto)
        self.assertIn("Libre:", texto)
        self.assertIn("2 min 5 s", texto.split("Libre:")[1].split("\n")[0])
        datos = json.loads(self._path.read_text(encoding="utf-8"))
        self.assertEqual(datos["totales"]["segundos_jugados"], 125)
        self.assertEqual(datos["sesiones"][-1]["duracion_seg"], 125)
        self.assertEqual(datos["por_modo"]["libre"]["segundos_jugados"], 125)

    def test_panel_vacio_muestra_secciones_sin_historial_ni_ranking(self) -> None:
        texto = formatear_panel_estadisticas()
        self.assertIn("--- SIGUE POR AQUI ---", texto)
        self.assertIn("primera partida", texto)
        self.assertIn("--- RESUMEN GLOBAL ---", texto)
        self.assertIn("--- RECORDS ---", texto)
        self.assertIn("max preguntas: 0", texto)
        self.assertIn("max puntos: 0", texto)
        self.assertIn("--- ANALISIS POR CONTENIDO ---", texto)
        self.assertNotIn("ULTIMAS SESIONES", texto)
        self.assertNotIn("Ranking resistencia", texto)

    def test_records_resistencia(self) -> None:
        from Comun.informe_examen import meta_cierre_historia

        cierre = CierreInformePartida(
            registros=_cierre_libre().registros,
            titulo="FIN",
            total_previsto=3,
            prefijo="resistencia",
            meta=meta_cierre_historia(
                preset_id="resistencia",
                preset_nombre="Resistencia",
                perfil="resistencia",
                materias=[],
                n_preguntas=3,
                modo_resistencia=True,
                racha=12,
            ),
        )
        estado = _estado()
        estado.puntos_arcade = 500
        estado.respondidas = 3
        registrar_cierre_partida(estado, cierre)
        texto = formatear_panel_estadisticas()
        self.assertIn("max preguntas: 3", texto)
        self.assertIn("max puntos: 500", texto)

    def test_panel_minimo_sin_escape_ni_analisis_contenido(self) -> None:
        from Comun.perfil_contenido import PerfilContenido

        registrar_cierre_partida(_estado(), _cierre_libre())
        perfil = PerfilContenido(modo_minimo=True, csv_minimal=True, tiene_presets=True)
        texto = formatear_panel_estadisticas(perfil)
        self.assertIn("--- RESUMEN GLOBAL ---", texto)
        self.assertIn("Libre:", texto)
        self.assertIn("Examen fijo:", texto)
        self.assertNotIn("Historia:", texto)
        self.assertNotIn("Escape room:", texto)
        self.assertNotIn("Escape - max salas", texto)
        self.assertNotIn("--- ANALISIS POR CONTENIDO ---", texto)
        self.assertNotIn("Teoria vs calculo", texto)
        self.assertNotIn("Materias a reforzar", texto)

    def test_panel_minimo_examen_fijo_en_por_modo(self) -> None:
        from Comun.informe_examen import meta_cierre_historia
        from Comun.perfil_contenido import PerfilContenido

        cierre = CierreInformePartida(
            registros=_cierre_libre().registros,
            titulo="FIN",
            total_previsto=3,
            prefijo="examen",
            meta=meta_cierre_historia(
                preset_id="examen_fijo",
                preset_nombre="Examen fijo",
                perfil="balanceado",
                materias=[],
                n_preguntas=24,
            ),
        )
        registrar_cierre_partida(_estado(), cierre)
        perfil = PerfilContenido(modo_minimo=True, csv_minimal=True, tiene_presets=True)
        texto = formatear_panel_estadisticas(perfil)
        self.assertIn("Examen fijo: 1 partidas", texto)
        self.assertNotIn("Historia:", texto)


    def test_tarjeta_sigue_por_aqui_materia_debil(self) -> None:
        from Comun.informe_examen import RegistroRespuesta, meta_cierre_libre

        algebra = _pregunta("Algebra Lineal")
        calculo = _pregunta("Calculo", tipo="Calculo")
        registros = [
            RegistroRespuesta(1, algebra, "A", False),
            RegistroRespuesta(2, algebra, "A", False),
            RegistroRespuesta(3, algebra, "A", True),
            RegistroRespuesta(4, calculo, "A", True),
            RegistroRespuesta(5, calculo, "A", True),
            RegistroRespuesta(6, calculo, "A", True),
        ]
        cierre = CierreInformePartida(
            registros=registros,
            titulo="FIN",
            total_previsto=6,
            prefijo="partida_libre",
            meta=meta_cierre_libre(
                banco="dataset",
                filtro="todas",
                infinito=False,
                n_preguntas=6,
            ),
        )
        registrar_cierre_partida(_estado(), cierre)
        texto = formatear_panel_estadisticas()
        self.assertIn("Refuerza Algebra Lineal", texto)


if __name__ == "__main__":
    unittest.main()
