#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pantallas pygame del modo historia (presets fijos)."""

from __future__ import annotations

import time
from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from Comun.modelos import Pregunta
from Comun.motor_nucleo import (
    EstadoPartida,
    ResultadoRespuesta,
    linea_estado,
)
from Comun.motor_resistencia_comun import (
    aplicar_bonificaciones_puntos_resistencia,
    aplicar_modificadores_visuales_escalada,
    avisos_pre_pregunta_resistencia,
    crear_estado_resistencia,
    procesar_turno_resistencia,
    texto_pregunta_para_turno,
    tiempo_pregunta_efectivo,
    usar_powerup,
)
from Comun.powerups_resistencia import descripcion_powerup, etiqueta_powerup
from Comun.iconos_resistencia import emoji_powerup, prefijar_emoji
from Comun.config_historia import (
    GRUPOS_TEMATICOS,
    ConfigPresetHistoria,
    OpcionPreset,
    cursos_disponibles,
    semestres_para_curso,
    validar_config,
)
from Comun.presets_historia import PresetHistoria, config_defecto
from Comun.reglas_partida import ReglasPartida, formatear_resultado_puntuacion
from Comun.cierre_informe import CierreInformePartida, meta_cierre_historia
from Comun.ranking_resistencia import mejor_de_jugador, registrar_partida, top_records
from Comun.resistencia_historia import (
    aplicar_escalada_a_reglas,
    crear_seleccion_resistencia,
    elegir_indice_resistencia,
    escalada_para_pregunta,
    etiqueta_tier_exclusiva,
    texto_efectos_escalada,
)
from Comun.rutas import resolver_ranking_resistencia
from Grafico.textos_grafico import (
    BTN_ABANDONAR,
    BTN_ATRAS,
    BTN_CONTINUAR,
    BTN_EMPEZAR,
    BTN_VER_RANKING,
    BTN_VOLVER,
    BTN_VOLVER_MENU,
    etiqueta,
    etiqueta_campo,
    subtitulo,
    titulo_pantalla,
)
from Grafico.informe_partida import lineas_resumen_breve
from Grafico.aviso_resistencia import (
    aviso_debe_avanzar,
    dibujar_aviso_resistencia,
    marcar_inicio_aviso,
)
from Grafico.feedback_partida import (
    dibujar_feedback_partida,
    feedback_debe_avanzar,
    marcar_inicio_feedback,
    solucion_feedback_grafico,
)
from Grafico.barra_estado import dibujar_estado_partida_en_barra
from Grafico.modo_historia import (
    cargar_catalogo_historia,
    iniciar_pantalla_partida_historia,
    preparar_partida_historia,
)
from Comun.resistencia_historia import es_preset_resistencia
from Grafico.pantallas import (
    ALTURA_BARRA_PARTIDA,
    ALTO_BOTON_CONTINUAR_PARTIDA,
    ALTO_BARRA_PROGRESO_PARTIDA,
    ALTO_OPCION_PARTIDA,
    ALTO_PANEL_PREGUNTA,
    GAP_TRAS_BARRA_PROGRESO,
    GAP_TRAS_PANEL_PARTIDA,
    MARGEN_ICONOS_FIJOS,
    MARGEN_INF_PARTIDA,
    SEP_OPCIONES_PARTIDA,
    Y_PANEL_PREGUNTA,
    MenuPrincipal,
    Pantalla,
    ResumenPartida,
    _segundos_pregunta_restantes,
)
from Grafico.tooltips_ui import (
    TOOLTIP_ABANDONAR_HISTORIA,
    TOOLTIP_ABANDONAR_RESISTENCIA,
    TOOLTIP_ATRAS,
    TOOLTIP_CONTINUAR,
    TOOLTIP_EMPEZAR,
    TOOLTIP_VER_RANKING,
    tooltip_opcion_ciclo_historia,
)
from Grafico.tema import (
    ALTO,
    ANCHO,
    COLOR_ACENTO,
    COLOR_AVISO,
    COLOR_ERROR,
    COLOR_FONDO,
    COLOR_OK,
    COLOR_TEXTO,
    COLOR_TITULO,
    MARGEN,
    crear_fuentes,
)
from Grafico.texto import dibujar_texto_centro, preparar_texto_ui
from Grafico.ui import (
    Boton,
    BotonOpcion,
    _fuente_ajustada,
    dibujar_panel,
    dibujar_texto_multilinea,
    dibujar_tooltip,
    dibujar_tooltips_botones,
    medir_etiqueta_boton,
    posicionar_botones_fila,
    posicionar_pila_inferior,
    rect_boton_etiqueta,
    tamano_grupo_botones,
)

if TYPE_CHECKING:
    from Grafico.app import DatosJuego


