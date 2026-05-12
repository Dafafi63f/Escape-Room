# -*- coding: utf-8 -*-
"""
Elimina preguntas duplicadas del dataset, reemplazándolas por preguntas nuevas
desde plantillas cuando es posible. Se considera duplicado cuando pregunta, A, B, C y D
son idénticos.
"""

import csv
import json
import random
from utils_dataset_csv import guardar_filas_csv, ordenar_filas_por_tema_y_id, renumerar_ids
from borrar_pycache import borrar_pycache_en_proyecto

PATH_PREGUNTAS = "Data/Preguntas.csv"
PATH_PLANTILLAS = "Data/plantillas.json"


def cargar_plantillas():
    """Carga todas las plantillas (general, dificil, calculo) para máxima capacidad."""
    with open(PATH_PLANTILLAS, "r", encoding="utf-8") as f:
        raw = json.load(f)
    result = {}
    for tema, items in raw.items():
        result[tema] = items
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


def generar_reemplazo(tema, plantillas, claves_existentes):
    """Genera una pregunta nueva para el tema que no esté en claves_existentes."""
    templates = plantillas.get(tema, [])
    if not templates:
        return None
    # Probar plantillas en orden aleatorio para variedad
    orden = list(range(len(templates)))
    random.shuffle(orden)
    for idx in orden:
        t = templates[idx]
        for n in expandir_plantilla(t):
            clave = (n["Pregunta"], n["A"], n["B"], n["C"], n["D"])
            if clave not in claves_existentes:
                return {**n, "Materia": tema}
    return None


def main():
    plantillas = cargar_plantillas()

    with open(PATH_PREGUNTAS, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = list(reader.fieldnames)
        filas = list(reader)

    # Detectar duplicados: clave -> lista de índices (el primero se mantiene)
    clave_a_indices = {}
    for idx, fila in enumerate(filas):
        clave = (fila["Pregunta"], fila["A"], fila["B"], fila["C"], fila["D"])
        if clave not in clave_a_indices:
            clave_a_indices[clave] = []
        clave_a_indices[clave].append(idx)

    # Índices a reemplazar (duplicados, no el primero de cada grupo)
    indices_a_reemplazar = []
    for clave, indices in clave_a_indices.items():
        if len(indices) > 1:
            # Mantener el primero, reemplazar el resto
            indices_a_reemplazar.extend(indices[1:])

    if not indices_a_reemplazar:
        print("No hay preguntas duplicadas.")
        return

    # Claves que ya existen (las que vamos a mantener)
    claves_existentes = set()
    for idx, fila in enumerate(filas):
        if idx not in indices_a_reemplazar:
            clave = (fila["Pregunta"], fila["A"], fila["B"], fila["C"], fila["D"])
            claves_existentes.add(clave)

    reemplazadas = 0
    eliminadas = 0

    for idx in sorted(indices_a_reemplazar):
        fila = filas[idx]
        materia = (fila.get("Materia") or fila.get("Tema") or "").strip()
        reemplazo = generar_reemplazo(materia, plantillas, claves_existentes)
        if reemplazo:
            filas[idx] = {
                "Id": fila["Id"],
                "Pregunta": reemplazo["Pregunta"],
                "Materia": materia,
                "Dificultad": reemplazo["Dificultad"],
                "Tipo": reemplazo["Tipo"],
                "A": reemplazo["A"], "B": reemplazo["B"], "C": reemplazo["C"], "D": reemplazo["D"],
                "Correcta": reemplazo["Correcta"],
            }
            clave_nueva = (reemplazo["Pregunta"], reemplazo["A"], reemplazo["B"], reemplazo["C"], reemplazo["D"])
            claves_existentes.add(clave_nueva)
            reemplazadas += 1
        else:
            # No hay plantilla para reemplazar: marcar para eliminar
            filas[idx] = None
            eliminadas += 1

    # Eliminar las que no pudieron reemplazarse
    filas = [f for f in filas if f is not None]

    filas = ordenar_filas_por_tema_y_id(filas)
    renumerar_ids(filas)

    guardar_filas_csv(list(fieldnames or []), filas)

    print(f"Duplicados procesados: {len(indices_a_reemplazar)}")
    print(f"  Reemplazados por preguntas nuevas: {reemplazadas}")
    if eliminadas > 0:
        print(f"  Eliminados (sin plantilla de reemplazo): {eliminadas}")
    print(f"Total final: {len(filas)} preguntas")


if __name__ == "__main__":
    try:
        main()
    finally:
        borrar_pycache_en_proyecto()
