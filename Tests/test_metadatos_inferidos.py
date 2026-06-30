#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Comun.informe_examen import RegistroRespuesta  # noqa: E402
from Comun.metadatos_inferidos import (  # noqa: E402
    actualizar_desde_registros,
    cobertura_metadatos_inferidos,
    enriquecer_preguntas_minimal,
    exportar_csv_intermedio,
    exportar_dataset_intermedio,
    exportar_listado_materias_intermedio,
    huella_pregunta,
    inferir_dificultad_desde_tasa,
    inferir_tematica_desde_enunciado,
    inferir_tipo_desde_enunciado,
    vaciar_metadatos_inferidos,
)
from Comun.modelos import Pregunta  # noqa: E402


def _pregunta(
    texto: str,
    *,
    correcta: str = "A",
    opciones: dict[str, str] | None = None,
) -> Pregunta:
    opts = opciones or {
        "A": "1",
        "B": "2",
        "C": "3",
        "D": "4",
    }
    return Pregunta(
        texto=texto,
        materia="",
        tematica="",
        dificultad="",
        tipo="",
        grupo="",
        nivel="",
        curso="",
        semestre="",
        opciones=opts,
        correcta=correcta,
    )


class TestMetadatosInferidos(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self._path = Path(self._tmpdir.name) / "metadatos_inferidos.json"
        self._patch = mock.patch(
            "Comun.metadatos_inferidos.resolver_path_metadatos_inferidos",
            return_value=self._path,
        )
        self._patch.start()
        vaciar_metadatos_inferidos()

    def tearDown(self) -> None:
        self._patch.stop()
        self._tmpdir.cleanup()

    def test_huella_estable_por_texto(self) -> None:
        p = _pregunta("¿Cuánto es 2+2?")
        self.assertEqual(len(huella_pregunta(p)), 16)
        self.assertEqual(huella_pregunta(p), huella_pregunta(_pregunta("¿Cuánto es 2+2?")))

    def test_heuristica_tipo_calculo(self) -> None:
        self.assertEqual(
            inferir_tipo_desde_enunciado("Calcula la integral de x^2"),
            "Calculo",
        )
        self.assertEqual(
            inferir_tipo_desde_enunciado("Define el concepto de grupo"),
            "Teoria",
        )

    def test_dificultad_desde_tasa(self) -> None:
        self.assertEqual(inferir_dificultad_desde_tasa(8, 10), "Facil")
        self.assertEqual(inferir_dificultad_desde_tasa(5, 10), "Media")
        self.assertEqual(inferir_dificultad_desde_tasa(2, 10), "Dificil")

    def test_tematica_prefiere_palabra_larga(self) -> None:
        self.assertEqual(
            inferir_tematica_desde_enunciado(
                "Un sistema distribuido coordina componentes sin reloj global"
            ),
            "distribuido",
        )
        self.assertEqual(
            inferir_tematica_desde_enunciado("Capacidad reservada en DynamoDB reduce:"),
            "dynamodb",
        )

    def test_dificultad_parcial_con_un_intento(self) -> None:
        p = _pregunta("Pregunta única redis cluster")
        actualizar_desde_registros([RegistroRespuesta(1, p, "A", False)])
        enriquecer_preguntas_minimal([p])
        self.assertEqual(p.dificultad, "Dificil")

    def test_catalogo_agrupa_mas_en_variado(self) -> None:
        pool = [_pregunta(f"Pregunta única número {i} sobre cloud") for i in range(20)]
        enriquecer_preguntas_minimal(pool, aplicar_catalogo=True)
        materias = {p.materia for p in pool if p.materia}
        self.assertLessEqual(len(materias), 4)

    def test_actualizar_y_enriquecer(self) -> None:
        p = _pregunta("Pregunta de prueba algebra lineal")
        registros = [
            RegistroRespuesta(i + 1, p, "A", False)
            for i in range(4)
        ]
        actualizar_desde_registros(registros)
        enriquecer_preguntas_minimal([p])
        self.assertEqual(p.dificultad, "Dificil")
        self.assertIn(p.tipo, {"Teoria", "Calculo"})
        self.assertTrue(p.tematica)

    def test_dataset_intermedio_tras_cobertura(self) -> None:
        pool = [_pregunta(f"Pregunta única número {i} matriz") for i in range(12)]
        for i, p in enumerate(pool):
            actualizar_desde_registros(
                [RegistroRespuesta(1, p, "A", i % 3 == 0) for _ in range(4)]
            )
        enriquecer_preguntas_minimal(pool, aplicar_catalogo=True)
        cov = cobertura_metadatos_inferidos(pool)
        self.assertTrue(cov["dataset_intermedio"])
        self.assertGreaterEqual(cov["con_dificultad"], 8)

    def test_materias_y_grupos_artificiales(self) -> None:
        pool = [
            _pregunta("Pregunta sobre matriz y determinante calcula valor"),
            _pregunta("Otra pregunta con matriz y determinante resuelve"),
            _pregunta("Define el concepto de grupo algebraico abstracto"),
            _pregunta("Explica la definicion formal de grupo en algebra"),
        ]
        enriquecer_preguntas_minimal(pool, aplicar_catalogo=True)
        materias = {p.materia for p in pool if p.materia}
        grupos = {p.grupo for p in pool if p.grupo}
        self.assertGreaterEqual(len(materias), 2)
        self.assertTrue(all(m.startswith("Tema ") for m in materias))
        self.assertTrue(grupos)

    def test_exportar_dataset_intermedio(self) -> None:
        pool = [_pregunta(f"Pregunta export {i}") for i in range(4)]
        carpeta = Path(self._tmpdir.name) / "export"
        resultado = exportar_dataset_intermedio(pool, carpeta=carpeta)
        self.assertEqual(resultado.n_preguntas, 4)
        self.assertTrue(resultado.csv.is_file())
        self.assertTrue(resultado.listado.is_file())
        self.assertIn("Grupo", resultado.csv.read_text(encoding="utf-8"))

    def test_exportar_csv_y_listado_intermedio(self) -> None:
        pool = [
            _pregunta(f"Pregunta algebra lineal numero {i} matriz")
            for i in range(6)
        ]
        actualizar_desde_registros(
            [RegistroRespuesta(1, pool[0], "A", False) for _ in range(3)]
        )
        csv_path = Path(self._tmpdir.name) / "banco.csv"
        listado_path = Path(self._tmpdir.name) / "materias.csv"
        n = exportar_csv_intermedio(pool, csv_path)
        self.assertEqual(n, 6)
        texto = csv_path.read_text(encoding="utf-8")
        self.assertIn("Materia", texto)
        self.assertIn("Grupo", texto)
        n_list = exportar_listado_materias_intermedio(pool, listado_path)
        self.assertGreaterEqual(n_list, 1)
        self.assertIn("Grupo", listado_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
