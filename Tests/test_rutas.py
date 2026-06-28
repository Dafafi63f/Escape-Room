#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Resolución de rutas del paquete (sin escanear el perfil del usuario)."""

from __future__ import annotations

import os
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Comun import rutas


class TestRutasPaquete(unittest.TestCase):
    def _reiniciar_cache_creador(self) -> None:
        rutas._path_creador_privado = rutas._CREADOR_PRIVADO_SIN_RESOLVER

    def test_roots_busqueda_acotada_al_paquete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp) / "MATCAD_minimal"
            juego = raiz / "Juego"
            juego.mkdir(parents=True)
            cwd_prev = Path.cwd()
            try:
                os.chdir(raiz)
                with patch.object(rutas, "_JUEGO_DIR", juego):
                    candidatos = rutas._roots_busqueda()
            finally:
                os.chdir(cwd_prev)

        tmp_resuelto = Path(tmp).resolve()
        for candidato in candidatos:
            with self.subTest(candidato=candidato):
                self.assertTrue(
                    str(candidato.resolve()).startswith(str(tmp_resuelto)),
                    f"Raíz fuera del paquete temporal: {candidato}",
                )

    def test_creador_privado_ausente_resuelve_rapido(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp) / "MATCAD_minimal"
            juego = raiz / "Juego"
            juego.mkdir(parents=True)
            self._reiniciar_cache_creador()
            cwd_prev = Path.cwd()
            try:
                os.chdir(raiz)
                with patch.object(rutas, "_JUEGO_DIR", juego):
                    t0 = time.perf_counter()
                    path = rutas.resolver_config_creador_privado()
                    elapsed = time.perf_counter() - t0
            finally:
                os.chdir(cwd_prev)

        self.assertIsNone(path)
        self.assertLess(elapsed, 0.25)

    def test_creador_privado_en_data_banco(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp) / "MATCAD_minimal"
            juego = raiz / "Juego"
            banco = raiz / "Data" / "Banco"
            banco.mkdir(parents=True)
            privado = banco / "creador_privado.json"
            privado.write_text("{}", encoding="utf-8")
            self._reiniciar_cache_creador()
            with patch.object(rutas, "_JUEGO_DIR", juego):
                path = rutas.resolver_config_creador_privado()
        self.assertEqual(path.resolve(), privado.resolve())

    def test_buscar_archivo_ausente_usa_cache_negativo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            raiz = Path(tmp) / "MATCAD_minimal"
            juego = raiz / "Juego"
            juego.mkdir(parents=True)
            rutas._archivos_no_encontrados.clear()
            cwd_prev = Path.cwd()
            try:
                os.chdir(raiz)
                with patch.object(rutas, "_JUEGO_DIR", juego):
                    with self.assertRaises(FileNotFoundError):
                        rutas.resolver_listado_materias()
                    clave = (str(raiz.resolve()), "listado_materias.csv", "banco", True)
                    self.assertIn(clave, rutas._archivos_no_encontrados)
                    t0 = time.perf_counter()
                    with self.assertRaises(FileNotFoundError):
                        rutas.resolver_listado_materias()
                    elapsed = time.perf_counter() - t0
            finally:
                os.chdir(cwd_prev)
        self.assertLess(elapsed, 0.05)


if __name__ == "__main__":
    unittest.main()
