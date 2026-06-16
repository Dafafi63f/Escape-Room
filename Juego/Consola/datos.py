#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Carga de datos (compartida) y elección de banco en consola."""

from __future__ import annotations

from pathlib import Path

from Comun.datos import *  # noqa: F403
from Comun.modelos import BancoPreguntas, ETIQUETA_BANCO, Pregunta


def elegir_banco_preguntas(
    path_csv: Path,
    path_plantillas: Path,
    materias_meta: dict[str, dict[str, str]],
) -> tuple[list[Pregunta], BancoPreguntas]:
    try:
        conteos = contar_bancos(path_csv, path_plantillas, materias_meta)
    except FileNotFoundError as e:
        print(str(e))
        print("Usando solo el dataset revisado.")
        return cargar_preguntas(path_csv, materias_meta), BancoPreguntas.DATASET

    n_ds = conteos[BancoPreguntas.DATASET]
    n_extra = conteos[BancoPreguntas.PLANTILLAS_EXTRA]
    n_todo = conteos[BancoPreguntas.PLANTILLAS_TODO]

    from .entrada_menu import elegir_indice_menu
    from .navegacion import ContextoPantalla, VolverAtras, mostrar_transicion

    def _mostrar_menu_banco() -> None:
        print("\nBanco de preguntas:")
        print(
            f"  1) Dataset revisado — MODO SEGURO ({n_ds} preguntas) [por defecto, recomendado]"
        )
        print(
            f"  2) Todo — MODO BETA ({n_ds} + {n_extra} = {n_todo}): "
            "dataset + plantillas no revisadas"
        )
        print(f"  3) Solo plantillas extra — MODO BETA ({n_extra} no revisadas)")
        print("     La opcion 1 es el banco seguro. Las opciones 2 y 3 incluyen contenido beta.")

    mapa_banco = {
        1: BancoPreguntas.DATASET,
        2: BancoPreguntas.PLANTILLAS_TODO,
        3: BancoPreguntas.PLANTILLAS_EXTRA,
    }

    mostrar_transicion(
        _mostrar_menu_banco,
        contexto=ContextoPantalla(titulo="Banco de preguntas", reimprimir=_mostrar_menu_banco),
    )

    while True:
        try:
            idx = elegir_indice_menu(
                3,
                defecto=1,
                permitir_atras=True,
                prompt="Selecciona banco",
            )
        except VolverAtras:
            raise
        banco = mapa_banco[idx]
        n = conteos[banco]
        if n == 0:
            print("Ese banco no tiene preguntas jugables. Prueba otra opcion.")
            continue
        break

    modo_txt, desc = ETIQUETA_BANCO[banco]
    print(f"\n>>> {modo_txt}: {desc} ({n} preguntas cargadas)")
    if banco != BancoPreguntas.DATASET:
        print(
            "AVISO: incluye preguntas no revisadas. "
            "Usa el banco 1 (modo seguro) para evaluación fiable del TFG."
        )

    from Comun.pool_libre import cargar_pool_por_banco

    preguntas = cargar_pool_por_banco(
        banco,
        preguntas_dataset=cargar_preguntas(path_csv, materias_meta),
        path_preguntas_csv=path_csv,
        path_plantillas_json=path_plantillas,
        materias_meta=materias_meta,
    )
    return preguntas, banco
