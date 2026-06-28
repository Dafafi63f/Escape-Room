#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Capturas de pantalla del juego pygame para la memoria TFG (sin ventana visible).

Renderiza pantallas como la aplicación real: contenido + barra fija superior
(pausa, diarios, ranking, feedback, opciones). Usa SDL_VIDEODRIVER=dummy,
igual que los tests en CI.

Uso (desde la raíz del proyecto):
  python Docs/capturar_pantallas_juego.py
  python Docs/capturar_pantallas_juego.py --forzar
"""

from __future__ import annotations

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import sys
from pathlib import Path
from typing import Callable
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
DOCS = Path(__file__).resolve().parent
FIGURAS = DOCS / "Figuras"
_JUEGO = ROOT / "Juego"

if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

SEMILLA_CAPTURA = 42
ESCAPE_REF_ALTURA_MAX = 680
ESCAPE_REF_SEPARACION = 28
ESCAPE_REF_COLOR_SEPARADOR = (200, 210, 225)

CAPTURAS_SALIDA = (
    "tfg_menu_principal.png",
    "tfg_escape_referencia.png",
    "tfg_escape_tienda.png",
)

CAPTURAS_OBSOLETAS = (
    "tfg_menu_modos_especiales.png",
    "tfg_escape_puertas.png",
    "tfg_escape_pregunta_inventario.png",
)


def _init_pygame() -> None:
    import pygame

    from Grafico.fuentes import invalidar_cache_fuentes

    if pygame.get_init():
        pygame.quit()
    pygame.init()
    pygame.display.set_mode((960, 720))
    invalidar_cache_fuentes()


def _crear_datos_juego():
    from Comun.datos import cargar_materias, cargar_preguntas
    from Comun.rutas import PATH_MATERIAS, PATH_PREGUNTAS, resolver_plantillas
    from Grafico.app import DatosJuego

    materias_meta = cargar_materias(PATH_MATERIAS)
    preguntas = cargar_preguntas(PATH_PREGUNTAS, materias_meta)
    return DatosJuego(
        num_preguntas=len(preguntas),
        num_materias=len(materias_meta),
        preguntas=preguntas,
        materias_meta=materias_meta,
        path_preguntas_csv=PATH_PREGUNTAS,
        path_plantillas_json=resolver_plantillas(),
    )


def _superficie_pantalla_como_app(pantalla):
    import pygame

    from Grafico.app import dibujar_barra_iconos_fijos
    from Grafico.tema import ALTO, ANCHO, COLOR_FONDO, crear_fuentes

    superficie = pygame.Surface((ANCHO, ALTO))
    fuentes = crear_fuentes()
    pantalla.dibujar(superficie)
    dibujar_barra_iconos_fijos(superficie, fuentes)
    return superficie


def _guardar_pantalla_como_app(pantalla, destino: Path) -> Path:
    import pygame

    destino.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(_superficie_pantalla_como_app(pantalla), str(destino))
    return destino


def _superficie_a_pil(superficie):
    import pygame
    from PIL import Image

    data = pygame.image.tobytes(superficie, "RGB")
    return Image.frombytes("RGB", superficie.get_size(), data)


def _componer_escape_referencia(superficie_arriba, superficie_abajo, destino: Path) -> Path:
    """Apila dos capturas 960×720 reducidas para caber en una página del informe."""
    from PIL import Image, ImageDraw

    from Grafico.tema import COLOR_FONDO

    arriba = _superficie_a_pil(superficie_arriba)
    abajo = _superficie_a_pil(superficie_abajo)
    altura_panel = (ESCAPE_REF_ALTURA_MAX - ESCAPE_REF_SEPARACION) // 2
    ancho_panel = int(arriba.width * altura_panel / arriba.height)
    arriba = arriba.resize((ancho_panel, altura_panel), Image.Resampling.LANCZOS)
    abajo = abajo.resize((ancho_panel, altura_panel), Image.Resampling.LANCZOS)
    total_h = altura_panel * 2 + ESCAPE_REF_SEPARACION
    canvas = Image.new("RGB", (ancho_panel, total_h), COLOR_FONDO)
    canvas.paste(arriba, (0, 0))
    canvas.paste(abajo, (0, altura_panel + ESCAPE_REF_SEPARACION))

    draw = ImageDraw.Draw(canvas)
    y_linea = altura_panel + ESCAPE_REF_SEPARACION // 2
    draw.line(
        [(0, y_linea), (ancho_panel - 1, y_linea)],
        fill=ESCAPE_REF_COLOR_SEPARADOR,
        width=2,
    )

    destino.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destino)
    return destino


def _crear_menu_principal():
    from Grafico.pantallas import MenuPrincipal

    datos = _crear_datos_juego()
    return MenuPrincipal(datos, lambda _p: None, lambda: None)


def _crear_partida_escape(*, semilla: int = SEMILLA_CAPTURA):
    from Comun.datos import cargar_preguntas
    from Comun.escape_partida import construir_pool_escape, materias_del_pool
    from Comun.escape_room import config_escape_room, total_preguntas_escape
    from Comun.presets_historia import aplicar_preset, buscar_preset
    from Grafico.pantallas_escape import PartidaEscapeRoom

    datos = _crear_datos_juego()
    preset = buscar_preset("escape_room")
    config = config_escape_room()
    pool = construir_pool_escape(
        cargar_preguntas(datos.path_preguntas_csv, datos.materias_meta),
        path_csv=datos.path_preguntas_csv,
        path_plantillas=datos.path_plantillas_json,
        materias_meta=datos.materias_meta,
    )
    if not pool:
        raise RuntimeError("No hay preguntas disponibles para capturar el escape room.")
    reglas = aplicar_preset(preset, None)
    return PartidaEscapeRoom(
        nombre="Captura memoria",
        preset=preset,
        config=config,
        pool=pool,
        materias_pool=materias_del_pool(pool),
        reglas=reglas,
        semilla=semilla,
        total_previsto=total_preguntas_escape(config),
        ir_a=lambda _p: None,
        datos=datos,
        salir_app=lambda: None,
    )


def _indice_puerta_contenido(partida) -> int:
    from Comun.tienda_escape import puerta_es_tienda

    for i, puerta in enumerate(partida.puertas_actuales):
        if puerta.modificadores.sin_pregunta or puerta_es_tienda(puerta):
            continue
        return i
    raise RuntimeError("No hay puerta de contenido en la sala actual.")


def _preparar_fase_pregunta_inventario(partida) -> None:
    from Comun.objetos_partida import POWERUPS

    idx = _indice_puerta_contenido(partida)
    partida._elegir_puerta(idx)
    if partida.fase != "pregunta":
        raise RuntimeError(f"Se esperaba fase pregunta, obtuvo {partida.fase!r}.")
    for pid in POWERUPS:
        partida.inventario_escape.agregar(pid)
    partida._reconstruir_inventario_botones()


def _preparar_fase_tienda(partida) -> None:
    from Comun.economia_partida import puede_visitar_tienda_escape
    from Comun.tienda_escape import puerta_es_tienda

    partida.estado.puntos_arcade = max(partida.estado.puntos_arcade, 500)
    for sala_idx in range(partida.config.n_salas):
        partida.sala_idx = sala_idx
        partida._preparar_puertas()
        for i, puerta in enumerate(partida.puertas_actuales):
            if not puerta_es_tienda(puerta):
                continue
            if not puede_visitar_tienda_escape(
                sala_idx + 1,
                partida.estado,
                vidas_max=partida.vidas_max,
            ):
                continue
            partida._elegir_puerta(i)
            if partida.fase == "tienda":
                return
    raise RuntimeError("No se encontró una visita a tienda reproducible con la semilla fija.")


def _eliminar_capturas_obsoletas(destino_dir: Path) -> None:
    for nombre in CAPTURAS_OBSOLETAS:
        ruta = destino_dir / nombre
        if ruta.is_file():
            ruta.unlink()


def generar_capturas_juego(
    *,
    semilla: int = SEMILLA_CAPTURA,
    destino_dir: Path | None = None,
) -> list[Path]:
    """Genera PNG del menú y del escape room con barra fija superior."""
    destino_dir = destino_dir or FIGURAS
    _init_pygame()
    _eliminar_capturas_obsoletas(destino_dir)

    rutas: list[Path] = []

    rutas.append(
        _guardar_pantalla_como_app(
            _crear_menu_principal(),
            destino_dir / "tfg_menu_principal.png",
        )
    )

    with patch("Comun.escape_room.semilla_partida_escape", return_value=semilla):
        partida_puertas = _crear_partida_escape(semilla=semilla)
        superficie_puertas = _superficie_pantalla_como_app(partida_puertas)

        partida_pregunta = _crear_partida_escape(semilla=semilla)
        _preparar_fase_pregunta_inventario(partida_pregunta)
        superficie_pregunta = _superficie_pantalla_como_app(partida_pregunta)

        rutas.append(
            _componer_escape_referencia(
                superficie_puertas,
                superficie_pregunta,
                destino_dir / "tfg_escape_referencia.png",
            )
        )

        partida_tienda = _crear_partida_escape(semilla=semilla)
        _preparar_fase_tienda(partida_tienda)
        rutas.append(
            _guardar_pantalla_como_app(
                partida_tienda,
                destino_dir / "tfg_escape_tienda.png",
            )
        )

    return rutas


# Compatibilidad con generar_figuras_memoria.py
generar_capturas_escape = generar_capturas_juego


def _mtime(ruta: Path) -> float:
    try:
        return ruta.stat().st_mtime
    except OSError:
        return 0.0


def capturas_necesitan_regeneracion() -> tuple[bool, str]:
    salidas = [FIGURAS / n for n in CAPTURAS_SALIDA]
    faltan = [p.name for p in salidas if not p.is_file()]
    if faltan:
        return True, f"faltan {', '.join(faltan)}"
    if any((FIGURAS / nombre).is_file() for nombre in CAPTURAS_OBSOLETAS):
        return True, "quedan capturas obsoletas"
    mas_reciente_salida = max(_mtime(p) for p in salidas)
    entradas = [
        Path(__file__).resolve(),
        _JUEGO / "Grafico" / "app.py",
        _JUEGO / "Grafico" / "pantallas_modos.py",
        _JUEGO / "Grafico" / "pantallas.py",
        _JUEGO / "Grafico" / "tema.py",
    ]
    for ruta in entradas:
        if ruta.is_file() and _mtime(ruta) > mas_reciente_salida + 1e-6:
            return True, f"cambió {ruta.name}"
    return False, ""


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        description="Captura pantallas del juego pygame (menús + escape room)."
    )
    parser.add_argument(
        "--forzar",
        action="store_true",
        help="Regenerar aunque no haya cambios en el código",
    )
    args = parser.parse_args(argv)

    if not args.forzar:
        necesita, motivo = capturas_necesitan_regeneracion()
        if not necesita:
            print("=== CAPTURAS PYGAME ===")
            print(f"  Sin cambios; se reutilizan {len(CAPTURAS_SALIDA)} PNG en Docs/Figuras/")
            print("  (usa --forzar para regenerar)")
            return 0
        print(f"=== CAPTURAS PYGAME === Regenerando ({motivo})")

    rutas = generar_capturas_juego()
    for ruta in rutas:
        print(f"  OK {ruta.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
