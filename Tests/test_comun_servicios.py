#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Servicios de dominio en Comun tras la migración (informes, feedback, creador)."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Comun.feedback import (  # noqa: E402
    PLANTILLA_CREADOR_PRIVADO,
    creador_privado_para_distribucion,
    escribir_plantilla_creador_privado,
    mensaje_crear_creador_privado,
    plantilla_creador_privado,
    smtp_distribucion_listo,
    texto_creador_privado_distribucion,
    texto_plantilla_creador_privado,
)
from Comun.informe_examen import meta_cierre_historia, meta_cierre_libre  # noqa: E402
from Comun.informe_examen import RegistroRespuesta, generar_id_sesion  # noqa: E402


class TestConfigCreador(unittest.TestCase):
    def test_plantilla_es_copia_independiente(self) -> None:
        copia = plantilla_creador_privado()
        copia["creador"]["nombre"] = "Mutado"
        self.assertNotEqual(
            copia["creador"]["nombre"],
            PLANTILLA_CREADOR_PRIVADO["creador"]["nombre"],
        )

    def test_texto_plantilla_json_valido(self) -> None:
        datos = json.loads(texto_plantilla_creador_privado())
        self.assertIn("feedback_smtp", datos)
        self.assertIn("smtp_destino", datos["feedback_smtp"])

    def test_escribir_y_rechazar_duplicado(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "creador_privado.json"
            ruta = escribir_plantilla_creador_privado(destino)
            self.assertTrue(ruta.is_file())
            self.assertEqual(json.loads(ruta.read_text(encoding="utf-8"))["github"]["usuario"], "tu_usuario")
            with self.assertRaises(FileExistsError):
                escribir_plantilla_creador_privado(destino)

    def test_mensaje_apunta_a_comun(self) -> None:
        self.assertIn("Comun.feedback", mensaje_crear_creador_privado())
        self.assertNotIn("Consola", mensaje_crear_creador_privado())

    def test_distribucion_solo_feedback_smtp(self) -> None:
        smtp = {
            "smtp_servidor": "smtp.gmail.com",
            "smtp_usuario": "a@b.c",
            "smtp_password": "secreto",
            "smtp_destino": "dest@x.y",
        }
        privado = {"feedback_smtp": smtp, "github": {"personal_access_token": "tok"}}
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "creador_privado.json"
            ruta.write_text(json.dumps(privado), encoding="utf-8")
            with patch("Comun.feedback.resolver_config_creador_privado", return_value=ruta):
                datos = creador_privado_para_distribucion()
                assert datos is not None
                self.assertEqual(set(datos.keys()), {"feedback_smtp"})
                self.assertNotIn("github", datos)
                listo, dest = smtp_distribucion_listo()
                self.assertTrue(listo)
                self.assertEqual(dest, "dest@x.y")
                texto = texto_creador_privado_distribucion()
                assert texto is not None
                empaquetado = json.loads(texto)
                self.assertEqual(empaquetado["feedback_smtp"]["smtp_password"], "secreto")

    def test_distribucion_rechaza_smtp_incompleto(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "creador_privado.json"
            ruta.write_text(
                '{"feedback_smtp": {"smtp_servidor": "x", "smtp_usuario": "y"}}',
                encoding="utf-8",
            )
            with patch("Comun.feedback.resolver_config_creador_privado", return_value=ruta):
                listo, _ = smtp_distribucion_listo()
                self.assertFalse(listo)
                self.assertIsNone(texto_creador_privado_distribucion())


class TestCierreInforme(unittest.TestCase):
    def test_meta_cierre_libre_infinito(self) -> None:
        meta = meta_cierre_libre(
            banco="dataset",
            filtro="todas",
            infinito=True,
            n_preguntas=0,
        )
        self.assertEqual(meta["tipo_actividad"], "libre_infinito")
        self.assertIn("infinito", meta["etiqueta_sesion"].lower())

    def test_meta_cierre_historia_resistencia(self) -> None:
        meta = meta_cierre_historia(
            preset_id="resistencia",
            preset_nombre="Ranking",
            perfil="resistencia",
            materias=["Alg", "Calc"],
            n_preguntas=0,
            modo_resistencia=True,
            racha=7,
        )
        self.assertEqual(meta["tipo_actividad"], "resistencia")
        self.assertEqual(meta["racha"], 7)


class TestInformeExamenUtilidades(unittest.TestCase):
    def test_generar_id_sesion_formato(self) -> None:
        id_sesion = generar_id_sesion()
        self.assertTrue(id_sesion.startswith("MATCAD-"))
        partes = id_sesion.split("-")
        self.assertGreaterEqual(len(partes), 4)

    def test_registro_respuesta_tiempo_agotado(self) -> None:
        from Comun.modelos import Pregunta

        p = Pregunta(
            texto="?",
            materia="M",
            tematica="",
            dificultad="Facil",
            tipo="Teoria",
            grupo="",
            nivel="1",
            curso="1",
            semestre="1",
            opciones={"A": "1", "B": "2", "C": "3", "D": "4"},
            correcta="A",
        )
        reg = RegistroRespuesta(1, p, "", False, tiempo_agotado=True)
        self.assertTrue(reg.tiempo_agotado)


class TestImportsModulosMigrados(unittest.TestCase):
    def test_envio_feedback_desde_comun(self) -> None:
        from Comun.feedback import CategoriaFeedback, ReporteFeedback

        reporte = ReporteFeedback(
            categoria=CategoriaFeedback.BUG,
            mensaje="prueba",
        )
        self.assertTrue(reporte.id_reporte.startswith("FB-"))

    def test_generador_examen_desde_comun(self) -> None:
        from Comun.generador_examen_historia import PREGUNTAS_POR_MATERIA_DEFECTO
        from Comun.reglas import MIN_PREGUNTAS_PARTIDA

        self.assertEqual(PREGUNTAS_POR_MATERIA_DEFECTO, 4)
        self.assertGreaterEqual(MIN_PREGUNTAS_PARTIDA, 5)


if __name__ == "__main__":
    unittest.main()
