#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Carrusel del modo historia (solo paquete completo)."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from Comun.config_historia import (
    ConfigPresetHistoria,
    etiqueta_campo_estrategia_practica,
    preset_usa_prioridad_materias,
)
from Comun.presets_historia import PresetHistoria
from Comun.preferencias_grafico import nombre_jugador_grafico
from Grafico.textos_grafico import (
    BTN_CONTINUAR,
    BTN_VOLVER_MENU,
    etiqueta,
    etiqueta_campo,
    subtitulo,
    titulo_pantalla,
)
from Grafico.modo_historia import cargar_catalogo_historia
from Grafico.arranque_partida import (
    construir_navegacion_fin_partida,
    iniciar_pantalla_partida,
)
from Grafico.pantallas import MenuPrincipal, Pantalla
from Grafico.tooltips_ui import TOOLTIP_CONTINUAR
from Grafico.tema import (
    ALTO,
    ANCHO,
    COLOR_ACENTO,
    COLOR_AVISO,
    COLOR_FONDO,
    COLOR_TEXTO,
    COLOR_TITULO,
    MARGEN,
    Y_INICIO_TITULO,
    crear_fuentes,
)
from Grafico.ui import (
    Boton,
    dibujar_flecha_ciclo,
    dibujar_panel,
    dibujar_texto_multilinea,
    dibujar_tooltips_botones,
    posicionar_botones_fila,
    rect_boton_etiqueta,
    tamano_grupo_botones,
)
from Grafico.texto import dibujar_texto_centro, preparar_texto_ui

if TYPE_CHECKING:
    from Grafico.app import DatosJuego

Y_TITULO_HISTORIA = Y_INICIO_TITULO
COLOR_ETIQUETA_PANEL_CLARO = (45, 55, 70)
Y_PASO_HISTORIA = Y_TITULO_HISTORIA + 32
GAP_SUBTITULO_CONTENIDO = 20
GAP_LBL_CAMPO = 12
GAP_CAMPO_SECCION = 28
GAP_SECCION_CARRUSEL = 20
ALTO_ETIQUETA_MENU = 24
Y_PRESET_LBL_TOP = Y_PASO_HISTORIA + ALTO_ETIQUETA_MENU + GAP_CAMPO_SECCION
Y_CARRUSEL = Y_PRESET_LBL_TOP + ALTO_ETIQUETA_MENU + GAP_SECCION_CARRUSEL
ALTO_TARJETA_PRESET = 320
ANCHO_FLECHA = 44
GAP_TRAS_TARJETA_DOTS = 14
MARGEN_INF_HISTORIA = 22
MARGEN_RANKING_TARJETA = 28
MARGEN_PIE_TARJETA = 14
ALTO_TEXTO_CONTADOR = 16
GAP_RANKING_CONTADOR = 12
GAP_DESC_RANKING = 10
Y_DOTS = Y_CARRUSEL + ALTO_TARJETA_PRESET + GAP_TRAS_TARJETA_DOTS
DOT_RADIO_ACTIVO = 6
DOT_RADIO_INACTIVO = 4
DOT_SEPARACION = 16
DOT_MAX_ANCHO = ANCHO - 2 * MARGEN - 120


def _dibujar_cabecera_historia(
    superficie: pygame.Surface,
    fuentes: dict[str, pygame.font.Font],
    paso: str,
) -> None:
    _dibujar_cabecera_catalogo(
        superficie,
        fuentes,
        titulo="MODO HISTORIA",
        paso=paso,
        emoji="📕",
    )


