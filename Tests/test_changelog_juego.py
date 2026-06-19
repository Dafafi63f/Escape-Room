#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Carga y simplificación de changelogs para la UI gráfica."""

from __future__ import annotations

import unittest

from Comun.changelog_juego import (
    cargar_changelog_juego,
    cargar_changelog_juego_grafico,
    cargar_changelog_proyecto,
    resolver_changelog,
    resolver_changelog_juego_grafico,
    resolver_changelog_proyecto,
    simplificar_changelog_para_ui,
)


class TestChangelogJuego(unittest.TestCase):
    def test_resolver_proyecto(self) -> None:
        path = resolver_changelog_proyecto()
        self.assertIsNotNone(path)
        assert path is not None
        self.assertEqual(path.name, "CHANGELOG_PROYECTO.md")

    def test_resolver_juego_grafico(self) -> None:
        from Comun.rutas import juego_dir

        path = resolver_changelog_juego_grafico()
        self.assertIsNotNone(path)
        assert path is not None
        self.assertEqual(path.name, "CHANGELOG_JUEGO.md")
        self.assertEqual(path.parent.name, "Docs")
        self.assertEqual(path.parent.parent, juego_dir().parent)

    def test_resolver_alias_legado(self) -> None:
        self.assertEqual(resolver_changelog(), resolver_changelog_proyecto())

    def test_simplificar_quita_tablas(self) -> None:
        raw = "# Título\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\nPárrafo."
        texto = simplificar_changelog_para_ui(raw)
        self.assertIn("Título", texto)
        self.assertIn("Párrafo", texto)
        self.assertNotIn("| A |", texto)

    def test_cargar_proyecto_contiene_resumen(self) -> None:
        texto = cargar_changelog_proyecto()
        self.assertIn("Resumen ejecutivo", texto)

    def test_cargar_juego_grafico_contiene_novedades(self) -> None:
        texto = cargar_changelog_juego_grafico()
        self.assertIn("Modo feedback", texto)

    def test_alias_cargar_juego(self) -> None:
        self.assertEqual(cargar_changelog_juego(), cargar_changelog_juego_grafico())


if __name__ == "__main__":
    unittest.main()
