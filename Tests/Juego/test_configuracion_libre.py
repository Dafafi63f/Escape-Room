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

from Consola.configuracion_reglas_libre import alcance_para_contexto
from Consola.politica_reglas import ContextoPartida, validar_reglas
from Consola.reglas_partida import ReglasPartida, SistemaPuntuacion, preset_libre_repaso


class TestConfiguracionLibre(unittest.TestCase):
    def test_alcance_solo_donde_permitido(self) -> None:
        self.assertIsNotNone(alcance_para_contexto(ContextoPartida.LIBRE_BLOQUE_NORMAL))
        self.assertIsNotNone(alcance_para_contexto(ContextoPartida.LIBRE_BLOQUE_CORTO))
        self.assertIsNone(alcance_para_contexto(ContextoPartida.LIBRE_INFINITO))
        self.assertIsNone(alcance_para_contexto(ContextoPartida.HISTORIA_SIMULACRO))

    def test_validar_nota_sin_vidas_mantiene_correccion_si_activa(self) -> None:
        reglas = ReglasPartida(
            vidas=3,
            sistema_puntuacion=SistemaPuntuacion.NOTA,
            correccion_al_final=True,
        )
        out = validar_reglas(reglas, ContextoPartida.LIBRE_BLOQUE_NORMAL)
        self.assertIsNone(out.vidas)
        self.assertTrue(out.correccion_al_final)

    def test_bloque_corto_rechaza_nota(self) -> None:
        reglas = ReglasPartida(
            vidas=None,
            sistema_puntuacion=SistemaPuntuacion.NOTA,
        )
        out = validar_reglas(reglas, ContextoPartida.LIBRE_BLOQUE_CORTO)
        self.assertEqual(out.sistema_puntuacion, SistemaPuntuacion.ARCADE)
        self.assertTrue(out.tiene_vidas())

    def test_repaso_preset_sin_correccion_al_final(self) -> None:
        out = validar_reglas(
            preset_libre_repaso(),
            ContextoPartida.LIBRE_BLOQUE_NORMAL,
        )
        self.assertFalse(out.correccion_al_final)


if __name__ == "__main__":
    unittest.main()
