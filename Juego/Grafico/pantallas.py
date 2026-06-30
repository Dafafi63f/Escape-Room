#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pantallas pygame del cuestionario (navegación por ratón)."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from Comun.reglas import (
    max_complejidad_pool,
    niveles_en_pool,
    normalizar_niveles_seleccionados,
    describe_niveles_seleccion,
    techo_complejidad_partida,
)
from Comun.modelos import Pregunta
from Comun.reglas import ReglasPartida, vidas_iniciales_partida
from Comun.motor_nucleo import (
    EstadoPartida,
    ResultadoRespuesta,
    PresentacionOpcionesPregunta,
    evaluar_respuesta,
    linea_estado,
    marcar_botones_opciones_tras_respuesta,
    presentacion_opciones_pantalla,
    texto_solucion,
)
from Comun.semillas import crear_rng_partida, semilla_partida_aleatoria
from Comun.linea_estado_ui import texto_progreso_examen_cerrado
from Comun.informe_examen import CierreInformePartida
from Comun.preferencias_grafico import es_nombre_anonimo
from Comun.motor_nucleo import NavegacionFinPartida
from Comun.pool_libre import crear_estado_seleccion, elegir_indice_siguiente
from Comun.preferencias_grafico import guardar_informes_txt_habilitados
from Grafico.informe_partida import guardar_informe_cierre, lineas_resumen_breve
from Grafico.tema import ALTO, ANCHO, COLOR_ACENTO, COLOR_AVISO, COLOR_ERROR, COLOR_FONDO, COLOR_OK, COLOR_TEXTO, COLOR_TITULO, MARGEN, crear_fuentes, x_min_centro_barra_partida
from Grafico.texto import dibujar_texto_centro, preparar_texto_ui
from Grafico.ui import (
    Boton,
    BotonOpcion,
    _fuente_ajustada,
    capturar,
    dibujar_panel,
    dibujar_texto_multilinea,
    dibujar_tooltips_botones,
    posicionar_botones_fila,
    posicionar_pila_inferior,
    rect_boton_etiqueta,
    rects_botones_apilados,
)
from Grafico.barra_estado import dibujar_estado_partida_en_barra
from Grafico.feedback_partida import (
    dibujar_feedback_partida,
    feedback_debe_avanzar,
    marcar_inicio_feedback,
    solucion_feedback_grafico,
)
from Comun.version import etiqueta_version
from Comun.textos_ui import OPCIONES_MENU_PRINCIPAL
from Grafico.textos_grafico import etiqueta_opcion_menu
from Grafico.tooltips_ui import (
    TOOLTIP_ABANDONAR_LIBRE,
    TOOLTIP_GUARDAR_INFORME,
    tooltip_menu_principal,
)
from Grafico.atajos_teclado import manejar_teclado_partida
from Grafico.textos_grafico import (
    BTN_ABANDONAR,
    BTN_CAMBIAR_OPCIONES,
    BTN_GUARDAR_INFORME,
    BTN_REPETIR_PARTIDA,
    BTN_VOLVER,
    BTN_VOLVER_MENU,
    etiqueta,
    titulo_pantalla,
)

if TYPE_CHECKING:
    from Grafico.app import DatosJuego

Y_WIZARD_CONTENIDO = 96

ALTURA_BARRA_PARTIDA = 58
GAP_BAJO_BARRA_PARTIDA = 20
Y_PANEL_PREGUNTA = ALTURA_BARRA_PARTIDA + GAP_BAJO_BARRA_PARTIDA
ALTO_PANEL_PREGUNTA = 150


def rect_enunciado_panel_pregunta(panel: pygame.Rect, *, con_meta: bool) -> pygame.Rect:
    """Área del texto de la pregunta dentro del panel (con o sin línea de metadatos)."""
    if con_meta:
        return pygame.Rect(panel.x + 8, panel.y + 36, panel.width - 16, panel.height - 44)
    return pygame.Rect(panel.x + 8, panel.y + 10, panel.width - 16, panel.height - 18)
