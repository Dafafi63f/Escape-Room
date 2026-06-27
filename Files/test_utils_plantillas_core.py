#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from test_support import ensure_scripts_path

ensure_scripts_path()

from utils_plantillas_core import (  # noqa: E402
    clave_contenido,
    expandir_plantilla_base,
    expandir_plantilla_csv_filas,
    expandir_plantilla_instancias,
    quitar_etiqueta_materia_enunciado,
    tiene_placeholders,
)


class TestClaveContenido(unittest.TestCase):
    def test_normaliza_mayusculas_y_espacios(self) -> None:
        opts = {"A": " Uno ", "B": "Dos", "C": "Tres", "D": "Cuatro"}
        k1 = clave_contenido("  Àlgebra  ", "  Pregunta?  ", opts, "a")
        k2 = clave_contenido("àlgebra", "pregunta?", opts, "A")
        self.assertEqual(k1, k2)


class TestExpandirPlantilla(unittest.TestCase):
    def test_una_fila_una_pregunta(self) -> None:
        tpl = {
            "pregunta": "¿2+2?",
            "A": "3",
            "B": "4",
            "C": "5",
            "D": "6",
            "correcta": "B",
            "dificultad": "Facil",
            "tipo": "Calculo",
        }
        inst = expandir_plantilla_base(tpl)
        self.assertEqual(len(inst), 1)
        self.assertEqual(inst[0]["pregunta"], "¿2+2?")
        self.assertEqual(inst[0]["correcta"], "B")

    def test_rechaza_campo_variaciones_legacy(self) -> None:
        tpl = {
            "pregunta": "¿Cuánto es {n}+{n}?",
            "A": "{n}",
            "B": "{doble}",
            "C": "0",
            "D": "1",
            "correcta": "B",
            "variaciones": [{"n": "2", "doble": "4"}, {"n": "3", "doble": "6"}],
        }
        inst = expandir_plantilla_base(tpl)
        self.assertEqual(len(inst), 1)
        self.assertEqual(inst[0]["pregunta"], "¿Cuánto es {n}+{n}?")

    def test_instancias_incluyen_materia(self) -> None:
        tpl = {
            "pregunta": "P",
            "A": "a",
            "B": "b",
            "C": "c",
            "D": "d",
            "correcta": "A",
        }
        inst = expandir_plantilla_instancias("Tema X", tpl)
        self.assertEqual(inst[0]["materia"], "Tema X")

    def test_formato_csv(self) -> None:
        tpl = {
            "pregunta": "P",
            "A": "a",
            "B": "b",
            "C": "c",
            "D": "d",
            "correcta": "C",
            "tipo": "Teoria",
        }
        filas = expandir_plantilla_csv_filas(tpl)
        self.assertEqual(filas[0]["Pregunta"], "P")
        self.assertEqual(filas[0]["Correcta"], "C")


class TestPlaceholders(unittest.TestCase):
    def test_detecta_placeholder(self) -> None:
        self.assertTrue(tiene_placeholders("Hola {nombre}"))
        self.assertFalse(tiene_placeholders("Hola mundo"))


class TestEtiquetaMateria(unittest.TestCase):
    def test_quita_sufijo_catalogo_internet(self) -> None:
        raw = "Una distribución Normal estándar tiene: [Probabilitat]"
        self.assertEqual(
            quitar_etiqueta_materia_enunciado(raw, "Probabilitat"),
            "Una distribución Normal estándar tiene:",
        )

    def test_no_toca_corchetes_matematicos(self) -> None:
        texto = "Var(X)=E[X²]-(E[X])² requiere:"
        self.assertEqual(quitar_etiqueta_materia_enunciado(texto, "Probabilitat"), texto)


if __name__ == "__main__":
    unittest.main()
