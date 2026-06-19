#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Widgets reutilizables para la interfaz pygame (ratón primero)."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from Comun.jugador import nombre_jugador_efectivo
from Grafico.fuentes import FamiliaFuente, crear_fuente
from Grafico.tema import ALTO, ANCHO, COLOR_ACENTO, COLOR_PANEL, COLOR_TEXTO, COLOR_TITULO
from Grafico.texto import (
    medir_texto_mixto,
    preparar_texto_ui,
    renderizar_texto_mixto,
    texto_requiere_fuentes_mixtas,
)

COLOR_BOTON = (255, 255, 255)
COLOR_BOTON_HOVER = (245, 247, 250)
COLOR_BOTON_SELECCION = (230, 236, 248)
COLOR_BOTON_BORDE = (180, 190, 205)
COLOR_BOTON_TEXTO = (25, 25, 30)
COLOR_BOTON_TEXTO_HOVER = (0, 0, 0)
COLOR_CAMPO_FONDO = (24, 36, 58)
COLOR_CAMPO_ACTIVO = (36, 54, 86)
COLOR_OK_FONDO = (32, 72, 52)
COLOR_ERROR_FONDO = (88, 36, 36)
COLOR_MARCA_ON_FONDO = (38, 108, 210)
COLOR_MARCA_ON_BORDE = (170, 210, 255)
COLOR_MARCA_ON_TEXTO = (255, 255, 255)
COLOR_MARCA_OFF_FONDO = (255, 255, 255)
COLOR_MARCA_OFF_BORDE = (160, 175, 195)
COLOR_MARCA_CASILLA_BORDE = (110, 130, 160)

PADDING_BOTON_X = 14
PADDING_BOTON_Y = 8
MARGEN_INFERIOR_BOTONES = 20


def alto_pila_botones(num_botones: int, alto_boton: int, gap: int) -> int:
    if num_botones <= 0:
        return 0
    return num_botones * alto_boton + (num_botones - 1) * gap


def clamp_y_apilado(
    y_preferido: int,
    *,
    alto_boton: int,
    num_botones: int,
    gap: int,
    alto_pantalla: int = ALTO,
    margen_inferior: int = MARGEN_INFERIOR_BOTONES,
) -> int:
    """Limita la Y del primer botón para que la pila no se salga por abajo."""
    y_max = alto_pantalla - margen_inferior - alto_pila_botones(
        num_botones, alto_boton, gap
    )
    return min(y_preferido, y_max)


def clamp_y_boton(
    y_preferido: int,
    alto_boton: int,
    *,
    alto_pantalla: int = ALTO,
    margen_inferior: int = MARGEN_INFERIOR_BOTONES,
) -> int:
    return clamp_y_apilado(
        y_preferido,
        alto_boton=alto_boton,
        num_botones=1,
        gap=0,
        alto_pantalla=alto_pantalla,
        margen_inferior=margen_inferior,
    )


def posicionar_botones_apilados(
    botones: list[Boton],
    y_preferido: int,
    *,
    x_centro: int,
    gap: int,
    alto_pantalla: int = ALTO,
    margen_inferior: int = MARGEN_INFERIOR_BOTONES,
) -> None:
    """Coloca botones en vertical, respetando el borde inferior de la pantalla."""
    if not botones:
        return
    alto = botones[0].rect.height
    ancho = botones[0].rect.width
    y0 = clamp_y_apilado(
        y_preferido,
        alto_boton=alto,
        num_botones=len(botones),
        gap=gap,
        alto_pantalla=alto_pantalla,
        margen_inferior=margen_inferior,
    )
    x = x_centro - ancho // 2
    for i, boton in enumerate(botones):
        boton.rect.topleft = (x, y0 + i * (alto + gap))


