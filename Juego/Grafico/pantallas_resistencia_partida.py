#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pantalla de partida del modo resistencia (preset especial)."""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from typing import TYPE_CHECKING

import pygame

from Comun.modelos import Pregunta
from Comun.motor_nucleo import (
    EstadoPartida,
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
from Comun.objetos_partida import (
    segundos_pregunta_restantes,
    tiempo_pregunta_agotado,
)
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
    segmento_bloque_filtro_barra,
    separar_emoji_mensaje,
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
    partes_texto_barra_resistencia,
    texto_efectos_escalada,
    texto_meta_pregunta_resistencia,
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
from Comun.presets_historia import PresetHistoria, config_defecto
from Comun.preferencias_grafico import emojis_habilitados, nombre_jugador_grafico
from Comun.reglas import ReglasPartida, formatear_resultado_puntuacion, vidas_iniciales_partida
from Comun.informe_examen import CierreInformePartida, meta_cierre_historia
from Grafico.atajos_teclado import manejar_teclado_partida
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
    evento_clic_salta_espera,
    evento_tecla_salta_espera,
    feedback_debe_avanzar,
    marcar_inicio_feedback,
    solucion_feedback_grafico,
)
from Grafico.barra_estado import dibujar_estado_partida_en_barra
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
    rect_enunciado_panel_pregunta,
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
    TAMANO_FUENTE_PEQUENA,
    Y_INICIO_TITULO,
    crear_fuentes,
    x_min_centro_barra_partida,
)
from Grafico.ui import (
    ALTO_BOTON_COMPACTO,
    FILA_ALTURA_BOTONES_COMPACTOS,
    GAP_BOTONES_COMPACTOS,
    PADDING_BANDA_BOTONES_COMPACTOS,
    PADDING_BOTON_COMPACTO_X,
    Boton,
    BotonOpcion,
    CampoEntero,
    _fuente_ajustada,
    ancho_boton_etiqueta,
    capturar,
    dibujar_caja_valor_ciclo,
    dibujar_panel,
    dibujar_texto_multilinea,
    dibujar_tooltips_botones,
    empaquetar_anchos_en_filas,
    posicionar_botones_fila,
    posicionar_pila_inferior,
    rect_boton_etiqueta,
    tamano_grupo_botones,
    unir_partes_cabientes,
)
from Grafico.texto import (
    dibujar_texto_centro,
    medir_texto_mixto,
    preparar_texto_ui,
    renderizar_texto_mixto,
    texto_requiere_fuentes_mixtas,
)

if TYPE_CHECKING:
    from Grafico.app import DatosJuego

