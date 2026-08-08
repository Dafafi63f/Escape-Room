#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pantallas de sistema: info del juego y feedback al creador."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

import pygame

from Grafico.changelog_juego import cargar_changelog_juego_grafico
from Comun.feedback import texto_bloque_contacto_alternativo
from Comun.estadisticas_jugador import formatear_panel_estadisticas
from Comun.version import texto_version_completo
from Grafico.pantallas import Pantalla
from Grafico.tema import (
    ALTO,
    ANCHO,
    COLOR_FONDO,
    COLOR_TEXTO,
    COLOR_TEXTO_PANEL,
    COLOR_TITULO,
    MARGEN,
    TAMANO_FUENTE_PEQUENA,
    Y_INICIO_TITULO,
    crear_fuentes,
)
from Grafico.texto import dibujar_texto_centro, preparar_texto_ui, renderizar_texto_mixto
from Grafico.textos_grafico import BTN_VOLVER, etiqueta, texto_controles_juego_grafico, titulo_pantalla
from Grafico.ui import (
    Boton,
    capturar,
    dibujar_panel,
    dibujar_tooltips_botones,
    partir_texto,
    partir_texto_con_sangria,
    posicionar_pila_inferior,
    rect_boton_etiqueta,
    rects_botones_apilados,
)

_COLOR_TEXTO_INFO = (55, 65, 82)
_MARGEN_SCROLL = 14
_GAP_TRAS_SUBTITULO = 18
_PAD_CONTACTO = 14
_GAP_CONTACTO_BOTONES = 16
_Y_PANEL_TEXTO = Y_INICIO_TITULO + 36
_MARGEN_INF_VOLVER = 24
_ALTO_MIN_VOLVER = 48
_GAP_PANEL_VOLVER = 12
_ESPACIO_HINT_SCROLL = 36


def _texto_contacto_hub() -> str:
    return f"{texto_version_completo()}\n\n{texto_bloque_contacto_alternativo()}"


