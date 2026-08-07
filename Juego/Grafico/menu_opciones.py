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
from Comun.rutas import etiqueta_dir_datos_jugador

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
    ANCHO,
    MARGEN,
    crear_fuentes,
    zona_segura_panel_modal,
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
_LBL_DATOS_COMPACTO = "Datos locales:"


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

    # Desplazamientos verticales respecto a ``panel.y`` (modo normal; compacto en ``_OFFSETS_COMPACTO``).
    _GAP_TRAS_FILA_CICLO = 14
    _GAP_HINT_BORRADO = 18
    _GAP_ZONA_BORRADO = 12
    _GAP_BORRADO_FILAS = 8
    _GAP_BORRADO_COLUMNAS = 16
    _MARGEN_PANEL_INFERIOR = 18

    _GAP_SECCION_DATASET = 10
    _GAP_DATASET_HINT = 6
    _ALTO_MENSAJE_EXPORT = 36
    _GAP_MIN_INFERIOR = 6
    _GAP_TRAS_INFORMES = 12

    _OFFSETS_NORMAL: dict[str, int] = {
        "titulo": 30,
        "subtitulo": 50,
        "campo_nombre": 92,
        "tooltips_lbl": 148,
        "tooltips_fila": 172,
        "emojis_lbl": 220,
        "emojis_fila": 244,
        "informes_lbl": 292,
        "informes_fila": 316,
    }
    _OFFSETS_COMPACTO: dict[str, int] = {
        "titulo": 24,
        "subtitulo": 46,
        "campo_nombre": 78,
        "tooltips_lbl": 132,
        "tooltips_fila": 156,
        "emojis_lbl": 206,
        "emojis_fila": 230,
        "informes_lbl": 280,
        "informes_fila": 304,
    }

    def __init__(
        self,
        *,
        on_cerrar: Callable[[], None],
        export_dataset: ExportDatasetOpciones | None = None,
    ) -> None:
        self.on_cerrar = on_cerrar
        self.export_dataset = export_dataset
        self._modo_minimo = export_dataset is not None
        self.mensaje_export = ""
        self.fuentes = crear_fuentes()
        y_superior, y_inferior = zona_segura_panel_modal(self.fuentes["menu"])
        self._y_inferior_seguro = y_inferior
        self.panel = pygame.Rect(
            MARGEN + 24,
            y_superior,
            ANCHO - 2 * (MARGEN + 24),
            y_inferior - y_superior,
        )
        self._off = self._offsets_rel()
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
        self.campo_nombre.rect.y = py + self._off["campo_nombre"]
        self._y_etiquetas = {
            "tooltips": py + self._off["tooltips_lbl"],
            "emojis": py + self._off["emojis_lbl"],
            "informes": py + self._off["informes_lbl"],
        }
        self._y_filas = {
            "tooltips": py + self._off["tooltips_fila"],
            "emojis": py + self._off["emojis_fila"],
            "informes": py + self._off["informes_fila"],
        }
        self._crear_ciclos()
        self._crear_botones_borrado()
        self._crear_boton_export_dataset()
        self._reposicionar_campo_nombre()
        self._y_borrado_lbl_dibujo = 0
        self._y_hint_borrado_dibujo = 0
        self._y_mensaje_export_dibujo: int | None = None
        self._y_top_datos_botones = 0
        self._mostrar_lbl_datos = True
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

    def _offsets_rel(self) -> dict[str, int]:
        return dict(self._OFFSETS_COMPACTO if self._modo_minimo else self._OFFSETS_NORMAL)

    def _gap(self, normal: int, *, compacto: int | None = None) -> int:
        if not self._modo_minimo:
            return normal
        return compacto if compacto is not None else max(6, normal - 6)

    def _margen_inferior_panel(self) -> int:
        return self._gap(self._MARGEN_PANEL_INFERIOR, compacto=12)

    def _leer_gap_seccion_dataset(self) -> int:
        return self._gap(self._GAP_SECCION_DATASET, compacto=10)

    def _valor_gap_hint_borrado(self) -> int:
        return self._gap(self._GAP_HINT_BORRADO, compacto=12)

    def _leer_gap_zona_borrado(self) -> int:
        return self._gap(self._GAP_ZONA_BORRADO, compacto=8)

    def _valor_gap_dataset_hint(self) -> int:
        return self._gap(self._GAP_DATASET_HINT, compacto=10)

    def _ajustar_altura_panel(self) -> None:
        alto_necesario = (
            self.boton_listo.rect.bottom + self._margen_inferior_panel() - self.panel.y
        )
        alto_maximo = self._y_inferior_seguro - self.panel.y
        self.panel.height = min(alto_maximo, max(280, alto_necesario))

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
            tooltip=f"Elimina los .txt de {etiqueta_dir_datos_jugador()}/.",
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

    def _crear_boton_export_dataset(self) -> None:
        fuente_peq = self.fuentes["pequena"]
        etiq = etiqueta(*BTN_EXPORTAR_DATASET_INTERMEDIO)
        habilitado = self.export_dataset is not None
        tooltip = (
            (
                "Crea Preguntas_intermedio.csv y listado_materias_intermedio.csv "
                f"en {etiqueta_dir_datos_jugador()}/ a partir de metadatos_inferidos.json "
                "(usable en el juego completo)."
            )
            if habilitado
            else "Solo disponible en la instalación mínima de teoría."
        )
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
            tooltip=tooltip,
        )
        self.boton_export_dataset.activo = habilitado

    def _reposicionar_campo_nombre(self) -> None:
        """Campo de nombre a ancho completo del panel."""
        margen = 48
        x0 = self.panel.x + margen
        y = self.panel.y + self._off["campo_nombre"]
        self.campo_nombre.rect.topleft = (x0, y)
        self.campo_nombre.rect.width = self.panel.width - 2 * margen

    def _y_minima_seccion_inferior(self) -> int:
        return (
            self.panel.y
            + self._off["informes_fila"]
            + self.ALTO_CTRL
            + max(self._GAP_TRAS_INFORMES, self._leer_gap_seccion_dataset())
        )

    def _y_inferior_fila_informes(self) -> int:
        return self.panel.y + self._off["informes_fila"] + self.ALTO_CTRL

    def _colocar_fila_dos_botones(self, izq: Boton, der: Boton, y: int) -> int:
        """Dos botones en horizontal con columnas iguales; devuelve el alto de la fila."""
        gap = self._GAP_BORRADO_COLUMNAS
        margen = 48
        ancho_util = self.panel.width - 2 * margen
        col_w = max(120, (ancho_util - gap) // 2)
        izq.rect.width = col_w
        der.rect.width = col_w
        alto_fila = max(izq.rect.height, der.rect.height)
        total = col_w + gap + col_w
        x0 = ANCHO // 2 - total // 2
        izq.rect.topleft = (x0, y)
        der.rect.topleft = (x0 + col_w + gap, y)
        izq.rect.centery = y + alto_fila // 2
        der.rect.centery = y + alto_fila // 2
        return alto_fila

    def _colocar_datos_con_tope(self, y_bottom: int) -> int:
        """Dos filas: dataset|txt y preferencias|estadísticas."""
        y_fila = y_bottom
        alto_fila2 = max(
            self.boton_vaciar_preferencias.rect.height,
            self.boton_vaciar_estadisticas.rect.height,
        )
        y_fila -= alto_fila2
        self._colocar_fila_dos_botones(
            self.boton_vaciar_preferencias,
            self.boton_vaciar_estadisticas,
            y_fila,
        )
        y_fila -= self._GAP_BORRADO_FILAS
        alto_fila1 = max(
            self.boton_export_dataset.rect.height,
            self.boton_borrar_txt.rect.height,
        )
        y_fila -= alto_fila1
        self._colocar_fila_dos_botones(
            self.boton_export_dataset,
            self.boton_borrar_txt,
            y_fila,
        )
        return y_fila

    def _colocar_borrado_con_tope(self, y_bottom: int) -> int:
        """Coloca el bloque de datos locales con borde inferior en ``y_bottom``."""
        return self._colocar_datos_con_tope(y_bottom)

    def _layout_inferior_con_gaps(
        self,
        *,
        gap_listo: int,
        gap_hint: int,
        gap_seccion: int,
        lbl_borrado: pygame.Surface,
    ) -> int:
        y = self._y_inferior_seguro - self._margen_inferior_panel()
        self.boton_listo.rect.midbottom = (ANCHO // 2, y)

        y = self.boton_listo.rect.top - gap_listo
        y_top_botones = self._colocar_borrado_con_tope(y)
        self._y_top_datos_botones = y_top_botones

        y = y_top_botones - gap_seccion
        self._y_mensaje_export_dibujo = None
        if self.mensaje_export:
            self._y_mensaje_export_dibujo = y - self._ALTO_MENSAJE_EXPORT
            y = self._y_mensaje_export_dibujo - gap_hint
        self._y_hint_borrado_dibujo = 0
        alto_lbl = lbl_borrado.get_height()
        informes_fin = self._y_inferior_fila_informes()
        y_lbl_min = informes_fin + 6
        y_lbl_max = y_top_botones - 4 - alto_lbl
        y_lbl_ideal = y - alto_lbl
        self._mostrar_lbl_datos = y_lbl_max >= y_lbl_min
        if self._mostrar_lbl_datos:
            self._y_borrado_lbl_dibujo = min(max(y_lbl_ideal, y_lbl_min), y_lbl_max)
        return y_top_botones

    def _alto_bloque_borrado(self) -> int:
        alto_fila1 = max(
            self.boton_export_dataset.rect.height,
            self.boton_borrar_txt.rect.height,
        )
        alto_fila2 = max(
            self.boton_vaciar_preferencias.rect.height,
            self.boton_vaciar_estadisticas.rect.height,
        )
        return alto_fila1 + self._GAP_BORRADO_FILAS + alto_fila2

    def _reposicionar_inferior(self) -> None:
        """Ancla «Listo» al pie seguro y apila export/borrado hacia arriba."""
        fuente_peq = self.fuentes["pequena"]
        lbl_borrado = fuente_peq.render(_LBL_DATOS_COMPACTO, True, _COLOR_ETIQUETA_PANEL)
        min_y = self._y_minima_seccion_inferior()
        escalas = (1.0, 0.82, 0.66) if self._modo_minimo else (1.0, 0.88, 0.72)
        for escala in escalas:
            gap_listo = max(self._GAP_MIN_INFERIOR, int(self._leer_gap_zona_borrado() * escala))
            gap_hint = max(self._GAP_MIN_INFERIOR, int(self._valor_gap_hint_borrado() * escala))
            gap_seccion = max(self._GAP_MIN_INFERIOR, int(self._leer_gap_seccion_dataset() * escala))
            y_fila_datos = self._layout_inferior_con_gaps(
                gap_listo=gap_listo,
                gap_hint=gap_hint,
                gap_seccion=gap_seccion,
                lbl_borrado=lbl_borrado,
            )
            if y_fila_datos >= min_y:
                break
        self._ajustar_altura_panel()

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
            self.boton_export_dataset,
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
        self._reposicionar_inferior()
        dibujar_panel(superficie, self.panel, color=(255, 255, 255))
        dibujar_texto_centro(
            superficie,
            "OPCIONES",
            (ANCHO // 2, self.panel.y + self._off["titulo"]),
            self.fuentes["titulo"].get_height(),
            (25, 25, 30),
            bold=True,
        )

        fuente_peq = self.fuentes["pequena"]
        if self._modo_minimo:
            subt_texto = (
                f"Ajustes de esta instalación (se guardan en {etiqueta_dir_datos_jugador()}/)."
            )
        else:
            subt_texto = "Ajustes de esta instalación (se guardan en el equipo)."
        subt = fuente_peq.render(
            subt_texto,
            True,
            _COLOR_ETIQUETA_PANEL,
        )
        superficie.blit(subt, subt.get_rect(midtop=(ANCHO // 2, self.panel.y + self._off["subtitulo"])))

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

        lbl_borrado = fuente_peq.render(_LBL_DATOS_COMPACTO, True, _COLOR_ETIQUETA_PANEL)
        if self._mostrar_lbl_datos:
            superficie.blit(
                lbl_borrado,
                lbl_borrado.get_rect(midtop=(ANCHO // 2, self._y_borrado_lbl_dibujo)),
            )
        if self.mensaje_export and self._y_mensaje_export_dibujo is not None:
            msg = fuente_peq.render(self.mensaje_export, True, (40, 110, 60))
            superficie.blit(
                msg,
                msg.get_rect(midtop=(ANCHO // 2, self._y_mensaje_export_dibujo)),
            )

        self.boton_export_dataset.dibujar(superficie, fuente_peq)
        self.boton_borrar_txt.dibujar(superficie, fuente_peq)
        self.boton_vaciar_preferencias.dibujar(superficie, fuente_peq)
        self.boton_vaciar_estadisticas.dibujar(superficie, fuente_peq)

        self.boton_listo.dibujar(superficie, self.fuentes["menu"])
        dibujar_tooltips_botones(superficie, fuente_peq, self._botones())
