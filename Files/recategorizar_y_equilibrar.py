#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Recategoriza una pregunta por Id y equilibra materias con estrategia:

1) Mueve la pregunta a materia nueva (automática por criterios o manual).
2) Crea 1 pregunta nueva en la materia vieja (9+1) desde plantillas.
3) Borra 1 pregunta de la materia nueva (11-1), preferentemente del mismo
   Tipo+Dificultad y de peor encaje semántico.

Cierra con reordenado canónico (solo metadatos) y validación.

Uso:
  python Files/recategorizar_y_equilibrar.py --id 11 --inplace
  python Files/recategorizar_y_equilibrar.py --id 11 --materia-destino "Equacions en Derivades Parcials" --inplace
  python Files/recategorizar_y_equilibrar.py --id 11 --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from balance_lib import ejecutar_reordenar, ejecutar_validar
from dataset_pipeline import generar_pregunta_para_slot
from utils_clasificacion_pregunta import prioridad_eliminacion
from utils_dataset_csv import fila_pregunta, guardar_filas_csv
from utils_puntuacion_materia import mejor_materia_por_texto

PATH_CSV = BASE / "Data" / "Preguntas.csv"
PATH_PLANTILLAS = BASE / "Data" / "plantillas.json"


def _cargar_rows() -> tuple[list[str], list[dict]]:
    with PATH_CSV.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter=";")
        return list(reader.fieldnames or []), list(reader)


def _resolver_materia_destino(row: dict, materia_destino: str | None) -> str | None:
    if materia_destino:
        return materia_destino.strip()
    mid, _ = mejor_materia_por_texto(
        row.get("Pregunta", ""),
        row.get("A", ""),
        row.get("B", ""),
        row.get("C", ""),
        row.get("D", ""),
    )
    if not mid:
        return None
    from utils_puntuacion_materia import MATERIAS

    return MATERIAS.get(mid)


def _elegir_eliminacion(rows: list[dict], materia: str, tipo: str, dificultad: str, id_movida: str) -> int | None:
    # Priorizar mismo Tipo+Dificultad para no desbalancear bloques internos.
    idx_candidatos = [
        i
        for i, r in enumerate(rows)
        if r.get("Materia") == materia
        and r.get("Id") != id_movida
        and r.get("Tipo") == tipo
        and r.get("Dificultad") == dificultad
    ]
    if not idx_candidatos:
        idx_candidatos = [
            i for i, r in enumerate(rows) if r.get("Materia") == materia and r.get("Id") != id_movida
        ]
    if not idx_candidatos:
        return None
    # Menor prioridad_eliminacion => peor encaje => mejor candidata a borrar.
    idx_candidatos.sort(key=lambda i: prioridad_eliminacion(rows[i], materia))
    return idx_candidatos[0]


def _forzar_variante_desde_plantillas(materia: str, claves_existentes: set[tuple]) -> dict | None:
    """Último recurso: crea variante textual mínima para evitar bloqueo."""
    try:
        with PATH_PLANTILLAS.open("r", encoding="utf-8") as f:
            pl = json.load(f)
    except Exception:
        return None
    items = list(pl.get(materia, []))
    if not items:
        return None
    for it in items:
        base_q = str(it.get("pregunta", "")).strip()
        if not base_q:
            continue
        a = str(it.get("A", "")).strip()
        b = str(it.get("B", "")).strip()
        c = str(it.get("C", "")).strip()
        d = str(it.get("D", "")).strip()
        corr = str(it.get("correcta", "A")).strip().upper()[:1] or "A"
        tipo = str(it.get("tipo", "Teoria")).strip() or "Teoria"
        dif = str(it.get("dificultad", "Media")).strip() or "Media"
        for k in range(1, 200):
            q = f"{base_q} (variante {k})"
            key = (q, a, b, c, d)
            if key not in claves_existentes:
                return {
                    "Pregunta": q,
                    "A": a,
                    "B": b,
                    "C": c,
                    "D": d,
                    "Correcta": corr,
                    "Tipo": tipo,
                    "Dificultad": dif,
                }
    return None


