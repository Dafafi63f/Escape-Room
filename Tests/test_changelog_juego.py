#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Carga y simplificación de changelogs para la UI gráfica."""

from __future__ import annotations

import unittest
from pathlib import Path

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Grafico.changelog_juego import (
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

    def test_simplificar_quita_negrita_markdown(self) -> None:
        raw = "- **Modo feedback** integrado (icono ℹ️).\n**Última actualización:** hoy."
        texto = simplificar_changelog_para_ui(raw)
        self.assertNotIn("**", texto)
        self.assertIn("Modo feedback", texto)
        self.assertIn("Última actualización:", texto)
        self.assertIn("ℹ️", texto)
        self.assertIn("• Modo feedback", texto)

    def test_simplificar_formato_secciones_y_viñetas(self) -> None:
        raw = (
            "# Novedades del juego\n\n"
            "## 2026-06-28 (estadísticas)\n\n"
            "- **Mis estadísticas:** resumen.\n\n"
            "---\n\n"
            "Al añadir algo que el jugador note, documenta aquí."
        )
        texto = simplificar_changelog_para_ui(raw)
        self.assertNotIn("Novedades del juego", texto)
        self.assertIn("--- 2026-06-28 (estadísticas) ---", texto)
        self.assertIn("• Mis estadísticas:", texto)
        self.assertNotIn("Al añadir algo", texto)

    def test_simplificar_omite_nota_tecnica_inicial(self) -> None:
        raw = (
            "# Novedades del juego\n\n"
            "Cambios visibles para quien juega en pygame. El historial técnico del TFG "
            "está en [CHANGELOG_PROYECTO.md](CHANGELOG_PROYECTO.md).\n\n"
            "**Última actualización:** hoy\n"
        )
        texto = simplificar_changelog_para_ui(raw)
        self.assertNotIn("CHANGELOG_PROYECTO", texto)
        self.assertNotIn("pygame.md", texto)
        self.assertIn("Cambios visibles para quien juega en pygame.", texto)
        self.assertIn("Última actualización:", texto)

    def test_viñeta_partida_con_sangria_colgante(self) -> None:
        import os

        import pygame

        os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
        pygame.init()
        try:
            from Grafico.tema import ANCHO, MARGEN, TAMANO_FUENTE_PEQUENA, crear_fuentes
            from Grafico.ui import partir_texto_con_sangria

            fuente = crear_fuentes()["pequena"]
            ancho = 320
            bloque = (
                "  • Mis estadísticas: en Info del juego (ℹ️) → «📊 Mis estadísticas». "
                "Muestra totales, evolución semanal, récords."
            )
            lineas = partir_texto_con_sangria(
                fuente,
                bloque,
                ancho,
                tamano_pt=TAMANO_FUENTE_PEQUENA,
            )
            self.assertGreater(len(lineas), 1)
            self.assertTrue(lineas[0].startswith("  • "))
            self.assertFalse(lineas[1].startswith("  • "))
            self.assertTrue(lineas[1].startswith(" "))
            self.assertGreater(len(lineas[1]) - len(lineas[1].lstrip(" ")), 2)
        finally:
            pygame.quit()

    def test_cargar_proyecto_contiene_resumen(self) -> None:
        texto = cargar_changelog_proyecto()
        self.assertIn("Resumen ejecutivo", texto)

    def test_cargar_juego_grafico_contiene_novedades(self) -> None:
        texto = cargar_changelog_juego_grafico()
        self.assertIn("Modo feedback", texto)

    def test_alias_cargar_juego(self) -> None:
        self.assertEqual(cargar_changelog_juego(), cargar_changelog_juego_grafico())

    def test_resolver_juego_en_layout_paquete_minimo(self) -> None:
        import os
        import shutil
        import tempfile
        from unittest.mock import patch

        origen = resolver_changelog_juego_grafico()
        self.assertIsNotNone(origen)
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp) / "MATCAD_minimal"
            juego = raiz / "Juego"
            juego.mkdir(parents=True)
            shutil.copy(origen, juego / "CHANGELOG_JUEGO.md")
            cwd_prev = Path.cwd()
            try:
                os.chdir(raiz)
                with patch("Grafico.changelog_juego.juego_dir", return_value=juego):
                    path = resolver_changelog_juego_grafico()
            finally:
                os.chdir(cwd_prev)
        self.assertIsNotNone(path)
        assert path is not None
        self.assertEqual(path.name, "CHANGELOG_JUEGO.md")
        self.assertEqual(path.parent, juego)


if __name__ == "__main__":
    unittest.main()