ALTO_OPCION_PARTIDA = 64
SEP_OPCIONES_PARTIDA = 8
ALTO_BARRA_PROGRESO_PARTIDA = 8
GAP_TRAS_PANEL_PARTIDA = 12
GAP_TRAS_BARRA_PROGRESO = 10
MARGEN_INF_PARTIDA = 12
ALTO_BOTON_CONTINUAR_PARTIDA = 44


def fraccion_barra_progreso_partida(*, indice_pregunta: int, total: int) -> float:
    """Fracción 0–1 alineada con «Pregunta N/total» (pregunta actual, no respondidas)."""
    if total <= 0:
        return 0.0
    return min(1.0, (indice_pregunta + 1) / total)


class Pantalla:
    def titulo_pausa(self) -> str:
        return "Pantalla actual"

    def en_partida_activa(self) -> bool:
        """True en pantallas de partida (Esc abre pausa)."""
        return False

    def atajo_avanzar(self) -> bool:
        """Enter / avanzar: True si la pantalla consumió la tecla."""
        from Grafico.atajos_teclado import pulsar_primer_boton

        return pulsar_primer_boton(
            self,
            "boton_empezar",
            "boton_siguiente",
            "boton_continuar",
            "boton_enviar",
        )

    def atajo_retroceder(self) -> bool:
        """Retroceso / volver: True si la pantalla consumió la tecla."""
        from Grafico.atajos_teclado import pulsar_primer_boton

        return pulsar_primer_boton(self, "boton_volver", "boton_atras")

    def atajo_opcion_numerica(self, indice: int) -> bool:
        """Tecla 1–9 en menús con lista de botones."""
        from Grafico.atajos_teclado import botones_menu_pantalla, pulsar_boton_indice

        botones = botones_menu_pantalla(self)
        if not botones:
            return False
        return pulsar_boton_indice(botones, indice)

    def manejar_evento(self, _evento: pygame.event.Event) -> Pantalla | None:
        return None

    def actualizar(self) -> Pantalla | None:
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        raise NotImplementedError

    def popup_bloqueante(self) -> bool:
        """Popup modal: bloquea y atenúa la barra fija hasta cerrarse (clic o tiempo)."""
        return False

    def dibujar_contenido_popup_bloqueante(self, superficie: pygame.Surface) -> None:
        """Panel del popup; la app dibuja el velo semitransparente antes."""

    def restaurar_vista_completa(self) -> None:
        """Tras pausa → Continuar: redibuja la pantalla actual con su UI completa."""
        for attr in (
            "botones",
            "boton_volver",
            "boton_abandonar",
            "boton_siguiente",
            "boton_atras",
            "boton_empezar",
            "boton_continuar",
            "botones_opcion",
            "botones_powerup",
            "botones_filtro",
            "botones_subfiltro",
        ):
            self._reset_hover_ui(getattr(self, attr, None))
        for par in getattr(self, "botones_ciclo", {}).values():
            self._reset_hover_ui(par)

    @staticmethod
    def _reset_hover_ui(grupo: object) -> None:
        if grupo is None:
            return
        if isinstance(grupo, Boton):
            grupo.hover = False
            return
        if isinstance(grupo, (list, tuple)):
            for item in grupo:
                Pantalla._reset_hover_ui(item)


_OPCIONES_MENU_EXCLUIDAS_GRAFICO = frozenset({"diarios"})


