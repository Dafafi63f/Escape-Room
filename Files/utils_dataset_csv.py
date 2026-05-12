#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilidades compartidas para leer/escribir y ordenar filas del dataset CSV.
"""

from __future__ import annotations

import csv
from pathlib import Path
from utils_orden_temas import cargar_orden_temas, key_orden_tema


BASE = Path(__file__).resolve().parent.parent
PATH_PREGUNTAS = BASE / "Data" / "Preguntas.csv"
PATH_LISTADO_MATERIAS = BASE / "Data" / "listado_materias.csv"

# Cabecera canónica de Data/Preguntas.csv (solo lo no redundante con listado_materias.csv).
# Grupo, Nivel, Curso, Semestre, Tematica, Id del catálogo y ComplejidadGlobal se obtienen
# al vuelo desde el listado + fórmula (ver enriquecer_metadatos_desde_listado, complejidad_global_valor).
COLUMNAS_PREGUNTAS: tuple[str, ...] = (
    "Id",
    "Materia",
    "Dificultad",
    "Tipo",
    "Pregunta",
    "A",
    "B",
    "C",
    "D",
    "Correcta",
)


def fila_pregunta(
    *,
    id_: str | int,
    materia: str,
    dificultad: str,
    tipo: str,
    pregunta: str,
    a: str,
    b: str,
    c: str,
    d: str,
    correcta: str,
) -> dict[str, str]:
    """Construye una fila con las mismas claves que COLUMNAS_PREGUNTAS (CSV mínimo)."""
    return {
        "Id": str(id_).strip(),
        "Materia": (materia or "").strip(),
        "Dificultad": (dificultad or "").strip(),
        "Tipo": (tipo or "").strip(),
        "Pregunta": (pregunta or "").strip(),
        "A": (a or "").strip(),
        "B": (b or "").strip(),
        "C": (c or "").strip(),
        "D": (d or "").strip(),
        "Correcta": (correcta or "").strip().upper(),
    }


def mapa_metadatos_por_materia(path_listado: Path | None = None) -> dict[str, dict[str, str]]:
    """
    Devuelve Materia -> {IdMateria, Grupo, Nivel, Curso, Semestre, Tematica} desde listado_materias.csv.
    IdMateria corresponde a la columna Id del listado (identificador de la asignatura).
    """
    path = path_listado or PATH_LISTADO_MATERIAS
    out: dict[str, dict[str, str]] = {}
    if not path.exists():
        return out
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        for row in reader:
            nombre = (row.get("Materia") or "").strip()
            if not nombre:
                continue
            out[nombre] = {
                "IdMateria": str(row.get("Id", "") or "").strip(),
                "Grupo": (row.get("Grupo") or "").strip(),
                "Nivel": (row.get("Nivel") or "").strip(),
                "Curso": (row.get("Curso") or row.get("Año") or row.get("Ano") or "").strip(),
                "Semestre": (row.get("Semestre") or "").strip(),
                "Tematica": (row.get("Tematica") or "").strip(),
            }
    return out


def complejidad_global_valor(nivel: str, dificultad: str) -> int:
    """Misma formula que el juego: Nivel(entero>=1) + base(Dificultad) - 1."""
    try:
        nv = max(1, int(float(str(nivel).strip() or "1")))
    except (TypeError, ValueError):
        nv = 1
    db = {"Facil": 1, "Media": 2, "Dificil": 3}.get(str(dificultad).strip(), 2)
    return nv + db - 1


def enriquecer_metadatos_desde_listado(
    fila: dict, mapa: dict[str, dict[str, str]] | None = None
) -> None:
    """Rellena IdMateria..Tematica desde el listado y ComplejidadGlobal (muta fila)."""
    m = mapa if mapa is not None else mapa_metadatos_por_materia()
    mat = materia_de_fila(fila)
    meta = m.get(mat, {})
    for clave in ("IdMateria", "Grupo", "Nivel", "Curso", "Semestre", "Tematica"):
        fila[clave] = meta.get(clave, "")
    nivel = str(fila.get("Nivel") or "").strip()
    diff = str(fila.get("Dificultad") or "").strip()
    fila["ComplejidadGlobal"] = str(complejidad_global_valor(nivel, diff))


def materia_de_fila(fila: dict) -> str:
    """Nombre de materia: columna oficial `Materia`, con compatibilidad `Tema` antigua."""
    m = fila.get("Materia")
    if m is not None and str(m).strip():
        return str(m).strip()
    t = fila.get("Tema")
    return (str(t).strip() if t is not None else "")


def cargar_filas_csv(path_csv: Path | None = None) -> tuple[list[str], list[dict]]:
    """Carga un CSV ';' y devuelve (fieldnames, filas)."""
    path = path_csv or PATH_PREGUNTAS
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames or [])
        filas = list(reader)
    for row in filas:
        if not (row.get("Materia") or "").strip() and (row.get("Tema") or "").strip():
            row["Materia"] = str(row["Tema"]).strip()
    return fieldnames, filas


def guardar_filas_csv(
    fieldnames: list[str] | None, filas: list[dict], path_csv: Path | None = None
) -> None:
    """
    Guarda filas en CSV ';' con UTF-8.
    Solo persiste COLUMNAS_PREGUNTAS (en ese orden). Antes de escribir, enriquece en copia
    para comprobar coherencia con el listado; no vuelca al CSV columnas derivadas.
    El primer argumento se conserva por compatibilidad con scripts antiguos y no determina el orden.
    """
    _ = fieldnames
    path = path_csv or PATH_PREGUNTAS
    mapa = mapa_metadatos_por_materia()
    out_fn = list(COLUMNAS_PREGUNTAS)
    out_rows: list[dict] = []
    for f in filas:
        f = dict(f)
        enriquecer_metadatos_desde_listado(f, mapa)
        row: dict[str, str] = {}
        for c in COLUMNAS_PREGUNTAS:
            if c == "Materia":
                row[c] = materia_de_fila(f)
            else:
                v = f.get(c, "")
                row[c] = "" if v is None else str(v)
        out_rows.append(row)
    with path.open("w", encoding="utf-8", newline="") as fp:
        writer = csv.DictWriter(fp, fieldnames=out_fn, delimiter=";")
        writer.writeheader()
        writer.writerows(out_rows)


def ordenar_filas_por_tema_y_id(filas: list[dict]) -> list[dict]:
    """
    Ordena filas por materia (`listado_materias.csv`) y luego por Id numérico.

    No aplica el orden canónico completo del banco (bloques 5+5 Teoría/Cálculo,
    escalón TF…TM…TD / CF…CM…CD, reparto F/M/D por bloque de 10 ni ciclo ABCD).
    Tras editar el CSV con scripts de mantenimiento, conviene ejecutar
    `reordenar_balance_por_materia.py` (o `ordenar_dataset.py`, que delega en él).
    """
    _, tema_rank = cargar_orden_temas()
    return sorted(
        filas,
        key=lambda r: (key_orden_tema(tema_rank, materia_de_fila(r)), int(r["Id"])),
    )


def renumerar_ids(filas: list[dict], start: int = 1) -> None:
    """Renumera la columna Id en el orden actual de la lista."""
    for i, fila in enumerate(filas, start=start):
        fila["Id"] = str(i)
