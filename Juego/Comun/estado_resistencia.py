#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Estado de partida del modo resistencia (racha, vidas máx. e inventario)."""

from __future__ import annotations

from dataclasses import dataclass, field

VIDAS_MAX_INICIAL = 5
VIDAS_MAX_ABSOLUTO = 9
VIDAS_MIN_CAP = 2


@dataclass
class EstadoResistencia:
    """Racha de aciertos seguidos (se corta al fallar); vidas e inventario aparte."""

    racha: int = 0
    mejor_racha: int = 0
    vidas_max: int = VIDAS_MAX_INICIAL
    inventario: dict[str, int] = field(default_factory=dict)
    letras_ocultas: frozenset[str] = field(default_factory=frozenset)
    fraccion_enunciado: float = 1.0
    tiempo_extra_seg: int = 0
    escudo_activo: bool = False
    ultimo_evento: str = ""

    def reset_pregunta(self) -> None:
        self.letras_ocultas = frozenset()
        self.fraccion_enunciado = 1.0
        self.tiempo_extra_seg = 0
        self.ultimo_evento = ""

    def registrar_acierto(self) -> None:
        self.racha += 1
        self.mejor_racha = max(self.mejor_racha, self.racha)

    def registrar_fallo(self) -> None:
        self.racha = 0

    def cantidad(self, powerup_id: str) -> int:
        return max(0, self.inventario.get(powerup_id, 0))

    def agregar_powerup(self, powerup_id: str, cantidad: int = 1) -> None:
        if cantidad <= 0:
            return
        self.inventario[powerup_id] = self.cantidad(powerup_id) + cantidad

    def consumir_powerup(self, powerup_id: str) -> bool:
        n = self.cantidad(powerup_id)
        if n <= 0:
            return False
        if n == 1:
            self.inventario.pop(powerup_id, None)
        else:
            self.inventario[powerup_id] = n - 1
        return True

    def inventario_resumen(self) -> str:
        from Comun.iconos_resistencia import emoji_powerup, prefijar_emoji
        from Comun.powerups_resistencia import etiqueta_powerup

        partes = [
            prefijar_emoji(f"{etiqueta_powerup(pid)}×{n}", emoji_powerup(pid))
            for pid, n in sorted(self.inventario.items())
            if n > 0
        ]
        return ", ".join(partes) if partes else "vacío"
