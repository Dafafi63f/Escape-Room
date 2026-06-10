#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI unificada para operaciones de materias/criterios.

Fase 1 de consolidación: este archivo enruta a scripts existentes.
"""

from __future__ import annotations

import sys
from pathlib import Path

_FILES = Path(__file__).resolve().parent.parent
_SCRIPTS = _FILES / "Scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))
if str(_FILES) not in sys.path:
    sys.path.insert(0, str(_FILES))

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent.parent
FILES = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(FILES))

from utils_dataset_csv import guardar_filas_csv, materia_de_fila
from utils_puntuacion_materia import MATERIAS, mejor_materia_por_texto, normalizar, puntuar_texto_completo

PATH_CRIT = BASE / "Data" / "criterios_clasificacion_materia.csv"

ALIASES_GUIAS_ES: dict[str, list[str]] = {
    "Àlgebra Lineal": ["álgebra lineal"],
    "Càlcul en una Variable": ["cálculo en una variable"],
    "Fonaments de Computadors": ["fundamentos de computadores"],
    "Iniciació a la Programació": ["iniciación a la programación"],
    "Programari de Sistema": ["software de sistema"],
    "Algorítmia i Combinatòria en Grafs. Mètodes Heurístics": [
        "algoritmia y combinatoria en grafos",
        "métodos heurísticos",
    ],
    "Càlcul en Diverses Variables": ["cálculo en varias variables"],
    "Càlcul Numèric": ["cálculo numérico"],
    "Probabilitat": ["probabilidad"],
    "Programació Orientada als Objectes": ["programación orientada a los objetos"],
    "Bases de Dades Relacionals": ["bases de datos relacionales"],
    "Equacions Diferencials Ordinàries": ["ecuaciones diferenciales ordinarias"],
    "Modelització i Inferència": ["modelización e inferencia"],
    "Tècniques de Disseny d'Algoritmes": ["técnicas de diseño de algoritmos"],
    "Visualització 3D": ["visualización 3d"],
    "Anàlisi Complexa i de Fourier": ["análisis complejo y de fourier"],
    "Anàlisi de Dades Complexes": ["análisis de datos complejos"],
    "Intel·ligència Artificial": ["inteligencia artificial"],
    "Mètodes Numèrics i Probabilístics": ["métodos numéricos y probabilísticos"],
    "Optimització": ["optimización"],
    "Aprenentatge Computacional": ["aprendizaje computacional"],
    "Computació i Simulació d'Altes Prestacions": ["computación de altas prestaciones"],
    "Equacions en Derivades Parcials": ["ecuaciones en derivadas parciales"],
    "Física, Abstracció i Computació": ["física, abstracción y computación"],
    "Teoria de la Informació": ["teoría de la información"],
    "Bases de Dades No Relacionals": ["bases de datos no relacionales"],
    "Informació Quàntica": ["información cuántica"],
    "Modelització i Simulació": ["modelización y simulación"],
    "Sistemes Distribuïts i el Núvol": ["sistemas distribuidos y la nube"],
    "Xarxes Neuronals i Aprenentatge Profund": ["redes neuronales y aprendizaje profundo"],
    "Anàlisi de Dades Financeres": ["análisis de datos financieros"],
    "Anàlisi de Dades Temporals": ["análisis de datos temporales"],
    "Anàlisi Topològica de Dades": ["análisis topológico de datos"],
    "Internet de les Coses": ["internet de las cosas"],
    "Mètodes d Anàlisi en Ciències de la Salut": ["métodos de análisis en ciencias de la salud"],
    "Anàlisi de Dades en Astrofísica": ["análisis de datos en astrofísica"],
    "Bioinformàtica": ["bioinformática"],
    "Informació i Seguretat": ["información y seguridad"],
    "Teoria de Jocs": ["teoría de juegos"],
    "Visió per Computador": ["visión por computador"],
}


def _run(script_name: str, args: list[str]) -> int:
    cmd = [sys.executable, str(FILES / script_name), *args]
    print(f">>> {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=BASE).returncode


def _cmd_criterios_sync_guias(args: argparse.Namespace) -> int:
    with PATH_CRIT.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter=";"))

    total_add = 0
    by_materia = {r["Materia"]: r for r in rows}
    for materia, aliases in ALIASES_GUIAS_ES.items():
        row = by_materia.get(materia)
        if not row:
            continue
        kws = [p.strip() for p in (row.get("Palabras_clave", "")).split("|") if p.strip()]
        norm_set = {normalizar(k) for k in kws}
        for a in aliases:
            if normalizar(a) not in norm_set:
                kws.append(a)
                norm_set.add(normalizar(a))
                total_add += 1
        row["Palabras_clave"] = " | ".join(kws)
        row["N_palabras_clave"] = str(len(kws))

    print(f"Aliases nuevos anadidos: {total_add}")
    if args.dry_run or not args.inplace:
        print("Dry-run: no se ha escrito el CSV.")
        return 0

    with PATH_CRIT.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Guardado: {PATH_CRIT}")
    return 0


def _cmd_criterios_export(args: argparse.Namespace) -> int:
    forward: list[str] = []
    if args.corregir_ids_permutados:
        forward.append("--corregir-ids-permutados")
    return _run("exportar_criterios_clasificacion_materia.py", forward)


def _cmd_dataset_reasignar(args: argparse.Namespace) -> int:
    path_csv = BASE / "Data" / "Preguntas.csv"
    with path_csv.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames or [])
        filas = list(reader)

    cambios: list[tuple[str, str, str, str]] = []
    ambiguas: list[tuple[str, str, str]] = []
    for row in filas:
        rid = str(row.get("Id", ""))
        materia_actual = materia_de_fila(row)
        scores = puntuar_texto_completo(
            row.get("Pregunta", ""),
            row.get("A", ""),
            row.get("B", ""),
            row.get("C", ""),
            row.get("D", ""),
        )
        if not scores:
            ambiguas.append((rid, "sin_match", row.get("Pregunta", "")[:90]))
            continue
        max_score = max(scores.values())
        candidatas = [mid for mid, s in scores.items() if s == max_score]
        if len(candidatas) != 1:
            ambiguas.append((rid, "empate", row.get("Pregunta", "")[:90]))
            continue
        materia_inferida = MATERIAS.get(candidatas[0])
        if materia_inferida and materia_inferida != materia_actual:
            cambios.append((rid, materia_actual, materia_inferida, row.get("Pregunta", "")[:90]))
            row["Materia"] = materia_inferida

    print(f"Filas totales: {len(filas)}")
    print(f"Cambios de Materia: {len(cambios)}")
    print(f"Ambiguas (sin tocar): {len(ambiguas)}")
    if cambios:
        print("\nPrimeros cambios:")
        for rid, ant, nue, pre in cambios[: args.max_detalle]:
            print(f"  Id {rid}: {ant!r} -> {nue!r} | {pre}")
    if ambiguas:
        print("\nPrimeras ambiguas:")
        for rid, motivo, pre in ambiguas[: args.max_detalle]:
            print(f"  Id {rid}: {motivo} | {pre}")

    if args.dry_run or not args.inplace:
        print("\nDry-run: no se ha modificado el CSV.")
        return 0

    guardar_filas_csv(fieldnames, filas, path_csv)
    print(f"\nGuardado: {path_csv}")
    return 0


def _cmd_dataset_actualizar_materia_plantillas(args: argparse.Namespace) -> int:
    path_csv = BASE / "Data" / "Preguntas.csv"
    path_plantillas = BASE / "Data" / "plantillas.json"
    inplace = args.inplace and not args.dry_run

    with path_csv.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames or [])
        filas = list(reader)
    cambios_ds = 0
    sin_ds = 0
    for row in filas:
        actual = materia_de_fila(row)
        mid, _ = mejor_materia_por_texto(
            row.get("Pregunta", ""),
            row.get("A", ""),
            row.get("B", ""),
            row.get("C", ""),
            row.get("D", ""),
        )
        inferida = MATERIAS.get(mid) if mid else None
        if not inferida:
            sin_ds += 1
            continue
        if inferida != actual:
            row["Materia"] = inferida
            cambios_ds += 1
    if inplace:
        guardar_filas_csv(fieldnames, filas, path_csv)

    with path_plantillas.open(encoding="utf-8") as f:
        plantillas = json.load(f)
    nuevas: dict[str, list] = {m: [] for m in plantillas.keys()}
    mov_pl = 0
    sin_pl = 0
    for materia_actual, items in plantillas.items():
        for it in items:
            mid, _ = mejor_materia_por_texto(
                it.get("pregunta", ""),
                it.get("A", ""),
                it.get("B", ""),
                it.get("C", ""),
                it.get("D", ""),
            )
            inferida = MATERIAS.get(mid) if mid else None
            if not inferida:
                sin_pl += 1
                inferida = materia_actual
            if inferida != materia_actual:
                mov_pl += 1
            if inferida not in nuevas:
                nuevas[inferida] = []
            nuevas[inferida].append(it)
    if inplace:
        with path_plantillas.open("w", encoding="utf-8") as f:
            json.dump(nuevas, f, ensure_ascii=False, indent=2)
            f.write("\n")

    print("=== Actualizacion por criterios ===")
    print(f"Dataset: cambios de materia = {cambios_ds}, sin_match = {sin_ds}")
    print(f"Plantillas: movidas de bucket = {mov_pl}, sin_match = {sin_pl}")
    print("Dry-run: no se han escrito cambios." if not inplace else "Cambios guardados.")
    return 0


def _cmd_dataset_aplicar_correcciones(args: argparse.Namespace) -> int:
    forward: list[str] = []
    if args.solo_dataset:
        forward.append("--solo-dataset")
    if args.solo_plantillas:
        forward.append("--solo-plantillas")
    return _run("aplicar_correcciones_materia.py", forward)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="CLI unificada de materias/criterios")
    sub = p.add_subparsers(dest="grupo", required=True)

    p_crit = sub.add_parser("criterios", help="Operaciones sobre criterios de clasificación")
    sub_crit = p_crit.add_subparsers(dest="accion", required=True)

    p_sync = sub_crit.add_parser("sync-guias", help="Añade aliases oficiales de guías")
    p_sync.add_argument("--inplace", action="store_true")
    p_sync.add_argument("--dry-run", action="store_true")
    p_sync.set_defaults(func=_cmd_criterios_sync_guias)

    p_export = sub_crit.add_parser("export", help="Recalcula columnas derivadas de criterios")
    p_export.add_argument("--corregir-ids-permutados", action="store_true")
    p_export.set_defaults(func=_cmd_criterios_export)

    p_ds = sub.add_parser("dataset", help="Operaciones de materia sobre dataset/plantillas")
    sub_ds = p_ds.add_subparsers(dest="accion", required=True)

    p_reas = sub_ds.add_parser("reasignar", help="Reasigna Materia en dataset por criterios")
    p_reas.add_argument("--inplace", action="store_true")
    p_reas.add_argument("--dry-run", action="store_true")
    p_reas.add_argument("--max-detalle", type=int, default=25)
    p_reas.set_defaults(func=_cmd_dataset_reasignar)

    p_amp = sub_ds.add_parser(
        "actualizar-materia-plantillas",
        help="Actualiza Materia en dataset y plantillas por criterios",
    )
    p_amp.add_argument("--inplace", action="store_true")
    p_amp.add_argument("--dry-run", action="store_true")
    p_amp.set_defaults(func=_cmd_dataset_actualizar_materia_plantillas)

    p_corr = sub_ds.add_parser("aplicar-correcciones", help="Aplica correcciones curadas")
    p_corr.add_argument("--solo-dataset", action="store_true")
    p_corr.add_argument("--solo-plantillas", action="store_true")
    p_corr.set_defaults(func=_cmd_dataset_aplicar_correcciones)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    from utils_banco_cerrado import rechazar_script_deprecado

    rechazar_script_deprecado("materias_cli.py")
    raise SystemExit(main())