def _fallback_manual_por_materia(
    materia: str,
    claves_existentes: set[tuple],
    *,
    tipo: str,
    dificultad: str,
) -> dict | None:
    """Último recurso: banco mínimo curado para no introducir contenido incoherente."""
    bancos: dict[str, list[dict[str, str]]] = {
        "Càlcul en una Variable": [
            {
                "Pregunta": "¿Qué mide la derivada de f en un punto?",
                "A": "La tasa de cambio instantánea",
                "B": "El área bajo la curva",
                "C": "El valor medio en todo el intervalo",
                "D": "El máximo global",
                "Correcta": "A",
            },
            {
                "Pregunta": "¿Cuál es una interpretación geométrica de la derivada en x=a?",
                "A": "Pendiente de la tangente en x=a",
                "B": "Área del rectángulo de base a",
                "C": "Longitud de la curva completa",
                "D": "Curvatura media",
                "Correcta": "A",
            },
            {
                "Pregunta": "Si f es derivable en x=a, entonces f también es:",
                "A": "Periódica",
                "B": "Continua en x=a",
                "C": "Constante",
                "D": "Par",
                "Correcta": "B",
            },
        ]
    }
    for base in bancos.get(materia, []):
        key = (base["Pregunta"], base["A"], base["B"], base["C"], base["D"])
        if key in claves_existentes:
            continue
        g = dict(base)
        g["Tipo"] = tipo
        g["Dificultad"] = dificultad
        return g
    return None


def _plantilla_compatible_con_materia(g: dict, materia_objetivo: str) -> bool:
    """
    Acepta la plantilla si su mejor materia inferida coincide con la objetivo.
    Además, añade veto de marcadores multivariable en Càlcul en una Variable.
    """
    pregunta = g.get("Pregunta", "")
    a = g.get("A", "")
    b = g.get("B", "")
    c = g.get("C", "")
    d = g.get("D", "")
    texto = f"{pregunta} {a} {b} {c} {d}".lower()

    if materia_objetivo == "Càlcul en una Variable":
        # Evita contaminar Càlcul I con contenido claramente multivariable.
        if re.search(r"\b(gradiente|jacobiano|hessian[oa]?|derivada parcial|integral doble)\b", texto):
            return False

    mid, _ = mejor_materia_por_texto(
        pregunta,
        a,
        b,
        c,
        d,
    )
    if not mid:
        return True
    from utils_puntuacion_materia import MATERIAS

    return MATERIAS.get(mid) == materia_objetivo


