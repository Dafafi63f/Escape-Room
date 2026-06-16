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

from Comun.compatibilidad_reglas_libre import sanitizar_reglas_libre
from Consola.politica_reglas import ContextoPartida, validar_reglas
from Comun.reglas_partida import ReglasPartida, SistemaPuntuacion


class TestConfiguracionLibre(unittest.TestCase):
    def test_arcade_sin_vidas_se_mantiene(self) -> None:
        reglas = ReglasPartida(
            vidas=None,
            sistema_puntuacion=SistemaPuntuacion.ARCADE,
        )
        out = validar_reglas(reglas, ContextoPartida.LIBRE_BLOQUE_NORMAL, n_preguntas=10)
        self.assertIsNone(out.vidas)
        self.assertEqual(out.sistema_puntuacion, SistemaPuntuacion.ARCADE)

    def test_nota_sin_vidas_en_bloque_largo(self) -> None:
        reglas = ReglasPartida(
            vidas=None,
            sistema_puntuacion=SistemaPuntuacion.NOTA,
        )
        out = validar_reglas(reglas, ContextoPartida.LIBRE_BLOQUE_NORMAL, n_preguntas=10)
        self.assertIsNone(out.vidas)
        self.assertEqual(out.sistema_puntuacion, SistemaPuntuacion.NOTA)

    def test_correccion_al_final_se_anula_en_libre(self) -> None:
        reglas = ReglasPartida(
            vidas=None,
            sistema_puntuacion=SistemaPuntuacion.NOTA,
            correccion_al_final=True,
        )
        out = validar_reglas(reglas, ContextoPartida.LIBRE_BLOQUE_NORMAL, n_preguntas=10)
        self.assertFalse(out.correccion_al_final)


if __name__ == "__main__":
    unittest.main()
