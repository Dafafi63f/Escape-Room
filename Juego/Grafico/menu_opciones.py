#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Panel superpuesto de opciones globales (barra fija de la app gráfica)."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from Comun.jugador import es_nombre_anonimo, nombre_jugador_efectivo
from Comun.datos_locales_juego import borrar_txt_informes_feedback, vaciar_preferencias_locales
from Comun.ranking_resistencia import vaciar_ranking_variante
from Comun.preferencias_grafico import (
    PreferenciasGrafico,
    cargar_preferencias_grafico,
    ciclar_emojis,
    ciclar_guardar_informes,
    ciclar_tooltips,
    guardar_preferencias_grafico,
    nombre_inicial_grafico,
)
from Grafico.tema import (
    ALTO,
    ANCHO,
    MARGEN,
    crear_fuentes,
)
from Grafico.texto import dibujar_texto_centro
from Grafico.textos_grafico import (
    BTN_BORRAR_RANKING,
    BTN_BORRAR_TXT_INFORMES,
    BTN_VACIAR_PREFERENCIAS,
    etiqueta,
)
from Grafico.ui import (
    Boton,
    CampoTexto,
    dibujar_caja_valor_ciclo,
    dibujar_panel,
    dibujar_tooltips_botones,
    rect_boton_etiqueta,
)


_COLOR_ETIQUETA_PANEL = (70, 80, 95)