class MenuPrincipal(Pantalla):
    OPCIONES = tuple(
        o for o in OPCIONES_MENU_PRINCIPAL if o.id not in _OPCIONES_MENU_EXCLUIDAS_GRAFICO
    )

    def __init__(
        self,
        datos: DatosJuego,
        ir_a: Callable[[Pantalla], None],
        salir_app: Callable[[], None],
        abrir_feedback: Callable[[], None] | None = None,
    ) -> None:
        self.datos = datos
        self.ir_a = ir_a
        self.salir_app = salir_app
        self.abrir_feedback = abrir_feedback or datos.abrir_feedback
        perfil = datos.perfil
        if perfil.tipo_paquete == "minimo":
            self.mensaje = f"{datos.num_preguntas} preguntas  MATCAD mínimo"
        elif perfil.tipo_paquete == "completo":
            self.mensaje = (
                f"{datos.num_preguntas} preguntas  {datos.num_materias} materias  MATCAD completo"
            )
        elif perfil.paquete_completo:
            self.mensaje = (
                f"{datos.num_preguntas} preguntas  {datos.num_materias} materias  juego completo"
            )
        elif perfil.solo_csv:
            self.mensaje = (
                f"{datos.num_preguntas} preguntas  juego mínimo (CSV portable)"
            )
        else:
            self.mensaje = f"{datos.num_preguntas} preguntas  juego mínimo"
        self.mensaje = f"{self.mensaje}  {etiqueta_version()}"
        if datos.avisos_carga and perfil.tipo_paquete == "desarrollo":
            self.mensaje += "  revisa los avisos al arrancar"
        self.fuentes = crear_fuentes()
        self.botones = self._crear_botones()

    def _crear_botones(self) -> list[Boton]:
        fuente = self.fuentes["menu"]
        etiquetas = [etiqueta_opcion_menu(opcion) for opcion in self.OPCIONES]
        rects = rects_botones_apilados(
            etiquetas,
            fuente,
            x_centro=ANCHO // 2,
            y0=250,
            gap=14,
            ancho_min=420,
            alto_min=48,
        )
        botones: list[Boton] = []
        for opcion, rect in zip(self.OPCIONES, rects, strict=True):
            etiq = etiqueta_opcion_menu(opcion)
            boton = Boton(
                etiq,
                rect,
                capturar(self._al_pulsar, opcion.id),
                tooltip=tooltip_menu_principal(opcion.id, self.datos.perfil),
            )
            if not self.datos.perfil.modo_disponible(opcion.id):
                boton.activo = False
            botones.append(boton)
        return botones

    def _al_pulsar(self, opcion_id: str) -> None:
        if opcion_id == "salir":
            self.salir_app()
            return
        if not self.datos.perfil.modo_disponible(opcion_id):
            self.mensaje = self.datos.perfil.motivo_modo_no_disponible(opcion_id)
            return
        if opcion_id == "libre":
            from Grafico.pantallas_libre import ConfigOpcionesLibre

            self.ir_a(ConfigOpcionesLibre(self.datos, self.ir_a, self.salir_app))
            return
        if opcion_id == "historia":
            from Grafico.pantallas_historia import ConfigModoHistoria

            self.ir_a(ConfigModoHistoria(self.datos, self.ir_a, self.salir_app))
            return
        if opcion_id == "especiales":
            from Grafico.pantallas_modos import ConfigModosEspeciales

            self.ir_a(ConfigModosEspeciales(self.datos, self.ir_a, self.salir_app))
            return
        if opcion_id == "feedback":
            if self.abrir_feedback is not None:
                self.abrir_feedback()
            return
        self.mensaje = "Esta opción no está disponible."

    def atajo_retroceder(self) -> bool:
        self.salir_app()
        return True

    def atajo_avanzar(self) -> bool:
        for boton in self.botones:
            if boton.activo:
                boton.al_pulsar()
                return True
        return False

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
        dibujar_texto_centro(
            superficie,
            "CUESTIONARIO MATCAD",
            (ANCHO // 2, 110),
            self.fuentes["titulo"].get_height(),
            COLOR_TITULO,
            bold=True,
        )
        dibujar_texto_centro(
            superficie,
            self.mensaje,
            (ANCHO // 2, 175),
            self.fuentes["cuerpo"].get_height(),
            COLOR_TEXTO,
        )
        for boton in self.botones:
            boton.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(superficie, self.fuentes["pequena"], self.botones)
        dibujar_texto_centro(
            superficie,
            "Haz clic en una opción",
            (ANCHO // 2, ALTO - 40),
            self.fuentes["pie"].get_height(),
            COLOR_TEXTO,
        )

    def titulo_pausa(self) -> str:
        return "Menú principal"


def _segundos_pregunta_restantes(inicio: float, limite: int | None) -> int | None:
    if not limite:
        return None
    return max(0, int(limite - (time.monotonic() - inicio)))


class PartidaModoLibre(Pantalla):
    def __init__(
        self,
        *,
        nombre: str,
        pool: list[Pregunta],
        reglas: ReglasPartida,
        ir_a: Callable[[Pantalla], None],
        datos: DatosJuego,
        salir_app: Callable[[], None],
        infinito: bool = False,
        total_previsto: int | None = None,
        complejidad_min: int = 1,
        complejidad_max: int | None = None,
        niveles_complejidad: frozenset[int] | set[int] | None = None,
        meta_informe: dict | None = None,
        navegacion_fin: NavegacionFinPartida | None = None,
        estrategia_practica: str = "sin_historico",
    ) -> None:
        self.nombre = nombre
        self.pool = list(pool)
        self.estrategia_practica = estrategia_practica
        from Comun.pool_libre import peso_pregunta_libre_desde_estrategia

        self._peso_pregunta = peso_pregunta_libre_desde_estrategia(
            datos.perfil,
            datos.materias_meta,
            estrategia_practica,
        )
        self.infinito = infinito
        self.total = None if infinito else (total_previsto or len(self.pool))
        if niveles_complejidad is not None:
            self.niveles_complejidad = normalizar_niveles_seleccionados(
                niveles_complejidad,
                self.pool,
            )
        else:
            rango = set(range(complejidad_min, (complejidad_max or max_complejidad_pool(self.pool)) + 1))
            self.niveles_complejidad = normalizar_niveles_seleccionados(rango, self.pool)
        self.meta_informe = meta_informe or {}
        self.navegacion_fin = navegacion_fin
        self.registros: list = []
        self.ir_a = ir_a
        self.datos = datos
        self.salir_app = salir_app
        self.fuentes = crear_fuentes()
        self.estado = EstadoPartida(
            nombre=nombre,
            reglas=reglas,
            vidas_restantes=vidas_iniciales_partida(reglas),
        )
        self.indice_global = 0
        self.fase = "pregunta"
        self.feedback_mensaje = ""
        self.feedback_solucion: str | None = None
        self.feedback_ok = False
        self.respuesta_elegida = ""
        self.botones_opcion: list[BotonOpcion] = []
        self._presentacion_opciones: PresentacionOpcionesPregunta | None = None
        self.seleccion_pool = crear_estado_seleccion(len(self.pool))
        self.semilla_partida = semilla_partida_aleatoria()
        self._rng_partida = crear_rng_partida(self.semilla_partida)
        self.pregunta_idx: int | None = None
        self.inicio_pregunta = time.monotonic()
        self.inicio_feedback = 0.0
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
            tooltip=TOOLTIP_ABANDONAR_LIBRE,
        )
        if not self._cargar_siguiente_pregunta(inicial=True):
            raise IndexError("Sin preguntas disponibles.")
        self._reconstruir_opciones()

    def en_partida_activa(self) -> bool:
        return True

    def _cargar_siguiente_pregunta(self, *, inicial: bool = False) -> bool:
        if not inicial and self.total is not None and self.indice_global >= self.total:
            return False
        idx = elegir_indice_siguiente(
            self.pool,
            self.seleccion_pool,
            modo_infinito=self.infinito,
            dificultad_progresiva=self.estado.reglas.dificultad_progresiva,
            niveles_complejidad=self.niveles_complejidad,
            respondidas=self.estado.respondidas,
            rng=self._rng_partida,
            peso_pregunta=self._peso_pregunta,
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
        if self.infinito:
            return ""
        assert self.total is not None
        return texto_progreso_examen_cerrado(self.indice_global + 1, self.total)

    def _kwargs_progreso_barra(self) -> dict:
        if self.infinito:
            return {
                "progreso": "",
                "numero_pregunta": self.indice_global + 1,
            }
        return {"progreso": self._texto_progreso()}

    def _linea_estado_actual(self) -> str:
        seg_preg = None
        if self.fase == "pregunta":
            seg_preg = _segundos_pregunta_restantes(
                self.inicio_pregunta,
                self.estado.reglas.tiempo_por_pregunta_seg,
            )
        return linea_estado(
            self.estado,
            segundos_pregunta_restantes=seg_preg,
            **self._kwargs_progreso_barra(),
        )

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
            fuentes=self.fuentes,
            x_centro_min=x_centro_min,
            x_centro_max=x_centro_max,
            segundos_pregunta_restantes=seg_preg,
            **self._kwargs_progreso_barra(),
        )
        if self.nombre and not es_nombre_anonimo(self.nombre):
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
        disponibles = niveles_en_pool(self.pool)
        if len(disponibles) > 1 and (
            self.niveles_complejidad != disponibles
            or self.estado.reglas.dificultad_progresiva
        ):
            if self.estado.reglas.dificultad_progresiva:
                techo = techo_complejidad_partida(
                    dificultad_progresiva=True,
                    respondidas=self.estado.respondidas,
                    niveles_seleccion=self.niveles_complejidad,
                )
                partes.append(f"Niv. {techo} ({describe_niveles_seleccion(self.niveles_complejidad)})")
            else:
                partes.append(f"Niv. {describe_niveles_seleccion(self.niveles_complejidad)}")
        return "  ".join(partes)

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

    def _aplicar_resultado(self, resultado: ResultadoRespuesta) -> None:
        p = self._pregunta_actual()
        feedback = evaluar_respuesta(p, self.estado, resultado)
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
        self.respuesta_elegida = letra
        self._aplicar_resultado(
            ResultadoRespuesta(acierto=acierto, respuesta=letra_dataset)
        )

    def _responder_timeout(self) -> None:
        if self.fase != "pregunta":
            return
        self.respuesta_elegida = ""
        self._aplicar_resultado(
            ResultadoRespuesta(acierto=False, respuesta="", tiempo_agotado=True)
        )

    def _abandonar(self) -> None:
        if self.registros:
            self.ir_a(self._ir_a_resumen(abandonado=True))
            return
        self.ir_a(MenuPrincipal(self.datos, self.ir_a, self.salir_app))

    def _ir_a_resumen(self, *, abandonado: bool = False) -> Pantalla:
        total_prev = (
            self.total
            if self.total is not None
            else max(1, self.estado.respondidas)
        )
        cierre = None
        if self.registros:
            titulo_txt = (
                "ABANDONO (modo libre)" if abandonado else "FIN DE PARTIDA (modo libre)"
            )
            cierre = CierreInformePartida(
                registros=list(self.registros),
                titulo=titulo_txt,
                total_previsto=total_prev,
                prefijo="partida_libre",
                meta=dict(self.meta_informe),
                abandonado=abandonado,
            )
        return ResumenPartida(
            self.estado,
            total_prev,
            self.ir_a,
            self.datos,
            self.salir_app,
            cierre_informe=cierre,
            titulo="PARTIDA ABANDONADA" if abandonado else "FIN DE PARTIDA",
            navegacion_fin=self.navegacion_fin,
        )

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
        return f"{self.nombre}  {self._linea_estado_actual()}"

    def _actualizar_hover_partida_libre(self, pos: tuple[int, int]) -> None:
        self.boton_abandonar.actualizar_hover(pos)
        if self.fase != "pregunta":
            return
        for boton in self.botones_opcion:
            boton.actualizar_hover(pos)

    def _manejar_clic_partida_libre(self, pos: tuple[int, int], boton: int) -> bool:
        if self.boton_abandonar.manejar_clic(pos, boton):
            self._abandonar()
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
            self._actualizar_hover_partida_libre(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if self._manejar_clic_partida_libre(evento.pos, evento.button):
                return None
        return None

    def _dibujar_feedback(self, superficie: pygame.Surface) -> None:
        dibujar_feedback_partida(
            superficie,
            self.fuentes,
            mensaje=self.feedback_mensaje,
            solucion=self.feedback_solucion,
            acierto=self.feedback_ok,
            y_mensaje=self._y_fin_opciones() + 10,
        )

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        self._dibujar_barra_superior(superficie)

        p = self._pregunta_actual()
        panel = pygame.Rect(MARGEN, Y_PANEL_PREGUNTA, ANCHO - 2 * MARGEN, ALTO_PANEL_PREGUNTA)
        dibujar_panel(superficie, panel)
        mostrar_meta = self.datos.perfil.mostrar_metadatos_pregunta
        if mostrar_meta:
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
            rect_enunciado_panel_pregunta(panel, con_meta=mostrar_meta),
            COLOR_TITULO,
        )

        # Progreso finito: misma noción que «Pregunta N/total»; en infinito no se muestra.
        if self.total is not None and self.total > 0:
            barra_y = Y_PANEL_PREGUNTA + panel.height + GAP_TRAS_PANEL_PARTIDA
            barra_fondo = pygame.Rect(
                MARGEN, barra_y, ANCHO - 2 * MARGEN, ALTO_BARRA_PROGRESO_PARTIDA
            )
            pygame.draw.rect(superficie, (40, 56, 80), barra_fondo, border_radius=4)
            frac = fraccion_barra_progreso_partida(
                indice_pregunta=self.indice_global, total=self.total
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
            self._dibujar_feedback(superficie)
        dibujar_tooltips_botones(
            superficie, self.fuentes["pequena"], [self.boton_abandonar]
        )


class ResumenPartida(Pantalla):
    def __init__(
        self,
        estado: EstadoPartida,
        total_previsto: int,
        ir_a: Callable[[Pantalla], None],
        datos: DatosJuego,
        salir_app: Callable[[], None],
        *,
        cierre_informe: CierreInformePartida | None = None,
        titulo: str = "FIN DE PARTIDA",
        subtitulo: str | None = None,
        lineas_tras_jugador: tuple[str, ...] = (),
        navegacion_fin: NavegacionFinPartida | None = None,
    ) -> None:
        self.estado = estado
        self.total_previsto = total_previsto
        self.ir_a = ir_a
        self.datos = datos
        self.salir_app = salir_app
        self.cierre_informe = cierre_informe
        self.navegacion_fin = navegacion_fin
        self.titulo_pantalla = titulo
        self.subtitulo = subtitulo
        self.lineas_tras_jugador = lineas_tras_jugador
        self.fuentes = crear_fuentes()
        self.lineas = self._construir_lineas()
        self.mensaje_pie = ""
        self._botones_accion: list[Boton] = []
        self._crear_botones_accion()
        y_botones = ALTO - 88
        if len(self._botones_accion) == 1:
            posicionar_pila_inferior(
                self._botones_accion,
                x_centro=ANCHO // 2,
                gap=0,
                margen_inferior=20,
            )
        else:
            posicionar_botones_fila(
                self._botones_accion,
                y_botones,
                x_centro=ANCHO // 2,
                gap=10,
            )

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
                    tooltip="Misma configuración; preguntas nuevas.",
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

    def _construir_lineas(self) -> list[str]:
        abandonado = bool(self.cierre_informe and self.cierre_informe.abandonado)
        lineas: list[str] = []
        if self.subtitulo:
            lineas.append(self.subtitulo)
        lineas.extend(
            lineas_resumen_breve(
                self.estado,
                self.total_previsto,
                mostrar_aciertos=True,
                abandonado=abandonado,
            )
        )
        return lineas

    def atajo_avanzar(self) -> bool:
        self._ir_menu()
        return True

    def _persistir_estadisticas_si_procede(self) -> None:
        if not self.cierre_informe or not self.cierre_informe.registros:
            return
        try:
            from Comun.estadisticas_jugador import registrar_cierre_partida

            registrar_cierre_partida(self.estado, self.cierre_informe)
        except OSError:
            pass

    def _guardar_informe_si_procede(self) -> bool:
        self._persistir_estadisticas_si_procede()
        if not self.cierre_informe or not self.cierre_informe.registros:
            return True
        if not guardar_informes_txt_habilitados():
            return True
        ruta = guardar_informe_cierre(self.estado, self.cierre_informe)
        if ruta is None:
            self.mensaje_pie = "No se pudo guardar el informe."
            return False
        return True

    def _ir_menu(self) -> None:
        if not self._guardar_informe_si_procede():
            return
        self.ir_a(MenuPrincipal(self.datos, self.ir_a, self.salir_app))

    def _repetir(self) -> None:
        if not self._guardar_informe_si_procede():
            return
        if self.navegacion_fin and self.navegacion_fin.repetir:
            self.ir_a(self.navegacion_fin.repetir())

    def _configurar(self) -> None:
        if not self._guardar_informe_si_procede():
            return
        if self.navegacion_fin and self.navegacion_fin.configurar:
            self.ir_a(self.navegacion_fin.configurar())

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if evento.type == pygame.MOUSEMOTION:
            for boton in self._botones_accion:
                boton.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            for boton in self._botones_accion:
                if boton.manejar_clic(evento.pos, evento.button):
                    break
        return None

    def dibujar(self, superficie: pygame.Surface) -> None:
        superficie.fill(COLOR_FONDO)
        rect_titulo = dibujar_texto_centro(
            superficie,
            titulo_pantalla(self.titulo_pantalla),
            (ANCHO // 2, 80),
            self.fuentes["titulo"].get_height(),
            COLOR_TITULO,
            bold=True,
            ancho_max=ANCHO - 2 * MARGEN,
        )
        y_nombre = rect_titulo.bottom + 28
        paso_linea = 42
        for linea in (f"Jugador: {self.estado.nombre}", *self.lineas_tras_jugador):
            txt = self.fuentes["menu"].render(
                preparar_texto_ui(linea), True, COLOR_TEXTO
            )
            superficie.blit(txt, txt.get_rect(center=(ANCHO // 2, y_nombre)))
            y_nombre += paso_linea
        y = y_nombre
        for i, linea in enumerate(self.lineas):
            if linea.startswith(("Cada partida", "Los informes")):
                fuente = self.fuentes["pequena"]
            elif i == 0 and self.subtitulo:
                fuente = self.fuentes["subtitulo"]
            else:
                fuente = self.fuentes["cuerpo"]
            txt = fuente.render(preparar_texto_ui(linea), True, COLOR_TEXTO)
            superficie.blit(txt, txt.get_rect(center=(ANCHO // 2, y)))
            y += 34 if fuente == self.fuentes["pequena"] else paso_linea
        if self.mensaje_pie:
            aviso = self.fuentes["menu"].render(self.mensaje_pie, True, COLOR_AVISO)
            y_aviso = self._botones_accion[0].rect.y - 40
            superficie.blit(aviso, aviso.get_rect(center=(ANCHO // 2, y_aviso)))
        for boton in self._botones_accion:
            boton.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(
            superficie, self.fuentes["pequena"], self._botones_accion
        )

    def titulo_pausa(self) -> str:
        return "Fin de partida"