def posicionar_botones_fila(
    botones: list[Boton],
    y_preferido: int,
    *,
    x_centro: int,
    gap: int,
    alto_pantalla: int = ALTO,
    margen_inferior: int = MARGEN_INFERIOR_BOTONES,
) -> None:
    """Coloca botones en horizontal (p. ej. Atrás | Siguiente)."""
    if not botones:
        return
    alto = max(boton.rect.height for boton in botones)
    anchos = [boton.rect.width for boton in botones]
    total_w = sum(anchos) + gap * (len(botones) - 1)
    y = clamp_y_boton(
        y_preferido,
        alto,
        alto_pantalla=alto_pantalla,
        margen_inferior=margen_inferior,
    )
    x = x_centro - total_w // 2
    for boton, ancho in zip(botones, anchos, strict=True):
        boton.rect.topleft = (x, y + (alto - boton.rect.height) // 2)
        x += ancho + gap


def posicionar_pila_inferior(
    botones: list[Boton],
    *,
    x_centro: int,
    gap: int,
    alto_pantalla: int = ALTO,
    margen_inferior: int = MARGEN_INFERIOR_BOTONES,
) -> None:
    """Ancla la pila al borde inferior (primer botón = el más bajo)."""
    if not botones:
        return
    alto = botones[0].rect.height
    ancho = botones[0].rect.width
    alto_total = alto_pila_botones(len(botones), alto, gap)
    y0 = alto_pantalla - margen_inferior - alto_total
    x = x_centro - ancho // 2
    for i, boton in enumerate(botones):
        boton.rect.topleft = (x, y0 + i * (alto + gap))


def medir_etiqueta_boton(
    etiqueta: str,
    fuente: pygame.font.Font,
) -> tuple[int, int]:
    texto = preparar_texto_ui(etiqueta)
    tamano = fuente.get_height()
    if texto_requiere_fuentes_mixtas(texto):
        return medir_texto_mixto(texto, tamano)
    return fuente.size(texto)


def tamano_grupo_botones(
    etiquetas: list[str],
    fuente: pygame.font.Font,
    *,
    padding_x: int = PADDING_BOTON_X,
    padding_y: int = PADDING_BOTON_Y,
    ancho_min: int = 0,
    alto_min: int = 0,
) -> tuple[int, int]:
    medidas = [medir_etiqueta_boton(etiqueta, fuente) for etiqueta in etiquetas]
    ancho_texto = max(ancho for ancho, _ in medidas)
    alto_texto = max(alto for _, alto in medidas)
    return (
        max(ancho_min, ancho_texto + 2 * padding_x),
        max(alto_min, alto_texto + 2 * padding_y),
    )


def rect_boton_etiqueta(
    etiqueta: str,
    fuente: pygame.font.Font,
    *,
    y: int,
    x_derecha: int | None = None,
    x_centro: int | None = None,
    padding_x: int = PADDING_BOTON_X,
    padding_y: int = PADDING_BOTON_Y,
    ancho: int | None = None,
    alto: int | None = None,
    ancho_min: int = 0,
    alto_min: int = 0,
) -> pygame.Rect:
    w_texto, h_texto = medir_etiqueta_boton(etiqueta, fuente)
    w = ancho if ancho is not None else max(ancho_min, w_texto + 2 * padding_x)
    h = alto if alto is not None else max(alto_min, h_texto + 2 * padding_y)
    if x_centro is not None:
        rect = pygame.Rect(x_centro - w // 2, y, w, h)
    elif x_derecha is not None:
        rect = pygame.Rect(x_derecha - w, y, w, h)
    else:
        raise ValueError("Indica x_centro o x_derecha")
    return rect


def rects_botones_apilados(
    etiquetas: list[str],
    fuente: pygame.font.Font,
    *,
    x_centro: int,
    y0: int,
    gap: int = 12,
    padding_x: int = PADDING_BOTON_X,
    padding_y: int = PADDING_BOTON_Y,
    ancho_min: int = 0,
    alto_min: int = 0,
    alto_pantalla: int | None = ALTO,
    margen_inferior: int = MARGEN_INFERIOR_BOTONES,
) -> list[pygame.Rect]:
    ancho, alto = tamano_grupo_botones(
        etiquetas,
        fuente,
        padding_x=padding_x,
        padding_y=padding_y,
        ancho_min=ancho_min,
        alto_min=alto_min,
    )
    if alto_pantalla is not None:
        y0 = clamp_y_apilado(
            y0,
            alto_boton=alto,
            num_botones=len(etiquetas),
            gap=gap,
            alto_pantalla=alto_pantalla,
            margen_inferior=margen_inferior,
        )
    x = x_centro - ancho // 2
    rects: list[pygame.Rect] = []
    y = y0
    for _ in etiquetas:
        rects.append(pygame.Rect(x, y, ancho, alto))
        y += alto + gap
    return rects


def partir_texto(fuente: pygame.font.Font, texto: str, ancho_max: int) -> list[str]:
    texto = preparar_texto_ui(texto)
    palabras = texto.split()
    if not palabras:
        return [""]
    tamano = fuente.get_height()
    lineas: list[str] = []
    actual = palabras[0]
    for palabra in palabras[1:]:
        prueba = f"{actual} {palabra}"
        ancho = (
            medir_texto_mixto(prueba, tamano)[0]
            if texto_requiere_fuentes_mixtas(prueba)
            else fuente.size(prueba)[0]
        )
        if ancho <= ancho_max:
            actual = prueba
        else:
            lineas.append(actual)
            actual = palabra
    lineas.append(actual)
    return lineas


def dibujar_texto_multilinea(
    pantalla: pygame.Surface,
    fuente: pygame.font.Font,
    texto: str,
    rect: pygame.Rect,
    color: tuple[int, int, int],
    *,
    alineacion_centro: bool = False,
) -> None:
    lineas = partir_texto(fuente, texto, rect.width - 16)
    y = rect.y + 8
    tamano = fuente.get_height()
    for linea in lineas:
        if texto_requiere_fuentes_mixtas(linea):
            ancho_linea, alto_linea = medir_texto_mixto(linea, tamano)
            x = rect.centerx - ancho_linea // 2 if alineacion_centro else rect.x + 8
            renderizar_texto_mixto(pantalla, linea, (x, y), color, tamano)
            y += max(fuente.get_linesize(), alto_linea)
        else:
            superficie = fuente.render(linea, True, color)
            if alineacion_centro:
                dest = superficie.get_rect(centerx=rect.centerx, top=y)
            else:
                dest = superficie.get_rect(left=rect.x + 8, top=y)
            pantalla.blit(superficie, dest)
            y += fuente.get_linesize()
        if y > rect.bottom - 8:
            break


COLOR_TOOLTIP_FONDO = (22, 44, 82, 248)
COLOR_TOOLTIP_BORDE = (140, 175, 230)
COLOR_TOOLTIP_TEXTO = (248, 252, 255)
MARGEN_TOOLTIP = 10
ANCHO_MAX_TOOLTIP = 260
GAP_TOOLTIP = 8


def fila_rects_centrada(
    cantidad: int,
    ancho_item: int,
    alto_item: int,
    separacion: int,
    y: int,
    ancho_pantalla: int,
) -> list[pygame.Rect]:
    ancho_total = cantidad * ancho_item + max(0, cantidad - 1) * separacion
    x0 = (ancho_pantalla - ancho_total) // 2
    return [
        pygame.Rect(x0 + i * (ancho_item + separacion), y, ancho_item, alto_item)
        for i in range(cantidad)
    ]


def cuadricula_rects(
    cantidad: int,
    *,
    columnas: int,
    ancho_item: int,
    alto_item: int,
    separacion_x: int,
    separacion_y: int,
    y_inicio: int,
    ancho_pantalla: int,
) -> list[pygame.Rect]:
    if cantidad <= 0:
        return []
    columnas = max(1, columnas)
    ancho_fila = columnas * ancho_item + max(0, columnas - 1) * separacion_x
    x0 = (ancho_pantalla - ancho_fila) // 2
    rects: list[pygame.Rect] = []
    for i in range(cantidad):
        fila = i // columnas
        col = i % columnas
        x = x0 + col * (ancho_item + separacion_x)
        y = y_inicio + fila * (alto_item + separacion_y)
        rects.append(pygame.Rect(x, y, ancho_item, alto_item))
    return rects


def _fuente_ajustada(
    texto: str,
    fuente_base: pygame.font.Font,
    ancho_max: int,
    *,
    familia: FamiliaFuente = "texto",
) -> pygame.font.Font:
    tam = fuente_base.get_height()
    while tam > 12:
        fuente = crear_fuente(tam, familia=familia)
        if fuente.size(texto)[0] <= ancho_max:
            return fuente
        tam -= 1
    return fuente_base


def capturar(
    al_pulsar: Callable[..., None],
    /,
    *args: object,
    **kwargs: object,
) -> Callable[[], None]:
    """Callback sin argumentos con valores fijados (bucles de botones)."""

    def _envuelto() -> None:
        al_pulsar(*args, **kwargs)

    return _envuelto


class Boton:
    """Botón rectangular activable con clic del ratón."""

    def __init__(
        self,
        etiqueta: str,
        rect: pygame.Rect,
        al_pulsar: Callable[[], None],
        *,
        seleccionado: bool = False,
        fondo: tuple[int, int, int] | None = None,
        fondo_hover: tuple[int, int, int] | None = None,
        familia_etiqueta: FamiliaFuente = "texto",
        mostrar_texto: bool = True,
        tooltip: str | None = None,
    ) -> None:
        self.etiqueta = etiqueta
        self.rect = rect
        self.al_pulsar = al_pulsar
        self.seleccionado = seleccionado
        self.fondo = fondo
        self.fondo_hover = fondo_hover
        self.familia_etiqueta = familia_etiqueta
        self.mostrar_texto = mostrar_texto
        self.tooltip = tooltip
        self.hover = False
        self.activo = True

    def actualizar_hover(self, pos: tuple[int, int]) -> None:
        self.hover = self.activo and self.rect.collidepoint(pos)

    def manejar_clic(self, pos: tuple[int, int], boton: int) -> bool:
        if self.activo and boton == 1 and self.rect.collidepoint(pos):
            self.al_pulsar()
            return True
        return False

    def dibujar(self, pantalla: pygame.Surface, fuente: pygame.font.Font) -> None:
        if not self.activo:
            fondo = (40, 40, 40)
            texto_color = (120, 120, 120)
            borde = (70, 70, 70)
        elif self.seleccionado:
            fondo = self.fondo or COLOR_BOTON_SELECCION
            texto_color = COLOR_BOTON_TEXTO_HOVER
            borde = COLOR_ACENTO
        else:
            fondo = (self.fondo_hover if self.hover else self.fondo) or (
                COLOR_BOTON_HOVER if self.hover else COLOR_BOTON
            )
            texto_color = COLOR_BOTON_TEXTO_HOVER if self.hover else COLOR_BOTON_TEXTO
            borde = COLOR_BOTON_BORDE
        pygame.draw.rect(pantalla, fondo, self.rect, border_radius=8)
        pygame.draw.rect(pantalla, borde, self.rect, width=2, border_radius=8)
        if not self.mostrar_texto or not self.etiqueta.strip():
            return

        padding = 16
        ancho_texto = max(8, self.rect.width - 2 * padding)
        etiqueta = preparar_texto_ui(self.etiqueta)
        if (
            self.familia_etiqueta != "texto"
            or not texto_requiere_fuentes_mixtas(etiqueta)
        ):
            fuente_etiqueta = crear_fuente(
                fuente.get_height(),
                familia=self.familia_etiqueta,
            )
            fuente_etiqueta = _fuente_ajustada(
                etiqueta,
                fuente_etiqueta,
                ancho_texto,
                familia=self.familia_etiqueta,
            )
            superficie = fuente_etiqueta.render(etiqueta, True, texto_color)
            rect_texto = superficie.get_rect(center=self.rect.center)
            pantalla.blit(superficie, rect_texto)
        else:
            tamano = fuente.get_height()
            ancho, alto = medir_texto_mixto(etiqueta, tamano)
            x = self.rect.centerx - ancho // 2
            y = self.rect.centery - alto // 2
            renderizar_texto_mixto(
                pantalla, etiqueta, (x, y), texto_color, tamano
            )


class BotonMarcable(Boton):
    """Botón con casilla de verificación para opciones marcables (filtros, etc.)."""

    MARGEN_CASILLA = 10
    TAM_CASILLA = 18

    @classmethod
    def ancho_etiqueta(cls, ancho_boton: int) -> int:
        return ancho_boton - cls.MARGEN_CASILLA - cls.TAM_CASILLA - 8 - 4

    def dibujar(self, pantalla: pygame.Surface, fuente: pygame.font.Font) -> None:
        if not self.activo:
            fondo = (40, 40, 40)
            texto_color = (120, 120, 120)
            borde = (70, 70, 70)
            marca = (90, 90, 90)
        elif self.seleccionado:
            fondo = COLOR_MARCA_ON_FONDO
            texto_color = COLOR_MARCA_ON_TEXTO
            borde = COLOR_MARCA_ON_BORDE
            marca = COLOR_MARCA_ON_TEXTO
        else:
            if self.hover:
                fondo = COLOR_BOTON_HOVER
                borde = COLOR_BOTON_BORDE
            else:
                fondo = COLOR_MARCA_OFF_FONDO
                borde = COLOR_MARCA_OFF_BORDE
            texto_color = COLOR_BOTON_TEXTO
            marca = COLOR_MARCA_CASILLA_BORDE

        pygame.draw.rect(pantalla, fondo, self.rect, border_radius=8)
        pygame.draw.rect(pantalla, borde, self.rect, width=2, border_radius=8)

        casilla = pygame.Rect(
            self.rect.x + self.MARGEN_CASILLA,
            self.rect.centery - self.TAM_CASILLA // 2,
            self.TAM_CASILLA,
            self.TAM_CASILLA,
        )
        if self.seleccionado:
            relleno_casilla = (255, 255, 255)
            borde_casilla = (255, 255, 255)
            color_tick = COLOR_MARCA_ON_FONDO
        else:
            relleno_casilla = (248, 250, 252)
            borde_casilla = COLOR_MARCA_CASILLA_BORDE
            color_tick = marca
        pygame.draw.rect(pantalla, relleno_casilla, casilla, border_radius=4)
        pygame.draw.rect(pantalla, borde_casilla, casilla, width=2, border_radius=4)
        if self.seleccionado:
            pygame.draw.line(
                pantalla,
                color_tick,
                (casilla.x + 4, casilla.centery),
                (casilla.x + 8, casilla.bottom - 5),
                3,
            )
            pygame.draw.line(
                pantalla,
                color_tick,
                (casilla.x + 8, casilla.bottom - 5),
                (casilla.right - 4, casilla.y + 5),
                3,
            )

        if not self.mostrar_texto or not self.etiqueta.strip():
            return

        texto_rect = pygame.Rect(
            self.rect.x + self.MARGEN_CASILLA + self.TAM_CASILLA + 8,
            self.rect.y,
            self.rect.width - self.MARGEN_CASILLA - self.TAM_CASILLA - 16,
            self.rect.height,
        )
        etiqueta = preparar_texto_ui(self.etiqueta)
        fuente_etiqueta = _fuente_ajustada(
            etiqueta,
            fuente,
            max(8, texto_rect.width - 4),
        )
        superficie = fuente_etiqueta.render(etiqueta, True, texto_color)
        pantalla.blit(
            superficie,
            superficie.get_rect(midleft=(texto_rect.x, texto_rect.centery)),
        )


class BotonOpcion(Boton):
    """Opción de respuesta A–D con texto multilínea."""

    def __init__(
        self,
        letra: str,
        texto: str,
        rect: pygame.Rect,
        al_pulsar: Callable[[], None],
    ) -> None:
        super().__init__(f"{letra}) {texto}", rect, al_pulsar)
        self.letra = letra
        self.texto_opcion = texto
        self.marcar_correcta = False
        self.marcar_incorrecta = False

    def dibujar(self, pantalla: pygame.Surface, fuente: pygame.font.Font) -> None:
        if self.marcar_correcta:
            fondo, borde = COLOR_OK_FONDO, COLOR_ACENTO
            texto_color = (255, 255, 255)
        elif self.marcar_incorrecta:
            fondo, borde = COLOR_ERROR_FONDO, (220, 120, 120)
            texto_color = (255, 255, 255)
        elif not self.activo:
            fondo, borde = (40, 40, 40), (70, 70, 70)
            texto_color = (120, 120, 120)
        elif self.hover:
            fondo, borde = COLOR_BOTON_HOVER, COLOR_BOTON_BORDE
            texto_color = COLOR_BOTON_TEXTO_HOVER
        else:
            fondo, borde = COLOR_BOTON, COLOR_BOTON_BORDE
            texto_color = COLOR_BOTON_TEXTO
        pygame.draw.rect(pantalla, fondo, self.rect, border_radius=8)
        pygame.draw.rect(pantalla, borde, self.rect, width=2, border_radius=8)
        etiqueta = f"{self.letra}) {self.texto_opcion}"
        dibujar_texto_multilinea(
            pantalla, fuente, etiqueta, self.rect, texto_color
        )


def _posicion_panel_tooltip(
    rect_ancla: pygame.Rect,
    ancho_panel: int,
    alto_panel: int,
    *,
    ancho_pantalla: int = ANCHO,
    alto_pantalla: int = ALTO,
) -> tuple[int, int]:
    """Coloca el bocadillo según la zona de la pantalla (evita bloques enormes bajo iconos)."""
    margen = 6
    gap = GAP_TOOLTIP

    # Iconos fijos arriba a la izquierda: al lado del botón.
    if rect_ancla.centery < 72 and rect_ancla.centerx < ancho_pantalla // 2:
        x = rect_ancla.right + gap
        y = rect_ancla.centery - alto_panel // 2
        if x + ancho_panel > ancho_pantalla - margen:
            x = rect_ancla.left - gap - ancho_panel
        y = max(margen, min(y, alto_pantalla - alto_panel - margen))
        x = max(margen, min(x, ancho_pantalla - ancho_panel - margen))
        return x, y

    # Banda inferior (comodines, etc.): encima del botón.
    if rect_ancla.top > alto_pantalla - 150:
        x = rect_ancla.centerx - ancho_panel // 2
        x = max(margen, min(x, ancho_pantalla - ancho_panel - margen))
        y = rect_ancla.top - alto_panel - gap
        if y < margen:
            y = rect_ancla.bottom + gap
        return x, y

    # Resto: encima, alineado al borde izquierdo del botón.
    x = rect_ancla.left
    x = max(margen, min(x, ancho_pantalla - ancho_panel - margen))
    y = rect_ancla.top - alto_panel - gap
    if y < margen:
        y = rect_ancla.bottom + gap
    y = max(margen, min(y, alto_pantalla - alto_panel - margen))
    return x, y


def _dibujar_lineas_tooltip(
    pantalla: pygame.Surface,
    fuente: pygame.font.Font,
    lineas: list[str],
    panel: pygame.Rect,
    color: tuple[int, int, int],
) -> None:
    y = panel.y + MARGEN_TOOLTIP
    tamano = fuente.get_height()
    for linea in lineas:
        if texto_requiere_fuentes_mixtas(linea):
            renderizar_texto_mixto(pantalla, linea, (panel.x + MARGEN_TOOLTIP, y), color, tamano)
            y += max(fuente.get_linesize(), medir_texto_mixto(linea, tamano)[1])
        else:
            superficie = fuente.render(linea, True, color)
            pantalla.blit(superficie, (panel.x + MARGEN_TOOLTIP, y))
            y += fuente.get_linesize()


def dibujar_tooltip(
    pantalla: pygame.Surface,
    fuente: pygame.font.Font,
    rect_ancla: pygame.Rect,
    texto: str,
    *,
    ancho_pantalla: int = ANCHO,
    alto_pantalla: int = ALTO,
) -> None:
    """Bocadillo compacto al pasar el ratón (hover)."""
    texto = preparar_texto_ui(texto.strip())
    if not texto:
        return
    fuente_tip = crear_fuente(max(14, min(15, fuente.get_height())), familia="texto")
    ancho_texto_max = ANCHO_MAX_TOOLTIP - 2 * MARGEN_TOOLTIP
    lineas = partir_texto(fuente_tip, texto, ancho_texto_max)
    alto_linea = fuente_tip.get_linesize()
    alto_panel = 2 * MARGEN_TOOLTIP + len(lineas) * alto_linea
    anchos = []
    tamano = fuente_tip.get_height()
    for linea in lineas:
        if texto_requiere_fuentes_mixtas(linea):
            anchos.append(medir_texto_mixto(linea, tamano)[0])
        else:
            anchos.append(fuente_tip.size(linea)[0])
    ancho_panel = min(
        ANCHO_MAX_TOOLTIP,
        max(anchos, default=0) + 2 * MARGEN_TOOLTIP,
    )
    x, y = _posicion_panel_tooltip(
        rect_ancla,
        ancho_panel,
        alto_panel,
        ancho_pantalla=ancho_pantalla,
        alto_pantalla=alto_pantalla,
    )
    panel = pygame.Rect(x, y, ancho_panel, alto_panel)
    fondo = pygame.Surface((ancho_panel, alto_panel), pygame.SRCALPHA)
    fondo.fill(COLOR_TOOLTIP_FONDO)
    pantalla.blit(fondo, panel.topleft)
    pygame.draw.rect(pantalla, COLOR_TOOLTIP_BORDE, panel, width=1, border_radius=8)
    _dibujar_lineas_tooltip(pantalla, fuente_tip, lineas, panel, COLOR_TOOLTIP_TEXTO)


from Comun.preferencias_grafico import tooltips_habilitados


def dibujar_tooltips_botones(
    pantalla: pygame.Surface,
    fuente: pygame.font.Font,
    botones: list[Boton],
) -> None:
    if not tooltips_habilitados():
        return
    for boton in botones:
        if boton.activo and boton.hover and boton.tooltip:
            dibujar_tooltip(pantalla, fuente, boton.rect, boton.tooltip)
            return


class CampoTexto:
    """Campo de texto: el teclado solo se usa aquí."""

    def __init__(
        self,
        rect: pygame.Rect,
        *,
        texto_inicial: str = "",
        longitud_max: int = 32,
        placeholder: str = "Escribe aquí…",
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
        if evento.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            self.activo = False
            return True
        char = evento.unicode
        if char.isprintable() and len(self.texto) < self.longitud_max:
            self.texto += char
            return True
        return False

    def valor(self) -> str:
        return nombre_jugador_efectivo(self.texto)

    def dibujar(self, pantalla: pygame.Surface, fuente: pygame.font.Font) -> None:
        fondo = COLOR_CAMPO_ACTIVO if self.activo else COLOR_CAMPO_FONDO
        borde = COLOR_ACENTO if self.activo else COLOR_BOTON_BORDE
        pygame.draw.rect(pantalla, fondo, self.rect, border_radius=8)
        pygame.draw.rect(pantalla, borde, self.rect, width=2, border_radius=8)
        mostrar = self.texto if self.texto or self.activo else self.placeholder
        color = COLOR_TITULO if self.texto or self.activo else COLOR_TEXTO
        etiqueta = fuente.render(mostrar, True, color)
        pantalla.blit(etiqueta, (self.rect.x + 12, self.rect.centery - etiqueta.get_height() // 2))
        if self.activo and pygame.time.get_ticks() % 1000 < 500:
            x_cursor = self.rect.x + 12 + fuente.size(self.texto)[0] + 2
            pygame.draw.line(
                pantalla,
                COLOR_TITULO,
                (x_cursor, self.rect.y + 10),
                (x_cursor, self.rect.bottom - 10),
                2,
            )


class CampoEntero:
    """Campo numérico con teclado (solo dígitos)."""

    def __init__(
        self,
        rect: pygame.Rect,
        *,
        texto_inicial: str = "10",
        placeholder: str = "10",
        minimo: int = 1,
        maximo: int = 999,
    ) -> None:
        self.rect = rect
        self.texto = texto_inicial
        self.placeholder = placeholder
        self.minimo = minimo
        self.maximo = maximo
        self.longitud_max = len(str(maximo))
        self.activo = False
        self.habilitado = True

    def manejar_evento(self, evento: pygame.event.Event) -> bool:
        if not self.habilitado:
            if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self.activo = self.rect.collidepoint(evento.pos)
                if self.activo:
                    self.activo = False
            return False
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self.activo = self.rect.collidepoint(evento.pos)
            return self.activo
        if not self.activo or evento.type != pygame.KEYDOWN:
            return False
        if evento.key == pygame.K_BACKSPACE:
            self.texto = self.texto[:-1]
            return True
        if evento.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            self.activo = False
            return True
        char = evento.unicode
        if char.isdigit() and len(self.texto) < self.longitud_max:
            self.texto += char
            return True
        return False

    def valor_entero(self, defecto: int = 10) -> int | None:
        limpio = self.texto.strip()
        if not limpio:
            return defecto
        if not limpio.isdigit():
            return None
        valor = int(limpio)
        if valor < self.minimo or valor > self.maximo:
            return None
        return valor

    def establecer_habilitado(self, habilitado: bool) -> None:
        self.habilitado = habilitado
        if not habilitado:
            self.activo = False

    def actualizar_limites(self, minimo: int, maximo: int) -> None:
        self.minimo = minimo
        self.maximo = maximo
        self.longitud_max = len(str(maximo))

    def dibujar(self, pantalla: pygame.Surface, fuente: pygame.font.Font) -> None:
        if not self.habilitado:
            fondo = (40, 40, 40)
            borde = (70, 70, 70)
            color_texto = (120, 120, 120)
        elif self.activo:
            fondo = COLOR_CAMPO_ACTIVO
            borde = COLOR_ACENTO
            color_texto = COLOR_TITULO
        else:
            fondo = COLOR_CAMPO_FONDO
            borde = COLOR_BOTON_BORDE
            color_texto = COLOR_TITULO if self.texto else COLOR_TEXTO
        pygame.draw.rect(pantalla, fondo, self.rect, border_radius=8)
        pygame.draw.rect(pantalla, borde, self.rect, width=2, border_radius=8)
        mostrar = self.texto if self.texto or self.activo else self.placeholder
        if not self.habilitado and not self.texto:
            mostrar = self.placeholder
        etiqueta = fuente.render(mostrar, True, color_texto)
        pantalla.blit(etiqueta, (self.rect.x + 12, self.rect.centery - etiqueta.get_height() // 2))
        if self.habilitado and self.activo and pygame.time.get_ticks() % 1000 < 500:
            x_cursor = self.rect.x + 12 + fuente.size(self.texto)[0] + 2
            pygame.draw.line(
                pantalla,
                COLOR_TITULO,
                (x_cursor, self.rect.y + 10),
                (x_cursor, self.rect.bottom - 10),
                2,
            )


def dibujar_overlay_atenuacion(
    superficie: pygame.Surface,
    *,
    alpha: int | None = None,
) -> None:
    """Oscurece pantalla e iconos fijos bajo un popup modal."""
    from Grafico.tema import ALPHA_OVERLAY_POPUP

    if alpha is None:
        alpha = ALPHA_OVERLAY_POPUP
    overlay = pygame.Surface(superficie.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, alpha))
    superficie.blit(overlay, (0, 0))


def dibujar_caja_valor_ciclo(
    superficie: pygame.Surface,
    rect: pygame.Rect,
    texto: str,
    fuente: pygame.font.Font,
    *,
    padding_x: int = 8,
) -> None:
    """Fondo azul del valor central en selectores ◀ valor ▶."""
    if rect.width <= 0 or rect.height <= 0:
        return
    pygame.draw.rect(superficie, COLOR_PANEL, rect, border_radius=6)
    texto_ui = preparar_texto_ui(texto)
    fuente_val = _fuente_ajustada(texto_ui, fuente, rect.width - 2 * padding_x)
    surf = fuente_val.render(texto_ui, True, COLOR_TEXTO)
    superficie.blit(surf, surf.get_rect(center=rect.center))


def dibujar_panel(
    pantalla: pygame.Surface,
    rect: pygame.Rect,
    *,
    color: tuple[int, int, int] = COLOR_PANEL,
) -> None:
    pygame.draw.rect(pantalla, color, rect, border_radius=10)
    pygame.draw.rect(pantalla, COLOR_BOTON_BORDE, rect, width=1, border_radius=10)