def _dibujar_cabecera_catalogo(
    superficie: pygame.Surface,
    fuentes: dict[str, pygame.font.Font],
    *,
    titulo: str,
    paso: str,
    emoji: str = "📕",
) -> None:
    dibujar_texto_centro(
        superficie,
        titulo_pantalla(titulo),
        (ANCHO // 2, Y_TITULO_HISTORIA),
        fuentes["titulo"].get_height(),
        COLOR_TITULO,
        bold=True,
    )
    dibujar_texto_centro(
        superficie,
        subtitulo(paso, emoji),
        (ANCHO // 2, Y_PASO_HISTORIA),
        fuentes["pequena"].get_height(),
        COLOR_TEXTO,
    )


def _rect_tarjeta_carrusel() -> pygame.Rect:
    ancho = ANCHO - 2 * MARGEN - 2 * ANCHO_FLECHA - 24
    x = (ANCHO - ancho) // 2
    return pygame.Rect(x, Y_CARRUSEL, ancho, ALTO_TARJETA_PRESET)


def _dibujar_flecha_carrusel(
    superficie: pygame.Surface,
    rect: pygame.Rect,
    direccion: str,
    *,
    activo: bool,
    hover: bool,
) -> None:
    dibujar_flecha_ciclo(
        superficie,
        rect,
        direccion,
        activo=activo,
        hover=hover,
        border_radius=10,
    )


def _layout_puntos_carrusel(n: int) -> tuple[list[tuple[int, int]], int]:
    """Posiciones (x, y) de los puntos y separación usada."""
    if n <= 0:
        return [], DOT_SEPARACION
    sep = DOT_SEPARACION
    while n > 1 and (n - 1) * sep > DOT_MAX_ANCHO:
        sep = max(8, sep - 2)
    total_ancho = (n - 1) * sep
    x0 = (ANCHO - total_ancho) // 2
    return [(x0 + i * sep, Y_DOTS) for i in range(n)], sep

class ConfigModoHistoria(Pantalla):
    """Carrusel de presets del modo historia."""

    def __init__(
        self,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
        *,
        indice_inicial: int = 0,
        preset_id_inicial: str | None = None,
        configs_preset: dict[str, ConfigPresetHistoria] | None = None,
    ) -> None:
        self.datos = datos
        self.ir_a = ir_a
        self.salir_app = salir_app
        if not datos.perfil.modo_historia_disponible:
            ir_a(MenuPrincipal(datos, ir_a, salir_app))
            return
        self.fuentes = crear_fuentes()
        self.mensaje = ""
        self.presets = cargar_catalogo_historia(datos.perfil)
        self._configs_preset: dict[str, ConfigPresetHistoria] = dict(
            configs_preset or {}
        )
        self.indice = 0
        if self.presets:
            if preset_id_inicial:
                for i, preset in enumerate(self.presets):
                    if preset.id == preset_id_inicial:
                        self.indice = i
                        break
            else:
                self.indice = max(0, min(len(self.presets) - 1, indice_inicial))

        tarjeta = _rect_tarjeta_carrusel()
        alto_flecha = min(88, ALTO_TARJETA_PRESET - 40)
        y_flecha = tarjeta.centery - alto_flecha // 2
        self.rect_flecha_izq = pygame.Rect(tarjeta.x - ANCHO_FLECHA - 8, y_flecha, ANCHO_FLECHA, alto_flecha)
        self.rect_flecha_der = pygame.Rect(tarjeta.right + 8, y_flecha, ANCHO_FLECHA, alto_flecha)
        self.hover_izq = False
        self.hover_der = False

        fuente_menu = self.fuentes["menu"]
        etiq_empezar = etiqueta(*BTN_CONTINUAR)
        etiq_volver = etiqueta(*BTN_VOLVER_MENU)
        ancho_btns, alto_btns = tamano_grupo_botones(
            [etiq_empezar, etiq_volver],
            fuente_menu,
            alto_min=44,
        )
        self.boton_empezar = Boton(
            etiq_empezar,
            rect_boton_etiqueta(
                etiq_empezar,
                fuente_menu,
                x_centro=ANCHO // 2,
                y=0,
                ancho=ancho_btns,
                alto=alto_btns,
            ),
            self._continuar,
            tooltip=TOOLTIP_CONTINUAR,
        )
        self.boton_volver = Boton(
            etiq_volver,
            rect_boton_etiqueta(
                etiq_volver,
                fuente_menu,
                x_centro=ANCHO // 2,
                y=0,
                ancho=ancho_btns,
                alto=alto_btns,
            ),
            lambda: self.ir_a(MenuPrincipal(datos, ir_a, salir_app)),
        )
        self._reposicionar_botones_navegacion()

    def _pantalla_carrusel(
        self,
        *,
        indice: int | None = None,
        configs_preset: dict[str, ConfigPresetHistoria] | None = None,
    ) -> ConfigModoHistoria:
        return ConfigModoHistoria(
            self.datos,
            self.ir_a,
            self.salir_app,
            indice_inicial=self.indice if indice is None else indice,
            configs_preset=(
                self._configs_preset if configs_preset is None else configs_preset
            ),
        )

    def _reserva_pie_tarjeta(self) -> int:
        return MARGEN_PIE_TARJETA + ALTO_TEXTO_CONTADOR

    def _reposicionar_botones_navegacion(self) -> None:
        alto = self.boton_empezar.rect.height
        y_nav = ALTO - MARGEN_INF_HISTORIA - alto
        posicionar_botones_fila(
            [self.boton_volver, self.boton_empezar],
            y_nav,
            x_centro=ANCHO // 2,
            gap=12,
        )

    @property
    def preset_actual(self) -> PresetHistoria | None:
        if not self.presets:
            return None
        return self.presets[self.indice]

    def _ir_a_indice(self, indice: int) -> None:
        if not self.presets:
            return
        self.indice = max(0, min(len(self.presets) - 1, indice))
        self.mensaje = ""
        self._reposicionar_botones_navegacion()

    def _anterior(self) -> None:
        self._ir_a_indice(self.indice - 1)

    def _siguiente(self) -> None:
        self._ir_a_indice(self.indice + 1)

    def _indice_desde_punto(self, pos: tuple[int, int]) -> int | None:
        posiciones, _sep = _layout_puntos_carrusel(len(self.presets))
        for i, (x, y) in enumerate(posiciones):
            radio = DOT_RADIO_ACTIVO + 6
            if (pos[0] - x) ** 2 + (pos[1] - y) ** 2 <= radio**2:
                return i
        return None

    def _continuar(self) -> None:
        preset = self.preset_actual
        if preset is None:
            self.mensaje = "No hay presets disponibles."
            return
        viable, motivo = self.datos.perfil.preset_historia_viable(preset)
        if not viable:
            self.mensaje = motivo
            return
        nombre = nombre_jugador_grafico()
        self.mensaje = ""
        if preset.tiene_opciones():
            indice = self.indice
            configs = dict(self._configs_preset)

            def _volver_opciones(config: ConfigPresetHistoria) -> None:
                configs[preset.id] = config
                self.ir_a(
                    ConfigModoHistoria(
                        self.datos,
                        self.ir_a,
                        self.salir_app,
                        indice_inicial=indice,
                        configs_preset=configs,
                    )
                )

            config_ini = self._configs_preset.get(preset.id)
            from Grafico.pantallas_examen_fijo import ConfigOpcionesHistoria

            self.ir_a(
                ConfigOpcionesHistoria(
                    self.datos,
                    preset,
                    nombre,
                    self.ir_a,
                    self.salir_app,
                    _volver_opciones,
                    config_inicial=config_ini,
                )
            )
            return
        self._iniciar_partida(preset, ConfigPresetHistoria(), nombre)

    def _iniciar_partida(
        self,
        preset: PresetHistoria,
        config: ConfigPresetHistoria,
        nombre: str,
    ) -> None:
        indice = self.indice
        configs = dict(self._configs_preset)

        def _pantalla_configuracion() -> Pantalla:
            if preset.tiene_opciones():

                def _volver_opciones(cfg: ConfigPresetHistoria) -> None:
                    configs[preset.id] = cfg
                    self.ir_a(
                        ConfigModoHistoria(
                            self.datos,
                            self.ir_a,
                            self.salir_app,
                            indice_inicial=indice,
                            configs_preset=configs,
                        )
                    )

                from Grafico.pantallas_examen_fijo import ConfigOpcionesHistoria

                return ConfigOpcionesHistoria(
                    self.datos,
                    preset,
                    nombre,
                    self.ir_a,
                    self.salir_app,
                    _volver_opciones,
                    config_inicial=config,
                )
            return self._pantalla_carrusel(
                indice=indice,
                configs_preset={**configs, preset.id: config},
            )

        navegacion = construir_navegacion_fin_partida(
            self.datos,
            preset,
            config,
            nombre,
            self.ir_a,
            self.salir_app,
            _pantalla_configuracion,
        )
        try:
            pantalla = iniciar_pantalla_partida(
                self.datos,
                preset,
                config,
                nombre,
                self.ir_a,
                self.salir_app,
                navegacion_fin=navegacion,
            )
        except ValueError as e:
            self.mensaje = str(e)
            return
        self.mensaje = ""
        self.ir_a(pantalla)

    def _botones_ui(self) -> list[Boton]:
        return [self.boton_empezar, self.boton_volver]

    def _clic_flecha(self, pos: tuple[int, int], boton: int) -> bool:
        if boton != 1:
            return False
        if self.rect_flecha_izq.collidepoint(pos) and self.indice > 0:
            self._anterior()
            return True
        if self.rect_flecha_der.collidepoint(pos) and self.indice < len(self.presets) - 1:
            self._siguiente()
            return True
        return False

    def _manejar_rueda_carrusel(self, evento: pygame.event.Event) -> None:
        if evento.y > 0:
            self._anterior()
        elif evento.y < 0:
            self._siguiente()

    def _actualizar_hover_carrusel(self, pos: tuple[int, int]) -> None:
        self.hover_izq = self.rect_flecha_izq.collidepoint(pos)
        self.hover_der = self.rect_flecha_der.collidepoint(pos)
        for boton in self._botones_ui():
            boton.actualizar_hover(pos)

    def _manejar_clic_carrusel(self, pos: tuple[int, int], boton: int) -> bool:
        if self._clic_flecha(pos, boton):
            return True
        idx = self._indice_desde_punto(pos)
        if idx is not None and boton == 1:
            self._ir_a_indice(idx)
            return True
        return any(b.manejar_clic(pos, boton) for b in self._botones_ui())

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEWHEEL and self.presets:
            self._manejar_rueda_carrusel(evento)
        elif evento.type == pygame.MOUSEMOTION:
            self._actualizar_hover_carrusel(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if self._manejar_clic_carrusel(evento.pos, evento.button):
                return None
        return None

    def _dibujar_tarjeta_preset(self, superficie: pygame.Surface, preset: PresetHistoria) -> None:
        tarjeta = _rect_tarjeta_carrusel()
        dibujar_panel(superficie, tarjeta, color=(255, 255, 255))

        cat = self.fuentes["pequena"].render(f"[{preset.categoria}]", True, COLOR_ACENTO)
        superficie.blit(cat, cat.get_rect(midtop=(tarjeta.centerx, tarjeta.y + 16)))

        y_nombre = tarjeta.y + 34
        if preset_usa_prioridad_materias(preset, self.datos.perfil):
            y_badge = tarjeta.y + 34
            badge_pract = self.fuentes["pequena"].render(
                etiqueta_campo(
                    "estrategia_practica",
                    etiqueta_campo_estrategia_practica(),
                ),
                True,
                (20, 110, 70),
            )
            superficie.blit(
                badge_pract,
                badge_pract.get_rect(midtop=(tarjeta.centerx, y_badge)),
            )
            y_nombre = y_badge + 24

        nombre = self.fuentes["subtitulo"].render(
            preparar_texto_ui(preset.nombre),
            True,
            (25, 35, 50),
        )
        superficie.blit(nombre, nombre.get_rect(midtop=(tarjeta.centerx, y_nombre)))

        reserva_pie = self._reserva_pie_tarjeta()

        dibujar_texto_multilinea(
            superficie,
            self.fuentes["cuerpo"],
            preset.descripcion,
            pygame.Rect(
                tarjeta.x + 24,
                y_nombre + 36,
                tarjeta.width - 48,
                max(
                    40,
                    tarjeta.height - (y_nombre + 36 - tarjeta.y) - reserva_pie,
                ),
            ),
            (45, 55, 70),
            alineacion_centro=True,
        )

        contador = self.fuentes["pie"].render(
            f"{self.indice + 1} / {len(self.presets)}",
            True,
            (90, 100, 115),
        )
        tarjeta = _rect_tarjeta_carrusel()
        superficie.blit(
            contador,
            contador.get_rect(midbottom=(tarjeta.centerx, tarjeta.bottom - MARGEN_PIE_TARJETA)),
        )

    def _dibujar_puntos(self, superficie: pygame.Surface) -> None:
        n = len(self.presets)
        if n <= 1:
            return
        posiciones, _sep = _layout_puntos_carrusel(n)
        for i, (x, y) in enumerate(posiciones):
            activo = i == self.indice
            radio = DOT_RADIO_ACTIVO if activo else DOT_RADIO_INACTIVO
            color = COLOR_TITULO if activo else (140, 165, 200)
            pygame.draw.circle(superficie, color, (x, y), radio)

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        _dibujar_cabecera_historia(
            superficie,
            self.fuentes,
            (
                "Ajusta la prioridad según tu práctica en cada modo (donde aplique)"
            ),
        )

        preset_lbl = self.fuentes["menu"].render(
            etiqueta_campo("tipo_partida", "Tipo de partida:"),
            True,
            COLOR_TEXTO,
        )
        superficie.blit(preset_lbl, preset_lbl.get_rect(midtop=(ANCHO // 2, Y_PRESET_LBL_TOP)))

        if self.preset_actual:
            _dibujar_flecha_carrusel(
                superficie,
                self.rect_flecha_izq,
                "izq",
                activo=self.indice > 0,
                hover=self.hover_izq,
            )
            _dibujar_flecha_carrusel(
                superficie,
                self.rect_flecha_der,
                "der",
                activo=self.indice < len(self.presets) - 1,
                hover=self.hover_der,
            )
            self._dibujar_tarjeta_preset(superficie, self.preset_actual)
            self._dibujar_puntos(superficie)

        if self.mensaje:
            aviso = self.fuentes["menu"].render(self.mensaje, True, COLOR_AVISO)
            superficie.blit(aviso, aviso.get_rect(center=(ANCHO // 2, self.boton_empezar.rect.y - 28)))

        for boton in self._botones_ui():
            boton.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(
            superficie, self.fuentes["pequena"], self._botones_ui()
        )

    def titulo_pausa(self) -> str:
        return "Modo historia — configuración"
