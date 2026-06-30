#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Powerups, packs y economía de tienda."""

from __future__ import annotations

import random
import unittest

from Tests.Fixtures.support import ensure_juego_path

ensure_juego_path()

from Comun.modelos import Pregunta  # noqa: E402


def _pregunta() -> Pregunta:
    return Pregunta(
        texto="?",
        materia="M",
        tematica="",
        dificultad="Facil",
        tipo="test",
        grupo="",
        nivel="",
        curso="1",
        semestre="1",
        opciones={"A": "1", "B": "2", "C": "3", "D": "4"},
        correcta="B",
    )


class TestPowerupsNuevos(unittest.TestCase):
    def test_descarte_inteligente_quita_dos(self) -> None:
        from Comun.objetos_partida import letras_ocultas_descarte_inteligente

        p = _pregunta()
        ocultas = letras_ocultas_descarte_inteligente(p, rng=random.Random(1))
        self.assertEqual(len(ocultas), 2)
        self.assertNotIn("B", ocultas)

    def test_pack_random_resuelve_contenido(self) -> None:
        from Comun.objetos_partida import POWERUPS_LOOT, resolver_contenido_pack

        rng = random.Random(7)
        items = resolver_contenido_pack("pack_random_3", rng)
        self.assertEqual(len(items), 3)
        for pid, cant in items:
            self.assertIn(pid, POWERUPS_LOOT)
            self.assertEqual(cant, 1)

    def test_comprar_pack_supervivencia(self) -> None:
        from Comun.motor_nucleo import EstadoPartida
        from Comun.reglas import ReglasPartida
        from Comun.tienda_escape import EstadoInventarioEscape, comprar_articulo

        estado = EstadoPartida(
            nombre="t",
            reglas=ReglasPartida(),
            puntos_arcade=100,
            vidas_restantes=3,
        )
        inv = EstadoInventarioEscape()
        self.assertIsNone(comprar_articulo(estado, inv, "pack_supervivencia", rng=random.Random(1)))
        self.assertEqual(inv.cantidad("escudo"), 1)
        self.assertEqual(inv.cantidad("tiempo_extra"), 1)

    def test_variar_precio_max_un_gratis_por_visita(self) -> None:
        from Comun.economia_partida import variar_precio_tienda

        rng = random.Random(0)
        gratis = 0
        for _ in range(200):
            precio, etiqueta = variar_precio_tienda(rng, 30, gratis_permitido=True)
            if etiqueta == "Gratis":
                gratis += 1
                precio2, _ = variar_precio_tienda(rng, 30, gratis_permitido=False)
                self.assertGreater(precio2, 0)
        self.assertGreater(gratis, 0)


if __name__ == "__main__":
    unittest.main()
