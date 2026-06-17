#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pruebas de emojis y textos de ayuda del modo resistencia."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_JUEGO = Path(__file__).resolve().parents[2] / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Comun.iconos_resistencia import (  # noqa: E402
    emoji_evento_etiqueta,
    emoji_powerup,
    emoji_recompensa_etiqueta,
    prefijar_emoji,
    separar_emoji_mensaje,
)
from Comun.motor_resistencia_comun import formatear_aviso_evento, formatear_aviso_recompensa  # noqa: E402


class TestIconosResistencia(unittest.TestCase):
    def test_emoji_powerups(self) -> None:
        self.assertEqual(emoji_powerup("bomba"), "💣")
        self.assertEqual(emoji_powerup("escudo"), "🛡️")

    def test_prefijar_y_separar(self) -> None:
        mensaje = prefijar_emoji("Bomba", "💣")
        self.assertEqual(mensaje, "💣  Bomba")
        emoji, resto = separar_emoji_mensaje(mensaje)
        self.assertEqual(emoji, "💣")
        self.assertEqual(resto, "Bomba")

    def test_emoji_eventos(self) -> None:
        self.assertEqual(emoji_evento_etiqueta("Relámpago: 8 s por pregunta"), "⚡")
        self.assertEqual(emoji_evento_etiqueta("Pregunta extra difícil"), "☠️")

    def test_avisos_con_emoji(self) -> None:
        aviso = formatear_aviso_evento("Doble puntos")
        self.assertTrue(aviso.startswith("✨"))
        rec = formatear_aviso_recompensa("Objeto: Bomba")
        self.assertIn("💣", rec)
        self.assertIn("Bomba", rec)

    def test_emoji_recompensa_vida(self) -> None:
        self.assertEqual(emoji_recompensa_etiqueta("¡Vida extra!"), "❤️")


if __name__ == "__main__":
    unittest.main()