class PartidaResistencia(Pantalla):
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
        from Comun.motor_nucleo import NavegacionFinPartida

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
        self.er = crear_estado_resistencia(vidas_iniciales_partida(reglas))
        self.er.banco_resistencia = banco
        configurar_partida_resistencia(
            self.er,
            preset_id=self.preset.id,
            sin_escalada_dificultad=datos.perfil.resistencia_solo_eventos,
        )
        self.escalada = escalada_para_pregunta(1, er=self.er)
        vidas_ini = vidas_iniciales_partida(reglas)
        self.estado = EstadoPartida(
            nombre=nombre,
            reglas=aplicar_escalada_a_reglas(reglas, self.escalada),
            vidas_restantes=vidas_ini,
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
        self.avisos_recompensa_pendientes: list[str] = []
        self.aviso_es_recompensa = False
        self.indice_aviso = 0
        self.inicio_aviso = 0.0
        self.boton_evento_si: Boton | None = None
        self.boton_evento_no: Boton | None = None
        self.botones_opcion: list[BotonOpcion] = []
        self._presentacion_opciones: PresentacionOpcionesPregunta | None = None
        self.botones_powerup: list[Boton] = []
        self.inicio_pregunta = time.monotonic()
        self.inicio_feedback = 0.0
        self._timer_pausa_acum_seg = 0.0
        self._timer_pausa_desde: float | None = None
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

    def _fases_pausa_timers(self) -> bool:
        return self.fase in ("aviso", "evento_si_no")

    def _barra_muestra_estado_pregunta(self) -> bool:
        """Cronómetro y símbolos de la pregunta solo cuando empieza a contar el tiempo."""
        return self.fase == "pregunta"

    def _barra_muestra_bloque_filtro(self) -> bool:
        """Bloque temático activo: visible en pregunta y feedback (como progreso de puerta en escape)."""
        return self.fase in ("pregunta", "feedback")

    def _reset_pausa_timer_pregunta(self) -> None:
        self._timer_pausa_acum_seg = 0.0
        self._timer_pausa_desde = None

    def _pausa_timer_pregunta_seg(self) -> float:
        pausa = self._timer_pausa_acum_seg
        if self._timer_pausa_desde is not None:
            pausa += time.monotonic() - self._timer_pausa_desde
        return pausa

    def _sincronizar_pausa_timers(self) -> None:
        from Comun.maldiciones_partida import desafio_maldicion_activo

        pausar = self._fases_pausa_timers()
        desafio = desafio_maldicion_activo(self.er.maldicion)
        if pausar:
            if self._timer_pausa_desde is None:
                self._timer_pausa_desde = time.monotonic()
            if desafio is not None:
                desafio.pausar()
        else:
            if self._timer_pausa_desde is not None:
                self._timer_pausa_acum_seg += time.monotonic() - self._timer_pausa_desde
                self._timer_pausa_desde = None
            if desafio is not None:
                desafio.reanudar()

    def _iniciar_fase_pregunta(self) -> None:
        p = self._pregunta_actual()
        aplicar_modificadores_visuales_escalada(
            self.er, self.escalada, p, self._numero_pregunta()
        )
        self.fase = "pregunta"
        self.inicio_pregunta = time.monotonic()
        self._reset_pausa_timer_pregunta()
        self.avisos_cola = []
        self.indice_aviso = 0
        self._reconstruir_opciones()
        self._reconstruir_powerups()

    def _iniciar_cola_avisos(
        self,
        avisos: list[str],
        *,
        es_recompensa: bool = False,
    ) -> None:
        self._reset_pausa_timer_pregunta()
        self.avisos_cola = avisos
        self.aviso_es_recompensa = es_recompensa
        self.indice_aviso = 0
        self.fase = "aviso"
        self.inicio_aviso = marcar_inicio_aviso()
        self.botones_opcion = []
        self.botones_powerup = []

    def _titulo_aviso_resistencia(self) -> str:
        total = len(self.avisos_cola)
        if self.aviso_es_recompensa:
            base = "Recompensa"
        else:
            base = "Esta pregunta"
        if total <= 1:
            return base
        return f"{base} ({self.indice_aviso + 1}/{total})"

    def _entrar_pregunta_o_avisos(self) -> None:
        if self.er.evento_si_no:
            self.fase = "evento_si_no"
            self._reconstruir_botones_evento_si_no()
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
            self._iniciar_cola_avisos(avisos, es_recompensa=False)
            return
        self._iniciar_fase_pregunta()

    def _reconstruir_botones_evento_si_no(self) -> None:
        lbl_si = etiqueta(*BTN_APUESTA_SI)
        lbl_no = etiqueta(*BTN_APUESTA_NO)
        tam = 56
        gap = 20
        y = ALTO // 2 + 122
        cx = ANCHO // 2
        evento = self.er.evento_si_no
        puede_si = (
            evento is not None
            and puede_aceptar_evento_si_no(evento, self.estado, self.er) is None
        )
        tooltip_si = TOOLTIP_EVENTO_SI_NO_SI
        if evento is not None and evento.requiere_puntos and not puede_si:
            err = puede_aceptar_evento_si_no(evento, self.estado, self.er)
            tooltip_si = err or TOOLTIP_EVENTO_SI_NO_SI
        elif evento is not None and evento.es_riesgo_en_pregunta:
            tooltip_si = TOOLTIP_EVENTO_SI_NO_SI_RIESGO
        self.boton_evento_si = Boton(
            lbl_si,
            pygame.Rect(cx - tam - gap // 2, y, tam, tam),
            self._aceptar_evento_si_no,
            tooltip=tooltip_si,
            familia_etiqueta="emoji",
        )
        self.boton_evento_si.activo = puede_si
        self.boton_evento_no = Boton(
            lbl_no,
            pygame.Rect(cx + gap // 2, y, tam, tam),
            self._rechazar_evento_si_no,
            tooltip=TOOLTIP_EVENTO_SI_NO_NO,
            familia_etiqueta="emoji",
        )

    def en_partida_activa(self) -> bool:
        return True

    def atajo_avanzar(self) -> bool:
        if self.fase == "evento_si_no":
            from Grafico.atajos_teclado import pulsar_boton_si_activo

            return pulsar_boton_si_activo(self.boton_evento_si)
        return False

    def atajo_opcion_numerica(self, indice: int) -> bool:
        if self.fase == "evento_si_no":
            from Grafico.atajos_teclado import pulsar_boton_si_activo

            if indice == 1:
                return pulsar_boton_si_activo(self.boton_evento_si)
            if indice == 2:
                return pulsar_boton_si_activo(self.boton_evento_no)
            return False
        return super().atajo_opcion_numerica(indice)

    def _aceptar_evento_si_no(self) -> None:
        evento = self.er.evento_si_no
        if evento is None:
            return
        err = aceptar_evento_si_no(
            evento,
            self.estado,
            self.er,
            numero_pregunta=self._numero_pregunta(),
        )
        if err:
            self._reconstruir_botones_evento_si_no()
            return
        self.er.evento_si_no = None
        self._entrar_pregunta_o_avisos()

    def _rechazar_evento_si_no(self) -> None:
        self.er.evento_si_no = None
        self._entrar_pregunta_o_avisos()

    def _segundos_restantes_pregunta(self) -> int | None:
        return segundos_pregunta_restantes(
            self.inicio_pregunta,
            self._limite_tiempo_pregunta(),
            factor_velocidad=self.er.factor_velocidad_tiempo,
            pausa_seg=self._pausa_timer_pregunta_seg(),
        )

    def _limite_tiempo_pregunta(self) -> int | None:
        return tiempo_pregunta_efectivo(
            self.estado.reglas.tiempo_por_pregunta_seg,
            self.er,
        )

    def _numero_pregunta(self) -> int:
        return self.indice_global + 1

    def _aplicar_escalada(self, numero_pregunta: int) -> None:
        self.escalada = escalada_para_pregunta(numero_pregunta, er=self.er)
        self.estado.reglas = aplicar_escalada_a_reglas(self.reglas_base, self.escalada)
        self.efecto_actual = texto_efectos_escalada(self.escalada)

    def _cargar_siguiente_pregunta(self) -> bool:
        self.er.reset_pregunta()
        numero = self._numero_pregunta()
        self._aplicar_escalada(numero)
        avisos_turno = preparar_eventos_nuevo_turno(
            self.er, self.pool, numero, self.estado
        )
        self.avisos_pendientes.extend(avisos_turno)
        idx = elegir_indice_resistencia(
            self.pool, self.seleccion_pool, self.escalada, numero, er=self.er
        )
        if idx is None:
            return False
        self.pregunta_idx = idx
        return True

    def _pregunta_actual(self) -> Pregunta:
        if self.pregunta_idx is None:
            raise IndexError("Sin pregunta cargada.")
        return self.pool[self.pregunta_idx]

    def _filas_layout_powerups(
        self,
    ) -> list[list[tuple[str, int, int, str]]]:
        """Filas de (id, cantidad, ancho, etiqueta) sin desbordar el ancho útil."""
        items = [
            (pid, self.er.cantidad(pid))
            for pid in sorted(self.er.inventario.keys())
            if self.er.cantidad(pid) > 0
        ]
        if not items:
            return []
        metas: list[tuple[str, int, int, str]] = []
        for pid, cant in items:
            nombre = etiqueta_powerup(pid)
            etiqueta_btn = prefijar_emoji(f"{nombre} ({cant})", emoji_powerup(pid))
            ancho = ancho_boton_etiqueta(
                etiqueta_btn,
                self.fuentes["pequena"],
                padding_x=PADDING_BOTON_COMPACTO_X,
            )
            metas.append((pid, cant, ancho, etiqueta_btn))
        filas_anchos = empaquetar_anchos_en_filas(
            [m[2] for m in metas],
            ancho_disponible=ANCHO - 2 * MARGEN,
            gap=GAP_BOTONES_COMPACTOS,
        )
        filas: list[list[tuple[str, int, int, str]]] = []
        cursor = 0
        for fila_anchos in filas_anchos:
            n = len(fila_anchos)
            filas.append(metas[cursor : cursor + n])
            cursor += n
        return filas

    def _altura_banda_powerups(self) -> int:
        n_filas = len(self._filas_layout_powerups())
        if n_filas <= 0:
            return 0
        return n_filas * FILA_ALTURA_BOTONES_COMPACTOS + PADDING_BANDA_BOTONES_COMPACTOS

    def _y_banda_powerups(self) -> int:
        altura = self._altura_banda_powerups()
        if altura <= 0:
            return ALTO - MARGEN_INF_PARTIDA
        return ALTO - MARGEN_INF_PARTIDA - altura

    def _offset_y_panel(self) -> int:
        if not self._partes_texto_extra_layout():
            return 0
        return self.fuentes["pequena"].get_height() + 22

    def _ancho_texto_extra(self) -> int:
        x_centro_min = x_min_centro_barra_partida(self.fuentes["menu"])
        return max(80, ANCHO - MARGEN - x_centro_min)

    def _partes_texto_extra_contenido(self) -> list[str]:
        from Comun.resistencia_motor import texto_bloque_filtro_extra

        partes: list[str] = []
        bloque_extra = texto_bloque_filtro_extra(self.er)
        if bloque_extra:
            partes.append(bloque_extra)
        if self.er.sin_escalada_dificultad:
            limite = self._limite_tiempo_pregunta()
            partes.extend(
                partes_texto_barra_resistencia(
                    self.escalada,
                    self.er,
                    limite_tiempo_seg=limite,
                )
            )
            return partes
        partes.extend(partes_texto_efectos_escalada(self.escalada, solo_eventos=False))
        return partes

    def _partes_texto_extra_layout(self) -> list[str]:
        return self._partes_texto_extra_contenido()

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

    def _texto_desafio_bloque_barra(self) -> str | None:
        if not self._barra_muestra_estado_pregunta():
            return None
        return texto_segmento_desafio_bloque(self.er)

    def _texto_bloque_filtro_barra(self) -> str | None:
        if not self._barra_muestra_bloque_filtro():
            return None
        return segmento_bloque_filtro_barra(self.er)

    def _comprobar_desafio_bloque_expirado(self) -> bool:
        if not desafio_bloque_expirado(self.er):
            return False
        self.avisos_pendientes.append(
            finalizar_partida_por_desafio_bloque(self.estado, self.er)
        )
        return True

    def _linea_estado_actual(self) -> str:
        seg_preg = None
        if self._barra_muestra_estado_pregunta():
            seg_preg = self._segundos_restantes_pregunta()
        return linea_estado(
            self.estado,
            "",
            segundos_pregunta_restantes=seg_preg,
            vidas_max=self.er.vidas_max,
            numero_pregunta=self._numero_pregunta(),
            racha=self.er.racha,
            desafio_bloque_texto=self._texto_desafio_bloque_barra(),
            bloque_filtro_texto=self._texto_bloque_filtro_barra(),
        )

    def _reconstruir_powerups(self) -> None:
        from Comun.maldiciones_partida import objetos_bloqueados_efectivo_resistencia

        self.botones_powerup = []
        if self.fase != "pregunta":
            return
        objetos_bloqueados = objetos_bloqueados_efectivo_resistencia(self.er)
        filas = self._filas_layout_powerups()
        if not filas:
            return
        y = self._y_banda_powerups()
        for fila in filas:
            x = MARGEN
            for pid, _cant, ancho, etiqueta_btn in fila:
                rect = pygame.Rect(x, y, ancho, ALTO_BOTON_COMPACTO)
                boton = Boton(
                    etiqueta_btn,
                    rect,
                    capturar(self._usar_powerup, pid),
                    tooltip=descripcion_powerup(pid),
                    padding_etiqueta_x=PADDING_BOTON_COMPACTO_X,
                    alinear_etiqueta="izquierda",
                )
                boton.activo = not objetos_bloqueados and (
                    puede_usar_powerup_en_pregunta(pid, self.er.powerups_usados_en_pregunta)
                    is None
                )
                if objetos_bloqueados:
                    boton.tooltip = "Maldición activa: no puedes usar objetos."
                self.botones_powerup.append(boton)
                x += ancho + GAP_BOTONES_COMPACTOS
            y += FILA_ALTURA_BOTONES_COMPACTOS

    def _reconstruir_opciones(self) -> None:
        from Comun.resistencia_motor import rng_partida

        p = self._pregunta_actual()
        self._presentacion_opciones = presentacion_opciones_pantalla(
            p, rng=rng_partida(self.er)
        )
        self.botones_opcion = []
        y = self._y_inicio_opciones()
        for etiqueta, texto, letra_ds in self._presentacion_opciones.filas:
            texto_visible = texto_opcion_visible_pantalla(
                texto,
                letra_ds,
                letras_eliminadas=self.er.letras_ocultas,
                letras_niebla=self.er.letras_niebla,
            )
            if texto_visible is None:
                continue
            rect = pygame.Rect(MARGEN, y, ANCHO - 2 * MARGEN, ALTO_OPCION_PARTIDA)
            boton = BotonOpcion(
                etiqueta,
                texto_visible,
                rect,
                capturar(self._responder, etiqueta),
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
            if self.er.skip_sin_cortar_racha > 0:
                self.er.skip_sin_cortar_racha -= 1
            else:
                self.er.registrar_fallo()
            consumir_bloque_filtro(self.er)
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
                revocar_powerup_usado(self.er.powerups_usados_en_pregunta, "cambio")
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
            self.er.reiniciar_slot_pregunta()
            self._reconstruir_opciones()
            self._reconstruir_powerups()
            return
        if powerup_id in {"fifty_fifty", "bomba", "comodin", "descarte_inteligente"}:
            self._reconstruir_opciones()
        self._reconstruir_powerups()

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

    def _ajustar_multiplicador(self, resultado: ResultadoRespuesta, puntos_prev: int, mult_apuesta: int) -> None:
        from Comun.maldiciones_partida import multiplicador_puntos_maldicion

        aplicar_bonificaciones_puntos_resistencia(
            self.estado,
            puntos_prev=puntos_prev,
            racha=self.er.racha,
            mult_escalada=self.escalada.multiplicador_puntos,
            exclusiva=self._pregunta_actual().exclusiva_resistencia,
            acierto=resultado.acierto,
            tiempo_agotado=resultado.tiempo_agotado,
            mult_apuesta=mult_apuesta,
            mult_maldicion=multiplicador_puntos_maldicion(self.er.maldicion),
        )

    def _fin_partida(self, *, abandonado: bool = False) -> None:
        from Comun.generador_examen_historia import cargar_estadisticas_historicas

        cierre = None
        if self.registros:
            stats: dict = {}
            if (
                self.datos.perfil.analisis_historico_disponible
                and self.datos.path_historico is not None
            ):
                try:
                    stats = cargar_estadisticas_historicas(
                        self.datos.path_historico,
                        materias_validas=set(self.datos.materias_meta),
                    )
                except FileNotFoundError:
                    stats = {}
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
                meta={
                    **meta_cierre_historia(
                        preset_id=self.preset.id,
                        preset_nombre=self.preset.nombre,
                        perfil=self.preset.perfil,
                        materias=[],
                        n_preguntas=self.estado.respondidas,
                        modo_resistencia=True,
                        racha=self.er.mejor_racha,
                    ),
                    "resistencia_variedad_vista": sorted(self.er.variedad_vista),
                },
                stats_historicas=stats,
                abandonado=abandonado,
            )
        titulo_pantalla = (
            f"Pregunta {self.estado.respondidas} — {self.preset.nombre[:36]}"
            if not abandonado
            else f"Abandono — {self.preset.nombre[:40]}"
        )
        self.ir_a(
            ResumenResistencia(
                self.estado,
                self.preset,
                self.ir_a,
                self.datos,
                self.salir_app,
                cierre_informe=cierre,
                titulo=titulo_pantalla,
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

    def _mostrar_feedback_tras_respuesta(
        self,
        p: Pregunta,
        resultado: ResultadoRespuesta,
        mensaje: str,
        feedback,
        *,
        acierto_ok: bool,
    ) -> None:
        self.feedback_mensaje = mensaje
        if feedback.solucion and self._presentacion_opciones is not None:
            self.feedback_solucion = solucion_feedback_grafico(
                texto_solucion(p, self._presentacion_opciones)
            )
        else:
            self.feedback_solucion = solucion_feedback_grafico(feedback.solucion)
        self.feedback_ok = acierto_ok
        self.fase = "feedback"
        self.inicio_feedback = marcar_inicio_feedback()
        self.botones_powerup = []
        if self._presentacion_opciones is not None:
            marcar_botones_opciones_tras_respuesta(
                self.botones_opcion,
                presentacion=self._presentacion_opciones,
                correcta_dataset=p.correcta,
                respuesta_dataset=resultado.respuesta,
                acierto=resultado.acierto,
            )

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
            self.avisos_recompensa_pendientes.extend(turno.avisos_extra)
        if not turno.reintentar_pregunta:
            self._registrar_respuesta(p, resultado)

        feedback = turno.feedback
        mensaje = feedback.mensaje

        if feedback.sin_vidas or not self.estado.debe_continuar(None):
            self._mostrar_feedback_tras_respuesta(
                p, resultado, mensaje, feedback, acierto_ok=False
            )
            return

        self._mostrar_feedback_tras_respuesta(
            p,
            resultado,
            mensaje,
            feedback,
            acierto_ok=resultado.acierto and not resultado.tiempo_agotado,
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

    def _responder_timeout(self) -> None:
        if self.fase != "pregunta":
            return
        self._tras_respuesta(
            ResultadoRespuesta(acierto=False, respuesta="", tiempo_agotado=True)
        )

    def _pasar_a_siguiente_pregunta(self) -> None:
        consumir_bloque_filtro(self.er)
        self.indice_global += 1
        if not self._cargar_siguiente_pregunta():
            self._fin_partida()
            return
        self.feedback_mensaje = ""
        self.feedback_solucion = None
        self.feedback_ok = False
        self._entrar_pregunta_o_avisos()

    def _procesar_aviso_listo(self) -> None:
        self.indice_aviso += 1
        if self.indice_aviso < len(self.avisos_cola):
            self.inicio_aviso = marcar_inicio_aviso()
        elif self.aviso_es_recompensa:
            self.aviso_es_recompensa = False
            self._pasar_a_siguiente_pregunta()
        else:
            self._iniciar_fase_pregunta()

    def _continuar(self) -> None:
        if self.fase != "feedback":
            return
        if self._comprobar_desafio_bloque_expirado():
            self._fin_partida()
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
        if self.avisos_recompensa_pendientes:
            self._iniciar_cola_avisos(
                list(self.avisos_recompensa_pendientes),
                es_recompensa=True,
            )
            self.avisos_recompensa_pendientes = []
            return
        self._pasar_a_siguiente_pregunta()

    def actualizar(self) -> Pantalla | None:
        self._sincronizar_pausa_timers()
        if self._comprobar_desafio_bloque_expirado():
            self._fin_partida()
            return None
        if self.fase == "aviso":
            if aviso_debe_avanzar(self.inicio_aviso):
                self._procesar_aviso_listo()
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
        if lim and tiempo_pregunta_agotado(
            self.inicio_pregunta,
            lim,
            factor_velocidad=self.er.factor_velocidad_tiempo,
            pausa_seg=self._pausa_timer_pregunta_seg(),
        ):
            self._responder_timeout()
        return None

    def titulo_pausa(self) -> str:
        return f"{self.preset.nombre}  {self._linea_estado_actual()}"

    def popup_bloqueante(self) -> bool:
        return self.fase in ("aviso", "evento_si_no")

    def dibujar_contenido_popup_bloqueante(self, superficie: pygame.Surface) -> None:
        fuente = self.fuentes["menu"]
        if self.fase == "evento_si_no" and self.er.evento_si_no:
            evento = self.er.evento_si_no
            dibujar_contenido_aviso_resistencia(
                superficie,
                self.fuentes,
                mensaje=formatear_aviso_evento_si_no(evento),
                titulo=titulo_popup_evento_si_no(evento),
                mostrar_pie_espera=False,
            )
            if self.boton_evento_si:
                self.boton_evento_si.dibujar(superficie, fuente)
            if self.boton_evento_no:
                self.boton_evento_no.dibujar(superficie, fuente)
            tips_evento = [
                b
                for b in (self.boton_evento_si, self.boton_evento_no)
                if b is not None
            ]
            dibujar_tooltips_botones(superficie, self.fuentes["pequena"], tips_evento)
            return
        if self.fase == "aviso" and self.avisos_cola:
            dibujar_contenido_aviso_resistencia(
                superficie,
                self.fuentes,
                mensaje=self.avisos_cola[self.indice_aviso],
                indice=self.indice_aviso,
                total=len(self.avisos_cola),
                titulo=self._titulo_aviso_resistencia(),
            )

    def _texto_extra_layout(self) -> str:
        return self._texto_extra_barra()

    def _texto_extra_barra(self) -> str:
        if not self._barra_muestra_estado_pregunta():
            return ""
        partes = self._partes_texto_extra_contenido()
        if not partes:
            return ""
        return unir_partes_cabientes(
            partes,
            self.fuentes["pequena"],
            self._ancho_texto_extra(),
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
        altura_fuente = fuente.get_height()
        texto_extra = self._texto_extra_barra()
        y_estado = (ALTURA_BARRA_PARTIDA - altura_fuente) // 2
        seg_preg = None
        if self._barra_muestra_estado_pregunta():
            seg_preg = self._segundos_restantes_pregunta()
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
            desafio_bloque_texto=self._texto_desafio_bloque_barra(),
            bloque_filtro_texto=self._texto_bloque_filtro_barra(),
        )
        if texto_extra:
            ancho_extra = self._ancho_texto_extra()
            texto_dibujo = texto_extra
            if not emojis_habilitados():
                _, texto_dibujo = separar_emoji_mensaje(texto_extra)
            ancho_texto, _ = medir_texto_mixto(texto_dibujo, TAMANO_FUENTE_PEQUENA)
            x_extra = x_centro_min + max(0, (ancho_extra - ancho_texto) // 2)
            y_extra = ALTURA_BARRA_PARTIDA + 10
            renderizar_texto_mixto(
                superficie,
                texto_dibujo,
                (x_extra, y_extra),
                COLOR_AVISO,
                TAMANO_FUENTE_PEQUENA,
            )
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
        if self.fase == "evento_si_no":
            if self.boton_evento_si:
                self.boton_evento_si.actualizar_hover(pos)
            if self.boton_evento_no:
                self.boton_evento_no.actualizar_hover(pos)
            return
        if self.fase != "pregunta":
            return
        for boton in self.botones_powerup:
            boton.actualizar_hover(pos)
        for boton in self.botones_opcion:
            boton.actualizar_hover(pos)

    def _manejar_clic_evento_si_no(self, pos: tuple[int, int], boton: int) -> bool:
        if self.boton_evento_si and self.boton_evento_si.manejar_clic(pos, boton):
            return True
        return bool(
            self.boton_evento_no and self.boton_evento_no.manejar_clic(pos, boton)
        )

    def _manejar_clic_pregunta_resistencia(self, pos: tuple[int, int], boton: int) -> bool:
        for btn in self.botones_powerup:
            if btn.manejar_clic(pos, boton):
                return True
        return any(b.manejar_clic(pos, boton) for b in self.botones_opcion)

    def _manejar_clic_resistencia(self, pos: tuple[int, int], boton: int) -> bool:
        if self.boton_abandonar.manejar_clic(pos, boton):
            return True
        if self.fase == "feedback":
            self._continuar()
            return True
        if self.fase == "aviso":
            self._procesar_aviso_listo()
            return True
        if self.fase == "evento_si_no":
            return self._manejar_clic_evento_si_no(pos, boton)
        if self.fase == "pregunta":
            return self._manejar_clic_pregunta_resistencia(pos, boton)
        return False

    def manejar_evento(self, evento: pygame.event.Event) -> Pantalla | None:
        if self.fase == "aviso" and (
            evento_tecla_salta_espera(evento) or evento_clic_salta_espera(evento)
        ):
            self._procesar_aviso_listo()
            return None
        if self.fase in ("pregunta", "feedback") and manejar_teclado_partida(
            evento,
            fase=self.fase,
            botones_opcion=self.botones_opcion,
            on_responder=self._responder,
            on_continuar=self._continuar,
        ):
            return None
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
        if not self.er.sin_escalada_dificultad:
            meta_partes.append(
                texto_meta_pregunta_resistencia(
                    p,
                    self.escalada,
                    solo_eventos=False,
                )
            )
        mostrar_meta = bool(meta_partes)
        if mostrar_meta:
            meta = self.fuentes["pequena"].render(
                "  ".join(meta_partes),
                True,
                COLOR_AVISO if p.exclusiva_resistencia else COLOR_ACENTO,
            )
            superficie.blit(meta, (panel.x + 12, panel.y + 10))
        dibujar_texto_multilinea(
            superficie,
            self.fuentes["cuerpo"],
            self._pregunta_actual().texto,
            rect_enunciado_panel_pregunta(panel, con_meta=mostrar_meta),
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




class ResumenResistencia(ResumenPartida):
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
        abandonado: bool = False,
        mejor_racha: int | None = None,
        navegacion_fin=None,
    ) -> None:
        self.preset = preset
        self.abandonado_resistencia = abandonado
        self.mejor_racha = mejor_racha if mejor_racha is not None else estado.aciertos
        titulo_resumen = titulo or f"FIN — {preset.nombre[:44]}"
        super().__init__(
            estado,
            estado.respondidas,
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
        lineas = lineas_resumen_breve(
            self.estado,
            self.total_previsto,
            mostrar_aciertos=mostrar_aciertos,
            abandonado=abandonado,
        )
        lineas.insert(0, f"Preguntas respondidas: {self.estado.respondidas}")
        lineas.insert(1, f"Mejor racha (bonificación puntos): {self.mejor_racha}")
        return lineas
