#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Bucle principal pygame y enrutador de pantallas."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import math
import pygame

from Comun.modelos import Pregunta
from Comun.perfil_contenido import PerfilContenido
from Grafico.textos_grafico import (
    BTN_CONTINUAR,
    BTN_CONTINUAR_PARTIDA,
    BTN_PANTALLA_TITULO,
    BTN_SALIR_PROGRAMA,
    emoji_icono,
    etiqueta_menu,
)
from Grafico.texto import dibujar_texto_centro
from Grafico.tema import (
    ALTO,
    ANCHO,
    FPS,
    GAP_ICONOS_FIJOS,
    MARGEN,
    TITULO_VENTANA,
    X_ICONOS_FIJOS,
    Y_ICONOS_FIJOS,
    alto_icono_fijo,
    ancho_icono_fijo,
    crear_fuentes,
)
from Grafico.ui import (
    Boton,
    COLOR_BOTON,
    COLOR_BOTON_HOVER,
    COLOR_BOTON_INACTIVO,
    COLOR_BOTON_INACTIVO_TEXTO,
    colores_boton,
    dibujar_overlay_atenuacion,
    dibujar_panel,
    dibujar_tooltips_botones,
    rects_botones_apilados,
)
from Grafico.tooltips_ui import (
    TOOLTIP_BARRA_BIENVENIDA,
    TOOLTIP_BARRA_DURANTE_OPCIONES,
    TOOLTIP_BARRA_DURANTE_PAUSA,
    TOOLTIP_BARRA_DURANTE_PARTIDA,
    TOOLTIP_FEEDBACK,
    TOOLTIP_OPCIONES,
    TOOLTIP_PAUSA,
    TOOLTIP_RANKING,
    tooltip_barra_diarios,
    tooltips_menu_pausa,
)
from Grafico.atajos_teclado import (
    _FASES_PARTIDA_SIN_RETROCESO,
    atajo_avanzar_pantalla,
    atajo_opcion_numerica_pantalla,
    atajo_retroceder_pantalla,
    navegacion_global_bloqueada_en_partida,
    pantalla_campo_texto_activo,
    pantalla_en_partida_activa,
    pulsar_boton_indice,
    tecla_es_avanzar,
    tecla_es_retroceso,
    tecla_opcion_numerica,
    tipo_barra_fija_para_tecla,
)
from Grafico.menu_opciones import OverlayOpcionesGrafico
from Comun.preferencias_grafico import debe_saltar_bienvenida_grafico
from Grafico.pantallas import MenuPrincipal, Pantalla
from Grafico.pantallas_inicio import PantallaBienvenida
from Grafico.pantallas_sistema import PantallaFeedback, PantallaInfoHub, PantallaInfoTexto

_ETIQUETA_ICONO_FIJO_SIN_EMOJI: dict[str, str] = {
    "pausa": "PA",
    "diarios": "DI",
    "examen_fijo": "EF",
    "ranking": "IN",
    "feedback": "FB",
    "opciones": "OP",
}

_ICONOS_FIJOS_CFG: tuple[tuple[str, str], ...] = (
    ("pausa", TOOLTIP_PAUSA),
    ("diarios", ""),
    ("ranking", TOOLTIP_RANKING),
    ("feedback", TOOLTIP_FEEDBACK),
    ("opciones", TOOLTIP_OPCIONES),
)


def _clave_icono_barra(tipo: str, perfil: PerfilContenido) -> str:
    if tipo == "diarios" and perfil.examen_fijo_barra_completo:
        return "examen_fijo"
    return tipo