def recategorizar_y_equilibrar_por_id(
    id_objetivo: str | int,
    materia_destino: str | None,
    *,
    inplace: bool = True,
    dry_run: bool = False,
) -> int:
    """
    API pública: dado un id y materia destino, ejecuta todo el flujo:
    recategoriza + 9+1 + 11-1 + (opcional) guardar/reordenar/validar.
    """
    id_objetivo = str(id_objetivo).strip()
    fieldnames, rows = _cargar_rows()
    row = next((r for r in rows if r.get("Id") == id_objetivo), None)
    if not row:
        print(f"No existe Id {id_objetivo}")
        return 1

    materia_vieja = row.get("Materia", "").strip()
    tipo_slot = row.get("Tipo", "Teoria").strip()
    diff_slot = row.get("Dificultad", "Media").strip()

    mat_nueva = _resolver_materia_destino(row, materia_destino)
    if not mat_nueva:
        print("No se pudo inferir materia destino automáticamente.")
        return 1
    if mat_nueva == materia_vieja:
        print(f"Sin cambios: la pregunta ya está en {mat_nueva!r}.")
        return 0

    # 1) Recategorizar pregunta objetivo.
    row["Materia"] = mat_nueva

    # 2) Crear nueva pregunta en materia vieja (9+1), mismo Tipo+Dificultad.
    claves_existentes = {(r["Pregunta"], r["A"], r["B"], r["C"], r["D"]) for r in rows}
    # Intento estricto y luego degradado para no bloquear el flujo manual.
    # Además, exigimos coherencia semántica con la materia_vieja para evitar
    # "rebotes" (p.ej., meter una de gradiente en Càlcul en una Variable).
    g = None
    for t, d in (
        (tipo_slot, diff_slot),
        (tipo_slot, None),
        (None, diff_slot),
        (None, None),
    ):
        cand = generar_pregunta_para_slot(materia_vieja, claves_existentes, tipo=t, dificultad=d)
        if cand and _plantilla_compatible_con_materia(cand, materia_vieja):
            g = cand
            break
    if not g:
        cand = _forzar_variante_desde_plantillas(materia_vieja, claves_existentes)
        if cand and _plantilla_compatible_con_materia(cand, materia_vieja):
            g = cand
    if not g:
        g = _fallback_manual_por_materia(
            materia_vieja,
            claves_existentes,
            tipo=tipo_slot,
            dificultad=diff_slot,
        )
    if not g:
        print(
            f"No hay plantilla compatible disponible para crear en {materia_vieja!r} "
            "(Tipo/Dificultad objetivo o degradados)."
        )
        return 1

    max_id = max(int(r.get("Id", "0")) for r in rows)
    nueva = fila_pregunta(
        id_=max_id + 1,
        materia=materia_vieja,
        dificultad=g.get("Dificultad", diff_slot),
        tipo=g.get("Tipo", tipo_slot),
        pregunta=g["Pregunta"],
        a=g["A"],
        b=g["B"],
        c=g["C"],
        d=g["D"],
        correcta=g["Correcta"],
    )
    rows.append(nueva)

    # 3) Borrar una de la materia nueva (11-1), evitando la movida.
    tipo_elim = nueva["Tipo"]
    diff_elim = nueva["Dificultad"]
    idx_borrar = _elegir_eliminacion(rows, mat_nueva, tipo_elim, diff_elim, id_objetivo)
    if idx_borrar is None:
        print(f"No se encontró candidata para borrar en {mat_nueva!r}.")
        return 1
    borrada = rows.pop(idx_borrar)

    print(f"Id {id_objetivo}: Materia {materia_vieja!r} -> {mat_nueva!r}")
    print(
        "Añadida 1 en materia vieja: "
        f"{materia_vieja!r} (Tipo={nueva['Tipo']} Dificultad={nueva['Dificultad']})"
    )
    print(
        "Eliminada 1 en materia nueva: "
        f"Id {borrada.get('Id')} de {mat_nueva!r} "
        f"(Tipo={borrada.get('Tipo')} Dificultad={borrada.get('Dificultad')})"
    )

    if dry_run or not inplace:
        print("Dry-run: no se guardan cambios.")
        return 0

    guardar_filas_csv(fieldnames, rows, PATH_CSV)
    # Regla de trabajo del proyecto: ordenar al final.
    rc = ejecutar_reordenar(solo_metadatos=True, sin_permutar_respuestas=True)
    if rc != 0:
        return rc
    return ejecutar_validar(detalle=False, estricto=False)


def ejecutar(id_objetivo: str, materia_destino: str | None, inplace: bool, dry_run: bool) -> int:
    """Compatibilidad con llamadas previas."""
    return recategorizar_y_equilibrar_por_id(
        id_objetivo=id_objetivo,
        materia_destino=materia_destino,
        inplace=inplace,
        dry_run=dry_run,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--id", required=True, help="Id de la pregunta a recategorizar")
    parser.add_argument(
        "--materia-destino",
        default=None,
        help="Materia destino manual (si no se indica, se infiere por criterios)",
    )
    parser.add_argument("--inplace", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.inplace and not args.dry_run:
        args.dry_run = True

    return ejecutar(
        id_objetivo=str(args.id).strip(),
        materia_destino=args.materia_destino,
        inplace=args.inplace,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    raise SystemExit(main())