class OverlayOpcionesGrafico:
    """Opciones globales: nombre, tooltips, emojis y borrado local."""

    ANCHO_BTN_CICLO = 40
    ALTO_CTRL = 36
    GAP_CICLO = 8
    ANCHO_CICLO = 200

    # Desplazamientos verticales respecto a ``panel.y``.
    _Y_SUBTITULO = 58
    _Y_CAMPO_NOMBRE = 104
    _Y_TOOLTIPS_LBL = 160
    _Y_TOOLTIPS_FILA = 184
    _Y_EMOJIS_LBL = 232
    _Y_EMOJIS_FILA = 256
    _Y_INFORMES_LBL = 296
    _Y_INFORMES_FILA = 320
    _GAP_TRAS_FILA_CICLO = 14
    _GAP_CAMPO_RESTABLECER = 12
    _ANCHO_FRACCION_CAMPO_NOMBRE = 0.58
    _Y_BORRADO_LBL = _Y_INFORMES_FILA + ALTO_CTRL + _GAP_TRAS_FILA_CICLO
    _GAP_HINT_BORRADO = 18
    _GAP_ZONA_BORRADO = 12
    _GAP_BORRADO_FILAS = 10
    _GAP_BORRADO_COLUMNAS = 16
    _MARGEN_PANEL_INFERIOR = 24
    _MARGEN_VENTANA_INFERIOR = 44
    _Y_PANEL = 58

    def __init__(self, *, on_cerrar: Callable[[], None]) -> None:
        self.on_cerrar = on_cerrar
        self.fuentes = crear_fuentes()
        self.panel = pygame.Rect(
            MARGEN + 24,
            self._Y_PANEL,
            ANCHO - 2 * (MARGEN + 24),
            520,
        )
        prefs = cargar_preferencias_grafico()
        self.mostrar_tooltips = prefs.mostrar_tooltips
        self.mostrar_emojis = prefs.mostrar_emojis
        self.guardar_informes_txt = prefs.guardar_informes_txt
        self.campo_nombre = CampoTexto(
            pygame.Rect(self.panel.x + 48, 0, self.panel.width - 96, 40),
            texto_inicial=nombre_inicial_grafico(),
            placeholder="Nombre del jugador",
        )
        py = self.panel.y
        self.campo_nombre.rect.y = py + self._Y_CAMPO_NOMBRE
        self._y_etiquetas = {
            "tooltips": py + self._Y_TOOLTIPS_LBL,
            "emojis": py + self._Y_EMOJIS_LBL,
            "informes": py + self._Y_INFORMES_LBL,
        }
        self._y_filas = {
            "tooltips": py + self._Y_TOOLTIPS_FILA,
            "emojis": py + self._Y_EMOJIS_FILA,
            "informes": py + self._Y_INFORMES_FILA,
        }
        self._crear_ciclos()
        self._crear_botones_borrado()
        self._reposicionar_campo_y_restablecer()
        self.boton_listo = Boton(
            "Listo",
            rect_boton_etiqueta(
                "Listo",
                self.fuentes["menu"],
                x_centro=ANCHO // 2,
                y=0,
                ancho_min=200,
                alto_min=48,
            ),
            self.guardar_y_cerrar,
            tooltip="Guarda los cambios y cierra el panel.",
        )
        self._reposicionar_inferior()

    def _crear_ciclos(self) -> None:
        self._botones_ciclo: dict[str, tuple[Boton, Boton]] = {}
        for clave, y in self._y_filas.items():
            x_ciclo = ANCHO // 2 - self.ANCHO_CICLO // 2
            rect_izq = pygame.Rect(x_ciclo, y, self.ANCHO_BTN_CICLO, self.ALTO_CTRL)
            rect_der = pygame.Rect(
                x_ciclo + self.ANCHO_CICLO - self.ANCHO_BTN_CICLO,
                y,
                self.ANCHO_BTN_CICLO,
                self.ALTO_CTRL,
            )
            menos = Boton("◀", rect_izq, lambda d=-1, k=clave: self._ciclar(k, d))
            mas = Boton("▶", rect_der, lambda d=1, k=clave: self._ciclar(k, d))
            self._botones_ciclo[clave] = (menos, mas)
        self._rects_valor = {
            clave: pygame.Rect(
                x_ciclo + self.ANCHO_BTN_CICLO + self.GAP_CICLO,
                y,
                self.ANCHO_CICLO - 2 * self.ANCHO_BTN_CICLO - 2 * self.GAP_CICLO,
                self.ALTO_CTRL,
            )
            for clave, y in self._y_filas.items()
            for x_ciclo in [ANCHO // 2 - self.ANCHO_CICLO // 2]
        }

    def _crear_botones_borrado(self) -> None:
        fuente_peq = self.fuentes["pequena"]
        _, icono_borrar = BTN_BORRAR_RANKING
        etiq_txt = etiqueta(*BTN_BORRAR_TXT_INFORMES)
        etiq_prefs = etiqueta(*BTN_VACIAR_PREFERENCIAS)
        etiq_infinita = etiqueta("Vaciar ranking infinita", icono_borrar)
        etiq_reto = etiqueta("Vaciar ranking reto del día", icono_borrar)
        self.boton_borrar_txt = Boton(
            etiq_txt,
            rect_boton_etiqueta(
                etiq_txt,
                fuente_peq,
                x_centro=ANCHO // 2,
                y=0,
                alto_min=36,
            ),
            lambda: self._solicitar_borrado("txt"),
            tooltip="Elimina los .txt de Data/Juego/.",
        )
        self.boton_vaciar_preferencias = Boton(
            etiq_prefs,
            rect_boton_etiqueta(
                etiq_prefs,
                fuente_peq,
                x_centro=0,
                y=0,
                alto_min=36,
            ),
            lambda: self._solicitar_borrado("preferencias"),
            tooltip="Restablece preferencias a valores por defecto (el .json se conserva).",
        )
        self.boton_borrar_infinita = Boton(
            etiq_infinita,
            rect_boton_etiqueta(
                etiq_infinita,
                fuente_peq,
                x_centro=0,
                y=0,
                alto_min=36,
            ),
            lambda: self._solicitar_borrado("infinita"),
            tooltip="Vacía el historial local del modo resistencia infinita (el fichero JSON se conserva).",
        )
        self.boton_borrar_reto = Boton(
            etiq_reto,
            rect_boton_etiqueta(
                etiq_reto,
                fuente_peq,
                x_centro=0,
                y=0,
                alto_min=36,
            ),
            lambda: self._solicitar_borrado("reto_dia"),
            tooltip="Vacía el historial local del reto del día (el fichero JSON se conserva).",
        )

    def _reposicionar_campo_y_restablecer(self) -> None:
        """Nombre a la izquierda y «Restablecer preferencias» a la derecha, misma fila."""
        margen = 48
        ancho_util = self.panel.width - 2 * margen
        ancho_campo = int(ancho_util * self._ANCHO_FRACCION_CAMPO_NOMBRE)
        x0 = self.panel.x + margen
        y = self.panel.y + self._Y_CAMPO_NOMBRE
        self.campo_nombre.rect.topleft = (x0, y)
        self.campo_nombre.rect.width = ancho_campo
        x_reset = x0 + ancho_campo + self._GAP_CAMPO_RESTABLECER
        ancho_reset = self.panel.right - margen - x_reset
        self.boton_vaciar_preferencias.rect.topleft = (x_reset, y)
        alto_fila = max(self.campo_nombre.rect.height, self.boton_vaciar_preferencias.rect.height)
        if self.boton_vaciar_preferencias.rect.width > ancho_reset:
            self.boton_vaciar_preferencias.rect.width = max(ancho_reset, 120)
        self.campo_nombre.rect.centery = y + alto_fila // 2
        self.boton_vaciar_preferencias.rect.centery = y + alto_fila // 2

    def _y_inferior_hint_borrado(self) -> int:
        fuente_peq = self.fuentes["pequena"]
        hint = fuente_peq.render(
            "Borrar: .txt | Vaciar: rankings (los .json se conservan).",
            True,
            _COLOR_ETIQUETA_PANEL,
        )
        return self.panel.y + self._Y_BORRADO_LBL + self._GAP_HINT_BORRADO + hint.get_height()

    def _alto_bloque_borrado(self) -> int:
        fila = [self.boton_borrar_infinita, self.boton_borrar_reto]
        gap_h = self._GAP_BORRADO_COLUMNAS
        ancho_max = self.panel.width - 48
        total_w = sum(boton.rect.width for boton in fila) + gap_h * (len(fila) - 1)
        if total_w > ancho_max:
            alto_ranking = sum(boton.rect.height for boton in fila) + self._GAP_BORRADO_FILAS * (
                len(fila) - 1
            )
        else:
            alto_ranking = max(boton.rect.height for boton in fila)
        return self.boton_borrar_txt.rect.height + self._GAP_BORRADO_FILAS + alto_ranking

    def _reposicionar_botones_borrado(self, *, y_superior: int, y_inferior: int) -> None:
        alto_bloque = self._alto_bloque_borrado()
        espacio = y_inferior - y_superior
        if espacio >= alto_bloque:
            y_bloque = y_superior + (espacio - alto_bloque) // 2
        else:
            y_bloque = y_superior

        self.boton_borrar_txt.rect.midtop = (ANCHO // 2, y_bloque)

        fila = [self.boton_borrar_infinita, self.boton_borrar_reto]
        gap_h = self._GAP_BORRADO_COLUMNAS
        y_ranking = y_bloque + self.boton_borrar_txt.rect.height + self._GAP_BORRADO_FILAS
        ancho_max = self.panel.width - 48
        total_w = sum(boton.rect.width for boton in fila) + gap_h * (len(fila) - 1)
        if total_w > ancho_max:
            y = y_ranking
            for boton in fila:
                boton.rect.midtop = (ANCHO // 2, y)
                y = boton.rect.bottom + self._GAP_BORRADO_FILAS
            return

        alto_fila = max(boton.rect.height for boton in fila)
        x = ANCHO // 2 - total_w // 2
        for boton in fila:
            boton.rect.topleft = (
                x,
                y_ranking + (alto_fila - boton.rect.height) // 2,
            )
            x += boton.rect.width + gap_h

    def _reposicionar_inferior(self) -> None:
        """Ancla «Listo» abajo y centra los botones de borrado entre el hint y «Listo»."""
        self.boton_listo.rect.midbottom = (
            ANCHO // 2,
            ALTO - self._MARGEN_VENTANA_INFERIOR - self._MARGEN_PANEL_INFERIOR,
        )
        y_listo_top = self.boton_listo.rect.top
        self._reposicionar_botones_borrado(
            y_superior=self._y_inferior_hint_borrado() + self._GAP_ZONA_BORRADO,
            y_inferior=y_listo_top - self._GAP_ZONA_BORRADO,
        )
        contenido_bottom = self.boton_listo.rect.bottom + self._MARGEN_PANEL_INFERIOR
        alto_necesario = contenido_bottom - self.panel.y
        alto_maximo = ALTO - self.panel.y - self._MARGEN_VENTANA_INFERIOR
        self.panel.height = min(max(520, alto_necesario), alto_maximo)

    def _ciclar(self, clave: str, delta: int) -> None:
        if clave == "tooltips":
            self.mostrar_tooltips = ciclar_tooltips(self.mostrar_tooltips)
        elif clave == "emojis":
            self.mostrar_emojis = ciclar_emojis(self.mostrar_emojis)
        elif clave == "informes":
            self.guardar_informes_txt = ciclar_guardar_informes(self.guardar_informes_txt)

    def _solicitar_borrado(self, accion: str) -> None:
        if accion == "txt":
            borrar_txt_informes_feedback()
            return
        if accion == "preferencias":
            vaciar_preferencias_locales()
            prefs = PreferenciasGrafico()
            self.mostrar_tooltips = prefs.mostrar_tooltips
            self.mostrar_emojis = prefs.mostrar_emojis
            self.guardar_informes_txt = prefs.guardar_informes_txt
            self.campo_nombre.texto = ""
            return
        vaciar_ranking_variante(accion)

    def _texto_valor(self, clave: str) -> str:
        if clave == "tooltips":
            return "Sí" if self.mostrar_tooltips else "No"
        if clave == "emojis":
            return "Sí" if self.mostrar_emojis else "No"
        if clave == "informes":
            return "Sí" if self.guardar_informes_txt else "No"
        return ""

    def guardar_y_cerrar(self) -> None:
        nombre_efectivo = nombre_jugador_efectivo(self.campo_nombre.texto)
        nombre_guardado = (
            "" if es_nombre_anonimo(nombre_efectivo) else nombre_efectivo
        )
        guardar_preferencias_grafico(
            PreferenciasGrafico(
                nombre_jugador=nombre_guardado,
                mostrar_tooltips=self.mostrar_tooltips,
                mostrar_emojis=self.mostrar_emojis,
                guardar_informes_txt=self.guardar_informes_txt,
            )
        )
        self.on_cerrar()

    def _botones(self) -> list[Boton]:
        out = [
            self.boton_listo,
            self.boton_borrar_txt,
            self.boton_vaciar_preferencias,
            self.boton_borrar_infinita,
            self.boton_borrar_reto,
        ]
        for par in self._botones_ciclo.values():
            out.extend(par)
        return out

    def manejar_evento(self, evento: pygame.event.Event) -> None:
        self.campo_nombre.manejar_evento(evento)
        if evento.type == pygame.MOUSEMOTION:
            for boton in self._botones():
                boton.actualizar_hover(evento.pos)
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            if self.campo_nombre.manejar_evento(evento):
                return
            for boton in self._botones():
                if boton.manejar_clic(evento.pos, evento.button):
                    return

    def dibujar_contenido(self, superficie: pygame.Surface) -> None:
        dibujar_panel(superficie, self.panel, color=(255, 255, 255))
        dibujar_texto_centro(
            superficie,
            "OPCIONES",
            (ANCHO // 2, self.panel.y + 36),
            self.fuentes["titulo"].get_height(),
            (25, 25, 30),
            bold=True,
        )

        fuente_peq = self.fuentes["pequena"]
        subt = fuente_peq.render(
            "Ajustes de esta instalación (se guardan en el equipo).",
            True,
            _COLOR_ETIQUETA_PANEL,
        )
        superficie.blit(subt, subt.get_rect(midtop=(ANCHO // 2, self.panel.y + self._Y_SUBTITULO)))

        self.campo_nombre.dibujar(superficie, self.fuentes["menu"])
        self.boton_vaciar_preferencias.dibujar(superficie, fuente_peq)

        etiquetas = {
            "tooltips": "Ayudas al pasar el ratón:",
            "emojis": "Emojis en botones y barra:",
            "informes": "Guardar informes .txt al terminar:",
        }
        for clave, y in self._y_filas.items():
            etiqueta_fila = fuente_peq.render(etiquetas[clave], True, _COLOR_ETIQUETA_PANEL)
            superficie.blit(
                etiqueta_fila,
                etiqueta_fila.get_rect(midtop=(ANCHO // 2, self._y_etiquetas[clave])),
            )
            rect_val = self._rects_valor[clave]
            dibujar_caja_valor_ciclo(
                superficie,
                rect_val,
                self._texto_valor(clave),
                fuente_peq,
            )
            menos, mas = self._botones_ciclo[clave]
            menos.dibujar(superficie, self.fuentes["menu"])
            mas.dibujar(superficie, self.fuentes["menu"])

        lbl_borrado = fuente_peq.render("Limpiar datos locales:", True, _COLOR_ETIQUETA_PANEL)
        hint_borrado = fuente_peq.render(
            "Borrar: .txt | Vaciar: rankings (los .json se conservan).",
            True,
            _COLOR_ETIQUETA_PANEL,
        )
        superficie.blit(
            lbl_borrado,
            lbl_borrado.get_rect(midtop=(ANCHO // 2, self.panel.y + self._Y_BORRADO_LBL)),
        )
        superficie.blit(
            hint_borrado,
            hint_borrado.get_rect(
                midtop=(ANCHO // 2, self.panel.y + self._Y_BORRADO_LBL + self._GAP_HINT_BORRADO),
            ),
        )

        self.boton_borrar_txt.dibujar(superficie, fuente_peq)
        self.boton_borrar_infinita.dibujar(superficie, fuente_peq)
        self.boton_borrar_reto.dibujar(superficie, fuente_peq)

        self.boton_listo.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(superficie, fuente_peq, self._botones())
