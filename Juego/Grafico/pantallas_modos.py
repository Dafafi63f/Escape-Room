#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Menús y partida de modos cortos: diarios, especiales y escape room."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from Comun.config_historia import ConfigPresetHistoria
from Comun.modos_diarios import (
    ID_PRESET_EXAMEN_FIJO,
    config_atajo_aleatorio,
    config_atajo_diario,
    etiqueta_fecha_examen_dia,
)
from Comun.presets_historia import PresetHistoria, buscar_preset
from Comun.preferencias_grafico import nombre_jugador_grafico
from Comun.textos_ui import EmojiPar, _p
from Grafico.modo_historia import (
    construir_navegacion_fin_partida_historia,
    iniciar_pantalla_partida_historia,
)
from Grafico.pantallas import MenuPrincipal, Pantalla
from Grafico.textos_grafico import (
    BTN_VOLVER_MENU,
    con_emoji,
    etiqueta,
    titulo_pantalla,
)
from Grafico.texto import dibujar_texto_centro
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
from Grafico.ui import (
    Boton,
    dibujar_tooltips_botones,
    posicionar_pila_inferior,
    rect_boton_etiqueta,
    rects_botones_apilados,
)

if TYPE_CHECKING:
    from Grafico.app import DatosJuego

Y_TITULO = Y_INICIO_TITULO
Y_DESC_INICIO = Y_TITULO + 54
ALTURA_LINEA_DESC = 22
DESCRIPCIONES = (
    "Examen del día: misma semilla hoy para todos; 4 materias, 24 preguntas; orden distinto cada vez.",
    "Examen aleatorio: semilla nueva cada partida; mismas materias; preguntas ordenadas F→M→D.",
)
GAP_TRAS_DESC = 28
Y_BOTONES_MODOS = Y_DESC_INICIO + len(DESCRIPCIONES) * ALTURA_LINEA_DESC + GAP_TRAS_DESC
MARGEN_INF = 22

_EMOJI_EXAMEN_DIA = _p("📕")
_EMOJI_EXAMEN_ALEATORIO = _p("🎲")


def _etiqueta_modo_diario(prefijo: str, fecha: str, emoji: EmojiPar) -> str:
    return con_emoji(
        f"{prefijo} — {fecha}",
        emoji,
        posicion="inicio",
    )