def crear_botones_iconos_fijos(
    fuentes: dict[str, pygame.font.Font],
    handlers: dict[str, Callable[[], None]] | None = None,
) -> list[tuple[Boton, str]]:
    """Rectángulos e iconos de la barra fija superior (pausa, diarios, …)."""
    fuente_ref = fuentes["menu"]
    w = ancho_icono_fijo(fuente_ref)
    h = alto_icono_fijo(fuente_ref)
    resultado: list[tuple[Boton, str]] = []
    x_actual = X_ICONOS_FIJOS
    noop: Callable[[], None] = lambda: None
    hdl = handlers or {}
    for tipo_icono, tooltip in _ICONOS_FIJOS_CFG:
        boton = Boton(
            "",
            pygame.Rect(x_actual, Y_ICONOS_FIJOS, w, h),
            hdl.get(tipo_icono, noop),
            mostrar_texto=False,
            tooltip=tooltip,
        )
        resultado.append((boton, tipo_icono))
        x_actual += w + GAP_ICONOS_FIJOS
    return resultado


def dibujar_icono_fijo_en(
    superficie: pygame.Surface,
    fuentes: dict[str, pygame.font.Font],
    tipo: str,
    rect: pygame.Rect,
    *,
    activo: bool = True,
    hover: bool = False,
) -> None:
    """Dibuja un botón de la barra fija (fondo + icono). Mismos blancos/grises que los botones del menú."""
    fondo, color_icono, borde = colores_boton(activo=activo, hover=hover)
    alpha_icono = 255

    pygame.draw.rect(superficie, fondo, rect, border_radius=8)
    pygame.draw.rect(superficie, borde, rect, width=2, border_radius=8)

    chip = rect.inflate(-8, -6)
    fuente = fuentes.get("icono_emoji") or fuentes["menu"]
    texto = emoji_icono(tipo) or _ETIQUETA_ICONO_FIJO_SIN_EMOJI.get(tipo, "")
    try:
        surf = fuente.render(texto, True, color_icono)
        if surf.get_width() > 4:
            if alpha_icono < 255:
                surf = surf.copy()
                surf.set_alpha(alpha_icono)
            superficie.blit(surf, surf.get_rect(center=chip.center))
            return
    except Exception:
        pass
    if tipo == "pausa":
        bar_w = max(3, chip.width // 8)
        bar_h = chip.height // 2
        cx = chip.centerx
        y = chip.centery - bar_h // 2
        pygame.draw.rect(
            superficie,
            color_icono,
            pygame.Rect(cx - bar_w - 3, y, bar_w, bar_h),
            border_radius=2,
        )
        pygame.draw.rect(
            superficie,
            color_icono,
            pygame.Rect(cx + 3, y, bar_w, bar_h),
            border_radius=2,
        )
        return
    if tipo == "opciones":
        cx, cy = chip.center
        r = max(6, min(chip.width, chip.height) // 4)
        pygame.draw.circle(superficie, color_icono, (cx, cy), r, width=2)
        for i in range(8):
            ang = i * math.pi / 4
            x1 = cx + int((r + 2) * math.cos(ang))
            y1 = cy + int((r + 2) * math.sin(ang))
            pygame.draw.circle(superficie, color_icono, (x1, y1), 2)
        return
    margin = max(4, chip.width // 10)
    envelope = pygame.Rect(
        chip.x + margin,
        chip.y + margin,
        chip.width - 2 * margin,
        chip.height - 2 * margin,
    )
    pygame.draw.rect(superficie, color_icono, envelope, width=2, border_radius=3)
    pygame.draw.line(
        superficie,
        color_icono,
        (envelope.left + 2, envelope.top + 2),
        (envelope.centerx, envelope.centery + 1),
        2,
    )
    pygame.draw.line(
        superficie,
        color_icono,
        (envelope.right - 2, envelope.top + 2),
        (envelope.centerx, envelope.centery + 1),
        2,
    )


def dibujar_barra_iconos_fijos(
    superficie: pygame.Surface,
    fuentes: dict[str, pygame.font.Font],
) -> None:
    """Barra fija superior como en el bucle principal de la aplicación."""
    for boton, tipo in crear_botones_iconos_fijos(fuentes):
        dibujar_icono_fijo_en(
            superficie,
            fuentes,
            tipo,
            boton.rect,
            activo=True,
            hover=boton.hover,
        )


@dataclass
class DatosJuego:
    num_preguntas: int
    num_materias: int
    preguntas: list[Pregunta]
    materias_meta: dict[str, dict[str, str]]
    path_preguntas_csv: Path
    path_plantillas_json: Path | None = None
    path_listado_materias: Path | None = None
    perfil: PerfilContenido = field(default_factory=PerfilContenido.completo)
    avisos_carga: tuple[str, ...] = ()
    abrir_feedback: Callable[[], None] | None = field(default=None, repr=False, compare=False)


class AplicacionGrafica:
    """Ventana pygame con menú y modos jugables."""

    def __init__(self, datos: DatosJuego, *, saltar_bienvenida: bool = False) -> None:
        pygame.init()
        pygame.display.set_caption(TITULO_VENTANA)
        self.pantalla = pygame.display.set_mode((ANCHO, ALTO))
        self.reloj = pygame.time.Clock()
        self.datos = datos
        datos.abrir_feedback = self._abrir_feedback
        self.fuentes = crear_fuentes()
        self.ejecutando = True
        if saltar_bienvenida or debe_saltar_bienvenida_grafico():
            self.actual: Pantalla = MenuPrincipal(datos, self._ir_a, self._salir)
        else:
            self.actual = PantallaBienvenida(datos, self._ir_a, self._salir)
        self._menu_pausa_abierto = False
        self._menu_opciones_abierto = False
        self._overlay_opciones: OverlayOpcionesGrafico | None = None
        self._anterior: Pantalla | None = None
        self._pantalla_antes_info: Pantalla | None = None
        self._botones_fijos = self._crear_botones_fijos()
        self._tooltips_barra_originales = {
            tipo: (boton.tooltip or "")
            for boton, tipo in self._botones_fijos
        }
        self._actualizar_estado_barra_fija()
        self._botones_pausa: list[Boton] = []

    def _ir_a(self, pantalla: Pantalla) -> None:
        self.actual = pantalla
        if not isinstance(
            pantalla,
            (PantallaFeedback, PantallaInfoHub, PantallaInfoTexto),
        ):
            self._anterior = None

    def _navegar_auxiliar(self, pantalla: Pantalla) -> None:
        self.actual = pantalla

    def _salir(self) -> None:
        self.ejecutando = False

    def _restaurar_vista_actual(self) -> None:
        """Vista completa de la pantalla en curso (redibujado integral)."""
        self.actual.restaurar_vista_completa()

    def _pantalla_en_contexto(self) -> Pantalla:
        if isinstance(
            self.actual,
            (PantallaFeedback, PantallaInfoHub, PantallaInfoTexto),
        ) and self._anterior is not None:
            return self._anterior
        return self.actual

    def _ir_a_menu_principal(self) -> None:
        self._ir_a(MenuPrincipal(self.datos, self._ir_a, self._salir))

    def _en_partida(self) -> bool:
        return pantalla_en_partida_activa(self._pantalla_en_contexto())

    def _tipo_barra_permitido(self, tipo: str) -> bool:
        """Blanco en barra = permitido; gris = sin clic ni atajo de barra asociado."""
        if isinstance(self.actual, PantallaBienvenida):
            return False
        if getattr(self.actual, "popup_bloqueante", lambda: False)():
            return False
        if self._menu_opciones_abierto:
            return tipo in ("pausa", "opciones")
        if self._menu_pausa_abierto:
            return tipo in ("pausa", "feedback")
        if pantalla_en_partida_activa(self.actual):
            return tipo == "pausa"
        if tipo == "diarios":
            return self.datos.perfil.modos_diarios_disponibles
        return True

    def _actualizar_estado_barra_fija(self) -> None:
        en_partida = pantalla_en_partida_activa(self.actual)
        for boton, tipo in self._botones_fijos:
            permitido = self._tipo_barra_permitido(tipo)
            boton.activo = permitido
            if not permitido:
                boton.hover = False
            if permitido:
                if tipo == "diarios":
                    boton.tooltip = tooltip_barra_diarios(self.datos.perfil)
                else:
                    boton.tooltip = self._tooltips_barra_originales.get(tipo, boton.tooltip)
            elif self._menu_opciones_abierto and tipo not in ("pausa", "opciones"):
                boton.tooltip = TOOLTIP_BARRA_DURANTE_OPCIONES
            elif self._menu_pausa_abierto and tipo not in ("pausa", "feedback"):
                boton.tooltip = TOOLTIP_BARRA_DURANTE_PAUSA
            elif isinstance(self.actual, PantallaBienvenida):
                boton.tooltip = TOOLTIP_BARRA_BIENVENIDA
            elif en_partida and tipo != "pausa":
                boton.tooltip = TOOLTIP_BARRA_DURANTE_PARTIDA
            elif tipo == "diarios":
                boton.tooltip = (
                    self.datos.perfil.motivo_modo_no_disponible("diarios")
                    or self._tooltips_barra_originales.get(tipo, "")
                )

    def _crear_botones_fijos(self) -> list[tuple[Boton, str]]:
        return crear_botones_iconos_fijos(
            self.fuentes,
            handlers={
                "pausa": self._toggle_pausa,
                "diarios": self._abrir_diarios,
                "ranking": self._abrir_info,
                "feedback": self._abrir_feedback,
                "opciones": self._toggle_opciones,
            },
        )

    def _crear_botones_pausa(self) -> None:
        en_partida = self._en_partida()
        etiquetas = [
            etiqueta_menu(*(BTN_CONTINUAR_PARTIDA if en_partida else BTN_CONTINUAR)),
            etiqueta_menu(*BTN_PANTALLA_TITULO),
            etiqueta_menu(*BTN_SALIR_PROGRAMA),
        ]
        acciones = [
            self._continuar_desde_pausa,
            self._pantalla_titulo_desde_pausa,
            self._salir,
        ]
        rects = rects_botones_apilados(
            etiquetas,
            self.fuentes["menu"],
            x_centro=ANCHO // 2,
            y0=290,
            gap=12,
            ancho_min=420,
            alto_min=48,
        )
        tip_cont, tip_titulo, tip_salir = tooltips_menu_pausa(en_partida=en_partida)
        self._botones_pausa = [
            Boton(etiq, rect, accion, tooltip=tip)
            for etiq, rect, accion, tip in zip(
                etiquetas,
                rects,
                acciones,
                (tip_cont, tip_titulo, tip_salir),
                strict=True,
            )
        ]

    def _overlay_abierto(self) -> bool:
        return self._menu_pausa_abierto or self._menu_opciones_abierto

    def _barra_fija_bloqueada(self) -> bool:
        """Popups modales: bienvenida, pausa, opciones y avisos en partida."""
        return self._overlay_abierto() or self.actual.popup_bloqueante()

    def _reset_hover_barra_fija(self) -> None:
        for boton, _tipo in self._botones_fijos:
            boton.hover = False

    def _cerrar_opciones_guardando(self) -> None:
        if self._overlay_opciones is not None:
            self._overlay_opciones.guardar_y_cerrar()
        else:
            self._cerrar_menu_opciones()

    def _abrir_menu_opciones(self) -> None:
        if self._menu_pausa_abierto:
            return
        self._menu_opciones_abierto = True
        export_dataset = None
        perfil = self.datos.perfil
        if perfil.modo_minimo and perfil.csv_minimal:
            from Comun.rutas import resolver_dir_informes
            from Grafico.menu_opciones import ExportDatasetOpciones

            export_dataset = ExportDatasetOpciones(
                preguntas=tuple(self.datos.preguntas),
                carpeta=resolver_dir_informes(),
            )
        self._overlay_opciones = OverlayOpcionesGrafico(
            on_cerrar=self._cerrar_menu_opciones,
            export_dataset=export_dataset,
        )
        self._actualizar_estado_barra_fija()

    def _cerrar_menu_opciones(self) -> None:
        self._menu_opciones_abierto = False
        self._overlay_opciones = None
        self._refrescar_tras_opciones()

    def _refrescar_tras_opciones(self) -> None:
        from Grafico.pantallas import MenuPrincipal

        pantalla = self.actual
        if isinstance(pantalla, MenuPrincipal):
            self.actual = MenuPrincipal(self.datos, self._ir_a, self._salir)
        elif hasattr(pantalla, "_pantalla_actual"):
            self.actual = pantalla._pantalla_actual()
        else:
            self._restaurar_vista_actual()
        self._actualizar_estado_barra_fija()

    def _toggle_opciones(self) -> None:
        if self._menu_opciones_abierto:
            if self._overlay_opciones is not None:
                self._overlay_opciones.guardar_y_cerrar()
            else:
                self._cerrar_menu_opciones()
            return
        if not self._tipo_barra_permitido("opciones"):
            return
        if self._menu_pausa_abierto:
            return
        self._abrir_menu_opciones()

    def _abrir_menu_pausa(self) -> None:
        if self._menu_opciones_abierto:
            self._cerrar_opciones_guardando()
        if self._menu_pausa_abierto:
            return
        self._menu_pausa_abierto = True
        self._crear_botones_pausa()
        self._actualizar_estado_barra_fija()

    def _cerrar_menu_pausa(self) -> None:
        self._menu_pausa_abierto = False
        self._actualizar_estado_barra_fija()

    def _continuar_desde_pausa(self) -> None:
        self._cerrar_menu_pausa()
        self._restaurar_vista_actual()

    def _pantalla_titulo_desde_pausa(self) -> None:
        self._cerrar_menu_pausa()
        self._ir_a_menu_principal()

    def _toggle_pausa(self) -> None:
        if self._menu_pausa_abierto:
            self._salir()
            return
        self._abrir_menu_pausa()

    def _en_flujo_info(self) -> bool:
        if self._pantalla_antes_info is None:
            return False
        from Grafico.pantallas_sistema import PantallaEstadisticasJugador
        from Grafico.pantallas_sistema import PantallaInfoHub, PantallaInfoTexto

        return isinstance(
            self.actual,
            (PantallaInfoHub, PantallaInfoTexto, PantallaEstadisticasJugador),
        )

    def _cerrar_info(self) -> None:
        if self._pantalla_antes_info is None:
            return
        pantalla_previa = self._pantalla_antes_info
        self._pantalla_antes_info = None
        self.actual = pantalla_previa
        pantalla_previa.restaurar_vista_completa()
        self._actualizar_estado_barra_fija()

    def _abrir_info(self) -> None:
        if self._en_flujo_info():
            self._cerrar_info()
            return
        if self._overlay_abierto():
            return
        if not self._tipo_barra_permitido("ranking"):
            return
        pantalla_previa = self.actual
        self._pantalla_antes_info = pantalla_previa

        def volver() -> None:
            self._pantalla_antes_info = None
            self.actual = pantalla_previa
            pantalla_previa.restaurar_vista_completa()
            self._actualizar_estado_barra_fija()

        self.actual = PantallaInfoHub(
            volver,
            navegar=self._navegar_auxiliar,
            perfil=self.datos.perfil,
        )

    def _boton_barra_por_tipo(self, tipo: str) -> Boton | None:
        for boton, tid in self._botones_fijos:
            if tid == tipo:
                return boton
        return None

    def _abrir_feedback(self) -> None:
        if self._menu_opciones_abierto:
            return
        if isinstance(self.actual, PantallaFeedback):
            self.actual.volver()
            return
        if not self._tipo_barra_permitido("feedback"):
            return
        if self._menu_pausa_abierto:
            self._cerrar_menu_pausa()
        self._anterior = self.actual

        def volver() -> None:
            pantalla_previa = self._anterior
            self._anterior = None
            if pantalla_previa is None:
                return
            self.actual = pantalla_previa
            pantalla_previa.restaurar_vista_completa()

        self.actual = PantallaFeedback(volver)

    def _cerrar_diarios_si_abierto(self) -> bool:
        from Comun.modos_diarios import ID_PRESET_EXAMEN_FIJO
        from Grafico.pantallas_examen_fijo import ConfigOpcionesHistoria
        from Grafico.pantallas_modos import ConfigModosDiarios

        if isinstance(self.actual, ConfigModosDiarios):
            self.actual.boton_volver.al_pulsar()
            return True
        if (
            isinstance(self.actual, ConfigOpcionesHistoria)
            and self.actual.preset.id == ID_PRESET_EXAMEN_FIJO
        ):
            self.actual.boton_atras.al_pulsar()
            return True
        return False

    def _abrir_diarios(self) -> None:
        if self._cerrar_diarios_si_abierto():
            return
        if self._overlay_abierto():
            return
        if not self._tipo_barra_permitido("diarios"):
            return
        if not self.datos.perfil.modos_diarios_disponibles:
            return
        if self.datos.perfil.examen_fijo_barra_completo:
            from Grafico.pantallas_modos import abrir_config_examen_fijo

            abrir_config_examen_fijo(self.datos, self._ir_a, self._salir)
            return
        from Grafico.pantallas_modos import ConfigModosDiarios

        self._ir_a(ConfigModosDiarios(self.datos, self._ir_a, self._salir))

    def _manejar_hover_fijos(self, pos: tuple[int, int]) -> None:
        if self._barra_fija_bloqueada():
            self._reset_hover_barra_fija()
            return
        for b, _tipo in self._botones_fijos:
            b.actualizar_hover(pos)

    def _manejar_clic_fijos(self, pos: tuple[int, int], boton: int) -> bool:
        if self._barra_fija_bloqueada():
            return False
        return any(b.manejar_clic(pos, boton) for b, _tipo in self._botones_fijos)

    def _manejar_hover_pausa(self, pos: tuple[int, int]) -> None:
        for boton in self._botones_pausa:
            boton.actualizar_hover(pos)

    def _manejar_feedback_en_pausa(self, evento: pygame.event.Event) -> bool:
        """El icono de feedback sigue activo con el menú de pausa abierto."""
        feedback = self._boton_barra_por_tipo("feedback")
        if feedback is None:
            return False
        if evento.type == pygame.MOUSEMOTION:
            feedback.actualizar_hover(evento.pos)
            return False
        if evento.type == pygame.MOUSEBUTTONDOWN:
            return feedback.manejar_clic(evento.pos, evento.button)
        return False

    def _manejar_clic_pausa(self, pos: tuple[int, int], boton: int) -> None:
        for btn in self._botones_pausa:
            if btn.manejar_clic(pos, boton):
                break

    def _manejar_interaccion_barra_fija_overlay(self, evento: pygame.event.Event) -> bool:
        if evento.type == pygame.MOUSEMOTION:
            for boton, _tipo in self._botones_fijos:
                if boton.activo:
                    boton.actualizar_hover(evento.pos)
                else:
                    boton.hover = False
            return False
        if evento.type == pygame.MOUSEBUTTONDOWN:
            return any(
                b.manejar_clic(evento.pos, evento.button)
                for b, _tipo in self._botones_fijos
                if b.activo
            )
        return False

    def _manejar_eventos_overlay(self, evento: pygame.event.Event) -> None:
        if self._menu_opciones_abierto and self._overlay_opciones is not None:
            if self._manejar_teclado_opciones(evento):
                return
            if self._manejar_interaccion_barra_fija_overlay(evento):
                return
            self._overlay_opciones.manejar_evento(evento)
            return
        if not self._menu_pausa_abierto:
            return
        if self._manejar_teclado_pausa(evento):
            return
        if self._manejar_feedback_en_pausa(evento):
            return
        if self._manejar_interaccion_barra_fija_overlay(evento):
            return
        if evento.type == pygame.MOUSEMOTION:
            self._manejar_hover_pausa(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            self._manejar_clic_pausa(evento.pos, evento.button)

    def _manejar_teclado_opciones(self, evento: pygame.event.Event) -> bool:
        if evento.type != pygame.KEYDOWN or self._overlay_opciones is None:
            return False
        overlay = self._overlay_opciones
        if overlay.campo_nombre.activo:
            return False
        if evento.key == pygame.K_ESCAPE:
            self._cerrar_opciones_guardando()
            self._abrir_menu_pausa()
            return True
        if evento.key == pygame.K_o:
            overlay.guardar_y_cerrar()
            return True
        if tecla_es_retroceso(evento.key):
            self._cerrar_menu_opciones()
            return True
        if tecla_es_avanzar(evento.key):
            from Grafico.atajos_teclado import pulsar_boton_si_activo

            pulsar_boton_si_activo(overlay.boton_listo)
            return True
        return False

    def _manejar_teclado_pausa(self, evento: pygame.event.Event) -> bool:
        if evento.type != pygame.KEYDOWN:
            return False
        if tecla_es_avanzar(evento.key):
            pulsar_boton_indice(self._botones_pausa, 1)
            return True
        if tecla_es_retroceso(evento.key):
            pulsar_boton_indice(self._botones_pausa, 2)
            return True
        if evento.key == pygame.K_ESCAPE:
            pulsar_boton_indice(self._botones_pausa, 3)
            return True
        if evento.key == pygame.K_f:
            if not self._tipo_barra_permitido("feedback"):
                return True
            self._abrir_feedback()
            return True
        indice = tecla_opcion_numerica(evento.key)
        if indice is not None:
            pulsar_boton_indice(self._botones_pausa, indice)
            return True
        return True

    def _ejecutar_atajo_barra_fija(self, tipo: str) -> bool:
        """Tecla de barra: solo actúa si el icono está permitido (blanco)."""
        if not self._tipo_barra_permitido(tipo):
            return True
        if tipo == "pausa":
            self._toggle_pausa()
        elif tipo == "diarios":
            self._abrir_diarios()
        elif tipo == "ranking":
            self._abrir_info()
        elif tipo == "feedback":
            self._abrir_feedback()
        elif tipo == "opciones":
            self._toggle_opciones()
        return True

    def _manejar_teclado_global(self, evento: pygame.event.Event) -> bool:
        if evento.type != pygame.KEYDOWN:
            return False
        if pantalla_campo_texto_activo(self.actual):
            return False

        fase = getattr(self.actual, "fase", None)

        tipo_barra = tipo_barra_fija_para_tecla(evento.key)
        if tipo_barra is not None:
            return self._ejecutar_atajo_barra_fija(tipo_barra)

        if tecla_es_retroceso(evento.key):
            if (
                self.actual.popup_bloqueante()
                or navegacion_global_bloqueada_en_partida(
                    self.actual,
                    menu_pausa_abierto=self._menu_pausa_abierto,
                )
            ):
                return True
            if fase in _FASES_PARTIDA_SIN_RETROCESO:
                return False
            return atajo_retroceder_pantalla(self.actual)

        if tecla_es_avanzar(evento.key):
            if fase in _FASES_PARTIDA_SIN_RETROCESO:
                return False
            return atajo_avanzar_pantalla(self.actual)

        indice = tecla_opcion_numerica(evento.key)
        if indice is not None:
            return atajo_opcion_numerica_pantalla(self.actual, indice)

        return False

    def _manejar_eventos_pausa(self, evento: pygame.event.Event) -> None:
        self._manejar_eventos_overlay(evento)

    def _dibujar_pantalla_actual(self) -> None:
        self.actual.dibujar(self.pantalla)

    def _procesar_evento(self, evento: pygame.event.Event) -> None:
        if evento.type == pygame.QUIT:
            self.ejecutando = False
            return
        if self._overlay_abierto():
            self._manejar_eventos_overlay(evento)
            return
        if self._manejar_teclado_global(evento):
            return
        if evento.type == pygame.MOUSEMOTION:
            self._manejar_hover_fijos(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if self._manejar_clic_fijos(evento.pos, evento.button):
                return
        nueva = self.actual.manejar_evento(evento)
        if nueva is not None:
            self.actual = nueva

    def _dibujar_barra_fija(self) -> None:
        """Barra superior encima del velo modal (no se atenúa con la pausa)."""
        for b, tipo in self._botones_fijos:
            clave = _clave_icono_barra(tipo, self.datos.perfil)
            dibujar_icono_fijo_en(
                self.pantalla,
                self.fuentes,
                clave,
                b.rect,
                activo=b.activo,
                hover=b.hover,
            )
        if not self._barra_fija_bloqueada():
            tooltips_barra = [b for b, _tipo in self._botones_fijos if b.activo]
        elif self._menu_opciones_abierto:
            tooltips_barra = [b for b, _tipo in self._botones_fijos if b.activo]
        elif self._menu_pausa_abierto:
            tooltips_barra = [b for b, _tipo in self._botones_fijos if b.activo]
        else:
            tooltips_barra = []
        if tooltips_barra:
            dibujar_tooltips_botones(
                self.pantalla,
                self.fuentes["pequena"],
                tooltips_barra,
            )

    def _dibujar_overlays_y_tooltips(self) -> None:
        if self._barra_fija_bloqueada():
            dibujar_overlay_atenuacion(self.pantalla)
        if self._menu_pausa_abierto:
            self._dibujar_contenido_menu_pausa()
        elif self._menu_opciones_abierto and self._overlay_opciones is not None:
            self._overlay_opciones.dibujar_contenido(self.pantalla)
        elif self.actual.popup_bloqueante():
            self.actual.dibujar_contenido_popup_bloqueante(self.pantalla)

    def ejecutar(self) -> None:
        while self.ejecutando:
            for evento in pygame.event.get():
                self._procesar_evento(evento)
                if not self.ejecutando:
                    break

            if not self._overlay_abierto():
                cambio = self.actual.actualizar()
                if cambio is not None:
                    self.actual = cambio

            self._actualizar_estado_barra_fija()
            self._dibujar_pantalla_actual()
            self._dibujar_overlays_y_tooltips()
            self._dibujar_barra_fija()

            pygame.display.flip()
            self.reloj.tick(FPS)
        pygame.quit()

    def _dibujar_contenido_menu_pausa(self) -> None:
        panel = pygame.Rect(MARGEN + 40, 150, ANCHO - 2 * (MARGEN + 40), 380)
        dibujar_panel(self.pantalla, panel, color=COLOR_BOTON)

        dibujar_texto_centro(
            self.pantalla,
            "PAUSA",
            (ANCHO // 2, panel.y + 50),
            self.fuentes["titulo"].get_height(),
            (25, 25, 30),
            bold=True,
        )

        dibujar_texto_centro(
            self.pantalla,
            f"Estás en: {self._pantalla_en_contexto().titulo_pausa()}",
            (ANCHO // 2, panel.y + 100),
            self.fuentes["cuerpo"].get_height(),
            (70, 80, 95),
        )

        for boton in self._botones_pausa:
            boton.dibujar(self.pantalla, self.fuentes["menu"])
        dibujar_tooltips_botones(
            self.pantalla, self.fuentes["pequena"], self._botones_pausa
        )
