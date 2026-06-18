#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pantallas pygame del modo libre (configuración en dos pasos)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from dataclasses import replace
from typing import TYPE_CHECKING

import pygame

from Comun.cierre_informe import meta_cierre_libre
from Comun.navegacion_fin_partida import NavegacionFinPartida
from Comun.compatibilidad_reglas_libre import (
    normalizar_vidas_y_sistema,
    opciones_reglas_libre,
)
from Comun.dificultad import (
    complejidad_pregunta,
    max_complejidad_pool,
    niveles_en_pool,
    normalizar_niveles_seleccionados,
)
from Comun.modelos import BancoPreguntas, Pregunta
from Comun.politica_reglas import validar_reglas
from Comun.preferencias_grafico import nombre_jugador_grafico
from Comun.pool_libre import (
    filtrar_pool,
    opciones_curso_semestre,
    opciones_tematica,
    opciones_tipo,
)
from Comun.reglas_libre import (
    ETIQUETAS_SISTEMA,
    alcance,
    contexto_partida,
    reglas_desde_combinacion,
)
from Comun.reglas_partida import ReglasPartida, SistemaPuntuacion
from Grafico.textos_grafico import (
    BTN_ATRAS,
    BTN_EMPEZAR,
    BTN_SIGUIENTE,
    etiqueta,
    etiqueta_campo,
    subtitulo,
    titulo_pantalla,
)
from Grafico.modo_libre import cargar_pool_banco, etiqueta_subfiltro_visible
from Grafico.pantallas import MenuPrincipal, Pantalla
from Grafico.tema import (
    ALTO,
    ANCHO,
    COLOR_AVISO,
    COLOR_FONDO,
    COLOR_TEXTO,
    COLOR_TITULO,
    MARGEN,
    Y_INICIO_TITULO,
    crear_fuentes,
)
from Grafico.texto import dibujar_texto_centro, preparar_texto_ui
from Grafico.tooltips_ui import (
    TOOLTIP_ATRAS,
    TOOLTIP_DIFICULTAD_PROGRESIVA,
    TOOLTIP_EMPEZAR,
    TOOLTIP_SIGUIENTE,
    tooltip_filtro_principal,
    tooltip_opcion_ciclo_libre,
)
from Grafico.ui import (
    Boton,
    BotonMarcable,
    _fuente_ajustada,
    cuadricula_rects,
    dibujar_caja_valor_ciclo,
    dibujar_panel,
    dibujar_tooltips_botones,
    dibujar_tooltip,
    fila_rects_centrada,
    rect_boton_etiqueta,
    posicionar_botones_fila,
    tamano_grupo_botones,
)

if TYPE_CHECKING:
    from Grafico.app import DatosJuego

GAP_PANEL_BTNS = 24
GAP_BTNS_NAVEGACION = 12
GAP_BTNS_NAVEGACION_PASO2 = 28
Y_TITULO_LIBRE = Y_INICIO_TITULO
Y_SUBTITULO_LIBRE = Y_TITULO_LIBRE + 32
ALTO_ETIQUETA_MENU = 24
GAP_LBL_CAMPO = 12
GAP_CAMPO_PANEL = 20
PADDING_PANEL_OPCIONES = 14
ALTO_FILA = 48
GAP_FILA = 6
X_ETIQUETA = MARGEN + 36
X_CONTROLES = MARGEN + 36 + 300 + 16
ANCHO_BTN_CICLO = 44
GAP_CICLO = 8
COLOR_TEXTO_PANEL = (45, 55, 70)

TIEMPO_NINGUNO = "ninguno"
TIEMPO_PREGUNTA = "pregunta"
TIEMPO_TOTAL = "total"

FILTRO_TODAS = "todas"
FILTRO_TEMATICA = "tematica"
FILTRO_SEMESTRE = "semestre"
FILTRO_TIPO = "tipo"

OPCIONES_FILTRO = (
    (FILTRO_TODAS, "Todas"),
    (FILTRO_TEMATICA, "Temática"),
    (FILTRO_SEMESTRE, "Semestre"),
    (FILTRO_TIPO, "Tipo"),
)

OPCIONES_BANCO = (
    (BancoPreguntas.DATASET, "Modo seguro"),
    (BancoPreguntas.PLANTILLAS_TODO, "Todo + beta"),
    (BancoPreguntas.PLANTILLAS_EXTRA, "Solo plantillas"),
)

PRESETS_PREGUNTAS = (5, 10, 15, 20, 25, 30, 40, 50, 75, 100)
PRESETS_TIEMPO_PREG = (30, 45, 60, 90, 120, 180, 300)
PRESETS_TIEMPO_TOTAL = (300, 600, 900, 1200, 1800, 3600)

ETIQUETAS_FILA_PASO1: dict[str, str] = {
    "banco": "Banco de datos",
    "n_preguntas": "Preguntas en la partida",
    "vidas": "Vidas",
    "tiempo_modo": "Límite de tiempo",
    "tiempo_pregunta": "Segundos por pregunta",
    "tiempo_total": "Tiempo total (min)",
    "sistema": "Puntuación",
}


@dataclass
class EstadoConfigLibrePaso1:
    nombre: str
    banco_elegido: BancoPreguntas
    modo_infinito: bool
    total_elegido: int
    sin_vidas: bool
    vidas_count: int
    modo_tiempo: str
    tiempo_pregunta: int
    tiempo_total: int
    sistema_elegido: SistemaPuntuacion
    reglas: ReglasPartida


@dataclass(frozen=True)
class SnapshotConfigFiltrosLibre:
    """Estado del paso 2 del modo libre para repetir o reconfigurar tras una partida."""

    estado: EstadoConfigLibrePaso1
    modo_filtro: str
    tematicas_sel: frozenset[str]
    semestres_sel: frozenset[str]
    tipos_sel: frozenset[str]
    niveles_sel: frozenset[int]


