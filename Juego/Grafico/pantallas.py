#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pantallas pygame del cuestionario (navegación por ratón)."""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import replace
from typing import TYPE_CHECKING

import pygame

from Comun.dificultad import dificultad_global_actual, max_complejidad_pool
from Comun.modelos import BancoPreguntas, Pregunta
from Comun.motor_nucleo import (
    EstadoPartida,
    ResultadoRespuesta,
    evaluar_respuesta,
    linea_estado,
)
from Comun.politica_reglas import validar_reglas
from Grafico.modo_libre import cargar_pool_banco, etiqueta_subfiltro_visible
from Comun.pool_libre import (
    crear_estado_seleccion,
    elegir_indice_siguiente,
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
from Comun.reglas_partida import ReglasPartida, SistemaPuntuacion, formatear_resultado_puntuacion, preset_libre_arcade
from Comun.compatibilidad_reglas_libre import (
    OpcionesReglasLibre,
    normalizar_vidas_y_sistema,
    opciones_reglas_libre,
)
from Grafico.tema import ALTO, ANCHO, COLOR_ACENTO, COLOR_AVISO, COLOR_ERROR, COLOR_FONDO, COLOR_OK, COLOR_TEXTO, COLOR_TITULO, MARGEN, crear_fuentes
from Grafico.texto import preparar_texto_ui
from Grafico.ui import (
    Boton,
    BotonMarcable,
    BotonOpcion,
    CampoEntero,
    CampoTexto,
    _fuente_ajustada,
    cuadricula_rects,
    dibujar_panel,
    dibujar_texto_multilinea,
    fila_rects_centrada,
)

if TYPE_CHECKING:
    from Grafico.app import DatosJuego

Y_WIZARD_TITULO = 46
Y_WIZARD_PASO = 78
Y_WIZARD_CONTENIDO = 96

# Reservado para los iconos fijos de pausa/feedback (ver Grafico/app.py).
MARGEN_ICONOS_FIJOS = 112
ALTURA_BARRA_PARTIDA = 52
Y_PANEL_PREGUNTA = ALTURA_BARRA_PARTIDA + 14
ALTO_PANEL_PREGUNTA = 150
ALTO_OPCION_PARTIDA = 64
SEP_OPCIONES_PARTIDA = 8
ALTO_BARRA_PROGRESO_PARTIDA = 8
GAP_TRAS_PANEL_PARTIDA = 12
GAP_TRAS_BARRA_PROGRESO = 10
MARGEN_INF_PARTIDA = 12
ALTO_BOTON_CONTINUAR_PARTIDA = 44


def dibujar_cabecera_wizard_modo_libre(
    superficie: pygame.Surface,
    fuentes: dict[str, pygame.font.Font],
    paso_texto: str,
) -> None:
    titulo = fuentes["titulo"].render("MODO LIBRE", True, COLOR_TITULO)
    superficie.blit(titulo, titulo.get_rect(center=(ANCHO // 2, Y_WIZARD_TITULO)))
    paso = fuentes["pequena"].render(paso_texto, True, COLOR_TEXTO)
    superficie.blit(paso, paso.get_rect(center=(ANCHO // 2, Y_WIZARD_PASO)))


class Pantalla:
    def titulo_pausa(self) -> str:
        return "Pantalla actual"

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        return None

    def actualizar(self) -> Pantalla | None:
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        raise NotImplementedError

    def dibujar_cabecera(self, superficie: pygame.Surface) -> None:
        """Solo cabecera (opción 2 del menú de pausa, como en consola)."""
        self.dibujar(superficie)


class PantallaFeedback(Pantalla):
    """Pantalla informativa del modo feedback (placeholder inicial)."""

    def titulo_pausa(self) -> str:
        return "Modo feedback"

    def __init__(self, volver: Callable[[], None]) -> None:
        self.volver = volver
        self.fuentes = crear_fuentes()
        self.boton_volver = Boton(
            "Volver",
            pygame.Rect(ANCHO // 2 - 110, ALTO - 90, 220, 48),
            self.volver,
        )

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEMOTION:
            self.boton_volver.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            self.boton_volver.manejar_clic(evento.pos, evento.button)
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        titulo = self.fuentes["titulo"].render("MODO FEEDBACK", True, COLOR_TITULO)
        superficie.blit(titulo, titulo.get_rect(center=(ANCHO // 2, 90)))

        panel = pygame.Rect(MARGEN, 170, ANCHO - 2 * MARGEN, 300)
        dibujar_panel(superficie, panel)
        texto = (
            "Aquí irá el modo feedback.\n\n"
            "Idea: después de responder, mostrar explicación y registrar errores "
            "para repetirlos más adelante."
        )
        dibujar_texto_multilinea(
            superficie,
            self.fuentes["cuerpo"],
            texto,
            pygame.Rect(panel.x + 16, panel.y + 16, panel.width - 32, panel.height - 32),
            COLOR_TEXTO,
        )
        self.boton_volver.dibujar(superficie, self.fuentes["menu"])

    def dibujar_cabecera(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        titulo = self.fuentes["titulo"].render("MODO FEEDBACK", True, COLOR_TITULO)
        superficie.blit(titulo, titulo.get_rect(center=(ANCHO // 2, 90)))


class MenuPrincipal(Pantalla):
    OPCIONES = ("Modo libre", "Modo historia", "Modo feedback", "Salir")

    def __init__(
        self,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
    ) -> None:
        self.datos = datos
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.mensaje = (
            f"{datos.num_preguntas} preguntas · {datos.num_materias} materias"
        )
        self.fuentes = crear_fuentes()
        self.botones = self._crear_botones()

    def _crear_botones(self) -> list[Boton]:
        botones: list[Boton] = []
        ancho, alto = 420, 48
        x = (ANCHO - ancho) // 2
        y0 = 250
        for i, etiqueta in enumerate(self.OPCIONES):
            y = y0 + i * (alto + 14)
            botones.append(
                Boton(
                    etiqueta,
                    pygame.Rect(x, y, ancho, alto),
                    lambda e=etiqueta: self._al_pulsar(e),
                )
            )
        return botones

    def _al_pulsar(self, etiqueta: str) -> None:
        if etiqueta == "Salir":
            self.salir_app()
            return
        if etiqueta == "Modo libre":
            self.ir_a(ConfigModoLibrePaso1(self.datos, self.ir_a, self.salir_app))
            return
        if etiqueta == "Modo feedback":
            # Misma acción lógica que el icono de feedback:
            # abrir la pantalla de feedback y volver a este menú al salir.
            self.ir_a(
                PantallaFeedback(
                    lambda: self.ir_a(MenuPrincipal(self.datos, self.ir_a, self.salir_app))
                )
            )
            return
        self.mensaje = f"«{etiqueta}» — disponible próximamente."

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEMOTION:
            for boton in self.botones:
                boton.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            for boton in self.botones:
                boton.manejar_clic(evento.pos, evento.button)
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        titulo = self.fuentes["titulo"].render("CUESTIONARIO MATCAD", True, COLOR_TITULO)
        superficie.blit(titulo, titulo.get_rect(center=(ANCHO // 2, 110)))
        info = self.fuentes["cuerpo"].render(self.mensaje, True, COLOR_TEXTO)
        superficie.blit(info, info.get_rect(center=(ANCHO // 2, 175)))
        for boton in self.botones:
            boton.dibujar(superficie, self.fuentes["menu"])
        pie = self.fuentes["pie"].render("Haz clic en una opción", True, COLOR_TEXTO)
        superficie.blit(pie, pie.get_rect(center=(ANCHO // 2, ALTO - 56)))

    def titulo_pausa(self) -> str:
        return "Menú principal"

    def dibujar_cabecera(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        titulo = self.fuentes["titulo"].render("CUESTIONARIO MATCAD", True, COLOR_TITULO)
        superficie.blit(titulo, titulo.get_rect(center=(ANCHO // 2, 110)))
        info = self.fuentes["cuerpo"].render(self.mensaje, True, COLOR_TEXTO)
        superficie.blit(info, info.get_rect(center=(ANCHO // 2, 175)))


class ConfigModoLibrePaso1(Pantalla):
    """Paso 1: nombre, banco, infinito y tamaño de partida."""

    OPCIONES_BANCO = (
        (BancoPreguntas.DATASET, "Modo seguro"),
        (BancoPreguntas.PLANTILLAS_TODO, "Todo + beta"),
        (BancoPreguntas.PLANTILLAS_EXTRA, "Solo plantillas"),
    )
    Y_NOMBRE_LBL = 132
    Y_CAMPO = 162
    Y_BANCO_LBL = 234
    Y_BANCO_BTN = 262
    Y_INFINITO = 364
    Y_TOTAL_LBL = 428
    Y_TOTAL_CAMPO = 456
    Y_SIGUIENTE = 558
    Y_VOLVER = 626

    def __init__(
        self,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
        *,
        nombre_inicial: str = "",
        banco_inicial: BancoPreguntas = BancoPreguntas.DATASET,
        modo_infinito_inicial: bool = False,
        total_inicial: int = 10,
    ) -> None:
        self.datos = datos
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.fuentes = crear_fuentes()
        self.total_elegido = total_inicial
        self.modo_infinito = modo_infinito_inicial
        self.banco_elegido = banco_inicial
        self.mensaje = ""
        self.campo_nombre = CampoTexto(
            pygame.Rect(MARGEN + 40, self.Y_CAMPO, ANCHO - 2 * MARGEN - 80, 44),
            texto_inicial=nombre_inicial,
            placeholder="Nombre del jugador",
        )
        self.botones_banco: list[BotonMarcable] = []
        rects_banco = fila_rects_centrada(
            len(self.OPCIONES_BANCO),
            ancho_item=230,
            alto_item=52,
            separacion=24,
            y=self.Y_BANCO_BTN,
            ancho_pantalla=ANCHO,
        )
        for rect, (banco, etiqueta) in zip(rects_banco, self.OPCIONES_BANCO, strict=True):
            btn = BotonMarcable(
                etiqueta,
                rect,
                lambda chosen=banco: self._elegir_banco(chosen),
            )
            btn.banco = banco  # type: ignore[attr-defined]
            self.botones_banco.append(btn)
        self._actualizar_seleccion_banco()

        self.boton_infinito = BotonMarcable(
            "Modo infinito",
            pygame.Rect(ANCHO // 2 - 150, self.Y_INFINITO, 300, 44),
            self._toggle_modo_infinito,
            seleccionado=self.modo_infinito,
        )
        self.campo_total = CampoEntero(
            pygame.Rect(ANCHO // 2 - 80, self.Y_TOTAL_CAMPO, 160, 44),
            texto_inicial=str(total_inicial),
            placeholder="10",
            minimo=1,
            maximo=999,
        )
        self.campo_total.establecer_habilitado(not self.modo_infinito)
        self.boton_siguiente = Boton(
            "Siguiente",
            pygame.Rect(ANCHO // 2 - 130, self.Y_SIGUIENTE, 260, 52),
            self._siguiente,
        )
        self.boton_volver = Boton(
            "Volver al menú",
            pygame.Rect(ANCHO // 2 - 130, self.Y_VOLVER, 260, 48),
            lambda: self.ir_a(MenuPrincipal(datos, ir_a, salir_app)),
        )

    def _elegir_banco(self, banco: BancoPreguntas) -> None:
        self.banco_elegido = banco
        self._actualizar_seleccion_banco()

    def _actualizar_seleccion_banco(self) -> None:
        for boton in self.botones_banco:
            banco_btn = getattr(boton, "banco", None)
            boton.seleccionado = banco_btn == self.banco_elegido

    def _toggle_modo_infinito(self) -> None:
        self.modo_infinito = not self.modo_infinito
        self.boton_infinito.seleccionado = self.modo_infinito
        self.campo_total.establecer_habilitado(not self.modo_infinito)
        self.mensaje = ""

    def _siguiente(self) -> None:
        if self.modo_infinito:
            self.total_elegido = 10
        else:
            total = self.campo_total.valor_entero(defecto=10)
            if total is None:
                self.mensaje = "Introduce un número entre 1 y 999."
                return
            self.total_elegido = total
        self.mensaje = ""
        self.ir_a(
            ConfigModoLibrePaso2(
                self.datos,
                self.ir_a,
                self.salir_app,
                nombre=self.campo_nombre.valor(),
                banco_elegido=self.banco_elegido,
                modo_infinito=self.modo_infinito,
                total_elegido=self.total_elegido,
            )
        )

    def _botones_ui(self) -> list[Boton | BotonMarcable]:
        return [
            *self.botones_banco,
            self.boton_infinito,
            self.boton_siguiente,
            self.boton_volver,
        ]

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        self.campo_nombre.manejar_evento(evento)
        self.campo_total.manejar_evento(evento)
        if evento.type == pygame.MOUSEMOTION:
            for boton in self._botones_ui():
                boton.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if self.campo_nombre.manejar_evento(evento):
                return None
            if self.campo_total.manejar_evento(evento):
                return None
            for boton in self._botones_ui():
                if boton.manejar_clic(evento.pos, evento.button):
                    break
        return None

    def _dibujar_cabecera_modo_libre(self, superficie: pygame.Surface) -> None:
        dibujar_cabecera_wizard_modo_libre(
            superficie,
            self.fuentes,
            "Paso 1 de 3 — jugador y partida",
        )

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        self._dibujar_cabecera_modo_libre(superficie)

        etiqueta = self.fuentes["menu"].render("Nombre (teclado):", True, COLOR_TEXTO)
        superficie.blit(etiqueta, (MARGEN + 40, self.Y_NOMBRE_LBL))
        self.campo_nombre.dibujar(superficie, self.fuentes["menu"])

        bank_lbl = self.fuentes["menu"].render("Banco de datos:", True, COLOR_TEXTO)
        superficie.blit(bank_lbl, bank_lbl.get_rect(center=(ANCHO // 2, self.Y_BANCO_LBL)))
        for boton in self.botones_banco:
            boton.dibujar(superficie, self.fuentes["menu"])

        self.boton_infinito.dibujar(superficie, self.fuentes["menu"])
        if self.modo_infinito:
            subt = self.fuentes["menu"].render(
                "Sin límite de preguntas — abandona cuando quieras",
                True,
                COLOR_TEXTO,
            )
            superficie.blit(subt, subt.get_rect(center=(ANCHO // 2, self.Y_TOTAL_LBL)))
        else:
            subt = self.fuentes["menu"].render("Número de preguntas (teclado):", True, COLOR_TEXTO)
            superficie.blit(subt, subt.get_rect(center=(ANCHO // 2, self.Y_TOTAL_LBL)))
            self.campo_total.dibujar(superficie, self.fuentes["menu"])
        if self.mensaje:
            aviso = self.fuentes["menu"].render(self.mensaje, True, COLOR_AVISO)
            superficie.blit(aviso, aviso.get_rect(center=(ANCHO // 2, 530)))
        self.boton_siguiente.dibujar(superficie, self.fuentes["menu"])
        self.boton_volver.dibujar(superficie, self.fuentes["menu"])

    def titulo_pausa(self) -> str:
        return "Modo libre — paso 1"

    def dibujar_cabecera(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        self._dibujar_cabecera_modo_libre(superficie)


class ConfigModoLibrePaso2(Pantalla):
    """Paso 2: combina vidas, tiempo y puntuación de forma independiente."""

    TIEMPO_NINGUNO = "ninguno"
    TIEMPO_PREGUNTA = "pregunta"
    TIEMPO_TOTAL = "total"

    Y_INICIO_SECCIONES = 118
    ALTURA_FILA = 38
    ALTURA_TEXTO_AYUDA = 16
    GAP_TITULO_FILA = 22
    GAP_FILA_AYUDA = 16
    GAP_AYUDA_OPCION = 18
    GAP_ENTRE_OPCIONES = 16
    GAP_ENTRE_SECCIONES = 20
    GAP_ANTES_RESUMEN = 24
    GAP_NAV_BOTONES = 14
    ANCHO_BTN_TIEMPO = 228
    ANCHO_CAMPO_TIEMPO = 88
    GAP_BTN_CAMPO = 12
    ALTURA_BTN_SIGUIENTE = 48
    Y_SIGUIENTE = 608
    Y_ATRAS = Y_SIGUIENTE + ALTURA_BTN_SIGUIENTE + GAP_NAV_BOTONES
    Y_FIJO_MSG = 200

    def __init__(
        self,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
        *,
        nombre: str,
        banco_elegido: BancoPreguntas,
        modo_infinito: bool,
        total_elegido: int,
        sin_vidas_inicial: bool = False,
        vidas_count_inicial: int = 3,
        modo_tiempo_inicial: str = TIEMPO_NINGUNO,
        tiempo_pregunta_inicial: int = 90,
        tiempo_total_inicial: int = 600,
        sistema_inicial: SistemaPuntuacion = SistemaPuntuacion.ARCADE,
    ) -> None:
        self.datos = datos
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.nombre = nombre
        self.banco_elegido = banco_elegido
        self.modo_infinito = modo_infinito
        self.total_elegido = total_elegido
        self.mensaje = ""
        self.fuentes = crear_fuentes()
        total_bloque = 10 if modo_infinito else total_elegido
        self.contexto = contexto_partida(
            modo_infinito=modo_infinito,
            n_preguntas=total_bloque,
        )
        self.alcance = alcance(self.contexto)
        self.sin_vidas = sin_vidas_inicial
        if self.alcance and not self.alcance.permitir_sin_vidas:
            self.sin_vidas = False
        self.sistema_elegido = sistema_inicial
        self.modo_tiempo = modo_tiempo_inicial
        if self.modo_tiempo not in {
            self.TIEMPO_NINGUNO,
            self.TIEMPO_PREGUNTA,
            self.TIEMPO_TOTAL,
        }:
            self.modo_tiempo = self.TIEMPO_NINGUNO

        min_v = 1
        max_v = 10
        if self.alcance:
            min_v = self.alcance.min_vidas if not self.alcance.permitir_sin_vidas else 0
            max_v = 10 if self.alcance.permitir_sin_vidas else self.alcance.max_vidas

        self.boton_sin_vidas = BotonMarcable(
            "Sin vidas",
            pygame.Rect(ANCHO // 2 - 280, 0, 180, self.ALTURA_FILA),
            self._elegir_sin_vidas,
            seleccionado=self.sin_vidas,
        )
        self.boton_con_vidas = BotonMarcable(
            "Con vidas",
            pygame.Rect(ANCHO // 2 - 80, 0, 150, self.ALTURA_FILA),
            self._elegir_con_vidas,
            seleccionado=not self.sin_vidas,
        )
        self.campo_vidas = CampoEntero(
            pygame.Rect(ANCHO // 2 + 90, 0, 80, self.ALTURA_FILA),
            texto_inicial=str(vidas_count_inicial),
            placeholder="3",
            minimo=min_v if not self.alcance or not self.alcance.permitir_sin_vidas else 1,
            maximo=max_v,
        )

        self.boton_tiempo_ninguno = BotonMarcable(
            "Sin límite de tiempo",
            pygame.Rect(ANCHO // 2 - 160, 0, 320, self.ALTURA_FILA),
            lambda: self._elegir_modo_tiempo(self.TIEMPO_NINGUNO),
            seleccionado=self.modo_tiempo == self.TIEMPO_NINGUNO,
        )
        self.boton_tiempo_pregunta = BotonMarcable(
            "Tiempo por pregunta",
            pygame.Rect(ANCHO // 2 - 280, 0, 220, self.ALTURA_FILA),
            lambda: self._elegir_modo_tiempo(self.TIEMPO_PREGUNTA),
            seleccionado=self.modo_tiempo == self.TIEMPO_PREGUNTA,
        )
        self.campo_tiempo_pregunta = CampoEntero(
            pygame.Rect(ANCHO // 2 + 20, 0, 100, self.ALTURA_FILA),
            texto_inicial=str(tiempo_pregunta_inicial),
            placeholder="90",
            minimo=1,
            maximo=600,
        )
        self.boton_tiempo_total = BotonMarcable(
            "Tiempo total",
            pygame.Rect(ANCHO // 2 - 280, 0, 220, self.ALTURA_FILA),
            lambda: self._elegir_modo_tiempo(self.TIEMPO_TOTAL),
            seleccionado=self.modo_tiempo == self.TIEMPO_TOTAL,
        )
        self.campo_tiempo_total = CampoEntero(
            pygame.Rect(ANCHO // 2 + 20, 0, 100, self.ALTURA_FILA),
            texto_inicial=str(tiempo_total_inicial),
            placeholder="600",
            minimo=1,
            maximo=7200,
        )

        self.botones_sistema: list[BotonMarcable] = []

        self.boton_siguiente = Boton(
            "Siguiente",
            pygame.Rect(ANCHO // 2 - 130, self.Y_SIGUIENTE, 260, self.ALTURA_BTN_SIGUIENTE),
            self._siguiente,
        )
        self.boton_atras = Boton(
            "Atrás",
            pygame.Rect(ANCHO // 2 - 130, self.Y_ATRAS, 260, 44),
            self._atras,
        )
        self._aplicar_layout()
        self._actualizar_estado_ui()

    def _ancho_fila_tiempo(self) -> int:
        return self.ANCHO_BTN_TIEMPO + self.GAP_BTN_CAMPO + self.ANCHO_CAMPO_TIEMPO

    def _colocar_fila_vidas(self, y: int) -> None:
        w_sin, w_con, w_campo = 180, 150, 80
        gap = 12
        con_sin = bool(self.alcance and self.alcance.permitir_sin_vidas)
        total = (w_sin + gap if con_sin else 0) + w_con + gap + w_campo
        x = (ANCHO - total) // 2
        if con_sin:
            self.boton_sin_vidas.rect.update(x, y, w_sin, self.ALTURA_FILA)
            x += w_sin + gap
        self.boton_con_vidas.rect.update(x, y, w_con, self.ALTURA_FILA)
        x += w_con + gap
        self.campo_vidas.rect.update(x, y, w_campo, self.ALTURA_FILA)

    def _colocar_sin_limite_tiempo(self, y: int) -> None:
        ancho = self._ancho_fila_tiempo()
        self.boton_tiempo_ninguno.rect.update(
            (ANCHO - ancho) // 2,
            y,
            ancho,
            self.ALTURA_FILA,
        )

    def _colocar_fila_tiempo(self, y: int, boton: BotonMarcable, campo: CampoEntero) -> None:
        x_btn = (ANCHO - self._ancho_fila_tiempo()) // 2
        boton.rect.update(x_btn, y, self.ANCHO_BTN_TIEMPO, self.ALTURA_FILA)
        campo.rect.update(
            x_btn + self.ANCHO_BTN_TIEMPO + self.GAP_BTN_CAMPO,
            y,
            self.ANCHO_CAMPO_TIEMPO,
            self.ALTURA_FILA,
        )

    def _tiene_seccion_tiempo(self) -> bool:
        return bool(
            self.alcance
            and (
                self.alcance.permitir_tiempo_pregunta
                or self.alcance.permitir_tiempo_total
            )
        )

    def _aplicar_layout(self) -> None:
        y = self.Y_INICIO_SECCIONES
        self._y_vidas_titulo = y
        y += self.GAP_TITULO_FILA
        self._y_vidas_fila = y
        self._colocar_fila_vidas(y)
        y += self.ALTURA_FILA + self.GAP_FILA_AYUDA
        self._y_vidas_ayuda = y
        y += self.ALTURA_TEXTO_AYUDA + self.GAP_ENTRE_SECCIONES

        if self._tiene_seccion_tiempo():
            self._y_tiempo_titulo = y
            y += self.GAP_TITULO_FILA
            self._y_tiempo_sin = y
            self._colocar_sin_limite_tiempo(y)
            y += self.ALTURA_FILA + self.GAP_FILA_AYUDA
            self._y_tiempo_ayuda = y
            y += self.ALTURA_TEXTO_AYUDA + self.GAP_AYUDA_OPCION
            if self.alcance and self.alcance.permitir_tiempo_pregunta:
                self._y_tiempo_pregunta = y
                self._colocar_fila_tiempo(y, self.boton_tiempo_pregunta, self.campo_tiempo_pregunta)
                y += self.ALTURA_FILA + self.GAP_ENTRE_OPCIONES
            else:
                self._y_tiempo_pregunta = 0
            if self.alcance and self.alcance.permitir_tiempo_total:
                self._y_tiempo_total = y
                self._colocar_fila_tiempo(y, self.boton_tiempo_total, self.campo_tiempo_total)
                y += self.ALTURA_FILA + self.GAP_ENTRE_SECCIONES
            else:
                self._y_tiempo_total = 0
                y += self.GAP_ENTRE_SECCIONES
        else:
            self._y_tiempo_titulo = 0
            self._y_tiempo_sin = 0
            self._y_tiempo_ayuda = 0
            self._y_tiempo_pregunta = 0
            self._y_tiempo_total = 0
            y += self.GAP_ENTRE_SECCIONES
            self.modo_tiempo = self.TIEMPO_NINGUNO

        self._y_punt_titulo = y
        y += self.GAP_TITULO_FILA
        self._y_punt_fila = y
        self._reconstruir_botones_sistema()
        y += self.ALTURA_FILA
        self._y_resumen = y + self.GAP_ANTES_RESUMEN
        tope_resumen = self.Y_SIGUIENTE - 30
        if self._y_resumen > tope_resumen:
            self._y_resumen = tope_resumen
        self._y_mensaje = min(self._y_resumen + 22, self.Y_SIGUIENTE - 16)

    def _n_preguntas_efectivas(self) -> int:
        return self.total_elegido if not self.modo_infinito else 10

    def _opciones_compat(self) -> OpcionesReglasLibre:
        return opciones_reglas_libre(
            modo_infinito=self.modo_infinito,
            n_preguntas=self._n_preguntas_efectivas(),
            sin_vidas=self.sin_vidas,
            sistema=self.sistema_elegido,
        )

    def _elegir_sin_vidas(self) -> None:
        opts = self._opciones_compat()
        if not opts.permitir_sin_vidas:
            return
        self.sin_vidas = True
        self.sin_vidas, self.sistema_elegido = normalizar_vidas_y_sistema(
            modo_infinito=self.modo_infinito,
            n_preguntas=self._n_preguntas_efectivas(),
            sin_vidas=True,
            sistema=self.sistema_elegido,
        )
        self.mensaje = ""
        self._actualizar_estado_ui()

    def _elegir_con_vidas(self) -> None:
        opts = self._opciones_compat()
        if not opts.permitir_con_vidas:
            return
        self.sin_vidas = False
        self.sin_vidas, self.sistema_elegido = normalizar_vidas_y_sistema(
            modo_infinito=self.modo_infinito,
            n_preguntas=self._n_preguntas_efectivas(),
            sin_vidas=False,
            sistema=self.sistema_elegido,
        )
        self.mensaje = ""
        self._actualizar_estado_ui()

    def _elegir_modo_tiempo(self, modo: str) -> None:
        if not self.alcance:
            return
        if modo == self.TIEMPO_PREGUNTA and not self.alcance.permitir_tiempo_pregunta:
            return
        if modo == self.TIEMPO_TOTAL and not self.alcance.permitir_tiempo_total:
            return
        self.modo_tiempo = modo
        self.mensaje = ""
        self._actualizar_seleccion_tiempo()
        self._actualizar_estado_ui()

    def _actualizar_seleccion_tiempo(self) -> None:
        self.boton_tiempo_ninguno.seleccionado = self.modo_tiempo == self.TIEMPO_NINGUNO
        self.boton_tiempo_pregunta.seleccionado = self.modo_tiempo == self.TIEMPO_PREGUNTA
        self.boton_tiempo_total.seleccionado = self.modo_tiempo == self.TIEMPO_TOTAL

    def _normalizar_modo_tiempo(self) -> None:
        if not self.alcance:
            self.modo_tiempo = self.TIEMPO_NINGUNO
            return
        if self.modo_tiempo == self.TIEMPO_PREGUNTA and not self.alcance.permitir_tiempo_pregunta:
            self.modo_tiempo = self.TIEMPO_NINGUNO
        if self.modo_tiempo == self.TIEMPO_TOTAL and not self.alcance.permitir_tiempo_total:
            self.modo_tiempo = self.TIEMPO_NINGUNO
        self._actualizar_seleccion_tiempo()

    def _reconstruir_botones_sistema(self) -> None:
        self.botones_sistema.clear()
        if not self.alcance:
            return
        opts = self._opciones_compat()
        sistemas = list(opts.sistemas)
        if self.sistema_elegido not in sistemas:
            self.sistema_elegido = sistemas[0]
        rects = fila_rects_centrada(
            len(sistemas),
            ancho_item=180,
            alto_item=self.ALTURA_FILA,
            separacion=16,
            y=self._y_punt_fila,
            ancho_pantalla=ANCHO,
        )
        for rect, sistema in zip(rects, sistemas, strict=True):
            etiqueta = ETIQUETAS_SISTEMA.get(sistema, sistema.value)
            btn = BotonMarcable(
                etiqueta,
                rect,
                lambda s=sistema: self._elegir_sistema(s),
            )
            btn.sistema = sistema  # type: ignore[attr-defined]
            btn.seleccionado = sistema == self.sistema_elegido
            self.botones_sistema.append(btn)

    def _elegir_sistema(self, sistema: SistemaPuntuacion) -> None:
        opts = self._opciones_compat()
        if sistema not in opts.sistemas:
            return
        self.sistema_elegido = sistema
        self.sin_vidas, self.sistema_elegido = normalizar_vidas_y_sistema(
            modo_infinito=self.modo_infinito,
            n_preguntas=self._n_preguntas_efectivas(),
            sin_vidas=self.sin_vidas,
            sistema=self.sistema_elegido,
        )
        self.mensaje = ""
        self._actualizar_estado_ui()

    def _actualizar_estado_ui(self) -> None:
        if not self.alcance:
            return
        self.sin_vidas, self.sistema_elegido = normalizar_vidas_y_sistema(
            modo_infinito=self.modo_infinito,
            n_preguntas=self._n_preguntas_efectivas(),
            sin_vidas=self.sin_vidas,
            sistema=self.sistema_elegido,
        )
        opts = self._opciones_compat()
        sistemas_actuales = tuple(
            getattr(boton, "sistema", None) for boton in self.botones_sistema
        )
        if sistemas_actuales != opts.sistemas:
            self._reconstruir_botones_sistema()
            opts = self._opciones_compat()

        self.boton_sin_vidas.seleccionado = self.sin_vidas
        self.boton_con_vidas.seleccionado = not self.sin_vidas
        self.boton_sin_vidas.activo = opts.permitir_sin_vidas
        self.boton_con_vidas.activo = opts.permitir_con_vidas
        con_vidas = not self.sin_vidas
        self.campo_vidas.establecer_habilitado(con_vidas and opts.permitir_con_vidas)
        if opts.permitir_con_vidas:
            self.campo_vidas.actualizar_limites(1, 10)

        self.boton_tiempo_ninguno.activo = True
        self.boton_tiempo_pregunta.activo = self.alcance.permitir_tiempo_pregunta
        self.boton_tiempo_total.activo = self.alcance.permitir_tiempo_total
        self.campo_tiempo_pregunta.establecer_habilitado(
            self.alcance.permitir_tiempo_pregunta
            and self.modo_tiempo == self.TIEMPO_PREGUNTA
        )
        self.campo_tiempo_total.establecer_habilitado(
            self.alcance.permitir_tiempo_total
            and self.modo_tiempo == self.TIEMPO_TOTAL
        )
        self._normalizar_modo_tiempo()

        for boton in self.botones_sistema:
            sis = getattr(boton, "sistema", None)
            boton.seleccionado = sis == self.sistema_elegido
            boton.activo = sis in opts.sistemas

    def _reglas_vista_previa(self) -> ReglasPartida:
        try:
            return self._construir_reglas()
        except ValueError:
            return preset_libre_arcade()

    def _construir_reglas(self) -> ReglasPartida:
        if not self.alcance:
            raise ValueError("Sin alcance de configuración")
        if self.sin_vidas and self.alcance.permitir_sin_vidas:
            vidas: int | None = None
        else:
            defecto = 3
            min_v = self.alcance.min_vidas
            max_v = self.alcance.max_vidas
            raw = self.campo_vidas.valor_entero(defecto=defecto)
            if raw is None or raw < min_v or raw > max_v:
                raise ValueError(f"Vidas entre {min_v} y {max_v}.")
            vidas = raw

        tiempo_preg: int | None = None
        tiempo_tot: int | None = None
        if self.modo_tiempo == self.TIEMPO_PREGUNTA:
            seg = self.campo_tiempo_pregunta.valor_entero(defecto=90)
            if seg is None or seg < 1 or seg > 600:
                raise ValueError("Segundos por pregunta entre 1 y 600.")
            tiempo_preg = seg
        elif self.modo_tiempo == self.TIEMPO_TOTAL:
            seg = self.campo_tiempo_total.valor_entero(defecto=600)
            if seg is None or seg < 1 or seg > 7200:
                raise ValueError("Tiempo total entre 1 y 7200 segundos.")
            tiempo_tot = seg

        return reglas_desde_combinacion(
            self.contexto,
            vidas=vidas,
            sistema=self.sistema_elegido,
            tiempo_por_pregunta_seg=tiempo_preg,
            tiempo_total_seg=tiempo_tot,
            mostrar_solucion_tras_fallo=True,
            mostrar_aciertos_en_curso=self._opciones_compat().permitir_aciertos_en_curso,
            dificultad_progresiva=False,
            modo_infinito=self.modo_infinito,
            n_preguntas=self._n_preguntas_efectivas(),
        )

    def _siguiente(self) -> None:
        try:
            reglas = self._construir_reglas()
        except ValueError as e:
            self.mensaje = str(e)
            return
        self.mensaje = ""
        self.ir_a(
            ConfigModoLibrePaso3(
                self.datos,
                self.ir_a,
                self.salir_app,
                nombre=self.nombre,
                banco_elegido=self.banco_elegido,
                modo_infinito=self.modo_infinito,
                total_elegido=self.total_elegido,
                reglas=reglas,
                sin_vidas_inicial=self.sin_vidas,
                vidas_count_inicial=int(self.campo_vidas.texto or "3"),
                modo_tiempo_inicial=self.modo_tiempo,
                tiempo_pregunta_inicial=int(self.campo_tiempo_pregunta.texto or "90"),
                tiempo_total_inicial=int(self.campo_tiempo_total.texto or "600"),
                sistema_inicial=self.sistema_elegido,
            )
        )

    def _atras(self) -> None:
        self.ir_a(
            ConfigModoLibrePaso1(
                self.datos,
                self.ir_a,
                self.salir_app,
                nombre_inicial=self.nombre,
                banco_inicial=self.banco_elegido,
                modo_infinito_inicial=self.modo_infinito,
                total_inicial=self.total_elegido,
            )
        )

    def _botones_ui(self) -> list[Boton | BotonMarcable]:
        botones: list[Boton | BotonMarcable] = [
            self.boton_siguiente,
            self.boton_atras,
        ]
        if self.alcance and self.alcance.permitir_sin_vidas:
            botones.extend([self.boton_sin_vidas, self.boton_con_vidas])
        else:
            botones.append(self.boton_con_vidas)
        if self._tiene_seccion_tiempo():
            botones.extend(
                [
                    self.boton_tiempo_ninguno,
                    self.boton_tiempo_pregunta,
                    self.boton_tiempo_total,
                ]
            )
        botones.extend(self.botones_sistema)
        return botones

    def _campos_ui(self) -> list[CampoEntero]:
        campos: list[CampoEntero] = []
        if not self.sin_vidas:
            campos.append(self.campo_vidas)
        if self.modo_tiempo == self.TIEMPO_PREGUNTA:
            campos.append(self.campo_tiempo_pregunta)
        if self.modo_tiempo == self.TIEMPO_TOTAL:
            campos.append(self.campo_tiempo_total)
        return campos

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        for campo in self._campos_ui():
            campo.manejar_evento(evento)
        if evento.type == pygame.MOUSEMOTION:
            for boton in self._botones_ui():
                boton.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            for campo in self._campos_ui():
                if campo.manejar_evento(evento):
                    return None
            for boton in self._botones_ui():
                if boton.manejar_clic(evento.pos, evento.button):
                    break
        self._actualizar_estado_ui()
        return None

    def _dibujar_seccion_vidas(self, superficie: pygame.Surface) -> None:
        titulo = self.fuentes["menu"].render("1. Vidas", True, COLOR_TITULO)
        superficie.blit(titulo, titulo.get_rect(center=(ANCHO // 2, self._y_vidas_titulo)))
        if self.alcance and self.alcance.permitir_sin_vidas:
            self.boton_sin_vidas.dibujar(superficie, self.fuentes["pequena"])
        self.boton_con_vidas.dibujar(superficie, self.fuentes["pequena"])
        if not self.sin_vidas:
            self.campo_vidas.dibujar(superficie, self.fuentes["menu"])
        ayuda = self.fuentes["pequena"].render(
            "Sin vidas = respondes todas las preguntas",
            True,
            COLOR_TEXTO,
        )
        superficie.blit(ayuda, ayuda.get_rect(center=(ANCHO // 2, self._y_vidas_ayuda)))

    def _dibujar_seccion_tiempo(self, superficie: pygame.Surface) -> None:
        if not self._tiene_seccion_tiempo():
            return
        titulo = self.fuentes["menu"].render("2. Tiempo", True, COLOR_TITULO)
        superficie.blit(titulo, titulo.get_rect(center=(ANCHO // 2, self._y_tiempo_titulo)))
        self.boton_tiempo_ninguno.dibujar(superficie, self.fuentes["pequena"])
        ayuda = self.fuentes["pequena"].render(
            "Elige un solo tipo de límite (por pregunta o total)",
            True,
            COLOR_TEXTO,
        )
        superficie.blit(ayuda, ayuda.get_rect(center=(ANCHO // 2, self._y_tiempo_ayuda)))
        if self.alcance and self.alcance.permitir_tiempo_pregunta:
            self.boton_tiempo_pregunta.dibujar(superficie, self.fuentes["pequena"])
            self.campo_tiempo_pregunta.dibujar(superficie, self.fuentes["menu"])
            unidad = self.fuentes["pequena"].render("s/pregunta", True, COLOR_TEXTO)
            superficie.blit(
                unidad,
                unidad.get_rect(
                    midleft=(
                        self.campo_tiempo_pregunta.rect.right + 10,
                        self.campo_tiempo_pregunta.rect.centery,
                    )
                ),
            )
        if self.alcance and self.alcance.permitir_tiempo_total:
            self.boton_tiempo_total.dibujar(superficie, self.fuentes["pequena"])
            self.campo_tiempo_total.dibujar(superficie, self.fuentes["menu"])
            unidad = self.fuentes["pequena"].render("s total", True, COLOR_TEXTO)
            superficie.blit(
                unidad,
                unidad.get_rect(
                    midleft=(
                        self.campo_tiempo_total.rect.right + 10,
                        self.campo_tiempo_total.rect.centery,
                    )
                ),
            )

    def _dibujar_seccion_puntuacion(self, superficie: pygame.Surface) -> None:
        titulo = self.fuentes["menu"].render("3. Puntuación", True, COLOR_TITULO)
        superficie.blit(titulo, titulo.get_rect(center=(ANCHO // 2, self._y_punt_titulo)))
        if len(self.botones_sistema) > 1:
            for boton in self.botones_sistema:
                boton.dibujar(superficie, self.fuentes["pequena"])
        elif self.botones_sistema:
            fijo = self.fuentes["cuerpo"].render(
                f"Solo disponible: {ETIQUETAS_SISTEMA.get(self.sistema_elegido, self.sistema_elegido.value)}",
                True,
                COLOR_TEXTO,
            )
            superficie.blit(fijo, fijo.get_rect(center=(ANCHO // 2, self._y_punt_fila + 18)))

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        dibujar_cabecera_wizard_modo_libre(
            superficie,
            self.fuentes,
            "Paso 2 de 3 — reglas de partida",
        )

        self._dibujar_seccion_vidas(superficie)
        self._dibujar_seccion_tiempo(superficie)
        self._dibujar_seccion_puntuacion(superficie)
        resumen = self.fuentes["menu"].render(
            self._reglas_vista_previa().describe(),
            True,
            COLOR_TEXTO,
        )
        superficie.blit(resumen, resumen.get_rect(center=(ANCHO // 2, self._y_resumen)))

        if self.mensaje:
            aviso = self.fuentes["menu"].render(self.mensaje, True, COLOR_AVISO)
            superficie.blit(aviso, aviso.get_rect(center=(ANCHO // 2, self._y_mensaje)))

        self.boton_siguiente.dibujar(superficie, self.fuentes["menu"])
        self.boton_atras.dibujar(superficie, self.fuentes["menu"])

    def titulo_pausa(self) -> str:
        return "Modo libre — paso 2"

    def dibujar_cabecera(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        dibujar_cabecera_wizard_modo_libre(
            superficie,
            self.fuentes,
            "Paso 2 de 3 — reglas de partida",
        )


class ConfigModoLibrePaso3(Pantalla):
    """Paso 3: filtros y dificultad inicial."""

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
    Y_FILTRO_LBL = 118
    Y_FILTRO_BTN = 148
    Y_SUB_LBL = 222
    Y_SUB_AYUDA = 242
    Y_SUB_GRID = 256
    SUBFILTRO_COLUMNAS = 3
    SUBFILTRO_FILAS = 4
    SUBFILTRO_ANCHO = 290
    SUBFILTRO_ALTO = 40
    Y_SCROLL_BTNS = 442
    Y_OPCIONES_LBL = 458
    Y_OPCIONES_FILA = 488
    ALTURA_OPCION = 36
    Y_DIF_LBL = 538
    Y_DIF_CAMPO = 564
    Y_AVISO = 594
    Y_EMPEZAR = 614
    Y_ATRAS = 674

    def __init__(
        self,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
        *,
        nombre: str,
        banco_elegido: BancoPreguntas,
        modo_infinito: bool,
        total_elegido: int,
        reglas: ReglasPartida,
        sin_vidas_inicial: bool = False,
        vidas_count_inicial: int = 3,
        modo_tiempo_inicial: str = ConfigModoLibrePaso2.TIEMPO_NINGUNO,
        tiempo_pregunta_inicial: int = 90,
        tiempo_total_inicial: int = 600,
        sistema_inicial: SistemaPuntuacion = SistemaPuntuacion.ARCADE,
        modo_filtro_inicial: str = FILTRO_TODAS,
        global_inicial: int = 1,
    ) -> None:
        self.datos = datos
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.nombre = nombre
        self.banco_elegido = banco_elegido
        self.modo_infinito = modo_infinito
        self.total_elegido = total_elegido
        self.reglas = reglas
        self.sin_vidas_inicial = sin_vidas_inicial
        self.vidas_count_inicial = vidas_count_inicial
        self.modo_tiempo_inicial = modo_tiempo_inicial
        self.tiempo_pregunta_inicial = tiempo_pregunta_inicial
        self.tiempo_total_inicial = tiempo_total_inicial
        self.sistema_inicial = sistema_inicial
        self.contexto = contexto_partida(
            modo_infinito=modo_infinito,
            n_preguntas=10 if modo_infinito else total_elegido,
        )
        self.alcance = alcance(self.contexto)
        self.modo_filtro = modo_filtro_inicial
        self.tematicas_sel: set[str] = set()
        self.semestres_sel: set[str] = set()
        self.tipos_sel: set[str] = set()
        self.subfiltro_scroll = 0
        self._opciones_subfiltro: list[tuple[str, str]] = []
        self.global_inicial = global_inicial
        self.mensaje = ""
        self.fuentes = crear_fuentes()
        self.pool_raw = cargar_pool_banco(datos, banco_elegido)

        self.botones_filtro: list[Boton] = []
        rects_filtro = fila_rects_centrada(
            len(self.OPCIONES_FILTRO),
            ancho_item=200,
            alto_item=52,
            separacion=20,
            y=self.Y_FILTRO_BTN,
            ancho_pantalla=ANCHO,
        )
        for rect, (codigo, etiqueta) in zip(rects_filtro, self.OPCIONES_FILTRO, strict=True):
            btn = BotonMarcable(
                etiqueta,
                rect,
                lambda c=codigo: self._elegir_modo_filtro(c),
            )
            btn.codigo_filtro = codigo  # type: ignore[attr-defined]
            self.botones_filtro.append(btn)

        self.botones_subfiltro: list[Boton] = []
        self.boton_subfiltro_subir = Boton(
            "Subir",
            pygame.Rect(ANCHO // 2 - 112, self.Y_SCROLL_BTNS, 100, 30),
            lambda: self._scroll_subfiltro(-1),
        )
        self.boton_subfiltro_bajar = Boton(
            "Bajar",
            pygame.Rect(ANCHO // 2 + 12, self.Y_SCROLL_BTNS, 100, 30),
            lambda: self._scroll_subfiltro(1),
        )
        mostrar_sol_ini = reglas.mostrar_solucion_tras_fallo
        opts_ini = opciones_reglas_libre(
            modo_infinito=self.modo_infinito,
            n_preguntas=self.total_elegido if not self.modo_infinito else 10,
            sin_vidas=reglas.vidas is None,
            sistema=reglas.sistema_puntuacion,
        )
        dif_prog_ini = opts_ini.permitir_dificultad_progresiva and reglas.dificultad_progresiva
        self.boton_mostrar_solucion = BotonMarcable(
            "Solución tras fallo",
            pygame.Rect(ANCHO // 2 - 250, self.Y_OPCIONES_FILA, 230, self.ALTURA_OPCION),
            self._toggle_mostrar_solucion,
            seleccionado=mostrar_sol_ini,
        )
        self.boton_dificultad_progresiva = BotonMarcable(
            "Dificultad progresiva",
            pygame.Rect(ANCHO // 2 + 20, self.Y_OPCIONES_FILA, 230, self.ALTURA_OPCION),
            self._toggle_dificultad_progresiva,
            seleccionado=dif_prog_ini,
        )
        self.campo_dificultad = CampoEntero(
            pygame.Rect(ANCHO // 2 - 80, self.Y_DIF_CAMPO, 160, 44),
            texto_inicial=str(global_inicial),
            placeholder="1",
            minimo=1,
            maximo=1,
        )
        self._reconstruir_subfiltros()
        self._actualizar_opciones_ui()
        self._reconstruir_dificultad()

        self.boton_empezar = Boton(
            "Empezar partida",
            pygame.Rect(ANCHO // 2 - 130, self.Y_EMPEZAR, 260, 52),
            self._empezar,
        )
        self.boton_atras = Boton(
            "Atrás",
            pygame.Rect(ANCHO // 2 - 130, self.Y_ATRAS, 260, 44),
            self._atras,
        )

    def _n_preguntas_efectivas(self) -> int:
        return self.total_elegido if not self.modo_infinito else 10

    def _opciones_compat_paso3(self) -> OpcionesReglasLibre:
        sin = self.reglas.vidas is None
        return opciones_reglas_libre(
            modo_infinito=self.modo_infinito,
            n_preguntas=self._n_preguntas_efectivas(),
            sin_vidas=sin,
            sistema=self.reglas.sistema_puntuacion,
        )

    def _dificultad_inicial_activa(self) -> bool:
        return (
            self.boton_dificultad_progresiva.activo
            and self.boton_dificultad_progresiva.seleccionado
        )

    def _toggle_mostrar_solucion(self) -> None:
        self.boton_mostrar_solucion.seleccionado = not self.boton_mostrar_solucion.seleccionado

    def _toggle_dificultad_progresiva(self) -> None:
        self.boton_dificultad_progresiva.seleccionado = (
            not self.boton_dificultad_progresiva.seleccionado
        )
        self._reconstruir_dificultad()

    def _actualizar_opciones_ui(self) -> None:
        if not self.alcance:
            self.boton_mostrar_solucion.activo = False
            self.boton_dificultad_progresiva.activo = False
            return
        opts = self._opciones_compat_paso3()
        self.boton_mostrar_solucion.activo = opts.permitir_solucion_tras_fallo
        self.boton_dificultad_progresiva.activo = opts.permitir_dificultad_progresiva
        if not opts.permitir_dificultad_progresiva:
            self.boton_dificultad_progresiva.seleccionado = False

    def _construir_reglas_finales(self) -> ReglasPartida:
        mostrar = (
            self.boton_mostrar_solucion.seleccionado
            if self.boton_mostrar_solucion.activo
            else self.reglas.mostrar_solucion_tras_fallo
        )
        dif = (
            self.boton_dificultad_progresiva.seleccionado
            if self.boton_dificultad_progresiva.activo
            else self.reglas.dificultad_progresiva
        )
        reglas = replace(
            self.reglas,
            mostrar_solucion_tras_fallo=mostrar,
            dificultad_progresiva=dif,
        )
        return validar_reglas(
            reglas,
            self.contexto,
            modo_infinito=self.modo_infinito,
            n_preguntas=self._n_preguntas_efectivas(),
        )

    def _pool_filtrado(self) -> list[Pregunta]:
        if self.modo_filtro == self.FILTRO_TEMATICA:
            return filtrar_pool(
                self.pool_raw,
                tematicas=self.tematicas_sel or None,
            )
        if self.modo_filtro == self.FILTRO_SEMESTRE:
            return filtrar_pool(
                self.pool_raw,
                cursos_semestres=self.semestres_sel or None,
            )
        if self.modo_filtro == self.FILTRO_TIPO:
            return filtrar_pool(
                self.pool_raw,
                tipos=self.tipos_sel or None,
            )
        return list(self.pool_raw)

    def _conjunto_seleccion_actual(self) -> set[str]:
        if self.modo_filtro == self.FILTRO_TEMATICA:
            return self.tematicas_sel
        if self.modo_filtro == self.FILTRO_SEMESTRE:
            return self.semestres_sel
        if self.modo_filtro == self.FILTRO_TIPO:
            return self.tipos_sel
        return set()

    def _elegir_modo_filtro(self, codigo: str) -> None:
        self.modo_filtro = codigo
        self.tematicas_sel.clear()
        self.semestres_sel.clear()
        self.tipos_sel.clear()
        self.subfiltro_scroll = 0
        self.mensaje = ""
        self._reconstruir_subfiltros()
        self._reconstruir_dificultad()

    def _opciones_para_modo_filtro(self) -> list[tuple[str, str]]:
        if self.modo_filtro == self.FILTRO_TEMATICA:
            opciones = [("__todas__", "Todas")]
            opciones.extend((valor, valor) for valor in opciones_tematica(self.pool_raw))
            return opciones
        if self.modo_filtro == self.FILTRO_SEMESTRE:
            return [("__todas__", "Todas"), *(
                (valor, valor) for valor in opciones_curso_semestre(self.pool_raw)
            )]
        if self.modo_filtro == self.FILTRO_TIPO:
            return [("__todas__", "Todas"), *(
                (valor, valor) for valor in opciones_tipo(self.pool_raw)
            )]
        return []

    def _scroll_subfiltro(self, direccion: int) -> None:
        paso = self.SUBFILTRO_COLUMNAS
        max_scroll = max(
            0,
            len(self._opciones_subfiltro)
            - self.SUBFILTRO_COLUMNAS * self.SUBFILTRO_FILAS,
        )
        self.subfiltro_scroll = max(
            0,
            min(max_scroll, self.subfiltro_scroll + direccion * paso),
        )
        self._montar_botones_subfiltro()

    def _reconstruir_subfiltros(self) -> None:
        for boton in self.botones_filtro:
            codigo = getattr(boton, "codigo_filtro", "")
            boton.seleccionado = codigo == self.modo_filtro

        self._opciones_subfiltro = self._opciones_para_modo_filtro()
        max_scroll = max(
            0,
            len(self._opciones_subfiltro)
            - self.SUBFILTRO_COLUMNAS * self.SUBFILTRO_FILAS,
        )
        self.subfiltro_scroll = min(self.subfiltro_scroll, max_scroll)
        self._montar_botones_subfiltro()

    def _montar_botones_subfiltro(self) -> None:
        self.botones_subfiltro = []
        if not self._opciones_subfiltro:
            return

        inicio = self.subfiltro_scroll
        fin = inicio + self.SUBFILTRO_COLUMNAS * self.SUBFILTRO_FILAS
        visibles = self._opciones_subfiltro[inicio:fin]
        rects = cuadricula_rects(
            len(visibles),
            columnas=self.SUBFILTRO_COLUMNAS,
            ancho_item=self.SUBFILTRO_ANCHO,
            alto_item=self.SUBFILTRO_ALTO,
            separacion_x=15,
            separacion_y=6,
            y_inicio=self.Y_SUB_GRID,
            ancho_pantalla=ANCHO,
        )
        seleccion = self._conjunto_seleccion_actual()
        for rect, (clave, etiqueta) in zip(rects, visibles, strict=True):
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

        hay_scroll = len(self._opciones_subfiltro) > (
            self.SUBFILTRO_COLUMNAS * self.SUBFILTRO_FILAS
        )
        self.boton_subfiltro_subir.activo = hay_scroll and self.subfiltro_scroll > 0
        self.boton_subfiltro_bajar.activo = hay_scroll and fin < len(self._opciones_subfiltro)

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
        self._reconstruir_dificultad()

    def _actualizar_seleccion_subfiltros(self) -> None:
        seleccion = self._conjunto_seleccion_actual()
        for boton in self.botones_subfiltro:
            clave = getattr(boton, "clave_subfiltro", "")
            if clave == "__todas__":
                boton.seleccionado = not seleccion
            else:
                boton.seleccionado = clave in seleccion

    def _reconstruir_dificultad(self) -> None:
        if not self._dificultad_inicial_activa():
            self.global_inicial = 1
            self.campo_dificultad.establecer_habilitado(False)
            return
        pool = self._pool_filtrado()
        max_global = max_complejidad_pool(pool)
        self.global_inicial = min(max(1, self.global_inicial), max_global)
        self.campo_dificultad.establecer_habilitado(True)
        self.campo_dificultad.actualizar_limites(1, max_global)
        valor = self.campo_dificultad.valor_entero(defecto=self.global_inicial)
        if valor is not None:
            self.global_inicial = valor
        self.campo_dificultad.texto = str(self.global_inicial)

    def _atras(self) -> None:
        self.ir_a(
            ConfigModoLibrePaso2(
                self.datos,
                self.ir_a,
                self.salir_app,
                nombre=self.nombre,
                banco_elegido=self.banco_elegido,
                modo_infinito=self.modo_infinito,
                total_elegido=self.total_elegido,
                sin_vidas_inicial=self.sin_vidas_inicial,
                vidas_count_inicial=self.vidas_count_inicial,
                modo_tiempo_inicial=self.modo_tiempo_inicial,
                tiempo_pregunta_inicial=self.tiempo_pregunta_inicial,
                tiempo_total_inicial=self.tiempo_total_inicial,
                sistema_inicial=self.sistema_inicial,
            )
        )

    def _empezar(self) -> None:
        if self.modo_filtro == self.FILTRO_SEMESTRE and not opciones_curso_semestre(self.pool_raw):
            self.mensaje = "No hay curso-semestre en este banco."
            return
        if self.modo_filtro == self.FILTRO_TIPO and not opciones_tipo(self.pool_raw):
            self.mensaje = "No hay tipos en este banco."
            return
        if self._dificultad_inicial_activa():
            dificultad = self.campo_dificultad.valor_entero(defecto=1)
            max_global = max_complejidad_pool(self._pool_filtrado())
            if dificultad is None:
                self.mensaje = f"Introduce una dificultad entre 1 y {max_global}."
                return
            self.global_inicial = dificultad
        pool = self._pool_filtrado()
        if not pool:
            self.mensaje = "No hay preguntas para ese filtro."
            return
        self.mensaje = ""
        reglas = self._construir_reglas_finales()
        self.ir_a(
            PartidaModoLibre(
                nombre=self.nombre,
                preguntas=pool,
                pool=pool,
                reglas=reglas,
                ir_a=self.ir_a,
                datos=self.datos,
                salir_app=self.salir_app,
                infinito=self.modo_infinito,
                total_previsto=self.total_elegido,
                global_inicial=(
                    self.global_inicial
                    if self._dificultad_inicial_activa()
                    else 1
                ),
            )
        )

    def _botones_ui(self) -> list[Boton]:
        botones = [
            *self.botones_filtro,
            *self.botones_subfiltro,
            self.boton_empezar,
            self.boton_atras,
        ]
        if self.modo_filtro in {
            self.FILTRO_TEMATICA,
            self.FILTRO_SEMESTRE,
            self.FILTRO_TIPO,
        }:
            botones.extend([self.boton_subfiltro_subir, self.boton_subfiltro_bajar])
        if self.boton_mostrar_solucion.activo:
            botones.append(self.boton_mostrar_solucion)
        if self.boton_dificultad_progresiva.activo:
            botones.append(self.boton_dificultad_progresiva)
        return botones

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if self._dificultad_inicial_activa():
            self.campo_dificultad.manejar_evento(evento)
        if evento.type == pygame.MOUSEWHEEL and self.modo_filtro in {
            self.FILTRO_TEMATICA,
            self.FILTRO_SEMESTRE,
            self.FILTRO_TIPO,
        }:
            self._scroll_subfiltro(-int(evento.y))
        elif evento.type == pygame.MOUSEMOTION:
            for boton in self._botones_ui():
                boton.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if (
                self._dificultad_inicial_activa()
                and self.campo_dificultad.manejar_evento(evento)
            ):
                return None
            for boton in self._botones_ui():
                if boton.manejar_clic(evento.pos, evento.button):
                    break
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        dibujar_cabecera_wizard_modo_libre(
            superficie,
            self.fuentes,
            "Paso 3 de 3 — filtros y dificultad",
        )

        filtro_lbl = self.fuentes["menu"].render("Filtro principal:", True, COLOR_TEXTO)
        superficie.blit(filtro_lbl, filtro_lbl.get_rect(center=(ANCHO // 2, self.Y_FILTRO_LBL)))
        for boton in self.botones_filtro:
            boton.dibujar(superficie, self.fuentes["menu"])

        if self.modo_filtro in {self.FILTRO_TEMATICA, self.FILTRO_SEMESTRE, self.FILTRO_TIPO}:
            sub_lbl = self.fuentes["menu"].render("Valor del filtro:", True, COLOR_TEXTO)
            superficie.blit(sub_lbl, sub_lbl.get_rect(center=(ANCHO // 2, self.Y_SUB_LBL)))
            ayuda = self.fuentes["pequena"].render(
                "Clic para marcar o desmarcar. Sin marcar ninguna = todas.",
                True,
                COLOR_TEXTO,
            )
            superficie.blit(ayuda, ayuda.get_rect(center=(ANCHO // 2, self.Y_SUB_AYUDA)))
            for boton in self.botones_subfiltro:
                boton.dibujar(superficie, self.fuentes["pequena"])
            hay_scroll = len(self._opciones_subfiltro) > (
                self.SUBFILTRO_COLUMNAS * self.SUBFILTRO_FILAS
            )
            if hay_scroll:
                self.boton_subfiltro_subir.activo = self.subfiltro_scroll > 0
                self.boton_subfiltro_bajar.activo = (
                    self.subfiltro_scroll
                    + self.SUBFILTRO_COLUMNAS * self.SUBFILTRO_FILAS
                    < len(self._opciones_subfiltro)
                )
                if self.boton_subfiltro_subir.activo:
                    self.boton_subfiltro_subir.dibujar(superficie, self.fuentes["pequena"])
                if self.boton_subfiltro_bajar.activo:
                    self.boton_subfiltro_bajar.dibujar(superficie, self.fuentes["pequena"])

        hay_opciones = (
            self.boton_mostrar_solucion.activo
            or self.boton_dificultad_progresiva.activo
            or self._dificultad_inicial_activa()
        )
        if hay_opciones:
            opc_lbl = self.fuentes["menu"].render(
                "Dificultad y opciones:",
                True,
                COLOR_TEXTO,
            )
            superficie.blit(opc_lbl, opc_lbl.get_rect(center=(ANCHO // 2, self.Y_OPCIONES_LBL)))
            if self.boton_mostrar_solucion.activo:
                self.boton_mostrar_solucion.dibujar(superficie, self.fuentes["pequena"])
            if self.boton_dificultad_progresiva.activo:
                self.boton_dificultad_progresiva.dibujar(superficie, self.fuentes["pequena"])

        if self._dificultad_inicial_activa():
            max_global = max_complejidad_pool(self._pool_filtrado())
            dif_lbl = self.fuentes["menu"].render(
                f"Dificultad global inicial (teclado, 1–{max_global}):",
                True,
                COLOR_TEXTO,
            )
            superficie.blit(dif_lbl, dif_lbl.get_rect(center=(ANCHO // 2, self.Y_DIF_LBL)))
            self.campo_dificultad.dibujar(superficie, self.fuentes["menu"])

        if self.mensaje:
            aviso = self.fuentes["menu"].render(self.mensaje, True, COLOR_AVISO)
            superficie.blit(aviso, aviso.get_rect(center=(ANCHO // 2, self.Y_AVISO)))

        self.boton_empezar.dibujar(superficie, self.fuentes["menu"])
        self.boton_atras.dibujar(superficie, self.fuentes["menu"])

    def titulo_pausa(self) -> str:
        return "Modo libre — paso 3"

    def dibujar_cabecera(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        dibujar_cabecera_wizard_modo_libre(
            superficie,
            self.fuentes,
            "Paso 3 de 3 — filtros y dificultad",
        )


# Alias del paso 1 (menú principal).
ConfigModoLibre = ConfigModoLibrePaso1


def _rect_boton_etiqueta(
    etiqueta: str,
    fuente: pygame.font.Font,
    *,
    x_derecha: int,
    y: int,
    padding_x: int = 14,
    padding_y: int = 8,
) -> pygame.Rect:
    texto = preparar_texto_ui(etiqueta)
    w = fuente.size(texto)[0] + 2 * padding_x
    h = fuente.get_height() + 2 * padding_y
    return pygame.Rect(x_derecha - w, y, w, h)


def _segundos_pregunta_restantes(inicio: float, limite: int | None) -> int | None:
    if not limite:
        return None
    return max(0, int(limite - (time.monotonic() - inicio)))


class PartidaModoLibre(Pantalla):
    def __init__(
        self,
        *,
        nombre: str,
        preguntas: list[Pregunta],
        reglas,
        ir_a: Callable[[Pantalla], None],
        datos: DatosJuego,
        salir_app: Callable[[], None],
        pool: list[Pregunta] | None = None,
        infinito: bool = False,
        total_previsto: int | None = None,
        global_inicial: int = 1,
    ) -> None:
        self.nombre = nombre
        self.pool = list(pool or preguntas)
        self.infinito = infinito
        self.total = None if infinito else (total_previsto or len(self.pool))
        self.global_inicial = max(1, global_inicial)
        self.max_global = max_complejidad_pool(self.pool)
        self.ir_a = ir_a
        self.datos = datos
        self.salir_app = salir_app
        self.fuentes = crear_fuentes()
        self.estado = EstadoPartida(
            nombre=nombre,
            reglas=reglas,
            vidas_restantes=reglas.vidas,
        )
        self.indice_global = 0
        self.fase = "pregunta"
        self.feedback_mensaje = ""
        self.feedback_solucion: str | None = None
        self.feedback_ok = False
        self.respuesta_elegida = ""
        self.botones_opcion: list[BotonOpcion] = []
        self.seleccion_pool = crear_estado_seleccion(len(self.pool))
        self.pregunta_idx: int | None = None
        self.inicio_pregunta = time.monotonic()
        self.boton_continuar = Boton(
            "Continuar",
            pygame.Rect(ANCHO // 2 - 90, ALTO - 60, 180, ALTO_BOTON_CONTINUAR_PARTIDA),
            self._continuar,
        )
        self.boton_abandonar = Boton(
            "Abandonar",
            _rect_boton_etiqueta(
                "Abandonar",
                self.fuentes["pequena"],
                x_derecha=ANCHO - MARGEN,
                y=14,
            ),
            lambda: self.ir_a(MenuPrincipal(datos, ir_a, salir_app)),
        )
        if not self._cargar_siguiente_pregunta(inicial=True):
            raise IndexError("Sin preguntas disponibles.")
        self._reconstruir_opciones()

    def _cargar_siguiente_pregunta(self, *, inicial: bool = False) -> bool:
        if not inicial and self.total is not None and self.indice_global >= self.total:
            return False
        idx = elegir_indice_siguiente(
            self.pool,
            self.seleccion_pool,
            modo_infinito=self.infinito,
            dificultad_progresiva=self.estado.reglas.dificultad_progresiva,
            global_inicial=self.global_inicial,
            respondidas=self.estado.respondidas,
        )
        if idx is None:
            return False
        self.pregunta_idx = idx
        self.inicio_pregunta = time.monotonic()
        return True

    def _pregunta_actual(self) -> Pregunta:
        if self.pregunta_idx is None:
            raise IndexError("Sin preguntas disponibles.")
        return self.pool[self.pregunta_idx]

    def _texto_progreso(self) -> str:
        total_txt = self.total if self.total is not None else "inf"
        return f"Pregunta {self.indice_global + 1}/{total_txt}"

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

    def _dibujar_barra_superior(self, superficie: pygame.Surface) -> None:
        fuente = self.fuentes["pequena"]
        self.boton_abandonar.rect = _rect_boton_etiqueta(
            "Abandonar",
            fuente,
            x_derecha=ANCHO - MARGEN,
            y=14,
        )
        x_centro_min = MARGEN_ICONOS_FIJOS + 8
        x_centro_max = self.boton_abandonar.rect.x - 12
        ancho_centro = max(80, x_centro_max - x_centro_min)
        estado_txt = self._linea_estado_actual()
        fuente_estado = _fuente_ajustada(estado_txt, fuente, ancho_centro)
        estado = fuente_estado.render(estado_txt, True, COLOR_TEXTO)
        superficie.blit(
            estado,
            estado.get_rect(midtop=(ANCHO // 2, 18)),
        )
        if self.nombre and self.nombre != "Anónimo":
            nombre_txt = fuente.render(self.nombre, True, COLOR_ACENTO)
            if nombre_txt.get_width() <= ancho_centro:
                superficie.blit(
                    nombre_txt,
                    nombre_txt.get_rect(midtop=(ANCHO // 2, 36)),
                )
        pygame.draw.line(
            superficie,
            (50, 72, 110),
            (MARGEN, ALTURA_BARRA_PARTIDA),
            (ANCHO - MARGEN, ALTURA_BARRA_PARTIDA),
            1,
        )
        self.boton_abandonar.dibujar(superficie, fuente)

    def _meta_pregunta(self, p: Pregunta) -> str:
        partes = [p.materia, p.tipo, p.dificultad]
        if self.estado.reglas.dificultad_progresiva:
            global_actual = dificultad_global_actual(
                respondidas=self.estado.respondidas,
                global_inicial=self.global_inicial,
                max_global=self.max_global,
            )
            partes.append(f"Dif. {global_actual}/{self.max_global}")
        return " · ".join(partes)

    def _y_inicio_opciones(self) -> int:
        y = Y_PANEL_PREGUNTA + ALTO_PANEL_PREGUNTA + GAP_TRAS_PANEL_PARTIDA
        if self.total is not None and self.total > 0:
            y += ALTO_BARRA_PROGRESO_PARTIDA + GAP_TRAS_BARRA_PROGRESO
        return y

    def _y_fin_opciones(self) -> int:
        if not self.botones_opcion:
            n = 4
            return (
                self._y_inicio_opciones()
                + n * ALTO_OPCION_PARTIDA
                + max(0, n - 1) * SEP_OPCIONES_PARTIDA
            )
        return max(b.rect.bottom for b in self.botones_opcion)

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

    def _aplicar_resultado(self, resultado: ResultadoRespuesta) -> None:
        p = self._pregunta_actual()
        feedback = evaluar_respuesta(p, self.estado, resultado)
        self.feedback_mensaje = feedback.mensaje
        self.feedback_solucion = feedback.solucion
        self.feedback_ok = resultado.acierto and not resultado.tiempo_agotado
        self.fase = "feedback"
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
        self.respuesta_elegida = letra
        self._aplicar_resultado(ResultadoRespuesta(acierto=acierto, respuesta=letra))

    def _responder_timeout(self) -> None:
        if self.fase != "pregunta":
            return
        self.respuesta_elegida = ""
        self._aplicar_resultado(
            ResultadoRespuesta(acierto=False, respuesta="", tiempo_agotado=True)
        )

    def _ir_a_resumen(self) -> Pantalla:
        total_prev = (
            self.total
            if self.total is not None
            else max(1, self.estado.respondidas)
        )
        return ResumenPartida(
            self.estado,
            total_prev,
            self.ir_a,
            self.datos,
            self.salir_app,
        )

    def actualizar(self) -> Pantalla | None:
        if self.fase != "pregunta":
            return None
        if self.estado.tiempo_total_restante() == 0:
            return self._ir_a_resumen()
        lim = self.estado.reglas.tiempo_por_pregunta_seg
        if lim and _segundos_pregunta_restantes(self.inicio_pregunta, lim) == 0:
            self._responder_timeout()
        return None

    def _continuar(self) -> None:
        if self.fase != "feedback":
            return
        if not self.estado.debe_continuar(self.total):
            self.ir_a(self._ir_a_resumen())
            return
        self.indice_global += 1
        if not self._cargar_siguiente_pregunta():
            self.ir_a(self._ir_a_resumen())
            return
        self.fase = "pregunta"
        self.feedback_mensaje = ""
        self.feedback_solucion = None
        self.feedback_ok = False
        self.respuesta_elegida = ""
        self._reconstruir_opciones()

    def titulo_pausa(self) -> str:
        return f"{self.nombre} · {self._linea_estado_actual()}"

    def dibujar_cabecera(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        self._dibujar_barra_superior(superficie)

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEMOTION:
            self.boton_abandonar.actualizar_hover(evento.pos)
            if self.fase == "pregunta":
                for boton in self.botones_opcion:
                    boton.actualizar_hover(evento.pos)
            else:
                self.boton_continuar.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if self.boton_abandonar.manejar_clic(evento.pos, evento.button):
                return None
            if self.fase == "pregunta":
                for boton in self.botones_opcion:
                    if boton.manejar_clic(evento.pos, evento.button):
                        break
            else:
                self.boton_continuar.manejar_clic(evento.pos, evento.button)
        return None

    def _dibujar_feedback(self, superficie: pygame.Surface) -> None:
        y_boton = ALTO - MARGEN_INF_PARTIDA - ALTO_BOTON_CONTINUAR_PARTIDA
        self.boton_continuar.rect = pygame.Rect(
            ANCHO // 2 - 90,
            y_boton,
            180,
            ALTO_BOTON_CONTINUAR_PARTIDA,
        )
        y_fin_opciones = self._y_fin_opciones()
        zona = pygame.Rect(
            MARGEN,
            y_fin_opciones + 10,
            ANCHO - 2 * MARGEN,
            max(40, y_boton - 8 - (y_fin_opciones + 10)),
        )
        color_fb = COLOR_OK if self.feedback_ok else COLOR_ERROR
        mensaje = self.fuentes["subtitulo"].render(
            preparar_texto_ui(self.feedback_mensaje), True, color_fb
        )
        superficie.blit(
            mensaje,
            mensaje.get_rect(midtop=(ANCHO // 2, zona.y)),
        )
        y_sol = zona.y + mensaje.get_height() + 6
        if self.feedback_solucion:
            rect_sol = pygame.Rect(
                zona.x + 8,
                y_sol,
                zona.width - 16,
                max(20, zona.bottom - y_sol),
            )
            dibujar_texto_multilinea(
                superficie,
                self.fuentes["pequena"],
                self.feedback_solucion,
                rect_sol,
                COLOR_AVISO,
                alineacion_centro=True,
            )
        self.boton_continuar.dibujar(superficie, self.fuentes["menu"])

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        self._dibujar_barra_superior(superficie)

        p = self._pregunta_actual()
        panel = pygame.Rect(MARGEN, Y_PANEL_PREGUNTA, ANCHO - 2 * MARGEN, ALTO_PANEL_PREGUNTA)
        dibujar_panel(superficie, panel)
        meta = self.fuentes["pequena"].render(
            self._meta_pregunta(p),
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

        # Progreso de la partida finita (respondidas / total); en infinito no se muestra.
        if self.total is not None and self.total > 0:
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
            self._dibujar_feedback(superficie)


class ResumenPartida(Pantalla):
    def __init__(
        self,
        estado: EstadoPartida,
        total_previsto: int,
        ir_a: Callable[[Pantalla], None],
        datos: DatosJuego,
        salir_app: Callable[[], None],
    ) -> None:
        self.estado = estado
        self.total_previsto = total_previsto
        self.ir_a = ir_a
        self.datos = datos
        self.salir_app = salir_app
        self.fuentes = crear_fuentes()
        self.lineas = self._construir_lineas()
        self.boton_menu = Boton(
            "Volver al menú",
            pygame.Rect(ANCHO // 2 - 110, ALTO - 90, 220, 48),
            lambda: self.ir_a(MenuPrincipal(datos, ir_a, salir_app)),
        )

    def _construir_lineas(self) -> list[str]:
        e = self.estado
        lineas = [
            f"Jugador: {e.nombre}",
            formatear_resultado_puntuacion(
                e.reglas,
                aciertos=e.aciertos,
                total=e.respondidas,
                puntos_arcade=e.puntos_arcade,
            ),
            f"Aciertos: {e.aciertos}/{e.respondidas}",
        ]
        if e.reglas.tiene_vidas():
            lineas.append(f"Vidas restantes: {e.vidas_restantes}")
        if e.respondidas < self.total_previsto:
            lineas.append(f"Partida incompleta ({e.respondidas}/{self.total_previsto})")
        return lineas

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEMOTION:
            self.boton_menu.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            self.boton_menu.manejar_clic(evento.pos, evento.button)
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        titulo = self.fuentes["titulo"].render("FIN DE PARTIDA", True, COLOR_TITULO)
        superficie.blit(titulo, titulo.get_rect(center=(ANCHO // 2, 90)))
        y = 170
        for linea in self.lineas:
            txt = self.fuentes["cuerpo"].render(linea, True, COLOR_TEXTO)
            superficie.blit(txt, txt.get_rect(center=(ANCHO // 2, y)))
            y += 40
        self.boton_menu.dibujar(superficie, self.fuentes["menu"])

    def titulo_pausa(self) -> str:
        return "Fin de partida"

    def dibujar_cabecera(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        titulo = self.fuentes["titulo"].render("FIN DE PARTIDA", True, COLOR_TITULO)
        superficie.blit(titulo, titulo.get_rect(center=(ANCHO // 2, 90)))
