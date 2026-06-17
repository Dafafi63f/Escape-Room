#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import unittest
from unittest.mock import patch

from Comun.textos_ui import (
    OPCIONES_MENU_PRINCIPAL,
    con_emoji,
    etiqueta,
    info_dataset,
    mensaje_feedback,
    titulo_flexible,
    titulo_pantalla,
)


class TestTextosUi(unittest.TestCase):
    def test_con_emoji_simetrico(self) -> None:
        self.assertEqual(con_emoji("Modo historia", "📕"), "📕 Modo historia 📕")

    def test_con_emoji_simple(self) -> None:
        self.assertEqual(
            con_emoji("Modo feedback", "📣", simetrico=False),
            "📣 Modo feedback",
        )

    def test_con_emoji_fin(self) -> None:
        self.assertEqual(
            con_emoji("Siguiente", "▶️", posicion="fin"),
            "Siguiente ▶️",
        )

    def test_con_emoji_inicio(self) -> None:
        self.assertEqual(
            con_emoji("Atrás", "◀️", posicion="inicio"),
            "◀️ Atrás",
        )

    def test_sin_emoji(self) -> None:
        self.assertEqual(con_emoji("Modo libre", "🎮", usar_emojis=False), "Modo libre")

    def test_titulo_pantalla_grafico(self) -> None:
        self.assertEqual(
            titulo_pantalla("MODO HISTORIA"),
            "📖 MODO HISTORIA 📖",
        )

    def test_titulo_pantalla_consola(self) -> None:
        self.assertEqual(
            titulo_pantalla("MODO HISTORIA", simetrico=False, contexto="consola"),
            "📕 MODO HISTORIA",
        )

    def test_info_dataset_grafico(self) -> None:
        self.assertIn("480 preguntas", info_dataset(480, 40))
        self.assertTrue(info_dataset(480, 40).startswith("📚"))

    def test_info_dataset_consola(self) -> None:
        self.assertTrue(
            info_dataset(480, 40, simetrico=False, contexto="consola").startswith("📕")
        )

    def test_mensaje_feedback(self) -> None:
        self.assertIn("✅", mensaje_feedback("Correcto (+10 puntos)"))
        self.assertIn("❌", mensaje_feedback("Incorrecto"))

    def test_menu_principal_ids(self) -> None:
        ids = {o.id for o in OPCIONES_MENU_PRINCIPAL}
        self.assertEqual(ids, {"libre", "historia", "feedback", "salir"})

    def test_opcion_menu_grafico(self) -> None:
        fb = next(o for o in OPCIONES_MENU_PRINCIPAL if o.id == "feedback")
        self.assertEqual(fb.etiqueta(), "📣 Modo feedback 📣")

    def test_navegacion_emojis_coherentes(self) -> None:
        from Comun.textos_ui import (
            BTN_ATRAS,
            BTN_CONTINUAR,
            BTN_EMPEZAR,
            BTN_SIGUIENTE,
            BTN_VOLVER,
            BTN_VOLVER_MENU,
            resolver_emoji,
        )

        atras = resolver_emoji(BTN_ATRAS[1])
        self.assertEqual(resolver_emoji(BTN_VOLVER[1]), atras)
        self.assertEqual(resolver_emoji(BTN_VOLVER_MENU[1]), atras)
        adelante = resolver_emoji(BTN_SIGUIENTE[1])
        self.assertEqual(resolver_emoji(BTN_EMPEZAR[1]), adelante)
        self.assertEqual(resolver_emoji(BTN_CONTINUAR[1]), adelante)

    def test_etiqueta_navegacion_consola(self) -> None:
        from Comun.textos_ui import BTN_ATRAS, BTN_SIGUIENTE
        from Consola.textos_consola import etiqueta as etiqueta_cli

        with patch("Consola.textos_consola.usar_emojis", return_value=True):
            self.assertEqual(etiqueta_cli(*BTN_ATRAS), "◀️ Atrás")
            self.assertEqual(etiqueta_cli(*BTN_SIGUIENTE), "Siguiente ▶️")

    def test_titulo_flexible_prefijo(self) -> None:
        self.assertIn("🔥", titulo_flexible("FIN RACHA — Resistencia"))

    @patch("Consola.textos_consola.usar_emojis", return_value=True)
    def test_etiqueta_opcion_menu_consola(self, _mock: object) -> None:
        from Consola.textos_consola import etiqueta_opcion_menu

        fb = next(o for o in OPCIONES_MENU_PRINCIPAL if o.id == "feedback")
        self.assertEqual(etiqueta_opcion_menu(fb), "📣 Modo feedback")
        historia = next(o for o in OPCIONES_MENU_PRINCIPAL if o.id == "historia")
        self.assertEqual(etiqueta_opcion_menu(historia), "📕 Modo historia")


if __name__ == "__main__":
    unittest.main()