class ConfigModosDiarios(Pantalla):
    """Examen del día y examen aleatorio desde el menú principal."""

    def __init__(
        self,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
    ) -> None:
        self.datos = datos
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.fuentes = crear_fuentes()
        self.mensaje = ""
        self.preset_examen_fijo = buscar_preset(ID_PRESET_EXAMEN_FIJO)
        self.config_examen_dia = config_atajo_diario()
        self.config_examen_aleatorio = config_atajo_aleatorio()

        fuente_menu = self.fuentes["menu"]
        etiquetas = [
            _etiqueta_modo_diario(
                "Examen del día",
                etiqueta_fecha_examen_dia(),
                _EMOJI_EXAMEN_DIA,
            ),
            con_emoji("Examen aleatorio", _EMOJI_EXAMEN_ALEATORIO, posicion="inicio"),
        ]
        rects_modos = rects_botones_apilados(
            etiquetas,
            fuente_menu,
            x_centro=ANCHO // 2,
            y0=Y_BOTONES_MODOS,
            gap=10,
            ancho_min=460,
            alto_min=48,
            margen_inferior=MARGEN_INF + 72,
        )
        self.boton_examen = Boton(
            etiquetas[0],
            rects_modos[0],
            self._iniciar_examen,
        )
        self.boton_examen_aleatorio = Boton(
            etiquetas[1],
            rects_modos[1],
            self._iniciar_examen_aleatorio,
        )

        etiq_volver = etiqueta(*BTN_VOLVER_MENU)
        self.boton_volver = Boton(
            etiq_volver,
            rect_boton_etiqueta(
                etiq_volver,
                fuente_menu,
                x_centro=ANCHO // 2,
                y=0,
                ancho_min=420,
                alto_min=44,
            ),
            lambda: self.ir_a(MenuPrincipal(datos, ir_a, salir_app)),
            tooltip="Vuelve al menú principal.",
        )
        posicionar_pila_inferior(
            [self.boton_volver],
            x_centro=ANCHO // 2,
            gap=14,
            margen_inferior=MARGEN_INF,
        )

    def _iniciar_partida_diaria(
        self,
        preset: PresetHistoria,
        config: ConfigPresetHistoria,
    ) -> None:
        nombre = nombre_jugador_grafico()

        def _pantalla_configuracion():
            return ConfigModosDiarios(self.datos, self.ir_a, self.salir_app)

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

    def _iniciar_examen(self) -> None:
        self._iniciar_partida_diaria(self.preset_examen_fijo, self.config_examen_dia)

    def _iniciar_examen_aleatorio(self) -> None:
        self._iniciar_partida_diaria(
            self.preset_examen_fijo,
            self.config_examen_aleatorio,
        )

    def _botones_ui(self) -> list[Boton]:
        return [
            self.boton_examen,
            self.boton_examen_aleatorio,
            self.boton_volver,
        ]

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
        dibujar_texto_centro(
            superficie,
            titulo_pantalla("Modos diarios"),
            (ANCHO // 2, Y_TITULO),
            self.fuentes["titulo"].get_height(),
            COLOR_TITULO,
            bold=True,
        )

        fuente_peq = self.fuentes["pequena"]
        for i, texto in enumerate(DESCRIPCIONES):
            subt = fuente_peq.render(texto, True, COLOR_TEXTO)
            superficie.blit(
                subt,
                subt.get_rect(midtop=(ANCHO // 2, Y_DESC_INICIO + i * ALTURA_LINEA_DESC)),
            )

        if self.mensaje:
            msg = fuente_peq.render(self.mensaje, True, COLOR_AVISO)
            superficie.blit(msg, msg.get_rect(midtop=(ANCHO // 2, Y_BOTONES_MODOS - 28)))

        for boton in self._botones_ui():
            boton.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(superficie, fuente_peq, self._botones_ui())

    def titulo_pausa(self) -> str:
        return "Modos diarios"

# --- Modos especiales ---

from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from Comun.config_historia import ConfigPresetHistoria
from Comun.presets_historia import PresetHistoria
from Comun.preferencias_grafico import nombre_jugador_grafico
from Comun.textos_ui import EmojiPar, _p
from Grafico.modo_historia import (
    cargar_catalogo_especiales,
    construir_navegacion_fin_partida_historia,
    iniciar_pantalla_partida_historia,
)
from Grafico.pantallas import MenuPrincipal, Pantalla
from Grafico.textos_grafico import (
    BTN_VOLVER_MENU,
    con_emoji,
    etiqueta,
    etiqueta_campo,
    subtitulo,
    titulo_pantalla,
)
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
from Grafico.texto import dibujar_texto_centro
from Grafico.tooltips_ui import tooltip_modo_especial
from Grafico.ui import (
    Boton,
    capturar,
    dibujar_caja_valor_ciclo,
    dibujar_panel,
    dibujar_tooltip,
    dibujar_tooltips_botones,
    posicionar_botones_fila,
    posicionar_pila_inferior,
    rect_boton_etiqueta,
    rects_botones_apilados,
    tamano_grupo_botones,
)

if TYPE_CHECKING:
    from Grafico.app import DatosJuego

Y_TITULO = Y_INICIO_TITULO
Y_SUBTITULO = Y_TITULO + 32
Y_MODOS_LBL = Y_SUBTITULO + 36
Y_BOTONES_MODOS = Y_MODOS_LBL + 32
MARGEN_INF = 22

from Comun.emojis_escape import EMOJI_MODO_ESCAPE

_EMOJI_ESCAPE = _p(EMOJI_MODO_ESCAPE)
_EMOJI_RESISTENCIA = _p("💪")
_EMOJI_ESPECIAL_DEFECTO = _p("⚡")

from Comun.escape_room import AjustesEscapeRoom
from Grafico.textos_grafico import BTN_ATRAS, BTN_EMPEZAR
from Grafico.tooltips_ui import TOOLTIP_ATRAS, TOOLTIP_EMPEZAR, tooltip_opcion_ciclo_libre

_EMOJI_POR_PRESET: dict[str, EmojiPar] = {
    "escape_room": _EMOJI_ESCAPE,
    "ranking_resistencia": _EMOJI_RESISTENCIA,
}


class ConfigModosEspeciales(Pantalla):
    """Lista de modos especiales (un botón por preset)."""

    def __init__(
        self,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
    ) -> None:
        self.datos = datos
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.fuentes = crear_fuentes()
        self.mensaje = ""
        self.presets = cargar_catalogo_especiales()

        fuente_menu = self.fuentes["menu"]
        etiquetas_modos = [preparar_etiqueta_modo(p) for p in self.presets]
        rects_modos = rects_botones_apilados(
            etiquetas_modos,
            fuente_menu,
            x_centro=ANCHO // 2,
            y0=Y_BOTONES_MODOS,
            gap=12,
            ancho_min=460,
            alto_min=52,
            margen_inferior=MARGEN_INF + 72,
        )
        self.botones_modo: list[Boton] = []
        for preset, rect, etiq in zip(self.presets, rects_modos, etiquetas_modos, strict=True):
            self.botones_modo.append(
                Boton(
                    etiq,
                    rect,
                    capturar(self._iniciar_modo, preset.id),
                    tooltip=tooltip_modo_especial(preset.id) or preset.descripcion,
                )
            )

        etiq_volver = etiqueta(*BTN_VOLVER_MENU)
        self.boton_volver = Boton(
            etiq_volver,
            rect_boton_etiqueta(
                etiq_volver,
                fuente_menu,
                x_centro=ANCHO // 2,
                y=0,
                ancho_min=420,
                alto_min=44,
            ),
            lambda: self.ir_a(MenuPrincipal(datos, ir_a, salir_app)),
        )
        posicionar_pila_inferior(
            [self.boton_volver],
            x_centro=ANCHO // 2,
            gap=14,
            margen_inferior=MARGEN_INF,
        )

    def _pantalla_actual(self) -> ConfigModosEspeciales:
        return ConfigModosEspeciales(self.datos, self.ir_a, self.salir_app)

    def _preset_por_id(self, preset_id: str) -> PresetHistoria:
        for preset in self.presets:
            if preset.id == preset_id:
                return preset
        raise KeyError(preset_id)

    def _iniciar_modo(self, preset_id: str) -> None:
        preset = self._preset_por_id(preset_id)
        if preset_id == "escape_room":
            self.mensaje = ""
            self.ir_a(
                ConfigAjustesEscapeRoom(
                    self.datos,
                    self.ir_a,
                    self.salir_app,
                    preset,
                )
            )
            return
        nombre = nombre_jugador_grafico()
        config = ConfigPresetHistoria()
        self.mensaje = ""

        def _pantalla_configuracion():
            return ConfigModosEspeciales(self.datos, self.ir_a, self.salir_app)

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
        self.ir_a(pantalla)

    def _botones_ui(self) -> list[Boton]:
        return [*self.botones_modo, self.boton_volver]

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
        dibujar_texto_centro(
            superficie,
            titulo_pantalla("MODOS ESPECIALES"),
            (ANCHO // 2, Y_TITULO),
            self.fuentes["titulo"].get_height(),
            COLOR_TITULO,
            bold=True,
        )
        dibujar_texto_centro(
            superficie,
            subtitulo(
                "Escape room y resistencia",
                "⚡",
            ),
            (ANCHO // 2, Y_SUBTITULO),
            self.fuentes["pequena"].get_height(),
            COLOR_TEXTO,
        )

        modos_lbl = self.fuentes["menu"].render(
            etiqueta_campo("modo_especial", "Elige un modo:"), True, COLOR_TEXTO
        )
        superficie.blit(modos_lbl, modos_lbl.get_rect(midtop=(ANCHO // 2, Y_MODOS_LBL)))

        for boton in self.botones_modo:
            boton.dibujar(superficie, self.fuentes["menu"])

        if self.mensaje:
            aviso = self.fuentes["menu"].render(self.mensaje, True, COLOR_AVISO)
            superficie.blit(
                aviso,
                aviso.get_rect(center=(ANCHO // 2, self.boton_volver.rect.y - 28)),
            )

        self.boton_volver.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(
            superficie,
            self.fuentes["pequena"],
            self._botones_ui(),
        )

    def titulo_pausa(self) -> str:
        return "Modos especiales"


def preparar_etiqueta_modo(preset: PresetHistoria) -> str:
    from Grafico.texto import preparar_texto_ui

    emoji = _EMOJI_POR_PRESET.get(preset.id, _EMOJI_ESPECIAL_DEFECTO)
    texto = preset.nombre
    return preparar_texto_ui(con_emoji(texto, emoji, posicion="inicio"))


class ConfigAjustesEscapeRoom(Pantalla):
    """Ajustes rápidos antes de iniciar el escape room."""

    ALTO_ETIQUETA_MENU = 24
    GAP_SUBTITULO_CONTENIDO = 20
    Y_OPCIONES = Y_SUBTITULO + ALTO_ETIQUETA_MENU + GAP_SUBTITULO_CONTENIDO
    ALTO_FILA = 56
    GAP_FILA = 8
    X_ETIQUETA = MARGEN + 36
    X_CONTROLES = MARGEN + 36 + 340 + 20
    ANCHO_BTN_CICLO = 44
    GAP_CICLO = 8
    COLOR_ETIQUETA_PANEL = (45, 55, 70)

    _FILAS = ("banco", "salas")
    _ETIQUETAS_FILA = {
        "banco": "Banco de preguntas",
        "salas": "Número de salas",
    }

    def __init__(
        self,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
        preset: PresetHistoria,
        *,
        ajustes: AjustesEscapeRoom | None = None,
    ) -> None:
        from Comun.datos import contar_bancos
        from Comun.escape_room import (
            OPCIONES_BANCO_ESCAPE,
            normalizar_n_salas_escape,
        )

        self.datos = datos
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.preset = preset
        self.fuentes = crear_fuentes()
        self.mensaje = ""

        inicial = ajustes or AjustesEscapeRoom()
        self._opciones_banco = OPCIONES_BANCO_ESCAPE
        self._idx_banco = self._opciones_banco.index(inicial.banco)
        self._n_salas = normalizar_n_salas_escape(inicial.n_salas)
        self._conteos_banco = contar_bancos(
            datos.path_preguntas_csv,
            datos.path_plantillas_json,
            datos.materias_meta,
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
            self._volver_especiales,
            tooltip=TOOLTIP_ATRAS,
        )
        self._reposicionar_botones_navegacion()

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
        rect_der = pygame.Rect(
            self.X_CONTROLES + ancho - self.ANCHO_BTN_CICLO,
            y,
            self.ANCHO_BTN_CICLO,
            alto,
        )
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
        for op_id in self._FILAS:
            self._y_opcion[op_id] = y
            y += self.ALTO_FILA + self.GAP_FILA
        self._y_fin_opciones = y

        self.botones_ciclo.clear()
        for op_id in self._FILAS:
            rect_izq, _, rect_der = self._rects_control_fila(op_id)
            self.botones_ciclo[op_id] = (
                Boton("◀", rect_izq, capturar(self._ciclar, op_id, -1)),
                Boton("▶", rect_der, capturar(self._ciclar, op_id, 1)),
            )
        if hasattr(self, "boton_empezar"):
            self._reposicionar_botones_navegacion()

    def _reposicionar_botones_navegacion(self) -> None:
        y = max(560, self._rect_panel_opciones().bottom + 48)
        posicionar_botones_fila(
            [self.boton_atras, self.boton_empezar],
            y,
            x_centro=ANCHO // 2,
            gap=12,
        )

    def _clave_opcion(self, op_id: str) -> str:
        if op_id == "banco":
            return self._opciones_banco[self._idx_banco].value
        if op_id == "salas":
            return str(self._n_salas)
        return ""

    def _actualizar_hover_opcion_valor(self, pos: tuple[int, int]) -> None:
        self._hover_opcion_valor = None
        for op_id in self._FILAS:
            _, rect_val, _ = self._rects_control_fila(op_id)
            if not rect_val.collidepoint(pos):
                continue
            if self._tooltip_opcion(op_id):
                self._hover_opcion_valor = op_id
            return

    def _tooltip_opcion(self, op_id: str) -> str | None:
        if op_id == "banco":
            return tooltip_opcion_ciclo_libre("banco", self._clave_opcion("banco"))
        if op_id == "salas":
            from Comun.escape_room import SALAS_MAX, SALAS_MIN, SALAS_PASO

            return (
                f"{self._n_salas} salas; cada una tiene tres puertas. "
                f"Rango {SALAS_MIN}–{SALAS_MAX} (paso {SALAS_PASO})."
            )
        return None

    def _dibujar_tooltip_opcion_valor(self, superficie: pygame.Surface) -> None:
        if not self._hover_opcion_valor:
            return
        op_id = self._hover_opcion_valor
        tip = self._tooltip_opcion(op_id)
        if not tip:
            return
        _, rect_val, _ = self._rects_control_fila(op_id)
        dibujar_tooltip(superficie, self.fuentes["pequena"], rect_val, tip)

    def _dibujar_fila_opcion(self, superficie: pygame.Surface, op_id: str, y: int) -> None:
        lbl = self.fuentes["menu"].render(
            etiqueta_campo(op_id, self._ETIQUETAS_FILA[op_id] + ":"),
            True,
            self.COLOR_ETIQUETA_PANEL,
        )
        superficie.blit(lbl, (self.X_ETIQUETA, y + 16))

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

    def _texto_valor(self, op_id: str) -> str:
        if op_id == "banco":
            return self._texto_banco()
        if op_id == "salas":
            return self._texto_salas()
        return "—"

    def _ajustes_actuales(self) -> AjustesEscapeRoom:
        from Comun.escape_room import AjustesEscapeRoom

        return AjustesEscapeRoom(
            banco=self._opciones_banco[self._idx_banco],
            n_salas=self._n_salas,
        )

    def _texto_banco(self) -> str:
        from Comun.modelos import BancoPreguntas, ETIQUETAS_BANCO_CORTAS

        banco = self._opciones_banco[self._idx_banco]
        n = self._conteos_banco.get(banco, 0)
        etiqueta = ETIQUETAS_BANCO_CORTAS.get(banco, str(banco))
        return f"{etiqueta} ({n})"

    def _texto_salas(self) -> str:
        return f"{self._n_salas} salas"

    def _ciclar(self, clave: str, delta: int) -> None:
        from Comun.config_historia import siguiente_entero_ciclo
        from Comun.escape_room import SALAS_MAX, SALAS_MIN, SALAS_PASO

        if clave == "banco":
            n = len(self._opciones_banco)
            self._idx_banco = (self._idx_banco + delta) % n
        elif clave == "salas":
            self._n_salas = siguiente_entero_ciclo(
                self._n_salas,
                delta,
                min_v=SALAS_MIN,
                max_v=SALAS_MAX,
                paso=SALAS_PASO,
            )
        self.mensaje = ""

    def _pantalla_ajustes(self) -> ConfigAjustesEscapeRoom:
        return ConfigAjustesEscapeRoom(
            self.datos,
            self.ir_a,
            self.salir_app,
            self.preset,
            ajustes=self._ajustes_actuales(),
        )

    def _volver_especiales(self) -> None:
        self.ir_a(ConfigModosEspeciales(self.datos, self.ir_a, self.salir_app))

    def _empezar(self) -> None:
        from Comun.config_historia import ConfigPresetHistoria
        from Comun.navegacion_fin_partida import NavegacionFinPartida

        nombre = nombre_jugador_grafico()
        config = ConfigPresetHistoria()
        ajustes = self._ajustes_actuales()
        self.mensaje = ""

        def _pantalla_configuracion():
            return self._pantalla_ajustes()

        nav_holder: dict[str, NavegacionFinPartida] = {}

        def repetir() -> Pantalla:
            return iniciar_pantalla_partida_historia(
                self.datos,
                self.preset,
                config,
                nombre,
                self.ir_a,
                self.salir_app,
                navegacion_fin=nav_holder["nav"],
                ajustes_escape=ajustes,
            )

        nav = NavegacionFinPartida(
            repetir=repetir,
            configurar=_pantalla_configuracion,
        )
        nav_holder["nav"] = nav

        try:
            pantalla = iniciar_pantalla_partida_historia(
                self.datos,
                self.preset,
                config,
                nombre,
                self.ir_a,
                self.salir_app,
                navegacion_fin=nav,
                ajustes_escape=ajustes,
            )
        except ValueError as e:
            self.mensaje = str(e)
            return
        self.ir_a(pantalla)

    def _botones_ui(self) -> list[Boton]:
        out: list[Boton] = []
        for par in self.botones_ciclo.values():
            out.extend(par)
        out.extend([self.boton_atras, self.boton_empezar])
        return out

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

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        dibujar_texto_centro(
            superficie,
            titulo_pantalla("ESCAPE ROOM"),
            (ANCHO // 2, Y_TITULO),
            self.fuentes["titulo"].get_height(),
            COLOR_TITULO,
            bold=True,
        )
        dibujar_texto_centro(
            superficie,
            subtitulo("Configura la partida", _EMOJI_ESCAPE),
            (ANCHO // 2, Y_SUBTITULO),
            self.fuentes["pequena"].get_height(),
            COLOR_TEXTO,
        )

        dibujar_panel(superficie, self._rect_panel_opciones(), color=(255, 255, 255))
        for op_id in self._FILAS:
            self._dibujar_fila_opcion(superficie, op_id, self._y_opcion[op_id])

        if self.mensaje:
            aviso = self.fuentes["menu"].render(self.mensaje, True, COLOR_AVISO)
            superficie.blit(
                aviso,
                aviso.get_rect(center=(ANCHO // 2, self.boton_empezar.rect.y - 28)),
            )

        self.boton_atras.dibujar(superficie, self.fuentes["menu"])
        self.boton_empezar.dibujar(superficie, self.fuentes["menu"])
        self._dibujar_tooltip_opcion_valor(superficie)
        dibujar_tooltips_botones(
            superficie,
            self.fuentes["pequena"],
            [self.boton_atras, self.boton_empezar],
        )

    def titulo_pausa(self) -> str:
        return "Escape room"


# --- Escape room ---

import time
from collections.abc import Callable
from dataclasses import replace
from typing import TYPE_CHECKING

import pygame

from Comun.informe_examen import CierreInformePartida, meta_cierre_historia
from Comun.config_historia import etiqueta_grupo_tematico
from Comun.escape_partida import (
    VIDAS_MAX_ABSOLUTO_ESCAPE,
    aplicar_bonificacion_completar,
    bonificacion_completar_escape,
    materias_del_grupo,
    mensaje_acierto_desafio,
    mensaje_feedback_puerta_sin_pregunta,
    puerta_es_jefe,
    puntos_extra_mult_desafio,
    reglas_juego_desafio,
    reglas_partida_desde_desafio,
    reemplazar_pregunta_cambio_escape,
    seleccionar_preguntas_desafio,
)
from Comun.reglas_partida import (
    SistemaPuntuacion,
    calcular_puntos_arcade,
    sumar_puntos_arcade,
    vidas_iniciales_partida,
)
from Comun.emojis_escape import CapaIconoEscape
from Comun.eventos_partida import (
    evento_por_id,
    evento_sin_pregunta_escape,
    emoji_tipo_puerta_escape,
    iconos_efecto_puerta,
    IconoEfectoPuerta,
    linea_bloque_preguntas_puerta,
    linea_recompensa_pie_carta,
    lineas_botin_puerta,
)
from Comun.semillas import crear_rng_partida
from Comun.escape_room import (
    ConfigEscapeRoom,
    PityPuertasEspecialesEscape,
    PuertaEscape,
    SalaEscapeRoom,
    generar_puertas_sala,
)
from Comun.resistencia_motor import (
    emoji_powerup,
    etiqueta_powerup,
    letras_ocultas_niebla,
    puede_usar_powerup_en_pregunta,
    prefijar_emoji,
    revocar_powerup_usado,
)
from Comun.tienda_escape import (
    ARTICULOS_POR_VISITA_TIENDA,
    EstadoInventarioEscape,
    aplicar_loot,
    articulo_comprable_tienda_escape,
    articulo_tienda_por_id,
    bonificacion_aplicable,
    comprar_articulo,
    descripcion_articulo,
    es_bonificacion,
    linea_detalle_tienda_puerta,
    puede_visitar_tienda_escape,
    puerta_es_tienda,
    seleccionar_articulos_tienda_visita,
    usar_objeto,
)
from Comun.modelos import Pregunta
from Comun.motor_nucleo import (
    EstadoPartida,
    ResultadoRespuesta,
    evaluar_respuesta,
    linea_estado,
    marcar_botones_opciones_tras_respuesta,
    presentacion_opciones_pantalla,
    texto_opcion_visible_pantalla,
    texto_solucion,
)
from Comun.presets_historia import PresetHistoria
from Comun.reglas_partida import ReglasPartida
from Grafico.barra_estado import dibujar_estado_partida_en_barra
from Grafico.feedback_partida import (
    dibujar_feedback_partida,
    feedback_debe_avanzar,
    marcar_inicio_feedback,
    solucion_feedback_grafico,
)
from Grafico.pantallas import (
    ALTURA_BARRA_PARTIDA,
    ALTO_OPCION_PARTIDA,
    ALTO_PANEL_PREGUNTA,
    GAP_TRAS_PANEL_PARTIDA,
    MARGEN_INF_PARTIDA,
    MenuPrincipal,
    Pantalla,
    SEP_OPCIONES_PARTIDA,
    Y_PANEL_PREGUNTA,
    _segundos_pregunta_restantes,
    x_min_centro_barra_partida,
)
from Grafico.pantallas_historia import ResumenHistoriaPartida
from Grafico.tema import (
    ALTO,
    ANCHO,
    COLOR_ACENTO,
    COLOR_FONDO,
    COLOR_TEXTO_PANEL,
    COLOR_TITULO,
    MARGEN,
    crear_fuentes,
)
from Grafico.texto import (
    medir_texto_mixto,
    preparar_texto_ui,
    renderizar_texto_mixto,
    texto_requiere_fuentes_mixtas,
)
from Grafico.textos_grafico import BTN_ABANDONAR, etiqueta, titulo_pantalla
from Grafico.tooltips_ui import TOOLTIP_ABANDONAR_HISTORIA
from Grafico.ui import (
    Boton,
    BotonOpcion,
    capturar,
    dibujar_panel,
    dibujar_texto_multilinea,
    dibujar_tooltip,
    dibujar_tooltips_botones,
    medir_etiqueta_boton,
    rect_boton_etiqueta,
)

if TYPE_CHECKING:
    from Grafico.app import DatosJuego

_INV_GAP = 8
_INV_ALTO_BOTON = 32
_INV_FILA_ALTURA = 36
_INV_PADDING_BANDA = 8
_INV_ANCHO_MIN = 96
_INV_ANCHO_MAX = 156
_INV_PADDING_ETIQUETA = 28


def empaquetar_filas_inventario(
    anchos: list[int],
    *,
    ancho_disponible: int,
    gap: int = _INV_GAP,
) -> list[list[int]]:
    """Distribuye anchos de botones en filas sin desbordar ``ancho_disponible``."""
    if not anchos:
        return []
    filas: list[list[int]] = []
    fila: list[int] = []
    ancho_fila = 0
    for ancho in anchos:
        extra = gap if fila else 0
        if fila and ancho_fila + extra + ancho > ancho_disponible:
            filas.append(fila)
            fila = []
            ancho_fila = 0
            extra = 0
        if extra:
            ancho_fila += extra
        fila.append(ancho)
        ancho_fila += ancho
    if fila:
        filas.append(fila)
    return filas


class PartidaEscapeRoom(Pantalla):
    """30 salas: elige 1 de 3 puertas; fallar avanza pero cuesta 1 vida."""

    Y_TITULO_SALA = 96
    Y_SUBTITULO_PUERTAS = 148
    Y_CARTAS_PUERTAS = 188
    GAP_CARTAS_PUERTAS = 14
    ALTO_CARTA_PUERTA = 400
    _COLOR_CARTA = (255, 255, 255)
    _COLOR_CARTA_HOVER = (228, 238, 252)
    _COLOR_TEXTO_CARTA = (40, 52, 72)
    _COLOR_SUBTEXTO_CARTA = (75, 90, 115)
    _ALTO_FILA_ICONOS = 34
    _GAP_ICONOS = 8
    _PAD_ICONO = 6
    _TAMANO_ICONO = 26

    def __init__(
        self,
        *,
        nombre: str,
        preset: PresetHistoria,
        config: ConfigEscapeRoom,
        pool: list[Pregunta],
        materias_pool: tuple[str, ...],
        reglas: ReglasPartida,
        semilla: int,
        total_previsto: int,
        ir_a: Callable[[Pantalla], None],
        datos: DatosJuego,
        salir_app: Callable[[], None],
        navegacion_fin=None,
    ) -> None:
        from Comun.navegacion_fin_partida import NavegacionFinPartida

        self.nombre = nombre
        self.preset = preset
        self.config = config
        self.pool = pool
        self.materias_pool = materias_pool
        self.semilla = semilla
        self.rng = crear_rng_partida(semilla)
        self.total_previsto = total_previsto
        self.ir_a = ir_a
        self.datos = datos
        self.salir_app = salir_app
        self.navegacion_fin: NavegacionFinPartida | None = navegacion_fin
        self.vidas_max = vidas_iniciales_partida(reglas)
        self.fuentes = crear_fuentes()
        self.reglas_base = reglas
        self.registros: list = []
        self.estado = EstadoPartida(
            nombre=nombre,
            reglas=reglas,
            vidas_restantes=self.vidas_max,
        )
        self.sala_idx = 0
        self.pregunta_idx = 0
        self.preguntas_desafio: list[Pregunta] = []
        self._usadas_pool: set[int] = set()
        self.puertas_actuales: tuple[PuertaEscape, ...] = ()
        self.puerta_actual: PuertaEscape | None = None
        self.botones_puerta: list[Boton] = []
        self._iconos_puerta: list[tuple[IconoEfectoPuerta, ...]] = []
        self._hover_icono: tuple[int, int] | None = None
        self.fase = "puertas"
        self._resultado: str | None = None
        self.desafio_fallo = False
        self.letras_ocultas: frozenset[str] = frozenset()
        self.letras_niebla: frozenset[str] = frozenset()
        self.tiempo_pregunta_limite: int | None = None
        self.feedback_mensaje = ""
        self.feedback_solucion: str | None = None
        self.feedback_ok = False
        self.inicio_feedback = 0.0
        self.botones_opcion: list[BotonOpcion] = []
        self._presentacion_opciones = None
        self.inicio_pregunta = time.monotonic()
        self._tiempo_agotado_marcado = False
        self._bonus_completar_mostrado = False
        self._mult_puntos_desafio = 1
        self.inventario_escape = EstadoInventarioEscape()
        self.botones_tienda: list[Boton] = []
        self._articulos_tienda: tuple = ()
        self._articulos_comprados_visita: set[str] = set()
        self._hover_icono_tienda: int | None = None
        self.botones_inventario: list[Boton] = []
        self.boton_salir_tienda: Boton | None = None
        self.mensaje_tienda = ""
        self._pity_puertas = PityPuertasEspecialesEscape()

        lbl_abandonar = etiqueta(*BTN_ABANDONAR)
        self.boton_abandonar = Boton(
            lbl_abandonar,
            rect_boton_etiqueta(
                lbl_abandonar,
                self.fuentes["pequena"],
                x_derecha=ANCHO - MARGEN,
                y=14,
            ),
            self._abandonar,
            tooltip=TOOLTIP_ABANDONAR_HISTORIA,
        )
        self._preparar_puertas()

    def _sala_actual(self) -> SalaEscapeRoom | None:
        if self.sala_idx >= len(self.config.salas):
            return None
        return self.config.salas[self.sala_idx]

    def _texto_progreso_sala(self) -> str:
        total = len(self.config.salas)
        return f"{min(self.sala_idx + 1, total)}/{total}"

    def _texto_progreso_puerta(self) -> str | None:
        if (
            self.puerta_actual is None
            or not self.preguntas_desafio
            or self.fase not in ("pregunta", "feedback")
            or self.puerta_actual.modificadores.sin_pregunta
        ):
            return None
        return f"{self.pregunta_idx + 1}/{len(self.preguntas_desafio)}"

    def _kwargs_barra_estado(self) -> dict:
        seg_preg = None
        if self.fase == "pregunta" and self.tiempo_pregunta_limite:
            limite = self._limite_tiempo_pregunta_efectivo()
            if limite:
                seg_preg = _segundos_pregunta_restantes(
                    self.inicio_pregunta,
                    limite,
                )
        return {
            "segundos_pregunta_restantes": seg_preg,
            "vidas_max": self.vidas_max,
            "progreso_sala": self._texto_progreso_sala(),
            "progreso_puerta": self._texto_progreso_puerta(),
            "mostrar_tiempo_activo": (
                self.fase in ("pregunta", "feedback")
                and bool(self.estado.reglas.tiempo_total_seg)
            ),
        }

    def _linea_estado_actual(self) -> str:
        return linea_estado(
            self.estado,
            "",
            **self._kwargs_barra_estado(),
        )

    def _dibujar_meta_pregunta(
        self,
        superficie: pygame.Surface,
        texto: str,
        x: int,
        y: int,
    ) -> None:
        """Meta sobre el enunciado; soporta emoji (solo escape incluye icono de puerta)."""
        texto = preparar_texto_ui(texto)
        tam = self.fuentes["pequena"].get_height()
        if texto_requiere_fuentes_mixtas(texto):
            renderizar_texto_mixto(superficie, texto, (x, y), COLOR_ACENTO, tam)
            return
        meta = self.fuentes["pequena"].render(texto, True, COLOR_ACENTO)
        superficie.blit(meta, (x, y))

    def _preparar_puertas(self) -> None:
        sala = self._sala_actual()
        if sala is None:
            self._resultado = "victoria"
            self._fin_partida()
            return
        self.puertas_actuales, self._pity_puertas = generar_puertas_sala(
            sala,
            self.sala_idx,
            materias_pool=self.materias_pool,
            pool_preguntas=self.pool,
            rng=self.rng,
            puertas_por_sala=self.config.puertas_por_sala,
            n_salas=self.config.n_salas,
            pity=self._pity_puertas,
            estado=self.estado,
            vidas_max=self.vidas_max,
        )
        self.puerta_actual = None
        self.preguntas_desafio = []
        self.pregunta_idx = 0
        self.desafio_fallo = False
        self.fase = "puertas"
        rects = self._rects_cartas_puertas(len(self.puertas_actuales))
        self.botones_puerta = [
            Boton(
                "",
                rects[i],
                capturar(self._elegir_puerta, i),
                mostrar_texto=False,
            )
            for i in range(len(self.puertas_actuales))
        ]
        self._iconos_puerta = [
            iconos_efecto_puerta(
                evento=p.evento,
                modificadores=p.modificadores,
                n_preguntas=p.n_preguntas,
                delta_jefe=(
                    bonificacion_completar_escape(p).delta_vidas
                    if puerta_es_jefe(p)
                    else 0
                ),
                rng=self.rng,
            )
            for p in self.puertas_actuales
        ]
        self._hover_icono = None

    def _ancho_icono(self, emoji: str) -> int:
        texto = preparar_texto_ui(emoji)
        if texto_requiere_fuentes_mixtas(texto):
            return medir_texto_mixto(texto, self._TAMANO_ICONO)[0] + 2 * self._PAD_ICONO
        fuente = self.fuentes["menu"]
        return fuente.size(texto)[0] + 2 * self._PAD_ICONO

    def _rects_iconos_carta(
        self,
        inner: pygame.Rect,
        iconos: tuple[IconoEfectoPuerta, ...],
    ) -> list[pygame.Rect]:
        if not iconos:
            return []
        anchos = [self._ancho_icono(ic.emoji) for ic in iconos]
        total = sum(anchos) + self._GAP_ICONOS * (len(iconos) - 1)
        x = inner.x + max(0, (inner.width - total) // 2)
        y = inner.y
        rects: list[pygame.Rect] = []
        for ancho in anchos:
            rects.append(pygame.Rect(x, y, ancho, self._ALTO_FILA_ICONOS))
            x += ancho + self._GAP_ICONOS
        return rects

    def _dibujar_fila_iconos(
        self,
        superficie: pygame.Surface,
        inner: pygame.Rect,
        iconos: tuple[IconoEfectoPuerta, ...],
        *,
        hover_idx: int | None,
    ) -> list[pygame.Rect]:
        rects = self._rects_iconos_carta(inner, iconos)
        tamano = self._TAMANO_ICONO
        for i, (icono, rect) in enumerate(zip(iconos, rects, strict=True)):
            fondo = (232, 240, 252) if hover_idx == i else (245, 248, 252)
            pygame.draw.rect(superficie, fondo, rect, border_radius=6)
            if hover_idx == i:
                pygame.draw.rect(superficie, COLOR_ACENTO, rect, width=2, border_radius=6)
            emoji_ui = preparar_texto_ui(icono.emoji)
            if texto_requiere_fuentes_mixtas(emoji_ui):
                ancho, alto = medir_texto_mixto(emoji_ui, tamano)
                renderizar_texto_mixto(
                    superficie,
                    emoji_ui,
                    (rect.centerx - ancho // 2, rect.centery - alto // 2),
                    self._COLOR_TEXTO_CARTA,
                    tamano,
                )
            else:
                surf = self.fuentes["menu"].render(emoji_ui, True, self._COLOR_TEXTO_CARTA)
                superficie.blit(surf, surf.get_rect(center=rect.center))
        return rects

    def _actualizar_hover_iconos(self, pos: tuple[int, int]) -> None:
        self._hover_icono = None
        for i, boton in enumerate(self.botones_puerta):
            if not boton.rect.collidepoint(pos):
                continue
            inner = boton.rect.inflate(-20, -20)
            rects = self._rects_iconos_carta(inner, self._iconos_puerta[i])
            for j, rect in enumerate(rects):
                if rect.collidepoint(pos):
                    self._hover_icono = (i, j)
                    return
            return

    def _rects_cartas_puertas(self, cantidad: int) -> list[pygame.Rect]:
        if cantidad <= 0:
            return []
        gap = self.GAP_CARTAS_PUERTAS
        ancho_total = ANCHO - 2 * MARGEN
        ancho_carta = (ancho_total - gap * (cantidad - 1)) // cantidad
        rects: list[pygame.Rect] = []
        x = MARGEN
        for _ in range(cantidad):
            rects.append(
                pygame.Rect(x, self.Y_CARTAS_PUERTAS, ancho_carta, self.ALTO_CARTA_PUERTA)
            )
            x += ancho_carta + gap
        return rects

    def _lineas_carta_puerta(self, puerta: PuertaEscape) -> tuple[str, str, list[str]]:
        if puerta.modificadores.sin_pregunta:
            if puerta_es_tienda(puerta):
                ev = evento_por_id("tienda")
                return ev.nombre, ev.descripcion, []
            ev = evento_sin_pregunta_escape(puerta.modificadores) or evento_por_id("descanso")
            detalle = list(
                lineas_botin_puerta(
                    puerta.modificadores,
                    vidas_max_tope=self.vidas_max,
                    vidas_max_absoluto=VIDAS_MAX_ABSOLUTO_ESCAPE,
                )
            )
            return ev.nombre, ev.descripcion, detalle

        evento = puerta.evento
        titulo = evento.nombre
        descripcion = evento.descripcion
        detalle: list[str] = []
        if puerta.n_preguntas > 0:
            detalle.append(linea_bloque_preguntas_puerta(puerta.n_preguntas))
        if evento.materia:
            detalle.append(evento.materia)
        if evento.grupo:
            nombre_grupo = etiqueta_grupo_tematico(evento.grupo)
            mats = materias_del_grupo(self.pool, evento.grupo)
            if mats:
                detalle.append(f"{nombre_grupo} · {len(mats)} materias")
            else:
                detalle.append(nombre_grupo)
        detalle.extend(
            lineas_botin_puerta(
                puerta.modificadores,
                vidas_max_tope=self.vidas_max,
                vidas_max_absoluto=VIDAS_MAX_ABSOLUTO_ESCAPE,
            )
        )
        if puerta_es_jefe(puerta):
            bonus = bonificacion_completar_escape(puerta)
            if bonus.delta_vidas > 0:
                n = bonus.delta_vidas
                txt = "1 vida" if n == 1 else f"{n} vidas"
                detalle.append(linea_recompensa_pie_carta(f"+{txt} al superar (jefe)"))
        mult = puerta.modificadores.multiplicador_puntos
        if mult > 1:
            detalle.append(linea_recompensa_pie_carta(f"puntos ×{mult} en toda la puerta"))
        return titulo, descripcion, detalle

    def _dibujar_carta_puerta(
        self,
        superficie: pygame.Surface,
        puerta: PuertaEscape,
        rect: pygame.Rect,
        *,
        hover: bool,
        indice: int,
    ) -> None:
        dibujar_panel(superficie, rect, color=self._COLOR_CARTA_HOVER if hover else self._COLOR_CARTA)
        if hover:
            pygame.draw.rect(superficie, COLOR_ACENTO, rect, width=3, border_radius=10)

        inner = rect.inflate(-20, -20)
        y = inner.y
        iconos = self._iconos_puerta[indice]
        hover_icono = self._hover_icono[1] if self._hover_icono and self._hover_icono[0] == indice else None
        self._dibujar_fila_iconos(superficie, inner, iconos, hover_idx=hover_icono)
        y += self._ALTO_FILA_ICONOS + 10

        titulo, descripcion, detalle = self._lineas_carta_puerta(puerta)

        titulo_ui = preparar_texto_ui(titulo)
        fuente_tit = self.fuentes["menu"]
        tit_surf = fuente_tit.render(titulo_ui, True, self._COLOR_TEXTO_CARTA)
        tit_rect = tit_surf.get_rect(centerx=inner.centerx, top=y)
        superficie.blit(tit_surf, tit_rect)
        y += tit_surf.get_height() + 8

        alto_desc = min(56, max(36, inner.bottom - y - 120))
        desc_rect = pygame.Rect(inner.x, y, inner.width, alto_desc)
        dibujar_texto_multilinea(
            superficie,
            self.fuentes["pequena"],
            descripcion,
            desc_rect,
            self._COLOR_SUBTEXTO_CARTA,
        )
        y = desc_rect.bottom + 12

        if detalle:
            pygame.draw.line(
                superficie,
                (200, 210, 225),
                (inner.x, y),
                (inner.right, y),
                1,
            )
            y += 10

            detalle_rect = pygame.Rect(inner.x, y, inner.width, inner.bottom - y)
            dibujar_texto_multilinea(
                superficie,
                self.fuentes["cuerpo"],
                "\n".join(detalle),
                detalle_rect,
                self._COLOR_TEXTO_CARTA,
            )

    def _aplicar_reglas_desafio(self, puerta: PuertaEscape) -> None:
        reglas = reglas_juego_desafio(puerta, numero_sala=self.sala_idx + 1, n_salas=self.config.n_salas)
        self.estado.reglas = reglas_partida_desde_desafio(self.reglas_base, reglas)
        self.tiempo_pregunta_limite = reglas.tiempo_pregunta_seg
        if reglas.tiempo_puerta_seg:
            self.estado.inicio_total = time.monotonic()
        self._mult_puntos_desafio = reglas.multiplicador_puntos
        self.letras_ocultas = frozenset()
        self.letras_niebla = frozenset()
        self.inventario_escape.reset_pregunta()
        self._tiempo_agotado_marcado = False

    def _indice_pool_pregunta(self, pregunta: Pregunta) -> int | None:
        try:
            return self.pool.index(pregunta)
        except ValueError:
            return None

    def _limite_tiempo_pregunta_efectivo(self) -> int | None:
        if not self.tiempo_pregunta_limite:
            return None
        return self.tiempo_pregunta_limite + self.inventario_escape.tiempo_extra_seg

    def _elegir_puerta(self, indice: int) -> None:
        if self.fase != "puertas":
            return
        self.puerta_actual = self.puertas_actuales[indice]
        puerta = self.puerta_actual
        mods = puerta.modificadores

        if mods.sin_pregunta:
            if puerta_es_tienda(puerta):
                if not puede_visitar_tienda_escape(
                    self.sala_idx + 1,
                    self.estado,
                    vidas_max=self.vidas_max,
                ):
                    self.feedback_mensaje = mensaje_feedback_puerta_sin_pregunta(puerta)
                    self.feedback_solucion = None
                    self.feedback_ok = True
                    self.desafio_fallo = False
                    self._bonus_completar_mostrado = False
                    self.fase = "feedback"
                    self.inicio_feedback = marcar_inicio_feedback()
                    return
                self.desafio_fallo = False
                self._bonus_completar_mostrado = False
                self.mensaje_tienda = ""
                self._articulos_comprados_visita = set()
                self._articulos_tienda = seleccionar_articulos_tienda_visita(
                    self.sala_idx + 1,
                    rng=self.rng,
                    estado=self.estado,
                    vidas_max=self.vidas_max,
                )
                if not any(self._articulos_tienda):
                    self.feedback_mensaje = mensaje_feedback_puerta_sin_pregunta(puerta)
                    self.feedback_solucion = None
                    self.feedback_ok = True
                    self.fase = "feedback"
                    self.inicio_feedback = marcar_inicio_feedback()
                    return
                self.fase = "tienda"
                self._reconstruir_tienda()
                return
            self.feedback_mensaje = mensaje_feedback_puerta_sin_pregunta(puerta)
            self.feedback_solucion = None
            self.feedback_ok = True
            self.desafio_fallo = False
            self._bonus_completar_mostrado = False
            self.fase = "feedback"
            self.inicio_feedback = marcar_inicio_feedback()
            return

        self._bonus_completar_mostrado = False
        self._aplicar_reglas_desafio(puerta)
        self.inventario_escape.reset_pregunta()
        self.preguntas_desafio = seleccionar_preguntas_desafio(
            self.pool,
            puerta,
            numero_sala=self.sala_idx + 1,
            n_salas=self.config.n_salas,
            rng=self.rng,
            usadas=self._usadas_pool,
        )
        self.pregunta_idx = 0
        self.desafio_fallo = False
        self.fase = "pregunta"
        self.inicio_pregunta = time.monotonic()
        self._reconstruir_opciones()
        self._reconstruir_inventario_botones()

    def _items_inventario_usables(self) -> list[tuple[str, int]]:
        return [
            (aid, self.inventario_escape.cantidad(aid))
            for aid in sorted(self.inventario_escape.inventario.keys())
            if self.inventario_escape.cantidad(aid) > 0
            and puede_usar_powerup_en_pregunta(
                aid, self.inventario_escape.powerups_usados_en_pregunta
            )
            is None
        ]

    def _etiqueta_y_ancho_boton_inventario(self, aid: str, cant: int) -> tuple[str, int]:
        try:
            art = articulo_tienda_por_id(aid)
            emoji = art.emoji
            nombre = art.nombre
        except KeyError:
            emoji = emoji_powerup(aid)
            nombre = etiqueta_powerup(aid)
        etiqueta_btn = prefijar_emoji(f"{nombre} ({cant})", emoji)
        ancho = min(
            _INV_ANCHO_MAX,
            max(
                _INV_ANCHO_MIN,
                medir_etiqueta_boton(etiqueta_btn, self.fuentes["pequena"])[0]
                + _INV_PADDING_ETIQUETA,
            ),
        )
        return etiqueta_btn, ancho

    def _filas_layout_inventario(
        self,
    ) -> list[list[tuple[str, int, int, str]]]:
        """Filas de (id, cantidad, ancho, etiqueta) sin desbordar el ancho útil."""
        items = self._items_inventario_usables()
        if not items:
            return []
        metas: list[tuple[str, int, int, str]] = []
        for aid, cant in items:
            etiqueta, ancho = self._etiqueta_y_ancho_boton_inventario(aid, cant)
            metas.append((aid, cant, ancho, etiqueta))
        filas_anchos = empaquetar_filas_inventario(
            [m[2] for m in metas],
            ancho_disponible=ANCHO - 2 * MARGEN,
            gap=_INV_GAP,
        )
        filas: list[list[tuple[str, int, int, str]]] = []
        cursor = 0
        for fila_anchos in filas_anchos:
            n = len(fila_anchos)
            filas.append(metas[cursor : cursor + n])
            cursor += n
        return filas

    def _altura_banda_inventario(self) -> int:
        n_filas = len(self._filas_layout_inventario())
        if n_filas <= 0:
            return 0
        return n_filas * _INV_FILA_ALTURA + _INV_PADDING_BANDA

    def _y_banda_inventario(self) -> int:
        altura = self._altura_banda_inventario()
        if altura <= 0:
            return ALTO - MARGEN_INF_PARTIDA
        return ALTO - MARGEN_INF_PARTIDA - altura

    def _reconstruir_inventario_botones(self) -> None:
        self.botones_inventario = []
        if self.fase != "pregunta":
            return
        filas = self._filas_layout_inventario()
        if not filas:
            return
        y = self._y_banda_inventario()
        for fila in filas:
            x = MARGEN
            for aid, _cant, ancho, etiqueta_btn in fila:
                rect = pygame.Rect(x, y, ancho, _INV_ALTO_BOTON)
                self.botones_inventario.append(
                    Boton(
                        etiqueta_btn,
                        rect,
                        capturar(self._usar_objeto_escape, aid),
                        tooltip=descripcion_articulo(aid),
                    )
                )
                x += ancho + _INV_GAP
            y += _INV_FILA_ALTURA

    def _reconstruir_tienda(self) -> None:
        self.botones_tienda = []
        rects = self._rects_cartas_puertas(ARTICULOS_POR_VISITA_TIENDA)
        for i in range(ARTICULOS_POR_VISITA_TIENDA):
            art = self._articulos_tienda[i] if i < len(self._articulos_tienda) else None
            if art is None:
                boton = Boton("", rects[i], lambda: None, mostrar_texto=False)
                boton.activo = False
            else:
                boton = Boton(
                    "",
                    rects[i],
                    capturar(self._comprar_tienda, art.id),
                    mostrar_texto=False,
                )
                boton.activo = self._articulo_tienda_comprable(art.id) is None
            self.botones_tienda.append(boton)
        y_salir = self.Y_CARTAS_PUERTAS + self.ALTO_CARTA_PUERTA + 20
        ancho = ANCHO - 2 * MARGEN
        self.boton_salir_tienda = Boton(
            "Continuar",
            pygame.Rect(MARGEN, y_salir, ancho, 44),
            self._salir_tienda,
            tooltip="Salir de la tienda y avanzar de sala.",
        )

    def _articulo_tienda_comprable(self, articulo_id: str) -> str | None:
        return articulo_comprable_tienda_escape(
            articulo_id,
            self.estado,
            vidas_max=self.vidas_max,
            comprados_en_visita=self._articulos_comprados_visita,
        )

    def _comprar_tienda(self, articulo_id: str) -> None:
        previo = self._articulo_tienda_comprable(articulo_id)
        if previo:
            self.mensaje_tienda = previo
            return
        err = comprar_articulo(
            self.estado,
            self.inventario_escape,
            articulo_id,
            comprados_en_visita=self._articulos_comprados_visita,
            vidas_max=self.vidas_max,
        )
        if err:
            self.mensaje_tienda = err
            return
        self.mensaje_tienda = ""
        self._articulos_comprados_visita.add(articulo_id)
        self._reconstruir_tienda()

    def _iconos_carta_tienda(self, art) -> tuple[IconoEfectoPuerta, ...]:
        return (
            IconoEfectoPuerta(
                art.emoji,
                art.descripcion,
                CapaIconoEscape.TIENDA,
            ),
        )

    def _lineas_carta_tienda(self, art) -> tuple[str, str, list[str]]:
        detalle = [f"{art.precio} puntos"]
        if art.id in self._articulos_comprados_visita:
            detalle.append("Comprado")
            return art.nombre, art.descripcion, detalle
        if self.estado.puntos_arcade < art.precio:
            detalle.append("Puntos insuficientes.")
        elif es_bonificacion(art.id) and not bonificacion_aplicable(
            art.id, self.estado, vidas_max=self.vidas_max
        ):
            detalle.append("No aplica ahora.")
        return art.nombre, art.descripcion, detalle

    def _dibujar_carta_tienda_vacia(
        self,
        superficie: pygame.Surface,
        rect: pygame.Rect,
    ) -> None:
        dibujar_panel(superficie, rect, color=(32, 32, 32))
        inner = rect.inflate(-20, -20)
        tit = self.fuentes["menu"].render("—", True, (90, 90, 90))
        superficie.blit(tit, tit.get_rect(center=inner.center))

    def _dibujar_carta_tienda(
        self,
        superficie: pygame.Surface,
        art,
        rect: pygame.Rect,
        *,
        hover: bool,
        indice: int,
    ) -> None:
        comprado = art.id in self._articulos_comprados_visita
        comprable = self._articulo_tienda_comprable(art.id) is None
        if comprado or not comprable:
            color = (40, 40, 40)
            color_titulo = (120, 120, 120)
            color_sub = (100, 100, 100)
        else:
            color = self._COLOR_CARTA_HOVER if hover else self._COLOR_CARTA
            color_titulo = self._COLOR_TEXTO_CARTA
            color_sub = self._COLOR_SUBTEXTO_CARTA
        dibujar_panel(superficie, rect, color=color)
        if hover and comprable and not comprado:
            pygame.draw.rect(superficie, COLOR_ACENTO, rect, width=3, border_radius=10)

        inner = rect.inflate(-20, -20)
        y = inner.y
        iconos = self._iconos_carta_tienda(art)
        hover_icono = indice if self._hover_icono_tienda == indice else None
        self._dibujar_fila_iconos(superficie, inner, iconos, hover_idx=hover_icono)
        y += self._ALTO_FILA_ICONOS + 10

        titulo, descripcion, detalle = self._lineas_carta_tienda(art)

        titulo_ui = preparar_texto_ui(titulo)
        tit_surf = self.fuentes["menu"].render(titulo_ui, True, color_titulo)
        tit_rect = tit_surf.get_rect(centerx=inner.centerx, top=y)
        superficie.blit(tit_surf, tit_rect)
        y += tit_surf.get_height() + 8

        alto_desc = min(72, max(36, inner.bottom - y - 100))
        desc_rect = pygame.Rect(inner.x, y, inner.width, alto_desc)
        dibujar_texto_multilinea(
            superficie,
            self.fuentes["pequena"],
            descripcion,
            desc_rect,
            color_sub,
        )
        y = desc_rect.bottom + 12

        pygame.draw.line(
            superficie,
            (200, 210, 225),
            (inner.x, y),
            (inner.right, y),
            1,
        )
        y += 10
        detalle_rect = pygame.Rect(inner.x, y, inner.width, inner.bottom - y)
        dibujar_texto_multilinea(
            superficie,
            self.fuentes["cuerpo"],
            "\n".join(detalle),
            detalle_rect,
            color_titulo,
        )

    def _actualizar_hover_icono_tienda(self, pos: tuple[int, int]) -> None:
        self._hover_icono_tienda = None
        for i, boton in enumerate(self.botones_tienda):
            if not boton.rect.collidepoint(pos):
                continue
            inner = boton.rect.inflate(-20, -20)
            if self._rects_iconos_carta(inner, self._iconos_carta_tienda(self._articulos_tienda[i]))[
                0
            ].collidepoint(pos):
                self._hover_icono_tienda = i
            return

    def _salir_tienda(self) -> None:
        if self._intentar_feedback_bonus_completar():
            return
        self._finalizar_desafio()

    def _usar_objeto_escape(self, articulo_id: str) -> None:
        if self.fase != "pregunta":
            return
        p = self._pregunta_actual()
        if articulo_id in {"skip", "cambio"}:
            err = usar_objeto(articulo_id, self.inventario_escape, p)
            if err:
                self.feedback_mensaje = err
                self.feedback_ok = False
                self.feedback_solucion = None
                self.fase = "feedback"
                self.inicio_feedback = marcar_inicio_feedback()
                return
            if articulo_id == "skip":
                self.pregunta_idx += 1
                if self.pregunta_idx >= len(self.preguntas_desafio):
                    if self._intentar_feedback_bonus_completar():
                        return
                    self._finalizar_desafio()
                    return
                self.inventario_escape.reset_pregunta()
                self.inicio_pregunta = time.monotonic()
                self._tiempo_agotado_marcado = False
                self.fase = "pregunta"
                self._reconstruir_opciones()
                self._reconstruir_inventario_botones()
                return
            indice = self._indice_pool_pregunta(p)
            reemplazo = reemplazar_pregunta_cambio_escape(
                self.pool,
                self.puerta_actual,
                indice_actual=indice,
                numero_sala=self.sala_idx + 1,
                n_salas=self.config.n_salas,
                rng=self.rng,
                usadas=self._usadas_pool,
            )
            if reemplazo is None:
                revocar_powerup_usado(
                    self.inventario_escape.powerups_usados_en_pregunta, "cambio"
                )
                self.inventario_escape.agregar("cambio")
                self.feedback_mensaje = "No hay otra pregunta compatible."
                self.feedback_ok = False
                self.feedback_solucion = None
                self.fase = "feedback"
                self.inicio_feedback = marcar_inicio_feedback()
                return
            self.preguntas_desafio[self.pregunta_idx] = reemplazo
            self.inventario_escape.reiniciar_slot_pregunta()
            self.inicio_pregunta = time.monotonic()
            self._tiempo_agotado_marcado = False
            self.fase = "pregunta"
            self._reconstruir_opciones()
            self._reconstruir_inventario_botones()
            return

        err = usar_objeto(
            articulo_id,
            self.inventario_escape,
            p,
        )
        if err:
            self.feedback_mensaje = err
            self.feedback_ok = False
            self.feedback_solucion = None
            self.fase = "feedback"
            self.inicio_feedback = marcar_inicio_feedback()
            return
        if articulo_id in {"fifty_fifty", "bomba"}:
            self._reconstruir_opciones()
        self._reconstruir_inventario_botones()

    def _pregunta_actual(self) -> Pregunta:
        return self.preguntas_desafio[self.pregunta_idx]

    def _y_inicio_opciones(self) -> int:
        return Y_PANEL_PREGUNTA + ALTO_PANEL_PREGUNTA + GAP_TRAS_PANEL_PARTIDA

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
        limite = self._y_banda_inventario() - 6
        alto_est = self.fuentes["subtitulo"].get_height() + 8
        if y + alto_est > limite:
            y = max(self._y_fin_opciones() + 4, limite - alto_est)
        return y

    def _reconstruir_opciones(self) -> None:
        p = self._pregunta_actual()
        mods = self.puerta_actual.modificadores if self.puerta_actual else None
        ocultas_niebla: frozenset[str] = frozenset()
        if mods and mods.opciones_ocultas:
            ocultas_niebla = letras_ocultas_niebla(
                p,
                min(mods.opciones_ocultas, 1),
                rng=self.rng,
            )
        self.letras_niebla = ocultas_niebla
        self.letras_ocultas = self.inventario_escape.letras_ocultas_powerup
        self._presentacion_opciones = presentacion_opciones_pantalla(
            p, rng=self.rng
        )
        self.botones_opcion = []
        y = self._y_inicio_opciones()
        for etiqueta, texto_opc, letra_ds in self._presentacion_opciones.filas:
            texto_visible = texto_opcion_visible_pantalla(
                texto_opc,
                letra_ds,
                letras_eliminadas=self.letras_ocultas,
                letras_niebla=self.letras_niebla,
            )
            if texto_visible is None:
                continue
            rect = pygame.Rect(MARGEN, y, ANCHO - 2 * MARGEN, ALTO_OPCION_PARTIDA)
            self.botones_opcion.append(
                BotonOpcion(
                    etiqueta,
                    texto_visible,
                    rect,
                    capturar(self._responder, etiqueta),
                )
            )
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
        from Comun.generador_examen_historia import cargar_estadisticas_historicas

        victoria = self._resultado == "victoria" and not abandonado
        derrota = self._resultado == "derrota" and not abandonado
        cierre = None
        if self.registros:
            stats = cargar_estadisticas_historicas(
                materias_validas=set(self.datos.materias_meta)
            )
            if abandonado:
                titulo_txt = f"ABANDONO — {self.preset.nombre}"
            elif victoria:
                titulo_txt = f"COMPLETADO — {self.preset.nombre}"
            elif derrota:
                titulo_txt = f"DERROTA — {self.preset.nombre}"
            else:
                titulo_txt = f"FIN — {self.preset.nombre}"
            cierre = CierreInformePartida(
                registros=list(self.registros),
                titulo=titulo_txt,
                total_previsto=self.total_previsto,
                prefijo="escape",
                meta=meta_cierre_historia(
                    preset_id=self.preset.id,
                    preset_nombre=self.preset.nombre,
                    perfil=self.preset.perfil,
                    materias=list(self.materias_pool),
                    n_preguntas=self.total_previsto,
                ),
                stats_historicas=stats,
                abandonado=abandonado,
            )
        if abandonado:
            titulo_pantalla_fin = f"ABANDONO — {self.preset.nombre[:40]}"
        elif victoria:
            titulo_pantalla_fin = f"COMPLETADO — {self.preset.nombre[:40]}"
        elif derrota:
            titulo_pantalla_fin = f"DERROTA — {self.preset.nombre[:40]}"
        else:
            titulo_pantalla_fin = f"FIN — {self.preset.nombre[:44]}"
        self.ir_a(
            ResumenHistoriaPartida(
                self.estado,
                self.total_previsto,
                self.preset,
                self.ir_a,
                self.datos,
                self.salir_app,
                cierre_informe=cierre,
                titulo=titulo_pantalla_fin,
                navegacion_fin=self.navegacion_fin,
            )
        )

    def _tras_respuesta(self, resultado: ResultadoRespuesta) -> None:
        p = self._pregunta_actual()
        escudo = (
            not resultado.acierto
            and not resultado.tiempo_agotado
            and self.inventario_escape.escudo_activo
        )
        vidas_antes = self.estado.vidas_restantes if escudo else None
        feedback = evaluar_respuesta(p, self.estado, resultado)
        if escudo and vidas_antes is not None:
            self.estado.vidas_restantes = vidas_antes
            self.inventario_escape.escudo_activo = False
            feedback = replace(feedback, mensaje="Escudo: no pierdes vida.")
        if resultado.acierto and not resultado.tiempo_agotado:
            bonus_amuleto = self.inventario_escape.bonus_proximo_acierto
            if bonus_amuleto:
                self.estado.puntos_arcade, _ = sumar_puntos_arcade(
                    self.estado.puntos_arcade, bonus_amuleto
                )
                self.inventario_escape.bonus_proximo_acierto = 0
        if (
            resultado.acierto
            and not resultado.tiempo_agotado
            and self._mult_puntos_desafio > 1
            and self.estado.reglas.sistema_puntuacion == SistemaPuntuacion.ARCADE
        ):
            base = calcular_puntos_arcade(p.dificultad, True)
            extra = puntos_extra_mult_desafio(
                base, acierto=True, mult=self._mult_puntos_desafio
            )
            if extra:
                self.estado.puntos_arcade, _ = sumar_puntos_arcade(
                    self.estado.puntos_arcade, extra
                )
            feedback = replace(
                feedback,
                mensaje=mensaje_acierto_desafio(
                    base, mult=self._mult_puntos_desafio
                ),
            )
        self._registrar_respuesta(p, resultado)
        if not resultado.acierto or resultado.tiempo_agotado:
            self.desafio_fallo = True
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
        self._tras_respuesta(
            ResultadoRespuesta(acierto=acierto, respuesta=letra_dataset)
        )

    def _avanzar_sala(self) -> None:
        self.sala_idx += 1
        if self.sala_idx >= len(self.config.salas):
            self._resultado = "victoria"
            self._fin_partida()
            return
        self._preparar_puertas()

    def _finalizar_desafio(self) -> None:
        self.estado.reglas = self.reglas_base
        self.tiempo_pregunta_limite = None
        if self.estado.reglas.tiene_vidas() and (self.estado.vidas_restantes or 0) <= 0:
            self._resultado = "derrota"
            self._fin_partida()
            return
        self._avanzar_sala()

    def _intentar_feedback_bonus_completar(self) -> bool:
        """Muestra recompensa de puerta superada antes de avanzar de sala."""
        if (
            self.puerta_actual is None
            or self.desafio_fallo
            or self._bonus_completar_mostrado
        ):
            return False
        bonus = bonificacion_completar_escape(self.puerta_actual)
        if not bonus.tiene_recompensa:
            return False
        _, self.vidas_max = aplicar_bonificacion_completar(
            self.estado,
            bonus,
            vidas_max=self.vidas_max,
        )
        for pid, cant in bonus.powerups:
            aplicar_loot(
                pid,
                cant,
                self.estado,
                self.inventario_escape,
                vidas_max=self.vidas_max,
            )
        self._bonus_completar_mostrado = True
        self.feedback_mensaje = bonus.mensaje
        self.feedback_solucion = None
        self.feedback_ok = True
        self.fase = "feedback"
        self.inicio_feedback = marcar_inicio_feedback()
        return True

    def _continuar_tras_feedback(self) -> None:
        if self.fase != "feedback":
            return
        if self.puerta_actual is None or self.puerta_actual.modificadores.sin_pregunta:
            if (
                not self._bonus_completar_mostrado
                and self._intentar_feedback_bonus_completar()
            ):
                return
            self._finalizar_desafio()
            return
        if (
            not self.desafio_fallo
            and self.pregunta_idx < len(self.preguntas_desafio) - 1
        ):
            self.pregunta_idx += 1
            self.fase = "pregunta"
            self.inicio_pregunta = time.monotonic()
            self._tiempo_agotado_marcado = False
            self.inventario_escape.reset_pregunta()
            self.feedback_mensaje = ""
            self.feedback_solucion = None
            self.feedback_ok = False
            self._reconstruir_opciones()
            self._reconstruir_inventario_botones()
            return
        if (
            not self.desafio_fallo
            and self.pregunta_idx >= len(self.preguntas_desafio) - 1
            and not self._bonus_completar_mostrado
            and self._intentar_feedback_bonus_completar()
        ):
            return
        self._finalizar_desafio()

    def actualizar(self) -> Pantalla | None:
        if self.fase == "pregunta" and not self._tiempo_agotado_marcado:
            rest_puerta = self.estado.tiempo_total_restante()
            if rest_puerta is not None and rest_puerta <= 0:
                self._tiempo_agotado_marcado = True
                self._tras_respuesta(
                    ResultadoRespuesta(acierto=False, respuesta="", tiempo_agotado=True)
                )
                return None
            if (
                self.tiempo_pregunta_limite
                and self._limite_tiempo_pregunta_efectivo() is not None
                and time.monotonic() - self.inicio_pregunta
                >= self._limite_tiempo_pregunta_efectivo()
            ):
                self._tiempo_agotado_marcado = True
                self._tras_respuesta(
                    ResultadoRespuesta(acierto=False, respuesta="", tiempo_agotado=True)
                )
                return None
        if self.fase == "feedback":
            if feedback_debe_avanzar(
                self.inicio_feedback,
                solucion=self.feedback_solucion,
                acierto=self.feedback_ok,
            ):
                self._continuar_tras_feedback()
            return None
        return None

    def titulo_pausa(self) -> str:
        return f"{self.preset.nombre} · {self._linea_estado_actual()}"

    def _botones_ui(self) -> list:
        return [self.boton_abandonar]

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
        dibujar_estado_partida_en_barra(
            superficie,
            estado=self.estado,
            progreso="",
            fuentes=self.fuentes,
            x_centro_min=x_centro_min,
            x_centro_max=x_centro_max,
            y=y_estado,
            **self._kwargs_barra_estado(),
        )
        pygame.draw.line(
            superficie,
            (50, 72, 110),
            (MARGEN, ALTURA_BARRA_PARTIDA),
            (ANCHO - MARGEN, ALTURA_BARRA_PARTIDA),
            1,
        )
        self.boton_abandonar.dibujar(superficie, fuente)

    def _dibujar_puertas(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        self._dibujar_barra_superior(superficie)
        sala = self._sala_actual()
        titulo = titulo_pantalla(sala.nombre if sala else "Escape room")
        tit = self.fuentes["titulo"].render(titulo, True, COLOR_TITULO)
        superficie.blit(tit, tit.get_rect(midtop=(ANCHO // 2, self.Y_TITULO_SALA)))
        subt = self.fuentes["menu"].render("Elige una puerta:", True, COLOR_TEXTO_PANEL)
        superficie.blit(subt, subt.get_rect(midtop=(ANCHO // 2, self.Y_SUBTITULO_PUERTAS)))
        for i, boton in enumerate(self.botones_puerta):
            self._dibujar_carta_puerta(
            superficie,
                self.puertas_actuales[i],
                boton.rect,
                hover=boton.hover,
                indice=i,
            )
        self._dibujar_tooltip_icono_puerta(superficie)
        dibujar_tooltips_botones(superficie, self.fuentes["pequena"], self._botones_ui())

    def _dibujar_tooltip_icono_puerta(self, superficie: pygame.Surface) -> None:
        if not self._hover_icono:
            return
        i, j = self._hover_icono
        if i >= len(self.botones_puerta) or j >= len(self._iconos_puerta[i]):
            return
        inner = self.botones_puerta[i].rect.inflate(-20, -20)
        rects = self._rects_iconos_carta(inner, self._iconos_puerta[i])
        if j >= len(rects):
            return
        tip = self._iconos_puerta[i][j].tooltip
        dibujar_tooltip(superficie, self.fuentes["pequena"], rects[j], tip)

    def _dibujar_tienda(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        self._dibujar_barra_superior(superficie)
        sala = self._sala_actual()
        titulo = titulo_pantalla(f"{sala.nombre if sala else 'Escape room'} · Tienda")
        tit = self.fuentes["titulo"].render(titulo, True, COLOR_TITULO)
        superficie.blit(tit, tit.get_rect(midtop=(ANCHO // 2, self.Y_TITULO_SALA)))
        subt = self.fuentes["menu"].render(
            f"Puntos arcade: {self.estado.puntos_arcade}",
            True,
            COLOR_TEXTO_PANEL,
        )
        superficie.blit(subt, subt.get_rect(midtop=(ANCHO // 2, self.Y_SUBTITULO_PUERTAS)))
        intro = self.fuentes["pequena"].render(
            linea_detalle_tienda_puerta(),
            True,
            self._COLOR_SUBTEXTO_CARTA,
        )
        superficie.blit(intro, intro.get_rect(midtop=(ANCHO // 2, self.Y_SUBTITULO_PUERTAS + 36)))
        for i, boton in enumerate(self.botones_tienda):
            art = self._articulos_tienda[i] if i < len(self._articulos_tienda) else None
            if art is None:
                self._dibujar_carta_tienda_vacia(superficie, boton.rect)
            else:
                self._dibujar_carta_tienda(
                    superficie,
                    art,
                    boton.rect,
                    hover=boton.hover,
                    indice=i,
                )
        if self._hover_icono_tienda is not None:
            i = self._hover_icono_tienda
            if i < len(self.botones_tienda) and i < len(self._articulos_tienda):
                art = self._articulos_tienda[i]
                if art is not None:
                    inner = self.botones_tienda[i].rect.inflate(-20, -20)
                    rects = self._rects_iconos_carta(
                        inner, self._iconos_carta_tienda(art)
                    )
                    if rects:
                        dibujar_tooltip(
                            superficie,
                            self.fuentes["pequena"],
                            rects[0],
                            art.descripcion,
                        )
        if self.boton_salir_tienda:
            self.boton_salir_tienda.dibujar(superficie, self.fuentes["menu"])
        if self.mensaje_tienda:
            msg = self.fuentes["cuerpo"].render(self.mensaje_tienda, True, COLOR_ACENTO)
            superficie.blit(
                msg,
                msg.get_rect(midtop=(ANCHO // 2, self.Y_CARTAS_PUERTAS + self.ALTO_CARTA_PUERTA + 72)),
            )
        tips: list = []
        if self.boton_salir_tienda:
            tips.append(self.boton_salir_tienda)
        dibujar_tooltips_botones(superficie, self.fuentes["pequena"], tips + self._botones_ui())

    def _dibujar_feedback_sin_pregunta(self, superficie: pygame.Surface) -> None:
        """Tras descanso u otro desafío sin bloque de preguntas."""
        superficie.fill(COLOR_FONDO)
        self._dibujar_barra_superior(superficie)
        sala = self._sala_actual()
        titulo = titulo_pantalla(sala.nombre if sala else "Escape room")
        tit = self.fuentes["titulo"].render(titulo, True, COLOR_TITULO)
        superficie.blit(tit, tit.get_rect(midtop=(ANCHO // 2, self.Y_TITULO_SALA)))
        dibujar_feedback_partida(
            superficie,
            self.fuentes,
            mensaje=self.feedback_mensaje,
            solucion=self.feedback_solucion,
            acierto=self.feedback_ok,
            y_mensaje=self.Y_TITULO_SALA + 72,
        )
        dibujar_tooltips_botones(superficie, self.fuentes["pequena"], self._botones_ui())

    def _dibujar_pregunta(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        self._dibujar_barra_superior(superficie)
        sala = self._sala_actual()
        p = self._pregunta_actual()
        puerta = self.puerta_actual
        panel = pygame.Rect(MARGEN, Y_PANEL_PREGUNTA, ANCHO - 2 * MARGEN, ALTO_PANEL_PREGUNTA)
        dibujar_panel(superficie, panel)
        if puerta:
            foco_txt = puerta.evento.etiqueta_foco or p.materia
            meta_txt = (
                f"{emoji_tipo_puerta_escape(puerta.evento)} {puerta.evento.nombre} · "
                f"{foco_txt} · {p.tipo} / {p.dificultad}"
            )
        else:
            meta_txt = f"{sala.nombre if sala else p.materia} · {p.tipo} / {p.dificultad}"
        self._dibujar_meta_pregunta(superficie, meta_txt, panel.x + 12, panel.y + 10)
        dibujar_texto_multilinea(
            superficie,
            self.fuentes["cuerpo"],
            p.texto,
            pygame.Rect(panel.x + 8, panel.y + 36, panel.width - 16, panel.height - 44),
            COLOR_TITULO,
        )
        for boton in self.botones_opcion:
            boton.dibujar(superficie, self.fuentes["opcion"])
        if self.fase == "pregunta":
            for boton in self.botones_inventario:
                boton.dibujar(superficie, self.fuentes["pequena"])
        if self.fase == "feedback":
            dibujar_feedback_partida(
                superficie,
                self.fuentes,
                mensaje=self.feedback_mensaje,
                solucion=self.feedback_solucion,
                acierto=self.feedback_ok,
                y_mensaje=self._y_mensaje_feedback(),
            )
        tips = list(self._botones_ui())
        if self.fase == "pregunta":
            tips.extend(self.botones_inventario)
        dibujar_tooltips_botones(superficie, self.fuentes["pequena"], tips)

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEMOTION:
            for boton in self._botones_ui():
                boton.actualizar_hover(evento.pos)
            if self.fase == "puertas":
                for boton in self.botones_puerta:
                    boton.actualizar_hover(evento.pos)
                self._actualizar_hover_iconos(evento.pos)
            elif self.fase == "tienda":
                for boton in self.botones_tienda:
                    boton.actualizar_hover(evento.pos)
                self._actualizar_hover_icono_tienda(evento.pos)
                if self.boton_salir_tienda:
                    self.boton_salir_tienda.actualizar_hover(evento.pos)
            elif self.fase == "pregunta":
                for boton in self.botones_opcion:
                    boton.actualizar_hover(evento.pos)
                for boton in self.botones_inventario:
                    boton.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if self.boton_abandonar.manejar_clic(evento.pos, evento.button):
                        return None
            if self.fase == "puertas":
                for boton in self.botones_puerta:
                    if boton.manejar_clic(evento.pos, evento.button):
                        break
            elif self.fase == "tienda":
                for boton in self.botones_tienda:
                    if boton.manejar_clic(evento.pos, evento.button):
                        break
                if self.boton_salir_tienda and self.boton_salir_tienda.manejar_clic(
                    evento.pos, evento.button
                ):
                    pass
            elif self.fase == "pregunta":
                for boton in self.botones_inventario:
                    if boton.manejar_clic(evento.pos, evento.button):
                        break
                else:
                    for boton in self.botones_opcion:
                        if boton.manejar_clic(evento.pos, evento.button):
                            break
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        if self.fase == "puertas":
            self._dibujar_puertas(superficie)
        elif self.fase == "tienda":
            self._dibujar_tienda(superficie)
        elif self.fase == "feedback" and not self.preguntas_desafio:
            self._dibujar_feedback_sin_pregunta(superficie)
        else:
            self._dibujar_pregunta(superficie)