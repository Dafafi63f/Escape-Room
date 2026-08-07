#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capacidades del juego según los datos disponibles (CSV mínimo vs paquete completo)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from Comun.presets_historia import PresetHistoria

TipoPaquete = Literal["minimo", "completo", "desarrollo"]


@dataclass(frozen=True)
class PerfilContenido:
    """Qué modos y opciones puede usar el motor con el contenido cargado."""

    solo_csv: bool = False
    csv_minimal: bool = False
    modo_minimo: bool = False
    tipo_paquete: TipoPaquete = "desarrollo"
    tiene_listado_materias: bool = True
    tiene_plantillas: bool = True
    tiene_presets: bool = True
    tiene_preguntas_resistencia: bool = True
    tiene_metadatos_curriculares: bool = True
    tiene_grupos_tematicos: bool = True
    tiene_tipos_pregunta: bool = True
    dataset_intermedio: bool = False

    @property
    def mostrar_metadatos_pregunta(self) -> bool:
        """Materia, tipo y dificultad bajo el enunciado (CSV real o inferidos)."""
        return not self.csv_minimal or self.dataset_intermedio

    @property
    def paquete_completo(self) -> bool:
        return not self.modo_minimo

    @property
    def banco_beta_disponible(self) -> bool:
        """Banco ampliado (480 extras): solo si el autor incluye ``plantillas.json``."""
        return self.tiene_plantillas and not self.modo_minimo

    @property
    def filtros_libre_disponibles(self) -> bool:
        if self.dataset_intermedio and self.tiene_tipos_pregunta:
            return True
        return (
            not self.modo_minimo
            and self.tiene_listado_materias
            and not self.csv_minimal
        )

    @property
    def historia_restringida(self) -> bool:
        """Juego mínimo: sin carrusel de historia."""
        return self.modo_minimo

    @property
    def modo_historia_disponible(self) -> bool:
        """Carrusel historia; desactivado en el paquete mínimo."""
        if self.modo_minimo:
            return False
        if not self.tiene_presets:
            return False
        return self.tiene_listado_materias

    @property
    def examen_fijo_barra_completo(self) -> bool:
        """Paquete mínimo: barra superior abre examen fijo (día, aleatorio, semilla)."""
        return self.modo_minimo and self.tiene_presets

    @property
    def especiales_restringido(self) -> bool:
        """CSV mínimo / portable: solo modo resistencia."""
        return self.historia_restringida

    @property
    def resistencia_solo_eventos(self) -> bool:
        """Resistencia sin escalada por dificultad; progresión vía eventos aleatorios."""
        return self.historia_restringida

    @property
    def modos_especiales_disponibles(self) -> bool:
        if not self.tiene_presets:
            return False
        if self.modo_minimo:
            return True
        return self.tiene_presets

    @property
    def modos_diarios_disponibles(self) -> bool:
        """Examen del día y aleatorio (barra 📅; atajos del preset ``examen_fijo``)."""
        return self.tiene_presets

    def modo_disponible(self, modo: str) -> bool:
        if modo in {"libre", "feedback", "salir"}:
            return True
        if modo == "historia":
            return self.modo_historia_disponible
        if modo == "especiales":
            return self.modos_especiales_disponibles
        if modo == "diarios":
            return self.modos_diarios_disponibles
        return True

    def motivo_modo_no_disponible(self, modo: str) -> str:
        if modo == "historia":
            if self.modo_minimo:
                return (
                    "Modo historia no incluido en el paquete mínimo. "
                    "Usa Examen fijo en la barra superior (📕)."
                )
            if not self.tiene_presets:
                return "Falta el catálogo de presets (Juego/presets.json)."
            if not self.tiene_listado_materias:
                return "Falta el listado de materias."
        if modo == "especiales" and not self.tiene_presets:
            return "Falta el catálogo de presets (Juego/presets.json)."
        if modo == "diarios" and not self.tiene_presets:
            return "Falta el catálogo de presets (Juego/presets.json)."
        return "Modo no disponible con el contenido cargado."

    def modo_especial_disponible(self, preset_id: str) -> bool:
        if not self.modos_especiales_disponibles:
            return False
        if preset_id == "escape_room":
            return not self.especiales_restringido
        return True

    def motivo_modo_especial_no_disponible(self, preset_id: str) -> str:
        if preset_id == "escape_room" and self.especiales_restringido:
            return "Escape room no incluido en el paquete mínimo."
        if not self.modos_especiales_disponibles:
            return "Modos especiales no disponibles con el contenido cargado."
        return "Modo no disponible."

    def preset_historia_viable(self, preset: PresetHistoria) -> tuple[bool, str]:
        from Comun.config_historia import opcion_historia_soportada
        from Comun.presets_historia import PRESETS_HISTORIA_PORTABLE

        if self.historia_restringida and preset.id not in PRESETS_HISTORIA_PORTABLE:
            return False, f"El modo «{preset.nombre}» no está incluido en el paquete mínimo."
        if preset.usar_plantillas_materia and not self.tiene_plantillas:
            return False, "Este preset requiere plantillas.json (banco beta del autor)."
        for op in preset.opciones:
            if op.obligatorio and not opcion_historia_soportada(op, self):
                return False, f"Falta el dato necesario para «{op.etiqueta}»."
        if preset.id == "repaso_area" and not self.tiene_grupos_tematicos:
            return False, "Repaso por área requiere grupos temáticos en el listado de materias."
        return True, ""

    @classmethod
    def completo(cls) -> PerfilContenido:
        return cls()
