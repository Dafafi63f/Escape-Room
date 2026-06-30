#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Panel superpuesto de opciones globales (barra fija de la app gráfica)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pygame

from Comun.metadatos_inferidos import exportar_dataset_intermedio
from Comun.modelos import Pregunta

from Comun.preferencias_grafico import es_nombre_anonimo, nombre_jugador_efectivo
from Comun.persistencia import (
    borrar_txt_informes_feedback,
    vaciar_estadisticas_locales,
    vaciar_preferencias_locales,
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
    ALTO,
    ANCHO,
    MARGEN,
    crear_fuentes,
)
from Grafico.texto import dibujar_texto_centro
from Grafico.textos_grafico import (
    BTN_BORRAR_TXT_INFORMES,
    BTN_EXPORTAR_DATASET_INTERMEDIO,
    BTN_VACIAR_ESTADISTICAS,
    BTN_VACIAR_PREFERENCIAS,
    etiqueta,
)
from Grafico.ui import (
    Boton,
    CampoTexto,
    capturar,
    dibujar_caja_valor_ciclo,
    dibujar_panel,
    dibujar_tooltips_botones,
    rect_boton_etiqueta,
)


_COLOR_ETIQUETA_PANEL = (70, 80, 95)


@dataclass(frozen=True)
class ExportDatasetOpciones:
    preguntas: tuple[Pregunta, ...]
    carpeta: Path


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

    _GAP_SECCION_DATASET = 14
    _GAP_DATASET_HINT = 6
    _ALTO_MENSAJE_EXPORT = 40

    def __init__(
        self,
        *,
        on_cerrar: Callable[[], None],
        export_dataset: ExportDatasetOpciones | None = None,
    ) -> None:
        self.on_cerrar = on_cerrar
        self.export_dataset = export_dataset
        self.mensaje_export = ""
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
        self._crear_boton_export_dataset()
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
            menos = Boton("◀", rect_izq, capturar(self._ciclar, clave, -1))
            mas = Boton("▶", rect_der, capturar(self._ciclar, clave, 1))
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
        etiq_txt = etiqueta(*BTN_BORRAR_TXT_INFORMES)
        etiq_prefs = etiqueta(*BTN_VACIAR_PREFERENCIAS)
        etiq_stats = etiqueta(*BTN_VACIAR_ESTADISTICAS)
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
        self.boton_vaciar_estadisticas = Boton(
            etiq_stats,
            rect_boton_etiqueta(
                etiq_stats,
                fuente_peq,
                x_centro=0,
                y=0,
                alto_min=36,
            ),
            lambda: self._solicitar_borrado("estadisticas"),
            tooltip=(
                "Restablece récords, totales y evolución acumulada "
                "(el fichero estadisticas_jugador.json se conserva)."
            ),
        )
        self.boton_export_dataset: Boton | None = None

    def _crear_boton_export_dataset(self) -> None:
        if self.export_dataset is None:
            return
        fuente_peq = self.fuentes["pequena"]
        etiq = etiqueta(*BTN_EXPORTAR_DATASET_INTERMEDIO)
        self.boton_export_dataset = Boton(
            etiq,
            rect_boton_etiqueta(
                etiq,
                fuente_peq,
                x_centro=ANCHO // 2,
                y=0,
                alto_min=36,
            ),
            self._exportar_dataset_intermedio,
            tooltip=(
                "Crea Preguntas_intermedio.csv y listado_materias_intermedio.csv "
                "a partir de metadatos_inferidos.json (usable en el juego completo)."
            ),
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

    def _y_dataset_seccion(self) -> int | None:
        if self.export_dataset is None:
            return None
        return self.panel.y + self._Y_INFORMES_FILA + self.ALTO_CTRL + self._GAP_SECCION_DATASET

    def _alto_bloque_export(self) -> int:
        if self.export_dataset is None:
            return 0
        fuente_peq = self.fuentes["pequena"]
        lbl = fuente_peq.render("Exportar para juego completo:", True, _COLOR_ETIQUETA_PANEL)
        hint = fuente_peq.render(
            "Usa estadísticas locales y materias inferidas (sin curso ni semestre).",
            True,
            _COLOR_ETIQUETA_PANEL,
        )
        alto_btn = self.boton_export_dataset.rect.height if self.boton_export_dataset else 36
        alto = lbl.get_height() + self._GAP_DATASET_HINT + alto_btn + self._GAP_DATASET_HINT
        alto += hint.get_height()
        if self.mensaje_export:
            alto += self._GAP_DATASET_HINT + self._ALTO_MENSAJE_EXPORT
        return alto

    def _y_borrado_lbl(self) -> int:
        y = self.panel.y + self._Y_BORRADO_LBL
        y_dataset = self._y_dataset_seccion()
        if y_dataset is not None:
            y = y_dataset + self._alto_bloque_export() + self._GAP_SECCION_DATASET
        return y

    def _y_inferior_hint_borrado(self) -> int:
        fuente_peq = self.fuentes["pequena"]
        hint = fuente_peq.render(
            "Borrar: .txt | Vaciar: estadísticas (los .json se conservan).",
            True,
            _COLOR_ETIQUETA_PANEL,
        )
        return self._y_borrado_lbl() + self._GAP_HINT_BORRADO + hint.get_height()

    def _alto_bloque_borrado(self) -> int:
        return self.boton_borrar_txt.rect.height + self._GAP_BORRADO_FILAS + (
            self.boton_vaciar_estadisticas.rect.height
        )

    def _reposicionar_botones_borrado(self, *, y_superior: int, y_inferior: int) -> None:
        alto_bloque = self._alto_bloque_borrado()
        espacio = y_inferior - y_superior
        if espacio >= alto_bloque:
            y_bloque = y_superior + (espacio - alto_bloque) // 2
        else:
            y_bloque = y_superior

        self.boton_borrar_txt.rect.midtop = (ANCHO // 2, y_bloque)
        self.boton_vaciar_estadisticas.rect.midtop = (
            ANCHO // 2,
            y_bloque + self.boton_borrar_txt.rect.height + self._GAP_BORRADO_FILAS,
        )

    def _reposicionar_inferior(self) -> None:
        """Ancla «Listo» abajo y centra los botones de borrado entre el hint y «Listo»."""
        if self.boton_export_dataset is not None:
            y_dataset = self._y_dataset_seccion()
            if y_dataset is not None:
                fuente_peq = self.fuentes["pequena"]
                lbl = fuente_peq.render(
                    "Exportar para juego completo:",
                    True,
                    _COLOR_ETIQUETA_PANEL,
                )
                self.boton_export_dataset.rect.midtop = (
                    ANCHO // 2,
                    y_dataset + lbl.get_height() + self._GAP_DATASET_HINT,
                )
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

    def _exportar_dataset_intermedio(self) -> None:
        if self.export_dataset is None:
            return
        try:
            resultado = exportar_dataset_intermedio(
                list(self.export_dataset.preguntas),
                carpeta=self.export_dataset.carpeta,
            )
            self.mensaje_export = (
                f"Generados {resultado.n_preguntas} preguntas y "
                f"{resultado.n_materias} materias en {resultado.csv.parent.name}/"
            )
            if resultado.con_dificultad < resultado.total:
                self.mensaje_export += (
                    f" ({resultado.con_dificultad} con dificultad inferida por estadísticas)"
                )
        except OSError as exc:
            self.mensaje_export = f"No se pudo guardar: {exc}"
        self._reposicionar_inferior()

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
        if accion == "estadisticas":
            vaciar_estadisticas_locales()
            return

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
            self.boton_vaciar_estadisticas,
        ]
        if self.boton_export_dataset is not None:
            out.append(self.boton_export_dataset)
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

        if self.export_dataset is not None and self.boton_export_dataset is not None:
            y_dataset = self._y_dataset_seccion()
            assert y_dataset is not None
            lbl_dataset = fuente_peq.render(
                "Exportar para juego completo:",
                True,
                _COLOR_ETIQUETA_PANEL,
            )
            superficie.blit(
                lbl_dataset,
                lbl_dataset.get_rect(midtop=(ANCHO // 2, y_dataset)),
            )
            self.boton_export_dataset.rect.midtop = (
                ANCHO // 2,
                y_dataset + lbl_dataset.get_height() + self._GAP_DATASET_HINT,
            )
            hint_dataset = fuente_peq.render(
                "Usa estadísticas locales y materias inferidas (sin curso ni semestre).",
                True,
                _COLOR_ETIQUETA_PANEL,
            )
            superficie.blit(
                hint_dataset,
                hint_dataset.get_rect(
                    midtop=(
                        ANCHO // 2,
                        self.boton_export_dataset.rect.bottom + self._GAP_DATASET_HINT,
                    ),
                ),
            )
            if self.mensaje_export:
                msg = fuente_peq.render(self.mensaje_export, True, (40, 110, 60))
                superficie.blit(
                    msg,
                    msg.get_rect(
                        midtop=(
                            ANCHO // 2,
                            hint_dataset.get_rect().bottom + self._GAP_DATASET_HINT,
                        ),
                    ),
                )
            self.boton_export_dataset.dibujar(superficie, fuente_peq)

        lbl_borrado = fuente_peq.render("Limpiar datos locales:", True, _COLOR_ETIQUETA_PANEL)
        hint_borrado = fuente_peq.render(
            "Borrar: .txt | Vaciar: estadísticas (los .json se conservan).",
            True,
            _COLOR_ETIQUETA_PANEL,
        )
        superficie.blit(
            lbl_borrado,
            lbl_borrado.get_rect(midtop=(ANCHO // 2, self._y_borrado_lbl())),
        )
        superficie.blit(
            hint_borrado,
            hint_borrado.get_rect(
                midtop=(ANCHO // 2, self._y_borrado_lbl() + self._GAP_HINT_BORRADO),
            ),
        )

        self.boton_borrar_txt.dibujar(superficie, fuente_peq)
        self.boton_vaciar_estadisticas.dibujar(superficie, fuente_peq)

        self.boton_listo.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(superficie, fuente_peq, self._botones())
