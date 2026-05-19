# -*- coding: utf-8 -*-
"""
Script para crear o borrar x preguntas del dataset de forma aleatoria.
Uso:
  python crear_borrar_preguntas.py crear 50   -> crea 50 preguntas nuevas
  python crear_borrar_preguntas.py borrar 30   -> borra 30 preguntas aleatorias

Al terminar, el script ordena por listado+Id ligero; para el orden canónico completo
del TFG ejecutar `python Files/balance.py reordenar`.
"""

import argparse
import csv
import json
import random
import sys
from pathlib import Path
from utils_orden_temas import cargar_orden_temas
from utils_dataset_csv import fila_pregunta, guardar_filas_csv, ordenar_filas_por_tema_y_id, renumerar_ids
from borrar_pycache import borrar_pycache_en_proyecto

# Rutas relativas al directorio del proyecto
BASE = Path(__file__).resolve().parent.parent
PATH_PREGUNTAS = BASE / "Data" / "Preguntas.csv"
PATH_PLANTILLAS = BASE / "Data" / "plantillas.json"


def cargar_plantillas():
    """Carga plantillas priorizando uso general."""
    with open(PATH_PLANTILLAS, "r", encoding="utf-8") as f:
        raw = json.load(f)
    result = {}
    for tema, items in raw.items():
        generales = [t for t in items if t.get("uso") == "general"]
        result[tema] = generales if generales else items
    return result


def expandir_plantilla(template):
    """Convierte una plantilla en una o más preguntas (según variaciones)."""
    preguntas = []
    variaciones = template.get("variaciones")
    if variaciones:
        for var in variaciones:
            p = template["pregunta"]
            a = template["A"]
            b = template["B"]
            c = template["C"]
            d = template["D"]
            for key, val in var.items():
                placeholder = "{" + str(key) + "}"
                p = p.replace(placeholder, str(val))
                a = a.replace(placeholder, str(val))
                b = b.replace(placeholder, str(val))
                c = c.replace(placeholder, str(val))
                d = d.replace(placeholder, str(val))
            preguntas.append({
                "Pregunta": p,
                "A": a, "B": b, "C": c, "D": d,
                "Correcta": template["correcta"],
                "Dificultad": template.get("dificultad", "Media"),
                "Tipo": template.get("tipo", "Teoria"),
            })
    else:
        preguntas.append({
            "Pregunta": template["pregunta"],
            "A": template["A"], "B": template["B"], "C": template["C"], "D": template["D"],
            "Correcta": template["correcta"],
            "Dificultad": template.get("dificultad", "Media"),
            "Tipo": template.get("tipo", "Teoria"),
        })
    return preguntas


def obtener_claves_existentes(filas):
    """Extrae claves (pregunta, A, B, C, D) de las filas existentes."""
    return {(f["Pregunta"], f["A"], f["B"], f["C"], f["D"]) for f in filas}


def generar_preguntas_aleatorias(cantidad, plantillas, temas, claves_existentes):
    """
    Genera 'cantidad' preguntas nuevas repartidas aleatoriamente entre temas.
    Evita duplicados respecto a claves_existentes.
    """
    todas_plantillas = []
    for tema in temas:
        templates = plantillas.get(tema, [])
        for t in templates:
            todas_plantillas.append((tema, t))

    if not todas_plantillas:
        return []

    vistos = set(claves_existentes)
    resultado = []
    intentos_max = cantidad * 20
    intentos = 0

    while len(resultado) < cantidad and intentos < intentos_max:
        tema, template = random.choice(todas_plantillas)
        nuevas = expandir_plantilla(template)
        random.shuffle(nuevas)
        for n in nuevas:
            if len(resultado) >= cantidad:
                break
            clave = (n["Pregunta"], n["A"], n["B"], n["C"], n["D"])
            if clave in vistos:
                continue
            vistos.add(clave)
            resultado.append({**n, "Materia": tema})
        intentos += 1

    return resultado[:cantidad]


def crear_preguntas(cantidad):
    """Crea x preguntas nuevas desde plantillas y las añade al dataset."""
    plantillas = cargar_plantillas()

    with open(PATH_PREGUNTAS, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames)
        filas = list(reader)

    temas_ordenados, _ = cargar_orden_temas()

    temas = [t for t in temas_ordenados if t in plantillas]
    if not temas:
        temas = list(plantillas.keys())
    if not temas:
        temas = list(dict.fromkeys((f.get("Materia") or f.get("Tema") or "").strip() for f in filas if (f.get("Materia") or f.get("Tema"))))

    claves = obtener_claves_existentes(filas)
    nuevas = generar_preguntas_aleatorias(cantidad, plantillas, temas, claves)

    if len(nuevas) < cantidad:
        print(f"  [AVISO] Solo se pudieron generar {len(nuevas)} preguntas únicas (se pidieron {cantidad})")

    if not nuevas:
        print("  No se generaron preguntas nuevas.")
        return

    max_id = max(int(f["Id"]) for f in filas)
    for i, p in enumerate(nuevas):
        filas.append(
            fila_pregunta(
                id_=max_id + 1 + i,
                materia=p["Materia"],
                dificultad=p["Dificultad"],
                tipo=p["Tipo"],
                pregunta=p["Pregunta"],
                a=p["A"],
                b=p["B"],
                c=p["C"],
                d=p["D"],
                correcta=p["Correcta"],
            )
        )

    filas = ordenar_filas_por_tema_y_id(filas)
    renumerar_ids(filas)

    guardar_filas_csv(fieldnames, filas)

    print(f"  Creadas {len(nuevas)} preguntas nuevas. Total: {len(filas)}")


def borrar_preguntas(cantidad):
    """Borra x preguntas aleatorias del dataset."""
    with open(PATH_PREGUNTAS, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames)
        filas = list(reader)

    if cantidad >= len(filas):
        print(f"  [AVISO] Se borrarían todas las preguntas. Limitando a {len(filas) - 1}.")
        cantidad = len(filas) - 1

    indices_borrar = set(random.sample(range(len(filas)), cantidad))
    filas_nuevas = [f for i, f in enumerate(filas) if i not in indices_borrar]

    filas_nuevas = ordenar_filas_por_tema_y_id(filas_nuevas)
    renumerar_ids(filas_nuevas)

    guardar_filas_csv(fieldnames, filas_nuevas)

    print(f"  Borradas {cantidad} preguntas. Total: {len(filas_nuevas)}")


def main():
    parser = argparse.ArgumentParser(
        description="Crear o borrar preguntas del dataset de forma aleatoria."
    )
    parser.add_argument(
        "accion",
        choices=["crear", "borrar"],
        help="'crear' para añadir preguntas, 'borrar' para eliminarlas",
    )
    parser.add_argument(
        "cantidad",
        type=int,
        help="Número de preguntas a crear o borrar",
    )
    args = parser.parse_args()

    if args.cantidad <= 0:
        print("  La cantidad debe ser mayor que 0.")
        sys.exit(1)

    if args.accion == "crear":
        print(f"Creando {args.cantidad} preguntas nuevas...")
        crear_preguntas(args.cantidad)
    else:
        print(f"Borrando {args.cantidad} preguntas aleatorias...")
        borrar_preguntas(args.cantidad)


if __name__ == "__main__":
    try:
        main()
    finally:
        borrar_pycache_en_proyecto()
