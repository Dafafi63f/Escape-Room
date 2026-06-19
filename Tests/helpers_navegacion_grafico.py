#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Utilidades para simular pulsaciones de botones en menús gráficos."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import patch
import tempfile

if TYPE_CHECKING:
    from Grafico.app import AplicacionGrafica, DatosJuego
    from Grafico.pantallas import Pantalla
    from Grafico.ui import Boton


def configurar_pygame_tests() -> None:
    import pygame

    from Grafico.fuentes import invalidar_cache_fuentes

    if pygame.get_init():
        pygame.quit()
    pygame.init()
    pygame.display.set_mode((960, 720))
    invalidar_cache_fuentes()


@contextmanager
def preferencias_grafico_aisladas() -> Iterator[Path]:
    """Evita que los tests escriban en Data/Juego/preferencias_grafico.json del proyecto."""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "preferencias_grafico.json"
        with patch(
            "Comun.preferencias_grafico.resolver_path_preferencias_grafico",
            return_value=path,
        ):
            yield path


def evento_clic(centro: tuple[int, int]):
    import pygame

    return pygame.event.Event(pygame.MOUSEBUTTONDOWN, {"pos": centro, "button": 1})


def datos_prueba(*, preguntas: list | None = None) -> DatosJuego:
    from Comun.modelos import Pregunta
    from Grafico.app import DatosJuego

    if preguntas is None:
        preguntas = []
    return DatosJuego(
        max(len(preguntas), 1),
        1,
        preguntas,
        {"Test": {}},
        Path("."),
        Path("."),
    )


def crear_app_grafica_pruebas(
    datos: DatosJuego | None = None,
    *,
    nombre_jugador: str = "Test",
) -> AplicacionGrafica:
    """App gráfica en menú principal con nombre guardado (sin pantalla de bienvenida)."""
    from Comun.preferencias_grafico import PreferenciasGrafico, guardar_preferencias_grafico
    from Grafico.app import AplicacionGrafica

    if datos is None:
        datos = datos_prueba()
    guardar_preferencias_grafico(
        PreferenciasGrafico(
            nombre_jugador=nombre_jugador,
            mostrar_tooltips=True,
            mostrar_emojis=True,
            guardar_informes_txt=True,
        )
    )
    return AplicacionGrafica(datos, saltar_bienvenida=True)


def pregunta_minima() -> Pregunta:
    from Comun.modelos import Pregunta

    return Pregunta(
        texto="¿2+2?",
        materia="Test",
        tematica="",
        dificultad="Facil",
        tipo="Teoria",
        grupo="",
        nivel="1",
        curso="1",
        semestre="1",
        opciones={"A": "3", "B": "4", "C": "5", "D": "6"},
        correcta="B",
    )


def botones_interactivos(pantalla: Pantalla) -> list[Boton]:
    if hasattr(pantalla, "_botones_ui"):
        return list(pantalla._botones_ui())
    if hasattr(pantalla, "botones"):
        return list(pantalla.botones)
    if hasattr(pantalla, "boton_volver"):
        return [pantalla.boton_volver]
    if hasattr(pantalla, "boton_menu"):
        botones = [pantalla.boton_menu]
        if hasattr(pantalla, "boton_ranking"):
            botones.insert(0, pantalla.boton_ranking)
        return botones
    return []


def pulsar(boton: Boton) -> None:
    if not boton.activo:
        raise AssertionError(f"Botón inactivo: {boton.etiqueta!r}")
    if not boton.manejar_clic(boton.rect.center, 1):
        raise AssertionError(
            f"Clic sin efecto en {boton.etiqueta!r} (rect={boton.rect})"
        )


def pulsar_con_texto(pantalla: Pantalla, *fragmentos: str) -> Boton:
    for boton in botones_interactivos(pantalla):
        if boton.activo and all(f in boton.etiqueta for f in fragmentos):
            pulsar(boton)
            return boton
    visibles = [b.etiqueta for b in botones_interactivos(pantalla) if b.activo]
    raise AssertionError(
        f"Sin botón que contenga {fragmentos!r}. Activos: {visibles}"
    )


def clic_pantalla(pantalla: Pantalla, boton: Boton) -> None:
    pantalla.manejar_evento(evento_clic(boton.rect.center))


class SecuenciaNavegacion:
    """Encadena pulsaciones sobre ``AplicacionGrafica`` (usa ``app._ir_a`` real)."""

    def __init__(self, app: AplicacionGrafica) -> None:
        self.app = app

    @property
    def pantalla(self) -> Pantalla:
        return self.app.actual

    def comprobar(self, *tipos: type) -> None:
        if not isinstance(self.pantalla, tipos):
            nombre = getattr(type(self.pantalla), "__name__", repr(self.pantalla))
            esperado = ", ".join(t.__name__ for t in tipos)
            raise AssertionError(f"Pantalla actual {nombre}, se esperaba {esperado}")

    def pulsar_menu(self, opcion_id: str) -> None:
        from Grafico.pantallas import MenuPrincipal

        self.comprobar(MenuPrincipal)
        for boton, opcion in zip(
            self.pantalla.botones, MenuPrincipal.OPCIONES, strict=True
        ):
            if opcion.id == opcion_id:
                pulsar(boton)
                return
        raise AssertionError(f"Opción de menú desconocida: {opcion_id!r}")

    def pulsar_texto(self, *fragmentos: str) -> Boton:
        return pulsar_con_texto(self.pantalla, *fragmentos)

    def pulsar_evento(self, *fragmentos: str) -> Boton:
        boton = self._buscar(*fragmentos)
        clic_pantalla(self.pantalla, boton)
        return boton

    def establecer_nombre(self, nombre: str) -> None:
        if not hasattr(self.pantalla, "campo_nombre"):
            raise AssertionError("La pantalla actual no tiene campo de nombre")
        self.pantalla.campo_nombre.texto = nombre

    def pulsar_pausa(self) -> None:
        for boton, tipo in self.app._botones_fijos:
            if tipo == "pausa":
                pulsar(boton)
                return
        raise AssertionError("Botón de pausa no encontrado")

    def pulsar_pausa_opcion(self, indice: int) -> None:
        if not self.app._menu_pausa_abierto:
            self.pulsar_pausa()
        pulsar(self.app._botones_pausa[indice])

    def pulsar_ranking_barra(self) -> None:
        for boton, tipo in self.app._botones_fijos:
            if tipo == "ranking":
                pulsar(boton)
                return
        raise AssertionError("Botón de ranking no encontrado")

    def pulsar_feedback_barra(self) -> None:
        for boton, tipo in self.app._botones_fijos:
            if tipo == "feedback":
                pulsar(boton)
                return
        raise AssertionError("Botón de feedback no encontrado")

    def ejecutar(
        self,
        pasos: Iterable[tuple[str, Callable[[SecuenciaNavegacion], None], tuple[type, ...]]],
    ) -> None:
        for descripcion, accion, tipos_esperados in pasos:
            accion(self)
            try:
                self.comprobar(*tipos_esperados)
            except AssertionError as exc:
                raise AssertionError(f"Tras «{descripcion}»: {exc}") from exc

    def _buscar(self, *fragmentos: str) -> Boton:
        for boton in botones_interactivos(self.pantalla):
            if boton.activo and all(f in boton.etiqueta for f in fragmentos):
                return boton
        visibles = [b.etiqueta for b in botones_interactivos(self.pantalla) if b.activo]
        raise AssertionError(
            f"Sin botón que contenga {fragmentos!r}. Activos: {visibles}"
        )
