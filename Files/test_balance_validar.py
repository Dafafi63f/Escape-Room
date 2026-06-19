#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from test_support import ensure_scripts_path

ensure_scripts_path()

from balance_lib import ejecutar_validar  # noqa: E402
from objetivos_balanceo import TARGET_TOTAL_PREGUNTAS  # noqa: E402


class TestBalanceDataset(unittest.TestCase):
    def test_dataset_cerrado_pasa_validacion(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = ejecutar_validar()
        self.assertEqual(rc, 0, buf.getvalue())
        self.assertIn("OK", buf.getvalue())

    def test_objetivo_total_preguntas(self) -> None:
        self.assertEqual(TARGET_TOTAL_PREGUNTAS, 480)


if __name__ == "__main__":
    unittest.main()
