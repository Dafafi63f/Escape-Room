#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Panel superpuesto de opciones globales (barra fija de la app gráfica)."""

from __future__ import annotations

from collections.abc import Callable

import pygame

from Comun.jugador import es_nombre_anonimo, nombre_jugador_efectivo
from Comun.limpieza_local import (
    borrar_txt_informes_feedback,
    etiqueta_variante_ranking,
    vaciar_ranking_variante,
)
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
    ANCHO,
    COLOR_AVISO,
    MARGEN,
    crear_fuentes,
)
from Grafico.texto import dibujar_texto_centro
from Grafico.textos_grafico import BTN_BORRAR_RANKING, BTN_BORRAR_TXT_INFORMES, etiqueta
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
    _Y_SUBTITULO = 68
    _Y_CAMPO_NOMBRE = 118
    _GAP_LBL_CAMPO = 14
    _Y_TOOLTIPS_LBL = 176
    _Y_TOOLTIPS_FILA = 202
    _Y_EMOJIS_LBL = 252
    _Y_EMOJIS_FILA = 278
    _Y_INFORMES_LBL = 320
    _Y_INFORMES_FILA = 346
    _GAP_TRAS_FILA_CICLO = 20
    _Y_BORRADO_LBL = _Y_INFORMES_FILA + ALTO_CTRL + _GAP_TRAS_FILA_CICLO
    _Y_BORRAR_TXT = _Y_BORRADO_LBL + 28
    _GAP_BORRADO_FILAS = 12
    _GAP_BORRADO_COLUMNAS = 16
    _GAP_MENSAJE = 10
    _RESERVA_MENSAJE = 22
    _GAP_LISTO = 18
    _MARGEN_PANEL_INFERIOR = 16

    def __init__(self, *, on_cerrar: Callable[[], None]) -> None:
        self.on_cerrar = on_cerrar
        self.fuentes = crear_fuentes()
        self.panel = pygame.Rect(MARGEN + 24, 72, ANCHO - 2 * (MARGEN + 24), 572)
        prefs = cargar_preferencias_grafico()
        self.mostrar_tooltips = prefs.mostrar_tooltips
        self.mostrar_emojis = prefs.mostrar_emojis
        self.guardar_informes_txt = prefs.guardar_informes_txt
        self._confirmar_borrado: str | None = None
        self.mensaje = ""
        self.campo_nombre = CampoTexto(
            pygame.Rect(self.panel.x + 48, 0, self.panel.width - 96, 40),
            texto_inicial=nombre_inicial_grafico(),
            placeholder="Nombre del jugador",
        )
        self.campo_nombre.rect.y = self.panel.y + self._Y_CAMPO_NOMBRE
        py = self.panel.y
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
        self._reposicionar_botones_borrado()
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
        etiq_infinita = etiqueta("Borrar ranking infinita", icono_borrar)
        etiq_reto = etiqueta("Borrar ranking reto del día", icono_borrar)
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
            tooltip="Elimina los .txt de Juego/Informes/ y Juego/Feedback/.",
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
            tooltip="Vacía el historial local del modo resistencia infinita.",
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
            tooltip="Vacía el historial local del reto del día (resistencia).",
        )

    def _reposicionar_botones_borrado(self) -> None:
        y_txt = self.panel.y + self._Y_BORRAR_TXT
        self.boton_borrar_txt.rect.midtop = (ANCHO // 2, y_txt)

        fila = [self.boton_borrar_infinita, self.boton_borrar_reto]
        gap_h = self._GAP_BORRADO_COLUMNAS
        gap_v = self._GAP_BORRADO_FILAS
        y_ranking = self.boton_borrar_txt.rect.bottom + gap_v
        ancho_max = self.panel.width - 48
        total_w = sum(boton.rect.width for boton in fila) + gap_h * (len(fila) - 1)
        if total_w > ancho_max:
            y = y_ranking
            for boton in fila:
                boton.rect.midtop = (ANCHO // 2, y)
                y = boton.rect.bottom + gap_v
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
        """Coloca mensaje y «Listo» debajo de los botones de borrado sin solaparse."""
        botones_borrado = (
            self.boton_borrar_txt,
            self.boton_borrar_infinita,
            self.boton_borrar_reto,
        )
        y_mensaje = max(boton.rect.bottom for boton in botones_borrado) + self._GAP_MENSAJE
        y_listo = y_mensaje + self._RESERVA_MENSAJE + self._GAP_LISTO
        self._y_mensaje = y_mensaje
        self.boton_listo.rect.midtop = (ANCHO // 2, y_listo)
        contenido_bottom = self.boton_listo.rect.bottom + self._MARGEN_PANEL_INFERIOR
        self.panel.height = max(572, contenido_bottom - self.panel.y)

    def _ciclar(self, clave: str, delta: int) -> None:
        if clave == "tooltips":
            self.mostrar_tooltips = ciclar_tooltips(self.mostrar_tooltips)
        elif clave == "emojis":
            self.mostrar_emojis = ciclar_emojis(self.mostrar_emojis)
        elif clave == "informes":
            self.guardar_informes_txt = ciclar_guardar_informes(self.guardar_informes_txt)
        self._confirmar_borrado = None
        self.mensaje = ""

    def _etiqueta_accion_borrado(self, accion: str) -> str:
        if accion == "txt":
            return etiqueta(*BTN_BORRAR_TXT_INFORMES)
        _, icono_borrar = BTN_BORRAR_RANKING
        return etiqueta(
            f"Borrar ranking {etiqueta_variante_ranking(accion).lower()}",
            icono_borrar,
        )

    def _solicitar_borrado(self, accion: str) -> None:
        if self._confirmar_borrado != accion:
            self._confirmar_borrado = accion
            etiqueta_accion = self._etiqueta_accion_borrado(accion)
            self.mensaje = f"Pulsa otra vez «{etiqueta_accion}» para confirmar."
            return
        self._confirmar_borrado = None
        if accion == "txt":
            resumen = borrar_txt_informes_feedback()
            if resumen.errores:
                self.mensaje = (
                    f"Se borraron {resumen.borrados} .txt; "
                    f"{resumen.errores} no pudieron eliminarse."
                )
            elif resumen.borrados:
                self.mensaje = f"Se borraron {resumen.borrados} ficheros .txt de informes y feedback."
            else:
                self.mensaje = "No había ficheros .txt de informes ni feedback."
            return
        vaciar_ranking_variante(accion)
        etiqueta_tabla = etiqueta_variante_ranking(accion)
        self.mensaje = f"Historial de «{etiqueta_tabla}» borrado en este equipo."

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

        lbl_nombre = fuente_peq.render("Nombre del jugador:", True, _COLOR_ETIQUETA_PANEL)
        superficie.blit(
            lbl_nombre,
            lbl_nombre.get_rect(
                midbottom=(
                    self.campo_nombre.rect.centerx,
                    self.campo_nombre.rect.y - self._GAP_LBL_CAMPO,
                )
            ),
        )
        self.campo_nombre.dibujar(superficie, self.fuentes["menu"])

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

        lbl_borrado = fuente_peq.render("Borrar datos locales:", True, _COLOR_ETIQUETA_PANEL)
        superficie.blit(
            lbl_borrado,
            lbl_borrado.get_rect(midtop=(ANCHO // 2, self.panel.y + self._Y_BORRADO_LBL)),
        )

        self.boton_borrar_txt.dibujar(superficie, fuente_peq)
        self.boton_borrar_infinita.dibujar(superficie, fuente_peq)
        self.boton_borrar_reto.dibujar(superficie, fuente_peq)

        if self.mensaje:
            msg = fuente_peq.render(self.mensaje, True, COLOR_AVISO)
            superficie.blit(msg, msg.get_rect(midtop=(ANCHO // 2, self._y_mensaje)))

        self.boton_listo.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(superficie, fuente_peq, self._botones())
