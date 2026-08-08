#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generación del zip jugable (paquete portable)."""

from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[1]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

from Files.crear_zip_portable import crear_zip_portable  # noqa: E402


class TestZipPortable(unittest.TestCase):
    def test_crear_zip_incluye_juego_y_banco(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            destino = Path(tmp) / "MATCAD_juego_portable.zip"
            salida = crear_zip_portable(destino)
            self.assertTrue(salida.is_file())
            self.assertGreater(salida.stat().st_size, 10_000)

            with zipfile.ZipFile(salida) as zf:
                nombres = set(zf.namelist())

            self.assertIn("LEEME.txt", nombres)
            self.assertIn("Jugar.bat", nombres)
            self.assertIn(".matcad-paquete-completo", nombres)
            self.assertIn("Juego/juego_grafico.py", nombres)
            self.assertIn("Data/Banco/Preguntas.csv", nombres)
            self.assertIn("Data/Banco/listado_materias.csv", nombres)
            self.assertTrue(any(n.startswith("Juego/Comun/") for n in nombres))
            self.assertFalse(any(n.startswith("Tests/") for n in nombres))
            self.assertFalse(any(n.startswith("Files/") for n in nombres))
            self.assertFalse(any(n.startswith("Docs/") for n in nombres))


if __name__ == "__main__":
    unittest.main()
