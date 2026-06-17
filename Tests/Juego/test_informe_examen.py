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

from Comun.jugador import NOMBRE_JUGADOR_DEFECTO
from Consola.informe_examen import (
    RegistroRespuesta,
    construir_nombre_archivo_informe,
    formatear_informe_examen,
    generar_id_sesion,
    publicar_informe_partida,
)
from Comun.modelos import Pregunta
from Consola.motor_partida import EstadoPartida, aplicar_respuesta, ResultadoRespuesta
from Comun.reglas_partida import preset_historia_examen, preset_libre_arcade


def _pregunta() -> Pregunta:
    return Pregunta(
        texto="¿2+2?",
        materia="Test",
        tematica="",
        dificultad="Facil",
        tipo="Teoria",
        grupo="",
        nivel="1",
        curso="1",
        semestre="1",
        opciones={"A": "3", "B": "4", "C": "5", "D": "6"},
        correcta="B",
    )


class TestInformeExamen(unittest.TestCase):
    def test_informe_incluye_correccion_y_estadisticas(self) -> None:
        reglas = preset_historia_examen()
        estado = EstadoPartida("Ana", reglas, vidas_restantes=None)
        estado.aciertos = 1
        estado.respondidas = 2
        registros = [
            RegistroRespuesta(1, _pregunta(), "B", True),
            RegistroRespuesta(2, _pregunta(), "A", False),
        ]
        id_sesion = generar_id_sesion()
        nombre = construir_nombre_archivo_informe(
            prefijo="examen",
            nombre_jugador="Ana",
            id_sesion=id_sesion,
            meta={"modo": "Historia", "perfil": "simulacro"},
        )
        texto = formatear_informe_examen(
            estado,
            registros,
            titulo="FIN DEL EXAMEN (modo historia)",
            meta={
                "id_sesion": id_sesion,
                "nombre_archivo": nombre,
                "etiqueta_sesion": "Examen historia — simulacro",
                "modo": "Historia",
                "perfil": "simulacro",
                "n_preguntas": 2,
            },
            total_previsto=2,
            fallos_por_materia={"Test": 1},
        )
        self.assertIn("CORRECCIÓN DETALLADA", texto)
        self.assertIn("ESTADÍSTICAS POR MATERIA", texto)
        self.assertIn("Feedback:", texto)
        self.assertIn("MATERIAS A REFORZAR", texto)
        self.assertIn("Nota (0-10):", texto)
        self.assertIn(f"ID: {id_sesion}", texto)
        self.assertIn("Examen historia", texto)
        self.assertNotIn("Archivo:", texto)
        self.assertNotIn("Configuración elegida", texto)

    def test_nombres_archivo_distintos_por_id(self) -> None:
        id1 = generar_id_sesion()
        id2 = generar_id_sesion()
        meta = {"modo": "Libre"}
        n1 = construir_nombre_archivo_informe(
            prefijo="partida_libre", nombre_jugador="x", id_sesion=id1, meta=meta
        )
        n2 = construir_nombre_archivo_informe(
            prefijo="partida_libre", nombre_jugador="x", id_sesion=id2, meta=meta
        )
        self.assertNotEqual(n1, n2)

    def test_nombre_libre_sin_repetir_modo(self) -> None:
        nombre = construir_nombre_archivo_informe(
            prefijo="partida_libre",
            nombre_jugador=NOMBRE_JUGADOR_DEFECTO,
            id_sesion="MATCAD-20260617-182233-9ecf",
            meta={"modo": "libre", "tipo_actividad": "libre_infinito"},
        )
        self.assertRegex(
            nombre,
            r"^partida_libre_infinito_.+_\d{8}_\d{6}_9ecf\.txt$",
        )
        self.assertNotIn("_libre_libre_", nombre)

    def test_dos_actividades_misma_ejecucion_dos_archivos(self) -> None:
        """Cada cierre de partida genera su propio .txt (modo independiente)."""
        import tempfile
        from unittest.mock import patch

        reglas = preset_historia_examen()
        registros = [RegistroRespuesta(1, _pregunta(), "B", True)]

        with tempfile.TemporaryDirectory() as tmp:
            dir_tmp = Path(tmp)
            with patch(
                "Consola.informe_examen.resolver_dir_informes",
                return_value=dir_tmp,
            ):
                estado_libre = EstadoPartida("Ana", preset_libre_arcade(), vidas_restantes=3)
                estado_libre.aciertos = 1
                estado_libre.respondidas = 1
                ruta1 = publicar_informe_partida(
                    estado_libre,
                    registros,
                    titulo="FIN DE PARTIDA (modo libre)",
                    total_previsto=10,
                    nombre_jugador="Ana",
                    meta={
                        "modo": "libre",
                        "tipo_actividad": "libre_finito",
                        "etiqueta_sesion": "Partida modo libre",
                    },
                    prefijo="partida_libre",
                    mostrar_en_consola=False,
                )

                estado_hist = EstadoPartida("Ana", reglas, vidas_restantes=None)
                estado_hist.aciertos = 1
                estado_hist.respondidas = 1
                ruta2 = publicar_informe_partida(
                    estado_hist,
                    registros,
                    titulo="FIN DEL EXAMEN (modo historia)",
                    total_previsto=5,
                    nombre_jugador="Ana",
                    meta={
                        "modo": "historia",
                        "tipo_actividad": "historia",
                        "preset": "simulacro_examen",
                        "perfil": "simulacro",
                        "etiqueta_sesion": "Historia — Simulacro",
                    },
                    prefijo="examen_historia",
                    mostrar_en_consola=False,
                )

                self.assertIsNotNone(ruta1)
                self.assertIsNotNone(ruta2)
                self.assertNotEqual(ruta1, ruta2)
                self.assertEqual(len(list(dir_tmp.glob("*.txt"))), 2)

    def test_preset_historia_examen_correccion_al_final(self) -> None:
        reglas = preset_historia_examen()
        self.assertTrue(reglas.correccion_al_final)
        self.assertFalse(reglas.mostrar_solucion_tras_fallo)

    def test_examen_cerrado_sin_mensajes_inmediatos(self) -> None:
        from io import StringIO
        from unittest.mock import patch

        reglas = preset_historia_examen()
        estado = EstadoPartida("T", reglas, vidas_restantes=None)
        p = _pregunta()
        buf = StringIO()
        with patch("sys.stdout", buf):
            aplicar_respuesta(p, estado, ResultadoRespuesta(acierto=False, respuesta="A"))
            aplicar_respuesta(p, estado, ResultadoRespuesta(acierto=True, respuesta="B"))
        salida = buf.getvalue()
        self.assertNotIn("[OK]", salida)
        self.assertNotIn("[X]", salida)
        self.assertNotIn("Correcta:", salida)
        self.assertEqual(estado.aciertos, 1)
        self.assertEqual(estado.respondidas, 2)

    def test_arcade_sigue_mostrando_feedback(self) -> None:
        from io import StringIO
        from unittest.mock import patch

        reglas = preset_libre_arcade()
        estado = EstadoPartida("T", reglas, vidas_restantes=3)
        buf = StringIO()
        with patch("sys.stdout", buf):
            aplicar_respuesta(_pregunta(), estado, ResultadoRespuesta(acierto=True, respuesta="B"))
        self.assertIn("[OK]", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