def _dibujar_cabecera_libre(
    superficie: pygame.Surface,
    fuentes: dict[str, pygame.font.Font],
    paso: str,
) -> None:
    dibujar_texto_centro(
        superficie,
        titulo_pantalla("MODO LIBRE"),
        (ANCHO // 2, Y_TITULO_LIBRE),
        fuentes["titulo"].get_height(),
        COLOR_TITULO,
        bold=True,
    )
    dibujar_texto_centro(
        superficie,
        subtitulo(paso),
        (ANCHO // 2, Y_SUBTITULO_LIBRE),
        fuentes["pequena"].get_height(),
        COLOR_TEXTO,
    )


def _n_preguntas_efectivas(modo_infinito: bool, total_elegido: int) -> int:
    return 10 if modo_infinito else total_elegido


def _construir_reglas_paso1(
    *,
    modo_infinito: bool,
    total_elegido: int,
    sin_vidas: bool,
    vidas_count: int,
    modo_tiempo: str,
    tiempo_pregunta: int,
    tiempo_total: int,
    sistema_elegido: SistemaPuntuacion,
    dificultad_progresiva: bool = False,
) -> ReglasPartida:
    n = _n_preguntas_efectivas(modo_infinito, total_elegido)
    ctx = contexto_partida(modo_infinito=modo_infinito, n_preguntas=n)
    alc = alcance(ctx)
    if not alc:
        raise ValueError("Configuración no disponible para esta partida.")

    opts = opciones_reglas_libre(
        modo_infinito=modo_infinito,
        n_preguntas=n,
        sin_vidas=sin_vidas,
        sistema=sistema_elegido,
    )
    vidas: int | None = None if (sin_vidas and opts.permitir_sin_vidas) else vidas_count

    tiempo_preg: int | None = None
    tiempo_tot: int | None = None
    if modo_tiempo == TIEMPO_PREGUNTA:
        tiempo_preg = tiempo_pregunta
    elif modo_tiempo == TIEMPO_TOTAL:
        tiempo_tot = tiempo_total

    reglas = reglas_desde_combinacion(
        ctx,
        vidas=vidas,
        sistema=sistema_elegido,
        tiempo_por_pregunta_seg=tiempo_preg,
        tiempo_total_seg=tiempo_tot,
        mostrar_solucion_tras_fallo=False,
        dificultad_progresiva=dificultad_progresiva,
        modo_infinito=modo_infinito,
        n_preguntas=n,
    )
    return validar_reglas(reglas, ctx, modo_infinito=modo_infinito, n_preguntas=n)


class ConfigOpcionesLibre(Pantalla):
    """Paso 1: opciones de partida (selectores cíclicos)."""

    def __init__(
        self,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
        *,
        banco_inicial: BancoPreguntas = BancoPreguntas.DATASET,
        modo_infinito_inicial: bool = False,
        total_inicial: int = 10,
        sin_vidas_inicial: bool = False,
        vidas_count_inicial: int = 3,
        modo_tiempo_inicial: str = TIEMPO_NINGUNO,
        tiempo_pregunta_inicial: int = 90,
        tiempo_total_inicial: int = 600,
        sistema_inicial: SistemaPuntuacion = SistemaPuntuacion.ARCADE,
        dificultad_progresiva_inicial: bool = False,
    ) -> None:
        self.datos = datos
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.fuentes = crear_fuentes()
        self.mensaje = ""

        self.banco_elegido = banco_inicial
        self.modo_infinito = modo_infinito_inicial
        self.total_elegido = total_inicial
        self.sin_vidas = sin_vidas_inicial
        self.vidas_count = vidas_count_inicial
        self.modo_tiempo = modo_tiempo_inicial
        self.tiempo_pregunta = tiempo_pregunta_inicial
        self.tiempo_total = tiempo_total_inicial
        self.sistema_elegido = sistema_inicial
        self.dificultad_progresiva = dificultad_progresiva_inicial
        self.scroll_filas = 0

        self._y_panel_top = 0
        self._y_opciones = 0
        self._calcular_layout_panel()

        self.botones_ciclo: dict[str, tuple[Boton, Boton]] = {}
        self._y_opcion: dict[str, int] = {}
        self._filas_orden: list[str] = []
        self._hover_opcion_valor: str | None = None

        fuente_menu = self.fuentes["menu"]
        etiq_siguiente = etiqueta(*BTN_SIGUIENTE)
        etiq_atras = etiqueta(*BTN_ATRAS)
        ancho_btns, alto_btns = tamano_grupo_botones(
            [etiq_siguiente, etiq_atras],
            fuente_menu,
            alto_min=44,
        )
        self.boton_siguiente = Boton(
            etiq_siguiente,
            rect_boton_etiqueta(
                etiq_siguiente,
                fuente_menu,
                x_centro=ANCHO // 2,
                y=0,
                ancho=ancho_btns,
                alto=alto_btns,
            ),
            self._siguiente,
            tooltip=TOOLTIP_SIGUIENTE,
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
            self._volver_menu,
            tooltip=TOOLTIP_ATRAS,
        )
        self.boton_dificultad_progresiva = BotonMarcable(
            "Dificultad progresiva",
            pygame.Rect(0, 0, 220, 36),
            self._toggle_dificultad_progresiva,
            seleccionado=dificultad_progresiva_inicial,
            tooltip=TOOLTIP_DIFICULTAD_PROGRESIVA,
        )
        self._reconstruir_layout()

    def _reposicionar_botones_navegacion(self) -> None:
        y0 = self._rect_panel_opciones().bottom + GAP_PANEL_BTNS
        if self.boton_dificultad_progresiva.activo:
            rect = self.boton_dificultad_progresiva.rect
            rect.midtop = (ANCHO // 2, y0)
            self.boton_dificultad_progresiva.rect = rect
            y0 = rect.bottom + GAP_PANEL_BTNS
        if len(self._filas_orden) > self._max_filas_visibles():
            y0 += 28
        posicionar_botones_fila(
            [self.boton_atras, self.boton_siguiente],
            y0,
            x_centro=ANCHO // 2,
            gap=GAP_BTNS_NAVEGACION,
        )

    def _actualizar_toggle_dificultad(self) -> None:
        opts = self._opciones_compat()
        self.boton_dificultad_progresiva.activo = opts.permitir_dificultad_progresiva
        if not opts.permitir_dificultad_progresiva:
            self.dificultad_progresiva = False
            self.boton_dificultad_progresiva.seleccionado = False
        else:
            self.boton_dificultad_progresiva.seleccionado = self.dificultad_progresiva

    def _toggle_dificultad_progresiva(self) -> None:
        self.dificultad_progresiva = not self.dificultad_progresiva
        self.boton_dificultad_progresiva.seleccionado = self.dificultad_progresiva
        self._reposicionar_botones_navegacion()

    def _calcular_layout_panel(self) -> None:
        self._y_panel_top = Y_SUBTITULO_LIBRE + ALTO_ETIQUETA_MENU + GAP_CAMPO_PANEL
        self._y_opciones = self._y_panel_top + PADDING_PANEL_OPCIONES

    def _contexto(self):
        return contexto_partida(
            modo_infinito=self.modo_infinito,
            n_preguntas=_n_preguntas_efectivas(self.modo_infinito, self.total_elegido),
        )

    def _alcance(self):
        return alcance(self._contexto())

    def _opciones_compat(self):
        return opciones_reglas_libre(
            modo_infinito=self.modo_infinito,
            n_preguntas=_n_preguntas_efectivas(self.modo_infinito, self.total_elegido),
            sin_vidas=self.sin_vidas,
            sistema=self.sistema_elegido,
        )

    def _normalizar_reglas_ui(self) -> None:
        self.sin_vidas, self.sistema_elegido = normalizar_vidas_y_sistema(
            modo_infinito=self.modo_infinito,
            n_preguntas=_n_preguntas_efectivas(self.modo_infinito, self.total_elegido),
            sin_vidas=self.sin_vidas,
            sistema=self.sistema_elegido,
        )
        alc = self._alcance()
        if not alc:
            self.modo_tiempo = TIEMPO_NINGUNO
            return
        if self.modo_tiempo == TIEMPO_PREGUNTA and not alc.permitir_tiempo_pregunta:
            self.modo_tiempo = TIEMPO_NINGUNO
        if self.modo_tiempo == TIEMPO_TOTAL and not alc.permitir_tiempo_total:
            self.modo_tiempo = TIEMPO_NINGUNO

    def _filas_visibles(self) -> list[str]:
        self._normalizar_reglas_ui()
        filas = ["banco", "n_preguntas", "vidas"]
        alc = self._alcance()
        if alc and (alc.permitir_tiempo_pregunta or alc.permitir_tiempo_total):
            filas.append("tiempo_modo")
            if self.modo_tiempo == TIEMPO_PREGUNTA and alc.permitir_tiempo_pregunta:
                filas.append("tiempo_pregunta")
            if self.modo_tiempo == TIEMPO_TOTAL and alc.permitir_tiempo_total:
                filas.append("tiempo_total")
        filas.append("sistema")
        return filas

    def _max_filas_visibles(self) -> int:
        return 6

    def _rect_panel_opciones(self) -> pygame.Rect:
        alto = min(len(self._filas_orden), self._max_filas_visibles()) * (
            ALTO_FILA + GAP_FILA
        ) + 24
        return pygame.Rect(MARGEN + 16, self._y_panel_top, ANCHO - 2 * MARGEN - 32, alto)

    def _ancho_zona_controles(self) -> int:
        return self._rect_panel_opciones().right - 24 - X_CONTROLES

    def _rects_control_fila(self, op_id: str) -> tuple[pygame.Rect, pygame.Rect, pygame.Rect]:
        fila_y = self._y_opcion[op_id]
        ancho = self._ancho_zona_controles()
        alto = 36
        y = fila_y + 8
        rect_izq = pygame.Rect(X_CONTROLES, y, ANCHO_BTN_CICLO, alto)
        rect_der = pygame.Rect(X_CONTROLES + ancho - ANCHO_BTN_CICLO, y, ANCHO_BTN_CICLO, alto)
        rect_val = pygame.Rect(
            rect_izq.right + GAP_CICLO,
            y,
            rect_der.x - rect_izq.right - 2 * GAP_CICLO,
            alto,
        )
        return rect_izq, rect_val, rect_der

    def _reconstruir_layout(self) -> None:
        self._filas_orden = self._filas_visibles()
        max_scroll = max(0, len(self._filas_orden) - self._max_filas_visibles())
        self.scroll_filas = min(self.scroll_filas, max_scroll)
        visibles = self._filas_orden[
            self.scroll_filas : self.scroll_filas + self._max_filas_visibles()
        ]
        self._y_opcion.clear()
        y = self._y_opciones
        for op_id in visibles:
            self._y_opcion[op_id] = y
            y += ALTO_FILA + GAP_FILA
        self.botones_ciclo.clear()
        for op_id in visibles:
            rect_izq, _, rect_der = self._rects_control_fila(op_id)
            self.botones_ciclo[op_id] = (
                Boton("◀", rect_izq, lambda oid=op_id: self._ciclar_opcion(oid, -1)),
                Boton("▶", rect_der, lambda oid=op_id: self._ciclar_opcion(oid, 1)),
            )
        self._actualizar_toggle_dificultad()
        self._reposicionar_botones_navegacion()

    def _actualizar_hover_opcion_valor(self, pos: tuple[int, int]) -> None:
        self._hover_opcion_valor = None
        for op_id in self._y_opcion:
            _, rect_val, _ = self._rects_control_fila(op_id)
            if not rect_val.collidepoint(pos):
                continue
            if tooltip_opcion_ciclo_libre(op_id, self._clave_actual(op_id)):
                self._hover_opcion_valor = op_id
            return

    def _dibujar_tooltip_opcion_valor(self, superficie: pygame.Surface) -> None:
        if not self._hover_opcion_valor:
            return
        op_id = self._hover_opcion_valor
        tip = tooltip_opcion_ciclo_libre(op_id, self._clave_actual(op_id))
        if not tip:
            return
        _, rect_val, _ = self._rects_control_fila(op_id)
        dibujar_tooltip(superficie, self.fuentes["pequena"], rect_val, tip)

    def _items_opcion(self, op_id: str) -> list[tuple[str, str]]:
        if op_id == "banco":
            return [(b.value, etq) for b, etq in OPCIONES_BANCO]
        if op_id == "n_preguntas":
            items = [("infinito", "Infinito (sin límite)")]
            items.extend((str(n), str(n)) for n in PRESETS_PREGUNTAS)
            return items
        if op_id == "vidas":
            items: list[tuple[str, str]] = []
            opts = self._opciones_compat()
            if opts.permitir_sin_vidas:
                items.append(("sin", "Sin vidas"))
            if opts.permitir_con_vidas:
                alc = self._alcance()
                min_v = alc.min_vidas if alc else 1
                max_v = alc.max_vidas if alc else 10
                items.extend((str(n), str(n)) for n in range(min_v, max_v + 1))
            return items
        if op_id == "tiempo_modo":
            items = [(TIEMPO_NINGUNO, "Sin límite")]
            alc = self._alcance()
            if alc and alc.permitir_tiempo_pregunta:
                items.append((TIEMPO_PREGUNTA, "Por pregunta"))
            if alc and alc.permitir_tiempo_total:
                items.append((TIEMPO_TOTAL, "Tiempo total"))
            return items
        if op_id == "tiempo_pregunta":
            return [(str(s), f"{s} s") for s in PRESETS_TIEMPO_PREG]
        if op_id == "tiempo_total":
            return [
                (str(s), f"{s // 60} min" if s % 60 == 0 else f"{s} s")
                for s in PRESETS_TIEMPO_TOTAL
            ]
        if op_id == "sistema":
            return [
                (s.value, ETIQUETAS_SISTEMA.get(s, s.value))
                for s in self._opciones_compat().sistemas
            ]
        return []

    def _clave_actual(self, op_id: str) -> str:
        if op_id == "banco":
            return self.banco_elegido.value
        if op_id == "n_preguntas":
            return "infinito" if self.modo_infinito else str(self.total_elegido)
        if op_id == "vidas":
            return "sin" if self.sin_vidas else str(self.vidas_count)
        if op_id == "tiempo_modo":
            return self.modo_tiempo
        if op_id == "tiempo_pregunta":
            return str(self.tiempo_pregunta)
        if op_id == "tiempo_total":
            return str(self.tiempo_total)
        if op_id == "sistema":
            return self.sistema_elegido.value
        return ""

    def _asignar_clave(self, op_id: str, clave: str) -> None:
        if op_id == "banco":
            self.banco_elegido = BancoPreguntas(clave)
        elif op_id == "n_preguntas":
            if clave == "infinito":
                self.modo_infinito = True
            else:
                self.modo_infinito = False
                self.total_elegido = int(clave)
        elif op_id == "vidas":
            if clave == "sin":
                self.sin_vidas = True
            else:
                self.sin_vidas = False
                self.vidas_count = int(clave)
        elif op_id == "tiempo_modo":
            self.modo_tiempo = clave
        elif op_id == "tiempo_pregunta":
            self.tiempo_pregunta = int(clave)
        elif op_id == "tiempo_total":
            self.tiempo_total = int(clave)
        elif op_id == "sistema":
            self.sistema_elegido = SistemaPuntuacion(clave)

    def _texto_valor(self, op_id: str) -> str:
        for k, etq in self._items_opcion(op_id):
            if k == self._clave_actual(op_id):
                return etq
        items = self._items_opcion(op_id)
        return items[0][1] if items else "—"

    def _ciclar_opcion(self, op_id: str, delta: int) -> None:
        items = self._items_opcion(op_id)
        if not items:
            return
        claves = [k for k, _ in items]
        try:
            idx = claves.index(self._clave_actual(op_id))
        except ValueError:
            idx = 0
        self._asignar_clave(op_id, claves[(idx + delta) % len(claves)])
        self.mensaje = ""
        self._reconstruir_layout()

    def _siguiente(self) -> None:
        nombre = nombre_jugador_grafico()
        try:
            reglas = _construir_reglas_paso1(
                modo_infinito=self.modo_infinito,
                total_elegido=self.total_elegido,
                sin_vidas=self.sin_vidas,
                vidas_count=self.vidas_count,
                modo_tiempo=self.modo_tiempo,
                tiempo_pregunta=self.tiempo_pregunta,
                tiempo_total=self.tiempo_total,
                sistema_elegido=self.sistema_elegido,
                dificultad_progresiva=(
                    self.dificultad_progresiva
                    if self.boton_dificultad_progresiva.activo
                    else False
                ),
            )
        except ValueError as e:
            self.mensaje = str(e)
            return
        self.mensaje = ""
        estado = EstadoConfigLibrePaso1(
            nombre=nombre,
            banco_elegido=self.banco_elegido,
            modo_infinito=self.modo_infinito,
            total_elegido=self.total_elegido,
            sin_vidas=self.sin_vidas,
            vidas_count=self.vidas_count,
            modo_tiempo=self.modo_tiempo,
            tiempo_pregunta=self.tiempo_pregunta,
            tiempo_total=self.tiempo_total,
            sistema_elegido=self.sistema_elegido,
            reglas=reglas,
        )
        self.ir_a(ConfigFiltrosLibre(self.datos, self.ir_a, self.salir_app, estado))

    def _volver_menu(self) -> None:
        self.ir_a(MenuPrincipal(self.datos, self.ir_a, self.salir_app))

    def _botones_ui(self) -> list[Boton]:
        botones: list[Boton] = [self.boton_siguiente, self.boton_atras]
        for par in self.botones_ciclo.values():
            botones.extend(par)
        if self.boton_dificultad_progresiva.activo:
            botones.append(self.boton_dificultad_progresiva)
        return botones

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEWHEEL and len(self._filas_orden) > self._max_filas_visibles():
            max_scroll = max(0, len(self._filas_orden) - self._max_filas_visibles())
            self.scroll_filas = max(
                0,
                min(max_scroll, self.scroll_filas - int(evento.y)),
            )
            self._reconstruir_layout()
        elif evento.type == pygame.MOUSEMOTION:
            for boton in self._botones_ui():
                boton.actualizar_hover(evento.pos)
            self._actualizar_hover_opcion_valor(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            for boton in self._botones_ui():
                if boton.manejar_clic(evento.pos, evento.button):
                    break
        return None

    def _dibujar_fila_opcion(self, superficie: pygame.Surface, op_id: str, y: int) -> None:
        lbl = self.fuentes["menu"].render(
            etiqueta_campo(op_id, ETIQUETAS_FILA_PASO1[op_id] + ":"),
            True,
            COLOR_TEXTO_PANEL,
        )
        superficie.blit(lbl, (X_ETIQUETA, y + 14))
        if op_id not in self.botones_ciclo:
            return
        izq, der = self.botones_ciclo[op_id]
        _, rect_val, _ = self._rects_control_fila(op_id)
        if rect_val.width > 0:
            dibujar_caja_valor_ciclo(
                superficie,
                rect_val,
                self._texto_valor(op_id),
                self.fuentes["cuerpo"],
            )
        izq.dibujar(superficie, self.fuentes["menu"])
        der.dibujar(superficie, self.fuentes["menu"])

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        _dibujar_cabecera_libre(superficie, self.fuentes, "Paso 1 de 2 — opciones de partida")
        dibujar_panel(superficie, self._rect_panel_opciones(), color=(255, 255, 255))
        for op_id, y in self._y_opcion.items():
            self._dibujar_fila_opcion(superficie, op_id, y)
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
        if self.boton_dificultad_progresiva.activo:
            self.boton_dificultad_progresiva.dibujar(superficie, self.fuentes["menu"])
        if self.mensaje:
            aviso = self.fuentes["menu"].render(self.mensaje, True, COLOR_AVISO)
            superficie.blit(
                aviso,
                aviso.get_rect(center=(ANCHO // 2, self.boton_siguiente.rect.y - 24)),
            )
        self.boton_siguiente.dibujar(superficie, self.fuentes["menu"])
        self.boton_atras.dibujar(superficie, self.fuentes["menu"])
        self._dibujar_tooltip_opcion_valor(superficie)
        tips_nav = [self.boton_atras, self.boton_siguiente]
        if self.boton_dificultad_progresiva.activo:
            tips_nav.append(self.boton_dificultad_progresiva)
        dibujar_tooltips_botones(superficie, self.fuentes["pequena"], tips_nav)

    def titulo_pausa(self) -> str:
        return "Modo libre — paso 1"


class ConfigFiltrosLibre(Pantalla):
    """Paso 2: filtro de contenido (multi-selección) y opciones finales."""

    _Y_CONTENIDO = Y_SUBTITULO_LIBRE + ALTO_ETIQUETA_MENU + 6
    Y_FILTRO_LBL = _Y_CONTENIDO
    Y_FILTRO_BTN = Y_FILTRO_LBL + ALTO_ETIQUETA_MENU + GAP_LBL_CAMPO
    ALTO_FILTRO_PRINCIPAL = 48
    Y_SUB_LBL = Y_FILTRO_BTN + ALTO_FILTRO_PRINCIPAL + GAP_LBL_CAMPO
    Y_SUB_AYUDA = Y_SUB_LBL + ALTO_ETIQUETA_MENU + GAP_LBL_CAMPO
    Y_SUB_GRID = Y_SUB_AYUDA + 20 + 6
    SUBFILTRO_COLUMNAS = 3
    SUBFILTRO_ANCHO = 290
    SUBFILTRO_ALTO = 36
    ANCHO_BTN_NIVEL = 52
    ALTO_BTN_NIVEL = 40
    GAP_FILAS_NIVEL = 8

    def __init__(
        self,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
        estado: EstadoConfigLibrePaso1,
    ) -> None:
        self.datos = datos
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.estado = estado
        self.reglas = estado.reglas
        self.modo_infinito = estado.modo_infinito
        self.total_elegido = estado.total_elegido
        self.mensaje = ""
        self.fuentes = crear_fuentes()
        self.pool_raw = cargar_pool_banco(datos, estado.banco_elegido)

        self.modo_filtro = FILTRO_TODAS
        self.tematicas_sel: set[str] = set()
        self.semestres_sel: set[str] = set()
        self.tipos_sel: set[str] = set()
        self._opciones_subfiltro: list[tuple[str, str]] = []
        self.niveles_sel: set[int] = set()
        self.botones_nivel: list[BotonMarcable] = []

        self.botones_filtro: list[BotonMarcable] = []
        rects_filtro = fila_rects_centrada(
            len(OPCIONES_FILTRO),
            ancho_item=200,
            alto_item=self.ALTO_FILTRO_PRINCIPAL,
            separacion=20,
            y=self.Y_FILTRO_BTN,
            ancho_pantalla=ANCHO,
        )
        for rect, (codigo, texto_filtro) in zip(rects_filtro, OPCIONES_FILTRO, strict=True):
            btn = BotonMarcable(
                texto_filtro,
                rect,
                lambda c=codigo: self._elegir_modo_filtro(c),
                tooltip=tooltip_filtro_principal(codigo),
            )
            btn.codigo_filtro = codigo  # type: ignore[attr-defined]
            self.botones_filtro.append(btn)

        self.botones_subfiltro: list[BotonMarcable] = []

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
            self._atras,
            tooltip=TOOLTIP_ATRAS,
        )

        self._reconstruir_subfiltros()
        self._reconstruir_niveles_ui()

    def _filas_subfiltro_visibles(self) -> int:
        if not self._opciones_subfiltro:
            return 0
        return (
            len(self._opciones_subfiltro) + self.SUBFILTRO_COLUMNAS - 1
        ) // self.SUBFILTRO_COLUMNAS

    def _y_grid_subfiltro_inferior(self) -> int | None:
        if self.modo_filtro not in {FILTRO_TEMATICA, FILTRO_SEMESTRE, FILTRO_TIPO}:
            return None
        filas = self._filas_subfiltro_visibles()
        if filas == 0:
            return self.Y_SUB_GRID
        return self.Y_SUB_GRID + filas * (self.SUBFILTRO_ALTO + 5) - 5

    def _y_subfiltro_inferior(self) -> int | None:
        return self._y_grid_subfiltro_inferior()

    def _y_niveles_lbl(self) -> int:
        if self.modo_filtro == FILTRO_TODAS:
            return self.Y_FILTRO_BTN + self.ALTO_FILTRO_PRINCIPAL + GAP_PANEL_BTNS
        sub_inferior = self._y_subfiltro_inferior()
        if sub_inferior is not None:
            return sub_inferior + GAP_PANEL_BTNS
        return self.Y_FILTRO_BTN + self.ALTO_FILTRO_PRINCIPAL + GAP_PANEL_BTNS

    def _y_niveles_ayuda(self) -> int:
        return self._y_niveles_lbl() + ALTO_ETIQUETA_MENU + GAP_LBL_CAMPO

    def _y_niveles_fila(self) -> int:
        return self._y_niveles_ayuda() + 22 + GAP_LBL_CAMPO

    def _y_niveles_progresiva(self) -> int:
        return self._y_niveles_fila() + self.ALTO_BTN_NIVEL + GAP_LBL_CAMPO

    def _y_niveles_inferior(self) -> int:
        if self._selector_niveles_visible() and self.reglas.dificultad_progresiva:
            return self._y_niveles_progresiva() + 22
        return self._y_niveles_fila() + self.ALTO_BTN_NIVEL + GAP_PANEL_BTNS

    def _y_inferior_contenido(self) -> int:
        y = self.Y_FILTRO_BTN + self.ALTO_FILTRO_PRINCIPAL
        sub_inferior = self._y_subfiltro_inferior()
        if sub_inferior is not None:
            y = max(y, sub_inferior)
        if self._selector_niveles_visible():
            y = max(y, self._y_niveles_inferior())
        return y

    def _reposicionar_botones_navegacion(self) -> None:
        y0 = self._y_inferior_contenido() + GAP_PANEL_BTNS + 8
        posicionar_botones_fila(
            [self.boton_atras, self.boton_empezar],
            y0,
            x_centro=ANCHO // 2,
            gap=GAP_BTNS_NAVEGACION_PASO2,
        )

    def _n_preguntas_efectivas(self) -> int:
        return _n_preguntas_efectivas(self.modo_infinito, self.total_elegido)

    def _contexto(self):
        return contexto_partida(
            modo_infinito=self.modo_infinito,
            n_preguntas=self._n_preguntas_efectivas(),
        )

    def _opciones_compat(self):
        return opciones_reglas_libre(
            modo_infinito=self.modo_infinito,
            n_preguntas=self._n_preguntas_efectivas(),
            sin_vidas=self.reglas.vidas is None,
            sistema=self.reglas.sistema_puntuacion,
        )

    def _selector_niveles_visible(self) -> bool:
        return self._max_dificultad_pool() > 1

    def _niveles_disponibles_pool(self) -> frozenset[int]:
        return niveles_en_pool(self._pool_filtrado())

    def _toggle_nivel(self, nivel: int) -> None:
        disponibles = self._niveles_disponibles_pool()
        if nivel not in disponibles:
            return
        if nivel in self.niveles_sel:
            if len(self.niveles_sel) <= 1:
                self.mensaje = "Debe quedar al menos un nivel seleccionado."
                return
            self.niveles_sel.discard(nivel)
        else:
            self.niveles_sel.add(nivel)
        self.mensaje = ""
        if self.reglas.dificultad_progresiva and len(self.niveles_sel) < 2:
            self.mensaje = "La dificultad progresiva requiere al menos 2 niveles."
        self._actualizar_estado_botones_nivel()

    def _actualizar_estado_botones_nivel(self) -> None:
        disponibles = self._niveles_disponibles_pool()
        for boton in self.botones_nivel:
            nivel = getattr(boton, "nivel_valor", 0)
            boton.activo = nivel in disponibles
            boton.seleccionado = nivel in self.niveles_sel

    def _reconstruir_niveles_ui(self) -> None:
        pool = self._pool_filtrado()
        max_p = max(1, max_complejidad_pool(pool))
        disponibles = niveles_en_pool(pool)
        visible = max_p > 1
        if not visible:
            self.niveles_sel = set(disponibles)
            self.botones_nivel = []
            self._reposicionar_botones_navegacion()
            return

        if self.niveles_sel:
            self.niveles_sel &= set(disponibles)
        if not self.niveles_sel:
            self.niveles_sel = set(disponibles)

        valores = list(range(1, max_p + 1))
        rects = fila_rects_centrada(
            len(valores),
            self.ANCHO_BTN_NIVEL,
            self.ALTO_BTN_NIVEL,
            8,
            self._y_niveles_fila(),
            ANCHO,
        )
        self.botones_nivel = []
        for rect, nivel in zip(rects, valores, strict=True):
            btn = BotonMarcable(
                str(nivel),
                rect,
                lambda n=nivel: self._toggle_nivel(n),
            )
            btn.nivel_valor = nivel  # type: ignore[attr-defined]
            self.botones_nivel.append(btn)
        self._actualizar_estado_botones_nivel()
        self._reposicionar_botones_navegacion()

    def _pool_filtrado(self) -> list[Pregunta]:
        if self.modo_filtro == FILTRO_TEMATICA:
            return filtrar_pool(self.pool_raw, tematicas=self.tematicas_sel or None)
        if self.modo_filtro == FILTRO_SEMESTRE:
            return filtrar_pool(self.pool_raw, cursos_semestres=self.semestres_sel or None)
        if self.modo_filtro == FILTRO_TIPO:
            return filtrar_pool(self.pool_raw, tipos=self.tipos_sel or None)
        return list(self.pool_raw)

    def _max_dificultad_pool(self) -> int:
        return max(1, max_complejidad_pool(self._pool_filtrado()))

    def _conjunto_seleccion_actual(self) -> set[str]:
        if self.modo_filtro == FILTRO_TEMATICA:
            return self.tematicas_sel
        if self.modo_filtro == FILTRO_SEMESTRE:
            return self.semestres_sel
        if self.modo_filtro == FILTRO_TIPO:
            return self.tipos_sel
        return set()

    def _elegir_modo_filtro(self, codigo: str) -> None:
        self.modo_filtro = codigo
        self.tematicas_sel.clear()
        self.semestres_sel.clear()
        self.tipos_sel.clear()
        self.mensaje = ""
        self._reconstruir_subfiltros()
        self._reconstruir_niveles_ui()

    def _opciones_para_modo_filtro(self) -> list[tuple[str, str]]:
        if self.modo_filtro == FILTRO_TEMATICA:
            opciones = [("__todas__", "Todas")]
            opciones.extend((v, v) for v in opciones_tematica(self.pool_raw))
            return opciones
        if self.modo_filtro == FILTRO_SEMESTRE:
            return [("__todas__", "Todas"), *(
                (v, v) for v in opciones_curso_semestre(self.pool_raw)
            )]
        if self.modo_filtro == FILTRO_TIPO:
            return [("__todas__", "Todas"), *(
                (v, v) for v in opciones_tipo(self.pool_raw)
            )]
        return []

    def _reconstruir_subfiltros(self) -> None:
        for boton in self.botones_filtro:
            codigo = getattr(boton, "codigo_filtro", "")
            boton.seleccionado = codigo == self.modo_filtro

        self._opciones_subfiltro = self._opciones_para_modo_filtro()
        self._montar_botones_subfiltro()

    def _montar_botones_subfiltro(self) -> None:
        self.botones_subfiltro = []
        if not self._opciones_subfiltro:
            self._reposicionar_botones_navegacion()
            return
        rects = cuadricula_rects(
            len(self._opciones_subfiltro),
            columnas=self.SUBFILTRO_COLUMNAS,
            ancho_item=self.SUBFILTRO_ANCHO,
            alto_item=self.SUBFILTRO_ALTO,
            separacion_x=15,
            separacion_y=5,
            y_inicio=self.Y_SUB_GRID,
            ancho_pantalla=ANCHO,
        )
        seleccion = self._conjunto_seleccion_actual()
        for rect, (clave, _etiqueta) in zip(rects, self._opciones_subfiltro, strict=True):
            texto_btn = etiqueta_subfiltro_visible(
                clave,
                self.modo_filtro,
                ancho_boton=self.SUBFILTRO_ANCHO,
                fuente=self.fuentes["pequena"],
            )
            btn = BotonMarcable(
                texto_btn,
                rect,
                lambda k=clave: self._elegir_subfiltro(k),
            )
            btn.clave_subfiltro = clave  # type: ignore[attr-defined]
            if clave == "__todas__":
                btn.seleccionado = not seleccion
            else:
                btn.seleccionado = clave in seleccion
            self.botones_subfiltro.append(btn)

        self._reposicionar_botones_navegacion()

    def _elegir_subfiltro(self, clave: str) -> None:
        self.mensaje = ""
        seleccion = self._conjunto_seleccion_actual()
        if clave == "__todas__":
            seleccion.clear()
        elif clave in seleccion:
            seleccion.discard(clave)
        else:
            seleccion.add(clave)
        self._actualizar_seleccion_subfiltros()
        self._reconstruir_niveles_ui()

    def _actualizar_seleccion_subfiltros(self) -> None:
        seleccion = self._conjunto_seleccion_actual()
        for boton in self.botones_subfiltro:
            clave = getattr(boton, "clave_subfiltro", "")
            if clave == "__todas__":
                boton.seleccionado = not seleccion
            else:
                boton.seleccionado = clave in seleccion

    def _construir_reglas_finales(self) -> ReglasPartida:
        reglas = replace(
            self.reglas,
            mostrar_solucion_tras_fallo=False,
            mostrar_aciertos_en_curso=False,
        )
        return validar_reglas(
            reglas,
            self._contexto(),
            modo_infinito=self.modo_infinito,
            n_preguntas=self._n_preguntas_efectivas(),
        )

    def _meta_informe(self, pool: list[Pregunta]) -> dict:
        filtro_txt = "Todas"
        if self.modo_filtro == FILTRO_TEMATICA and self.tematicas_sel:
            filtro_txt = "Temática: " + ", ".join(sorted(self.tematicas_sel))
        elif self.modo_filtro == FILTRO_SEMESTRE and self.semestres_sel:
            filtro_txt = "Curso-semestre: " + ", ".join(sorted(self.semestres_sel))
        elif self.modo_filtro == FILTRO_TIPO and self.tipos_sel:
            filtro_txt = "Tipo: " + ", ".join(sorted(self.tipos_sel))
        n = self.total_elegido if not self.modo_infinito else max(1, len(pool))
        return meta_cierre_libre(
            banco=self.estado.banco_elegido.value,
            filtro=filtro_txt,
            infinito=self.modo_infinito,
            n_preguntas=n,
        )

    def _atras(self) -> None:
        e = self.estado
        self.ir_a(
            ConfigOpcionesLibre(
                self.datos,
                self.ir_a,
                self.salir_app,
                banco_inicial=e.banco_elegido,
                modo_infinito_inicial=e.modo_infinito,
                total_inicial=e.total_elegido,
                sin_vidas_inicial=e.sin_vidas,
                vidas_count_inicial=e.vidas_count,
                modo_tiempo_inicial=e.modo_tiempo,
                tiempo_pregunta_inicial=e.tiempo_pregunta,
                tiempo_total_inicial=e.tiempo_total,
                sistema_inicial=e.sistema_elegido,
                dificultad_progresiva_inicial=e.reglas.dificultad_progresiva,
            )
        )

    def _snapshot(self) -> SnapshotConfigFiltrosLibre:
        return SnapshotConfigFiltrosLibre(
            estado=self.estado,
            modo_filtro=self.modo_filtro,
            tematicas_sel=frozenset(self.tematicas_sel),
            semestres_sel=frozenset(self.semestres_sel),
            tipos_sel=frozenset(self.tipos_sel),
            niveles_sel=frozenset(self.niveles_sel),
        )

    @classmethod
    def desde_snapshot(
        cls,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
        snap: SnapshotConfigFiltrosLibre,
    ) -> ConfigFiltrosLibre:
        pantalla = cls(datos, ir_a, salir_app, snap.estado)
        pantalla.modo_filtro = snap.modo_filtro
        pantalla.tematicas_sel = set(snap.tematicas_sel)
        pantalla.semestres_sel = set(snap.semestres_sel)
        pantalla.tipos_sel = set(snap.tipos_sel)
        pantalla.niveles_sel = set(snap.niveles_sel)
        pantalla._reconstruir_subfiltros()
        pantalla._reconstruir_niveles_ui()
        return pantalla

    def _crear_partida(
        self,
        *,
        navegacion_fin: NavegacionFinPartida | None = None,
    ):
        from Grafico.pantallas import PartidaModoLibre

        pool = self._pool_filtrado()
        niveles = normalizar_niveles_seleccionados(self.niveles_sel, pool)
        reglas = self._construir_reglas_finales()
        return PartidaModoLibre(
            nombre=self.estado.nombre,
            preguntas=pool,
            pool=pool,
            reglas=reglas,
            ir_a=self.ir_a,
            datos=self.datos,
            salir_app=self.salir_app,
            infinito=self.modo_infinito,
            total_previsto=self.total_elegido,
            niveles_complejidad=niveles,
            meta_informe=self._meta_informe(pool),
            navegacion_fin=navegacion_fin,
        )

    def _construir_navegacion_fin(
        self, snap: SnapshotConfigFiltrosLibre
    ) -> NavegacionFinPartida:
        datos = self.datos
        ir_a = self.ir_a
        salir_app = self.salir_app
        nav_holder: list[NavegacionFinPartida | None] = [None]

        def repetir():
            cfg = ConfigFiltrosLibre.desde_snapshot(datos, ir_a, salir_app, snap)
            return cfg._crear_partida(navegacion_fin=nav_holder[0])

        def configurar():
            return ConfigFiltrosLibre.desde_snapshot(datos, ir_a, salir_app, snap)

        nav = NavegacionFinPartida(repetir=repetir, configurar=configurar)
        nav_holder[0] = nav
        return nav

    def _empezar(self) -> None:
        if self.modo_filtro == FILTRO_SEMESTRE and not opciones_curso_semestre(self.pool_raw):
            self.mensaje = "No hay curso-semestre en este banco."
            return
        if self.modo_filtro == FILTRO_TIPO and not opciones_tipo(self.pool_raw):
            self.mensaje = "No hay tipos en este banco."
            return
        pool = self._pool_filtrado()
        if not pool:
            self.mensaje = "No hay preguntas para ese filtro."
            return
        niveles = normalizar_niveles_seleccionados(self.niveles_sel, pool)
        if not niveles:
            self.mensaje = "Selecciona al menos un nivel."
            return
        if self.reglas.dificultad_progresiva and len(niveles) < 2:
            self.mensaje = "La dificultad progresiva requiere al menos 2 niveles."
            return
        try:
            self._construir_reglas_finales()
        except ValueError as e:
            self.mensaje = str(e)
            return

        self.mensaje = ""
        snap = self._snapshot()
        navegacion = self._construir_navegacion_fin(snap)
        try:
            self.ir_a(self._crear_partida(navegacion_fin=navegacion))
        except ValueError as e:
            self.mensaje = str(e)
            return

    def _botones_ui(self) -> list:
        botones: list = [
            *self.botones_filtro,
            *self.botones_subfiltro,
            *self.botones_nivel,
            self.boton_empezar,
            self.boton_atras,
        ]
        return botones

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEMOTION:
            for boton in self._botones_ui():
                boton.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            for boton in self._botones_ui():
                if boton.manejar_clic(evento.pos, evento.button):
                    break
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        _dibujar_cabecera_libre(
            superficie,
            self.fuentes,
            "Paso 2 de 2 — filtros y contenido",
        )

        filtro_lbl = self.fuentes["menu"].render(
            etiqueta_campo("filtro_principal", "Filtro principal:"), True, COLOR_TEXTO
        )
        superficie.blit(filtro_lbl, filtro_lbl.get_rect(midtop=(ANCHO // 2, self.Y_FILTRO_LBL)))
        for boton in self.botones_filtro:
            boton.dibujar(superficie, self.fuentes["menu"])

        if self.modo_filtro in {FILTRO_TEMATICA, FILTRO_SEMESTRE, FILTRO_TIPO}:
            sub_lbl = self.fuentes["menu"].render(
                etiqueta_campo("valor_filtro", "Valor del filtro:"), True, COLOR_TEXTO
            )
            superficie.blit(sub_lbl, sub_lbl.get_rect(midtop=(ANCHO // 2, self.Y_SUB_LBL)))
            ayuda = self.fuentes["pequena"].render(
                "Clic para marcar o desmarcar. Sin marcar ninguna = todas.",
                True,
                COLOR_TEXTO,
            )
            superficie.blit(ayuda, ayuda.get_rect(midtop=(ANCHO // 2, self.Y_SUB_AYUDA)))
            for boton in self.botones_subfiltro:
                boton.dibujar(superficie, self.fuentes["pequena"])

        if self._selector_niveles_visible():
            niveles_lbl = self.fuentes["menu"].render(
                etiqueta_campo("niveles_complejidad", "Niveles de complejidad:"),
                True,
                COLOR_TEXTO,
            )
            superficie.blit(
                niveles_lbl,
                niveles_lbl.get_rect(midtop=(ANCHO // 2, self._y_niveles_lbl())),
            )
            ayuda_nivel = self.fuentes["pequena"].render(
                "Clic para marcar o desmarcar. Los niveles sin preguntas aparecen desactivados.",
                True,
                COLOR_TEXTO,
            )
            superficie.blit(
                ayuda_nivel,
                ayuda_nivel.get_rect(midtop=(ANCHO // 2, self._y_niveles_ayuda())),
            )
            for boton in self.botones_nivel:
                boton.dibujar(superficie, self.fuentes["menu"])
            if self.reglas.dificultad_progresiva:
                progresiva_txt = self.fuentes["pequena"].render(
                    "Progresiva: sube por los niveles marcados, en orden.",
                    True,
                    COLOR_TEXTO,
                )
                superficie.blit(
                    progresiva_txt,
                    progresiva_txt.get_rect(
                        midtop=(ANCHO // 2, self._y_niveles_progresiva())
                    ),
                )

        if self.mensaje:
            aviso = self.fuentes["menu"].render(self.mensaje, True, COLOR_AVISO)
            superficie.blit(aviso, aviso.get_rect(center=(ANCHO // 2, self.boton_empezar.rect.y - 28)))

        self.boton_empezar.dibujar(superficie, self.fuentes["menu"])
        self.boton_atras.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(
            superficie,
            self.fuentes["pequena"],
            [self.boton_atras, self.boton_empezar, *self.botones_filtro],
        )

    def titulo_pausa(self) -> str:
        return "Modo libre — paso 2"


ConfigModoLibre = ConfigOpcionesLibre
