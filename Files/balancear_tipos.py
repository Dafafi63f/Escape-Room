# -*- coding: utf-8 -*-
"""
Balancea los tipos: mitad Teoria y mitad Calculo del total del dataset (400 → 200 y 200).
Estrategia: eliminar exceso y crear preguntas nuevas del tipo deficitario.
"""

import csv
import json
import re
from collections import defaultdict
from objetivos_balanceo import preguntas_por_tipo_global
from utils_orden_temas import cargar_orden_temas
from utils_dataset_csv import fila_pregunta, guardar_filas_csv
from borrar_pycache import borrar_pycache_en_proyecto

PATH_PREGUNTAS = "Data/Preguntas.csv"
PATH_PLANTILLAS = "Data/plantillas.json"
TARGET = preguntas_por_tipo_global()


def puntuar_como_calculo(pregunta, a, b, c, d):
    """
    Heurístico: mayor score = más parecida a cálculo.
    """
    texto = f"{pregunta} {a} {b} {c} {d}"
    score = 0
    if re.search(r'\d+', texto):
        score += 2
    if re.search(r'[=+\-*/^∫∑∏√π]', texto):
        score += 2
    if re.search(r'\b(media|varianza|integral|derivada|limite|límite|determinante|rango|matriz|vector)\b', texto.lower()):
        score += 2
    if re.search(r'\b(cuánto|cuántos|cuál es|valor|calcular)\b', texto.lower()):
        score += 1
    return score