Y_TITULO_HISTORIA = 46
COLOR_TEXTO_PANEL = (45, 55, 70)
Y_PASO_HISTORIA = 78
GAP_SUBTITULO_CONTENIDO = 20
GAP_LBL_CAMPO = 12
ALTO_CAMPO_NOMBRE_HIST = 44
GAP_CAMPO_SECCION = 28
GAP_SECCION_CARRUSEL = 20
ALTO_ETIQUETA_MENU = 24
Y_NOMBRE_LBL = Y_PASO_HISTORIA + ALTO_ETIQUETA_MENU + GAP_SUBTITULO_CONTENIDO
Y_CAMPO_NOMBRE = Y_NOMBRE_LBL + ALTO_ETIQUETA_MENU + GAP_LBL_CAMPO
Y_PRESET_LBL_TOP = Y_CAMPO_NOMBRE + ALTO_CAMPO_NOMBRE_HIST + GAP_CAMPO_SECCION
Y_CARRUSEL = Y_PRESET_LBL_TOP + ALTO_ETIQUETA_MENU + GAP_SECCION_CARRUSEL
ALTO_TARJETA_PRESET = 300
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
    if not activo:
        fondo, color = (40, 40, 40), (100, 100, 100)
    elif hover:
        fondo, color = (90, 140, 210), (255, 255, 255)
    else:
        fondo, color = (55, 95, 160), (240, 248, 255)
    pygame.draw.rect(superficie, fondo, rect, border_radius=10)
    pygame.draw.rect(superficie, color, rect, width=2, border_radius=10)
    cx, cy = rect.center
    tam = 12
    if direccion == "izq":
        puntos = [(cx + tam // 3, cy - tam), (cx - tam // 2, cy), (cx + tam // 3, cy + tam)]
    else:
        puntos = [(cx - tam // 3, cy - tam), (cx + tam // 2, cy), (cx - tam // 3, cy + tam)]
    if activo:
        pygame.draw.polygon(superficie, color, puntos)


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


def _dibujar_cabecera_historia(
    superficie: pygame.Surface,
    fuentes: dict[str, pygame.font.Font],
    paso: str,
) -> None:
    dibujar_texto_centro(
        superficie,
        titulo_pantalla("MODO HISTORIA"),
        (ANCHO // 2, Y_TITULO_HISTORIA),
        fuentes["titulo"].get_height(),
        COLOR_TITULO,
        bold=True,
    )
    dibujar_texto_centro(
        superficie,
        subtitulo(paso, "📕"),
        (ANCHO // 2, Y_PASO_HISTORIA),
        fuentes["pequena"].get_height(),
        COLOR_TEXTO,
    )


class ConfigModoHistoria(Pantalla):
    """Nombre del jugador y carrusel de presets (uno por pantalla)."""

    def __init__(
        self,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
        *,
        indice_inicial: int = 0,
        nombre_inicial: str = "",
        configs_preset: dict[str, ConfigPresetHistoria] | None = None,
    ) -> None:
        from Grafico.ui import CampoTexto

        self.datos = datos
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.fuentes = crear_fuentes()
        self.mensaje = ""
        self.presets = cargar_catalogo_historia()
        self._configs_preset: dict[str, ConfigPresetHistoria] = dict(
            configs_preset or {}
        )
        self.indice = 0
        if self.presets:
            self.indice = max(0, min(len(self.presets) - 1, indice_inicial))

        self.campo_nombre = CampoTexto(
            pygame.Rect(MARGEN + 40, Y_CAMPO_NOMBRE, ANCHO - 2 * MARGEN - 80, ALTO_CAMPO_NOMBRE_HIST),
            texto_inicial=nombre_inicial,
            placeholder="Nombre del jugador",
        )

        tarjeta = _rect_tarjeta_carrusel()
        alto_flecha = min(88, ALTO_TARJETA_PRESET - 40)
        y_flecha = tarjeta.centery - alto_flecha // 2
        self.rect_flecha_izq = pygame.Rect(tarjeta.x - ANCHO_FLECHA - 8, y_flecha, ANCHO_FLECHA, alto_flecha)
        self.rect_flecha_der = pygame.Rect(tarjeta.right + 8, y_flecha, ANCHO_FLECHA, alto_flecha)
        self.hover_izq = False
        self.hover_der = False

        fuente_menu = self.fuentes["menu"]
        etiq_ranking = etiqueta(*BTN_VER_RANKING)
        etiq_empezar = etiqueta(*BTN_CONTINUAR)
        etiq_volver = etiqueta(*BTN_VOLVER_MENU)
        ancho_btns, alto_btns = tamano_grupo_botones(
            [etiq_ranking, etiq_empezar, etiq_volver],
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
        self.boton_ranking = Boton(
            etiq_ranking,
            rect_boton_etiqueta(
                etiq_ranking,
                fuente_menu,
                x_centro=ANCHO // 2,
                y=0,
                ancho=ancho_btns,
                alto=alto_btns,
            ),
            self._ver_ranking,
            tooltip=TOOLTIP_VER_RANKING,
        )
        self.boton_ranking.activo = False
        if self.presets:
            self.boton_ranking.activo = es_preset_resistencia(self.presets[self.indice])
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
        nombre: str | None = None,
        configs_preset: dict[str, ConfigPresetHistoria] | None = None,
    ) -> ConfigModoHistoria:
        return ConfigModoHistoria(
            self.datos,
            self.ir_a,
            self.salir_app,
            indice_inicial=self.indice if indice is None else indice,
            nombre_inicial=self.campo_nombre.texto if nombre is None else nombre,
            configs_preset=(
                self._configs_preset if configs_preset is None else configs_preset
            ),
        )

    def _pie_tarjeta_con_ranking(self) -> bool:
        preset = self.preset_actual
        return bool(
            self.boton_ranking.activo
            and preset is not None
            and es_preset_resistencia(preset)
        )

    def _y_contador_tarjeta(self, tarjeta: pygame.Rect) -> int:
        return tarjeta.bottom - MARGEN_PIE_TARJETA

    def _reserva_pie_tarjeta(self) -> int:
        reserva = MARGEN_PIE_TARJETA + ALTO_TEXTO_CONTADOR
        if self._pie_tarjeta_con_ranking():
            reserva += GAP_RANKING_CONTADOR + self.boton_ranking.rect.height + GAP_DESC_RANKING
        return reserva

    def _reposicionar_boton_ranking_en_tarjeta(self) -> None:
        if not self.boton_ranking.activo:
            return
        tarjeta = _rect_tarjeta_carrusel()
        ancho_max = tarjeta.width - 2 * MARGEN_RANKING_TARJETA
        ancho = min(self.boton_ranking.rect.width, ancho_max)
        alto = self.boton_ranking.rect.height
        y_contador = self._y_contador_tarjeta(tarjeta)
        y = y_contador - ALTO_TEXTO_CONTADOR - GAP_RANKING_CONTADOR - alto
        x = tarjeta.centerx - ancho // 2
        self.boton_ranking.rect = pygame.Rect(x, y, ancho, alto)

    def _reposicionar_botones_navegacion(self) -> None:
        self._reposicionar_boton_ranking_en_tarjeta()
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
        preset = self.preset_actual
        self.boton_ranking.activo = bool(preset and es_preset_resistencia(preset))
        self._reposicionar_botones_navegacion()

    def _ver_ranking(self) -> None:
        carrusel = self._pantalla_carrusel()
        self.ir_a(
            RankingResistenciaHistoria(
                self.datos,
                self.ir_a,
                self.salir_app,
                volver_a=lambda: self.ir_a(carrusel),
            )
        )

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
        nombre = self.campo_nombre.valor()
        self.mensaje = ""
        if preset.tiene_opciones():
            indice = self.indice
            nombre_campo = self.campo_nombre.texto
            configs = dict(self._configs_preset)

            def _volver_opciones(config: ConfigPresetHistoria) -> None:
                configs[preset.id] = config
                self.ir_a(
                    ConfigModoHistoria(
                        self.datos,
                        self.ir_a,
                        self.salir_app,
                        indice_inicial=indice,
                        nombre_inicial=nombre_campo,
                        configs_preset=configs,
                    )
                )

            config_ini = self._configs_preset.get(preset.id)
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
        try:
            pantalla = iniciar_pantalla_partida_historia(
                self.datos,
                preset,
                config,
                nombre,
                self.ir_a,
                self.salir_app,
            )
        except ValueError as e:
            self.mensaje = str(e)
            return
        self.mensaje = ""
        self.ir_a(pantalla)

    def _botones_ui(self) -> list[Boton]:
        botones = [self.boton_empezar, self.boton_volver]
        if self.boton_ranking.activo:
            botones.insert(0, self.boton_ranking)
        return botones

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

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        self.campo_nombre.manejar_evento(evento)
        if evento.type == pygame.MOUSEWHEEL and self.presets:
            if evento.y > 0:
                self._anterior()
            elif evento.y < 0:
                self._siguiente()
        elif evento.type == pygame.MOUSEMOTION:
            self.hover_izq = self.rect_flecha_izq.collidepoint(evento.pos)
            self.hover_der = self.rect_flecha_der.collidepoint(evento.pos)
            for boton in self._botones_ui():
                boton.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if self.campo_nombre.manejar_evento(evento):
                return None
            if self._clic_flecha(evento.pos, evento.button):
                return None
            idx = self._indice_desde_punto(evento.pos)
            if idx is not None and evento.button == 1:
                self._ir_a_indice(idx)
                return None
            for boton in self._botones_ui():
                if boton.manejar_clic(evento.pos, evento.button):
                    break
        return None

    def _dibujar_tarjeta_preset(self, superficie: pygame.Surface, preset: PresetHistoria) -> None:
        tarjeta = _rect_tarjeta_carrusel()
        dibujar_panel(superficie, tarjeta, color=(255, 255, 255))

        cat = self.fuentes["pequena"].render(f"[{preset.categoria}]", True, COLOR_ACENTO)
        superficie.blit(cat, cat.get_rect(midtop=(tarjeta.centerx, tarjeta.y + 16)))

        if preset.usa_analisis_historico:
            badge = self.fuentes["pequena"].render(
                etiqueta_campo("datos_historicos", "Datos históricos MatCAD"), True, (20, 110, 70)
            )
            superficie.blit(badge, badge.get_rect(midtop=(tarjeta.centerx, tarjeta.y + 34)))

        nombre = self.fuentes["subtitulo"].render(
            preparar_texto_ui(preset.nombre),
            True,
            (25, 35, 50),
        )
        y_nombre = tarjeta.y + (58 if preset.usa_analisis_historico else 44)
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

        if self._pie_tarjeta_con_ranking():
            self.boton_ranking.dibujar(superficie, self.fuentes["menu"])

        contador = self.fuentes["pie"].render(
            f"{self.indice + 1} / {len(self.presets)}",
            True,
            (90, 100, 115),
        )
        superficie.blit(
            contador,
            contador.get_rect(midbottom=(tarjeta.centerx, self._y_contador_tarjeta(tarjeta))),
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
            "Los primeros modos usan qualificacions históricas del grado",
        )

        lbl = self.fuentes["menu"].render(
            etiqueta_campo("nombre_teclado", "Nombre (teclado):"), True, COLOR_TEXTO
        )
        superficie.blit(lbl, (MARGEN + 40, Y_NOMBRE_LBL))
        self.campo_nombre.dibujar(superficie, self.fuentes["menu"])

        preset_lbl = self.fuentes["menu"].render(
            etiqueta_campo("tipo_partida", "Tipo de partida:"), True, COLOR_TEXTO
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


class ConfigOpcionesHistoria(Pantalla):
    """Ajustes acotados del preset elegido (antes de empezar)."""

    Y_OPCIONES = Y_PASO_HISTORIA + ALTO_ETIQUETA_MENU + GAP_SUBTITULO_CONTENIDO
    ALTO_FILA = 56
    GAP_FILA = 8
    X_ETIQUETA = MARGEN + 36
    ANCHO_ETIQUETA = 340
    X_CONTROLES = MARGEN + 36 + 340 + 20
    ANCHO_BTN_CICLO = 44
    GAP_CICLO = 8

    def __init__(
        self,
        datos: DatosJuego,
        preset: PresetHistoria,
        nombre: str,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
        volver: Callable[[ConfigPresetHistoria], None],
        config_inicial: ConfigPresetHistoria | None = None,
    ) -> None:
        from Comun.datos import cargar_orden_materias
        from Comun.rutas import PATH_MATERIAS

        self.datos = datos
        self.preset = preset
        self.nombre = nombre
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.volver = volver
        self.fuentes = crear_fuentes()
        self.mensaje = ""
        self.orden_materias = cargar_orden_materias(PATH_MATERIAS)
        self.config = config_inicial or config_defecto(
            preset,
            materias_meta=datos.materias_meta,
            materias_orden=self.orden_materias,
        )
        self.botones_ciclo: dict[str, tuple[Boton, Boton]] = {}
        self._y_opcion: dict[str, int] = {}
        self._y_fin_opciones = self.Y_OPCIONES
        self._hover_opcion_valor: str | None = None
        self._reconstruir_layout()

        fuente_menu = self.fuentes["menu"]
        etiq_empezar = etiqueta(*BTN_EMPEZAR)
        etiq_atras = etiqueta(*BTN_ATRAS)
        ancho_btns, alto_btns = tamano_grupo_botones(
            [etiq_empezar, etiq_atras],
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
            self._empezar,
            tooltip=TOOLTIP_EMPEZAR,
        )
        self.boton_atras = Boton(
            etiq_atras,
            rect_boton_etiqueta(
                etiq_atras,
                fuente_menu,
                x_centro=ANCHO // 2,
                y=0,
                ancho=ancho_btns,
                alto=alto_btns,
            ),
            self._volver,
            tooltip=TOOLTIP_ATRAS,
        )
        self._reposicionar_botones_navegacion()

    def _opcion_preset(self, op_id: str) -> OpcionPreset | None:
        for op in self.preset.opciones:
            if op.id == op_id:
                return op
        return None

    def _clave_opcion(self, op_id: str) -> str:
        raw = self.config.valores.get(op_id)
        return "" if raw is None else str(raw)

    def _actualizar_hover_opcion_valor(self, pos: tuple[int, int]) -> None:
        self._hover_opcion_valor = None
        for op_id in self._y_opcion:
            _, rect_val, _ = self._rects_control_fila(op_id)
            if not rect_val.collidepoint(pos):
                continue
            op = self._opcion_preset(op_id)
            if op and tooltip_opcion_ciclo_historia(
                op.id,
                op.tipo,
                self._clave_opcion(op_id),
                etiqueta_opcion=op.etiqueta,
            ):
                self._hover_opcion_valor = op_id
            return

    def _dibujar_tooltip_opcion_valor(self, superficie: pygame.Surface) -> None:
        if not self._hover_opcion_valor:
            return
        op_id = self._hover_opcion_valor
        op = self._opcion_preset(op_id)
        if not op:
            return
        tip = tooltip_opcion_ciclo_historia(
            op.id,
            op.tipo,
            self._clave_opcion(op_id),
            etiqueta_opcion=op.etiqueta,
        )
        if not tip:
            return
        _, rect_val, _ = self._rects_control_fila(op_id)
        dibujar_tooltip(superficie, self.fuentes["pequena"], rect_val, tip)

    def _volver(self) -> None:
        self.volver(self.config)

    def _y_preferida_botones_navegacion(self) -> int:
        return max(560, self._y_fin_opciones + 48)

    def _reposicionar_botones_navegacion(self) -> None:
        if not hasattr(self, "boton_empezar"):
            return
        posicionar_botones_fila(
            [self.boton_atras, self.boton_empezar],
            self._y_preferida_botones_navegacion(),
            x_centro=ANCHO // 2,
            gap=12,
        )

    def _rect_panel_opciones(self) -> pygame.Rect:
        alto = max(120, self._y_fin_opciones - self.Y_OPCIONES + 24)
        return pygame.Rect(
            MARGEN + 16,
            self.Y_OPCIONES - 16,
            ANCHO - 2 * MARGEN - 32,
            alto,
        )

    def _ancho_zona_controles(self) -> int:
        panel = self._rect_panel_opciones()
        return panel.right - 24 - self.X_CONTROLES

    def _rects_control_fila(self, op_id: str) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
        fila_y = self._y_opcion[op_id]
        ancho = self._ancho_zona_controles()
        alto = 36
        y = fila_y + 10
        rect_izq = pygame.Rect(self.X_CONTROLES, y, self.ANCHO_BTN_CICLO, alto)
        rect_der = pygame.Rect(self.X_CONTROLES + ancho - self.ANCHO_BTN_CICLO, y, self.ANCHO_BTN_CICLO, alto)
        rect_val = pygame.Rect(
            rect_izq.right + self.GAP_CICLO,
            y,
            rect_der.x - rect_izq.right - 2 * self.GAP_CICLO,
            alto,
        )
        return rect_izq, rect_val, rect_der

    def _reconstruir_layout(self) -> None:
        self._y_opcion.clear()
        y = self.Y_OPCIONES
        for op in self.preset.opciones:
            self._y_opcion[op.id] = y
            y += self.ALTO_FILA + self.GAP_FILA
        self._y_fin_opciones = y

        self.botones_ciclo.clear()
        for op in self.preset.opciones:
            rect_izq, _, rect_der = self._rects_control_fila(op.id)
            self.botones_ciclo[op.id] = (
                Boton("◀", rect_izq, lambda oid=op.id: self._ciclar_opcion(oid, -1)),
                Boton("▶", rect_der, lambda oid=op.id: self._ciclar_opcion(oid, 1)),
            )
        self._reposicionar_botones_navegacion()

    def _items_opcion(self, op_id: str) -> list[tuple[str, str]]:
        for op in self.preset.opciones:
            if op.id != op_id:
                continue
            if op.tipo == "curso":
                items = [(c, f"Curso {c}") for c in cursos_disponibles(self.datos.materias_meta)]
                if not op.obligatorio:
                    return [("", "Todo el grado")] + items
                return items
            if op.tipo == "semestre":
                curso = self.config.valores.get("curso")
                if not curso:
                    return []
                items = [
                    (s, f"Semestre {s}")
                    for s in semestres_para_curso(self.datos.materias_meta, str(curso))
                ]
                if not op.obligatorio:
                    return [("", "Todo el curso")] + items
                return items
            if op.tipo == "grupo":
                return list(GRUPOS_TEMATICOS.items())
            if op.tipo == "materia":
                return [(m, m) for m in self.orden_materias]
            if op.tipo == "eleccion":
                return list(op.valores)
        return []

    def _texto_valor(self, op_id: str) -> str:
        for op in self.preset.opciones:
            if op.id != op_id:
                continue
            raw = self.config.valores.get(op_id)
            if raw is None or raw == "":
                if op.tipo == "curso" and not op.obligatorio:
                    return "Todo el grado"
                if op.tipo == "semestre" and not op.obligatorio:
                    return "Todo el curso"
                return "—"
            if op.tipo == "grupo":
                return GRUPOS_TEMATICOS.get(str(raw), str(raw))
            if op.tipo == "eleccion":
                for v, etq in op.valores:
                    if v == str(raw):
                        return etq
            if op.tipo == "curso":
                return f"Curso {raw}"
            if op.tipo == "semestre":
                return f"Semestre {raw}"
            if op.tipo == "entero":
                if op.id == "tiempo_total_min" and int(raw) == 0:
                    return "Sin límite"
                return str(raw)
            return str(raw)
        return ""

    def _ciclar_opcion(self, op_id: str, delta: int) -> None:
        for op in self.preset.opciones:
            if op.id != op_id:
                continue
            if op.tipo == "entero":
                self._ciclar_entero(op, delta)
            else:
                self._ciclar_lista(op_id, delta)
            return

    def _ciclar_entero(self, op: OpcionPreset, delta: int) -> None:
        min_v = op.min if op.min is not None else 0
        max_v = op.max if op.max is not None else 9999
        defecto = int(op.defecto if op.defecto is not None else min_v)
        actual = int(self.config.valores.get(op.id, defecto))
        actual = min(max(actual, min_v), max_v)
        rango = max_v - min_v + 1
        if rango <= 1:
            self.config.valores[op.id] = min_v
        else:
            self.config.valores[op.id] = min_v + (actual - min_v + delta) % rango
        self.mensaje = ""

    def _ciclar_lista(self, op_id: str, delta: int) -> None:
        items = self._items_opcion(op_id)
        if not items:
            self.mensaje = "Completa las opciones previas primero."
            return
        valores = [k for k, _ in items]
        actual = self.config.valores.get(op_id)
        if actual is None or actual == "":
            idx = 0
        else:
            try:
                idx = valores.index(str(actual))
            except ValueError:
                idx = 0
        idx = (idx + delta) % len(valores)
        elegido = valores[idx]
        if elegido == "":
            self.config.valores.pop(op_id, None)
        else:
            self.config.valores[op_id] = elegido
        if op_id == "curso":
            self.config.valores.pop("semestre", None)
            self._reconstruir_layout()
        self.mensaje = ""

    def _rect_valor_ciclo(self, op_id: str) -> pygame.Rect | None:
        if op_id not in self._y_opcion:
            return None
        _, rect_val, _ = self._rects_control_fila(op_id)
        return rect_val

    def _leer_config(self) -> ConfigPresetHistoria:
        return validar_config(
            self.preset.opciones,
            ConfigPresetHistoria(valores=dict(self.config.valores)),
            materias_meta=self.datos.materias_meta,
        )

    def _empezar(self) -> None:
        try:
            config = self._leer_config()
        except ValueError as e:
            self.mensaje = str(e)
            return
        self.mensaje = ""
        try:
            pantalla = iniciar_pantalla_partida_historia(
                self.datos,
                self.preset,
                config,
                self.nombre,
                self.ir_a,
                self.salir_app,
            )
        except ValueError as e:
            self.mensaje = str(e)
            return
        self.ir_a(pantalla)

    def _botones_ui(self) -> list[Boton]:
        botones = [self.boton_empezar, self.boton_atras]
        for par in self.botones_ciclo.values():
            botones.extend(par)
        return botones

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEMOTION:
            for boton in self._botones_ui():
                boton.actualizar_hover(evento.pos)
            self._actualizar_hover_opcion_valor(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            for boton in self._botones_ui():
                if boton.manejar_clic(evento.pos, evento.button):
                    break
        return None

    def _dibujar_fila_opcion(self, superficie: pygame.Surface, op, y: int) -> None:
        etiqueta = op.etiqueta.rstrip(":")
        lbl = self.fuentes["menu"].render(etiqueta + ":", True, COLOR_TEXTO_PANEL)
        superficie.blit(lbl, (self.X_ETIQUETA, y + 16))

        if op.id not in self.botones_ciclo:
            return

        izq, der = self.botones_ciclo[op.id]
        val_rect = self._rect_valor_ciclo(op.id)
        if val_rect and val_rect.width > 0:
            dibujar_panel(superficie, val_rect, color=(248, 250, 255))
            texto = preparar_texto_ui(self._texto_valor(op.id))
            fuente_val = _fuente_ajustada(
                texto,
                self.fuentes["cuerpo"],
                val_rect.width - 16,
            )
            val = fuente_val.render(texto, True, (25, 35, 50))
            superficie.blit(val, val.get_rect(center=val_rect.center))

        izq.dibujar(superficie, self.fuentes["menu"])
        der.dibujar(superficie, self.fuentes["menu"])

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        _dibujar_cabecera_historia(
            superficie,
            self.fuentes,
            f"Configurar: {self.preset.nombre}",
        )

        dibujar_panel(superficie, self._rect_panel_opciones(), color=(255, 255, 255))

        for op in self.preset.opciones:
            y = self._y_opcion.get(op.id, self.Y_OPCIONES)
            self._dibujar_fila_opcion(superficie, op, y)

        if self.mensaje:
            aviso = self.fuentes["menu"].render(self.mensaje, True, COLOR_AVISO)
            superficie.blit(
                aviso,
                aviso.get_rect(center=(ANCHO // 2, self.boton_empezar.rect.y - 28)),
            )

        self.boton_empezar.dibujar(superficie, self.fuentes["menu"])
        self.boton_atras.dibujar(superficie, self.fuentes["menu"])
        self._dibujar_tooltip_opcion_valor(superficie)
        dibujar_tooltips_botones(
            superficie,
            self.fuentes["pequena"],
            [self.boton_atras, self.boton_empezar],
        )

    def titulo_pausa(self) -> str:
        return f"Configurar — {self.preset.nombre}"


class PartidaModoHistoria(Pantalla):
    """Partida con lista fija de preguntas (como en consola)."""

    def __init__(
        self,
        *,
        nombre: str,
        preset: PresetHistoria,
        preguntas: list[Pregunta],
        reglas: ReglasPartida,
        ir_a: Callable[[Pantalla], None],
        datos: DatosJuego,
        salir_app: Callable[[], None],
        materias_examen: list[str] | None = None,
    ) -> None:
        self.nombre = nombre
        self.preset = preset
        self.preguntas = preguntas
        self.materias_examen = materias_examen or []
        self.total = len(preguntas)
        self.ir_a = ir_a
        self.datos = datos
        self.salir_app = salir_app
        self.fuentes = crear_fuentes()
        self.registros: list = []
        self.estado = EstadoPartida(
            nombre=nombre,
            reglas=reglas,
            vidas_restantes=reglas.vidas,
        )
        self.indice = 0
        self.fase = "pregunta"
        self.feedback_mensaje = ""
        self.feedback_solucion: str | None = None
        self.feedback_ok = False
        self.botones_opcion: list[BotonOpcion] = []
        self.inicio_pregunta = time.monotonic()
        self.inicio_feedback = 0.0
        lbl_abandonar = etiqueta(*BTN_ABANDONAR)
        self.boton_abandonar = Boton(
            lbl_abandonar,
            rect_boton_etiqueta(
                lbl_abandonar, self.fuentes["pequena"], x_derecha=ANCHO - MARGEN, y=14
            ),
            self._abandonar,
            tooltip=TOOLTIP_ABANDONAR_HISTORIA,
        )
        self._reconstruir_opciones()

    def _pregunta_actual(self) -> Pregunta:
        return self.preguntas[self.indice]

    def _y_fin_opciones(self) -> int:
        return self._y_inicio_opciones() + 4 * (ALTO_OPCION_PARTIDA + SEP_OPCIONES_PARTIDA)

    def _texto_progreso(self) -> str:
        return f"Escena {self.indice + 1}/{self.total}"

    def _linea_estado_actual(self) -> str:
        seg_preg = None
        if self.fase == "pregunta":
            seg_preg = _segundos_pregunta_restantes(
                self.inicio_pregunta,
                self.estado.reglas.tiempo_por_pregunta_seg,
            )
        return linea_estado(
            self.estado,
            self._texto_progreso(),
            segundos_pregunta_restantes=seg_preg,
        )

    def _examen_cerrado(self) -> bool:
        return self.estado.reglas.correccion_al_final

    def _y_inicio_opciones(self) -> int:
        y = Y_PANEL_PREGUNTA + ALTO_PANEL_PREGUNTA + GAP_TRAS_PANEL_PARTIDA
        if self.total > 0:
            y += ALTO_BARRA_PROGRESO_PARTIDA + GAP_TRAS_BARRA_PROGRESO
        return y

    def _reconstruir_opciones(self) -> None:
        p = self._pregunta_actual()
        self.botones_opcion = []
        y = self._y_inicio_opciones()
        for letra in ("A", "B", "C", "D"):
            rect = pygame.Rect(MARGEN, y, ANCHO - 2 * MARGEN, ALTO_OPCION_PARTIDA)
            boton = BotonOpcion(
                letra,
                p.opciones.get(letra, ""),
                rect,
                lambda l=letra: self._responder(l),
            )
            self.botones_opcion.append(boton)
            y += ALTO_OPCION_PARTIDA + SEP_OPCIONES_PARTIDA

    def _registrar_respuesta(self, p: Pregunta, resultado: ResultadoRespuesta) -> None:
        from Consola.informe_examen import RegistroRespuesta

        self.registros.append(
            RegistroRespuesta(
                indice=self.estado.respondidas,
                pregunta=p,
                respuesta=resultado.respuesta,
                acierto=resultado.acierto,
                tiempo_agotado=resultado.tiempo_agotado,
            )
        )

    def _abandonar(self) -> None:
        if self.registros:
            self._fin_partida(abandonado=True)
            return
        self.ir_a(MenuPrincipal(self.datos, self.ir_a, self.salir_app))

    def _fin_partida(self, *, abandonado: bool = False) -> None:
        from Consola.generador_examen_historia import cargar_estadisticas_historicas

        cierre = None
        if self.registros:
            stats = cargar_estadisticas_historicas(
                materias_validas=set(self.datos.materias_meta)
            )
            titulo_txt = (
                f"ABANDONO — {self.preset.nombre}"
                if abandonado
                else f"FIN — {self.preset.nombre}"
            )
            cierre = CierreInformePartida(
                registros=list(self.registros),
                titulo=titulo_txt,
                total_previsto=self.total,
                prefijo="examen",
                meta=meta_cierre_historia(
                    preset_id=self.preset.id,
                    preset_nombre=self.preset.nombre,
                    perfil=self.preset.perfil,
                    materias=self.materias_examen,
                    n_preguntas=self.total,
                ),
                stats_historicas=stats,
                abandonado=abandonado,
            )
        titulo_pantalla = (
            f"ABANDONO — {self.preset.nombre[:40]}"
            if abandonado
            else f"FIN — {self.preset.nombre[:44]}"
        )
        self.ir_a(
            ResumenHistoriaPartida(
                self.estado,
                self.total,
                self.preset,
                self.ir_a,
                self.datos,
                self.salir_app,
                cierre_informe=cierre,
                titulo=titulo_pantalla,
            )
        )

    def _tras_respuesta(self, resultado: ResultadoRespuesta) -> None:
        p = self._pregunta_actual()
        feedback = evaluar_respuesta(p, self.estado, resultado)
        self._registrar_respuesta(p, resultado)
        if self._examen_cerrado():
            if not self.estado.debe_continuar(self.total) or self.indice >= self.total - 1:
                self._fin_partida()
                return
            self.indice += 1
            self.inicio_pregunta = time.monotonic()
            self.fase = "pregunta"
            self._reconstruir_opciones()
            return

        self.feedback_mensaje = feedback.mensaje
        self.feedback_solucion = solucion_feedback_grafico(feedback.solucion)
        self.feedback_ok = resultado.acierto and not resultado.tiempo_agotado
        self.fase = "feedback"
        self.inicio_feedback = marcar_inicio_feedback()
        for boton in self.botones_opcion:
            boton.activo = False
            if boton.letra == p.correcta:
                boton.marcar_correcta = True
            elif boton.letra == resultado.respuesta and not resultado.acierto:
                boton.marcar_incorrecta = True

    def _responder(self, letra: str) -> None:
        if self.fase != "pregunta":
            return
        p = self._pregunta_actual()
        correcta = p.correcta if p.correcta in {"A", "B", "C", "D"} else ""
        acierto = letra == correcta and bool(correcta)
        self._tras_respuesta(ResultadoRespuesta(acierto=acierto, respuesta=letra))

    def _responder_timeout(self) -> None:
        if self.fase != "pregunta":
            return
        self._tras_respuesta(
            ResultadoRespuesta(acierto=False, respuesta="", tiempo_agotado=True)
        )

    def _continuar(self) -> None:
        if self.fase != "feedback":
            return
        if not self.estado.debe_continuar(self.total) or self.indice >= self.total - 1:
            self._fin_partida()
            return
        self.indice += 1
        self.inicio_pregunta = time.monotonic()
        self.fase = "pregunta"
        self.feedback_mensaje = ""
        self.feedback_solucion = None
        self.feedback_ok = False
        self._reconstruir_opciones()

    def actualizar(self) -> Pantalla | None:
        if self.fase == "feedback":
            if feedback_debe_avanzar(
                self.inicio_feedback,
                solucion=self.feedback_solucion,
                acierto=self.feedback_ok,
            ):
                self._continuar()
            return None
        if self.fase != "pregunta":
            return None
        if self.estado.tiempo_total_restante() == 0:
            self._fin_partida()
            return None
        lim = self.estado.reglas.tiempo_por_pregunta_seg
        if lim and _segundos_pregunta_restantes(self.inicio_pregunta, lim) == 0:
            self._responder_timeout()
        return None

    def titulo_pausa(self) -> str:
        return f"{self.preset.nombre} · {self._linea_estado_actual()}"

    def _dibujar_barra_superior(self, superficie: pygame.Surface) -> None:
        fuente = self.fuentes["pequena"]
        lbl_abandonar = etiqueta(*BTN_ABANDONAR)
        self.boton_abandonar.rect = rect_boton_etiqueta(
            lbl_abandonar,
            fuente,
            x_derecha=ANCHO - MARGEN,
            y=14,
        )
        x_centro_min = MARGEN_ICONOS_FIJOS + 8
        x_centro_max = self.boton_abandonar.rect.x - 12
        ancho_centro = max(80, x_centro_max - x_centro_min)
        seg_preg = None
        if self.fase == "pregunta":
            seg_preg = _segundos_pregunta_restantes(
                self.inicio_pregunta,
                self.estado.reglas.tiempo_por_pregunta_seg,
            )
        dibujar_estado_partida_en_barra(
            superficie,
            estado=self.estado,
            progreso=self._texto_progreso(),
            fuentes=self.fuentes,
            x_centro_min=x_centro_min,
            x_centro_max=x_centro_max,
            segundos_pregunta_restantes=seg_preg,
        )
        titulo = fuente.render(preparar_texto_ui(self.preset.nombre), True, COLOR_ACENTO)
        if titulo.get_width() <= ancho_centro:
            superficie.blit(titulo, titulo.get_rect(midtop=(ANCHO // 2, 36)))
        pygame.draw.line(
            superficie,
            (50, 72, 110),
            (MARGEN, ALTURA_BARRA_PARTIDA),
            (ANCHO - MARGEN, ALTURA_BARRA_PARTIDA),
            1,
        )
        self.boton_abandonar.dibujar(superficie, fuente)

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEMOTION:
            self.boton_abandonar.actualizar_hover(evento.pos)
            if self.fase == "pregunta":
                for boton in self.botones_opcion:
                    boton.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if self.boton_abandonar.manejar_clic(evento.pos, evento.button):
                return None
            if self.fase == "pregunta":
                for boton in self.botones_opcion:
                    if boton.manejar_clic(evento.pos, evento.button):
                        break
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        self._dibujar_barra_superior(superficie)

        p = self._pregunta_actual()
        panel = pygame.Rect(MARGEN, Y_PANEL_PREGUNTA, ANCHO - 2 * MARGEN, ALTO_PANEL_PREGUNTA)
        dibujar_panel(superficie, panel)
        meta = self.fuentes["pequena"].render(
            f"{p.materia} · {p.tipo} / {p.dificultad}",
            True,
            COLOR_ACENTO,
        )
        superficie.blit(meta, (panel.x + 12, panel.y + 10))
        dibujar_texto_multilinea(
            superficie,
            self.fuentes["cuerpo"],
            p.texto,
            pygame.Rect(panel.x + 8, panel.y + 36, panel.width - 16, panel.height - 44),
            COLOR_TITULO,
        )

        if self.total > 0:
            barra_y = Y_PANEL_PREGUNTA + panel.height + GAP_TRAS_PANEL_PARTIDA
            barra_fondo = pygame.Rect(
                MARGEN, barra_y, ANCHO - 2 * MARGEN, ALTO_BARRA_PROGRESO_PARTIDA
            )
            pygame.draw.rect(superficie, (40, 56, 80), barra_fondo, border_radius=4)
            progreso_w = int(barra_fondo.width * self.estado.respondidas / self.total)
            if progreso_w:
                pygame.draw.rect(
                    superficie,
                    COLOR_ACENTO,
                    pygame.Rect(
                        barra_fondo.x,
                        barra_fondo.y,
                        progreso_w,
                        ALTO_BARRA_PROGRESO_PARTIDA,
                    ),
                    border_radius=4,
                )

        for boton in self.botones_opcion:
            boton.dibujar(superficie, self.fuentes["opcion"])

        if self.fase == "feedback":
            dibujar_feedback_partida(
                superficie,
                self.fuentes,
                mensaje=self.feedback_mensaje,
                solucion=self.feedback_solucion,
                acierto=self.feedback_ok,
                y_mensaje=self._y_fin_opciones() + 8,
            )
        dibujar_tooltips_botones(
            superficie, self.fuentes["pequena"], [self.boton_abandonar]
        )


class PartidaResistenciaHistoria(Pantalla):
    """Modo resistencia: pool infinito, racha, vidas, inventario y escalada de dificultad."""

    def __init__(
        self,
        *,
        nombre: str,
        preset: PresetHistoria,
        pool: list[Pregunta],
        reglas: ReglasPartida,
        ir_a: Callable[[Pantalla], None],
        datos: DatosJuego,
        salir_app: Callable[[], None],
    ) -> None:
        self.nombre = nombre
        self.preset = preset
        self.pool = pool
        self.ir_a = ir_a
        self.datos = datos
        self.salir_app = salir_app
        self.fuentes = crear_fuentes()
        self.registros: list = []
        self.reglas_base = reglas
        self.er = crear_estado_resistencia(reglas.vidas or 3)
        self.escalada = escalada_para_pregunta(1)
        self.estado = EstadoPartida(
            nombre=nombre,
            reglas=aplicar_escalada_a_reglas(reglas, self.escalada),
            vidas_restantes=min(reglas.vidas or 3, self.er.vidas_max),
        )
        self.seleccion_pool = crear_seleccion_resistencia(pool)
        self.pregunta_idx: int | None = None
        self.indice_global = 0
        self.fase = "pregunta"
        self.feedback_mensaje = ""
        self.feedback_solucion: str | None = None
        self.feedback_ok = False
        self.reintentar_pregunta = False
        self.recompensa_pendiente = ""
        self.efecto_actual = ""
        self.avisos_cola: list[str] = []
        self.indice_aviso = 0
        self.inicio_aviso = 0.0
        self.botones_opcion: list[BotonOpcion] = []
        self.botones_powerup: list[Boton] = []
        self.inicio_pregunta = time.monotonic()
        self.inicio_feedback = 0.0
        lbl_abandonar = etiqueta(*BTN_ABANDONAR)
        self.boton_abandonar = Boton(
            lbl_abandonar,
            rect_boton_etiqueta(
                lbl_abandonar, self.fuentes["pequena"], x_derecha=ANCHO - MARGEN, y=14
            ),
            self._abandonar,
            tooltip=TOOLTIP_ABANDONAR_RESISTENCIA,
        )
        if not self._cargar_siguiente_pregunta(inicial=True):
            raise ValueError("Sin preguntas para resistencia.")
        self._entrar_pregunta_o_avisos()

    def _iniciar_fase_pregunta(self) -> None:
        p = self._pregunta_actual()
        aplicar_modificadores_visuales_escalada(
            self.er, self.escalada, p, self._numero_pregunta()
        )
        self.fase = "pregunta"
        self.inicio_pregunta = time.monotonic()
        self.avisos_cola = []
        self.indice_aviso = 0
        self._reconstruir_opciones()
        self._reconstruir_powerups()

    def _texto_pregunta_visible(self) -> str:
        return texto_pregunta_para_turno(self._pregunta_actual(), self.er)

    def _entrar_pregunta_o_avisos(self, *, recompensa_etiqueta: str | None = None) -> None:
        etiqueta_recompensa = recompensa_etiqueta or self.recompensa_pendiente or None
        self.recompensa_pendiente = ""
        p = self._pregunta_actual()
        avisos = avisos_pre_pregunta_resistencia(
            p,
            self._numero_pregunta(),
            recompensa_etiqueta=etiqueta_recompensa,
        )
        if avisos:
            self.avisos_cola = avisos
            self.indice_aviso = 0
            self.fase = "aviso"
            self.inicio_aviso = marcar_inicio_aviso()
            self.botones_opcion = []
            self.botones_powerup = []
            return
        self._iniciar_fase_pregunta()

    def _limite_tiempo_pregunta(self) -> int | None:
        return tiempo_pregunta_efectivo(
            self.estado.reglas.tiempo_por_pregunta_seg,
            self.er,
        )

    def _numero_pregunta(self) -> int:
        return self.indice_global + 1

    def _aplicar_escalada(self, numero_pregunta: int) -> None:
        self.escalada = escalada_para_pregunta(numero_pregunta)
        self.estado.reglas = aplicar_escalada_a_reglas(self.reglas_base, self.escalada)
        self.efecto_actual = texto_efectos_escalada(self.escalada)

    def _cargar_siguiente_pregunta(self, *, inicial: bool = False) -> bool:
        self.er.reset_pregunta()
        numero = self._numero_pregunta()
        self._aplicar_escalada(numero)
        idx = elegir_indice_resistencia(
            self.pool, self.seleccion_pool, self.escalada, numero
        )
        if idx is None:
            return False
        self.pregunta_idx = idx
        return True

    def _pregunta_actual(self) -> Pregunta:
        if self.pregunta_idx is None:
            raise IndexError("Sin pregunta cargada.")
        return self.pool[self.pregunta_idx]

    def _texto_progreso(self) -> str:
        return f"#{self._numero_pregunta()} · Racha {self.er.racha}"

    def _altura_banda_powerups(self) -> int:
        n = sum(1 for pid in self.er.inventario if self.er.cantidad(pid) > 0)
        if n <= 0:
            return 0
        filas = 1 + (n - 1) // 4
        return filas * 36 + 8

    def _y_banda_powerups(self) -> int:
        altura = self._altura_banda_powerups()
        if altura <= 0:
            return ALTO - MARGEN_INF_PARTIDA
        return ALTO - MARGEN_INF_PARTIDA - altura

    def _y_inicio_opciones(self) -> int:
        return Y_PANEL_PREGUNTA + ALTO_PANEL_PREGUNTA + GAP_TRAS_PANEL_PARTIDA + 8

    def _y_fin_opciones(self) -> int:
        n = len(self.botones_opcion)
        return self._y_inicio_opciones() + n * (ALTO_OPCION_PARTIDA + SEP_OPCIONES_PARTIDA)

    def _linea_estado_actual(self) -> str:
        seg_preg = None
        if self.fase == "pregunta":
            seg_preg = _segundos_pregunta_restantes(
                self.inicio_pregunta,
                self._limite_tiempo_pregunta(),
            )
        return linea_estado(
            self.estado,
            self._texto_progreso(),
            segundos_pregunta_restantes=seg_preg,
            vidas_max=self.er.vidas_max,
        )

    def _reconstruir_powerups(self) -> None:
        self.botones_powerup = []
        if self.fase != "pregunta":
            return
        items = [
            (pid, self.er.cantidad(pid))
            for pid in sorted(self.er.inventario.keys())
            if self.er.cantidad(pid) > 0
        ]
        if not items:
            return
        x = MARGEN
        y = self._y_banda_powerups()
        for pid, cant in items:
            nombre = etiqueta_powerup(pid)
            etiqueta_btn = prefijar_emoji(f"{nombre} ({cant})", emoji_powerup(pid))
            ancho = min(156, max(96, medir_etiqueta_boton(etiqueta_btn, self.fuentes["pequena"])[0] + 28))
            rect = pygame.Rect(x, y, ancho, 32)
            self.botones_powerup.append(
                Boton(
                    etiqueta_btn,
                    rect,
                    lambda p=pid: self._usar_powerup(p),
                    tooltip=descripcion_powerup(pid),
                )
            )
            x += ancho + 8
            if x > ANCHO - MARGEN - 80:
                x = MARGEN
                y += 36

    def _reconstruir_opciones(self) -> None:
        p = self._pregunta_actual()
        self.botones_opcion = []
        y = self._y_inicio_opciones()
        for letra in ("A", "B", "C", "D"):
            if letra in self.er.letras_ocultas:
                continue
            rect = pygame.Rect(MARGEN, y, ANCHO - 2 * MARGEN, ALTO_OPCION_PARTIDA)
            boton = BotonOpcion(
                letra,
                p.opciones.get(letra, ""),
                rect,
                lambda l=letra: self._responder(l),
            )
            self.botones_opcion.append(boton)
            y += ALTO_OPCION_PARTIDA + SEP_OPCIONES_PARTIDA

    def _usar_powerup(self, powerup_id: str) -> None:
        if self.fase != "pregunta":
            return
        p = self._pregunta_actual()
        err = usar_powerup(powerup_id, self.er, p)
        if err:
            self.feedback_mensaje = err
            self.feedback_solucion = None
            self.feedback_ok = False
            self.fase = "feedback"
            self.inicio_feedback = marcar_inicio_feedback()
            return
        if powerup_id == "skip":
            self.indice_global += 1
            if not self._cargar_siguiente_pregunta():
                self._fin_partida()
                return
            self.feedback_mensaje = ""
            self.feedback_solucion = None
            self._entrar_pregunta_o_avisos()
            return
        if powerup_id in {"fifty_fifty", "bomba"}:
            self._reconstruir_opciones()
        self._reconstruir_powerups()

    def _registrar_respuesta(self, p: Pregunta, resultado: ResultadoRespuesta) -> None:
        from Consola.informe_examen import RegistroRespuesta

        self.registros.append(
            RegistroRespuesta(
                indice=self.estado.respondidas,
                pregunta=p,
                respuesta=resultado.respuesta,
                acierto=resultado.acierto,
                tiempo_agotado=resultado.tiempo_agotado,
            )
        )

    def _ajustar_multiplicador(self, resultado: ResultadoRespuesta, puntos_prev: int) -> None:
        aplicar_bonificaciones_puntos_resistencia(
            self.estado,
            puntos_prev=puntos_prev,
            racha=self.er.racha,
            mult_escalada=self.escalada.multiplicador_puntos,
            exclusiva=self._pregunta_actual().exclusiva_resistencia,
            acierto=resultado.acierto,
            tiempo_agotado=resultado.tiempo_agotado,
        )

    def _fin_partida(self, *, abandonado: bool = False) -> None:
        from Consola.generador_examen_historia import cargar_estadisticas_historicas

        posicion_ranking: int | None = None
        if self.registros and not abandonado:
            try:
                _, posicion_ranking = registrar_partida(
                    resolver_ranking_resistencia(),
                    nombre=self.nombre,
                    racha=self.er.mejor_racha,
                    puntos=self.estado.puntos_arcade,
                    respondidas=self.estado.respondidas,
                    preset_id=self.preset.id,
                )
            except ValueError:
                posicion_ranking = None

        cierre = None
        if self.registros:
            stats = cargar_estadisticas_historicas(
                materias_validas=set(self.datos.materias_meta)
            )
            titulo_txt = (
                f"ABANDONO — {self.preset.nombre}"
                if abandonado
                else f"FIN RACHA — {self.preset.nombre}"
            )
            cierre = CierreInformePartida(
                registros=list(self.registros),
                titulo=titulo_txt,
                total_previsto=self.estado.respondidas,
                prefijo="resistencia",
                meta=meta_cierre_historia(
                    preset_id=self.preset.id,
                    preset_nombre=self.preset.nombre,
                    perfil=self.preset.perfil,
                    materias=[],
                    n_preguntas=self.estado.respondidas,
                    modo_resistencia=True,
                    racha=self.er.mejor_racha,
                ),
                stats_historicas=stats,
                abandonado=abandonado,
            )
        titulo_pantalla = (
            f"Pregunta {self.estado.respondidas} — {self.preset.nombre[:36]}"
            if not abandonado
            else f"Abandono — {self.preset.nombre[:40]}"
        )
        self.ir_a(
            ResumenResistenciaHistoria(
                self.estado,
                self.preset,
                self.ir_a,
                self.datos,
                self.salir_app,
                cierre_informe=cierre,
                titulo=titulo_pantalla,
                posicion_ranking=posicion_ranking,
                abandonado=abandonado,
                mejor_racha=self.er.mejor_racha,
            )
        )

    def _abandonar(self) -> None:
        if self.registros:
            self._fin_partida(abandonado=True)
            return
        self.ir_a(MenuPrincipal(self.datos, self.ir_a, self.salir_app))

    def _tras_respuesta(self, resultado: ResultadoRespuesta) -> None:
        p = self._pregunta_actual()
        puntos_prev = self.estado.puntos_arcade
        turno = procesar_turno_resistencia(
            self.estado,
            self.er,
            p,
            resultado,
            indice_pregunta=self._numero_pregunta(),
        )
        self._ajustar_multiplicador(resultado, puntos_prev)
        self.reintentar_pregunta = turno.reintentar_pregunta
        if turno.recompensa:
            self.recompensa_pendiente = turno.recompensa.etiqueta
        if not turno.reintentar_pregunta:
            self._registrar_respuesta(p, resultado)

        feedback = turno.feedback
        mensaje = feedback.mensaje

        if feedback.sin_vidas or not self.estado.debe_continuar(None):
            self.feedback_mensaje = mensaje
            self.feedback_solucion = solucion_feedback_grafico(feedback.solucion)
            self.feedback_ok = False
            self.fase = "feedback"
            self.inicio_feedback = marcar_inicio_feedback()
            self.botones_powerup = []
            for boton in self.botones_opcion:
                boton.activo = False
                if boton.letra == p.correcta:
                    boton.marcar_correcta = True
                elif boton.letra == resultado.respuesta and not resultado.acierto:
                    boton.marcar_incorrecta = True
            return

        self.feedback_mensaje = mensaje
        self.feedback_solucion = solucion_feedback_grafico(feedback.solucion)
        self.feedback_ok = resultado.acierto and not resultado.tiempo_agotado
        self.fase = "feedback"
        self.inicio_feedback = marcar_inicio_feedback()
        self.botones_powerup = []
        for boton in self.botones_opcion:
            boton.activo = False
            if boton.letra == p.correcta:
                boton.marcar_correcta = True
            elif boton.letra == resultado.respuesta and not resultado.acierto:
                boton.marcar_incorrecta = True

    def _responder(self, letra: str) -> None:
        if self.fase != "pregunta":
            return
        p = self._pregunta_actual()
        correcta = p.correcta if p.correcta in {"A", "B", "C", "D"} else ""
        acierto = letra == correcta and bool(correcta)
        self._tras_respuesta(ResultadoRespuesta(acierto=acierto, respuesta=letra))

    def _responder_timeout(self) -> None:
        if self.fase != "pregunta":
            return
        self._tras_respuesta(
            ResultadoRespuesta(acierto=False, respuesta="", tiempo_agotado=True)
        )

    def _continuar(self) -> None:
        if self.fase != "feedback":
            return
        if not self.estado.debe_continuar(None):
            self._fin_partida()
            return
        if self.reintentar_pregunta:
            self.reintentar_pregunta = False
            self.recompensa_pendiente = ""
            self._iniciar_fase_pregunta()
            for boton in self.botones_opcion:
                boton.activo = True
                boton.marcar_correcta = False
                boton.marcar_incorrecta = False
            return
        recompensa = self.recompensa_pendiente or None
        self.indice_global += 1
        if not self._cargar_siguiente_pregunta():
            self._fin_partida()
            return
        self.feedback_mensaje = ""
        self.feedback_solucion = None
        self.feedback_ok = False
        self._entrar_pregunta_o_avisos(recompensa_etiqueta=recompensa)

    def actualizar(self) -> Pantalla | None:
        if self.fase == "aviso":
            if aviso_debe_avanzar(self.inicio_aviso):
                self.indice_aviso += 1
                if self.indice_aviso < len(self.avisos_cola):
                    self.inicio_aviso = marcar_inicio_aviso()
                else:
                    self._iniciar_fase_pregunta()
            return None
        if self.fase == "feedback":
            if feedback_debe_avanzar(
                self.inicio_feedback,
                solucion=self.feedback_solucion,
                acierto=self.feedback_ok,
            ):
                self._continuar()
            return None
        if self.fase != "pregunta":
            return None
        lim = self._limite_tiempo_pregunta()
        if lim and _segundos_pregunta_restantes(self.inicio_pregunta, lim) == 0:
            self._responder_timeout()
        return None

    def titulo_pausa(self) -> str:
        return f"{self.preset.nombre} · {self._linea_estado_actual()}"

    def _dibujar_barra_superior(self, superficie: pygame.Surface) -> None:
        fuente = self.fuentes["pequena"]
        lbl_abandonar = etiqueta(*BTN_ABANDONAR)
        self.boton_abandonar.rect = rect_boton_etiqueta(
            lbl_abandonar,
            fuente,
            x_derecha=ANCHO - MARGEN,
            y=14,
        )
        x_centro_min = MARGEN_ICONOS_FIJOS + 8
        x_centro_max = self.boton_abandonar.rect.x - 12
        ancho_centro = max(80, x_centro_max - x_centro_min)
        seg_preg = None
        if self.fase == "pregunta":
            seg_preg = _segundos_pregunta_restantes(
                self.inicio_pregunta,
                self._limite_tiempo_pregunta(),
            )
        dibujar_estado_partida_en_barra(
            superficie,
            estado=self.estado,
            progreso=self._texto_progreso(),
            fuentes=self.fuentes,
            x_centro_min=x_centro_min,
            x_centro_max=x_centro_max,
            segundos_pregunta_restantes=seg_preg,
            vidas_max=self.er.vidas_max,
        )
        if self.efecto_actual and self.fase == "pregunta":
            fx = fuente.render(preparar_texto_ui(self.efecto_actual[:80]), True, COLOR_AVISO)
            if fx.get_width() <= ancho_centro:
                superficie.blit(fx, fx.get_rect(midtop=(ANCHO // 2, 36)))
        pygame.draw.line(
            superficie,
            (50, 72, 110),
            (MARGEN, ALTURA_BARRA_PARTIDA),
            (ANCHO - MARGEN, ALTURA_BARRA_PARTIDA),
            1,
        )
        self.boton_abandonar.dibujar(superficie, fuente)

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEMOTION:
            self.boton_abandonar.actualizar_hover(evento.pos)
            if self.fase == "pregunta":
                for boton in self.botones_powerup:
                    boton.actualizar_hover(evento.pos)
                for boton in self.botones_opcion:
                    boton.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if self.boton_abandonar.manejar_clic(evento.pos, evento.button):
                return None
            if self.fase == "pregunta":
                for boton in self.botones_powerup:
                    if boton.manejar_clic(evento.pos, evento.button):
                        return None
                for boton in self.botones_opcion:
                    if boton.manejar_clic(evento.pos, evento.button):
                        break
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        self._dibujar_barra_superior(superficie)
        if self.fase == "aviso" and self.avisos_cola:
            dibujar_aviso_resistencia(
                superficie,
                self.fuentes,
                mensaje=self.avisos_cola[self.indice_aviso],
                indice=self.indice_aviso,
                total=len(self.avisos_cola),
            )
            return
        p = self._pregunta_actual()
        panel = pygame.Rect(MARGEN, Y_PANEL_PREGUNTA, ANCHO - 2 * MARGEN, ALTO_PANEL_PREGUNTA)
        dibujar_panel(superficie, panel)
        meta_partes: list[str] = []
        if p.exclusiva_resistencia:
            tier = etiqueta_tier_exclusiva(p)
            if tier:
                meta_partes.append(f"★ {tier}")
        if self.er.escudo_activo:
            meta_partes.append("Escudo activo")
        meta_partes.append(
            f"{p.materia} · {p.tipo} / {p.dificultad} · Nivel {self.escalada.nivel}"
        )
        meta = self.fuentes["pequena"].render(
            " · ".join(meta_partes),
            True,
            COLOR_AVISO if p.exclusiva_resistencia else COLOR_ACENTO,
        )
        superficie.blit(meta, (panel.x + 12, panel.y + 10))
        dibujar_texto_multilinea(
            superficie,
            self.fuentes["cuerpo"],
            self._texto_pregunta_visible(),
            pygame.Rect(panel.x + 8, panel.y + 36, panel.width - 16, panel.height - 44),
            COLOR_TITULO,
        )
        for boton in self.botones_opcion:
            boton.dibujar(superficie, self.fuentes["opcion"])
        if self.fase == "pregunta":
            for boton in self.botones_powerup:
                boton.dibujar(superficie, self.fuentes["pequena"])
        if self.fase == "feedback":
            dibujar_feedback_partida(
                superficie,
                self.fuentes,
                mensaje=self.feedback_mensaje,
                solucion=self.feedback_solucion,
                acierto=self.feedback_ok,
                y_mensaje=self._y_fin_opciones() + 8,
            )
        tips: list[Boton] = [self.boton_abandonar]
        if self.fase == "pregunta":
            tips.extend(self.botones_powerup)
        dibujar_tooltips_botones(superficie, self.fuentes["pequena"], tips)


class RankingResistenciaHistoria(Pantalla):
    """Tabla histórica del modo resistencia (ranking local / multijugador offline)."""

    def __init__(
        self,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
        *,
        volver_a: Callable[[], None] | None = None,
    ) -> None:
        self.datos = datos
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.volver_a = volver_a or (
            lambda: self.ir_a(MenuPrincipal(datos, ir_a, salir_app))
        )
        self.fuentes = crear_fuentes()
        self.records = top_records(resolver_ranking_resistencia(), limite=25)
        self.boton_volver = Boton(
            etiqueta(*BTN_VOLVER),
            rect_boton_etiqueta(
                etiqueta(*BTN_VOLVER),
                self.fuentes["menu"],
                x_centro=ANCHO // 2,
                y=0,
                alto_min=48,
            ),
            self.volver_a,
        )
        posicionar_pila_inferior(
            [self.boton_volver],
            x_centro=ANCHO // 2,
            gap=0,
            margen_inferior=70,
        )

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEMOTION:
            self.boton_volver.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            self.boton_volver.manejar_clic(evento.pos, evento.button)
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        titulo = self.fuentes["titulo"].render(
            titulo_pantalla("Ranking — resistencia"), True, COLOR_TITULO
        )
        superficie.blit(titulo, titulo.get_rect(midtop=(ANCHO // 2, 36)))
        subt = self.fuentes["pequena"].render(
            "Multijugador local: récords guardados en este equipo",
            True,
            COLOR_TEXTO_PANEL,
        )
        superficie.blit(subt, subt.get_rect(midtop=(ANCHO // 2, 72)))

        y = 110
        fuente = self.fuentes["pequena"]
        if not self.records:
            vacio = fuente.render(
                etiqueta_campo("sin_registros", "Aún no hay partidas registradas."), True, COLOR_TEXTO
            )
            superficie.blit(vacio, vacio.get_rect(midtop=(ANCHO // 2, y + 40)))
        else:
            cab = fuente.render("#   Jugador          Preg.   Puntos", True, COLOR_ACENTO)
            superficie.blit(cab, (MARGEN + 20, y))
            y += 28
            for i, rec in enumerate(self.records, start=1):
                nombre = rec.nombre[:14].ljust(14)
                linea = f"{i:2}. {nombre}  {rec.respondidas:5}   {rec.puntos:6}"
                txt = fuente.render(linea, True, COLOR_TEXTO)
                superficie.blit(txt, (MARGEN + 20, y))
                y += 22
                if y > ALTO - 120:
                    mas = fuente.render("…", True, COLOR_TEXTO_PANEL)
                    superficie.blit(mas, (MARGEN + 20, y))
                    break

        self.boton_volver.dibujar(superficie, self.fuentes["menu"])

    def titulo_pausa(self) -> str:
        return "Ranking — resistencia"


class ResumenHistoriaPartida(ResumenPartida):
    def __init__(
        self,
        estado: EstadoPartida,
        total_previsto: int,
        preset: PresetHistoria,
        ir_a: Callable[[Pantalla], None],
        datos: DatosJuego,
        salir_app: Callable[[], None],
        *,
        cierre_informe: CierreInformePartida | None = None,
        titulo: str | None = None,
    ) -> None:
        self.preset = preset
        titulo_resumen = titulo or f"FIN — {preset.nombre[:44]}"
        super().__init__(
            estado,
            total_previsto,
            ir_a,
            datos,
            salir_app,
            cierre_informe=cierre_informe,
            titulo=titulo_resumen,
        )

    def _construir_lineas(self) -> list[str]:
        abandonado = bool(self.cierre_informe and self.cierre_informe.abandonado)
        mostrar_aciertos = self.estado.reglas.correccion_al_final
        return lineas_resumen_breve(
            self.estado,
            self.total_previsto,
            mostrar_aciertos=mostrar_aciertos,
            abandonado=abandonado,
        )


class ResumenResistenciaHistoria(ResumenHistoriaPartida):
    def __init__(
        self,
        estado: EstadoPartida,
        preset: PresetHistoria,
        ir_a: Callable[[Pantalla], None],
        datos: DatosJuego,
        salir_app: Callable[[], None],
        *,
        cierre_informe: CierreInformePartida | None = None,
        titulo: str | None = None,
        posicion_ranking: int | None = None,
        abandonado: bool = False,
        mejor_racha: int | None = None,
    ) -> None:
        self.posicion_ranking = posicion_ranking
        self.abandonado_resistencia = abandonado
        self.mejor_racha = mejor_racha if mejor_racha is not None else estado.aciertos
        super().__init__(
            estado,
            estado.respondidas,
            preset,
            ir_a,
            datos,
            salir_app,
            cierre_informe=cierre_informe,
            titulo=titulo,
        )
        fuente_menu = self.fuentes["menu"]
        etiq_ranking = etiqueta(*BTN_VER_RANKING)
        ancho_btns, alto_btns = tamano_grupo_botones(
            [self.boton_menu.etiqueta, etiq_ranking],
            fuente_menu,
            alto_min=44,
        )
        self.boton_menu.rect = rect_boton_etiqueta(
            self.boton_menu.etiqueta,
            fuente_menu,
            x_centro=ANCHO // 2,
            y=0,
            ancho=ancho_btns,
            alto=alto_btns,
        )
        self.boton_ranking = Boton(
            etiq_ranking,
            rect_boton_etiqueta(
                etiq_ranking,
                fuente_menu,
                x_centro=ANCHO // 2,
                y=0,
                ancho=ancho_btns,
                alto=alto_btns,
            ),
            self._ver_ranking,
        )
        posicionar_pila_inferior(
            [self.boton_ranking, self.boton_menu],
            x_centro=ANCHO // 2,
            gap=14,
            margen_inferior=20,
        )

    def _ver_ranking(self) -> None:
        self.ir_a(
            RankingResistenciaHistoria(
                self.datos,
                self.ir_a,
                self.salir_app,
                volver_a=lambda: self.ir_a(MenuPrincipal(self.datos, self.ir_a, self.salir_app)),
            )
        )

    def _construir_lineas(self) -> list[str]:
        lineas = super()._construir_lineas()
        lineas.insert(0, f"Preguntas respondidas: {self.estado.respondidas}")
        lineas.insert(1, f"Mejor racha (bonificación puntos): {self.mejor_racha}")
        if self.posicion_ranking is not None:
            lineas.insert(2, f"Posición en ranking: #{self.posicion_ranking}")
        mejor = mejor_de_jugador(resolver_ranking_resistencia(), self.estado.nombre)
        if mejor and mejor.respondidas > self.estado.respondidas:
            lineas.append(
                f"Tu récord personal: pregunta {mejor.respondidas} (puntos {mejor.puntos})"
            )
        return lineas

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEMOTION:
            self.boton_ranking.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            self.boton_ranking.manejar_clic(evento.pos, evento.button)
        return super().manejar_evento(evento)

    def dibujar(self, superficie: pygame.Surface) -> None:
        super().dibujar(superficie)
        if not self.abandonado_resistencia:
            self.boton_ranking.dibujar(superficie, self.fuentes["menu"])
