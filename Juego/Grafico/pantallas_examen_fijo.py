#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pantallas de examen fijo y partida por preset (examen del día, semilla, etc.).

Usado por modos diarios (barra) y, en el paquete completo, por presets del carrusel historia.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

import pygame

from Comun.modelos import Pregunta
from Comun.motor_nucleo import (
    EstadoPartida,
    NavegacionFinPartida,
    ResultadoRespuesta,
    PresentacionOpcionesPregunta,
    evaluar_respuesta,
    linea_estado,
    marcar_botones_opciones_tras_respuesta,
    presentacion_opciones_pantalla,
    texto_opcion_visible_pantalla,
    texto_solucion,
)
from Comun.semillas import RngPartida, crear_rng_partida
from Comun.linea_estado_ui import texto_progreso_examen_cerrado
from Comun.resistencia_motor import (
    aplicar_bonificaciones_puntos_resistencia,
    aplicar_modificadores_visuales_escalada,
    configurar_partida_resistencia,
    consumir_bloque_filtro,
    crear_estado_resistencia,
    desafio_bloque_expirado,
    descripcion_powerup,
    emoji_powerup,
    etiqueta_powerup,
    finalizar_partida_por_desafio_bloque,
    prefijar_emoji,
    preparar_eventos_nuevo_turno,
    procesar_turno_resistencia,
    puede_usar_powerup_en_pregunta,
    revocar_powerup_usado,
    texto_segmento_desafio_bloque,
    tiempo_pregunta_efectivo,
    usar_powerup,
)
from Comun.eventos_partida import (
    aceptar_evento_si_no,
    formatear_aviso_evento_si_no,
    puede_aceptar_evento_si_no,
    titulo_popup_evento_si_no,
)
from Comun.resistencia_partida import (
    aplicar_escalada_a_reglas,
    avisos_pre_pregunta_resistencia,
    crear_seleccion_resistencia,
    elegir_indice_resistencia,
    elegir_indice_similar,
    escalada_para_pregunta,
    etiqueta_tier_exclusiva,
    eventos_aleatorios_para_pregunta,
    partes_texto_efectos_escalada,
    texto_efectos_escalada,
)
from Comun.config_historia import (
    GRUPOS_TEMATICOS,
    ConfigPresetHistoria,
    OpcionPreset,
    cursos_disponibles,
    etiqueta_curso_academico,
    etiqueta_periodo_academico,
    etiqueta_periodo_desde_clave,
    limites_n_materias,
    limites_n_preguntas,
    ajustar_n_preguntas_examen_asignatura,
    max_tiempo_total_min,
    paso_entero_opcion_historia,
    siguiente_entero_ciclo,
    aplicar_exclusion_al_cambiar_ambito,
    filtro_ambito_bloqueado,
    opciones_config_historia,
    periodos_academicos,
    semestres_disponibles,
    semestres_para_curso,
    validar_config,
)
from Comun.presets_historia import PresetHistoria, config_defecto, preset_permite_examen_dirigido
from Comun.preferencias_grafico import nombre_jugador_grafico
from Comun.reglas import ReglasPartida, formatear_resultado_puntuacion, vidas_iniciales_partida
from Comun.informe_examen import CierreInformePartida, meta_cierre_historia
from Grafico.atajos_teclado import manejar_teclado_partida
from Grafico.textos_grafico import (
    BTN_ABANDONAR,
    BTN_APUESTA_NO,
    BTN_APUESTA_SI,
    BTN_ATRAS,
    BTN_CAMBIAR_OPCIONES,
    BTN_CONTINUAR,
    BTN_EMPEZAR,
    BTN_EXAMEN_DIRIGIDO,
    BTN_REPETIR_PARTIDA,
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
from Grafico.barra_estado import DatosBarraEstadoPartida, dibujar_estado_partida_en_barra
from Grafico.arranque_partida import (
    construir_navegacion_fin_partida,
    iniciar_pantalla_partida,
)
from Grafico.pantallas import (
    ALTURA_BARRA_PARTIDA,
    ALTO_BOTON_CONTINUAR_PARTIDA,
    ALTO_BARRA_PROGRESO_PARTIDA,
    fraccion_barra_progreso_partida,
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
    rect_enunciado_panel_pregunta,
    _segundos_pregunta_restantes,
)
from Grafico.tooltips_ui import (
    TOOLTIP_ABANDONAR_HISTORIA,
    TOOLTIP_ABANDONAR_RESISTENCIA,
    TOOLTIP_EVENTO_SI_NO_NO,
    TOOLTIP_EVENTO_SI_NO_SI,
    TOOLTIP_EVENTO_SI_NO_SI_RIESGO,
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
    CampoEntero,
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
    unir_partes_cabientes,
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
GAP_PANEL_BTNS = 24
ALTO_ETIQUETA_MENU = 24


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
        from Grafico.modo_historia import orden_materias_juego

        self.datos = datos
        self.preset = preset
        self.nombre = nombre
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.volver = volver
        self.fuentes = crear_fuentes()
        self.mensaje = ""
        self.orden_materias = orden_materias_juego(datos)
        self.config = config_inicial or config_defecto(
            preset,
            materias_meta=datos.materias_meta,
            materias_orden=self.orden_materias,
            perfil=datos.perfil,
            path_plantillas=datos.path_plantillas_json,
        )
        self.botones_ciclo: dict[str, tuple[Boton, Boton]] = {}
        self.campos_entero: dict[str, CampoEntero] = {}
        self._y_opcion: dict[str, int] = {}
        self._filas_orden: list[str] = []
        self.scroll_filas = 0
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

    def _opciones_ui(self) -> tuple[OpcionPreset, ...]:
        return opciones_config_historia(self.preset, perfil=self.datos.perfil)

    def _opcion_preset(self, op_id: str) -> OpcionPreset | None:
        for op in self._opciones_ui():
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
                curso_actual=self.config.valores.get("curso"),
                perfil=self.datos.perfil,
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
            curso_actual=self.config.valores.get("curso"),
            perfil=self.datos.perfil,
        )
        if not tip:
            return
        _, rect_val, _ = self._rects_control_fila(op_id)
        dibujar_tooltip(superficie, self.fuentes["pequena"], rect_val, tip)

    def _opcion_campo_teclado(self, op: OpcionPreset) -> bool:
        return op.id == "semilla" and self.preset.id == "examen_fijo"

    def _rect_campo_teclado(self, op_id: str) -> pygame.Rect:
        fila_y = self._y_opcion[op_id]
        y = fila_y + 10
        return pygame.Rect(self.X_CONTROLES, y, self._ancho_zona_controles(), 36)

    def _sync_campo_semilla_desde_config(self) -> None:
        campo = self.campos_entero.get("semilla")
        op = self._opcion_preset("semilla")
        if campo is None or op is None:
            return
        habilitado = not self._filtro_ambito_bloqueado("semilla")
        campo.establecer_habilitado(habilitado)
        min_v = int(op.min) if op.min is not None else 1
        max_v = int(op.max) if op.max is not None else 2147483646
        campo.actualizar_limites(min_v, max_v)
        if not habilitado:
            return
        from Comun.modos_diarios import formatear_semilla_diaria, semilla_defecto_examen_fijo

        raw = self.config.valores.get("semilla")
        if raw is not None and raw != "":
            campo.texto = formatear_semilla_diaria(int(raw))
        elif not campo.activo and not campo.texto:
            campo.texto = formatear_semilla_diaria(semilla_defecto_examen_fijo())

    def _aplicar_campos_teclado_a_config(self) -> None:
        if "semilla" not in self.campos_entero:
            return
        if self._filtro_ambito_bloqueado("semilla"):
            self.config.valores.pop("semilla", None)
            return
        op = self._opcion_preset("semilla")
        if op is None:
            return
        from Comun.modos_diarios import semilla_defecto_examen_fijo

        min_v = int(op.min) if op.min is not None else 1
        max_v = int(op.max) if op.max is not None else 2147483646
        valor = self.campos_entero["semilla"].valor_entero(
            defecto=semilla_defecto_examen_fijo()
        )
        if valor is None:
            raise ValueError(f"Semilla numérica: valor entre {min_v} y {max_v}.")
        self.config.valores["semilla"] = valor

    def _asegurar_campo_semilla(self) -> None:
        op = self._opcion_preset("semilla")
        if op is None or not self._opcion_campo_teclado(op):
            return
        rect = self._rect_campo_teclado("semilla")
        min_v = int(op.min) if op.min is not None else 1
        max_v = int(op.max) if op.max is not None else 2147483646
        if "semilla" not in self.campos_entero:
            self.campos_entero["semilla"] = CampoEntero(
                rect,
                placeholder="Introduce semilla…",
                minimo=min_v,
                maximo=max_v,
            )
        else:
            self.campos_entero["semilla"].rect = rect
        self._sync_campo_semilla_desde_config()

    def _filas_orden_opciones(self) -> list[str]:
        return [op.id for op in self._opciones_ui()]

    def _max_filas_visibles(self) -> int:
        return 6

    def _volver(self) -> None:
        try:
            self._aplicar_campos_teclado_a_config()
        except ValueError:
            pass
        self.volver(self.config)

    def _y_preferida_botones_navegacion(self) -> int:
        y0 = self._rect_panel_opciones().bottom + GAP_PANEL_BTNS
        if len(self._filas_orden) > self._max_filas_visibles():
            y0 += 28
        return y0

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
        n_vis = min(len(self._filas_orden), self._max_filas_visibles())
        alto = n_vis * (self.ALTO_FILA + self.GAP_FILA) + 24
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
        self._filas_orden = self._filas_orden_opciones()
        max_scroll = max(0, len(self._filas_orden) - self._max_filas_visibles())
        self.scroll_filas = min(self.scroll_filas, max_scroll)
        visibles = self._filas_orden[
            self.scroll_filas : self.scroll_filas + self._max_filas_visibles()
        ]
        self._y_opcion.clear()
        y = self.Y_OPCIONES
        for op_id in visibles:
            self._y_opcion[op_id] = y
            y += self.ALTO_FILA + self.GAP_FILA
        self._y_fin_opciones = y

        self.botones_ciclo.clear()
        for op_id in visibles:
            op = self._opcion_preset(op_id)
            if op is None or self._opcion_campo_teclado(op):
                continue
            rect_izq, _, rect_der = self._rects_control_fila(op_id)
            self.botones_ciclo[op_id] = (
                Boton("◀", rect_izq, capturar(self._ciclar_opcion, op_id, -1)),
                Boton("▶", rect_der, capturar(self._ciclar_opcion, op_id, 1)),
            )
        if "semilla" in visibles:
            self._asegurar_campo_semilla()
        elif "semilla" in self.campos_entero:
            self.campos_entero["semilla"].activo = False
        self._reposicionar_botones_navegacion()

    def _filtro_ambito_bloqueado(self, op_id: str) -> bool:
        return filtro_ambito_bloqueado(
            op_id,
            self.config.valores,
            self._opciones_ui(),
            preset_id=self.preset.id,
        )

    def _items_opcion_curso(self, op: OpcionPreset) -> list[tuple[str, str]]:
        items = [
            (c, etiqueta_curso_academico(c))
            for c in cursos_disponibles(self.datos.materias_meta)
        ]
        if not op.obligatorio:
            return [("", "Todo el grado")] + items
        return items

    def _items_opcion_semestre(self, op: OpcionPreset) -> list[tuple[str, str]]:
        curso = self.config.valores.get("curso")
        if curso:
            items = [
                (s, etiqueta_periodo_academico(str(curso), s))
                for s in semestres_para_curso(self.datos.materias_meta, str(curso))
            ]
            if not op.obligatorio:
                return [("", "Todo el curso")] + items
            return items
        items = [(s, f"Semestre {s}") for s in semestres_disponibles(self.datos.materias_meta)]
        if not op.obligatorio:
            return [("", "Cualquier semestre")] + items
        return items

    def _items_opcion_periodo(self, op: OpcionPreset) -> list[tuple[str, str]]:
        items = [
            (clave, etiqueta_periodo_desde_clave(clave))
            for clave, _, _ in periodos_academicos(self.datos.materias_meta)
        ]
        if not op.obligatorio:
            return [("", "Sin especificar")] + items
        return items

    def _items_opcion(self, op_id: str) -> list[tuple[str, str]]:
        op = self._opcion_preset(op_id)
        if op is None:
            return []
        if op.tipo == "curso":
            return self._items_opcion_curso(op)
        if op.tipo == "semestre":
            return self._items_opcion_semestre(op)
        if op.tipo == "periodo":
            return self._items_opcion_periodo(op)
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
            if self.config.valores.get("curso"):
                return "Todo el curso"
            return "Cualquier semestre"
        if op.tipo == "periodo" and not op.obligatorio:
            return "Sin especificar"
        return "—"

    def _semestre_valido_en_config(self, semestre: str) -> bool:
        curso = self.config.valores.get("curso")
        if curso:
            return semestre in semestres_para_curso(self.datos.materias_meta, str(curso))
        return semestre in semestres_disponibles(self.datos.materias_meta)

    def _ajustar_semestre_al_curso(self) -> None:
        semestre = self.config.valores.get("semestre")
        if semestre and not self._semestre_valido_en_config(str(semestre)):
            self.config.valores.pop("semestre", None)

    def _texto_valor_entero(self, op: OpcionPreset, raw: object) -> str:
        if op.id == "tiempo_total_min" and int(str(raw)) == 0:
            return "Sin límite"
        if op.id == "semilla":
            from Comun.modos_diarios import formatear_semilla_diaria

            return formatear_semilla_diaria(int(str(raw)))
        return str(raw)

    def _texto_valor_con_dato(self, op: OpcionPreset, raw: object) -> str:
        if op.tipo == "grupo":
            return GRUPOS_TEMATICOS.get(str(raw), str(raw))
        if op.tipo == "eleccion":
            for v, etq in op.valores:
                if v == str(raw):
                    return etq
            return str(raw)
        if op.tipo == "curso":
            return etiqueta_curso_academico(str(raw))
        if op.tipo == "semestre":
            curso = self.config.valores.get("curso")
            if curso:
                return etiqueta_periodo_academico(str(curso), str(raw))
            return f"Semestre {raw}"
        if op.tipo == "periodo":
            return etiqueta_periodo_desde_clave(str(raw))
        if op.tipo == "entero":
            return self._texto_valor_entero(op, raw)
        return str(raw)

    def _texto_valor(self, op_id: str) -> str:
        if self._filtro_ambito_bloqueado(op_id):
            return "Bloqueado"
        op = self._opcion_preset(op_id)
        if op is None:
            return ""
        raw = self.config.valores.get(op_id)
        if raw is None or raw == "":
            return self._texto_valor_vacio(op)
        return self._texto_valor_con_dato(op, raw)

    def _ciclar_opcion(self, op_id: str, delta: int) -> None:
        for op in self._opciones_ui():
            if op.id != op_id:
                continue
            if op.tipo == "entero":
                self._ciclar_entero(op, delta)
            else:
                self._ciclar_lista(op_id, delta)
            return

    def _kwargs_exclusion_ambito(self) -> dict[str, object]:
        op_nm = self._opcion_preset("n_materias")
        n_max = op_nm.max if op_nm and op_nm.max is not None else 40
        return {
            "preset_id": self.preset.id,
            "materias_meta": self.datos.materias_meta,
            "n_materias_max": n_max,
        }

    def _limites_n_materias(self) -> tuple[int, int] | None:
        op = self._opcion_preset("n_materias")
        if op is None:
            return None
        return limites_n_materias(
            op,
            self.config.valores,
            materias_meta=self.datos.materias_meta,
            preset_id=self.preset.id,
        )

    def _plantillas_materia_config(self) -> list[dict]:
        materia = self.config.valores.get("materia")
        if not materia or not self.datos.perfil.tiene_plantillas:
            return []
        from Comun.datos import cargar_plantillas_materia

        return cargar_plantillas_materia(
            self.datos.path_plantillas_json,
            str(materia),
        )

    def _limites_n_preguntas(self) -> tuple[int, int] | None:
        op = self._opcion_preset("n_preguntas")
        if op is None:
            return None
        plantillas = self._plantillas_materia_config()
        return limites_n_preguntas(
            op,
            self.config.valores,
            plantillas_materia=plantillas or None,
        )

    def _max_entero_opcion(self, op: OpcionPreset) -> int:
        if op.id == "n_materias":
            limites = self._limites_n_materias()
            if limites is not None:
                return limites[1]
        if op.id == "n_preguntas":
            limites = self._limites_n_preguntas()
            if limites is not None:
                return limites[1]
        if op.id == "tiempo_total_min":
            return max_tiempo_total_min(
                op,
                self.config.valores,
                preset_id=self.preset.id,
            )
        return op.max if op.max is not None else 9999

    def _min_entero_opcion(self, op: OpcionPreset) -> int:
        if op.id == "n_materias":
            limites = self._limites_n_materias()
            if limites is not None:
                return limites[0]
        if op.id == "n_preguntas":
            limites = self._limites_n_preguntas()
            if limites is not None:
                return limites[0]
        return op.min if op.min is not None else 0

    def _ajustar_n_materias_al_ambito(self) -> None:
        op = self._opcion_preset("n_materias")
        if op is None:
            return
        limites = self._limites_n_materias()
        if limites is None:
            return
        min_v, max_v = limites
        if max_v <= 0:
            self.config.valores.pop("n_materias", None)
            return
        defecto = int(op.defecto if op.defecto is not None else min_v)
        actual = int(self.config.valores.get("n_materias", defecto))
        self.config.valores["n_materias"] = min(max(actual, min_v), max_v)

    def _ajustar_n_preguntas_al_ambito(self) -> None:
        op = self._opcion_preset("n_preguntas")
        if op is None:
            return
        plantillas = self._plantillas_materia_config()
        if not plantillas:
            return
        ajustar_n_preguntas_examen_asignatura(
            self.config.valores,
            self._opciones_ui(),
            plantillas,
        )

    def _ciclar_entero(self, op: OpcionPreset, delta: int) -> None:
        min_v = self._min_entero_opcion(op)
        max_v = self._max_entero_opcion(op)
        defecto = int(op.defecto if op.defecto is not None else min_v)
        actual = int(self.config.valores.get(op.id, defecto))
        actual = min(max(actual, min_v), max_v)
        if max_v <= min_v:
            self.config.valores[op.id] = min_v
        else:
            paso = paso_entero_opcion_historia(op.id)
            self.config.valores[op.id] = siguiente_entero_ciclo(
                actual,
                delta,
                min_v=min_v,
                max_v=max_v,
                paso=paso,
            )
        self.mensaje = ""

    def _ciclar_lista(self, op_id: str, delta: int) -> None:
        if self._filtro_ambito_bloqueado(op_id):
            self.mensaje = "Desactiva el otro filtro de ámbito primero."
            return
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
        aplicar_exclusion_al_cambiar_ambito(
            self.config.valores, op_id, **self._kwargs_exclusion_ambito()
        )
        if op_id == "curso":
            self._ajustar_semestre_al_curso()
            self._ajustar_n_materias_al_ambito()
            self._reconstruir_layout()
        elif op_id in ("semestre", "grupo", "periodo"):
            self._ajustar_n_materias_al_ambito()
        elif op_id in ("materia", "enfoque"):
            self._ajustar_n_preguntas_al_ambito()
        elif op_id == "origen_semilla":
            aplicar_exclusion_al_cambiar_ambito(
                self.config.valores, op_id, **self._kwargs_exclusion_ambito()
            )
            self._sync_campo_semilla_desde_config()
            self._reconstruir_layout()
        self.mensaje = ""

    def _rect_valor_ciclo(self, op_id: str) -> pygame.Rect | None:
        if op_id not in self._y_opcion:
            return None
        _, rect_val, _ = self._rects_control_fila(op_id)
        return rect_val

    def _leer_config(self) -> ConfigPresetHistoria:
        self._aplicar_campos_teclado_a_config()
        plantillas = (
            self._plantillas_materia_config()
            if self._opcion_preset("n_preguntas") is not None
            else None
        )
        return validar_config(
            self._opciones_ui(),
            ConfigPresetHistoria(valores=dict(self.config.valores)),
            materias_meta=self.datos.materias_meta,
            preset_id=self.preset.id,
            plantillas_materia=plantillas or None,
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

        navegacion = construir_navegacion_fin_partida(
            self.datos,
            self.preset,
            config,
            self.nombre,
            self.ir_a,
            self.salir_app,
            _pantalla_configuracion,
        )
        try:
            pantalla = iniciar_pantalla_partida(
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

    def _desactivar_campos_fuera_clic(self, pos: tuple[int, int]) -> None:
        for campo in self.campos_entero.values():
            if not campo.rect.collidepoint(pos):
                campo.activo = False

    def _manejar_mouse_config(self, evento: pygame.event.Event) -> None:
        if evento.type == pygame.MOUSEMOTION:
            for boton in self._botones_ui():
                boton.actualizar_hover(evento.pos)
            self._actualizar_hover_opcion_valor(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            for boton in self._botones_ui():
                if boton.manejar_clic(evento.pos, evento.button):
                    break

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if self._manejar_scroll_rueda(evento):
            return None
        for campo in self.campos_entero.values():
            if campo.manejar_evento(evento):
                return None
        if evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
            self._desactivar_campos_fuera_clic(evento.pos)
        self._manejar_mouse_config(evento)
        return None

    def _manejar_scroll_rueda(self, evento: pygame.event.Event) -> bool:
        if evento.type != pygame.MOUSEWHEEL:
            return False
        if len(self._filas_orden) <= self._max_filas_visibles():
            return False
        max_scroll = max(0, len(self._filas_orden) - self._max_filas_visibles())
        self.scroll_filas = max(
            0,
            min(max_scroll, self.scroll_filas - int(evento.y)),
        )
        self._reconstruir_layout()
        return True

    def _dibujar_fila_opcion(self, superficie: pygame.Surface, op, y: int) -> None:
        bloqueado = self._filtro_ambito_bloqueado(op.id)
        color_lbl = (140, 140, 140) if bloqueado else COLOR_ETIQUETA_PANEL_CLARO
        etiqueta = op.etiqueta.rstrip(":")
        lbl = self.fuentes["menu"].render(etiqueta + ":", True, color_lbl)
        superficie.blit(lbl, (self.X_ETIQUETA, y + 16))

        if self._opcion_campo_teclado(op):
            campo = self.campos_entero.get(op.id)
            if campo is not None:
                campo.dibujar(superficie, self.fuentes["cuerpo"])
            return

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

        for op_id, y in self._y_opcion.items():
            op = self._opcion_preset(op_id)
            if op is not None:
                self._dibujar_fila_opcion(superficie, op, y)

        if len(self._filas_orden) > self._max_filas_visibles():
            hint = self.fuentes["pequena"].render(
                "Rueda del ratón para ver más opciones",
                True,
                COLOR_TEXTO,
            )
            superficie.blit(
                hint,
                hint.get_rect(center=(ANCHO // 2, self._rect_panel_opciones().bottom + 18)),
            )

        if self.mensaje:
            aviso = self.fuentes["menu"].render(self.mensaje, True, COLOR_AVISO)
            superficie.blit(
                aviso,
                aviso.get_rect(center=(ANCHO // 2, self.boton_empezar.rect.y - 28)),
            )

        self.boton_empezar.dibujar(superficie, self.fuentes["menu"])
        self.boton_atras.dibujar(superficie, self.fuentes["menu"])
        self._dibujar_tooltip_opcion_valor(superficie)
        for campo in self.campos_entero.values():
            if campo.activo and campo.habilitado:
                tip = tooltip_opcion_ciclo_historia(
                    "semilla",
                    "entero",
                    campo.texto,
                    etiqueta_opcion="Semilla numérica",
                )
                if tip:
                    dibujar_tooltip(superficie, self.fuentes["pequena"], campo.rect, tip)
                    break
        dibujar_tooltips_botones(
            superficie,
            self.fuentes["pequena"],
            [self.boton_atras, self.boton_empezar],
        )

    def titulo_pausa(self) -> str:
        return f"Configurar — {self.preset.nombre}"


@dataclass(frozen=True)
class OpcionesPartidaHistoria:
    """Opciones opcionales al crear una partida de examen fijo / historia."""

    materias_examen: list[str] | None = None
    config_historia: ConfigPresetHistoria | None = None
    semilla_partida: int = 0
    semilla_contenido: int = 0
    rng_partida: RngPartida | None = None
    navegacion_fin: NavegacionFinPartida | None = None
    cadena_dirigido: object | None = None


class PartidaModoHistoria(Pantalla):
    """Partida con lista fija de preguntas (preset historia o examen del día)."""

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
        opciones: OpcionesPartidaHistoria | None = None,
    ) -> None:
        opts = opciones or OpcionesPartidaHistoria()
        self.nombre = nombre
        self.preset = preset
        self.config_historia = opts.config_historia or ConfigPresetHistoria()
        self.semilla_partida = opts.semilla_partida
        self.semilla_contenido = opts.semilla_contenido or opts.semilla_partida
        self._rng_partida = opts.rng_partida or crear_rng_partida(opts.semilla_partida)
        self.navegacion_fin: NavegacionFinPartida | None = opts.navegacion_fin
        self.cadena_dirigido = opts.cadena_dirigido
        self.preguntas = preguntas
        self.materias_examen = opts.materias_examen or []
        self.total = len(preguntas)
        self.ir_a = ir_a
        self.datos = datos
        self.salir_app = salir_app
        self.fuentes = crear_fuentes()
        self.registros: list = []
        self.estado = EstadoPartida(
            nombre=nombre,
            reglas=reglas,
            vidas_restantes=vidas_iniciales_partida(reglas),
        )
        self.indice = 0
        self.fase = "pregunta"
        self.feedback_mensaje = ""
        self.feedback_solucion: str | None = None
        self.feedback_ok = False
        self.botones_opcion: list[BotonOpcion] = []
        self._presentacion_opciones: PresentacionOpcionesPregunta | None = None
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

    def en_partida_activa(self) -> bool:
        return True

    def _pregunta_actual(self) -> Pregunta:
        return self.preguntas[self.indice]

    def _y_fin_opciones(self) -> int:
        return self._y_inicio_opciones() + 4 * (ALTO_OPCION_PARTIDA + SEP_OPCIONES_PARTIDA)

    def _texto_progreso(self) -> str:
        return texto_progreso_examen_cerrado(self.indice + 1, self.total)

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
        self._presentacion_opciones = presentacion_opciones_pantalla(
            p, rng=self._rng_partida
        )
        self.botones_opcion = []
        y = self._y_inicio_opciones()
        for etiqueta, texto, _ in self._presentacion_opciones.filas:
            rect = pygame.Rect(MARGEN, y, ANCHO - 2 * MARGEN, ALTO_OPCION_PARTIDA)
            boton = BotonOpcion(
                etiqueta,
                texto,
                rect,
                capturar(self._responder, etiqueta),
            )
            self.botones_opcion.append(boton)
            y += ALTO_OPCION_PARTIDA + SEP_OPCIONES_PARTIDA

    def _registrar_respuesta(self, p: Pregunta, resultado: ResultadoRespuesta) -> None:
        from Comun.informe_examen import RegistroRespuesta

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
        from Comun.modos_diarios import titulo_fin_partida_historia

        cierre = None
        if self.registros:
            titulo_txt = titulo_fin_partida_historia(
                self.preset.id,
                self.preset.nombre,
                self.config_historia,
                abandonado=abandonado,
                semilla_partida=self.semilla_partida,
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
                abandonado=abandonado,
            )
        titulo_pantalla = titulo_fin_partida_historia(
            self.preset.id,
            self.preset.nombre,
            self.config_historia,
            abandonado=abandonado,
            semilla_partida=self.semilla_partida,
            max_len=72,
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
                config_historia=self.config_historia,
                cadena_dirigido=self.cadena_dirigido,
                semilla_partida=self.semilla_partida,
                semilla_contenido=self.semilla_contenido,
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
        if feedback.solucion and self._presentacion_opciones is not None:
            self.feedback_solucion = solucion_feedback_grafico(
                texto_solucion(p, self._presentacion_opciones)
            )
        else:
            self.feedback_solucion = solucion_feedback_grafico(feedback.solucion)
        self.feedback_ok = resultado.acierto and not resultado.tiempo_agotado
        self.fase = "feedback"
        self.inicio_feedback = marcar_inicio_feedback()
        if self._presentacion_opciones is not None:
            marcar_botones_opciones_tras_respuesta(
                self.botones_opcion,
                presentacion=self._presentacion_opciones,
                correcta_dataset=p.correcta,
                respuesta_dataset=resultado.respuesta,
                acierto=resultado.acierto,
            )

    def _responder(self, letra: str) -> None:
        if self.fase != "pregunta":
            return
        p = self._pregunta_actual()
        if self._presentacion_opciones is None:
            return
        letra_dataset = self._presentacion_opciones.letra_dataset(letra)
        correcta = p.correcta if p.correcta in {"A", "B", "C", "D"} else ""
        acierto = letra_dataset == correcta and bool(correcta)
        self._tras_respuesta(ResultadoRespuesta(acierto=acierto, respuesta=letra_dataset))

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
        return f"{self.preset.nombre}  {self._linea_estado_actual()}"

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
        altura_fuente = fuente.get_height()
        y_estado = (ALTURA_BARRA_PARTIDA - altura_fuente) // 2
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
            y=y_estado,
            datos=DatosBarraEstadoPartida(segundos_pregunta_restantes=seg_preg),
        )
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
        if self.fase == "feedback":
            self._continuar()
            return True
        if self.fase != "pregunta":
            return False
        return any(b.manejar_clic(pos, boton) for b in self.botones_opcion)

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if manejar_teclado_partida(
            evento,
            fase=self.fase,
            botones_opcion=self.botones_opcion,
            on_responder=self._responder,
            on_continuar=self._continuar,
        ):
            return None
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
        mostrar_meta = self.datos.perfil.mostrar_metadatos_pregunta
        if mostrar_meta:
            meta = self.fuentes["pequena"].render(
                f"{p.materia}  {p.tipo} / {p.dificultad}",
                True,
                COLOR_ACENTO,
            )
            superficie.blit(meta, (panel.x + 12, panel.y + 10))
        dibujar_texto_multilinea(
            superficie,
            self.fuentes["cuerpo"],
            p.texto,
            rect_enunciado_panel_pregunta(panel, con_meta=mostrar_meta),
            COLOR_TITULO,
        )

        if self.total > 0:
            barra_y = Y_PANEL_PREGUNTA + panel.height + GAP_TRAS_PANEL_PARTIDA
            barra_fondo = pygame.Rect(
                MARGEN, barra_y, ANCHO - 2 * MARGEN, ALTO_BARRA_PROGRESO_PARTIDA
            )
            pygame.draw.rect(superficie, (40, 56, 80), barra_fondo, border_radius=4)
            frac = fraccion_barra_progreso_partida(
                indice_pregunta=self.indice, total=self.total
            )
            progreso_w = int(barra_fondo.width * frac)
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
        config_historia: ConfigPresetHistoria | None = None,
        cadena_dirigido=None,
        semilla_partida: int = 0,
        semilla_contenido: int = 0,
    ) -> None:
        self.preset = preset
        self.config_historia = config_historia or ConfigPresetHistoria()
        self.cadena_dirigido = cadena_dirigido
        self.semilla_partida = semilla_partida
        self.semilla_contenido = semilla_contenido or semilla_partida
        from Comun.modos_diarios import (
            es_id_examen_fijo,
            lineas_semillas_fin_examen_fijo,
            titulo_fin_partida_historia,
        )

        if titulo is None:
            titulo_resumen = titulo_fin_partida_historia(
                preset.id,
                preset.nombre,
                self.config_historia,
                semilla_partida=semilla_partida,
                max_len=72,
            )
        else:
            titulo_resumen = titulo
        lineas_sem = ()
        if es_id_examen_fijo(preset.id):
            lineas_sem = tuple(
                lineas_semillas_fin_examen_fijo(
                    self.config_historia,
                    semilla_partida=semilla_partida,
                    semilla_contenido=self.semilla_contenido,
                )
            )
        super().__init__(
            estado,
            total_previsto,
            ir_a,
            datos,
            salir_app,
            cierre_informe=cierre_informe,
            titulo=titulo_resumen,
            lineas_tras_jugador=lineas_sem,
            navegacion_fin=navegacion_fin,
        )

    def _puede_examen_dirigido(self) -> bool:
        if not self.cierre_informe or self.cierre_informe.abandonado:
            return False
        if self.cierre_informe.prefijo != "examen":
            return False
        if not preset_permite_examen_dirigido(
            self.preset.id, self.cierre_informe.registros
        ):
            return False
        return bool(self.cierre_informe.registros)

    def _crear_botones_accion(self) -> None:
        fuente = self.fuentes["menu"]
        nav = self.navegacion_fin
        if nav and nav.repetir:
            etiq = etiqueta(*BTN_REPETIR_PARTIDA)
            self._botones_accion.append(
                Boton(
                    etiq,
                    rect_boton_etiqueta(etiq, fuente, x_centro=0, y=0, alto_min=44),
                    self._repetir,
                    tooltip="Mismas preguntas (misma semilla de contenido); orden y opciones nuevos.",
                )
            )
        if self._puede_examen_dirigido():
            etiq_dir = etiqueta(*BTN_EXAMEN_DIRIGIDO)
            self._botones_accion.append(
                Boton(
                    etiq_dir,
                    rect_boton_etiqueta(etiq_dir, fuente, x_centro=0, y=0, alto_min=44),
                    self._otro_examen_dirigido,
                    tooltip="Nuevo test aleatorio priorizando tus fallos acumulados en la cadena.",
                )
            )
        if nav and nav.configurar:
            etiq = etiqueta(*BTN_CAMBIAR_OPCIONES)
            self._botones_accion.append(
                Boton(
                    etiq,
                    rect_boton_etiqueta(etiq, fuente, x_centro=0, y=0, alto_min=44),
                    self._configurar,
                    tooltip="Vuelve a la pantalla de ajustes del modo.",
                )
            )
        etiq_menu = etiqueta(*BTN_VOLVER_MENU)
        self._botones_accion.append(
            Boton(
                etiq_menu,
                rect_boton_etiqueta(etiq_menu, fuente, x_centro=0, y=0, alto_min=44),
                self._ir_menu,
            )
        )

    def _otro_examen_dirigido(self) -> None:
        if not self._guardar_informe_si_procede() or not self.cierre_informe:
            return
        from Grafico.modo_historia import preparar_examen_dirigido_sesion

        try:
            plan, reglas, cadena = preparar_examen_dirigido_sesion(
                self.datos,
                self.preset,
                self.config_historia,
                self.cierre_informe.registros,
                cadena=self.cadena_dirigido,
            )
        except ValueError as exc:
            self.mensaje_pie = str(exc)
            return
        self.ir_a(
            PartidaModoHistoria(
                nombre=self.estado.nombre,
                preset=self.preset,
                preguntas=plan.preguntas,
                reglas=reglas,
                ir_a=self.ir_a,
                datos=self.datos,
                salir_app=self.salir_app,
                opciones=OpcionesPartidaHistoria(
                    materias_examen=plan.materias,
                    config_historia=self.config_historia,
                    semilla_partida=plan.semilla_partida,
                    semilla_contenido=plan.semilla_contenido,
                    rng_partida=plan.rng,
                    navegacion_fin=self.navegacion_fin,
                    cadena_dirigido=cadena,
                ),
            )
        )

    def _construir_lineas(self) -> list[str]:
        abandonado = bool(self.cierre_informe and self.cierre_informe.abandonado)
        mostrar_aciertos = self.estado.reglas.correccion_al_final
        meta = self.cierre_informe.meta if self.cierre_informe else {}
        salas_superadas = None
        n_salas = None
        if self.cierre_informe and self.cierre_informe.prefijo == "escape":
            if meta.get("salas_superadas") is not None:
                salas_superadas = int(meta["salas_superadas"])
            if meta.get("n_salas") is not None:
                n_salas = int(meta["n_salas"])
        return lineas_resumen_breve(
            self.estado,
            self.total_previsto,
            mostrar_aciertos=mostrar_aciertos,
            abandonado=abandonado,
            salas_superadas=salas_superadas,
            n_salas=n_salas,
        )