def main():
    temas_ordenados, _ = cargar_orden_temas()
    tema_rank = {t: i for i, t in enumerate(temas_ordenados)}
    fallback_rank = len(tema_rank)

    with open(PATH_PLANTILLAS, "r", encoding="utf-8") as f:
        raw = json.load(f)
    plantillas_calculo = {
        tema: [t for t in items if t.get("uso") == "calculo"]
        for tema, items in raw.items()
    }
    plantillas_teoria = {
        tema: [t for t in items if t.get("uso") == "general" and t.get("tipo") == "Teoria"]
        for tema, items in raw.items()
    }

    with open(PATH_PREGUNTAS, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = reader.fieldnames
        rows = list(reader)

    conteos = defaultdict(int)
    for r in rows:
        conteos[r["Tipo"]] += 1

    print("Estado actual:")
    print(f"  Teoria: {conteos['Teoria']}")
    print(f"  Calculo: {conteos['Calculo']}")

    exceso_teoria = max(0, conteos["Teoria"] - TARGET)
    exceso_calculo = max(0, conteos["Calculo"] - TARGET)
    deficit_teoria = max(0, TARGET - conteos["Teoria"])
    deficit_calculo = max(0, TARGET - conteos["Calculo"])

    indices_eliminar = set()
    eliminadas_por_tema = defaultdict(int)
    tipo_a_añadir = None  # "Calculo" o "Teoria"
    plantillas_a_usar = None

    if exceso_teoria > 0:
        # Eliminar Teoria, añadir Calculo
        temas_con_plantillas = {t for t, items in plantillas_calculo.items() if items}
        candidatos = [
            (i, puntuar_como_calculo(r["Pregunta"], r["A"], r["B"], r["C"], r["D"]))
            for i, r in enumerate(rows)
            if r["Tipo"] == "Teoria" and r["Materia"] in temas_con_plantillas
        ]
        candidatos.sort(key=lambda x: -x[1])
        for i in range(exceso_teoria):
            indices_eliminar.add(candidatos[i][0])
        for i in indices_eliminar:
            eliminadas_por_tema[rows[i]["Materia"]] += 1
        tipo_a_añadir = "Calculo"
        plantillas_a_usar = plantillas_calculo
        n_a_eliminar, n_a_añadir = exceso_teoria, exceso_teoria

    elif exceso_calculo > 0:
        # Eliminar Calculo, añadir Teoria (las Calculo que más parecen teoría = menor score)
        temas_con_plantillas = {t for t, items in plantillas_teoria.items() if items}
        candidatos = [
            (i, puntuar_como_calculo(r["Pregunta"], r["A"], r["B"], r["C"], r["D"]))
            for i, r in enumerate(rows)
            if r["Tipo"] == "Calculo" and r["Materia"] in temas_con_plantillas
        ]
        candidatos.sort(key=lambda x: x[1])  # Menor score primero (más tipo teoría)
        for i in range(exceso_calculo):
            indices_eliminar.add(candidatos[i][0])
        for i in indices_eliminar:
            eliminadas_por_tema[rows[i]["Materia"]] += 1
        tipo_a_añadir = "Teoria"
        plantillas_a_usar = plantillas_teoria
        n_a_eliminar, n_a_añadir = exceso_calculo, exceso_calculo

    filas_filtradas = [r for i, r in enumerate(rows) if i not in indices_eliminar]
    eliminadas = len(rows) - len(filas_filtradas)

    nuevas_filas = []
    if tipo_a_añadir and plantillas_a_usar:
        max_id = max(int(r["Id"]) for r in filas_filtradas)
        claves_existentes = {(r["Pregunta"], r["A"], r["B"], r["C"], r["D"]) for r in filas_filtradas}
        template_idx = defaultdict(int)

        for tema, n_añadir in eliminadas_por_tema.items():
            templates = plantillas_a_usar.get(tema, [])
            if not templates:
                continue
            for _ in range(n_añadir):
                t = templates[template_idx[tema] % len(templates)]
                template_idx[tema] += 1
                pregunta = t["pregunta"]
                a, b, c, d = t["A"], t["B"], t["C"], t["D"]
                clave = (pregunta, a, b, c, d)
                if clave in claves_existentes:
                    pregunta = pregunta.rstrip() + " (variante)"
                claves_existentes.add((pregunta, a, b, c, d))

                max_id += 1
                nuevas_filas.append(
                    fila_pregunta(
                        id_=max_id,
                        materia=tema,
                        dificultad=t.get("dificultad", "Media"),
                        tipo=tipo_a_añadir,
                        pregunta=pregunta,
                        a=a,
                        b=b,
                        c=c,
                        d=d,
                        correcta=t["correcta"],
                    )
                )

        # Si faltan
        faltan = n_a_añadir - len(nuevas_filas) if tipo_a_añadir else 0
        if faltan > 0:
            temas = list(plantillas_a_usar.keys())
            idx_tema = 0
            while faltan > 0:
                tema = temas[idx_tema % len(temas)]
                templates = plantillas_a_usar.get(tema, [])
                for t in templates:
                    if faltan <= 0:
                        break
                    pregunta, a, b, c, d = t["pregunta"], t["A"], t["B"], t["C"], t["D"]
                    clave = (pregunta, a, b, c, d)
                    if clave not in claves_existentes:
                        claves_existentes.add(clave)
                        max_id += 1
                        nuevas_filas.append(
                            fila_pregunta(
                                id_=max_id,
                                materia=tema,
                                dificultad=t.get("dificultad", "Media"),
                                tipo=tipo_a_añadir,
                                pregunta=pregunta,
                                a=a,
                                b=b,
                                c=c,
                                d=d,
                                correcta=t["correcta"],
                            )
                        )
                        faltan -= 1
                idx_tema += 1
                if idx_tema > len(temas) * 5:
                    break

    todas = filas_filtradas + nuevas_filas
    todas.sort(key=lambda r: (tema_rank.get(r["Materia"], fallback_rank), int(r["Id"])))

    for i, r in enumerate(todas, start=1):
        r["Id"] = str(i)

    guardar_filas_csv(list(fieldnames or []), todas)

    conteos_final = defaultdict(int)
    for r in todas:
        conteos_final[r["Tipo"]] += 1

    tipo_elim = "Teoria" if exceso_teoria > 0 else "Calculo"
    tipo_add = "Calculo" if exceso_teoria > 0 else "Teoria"
    print(f"\nEliminadas: {eliminadas} preguntas ({tipo_elim})")
    print(f"Añadidas: {len(nuevas_filas)} preguntas {tipo_add} nuevas")
    print("\nResultado final:")
    print(f"  Teoria: {conteos_final['Teoria']} {'[OK]' if conteos_final['Teoria'] == TARGET else f'(obj:{TARGET})'}")
    print(f"  Calculo: {conteos_final['Calculo']} {'[OK]' if conteos_final['Calculo'] == TARGET else f'(obj:{TARGET})'}")
    print(f"\nTotal: {len(todas)} preguntas")

    por_tema = defaultdict(int)
    for r in todas:
        por_tema[r["Materia"]] += 1
    min_t, max_t = min(por_tema.values()), max(por_tema.values())
    print(f"Por tema: min={min_t}, max={max_t}")


if __name__ == "__main__":
    try:
        main()
    finally:
        borrar_pycache_en_proyecto()
