#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Arranque de ``juego_grafico.py`` sin abrir la ventana pygame."""

from __future__ import annotations

import builtins
import importlib
import sys
import unittest
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Tests.Fixtures.adaptador_juego import crear_backend  # noqa: E402

_JUEGO = Path(__file__).resolve().parents[1] / "Juego"


def _importar_lanzador():
    if str(_JUEGO) not in sys.path:
        sys.path.insert(0, str(_JUEGO))
    return importlib.import_module("juego_grafico")


class TestLanzadorGrafico(unittest.TestCase):
    def test_carga_datos_igual_que_adaptador(self) -> None:
        from Comun.datos import cargar_materias, cargar_preguntas
        from Comun.rutas import PATH_MATERIAS, PATH_PREGUNTAS, resolver_plantillas
        from Grafico.app import DatosJuego

        materias_meta = cargar_materias(PATH_MATERIAS)
        preguntas_dataset = cargar_preguntas(PATH_PREGUNTAS, materias_meta)
        datos = DatosJuego(
            num_preguntas=len(preguntas_dataset),
            num_materias=len(materias_meta),
            preguntas=preguntas_dataset,
            materias_meta=materias_meta,
            path_preguntas_csv=PATH_PREGUNTAS,
            path_plantillas_json=resolver_plantillas(),
        )
        resumen = crear_backend().cargar_datos()
        self.assertEqual(datos.num_preguntas, resumen.num_preguntas)
        self.assertEqual(datos.num_materias, resumen.num_materias)
        self.assertEqual(datos.preguntas[0].texto, resumen.muestra_texto)

    def test_main_sin_pygame_imprime_aviso(self) -> None:
        modulo = _importar_lanzador()
        buf = StringIO()
        real_import = builtins.__import__

        def _import_sin_pygame(name, globals=None, locals=None, fromlist=(), level=0):
            if name == "pygame":
                raise ImportError("no pygame")
            return real_import(name, globals, locals, fromlist, level)

        with patch("builtins.__import__", side_effect=_import_sin_pygame):
            with patch("sys.stdout", buf):
                modulo.main()
        self.assertIn("pygame", buf.getvalue().lower())

    def test_main_sin_datos_imprime_error(self) -> None:
        modulo = _importar_lanzador()
        buf = StringIO()
        with patch.object(
            modulo,
            "cargar_contenido_juego",
            side_effect=FileNotFoundError("sin CSV"),
        ):
            with patch("sys.stdout", buf):
                modulo.main([])
        self.assertIn("sin CSV", buf.getvalue())


if __name__ == "__main__":
    unittest.main()
