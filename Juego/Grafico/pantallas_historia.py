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
    evaluar_respuesta,
    linea_estado,
)
from Comun.motor_resistencia_comun import (
    aplicar_bonificaciones_puntos_resistencia,
    aplicar_modificadores_visuales_escalada,
    avisos_pre_pregunta_resistencia,
    configurar_partida_resistencia,
    consumir_bloque_filtro,
    crear_estado_resistencia,
    elegir_indice_similar,
    formatear_aviso_apuesta,
    preparar_eventos_nuevo_turno,
    procesar_turno_resistencia,
    texto_pregunta_para_turno,
    texto_progreso_resistencia,
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
from Comun.preferencias_grafico import nombre_jugador_grafico
from Comun.reglas_partida import ReglasPartida, formatear_resultado_puntuacion
from Comun.cierre_informe import CierreInformePartida, meta_cierre_historia
from Comun.ranking_resistencia import (
    VARIANTES_RANKING,
    etiqueta_variante_ranking,
    mejor_de_jugador,
    path_ranking_para_preset,
    path_ranking_para_variante,
    registrar_partida,
    top_records,
    variante_desde_preset,
)
from Comun.resistencia_historia import (
    aplicar_escalada_a_reglas,
    crear_seleccion_resistencia,
    elegir_indice_resistencia,
    escalada_para_pregunta,
    etiqueta_tier_exclusiva,
    texto_efectos_escalada,
)
from Comun.reto_dia_resistencia import etiqueta_fecha_reto_dia
from Grafico.textos_grafico import (
    BTN_ABANDONAR,
    BTN_APUESTA_NO,
    BTN_APUESTA_SI,
    BTN_ATRAS,
    BTN_CONTINUAR,
    BTN_EMPEZAR,
    BTN_VOLVER,
    BTN_VOLVER_MENU,
    emoji_icono,
    etiqueta,
    etiqueta_campo,
    subtitulo,
    titulo_pantalla,
)
from Grafico.informe_partida import lineas_resumen_breve
from Grafico.aviso_resistencia import (
    aviso_debe_avanzar,
    dibujar_contenido_aviso_resistencia,
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
    construir_navegacion_fin_partida_historia,
    iniciar_pantalla_partida_historia,
    preparar_partida_historia,
)
from Grafico.pantallas import (
    ALTURA_BARRA_PARTIDA,
    ALTO_BOTON_CONTINUAR_PARTIDA,
    ALTO_BARRA_PROGRESO_PARTIDA,
    ALTO_OPCION_PARTIDA,
    ALTO_PANEL_PREGUNTA,
    GAP_TRAS_BARRA_PROGRESO,
    GAP_TRAS_PANEL_PARTIDA,
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
    TOOLTIP_APUESTA_NO,
    TOOLTIP_APUESTA_SI,
    TOOLTIP_ATRAS,
    TOOLTIP_CONTINUAR,
    TOOLTIP_EMPEZAR,
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
    COLOR_PANEL,
    COLOR_TEXTO,
    COLOR_TITULO,
    MARGEN,
    Y_INICIO_TITULO,
    crear_fuentes,
    x_min_centro_barra_partida,
)
from Grafico.ui import (
    Boton,
    BotonOpcion,
    _fuente_ajustada,
    capturar,
    dibujar_caja_valor_ciclo,
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
from Grafico.texto import dibujar_texto_centro, preparar_texto_ui, texto_requiere_fuentes_mixtas

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
        self.fuentes = crear_fuentes()
        self.mensaje = ""
        self.presets = cargar_catalogo_historia()
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

        navegacion = construir_navegacion_fin_partida_historia(
            self.datos,
            preset,
            config,
            nombre,
            self.ir_a,
            self.salir_app,
            _pantalla_configuracion,
        )
        try:
            pantalla = iniciar_pantalla_partida_historia(
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

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
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
            "Los primeros modos usan qualificacions históricas del grado",
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
                Boton("◀", rect_izq, capturar(self._ciclar_opcion, op.id, -1)),
                Boton("▶", rect_der, capturar(self._ciclar_opcion, op.id, 1)),
            )
        self._reposicionar_botones_navegacion()

    def _items_opcion_curso(self, op: OpcionPreset) -> list[tuple[str, str]]:
        items = [(c, f"Curso {c}") for c in cursos_disponibles(self.datos.materias_meta)]
        if not op.obligatorio:
            return [("", "Todo el grado")] + items
        return items

    def _items_opcion_semestre(self, op: OpcionPreset) -> list[tuple[str, str]]:
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

    def _items_opcion(self, op_id: str) -> list[tuple[str, str]]:
        op = self._opcion_preset(op_id)
        if op is None:
            return []
        if op.tipo == "curso":
            return self._items_opcion_curso(op)
        if op.tipo == "semestre":
            return self._items_opcion_semestre(op)
        if op.tipo == "grupo":
            return list(GRUPOS_TEMATICOS.items())
        if op.tipo == "materia":
            return [(m, m) for m in self.orden_materias]
        if op.tipo == "eleccion":
            return list(op.valores)
        return []

    def _texto_valor_vacio(self, op: OpcionPreset) -> str:
        if op.tipo == "curso" and not op.obligatorio:
            return "Todo el grado"
        if op.tipo == "semestre" and not op.obligatorio:
            return "Todo el curso"
        return "—"

    def _texto_valor_con_dato(self, op: OpcionPreset, raw: object) -> str:
        if op.tipo == "grupo":
            return GRUPOS_TEMATICOS.get(str(raw), str(raw))
        if op.tipo == "eleccion":
            for v, etq in op.valores:
                if v == str(raw):
                    return etq
            return str(raw)
        if op.tipo == "curso":
            return f"Curso {raw}"
        if op.tipo == "semestre":
            return f"Semestre {raw}"
        if op.tipo == "entero":
            if op.id == "tiempo_total_min" and int(str(raw)) == 0:
                return "Sin límite"
            return str(raw)
        return str(raw)

    def _texto_valor(self, op_id: str) -> str:
        op = self._opcion_preset(op_id)
        if op is None:
            return ""
        raw = self.config.valores.get(op_id)
        if raw is None or raw == "":
            return self._texto_valor_vacio(op)
        return self._texto_valor_con_dato(op, raw)

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

        def _pantalla_configuracion() -> Pantalla:
            return ConfigOpcionesHistoria(
                self.datos,
                self.preset,
                self.nombre,
                self.ir_a,
                self.salir_app,
                self.volver,
                config_inicial=config,
            )

        navegacion = construir_navegacion_fin_partida_historia(
            self.datos,
            self.preset,
            config,
            self.nombre,
            self.ir_a,
            self.salir_app,
            _pantalla_configuracion,
        )
        try:
            pantalla = iniciar_pantalla_partida_historia(
                self.datos,
                self.preset,
                config,
                self.nombre,
                self.ir_a,
                self.salir_app,
                navegacion_fin=navegacion,
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
        lbl = self.fuentes["menu"].render(etiqueta + ":", True, COLOR_ETIQUETA_PANEL_CLARO)
        superficie.blit(lbl, (self.X_ETIQUETA, y + 16))

        if op.id not in self.botones_ciclo:
            return

        izq, der = self.botones_ciclo[op.id]
        val_rect = self._rect_valor_ciclo(op.id)
        if val_rect and val_rect.width > 0:
            dibujar_caja_valor_ciclo(
                superficie,
                val_rect,
                self._texto_valor(op.id),
                self.fuentes["cuerpo"],
            )

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
        config_historia: ConfigPresetHistoria | None = None,
        navegacion_fin=None,
    ) -> None:
        from Comun.navegacion_fin_partida import NavegacionFinPartida

        self.nombre = nombre
        self.preset = preset
        self.config_historia = config_historia or ConfigPresetHistoria()
        self.navegacion_fin: NavegacionFinPartida | None = navegacion_fin
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
                capturar(self._responder, letra),
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
                navegacion_fin=self.navegacion_fin,
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
        x_centro_min = x_min_centro_barra_partida(self.fuentes["menu"])
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

    def _actualizar_hover_partida(self, pos: tuple[int, int]) -> None:
        self.boton_abandonar.actualizar_hover(pos)
        if self.fase != "pregunta":
            return
        for boton in self.botones_opcion:
            boton.actualizar_hover(pos)

    def _manejar_clic_partida(self, pos: tuple[int, int], boton: int) -> bool:
        if self.boton_abandonar.manejar_clic(pos, boton):
            return True
        if self.fase != "pregunta":
            return False
        return any(b.manejar_clic(pos, boton) for b in self.botones_opcion)

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEMOTION:
            self._actualizar_hover_partida(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if self._manejar_clic_partida(evento.pos, evento.button):
                return None
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
        banco,
        reglas: ReglasPartida,
        ir_a: Callable[[Pantalla], None],
        datos: DatosJuego,
        salir_app: Callable[[], None],
        navegacion_fin=None,
    ) -> None:
        from Comun.navegacion_fin_partida import NavegacionFinPartida

        self.nombre = nombre
        self.preset = preset
        self.navegacion_fin: NavegacionFinPartida | None = navegacion_fin
        self.pool = pool
        self.ir_a = ir_a
        self.datos = datos
        self.salir_app = salir_app
        self.fuentes = crear_fuentes()
        self.registros: list = []
        self.reglas_base = reglas
        self.er = crear_estado_resistencia(reglas.vidas or 3)
        self.er.banco_resistencia = banco
        configurar_partida_resistencia(self.er, preset_id=self.preset.id)
        self.escalada = escalada_para_pregunta(1, semilla_partida=self.er.semilla_partida)
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
        self.efecto_actual = ""
        self.avisos_cola: list[str] = []
        self.avisos_pendientes: list[str] = []
        self.indice_aviso = 0
        self.inicio_aviso = 0.0
        self.boton_apuesta_si: Boton | None = None
        self.boton_apuesta_no: Boton | None = None
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
        if not self._cargar_siguiente_pregunta():
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

    def _entrar_pregunta_o_avisos(self) -> None:
        if self.er.apuesta_oferta:
            self.fase = "apuesta"
            self._reconstruir_botones_apuesta()
            self.botones_opcion = []
            self.botones_powerup = []
            return
        p = self._pregunta_actual()
        avisos_extra = list(self.avisos_pendientes)
        self.avisos_pendientes = []
        avisos = avisos_pre_pregunta_resistencia(
            p,
            self._numero_pregunta(),
            avisos_extra=avisos_extra,
            er=self.er,
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

    def _reconstruir_botones_apuesta(self) -> None:
        lbl_si = etiqueta(*BTN_APUESTA_SI)
        lbl_no = etiqueta(*BTN_APUESTA_NO)
        tam = 56
        gap = 20
        y = ALTO // 2 + 122
        cx = ANCHO // 2
        self.boton_apuesta_si = Boton(
            lbl_si,
            pygame.Rect(cx - tam - gap // 2, y, tam, tam),
            self._aceptar_apuesta,
            tooltip=TOOLTIP_APUESTA_SI,
            familia_etiqueta="emoji",
        )
        self.boton_apuesta_no = Boton(
            lbl_no,
            pygame.Rect(cx + gap // 2, y, tam, tam),
            self._rechazar_apuesta,
            tooltip=TOOLTIP_APUESTA_NO,
            familia_etiqueta="emoji",
        )

    def _aceptar_apuesta(self) -> None:
        if self.er.apuesta_oferta:
            self.er.apuesta_activa = self.er.apuesta_oferta
            self.er.apuesta_oferta = None
        self._entrar_pregunta_o_avisos()

    def _rechazar_apuesta(self) -> None:
        self.er.apuesta_oferta = None
        self._entrar_pregunta_o_avisos()

    def _limite_tiempo_pregunta(self) -> int | None:
        return tiempo_pregunta_efectivo(
            self.estado.reglas.tiempo_por_pregunta_seg,
            self.er,
        )

    def _numero_pregunta(self) -> int:
        return self.indice_global + 1

    def _aplicar_escalada(self, numero_pregunta: int) -> None:
        self.escalada = escalada_para_pregunta(
            numero_pregunta, semilla_partida=self.er.semilla_partida, racha=self.er.racha
        )
        self.estado.reglas = aplicar_escalada_a_reglas(self.reglas_base, self.escalada)
        self.efecto_actual = texto_efectos_escalada(self.escalada)

    def _cargar_siguiente_pregunta(self) -> bool:
        self.er.reset_pregunta()
        numero = self._numero_pregunta()
        self._aplicar_escalada(numero)
        avisos_turno = preparar_eventos_nuevo_turno(self.er, self.pool, numero)
        self.avisos_pendientes.extend(avisos_turno)
        idx = elegir_indice_resistencia(
            self.pool, self.seleccion_pool, self.escalada, numero, er=self.er
        )
        if idx is None:
            return False
        consumir_bloque_filtro(self.er)
        self.pregunta_idx = idx
        return True

    def _pregunta_actual(self) -> Pregunta:
        if self.pregunta_idx is None:
            raise IndexError("Sin pregunta cargada.")
        return self.pool[self.pregunta_idx]

    def _texto_progreso(self) -> str:
        return texto_progreso_resistencia(self.er, self._numero_pregunta())

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

    def _offset_y_panel(self) -> int:
        if not self._texto_extra_layout():
            return 0
        return self.fuentes["pequena"].get_height() + 22

    def _y_panel_pregunta(self) -> int:
        return Y_PANEL_PREGUNTA + self._offset_y_panel()

    def _y_inicio_opciones(self) -> int:
        return self._y_panel_pregunta() + ALTO_PANEL_PREGUNTA + GAP_TRAS_PANEL_PARTIDA + 8

    def _y_fin_opciones(self) -> int:
        if self.botones_opcion:
            return max(boton.rect.bottom for boton in self.botones_opcion)
        n = 4
        return (
            self._y_inicio_opciones()
            + n * ALTO_OPCION_PARTIDA
            + max(0, n - 1) * SEP_OPCIONES_PARTIDA
        )

    def _y_mensaje_feedback(self) -> int:
        gap = 12
        y = self._y_fin_opciones() + gap
        limite = self._y_banda_powerups() - 6
        alto_est = self.fuentes["subtitulo"].get_height() + 8
        if y + alto_est > limite:
            y = max(self._y_fin_opciones() + 4, limite - alto_est)
        return y

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
        if self.fase != "pregunta" or self.er.objetos_bloqueados:
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
                    capturar(self._usar_powerup, pid),
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
                capturar(self._responder, letra),
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
            self.er.registrar_fallo()
            self.indice_global += 1
            if not self._cargar_siguiente_pregunta():
                self._fin_partida()
                return
            self.feedback_mensaje = ""
            self.feedback_solucion = None
            self._entrar_pregunta_o_avisos()
            return
        if powerup_id == "cambio":
            if self.pregunta_idx is None:
                return
            nuevo = elegir_indice_similar(
                self.pool,
                self.seleccion_pool,
                self.escalada,
                self._numero_pregunta(),
                self.pregunta_idx,
                er=self.er,
            )
            if nuevo is None:
                self.er.agregar_powerup("cambio", 1)
                self.feedback_mensaje = "No hay otra pregunta parecida disponible."
                self.feedback_solucion = None
                self.feedback_ok = False
                self.fase = "feedback"
                self.inicio_feedback = marcar_inicio_feedback()
                return
            self.pregunta_idx = nuevo
            aplicar_modificadores_visuales_escalada(
                self.er, self.escalada, self._pregunta_actual(), self._numero_pregunta()
            )
            self._reconstruir_opciones()
            self._reconstruir_powerups()
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

    def _ajustar_multiplicador(self, resultado: ResultadoRespuesta, puntos_prev: int, mult_apuesta: int) -> None:
        aplicar_bonificaciones_puntos_resistencia(
            self.estado,
            puntos_prev=puntos_prev,
            racha=self.er.racha,
            mult_escalada=self.escalada.multiplicador_puntos,
            exclusiva=self._pregunta_actual().exclusiva_resistencia,
            acierto=resultado.acierto,
            tiempo_agotado=resultado.tiempo_agotado,
            mult_apuesta=mult_apuesta,
        )

    def _fin_partida(self, *, abandonado: bool = False) -> None:
        from Consola.generador_examen_historia import cargar_estadisticas_historicas

        posicion_ranking: int | None = None
        if self.registros and not abandonado:
            try:
                _, posicion_ranking = registrar_partida(
                    path_ranking_para_preset(self.preset.id),
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
                navegacion_fin=self.navegacion_fin,
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
        self._ajustar_multiplicador(resultado, puntos_prev, turno.mult_apuesta)
        self.reintentar_pregunta = turno.reintentar_pregunta
        if turno.avisos_extra:
            self.avisos_pendientes.extend(turno.avisos_extra)
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
            self._iniciar_fase_pregunta()
            for boton in self.botones_opcion:
                boton.activo = True
                boton.marcar_correcta = False
                boton.marcar_incorrecta = False
            return
        self.indice_global += 1
        if not self._cargar_siguiente_pregunta():
            self._fin_partida()
            return
        self.feedback_mensaje = ""
        self.feedback_solucion = None
        self.feedback_ok = False
        self._entrar_pregunta_o_avisos()

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

    def popup_bloqueante(self) -> bool:
        return self.fase in ("aviso", "apuesta")

    def dibujar_contenido_popup_bloqueante(self, superficie: pygame.Surface) -> None:
        fuente = self.fuentes["menu"]
        if self.fase == "apuesta" and self.er.apuesta_oferta:
            dibujar_contenido_aviso_resistencia(
                superficie,
                self.fuentes,
                mensaje=formatear_aviso_apuesta(self.er.apuesta_oferta),
                titulo="Apuesta",
                mostrar_pie_espera=False,
            )
            if self.boton_apuesta_si:
                self.boton_apuesta_si.dibujar(superficie, fuente)
            if self.boton_apuesta_no:
                self.boton_apuesta_no.dibujar(superficie, fuente)
            tips_apuesta = [
                b for b in (self.boton_apuesta_si, self.boton_apuesta_no) if b
            ]
            dibujar_tooltips_botones(superficie, self.fuentes["pequena"], tips_apuesta)
            return
        if self.fase == "aviso" and self.avisos_cola:
            dibujar_contenido_aviso_resistencia(
                superficie,
                self.fuentes,
                mensaje=self.avisos_cola[self.indice_aviso],
                indice=self.indice_aviso,
                total=len(self.avisos_cola),
            )

    def _texto_extra_layout(self) -> str:
        partes: list[str] = []
        if self.efecto_actual:
            partes.append(self.efecto_actual[:80])
        if self.er.bloque_filtro:
            partes.append(self.er.bloque_filtro.etiqueta[:72])
        return " · ".join(partes)

    def _texto_extra_barra(self) -> str:
        if self.fase != "pregunta":
            return ""
        return self._texto_extra_layout()

    def _dibujar_barra_superior(self, superficie: pygame.Surface) -> None:
        fuente = self.fuentes["pequena"]
        lbl_abandonar = etiqueta(*BTN_ABANDONAR)
        self.boton_abandonar.rect = rect_boton_etiqueta(
            lbl_abandonar,
            fuente,
            x_derecha=ANCHO - MARGEN,
            y=14,
        )
        x_centro_min = x_min_centro_barra_partida(self.fuentes["menu"])
        x_centro_max = self.boton_abandonar.rect.x - 12
        ancho_centro = max(80, x_centro_max - x_centro_min)
        altura_fuente = fuente.get_height()
        texto_extra = self._texto_extra_barra()
        y_estado = (ALTURA_BARRA_PARTIDA - altura_fuente) // 2
        seg_preg = None
        if self.fase == "pregunta":
            seg_preg = _segundos_pregunta_restantes(
                self.inicio_pregunta,
                self._limite_tiempo_pregunta(),
            )
        numero = self._numero_pregunta()
        dibujar_estado_partida_en_barra(
            superficie,
            estado=self.estado,
            progreso="",
            fuentes=self.fuentes,
            x_centro_min=x_centro_min,
            x_centro_max=x_centro_max,
            y=y_estado,
            segundos_pregunta_restantes=seg_preg,
            vidas_max=self.er.vidas_max,
            numero_pregunta=numero,
            racha=self.er.racha,
        )
        if texto_extra:
            extra_txt = preparar_texto_ui(texto_extra)
            if len(extra_txt) > 96:
                extra_txt = extra_txt[:93] + "…"
            extra = fuente.render(extra_txt, True, COLOR_AVISO)
            y_extra = ALTURA_BARRA_PARTIDA + 10
            if extra.get_width() <= ancho_centro:
                superficie.blit(extra, extra.get_rect(midtop=(ANCHO // 2, y_extra)))
            else:
                superficie.blit(extra, (x_centro_min, y_extra))
        pygame.draw.line(
            superficie,
            (50, 72, 110),
            (MARGEN, ALTURA_BARRA_PARTIDA),
            (ANCHO - MARGEN, ALTURA_BARRA_PARTIDA),
            1,
        )
        self.boton_abandonar.dibujar(superficie, fuente)

    def _actualizar_hover_resistencia(self, pos: tuple[int, int]) -> None:
        self.boton_abandonar.actualizar_hover(pos)
        if self.fase == "apuesta":
            if self.boton_apuesta_si:
                self.boton_apuesta_si.actualizar_hover(pos)
            if self.boton_apuesta_no:
                self.boton_apuesta_no.actualizar_hover(pos)
            return
        if self.fase != "pregunta":
            return
        for boton in self.botones_powerup:
            boton.actualizar_hover(pos)
        for boton in self.botones_opcion:
            boton.actualizar_hover(pos)

    def _manejar_clic_apuesta(self, pos: tuple[int, int], boton: int) -> bool:
        if self.boton_apuesta_si and self.boton_apuesta_si.manejar_clic(pos, boton):
            return True
        return bool(
            self.boton_apuesta_no and self.boton_apuesta_no.manejar_clic(pos, boton)
        )

    def _manejar_clic_pregunta_resistencia(self, pos: tuple[int, int], boton: int) -> bool:
        for btn in self.botones_powerup:
            if btn.manejar_clic(pos, boton):
                return True
        return any(b.manejar_clic(pos, boton) for b in self.botones_opcion)

    def _manejar_clic_resistencia(self, pos: tuple[int, int], boton: int) -> bool:
        if self.boton_abandonar.manejar_clic(pos, boton):
            return True
        if self.fase == "apuesta":
            return self._manejar_clic_apuesta(pos, boton)
        if self.fase == "pregunta":
            return self._manejar_clic_pregunta_resistencia(pos, boton)
        return False

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEMOTION:
            self._actualizar_hover_resistencia(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if self._manejar_clic_resistencia(evento.pos, evento.button):
                return None
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        self._dibujar_barra_superior(superficie)
        if self.popup_bloqueante():
            return
        p = self._pregunta_actual()
        panel = pygame.Rect(MARGEN, self._y_panel_pregunta(), ANCHO - 2 * MARGEN, ALTO_PANEL_PREGUNTA)
        dibujar_panel(superficie, panel)
        meta_partes: list[str] = []
        if p.exclusiva_resistencia:
            tier = etiqueta_tier_exclusiva(p)
            if tier:
                meta_partes.append(f"★ {tier}")
        if self.er.escudo_activo:
            meta_partes.append("Escudo activo")
        meta_partes.append(
            f"{p.materia} · {p.tipo} / {p.dificultad} · Nivel {self.escalada.nivel_visible}"
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
            for boton_pw in self.botones_powerup:
                boton_pw.dibujar(superficie, self.fuentes["pequena"])
        if self.fase == "feedback":
            dibujar_feedback_partida(
                superficie,
                self.fuentes,
                mensaje=self.feedback_mensaje,
                solucion=self.feedback_solucion,
                acierto=self.feedback_ok,
                y_mensaje=self._y_mensaje_feedback(),
            )
        tips: list[Boton] = [self.boton_abandonar]
        if self.fase == "pregunta":
            tips.extend(self.botones_powerup)
        dibujar_tooltips_botones(superficie, self.fuentes["pequena"], tips)


class RankingResistenciaHistoria(Pantalla):
    """Tablas locales de resistencia infinita y reto del día (lado a lado)."""

    Y_INFO = Y_INICIO_TITULO + 48
    ALTURA_LINEA_INFO = 22
    _LINEAS_INFO_BASE = (
        "Solo en este ordenador. En otro PC no verás estos récords.",
        "Orden: preguntas alcanzadas, luego puntos.",
    )
    Y_TABLAS = Y_INFO + (len(_LINEAS_INFO_BASE) + 1) * ALTURA_LINEA_INFO + 16
    LIMITE_FILAS = 12
    GAP_COLUMNAS = 16
    _COLOR_TABLA_FONDO = (18, 44, 86)
    _COLOR_TABLA_FILA_ALT = (24, 56, 104)
    _COLOR_TABLA_BORDE = (88, 148, 215)
    _COLOR_TABLA_BORDE_DESTACADO = (255, 196, 96)
    _COLOR_TABLA_CABECERA = (120, 175, 235)
    _COLOR_TEXTO_SECUNDARIO = (200, 215, 235)
    _TAM_TEXTO_INFO = 16
    _GAP_TITULO_SUB_RETO = 38
    _GAP_LINEA_RETO = 24

    @classmethod
    def _lineas_info(cls) -> tuple[str, ...]:
        icono_opciones = emoji_icono("opciones")
        return (
            *cls._LINEAS_INFO_BASE,
            f"Borrado local: Opciones ({icono_opciones}) en la barra superior.",
        )

    def _dibujar_linea_info(
        self,
        superficie: pygame.Surface,
        texto: str,
        y: int,
    ) -> None:
        tam = self._TAM_TEXTO_INFO
        color = self._COLOR_TEXTO_SECUNDARIO
        if texto_requiere_fuentes_mixtas(texto):
            dibujar_texto_centro(
                superficie,
                texto,
                (ANCHO // 2, y + tam // 2),
                tam,
                color,
            )
            return
        subt = self.fuentes["pequena"].render(texto, True, color)
        superficie.blit(subt, subt.get_rect(midtop=(ANCHO // 2, y)))

    def __init__(
        self,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
        *,
        volver_a: Callable[[], None] | None = None,
        preset_id_inicial: str | None = None,
    ) -> None:
        self.datos = datos
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.volver_a = volver_a or (
            lambda: self.ir_a(MenuPrincipal(datos, ir_a, salir_app))
        )
        self.fuentes = crear_fuentes()
        self.columna_destacada = (
            variante_desde_preset(preset_id_inicial)
            if preset_id_inicial
            else None
        )
        self.records_por_variante: dict[str, list] = {}
        self._layout_columnas = self._calcular_layout_columnas()
        self._recargar_tablas()
        self._crear_botones_inferiores()

    def _calcular_layout_columnas(self) -> dict[str, pygame.Rect]:
        ancho_col = (ANCHO - 2 * MARGEN - self.GAP_COLUMNAS) // 2
        alto_tabla = ALTO - self.Y_TABLAS - 88
        return {
            "infinita": pygame.Rect(MARGEN, self.Y_TABLAS, ancho_col, alto_tabla),
            "reto_dia": pygame.Rect(
                MARGEN + ancho_col + self.GAP_COLUMNAS,
                self.Y_TABLAS,
                ancho_col,
                alto_tabla,
            ),
        }

    def _crear_botones_inferiores(self) -> None:
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
        self.boton_volver.rect.midtop = (ANCHO // 2, ALTO - 64)

    def _recargar_tablas(self) -> None:
        for variante in VARIANTES_RANKING:
            path = path_ranking_para_variante(variante)
            self.records_por_variante[variante] = top_records(path, limite=25)

    def _botones_ui(self) -> list[Boton]:
        return [self.boton_volver]

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEMOTION:
            for boton in self._botones_ui():
                boton.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            for boton in self._botones_ui():
                if boton.manejar_clic(evento.pos, evento.button):
                    break
        return None

    def _dibujar_cabecera_columna(
        self,
        superficie: pygame.Surface,
        fuente_peq: pygame.font.Font,
        variante: str,
        rect_col: pygame.Rect,
    ) -> int:
        titulo = etiqueta_variante_ranking(variante)
        color_titulo = COLOR_TITULO
        if self.columna_destacada == variante:
            color_titulo = self._COLOR_TABLA_BORDE_DESTACADO
        txt_titulo = self.fuentes["subtitulo"].render(titulo, True, color_titulo)
        y = rect_col.y + 10
        superficie.blit(txt_titulo, txt_titulo.get_rect(midtop=(rect_col.centerx, y)))
        y += self._GAP_TITULO_SUB_RETO
        if variante == "reto_dia":
            fecha = fuente_peq.render(
                f"Hoy: {etiqueta_fecha_reto_dia()}",
                True,
                self._COLOR_TEXTO_SECUNDARIO,
            )
            superficie.blit(fecha, fecha.get_rect(midtop=(rect_col.centerx, y)))
            y += self._GAP_LINEA_RETO
            reinicio = fuente_peq.render(
                "Se reinicia mañana automáticamente.",
                True,
                self._COLOR_TEXTO_SECUNDARIO,
            )
            superficie.blit(reinicio, reinicio.get_rect(midtop=(rect_col.centerx, y)))
            y += self._GAP_LINEA_RETO
        return y + 10

    def _dibujar_tabla_columna(
        self,
        superficie: pygame.Surface,
        fuente: pygame.font.Font,
        variante: str,
        rect_col: pygame.Rect,
    ) -> None:
        destacada = self.columna_destacada == variante
        borde = self._COLOR_TABLA_BORDE_DESTACADO if destacada else self._COLOR_TABLA_BORDE
        dibujar_panel(superficie, rect_col, color=self._COLOR_TABLA_FONDO)
        pygame.draw.rect(
            superficie,
            borde,
            rect_col,
            width=2,
            border_radius=8,
        )
        y = self._dibujar_cabecera_columna(superficie, fuente, variante, rect_col)
        records = self.records_por_variante.get(variante, [])
        if not records:
            vacio = fuente.render(
                etiqueta_campo("sin_registros", "Aún no hay partidas."),
                True,
                COLOR_TEXTO,
            )
            superficie.blit(vacio, vacio.get_rect(midtop=(rect_col.centerx, y + 28)))
            return
        cab = fuente.render("#  Jugador       Preg.  Puntos", True, self._COLOR_TABLA_CABECERA)
        superficie.blit(cab, (rect_col.x + 12, y))
        y += 24
        for i, rec in enumerate(records[: self.LIMITE_FILAS], start=1):
            if i % 2 == 0:
                fila_rect = pygame.Rect(rect_col.x + 4, y - 2, rect_col.width - 8, 20)
                pygame.draw.rect(
                    superficie,
                    self._COLOR_TABLA_FILA_ALT,
                    fila_rect,
                    border_radius=4,
                )
            nombre = rec.nombre[:12].ljust(12)
            linea = f"{i:2} {nombre} {rec.respondidas:5} {rec.puntos:6}"
            txt = fuente.render(linea, True, COLOR_TITULO)
            superficie.blit(txt, (rect_col.x + 12, y))
            y += 20
        if len(records) > self.LIMITE_FILAS:
            mas = fuente.render("…", True, self._COLOR_TEXTO_SECUNDARIO)
            superficie.blit(mas, (rect_col.x + 12, y))

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        dibujar_texto_centro(
            superficie,
            titulo_pantalla("Ranking local"),
            (ANCHO // 2, Y_INICIO_TITULO),
            self.fuentes["titulo"].get_height(),
            COLOR_TITULO,
            bold=True,
        )

        fuente_peq = self.fuentes["pequena"]
        for i, texto in enumerate(self._lineas_info()):
            self._dibujar_linea_info(
                superficie,
                texto,
                self.Y_INFO + i * self.ALTURA_LINEA_INFO,
            )

        for variante in VARIANTES_RANKING:
            rect_col = self._layout_columnas[variante]
            self._dibujar_tabla_columna(superficie, fuente_peq, variante, rect_col)

        self.boton_volver.dibujar(superficie, self.fuentes["menu"])

    def titulo_pausa(self) -> str:
        return "Ranking local"


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
        navegacion_fin=None,
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
            navegacion_fin=navegacion_fin,
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
        navegacion_fin=None,
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
            navegacion_fin=navegacion_fin,
        )

    def _construir_lineas(self) -> list[str]:
        lineas = super()._construir_lineas()
        lineas.insert(0, f"Preguntas respondidas: {self.estado.respondidas}")
        lineas.insert(1, f"Mejor racha (bonificación puntos): {self.mejor_racha}")
        path_rank = path_ranking_para_preset(self.preset.id)
        etiqueta_tabla = etiqueta_variante_ranking(variante_desde_preset(self.preset.id))
        if self.posicion_ranking is not None:
            lineas.insert(2, f"Posición en ranking ({etiqueta_tabla}): #{self.posicion_ranking}")
        mejor = mejor_de_jugador(path_rank, self.estado.nombre)
        if mejor and mejor.respondidas > self.estado.respondidas:
            lineas.append(
                f"Tu récord personal: pregunta {mejor.respondidas} (puntos {mejor.puntos})"
            )
        return lineas