def _dibujar_hint_scroll_raton(
    superficie: pygame.Surface,
    fuente: pygame.font.Font,
    *,
    y_centro: int,
    texto: str = "Rueda del ratón para desplazarte",
) -> None:
    """Hint sobre fondo oscuro, centrado en la franja entre panel y botones."""
    hint = fuente.render(preparar_texto_ui(texto), True, COLOR_TEXTO)
    superficie.blit(hint, hint.get_rect(center=(ANCHO // 2, y_centro)))


def _lineas_texto_panel(
    fuente: pygame.font.Font,
    texto: str,
    ancho: int,
) -> list[str]:
    lineas: list[str] = []
    for bloque in texto.split("\n"):
        if not bloque.strip():
            lineas.append("")
            continue
        lineas.extend(partir_texto(fuente, bloque, ancho))
    return lineas


def _alto_contenido_bloques(
    fuente_cuerpo: pygame.font.Font,
    fuente_titulo: pygame.font.Font,
    bloques: Sequence[tuple[str, list[str]]],
) -> int:
    alto_linea = fuente_cuerpo.get_linesize() + 4
    alto = 12
    for indice, (titulo, lineas) in enumerate(bloques):
        if indice > 0:
            alto += 12
        alto += fuente_titulo.get_height() + 8 + len(lineas) * alto_linea
    alto += 12
    return alto


@dataclass(frozen=True)
class SeccionInfo:
    id: str
    titulo: str
    emoji: str
    tooltip: str


SECCIONES_INFO: tuple[SeccionInfo, ...] = (
    SeccionInfo(
        "estadisticas",
        "Mis estadísticas",
        "📊",
        "Evolucion, records y materias a repasar.",
    ),
    SeccionInfo(
        "changelog_juego",
        "Novedades del juego",
        "🎮",
        "Cambios recientes en la interfaz gráfica.",
    ),
)


def _etiqueta_seccion(seccion: SeccionInfo) -> str:
    return f"{seccion.emoji} {seccion.titulo}"


class PantallaInfoTexto(Pantalla):
    """Texto informativo con desplazamiento vertical."""

    def __init__(
        self,
        titulo: str,
        contenido: str,
        volver_a: Callable[[], None],
    ) -> None:
        self.titulo = titulo
        self.contenido = contenido
        self.volver_a = volver_a
        self.fuentes = crear_fuentes()
        self.scroll = 0
        self.boton_volver = Boton(
            etiqueta(*BTN_VOLVER),
            rect_boton_etiqueta(
                etiqueta(*BTN_VOLVER),
                self.fuentes["menu"],
                x_centro=ANCHO // 2,
                y=0,
                alto_min=_ALTO_MIN_VOLVER,
            ),
            self.volver_a,
        )
        posicionar_pila_inferior(
            [self.boton_volver],
            x_centro=ANCHO // 2,
            gap=0,
            margen_inferior=_MARGEN_INF_VOLVER,
        )
        y_panel_inf = self.boton_volver.rect.top - _GAP_PANEL_VOLVER - _ESPACIO_HINT_SCROLL
        self._panel = pygame.Rect(
            MARGEN,
            _Y_PANEL_TEXTO,
            ANCHO - 2 * MARGEN,
            max(120, y_panel_inf - _Y_PANEL_TEXTO),
        )
        self._lineas = self._construir_lineas()

    def _construir_lineas(self) -> list[str]:
        fuente = self.fuentes["pequena"]
        ancho = self._panel.width - 24
        lineas: list[str] = []
        for bloque in self.contenido.split("\n"):
            if not bloque.strip():
                lineas.append("")
                continue
            lineas.extend(
                partir_texto_con_sangria(
                    fuente,
                    bloque,
                    ancho,
                    tamano_pt=TAMANO_FUENTE_PEQUENA,
                )
            )
        return lineas

    def _max_scroll(self) -> int:
        fuente = self.fuentes["pequena"]
        alto_linea = fuente.get_linesize() + 4
        alto_total = len(self._lineas) * alto_linea + 16
        return max(0, alto_total - self._panel.height)

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEWHEEL:
            self.scroll = max(0, min(self._max_scroll(), self.scroll - int(evento.y) * 24))
        elif evento.type == pygame.MOUSEMOTION:
            self.boton_volver.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            self.boton_volver.manejar_clic(evento.pos, evento.button)
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        dibujar_texto_centro(
            superficie,
            titulo_pantalla(self.titulo),
            (ANCHO // 2, Y_INICIO_TITULO),
            self.fuentes["titulo"].get_height(),
            COLOR_TITULO,
            bold=True,
        )
        dibujar_panel(superficie, self._panel, color=(255, 255, 255))
        fuente = self.fuentes["pequena"]
        alto_linea = fuente.get_linesize() + 4
        y = self._panel.y + 12 - self.scroll
        for linea in self._lineas:
            if y + alto_linea >= self._panel.y and y <= self._panel.bottom:
                if linea:
                    linea_ui = preparar_texto_ui(linea)
                    x = self._panel.x + 12
                    renderizar_texto_mixto(
                        superficie,
                        linea_ui,
                        (x, y),
                        _COLOR_TEXTO_INFO,
                        TAMANO_FUENTE_PEQUENA,
                    )
            y += alto_linea
            if y > self._panel.bottom + alto_linea:
                break
        if self._max_scroll() > 0:
            _dibujar_hint_scroll_raton(
                superficie,
                fuente,
                y_centro=self._panel.bottom + _ESPACIO_HINT_SCROLL // 2,
            )
        self.boton_volver.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(superficie, self.fuentes["pequena"], [self.boton_volver])


class PantallaEstadisticasJugador(PantallaInfoTexto):
    """Resumen de evolución, récords y materias débiles."""

    def __init__(self, volver_a: Callable[[], None], *, perfil=None) -> None:
        super().__init__(
            "Mis estadísticas",
            formatear_panel_estadisticas(perfil),
            volver_a,
        )


class PantallaInfoHub(Pantalla):
    """Menú unificado: estadísticas, contacto y changelog."""

    def titulo_pausa(self) -> str:
        return "Info del juego"

    def __init__(
        self,
        volver: Callable[[], None],
        *,
        navegar: Callable[[Pantalla], None],
        perfil=None,
    ) -> None:
        self.volver = volver
        self._navegar = navegar
        self._perfil = perfil
        self.fuentes = crear_fuentes()
        self.scroll = 0
        self._bloques_info = (
            ("Controles del juego", self._construir_lineas_controles()),
            ("Contacto del creador", self._construir_lineas_contacto()),
        )
        self._construir_layout_paneles()
        self._crear_botones()

    def _ancho_texto_panel(self) -> int:
        return ANCHO - 2 * MARGEN - 24

    def _construir_lineas_controles(self) -> list[str]:
        return _lineas_texto_panel(
            self.fuentes["pequena"],
            texto_controles_juego_grafico(),
            self._ancho_texto_panel(),
        )

    def _construir_lineas_contacto(self) -> list[str]:
        return _lineas_texto_panel(
            self.fuentes["pequena"],
            _texto_contacto_hub(),
            self._ancho_texto_panel(),
        )

    def _construir_layout_paneles(self) -> None:
        alto_botones = len(SECCIONES_INFO) * 48 + max(0, len(SECCIONES_INFO) - 1) * 12
        y_volver_top = ALTO - 28 - 48
        self._y_botones_seccion = y_volver_top - _GAP_CONTACTO_BOTONES - alto_botones
        y_viewport = Y_INICIO_TITULO + 40 + _GAP_TRAS_SUBTITULO
        alto_viewport = max(
            120,
            self._y_botones_seccion
            - _GAP_CONTACTO_BOTONES
            - _ESPACIO_HINT_SCROLL
            - y_viewport,
        )
        self._rect_viewport = pygame.Rect(
            MARGEN,
            y_viewport,
            ANCHO - 2 * MARGEN,
            alto_viewport,
        )

    def _max_scroll(self) -> int:
        alto_total = _alto_contenido_bloques(
            self.fuentes["pequena"],
            self.fuentes["menu"],
            self._bloques_info,
        )
        return max(0, alto_total - self._rect_viewport.height)

    def _crear_botones(self) -> None:
        fuente = self.fuentes["menu"]
        etiquetas = [_etiqueta_seccion(s) for s in SECCIONES_INFO]
        rects = rects_botones_apilados(
            etiquetas,
            fuente,
            x_centro=ANCHO // 2,
            y0=self._y_botones_seccion,
            gap=12,
            ancho_min=460,
            alto_min=48,
        )
        self.botones_seccion: list[Boton] = []
        secciones = SECCIONES_INFO
        for seccion, rect in zip(secciones, rects, strict=True):
            tooltip = seccion.tooltip
            if seccion.id == "estadisticas" and self._perfil is not None and self._perfil.modo_minimo:
                tooltip = (
                    "Resumen, evolución semanal y récords "
                    "(libre, examen fijo y resistencia)."
                )
            self.botones_seccion.append(
                Boton(
                    _etiqueta_seccion(seccion),
                    rect,
                    capturar(self._al_pulsar, seccion.id),
                    tooltip=tooltip,
                )
            )
        self.boton_volver = Boton(
            etiqueta(*BTN_VOLVER),
            rect_boton_etiqueta(
                etiqueta(*BTN_VOLVER),
                fuente,
                x_centro=ANCHO // 2,
                y=0,
                alto_min=48,
            ),
            self.volver,
        )
        posicionar_pila_inferior(
            [self.boton_volver],
            x_centro=ANCHO // 2,
            gap=0,
            margen_inferior=28,
        )

    def _volver_al_hub(self) -> None:
        self._navegar(self)

    def _al_pulsar(self, seccion_id: str) -> None:
        if seccion_id == "estadisticas":
            self._navegar(PantallaEstadisticasJugador(self._volver_al_hub, perfil=self._perfil))
            return
        if seccion_id == "changelog_juego":
            self._navegar(
                PantallaInfoTexto(
                    "Novedades del juego",
                    cargar_changelog_juego_grafico(),
                    self._volver_al_hub,
                ),
            )

    def _botones_ui(self) -> list[Boton]:
        return [*self.botones_seccion, self.boton_volver]

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEWHEEL:
            self.scroll = max(
                0,
                min(self._max_scroll(), self.scroll - int(evento.y) * 24),
            )
        elif evento.type == pygame.MOUSEMOTION:
            for boton in self._botones_ui():
                boton.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            for boton in self._botones_ui():
                if boton.manejar_clic(evento.pos, evento.button):
                    break
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        dibujar_texto_centro(
            superficie,
            titulo_pantalla("INFO DEL JUEGO"),
            (ANCHO // 2, Y_INICIO_TITULO),
            self.fuentes["titulo"].get_height(),
            COLOR_TITULO,
            bold=True,
        )
        subt = self.fuentes["menu"].render(
            "Controles, estadísticas, contacto y novedades del juego.",
            True,
            COLOR_TEXTO_PANEL,
        )
        superficie.blit(subt, subt.get_rect(center=(ANCHO // 2, Y_INICIO_TITULO + 40)))
        self._dibujar_bloques_info(superficie)
        if self._max_scroll() > 0:
            _dibujar_hint_scroll_raton(
                superficie,
                self.fuentes["pequena"],
                y_centro=self._rect_viewport.bottom + _ESPACIO_HINT_SCROLL // 2,
            )
        for boton in self.botones_seccion:
            boton.dibujar(superficie, self.fuentes["menu"])
        self.boton_volver.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(superficie, self.fuentes["pequena"], self._botones_ui())

    def _blit_si_visible(
        self,
        superficie: pygame.Surface,
        render,
        y: int,
        x: int,
    ) -> None:
        if y + render.get_height() >= self._rect_viewport.y and y <= self._rect_viewport.bottom:
            superficie.blit(render, (x, y))

    def _dibujar_lineas_bloque_info(
        self,
        superficie: pygame.Surface,
        fuente,
        lineas: list[str],
        y: int,
        x: int,
        alto_linea: int,
    ) -> int:
        for linea in lineas:
            if y + alto_linea >= self._rect_viewport.y and y <= self._rect_viewport.bottom:
                if linea:
                    txt = fuente.render(linea, True, _COLOR_TEXTO_INFO)
                    superficie.blit(txt, (x, y))
            y += alto_linea
        return y

    def _dibujar_bloques_info(self, superficie: pygame.Surface) -> None:
        dibujar_panel(superficie, self._rect_viewport, color=(255, 255, 255))
        fuente = self.fuentes["pequena"]
        fuente_titulo = self.fuentes["menu"]
        alto_linea = fuente.get_linesize() + 4
        y = self._rect_viewport.y + 12 - self.scroll
        x = self._rect_viewport.x + _PAD_CONTACTO
        for indice, (titulo, lineas) in enumerate(self._bloques_info):
            if indice > 0:
                y += 12
            tit_render = fuente_titulo.render(titulo, True, _COLOR_TEXTO_INFO)
            self._blit_si_visible(superficie, tit_render, y, x)
            y += tit_render.get_height() + 8
            y = self._dibujar_lineas_bloque_info(
                superficie, fuente, lineas, y, x, alto_linea
            )

# --- Feedback ---

from collections.abc import Callable

import pygame

from Comun.feedback import AREAS_FEEDBACK, CATEGORIAS_FEEDBACK, indice_area_defecto
from Comun.preferencias_grafico import nombre_jugador_grafico
from Comun.rutas import etiqueta_dir_datos_jugador, resolver_config_creador_privado
from Comun.feedback import (
    CategoriaFeedback,
    ReporteFeedback,
    describir_resultado_envio,
    enviar_feedback,
)
from Grafico.pantallas import Pantalla
from Grafico.tema import (
    ALTO,
    ANCHO,
    COLOR_ACENTO,
    COLOR_FONDO,
    COLOR_TEXTO,
    COLOR_TITULO,
    MARGEN,
    Y_INICIO_TITULO,
    crear_fuentes,
)
from Grafico.texto import dibujar_texto_centro
from Grafico.textos_grafico import BTN_ENVIAR, BTN_VOLVER, etiqueta, etiqueta_campo, titulo_pantalla
from Grafico.ui import (
    Boton,
    CampoTexto,
    COLOR_BOTON_BORDE,
    COLOR_CAMPO_ACTIVO,
    COLOR_CAMPO_FONDO,
    capturar,
    dibujar_caja_valor_ciclo,
    dibujar_panel,
    dibujar_texto_multilinea,
    dibujar_tooltips_botones,
    partir_texto,
    posicionar_botones_fila,
    rect_boton_etiqueta,
)

_COLOR_ETIQUETA = (55, 65, 82)
_COLOR_PIE_FONDO = (190, 205, 225)
_ANCHO_BTN_CICLO = 44
_ALTO_CTRL = 40
_GAP_CICLO = 8
_X_ETIQUETA = 20
_ANCHO_ETIQUETA = 182
_GAP_ETIQUETA_CAMPO = 14
_PAD_PANEL = 20
_GAP_FILA = 22
_ALTO_MENSAJE_MIN = 72
_MARGEN_BOTONES = 24
_ALTO_BOTON = 48
_GAP_PIE_BOTONES = 10
_GAP_PANEL_PIE = 8
_INTERLINEA_PIE = 4


class CampoTextoArea:
    """Área de texto multilínea para el mensaje del aviso."""

    def __init__(
        self,
        rect: pygame.Rect,
        *,
        texto_inicial: str = "",
        longitud_max: int = 800,
        placeholder: str = "Describe el aviso con detalle…",
    ) -> None:
        self.rect = rect
        self.texto = texto_inicial
        self.longitud_max = longitud_max
        self.placeholder = placeholder
        self.activo = False

    def manejar_evento(self, evento: pygame.event.Event) -> bool:
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.activo = self.rect.collidepoint(evento.pos)
            return self.activo
        if not self.activo or evento.type != pygame.KEYDOWN:
            return False
        if evento.key == pygame.K_BACKSPACE:
            self.texto = self.texto[:-1]
            return True
        if evento.key == pygame.K_DELETE:
            return True
        if evento.key == pygame.K_ESCAPE:
            self.activo = False
            return True
        if evento.key == pygame.K_RETURN:
            if len(self.texto) < self.longitud_max:
                self.texto += "\n"
            return True
        char = evento.unicode
        if char.isprintable() and len(self.texto) < self.longitud_max:
            self.texto += char
            return True
        return False

    def dibujar(self, pantalla: pygame.Surface, fuente: pygame.font.Font) -> None:
        fondo = COLOR_CAMPO_ACTIVO if self.activo else COLOR_CAMPO_FONDO
        borde = COLOR_ACENTO if self.activo else COLOR_BOTON_BORDE
        pygame.draw.rect(pantalla, fondo, self.rect, border_radius=8)
        pygame.draw.rect(pantalla, borde, self.rect, width=2, border_radius=8)
        inner = pygame.Rect(
            self.rect.x + 10,
            self.rect.y + 8,
            self.rect.width - 20,
            self.rect.height - 16,
        )
        mostrar = self.texto if self.texto or self.activo else self.placeholder
        color = COLOR_TITULO if self.texto or self.activo else COLOR_TEXTO
        dibujar_texto_multilinea(pantalla, fuente, mostrar, inner, color)
        if self.activo and pygame.time.get_ticks() % 1000 < 500:
            lineas = partir_texto(fuente, self.texto, inner.width - 16) if self.texto else [""]
            alto_linea = fuente.get_linesize()
            y_cursor = inner.y + 8 + max(0, len(lineas) - 1) * alto_linea
            x_cursor = inner.x + 8 + fuente.size(lineas[-1])[0] + 2
            pygame.draw.line(
                pantalla,
                COLOR_TITULO,
                (x_cursor, y_cursor),
                (x_cursor, y_cursor + fuente.get_height()),
                2,
            )


class PantallaFeedback(Pantalla):
    """Formulario de aviso al creador y pantalla de resultado tras el envío."""

    def titulo_pausa(self) -> str:
        return "Modo feedback"

    def __init__(self, volver: Callable[[], None]) -> None:
        self.volver = volver
        self.fuentes = crear_fuentes()
        self._fase = "form"
        self._lineas_resultado: list[str] = []
        self._idx_categoria = 0
        self._idx_area = indice_area_defecto()
        self._lineas_pie = self._lineas_pie_formulario()
        self._construir_layout()
        self._crear_botones()

    def _x_campo(self) -> int:
        return self.panel.x + _X_ETIQUETA + _ANCHO_ETIQUETA + _GAP_ETIQUETA_CAMPO

    def _ancho_campo(self) -> int:
        return self.panel.right - _PAD_PANEL - self._x_campo()

    def _alto_fijo_panel(self, gap_fila: int) -> int:
        return 2 * _PAD_PANEL + 3 * _ALTO_CTRL + 3 * gap_fila

    def _construir_layout(self) -> None:
        self._y_titulo = Y_INICIO_TITULO
        y_panel_top = Y_INICIO_TITULO + 36

        self._y_botones = ALTO - _MARGEN_BOTONES - _ALTO_BOTON
        lineas_pie = self._lineas_pie
        alto_pie = self._medir_alto_pie(lineas_pie)
        pie_bottom = self._y_botones - _GAP_PIE_BOTONES
        pie_top = pie_bottom - alto_pie
        self._rect_pie = pygame.Rect(
            MARGEN,
            pie_top,
            ANCHO - 2 * MARGEN,
            alto_pie,
        )
        panel_bottom = pie_top - _GAP_PANEL_PIE
        alto_panel = max(220, panel_bottom - y_panel_top)

        gap_fila = _GAP_FILA
        alto_mensaje = alto_panel - self._alto_fijo_panel(gap_fila)
        while alto_mensaje < _ALTO_MENSAJE_MIN and gap_fila > 14:
            gap_fila -= 2
            alto_mensaje = alto_panel - self._alto_fijo_panel(gap_fila)
        alto_mensaje = max(_ALTO_MENSAJE_MIN, alto_mensaje)

        self.panel = pygame.Rect(MARGEN, y_panel_top, ANCHO - 2 * MARGEN, alto_panel)
        py = self.panel.y + _PAD_PANEL
        x_campo = self._x_campo()
        ancho_campo = self._ancho_campo()

        y_categoria = py
        y_area = y_categoria + _ALTO_CTRL + gap_fila
        y_mensaje = y_area + _ALTO_CTRL + gap_fila
        y_contacto = y_mensaje + alto_mensaje + gap_fila

        self._alto_mensaje = alto_mensaje
        self._y_etiquetas = {
            "categoria": y_categoria,
            "area": y_area,
            "mensaje": y_mensaje,
            "contacto": y_contacto,
        }

        self.campo_mensaje = CampoTextoArea(
            pygame.Rect(x_campo, y_mensaje, ancho_campo, alto_mensaje),
        )
        self.campo_contacto = CampoTexto(
            pygame.Rect(x_campo, y_contacto, ancho_campo, _ALTO_CTRL),
            placeholder="Correo de contacto (opcional)",
            longitud_max=80,
        )

        self._y_ciclo = {"categoria": y_categoria, "area": y_area}
        self._botones_ciclo: dict[str, tuple[Boton, Boton]] = {}
        self._rects_valor: dict[str, pygame.Rect] = {}
        for clave, y in self._y_ciclo.items():
            rect_izq = pygame.Rect(x_campo, y, _ANCHO_BTN_CICLO, _ALTO_CTRL)
            rect_der = pygame.Rect(
                x_campo + ancho_campo - _ANCHO_BTN_CICLO,
                y,
                _ANCHO_BTN_CICLO,
                _ALTO_CTRL,
            )
            menos = Boton("◀", rect_izq, capturar(self._ciclar, clave, -1))
            mas = Boton("▶", rect_der, capturar(self._ciclar, clave, 1))
            self._botones_ciclo[clave] = (menos, mas)
            self._rects_valor[clave] = pygame.Rect(
                x_campo + _ANCHO_BTN_CICLO + _GAP_CICLO,
                y,
                ancho_campo - 2 * _ANCHO_BTN_CICLO - 2 * _GAP_CICLO,
                _ALTO_CTRL,
            )

    def _crear_botones(self) -> None:
        etiq_enviar = etiqueta(*BTN_ENVIAR)
        self.boton_enviar = Boton(
            etiq_enviar,
            rect_boton_etiqueta(
                etiq_enviar,
                self.fuentes["menu"],
                x_centro=ANCHO // 2 + 110,
                y=0,
                ancho_min=180,
                alto_min=48,
            ),
            self._enviar,
            tooltip=(
                f"Guarda el aviso en {etiqueta_dir_datos_jugador()}/ "
                "e intenta enviarlo por correo."
            ),
        )
        self.boton_volver = Boton(
            etiqueta(*BTN_VOLVER),
            rect_boton_etiqueta(
                etiqueta(*BTN_VOLVER),
                self.fuentes["menu"],
                x_centro=ANCHO // 2 - 110,
                y=0,
                alto_min=48,
            ),
            self.volver,
        )
        posicionar_botones_fila(
            [self.boton_volver, self.boton_enviar],
            self._y_botones,
            x_centro=ANCHO // 2,
            gap=24,
            margen_inferior=_MARGEN_BOTONES,
        )

    def _ciclar(self, clave: str, delta: int) -> None:
        if clave == "categoria":
            n = len(CATEGORIAS_FEEDBACK)
            self._idx_categoria = (self._idx_categoria + delta) % n
        elif clave == "area":
            n = len(AREAS_FEEDBACK)
            self._idx_area = (self._idx_area + delta) % n

    def _texto_valor(self, clave: str) -> str:
        if clave == "categoria":
            return CATEGORIAS_FEEDBACK[self._idx_categoria][1]
        if clave == "area":
            return AREAS_FEEDBACK[self._idx_area][1]
        return ""

    def _desactivar_campos(self) -> None:
        self.campo_mensaje.activo = False
        self.campo_contacto.activo = False

    def _contacto_normalizado(self) -> str:
        raw = self.campo_contacto.texto.strip()
        if not raw or raw.lower() == "sin contacto":
            return ""
        return raw

    def _enviar(self) -> None:
        cat_id = CATEGORIAS_FEEDBACK[self._idx_categoria][0]
        area_id = AREAS_FEEDBACK[self._idx_area][0]
        mensaje = self.campo_mensaje.texto.strip() or "(sin mensaje)"
        reporte = ReporteFeedback(
            categoria=CategoriaFeedback(cat_id),
            mensaje=mensaje,
            jugador=nombre_jugador_grafico(),
            contacto=self._contacto_normalizado(),
            area=area_id,
        )
        self._lineas_resultado = describir_resultado_envio(enviar_feedback(reporte))
        self._fase = "resultado"
        self._desactivar_campos()

    def _botones_ui(self) -> list[Boton]:
        if self._fase == "resultado":
            return [self.boton_volver]
        out: list[Boton] = [self.boton_volver, self.boton_enviar]
        for par in self._botones_ciclo.values():
            out.extend(par)
        return out

    def _manejar_evento_formulario(self, evento: pygame.event.Event) -> bool:
        if self._fase != "form":
            return False
        for campo in (self.campo_mensaje, self.campo_contacto):
            if not campo.manejar_evento(evento):
                continue
            for otro in (self.campo_mensaje, self.campo_contacto):
                if otro is not campo:
                    otro.activo = False
            return True
        return False

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if self._manejar_evento_formulario(evento):
            return None
        if evento.type == pygame.MOUSEMOTION:
            for boton in self._botones_ui():
                boton.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            self._desactivar_campos()
            for boton in self._botones_ui():
                if boton.manejar_clic(evento.pos, evento.button):
                    break
        return None

    def _x_etiqueta_derecha(self) -> int:
        return self.panel.x + _X_ETIQUETA + _ANCHO_ETIQUETA

    def _dibujar_etiqueta(
        self,
        superficie: pygame.Surface,
        clave: str,
        texto: str,
        *,
        alto_fila: int = _ALTO_CTRL,
        alinear_arriba: bool = False,
    ) -> None:
        y = self._y_etiquetas[clave]
        lbl = self.fuentes["menu"].render(
            etiqueta_campo(clave, texto + ":"),
            True,
            _COLOR_ETIQUETA,
        )
        if alinear_arriba:
            dest = lbl.get_rect(right=self._x_etiqueta_derecha(), top=y + 10)
        else:
            dest = lbl.get_rect(right=self._x_etiqueta_derecha(), centery=y + alto_fila // 2)
        superficie.blit(lbl, dest)

    def _dibujar_fila_ciclo(self, superficie: pygame.Surface, clave: str, etiqueta_txt: str) -> None:
        self._dibujar_etiqueta(superficie, clave, etiqueta_txt)
        rect_val = self._rects_valor[clave]
        dibujar_caja_valor_ciclo(
            superficie,
            rect_val,
            self._texto_valor(clave),
            self.fuentes["cuerpo"],
        )
        izq, der = self._botones_ciclo[clave]
        izq.dibujar(superficie, self.fuentes["menu"])
        der.dibujar(superficie, self.fuentes["menu"])

    def _lineas_pie_formulario(self) -> list[str]:
        lineas = [f"Siempre se guarda una copia local en {etiqueta_dir_datos_jugador()}/."]
        if resolver_config_creador_privado() is not None:
            lineas.append(
                "Config detectada: se intentará enviar el aviso por correo (SMTP)."
            )
        return lineas

    def _medir_alto_pie(self, lineas: list[str]) -> int:
        fuente = self.fuentes["pequena"]
        ancho = ANCHO - 2 * MARGEN - 16
        total = 8
        for linea in lineas:
            envueltas = partir_texto(fuente, linea, ancho)
            total += len(envueltas) * fuente.get_linesize()
            total += max(0, len(envueltas) - 1) * _INTERLINEA_PIE
            total += _INTERLINEA_PIE
        return max(32, total - _INTERLINEA_PIE)

    def _dibujar_pie_informativo(self, superficie: pygame.Surface) -> None:
        fuente = self.fuentes["pequena"]
        ancho = self._rect_pie.width - 16
        y = self._rect_pie.y + 4
        for linea in self._lineas_pie:
            for sub in partir_texto(fuente, linea, ancho):
                txt = fuente.render(sub, True, _COLOR_PIE_FONDO)
                superficie.blit(txt, (self._rect_pie.x + 8, y))
                y += fuente.get_linesize() + _INTERLINEA_PIE

    def _dibujar_formulario(self, superficie: pygame.Surface) -> None:
        dibujar_panel(superficie, self.panel, color=(255, 255, 255))

        self._dibujar_etiqueta(
            superficie,
            "mensaje",
            "Mensaje",
            alto_fila=self._alto_mensaje,
            alinear_arriba=True,
        )
        self._dibujar_etiqueta(superficie, "contacto", "Contacto")

        self.campo_mensaje.dibujar(superficie, self.fuentes["cuerpo"])
        self.campo_contacto.dibujar(superficie, self.fuentes["cuerpo"])

        self._dibujar_fila_ciclo(superficie, "categoria", "Tipo de aviso")
        self._dibujar_fila_ciclo(superficie, "area", "Zona del juego")

        self._dibujar_pie_informativo(superficie)

    def _dibujar_resultado(self, superficie: pygame.Surface) -> None:
        y_top = Y_INICIO_TITULO + 36
        alto = self._y_botones - _GAP_PIE_BOTONES - y_top - 12
        panel = pygame.Rect(MARGEN, y_top, ANCHO - 2 * MARGEN, max(200, alto))
        dibujar_panel(superficie, panel, color=(255, 255, 255))
        dibujar_texto_multilinea(
            superficie,
            self.fuentes["cuerpo"],
            "\n".join(self._lineas_resultado),
            pygame.Rect(panel.x + 20, panel.y + 20, panel.width - 40, panel.height - 40),
            _COLOR_ETIQUETA,
        )

    def _dibujar_botones(self, superficie: pygame.Surface) -> None:
        self.boton_volver.dibujar(superficie, self.fuentes["menu"])
        if self._fase == "form":
            self.boton_enviar.dibujar(superficie, self.fuentes["menu"])

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        titulo = "MODO FEEDBACK" if self._fase == "form" else "AVISO ENVIADO"
        dibujar_texto_centro(
            superficie,
            titulo_pantalla(titulo),
            (ANCHO // 2, self._y_titulo),
            self.fuentes["titulo"].get_height(),
            COLOR_TITULO,
            bold=True,
        )
        if self._fase == "form":
            self._dibujar_formulario(superficie)
        else:
            self._dibujar_resultado(superficie)
        self._dibujar_botones(superficie)
        dibujar_tooltips_botones(superficie, self.fuentes["pequena"], self._botones_ui())
