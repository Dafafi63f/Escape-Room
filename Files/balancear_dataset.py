# -*- coding: utf-8 -*-
"""
Balancea el dataset: elimina preguntas de temas con exceso (priorizando las de menor
encaje semántico, ver `utils_puntuacion_materia.py`) y genera preguntas nuevas desde plantillas
para temas con déficit.
Objetivo: mismo número de preguntas por cada materia del listado (400 en total; ver `objetivos_balanceo.py`).
"""

import csv
import json
import re
from collections import defaultdict
from objetivos_balanceo import TARGET_TOTAL_PREGUNTAS, preguntas_por_materia
from utils_orden_temas import cargar_orden_temas
from utils_dataset_csv import fila_pregunta, guardar_filas_csv
from utils_puntuacion_materia import MATERIA_TO_ID, MATERIAS, puntuar_texto_completo
from borrar_pycache import borrar_pycache_en_proyecto

TARGET = preguntas_por_materia()
TARGET_TOTAL = TARGET_TOTAL_PREGUNTAS
PATH_PREGUNTAS = "Data/Preguntas.csv"
PATH_PLANTILLAS = "Data/plantillas.json"


def cargar_plantillas():
    with open(PATH_PLANTILLAS, "r", encoding="utf-8") as f:
        raw = json.load(f)
    # Priorizar general; si no hay, usar cualquiera (dificil/calculo) para temas sin plantillas general
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


def generar_preguntas_desde_plantillas(tema, cantidad, plantillas, claves_existentes=None):
    """Genera hasta 'cantidad' preguntas para el tema desde plantillas."""
    templates = plantillas.get(tema, [])
    if not templates:
        return []
    claves_existentes = claves_existentes or set()
    resultado = []
    vistos = set(claves_existentes)  # Evitar duplicados exactos
    idx = 0
    intentos_sin_nuevas = 0
    while len(resultado) < cantidad:
        t = templates[idx % len(templates)]
        nuevas = expandir_plantilla(t)
        añadidas = 0
        for n in nuevas:
            if len(resultado) >= cantidad:
                break
            clave = (n["Pregunta"], n["A"], n["B"], n["C"], n["D"])
            if clave in vistos:
                continue
            vistos.add(clave)
            resultado.append({**n, "Materia": tema})
            añadidas += 1
        if añadidas == 0:
            intentos_sin_nuevas += 1
            if intentos_sin_nuevas >= len(templates) * 2:
                break  # No hay más preguntas únicas
        else:
            intentos_sin_nuevas = 0
        idx += 1
        if idx > 500:
            break
    return resultado[:cantidad]


def main():
    plantillas = cargar_plantillas()

    with open(PATH_PREGUNTAS, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = reader.fieldnames
        filas = list(reader)

    # Índice: tema -> lista de (idx_fila, score para ese tema)
    por_tema = defaultdict(list)
    for idx, fila in enumerate(filas):
        tema = fila["Materia"]
        mat_id = MATERIA_TO_ID.get(tema, 1)
        scores = puntuar_texto_completo(
            fila["Pregunta"],
            fila.get("A", ""),
            fila.get("B", ""),
            fila.get("C", ""),
            fila.get("D", ""),
        )
        score_tema = scores.get(mat_id, 0)
        por_tema[tema].append((idx, score_tema))

    # Calcular exceso y déficit
    conteo = defaultdict(int)
    for tema, lst in por_tema.items():
        conteo[tema] = len(lst)

    # Asegurar todos los temas del listado
    temas_a_procesar = list(MATERIAS.values())
    for t in temas_a_procesar:
        if t not in conteo:
            conteo[t] = 0
        if t not in por_tema:
            por_tema[t] = []

    total_deficit = sum(max(0, TARGET - conteo[t]) for t in temas_a_procesar)
    total_exceso = sum(max(0, conteo[t] - TARGET) for t in temas_a_procesar)
    total_generable = 0
    for tema in temas_a_procesar:
        deficit = max(0, TARGET - conteo[tema])
        generables = len(generar_preguntas_desde_plantillas(tema, deficit, plantillas))
        total_generable += generables

    # Eliminar todo el exceso (también cuando no hay déficit y total > TARGET_TOTAL)
    total_a_eliminar = total_exceso

    # 1) ELIMINAR exceso: marcar índices a eliminar (priorizar peor encaje semántico)
    indices_eliminar = set()
    eliminadas_por_tema = {t: 0 for t in temas_a_procesar}
    for tema in temas_a_procesar:
        n = conteo[tema]
        exceso = max(0, n - TARGET)
        if exceso == 0:
            continue
        lst = por_tema[tema]
        lst_ordenada = sorted(lst, key=lambda x: (x[1], x[0]))
        for i in range(exceso):
            if sum(eliminadas_por_tema.values()) >= total_a_eliminar:
                break
            idx = lst_ordenada[i][0]
            indices_eliminar.add(idx)
            eliminadas_por_tema[tema] += 1
        if sum(eliminadas_por_tema.values()) >= total_a_eliminar:
            break

    # Repartir eliminaciones proporcionalmente entre temas con exceso si aún no llegamos
    if sum(eliminadas_por_tema.values()) < total_a_eliminar:
        temas_con_exceso = [(t, conteo[t] - TARGET - eliminadas_por_tema[t]) for t in temas_a_procesar
                           if conteo[t] - TARGET - eliminadas_por_tema[t] > 0]
        temas_con_exceso.sort(key=lambda x: -x[1])
        faltan = total_a_eliminar - sum(eliminadas_por_tema.values())
        for tema, exc in temas_con_exceso:
            if faltan <= 0:
                break
            lst = por_tema[tema]
            ya_elim = eliminadas_por_tema[tema]
            lst_ordenada = sorted(lst, key=lambda x: (x[1], x[0]))
            for i in range(ya_elim, min(ya_elim + faltan, len(lst_ordenada))):
                idx = lst_ordenada[i][0]
                if idx not in indices_eliminar:
                    indices_eliminar.add(idx)
                    eliminadas_por_tema[tema] += 1
                    faltan -= 1

    # Filtrar filas: mantener las no eliminadas
    filas_filtradas = [f for i, f in enumerate(filas) if i not in indices_eliminar]
    eliminadas = len(filas) - len(filas_filtradas)

    # 2) AÑADIR preguntas nuevas para temas con déficit
    max_id = max(int(f.get("Id", 0)) for f in filas_filtradas) if filas_filtradas else 0
    nuevas_filas = []
    for tema in temas_a_procesar:
        n_actual = sum(1 for f in filas_filtradas if f["Materia"] == tema)
        deficit = max(0, TARGET - n_actual)
        if deficit == 0:
            continue
        generadas = generar_preguntas_desde_plantillas(tema, deficit, plantillas)
        for g in generadas:
            max_id += 1
            nuevas_filas.append(
                fila_pregunta(
                    id_=max_id,
                    materia=g["Materia"],
                    dificultad=g["Dificultad"],
                    tipo=g["Tipo"],
                    pregunta=g["Pregunta"],
                    a=g["A"],
                    b=g["B"],
                    c=g["C"],
                    d=g["D"],
                    correcta=g["Correcta"],
                )
            )

    todas = filas_filtradas + nuevas_filas

    # 3) Si total < TARGET_TOTAL, añadir más preguntas a temas con déficit hasta llegar
    faltan_total = max(0, TARGET_TOTAL - len(todas))
    extra_añadidas = 0
    if faltan_total > 0:
        max_id = max(int(f.get("Id", 0)) for f in todas)
        claves_existentes = {(f["Pregunta"], f["A"], f["B"], f["C"], f["D"]) for f in todas}
        temas_con_deficit = [(t, TARGET - sum(1 for f in todas if f["Materia"] == t))
                             for t in temas_a_procesar
                             if sum(1 for f in todas if f["Materia"] == t) < TARGET]
        temas_con_deficit.sort(key=lambda x: -x[1])  # Mayor déficit primero
        idx_tema = 0
        while extra_añadidas < faltan_total and temas_con_deficit:
            tema = temas_con_deficit[idx_tema % len(temas_con_deficit)][0]
            n_actual = sum(1 for f in todas if f["Materia"] == tema)
            deficit_restante = TARGET - n_actual
            a_generar = min(faltan_total - extra_añadidas, deficit_restante, 100)
            if a_generar > 0:
                generadas = generar_preguntas_desde_plantillas(tema, a_generar, plantillas, claves_existentes)
                for g in generadas:
                    if extra_añadidas >= faltan_total:
                        break
                    max_id += 1
                    todas.append(
                        fila_pregunta(
                            id_=max_id,
                            materia=g["Materia"],
                            dificultad=g["Dificultad"],
                            tipo=g["Tipo"],
                            pregunta=g["Pregunta"],
                            a=g["A"],
                            b=g["B"],
                            c=g["C"],
                            d=g["D"],
                            correcta=g["Correcta"],
                        )
                    )
                    extra_añadidas += 1
                    claves_existentes.add((g["Pregunta"], g["A"], g["B"], g["C"], g["D"]))
            idx_tema += 1
            if idx_tema > len(temas_con_deficit) * 10:
                break

    # Ordenar por tema siguiendo listado_materias, luego por Id original.
    temas_orden, _ = cargar_orden_temas()
    tema_rank = {t: i for i, t in enumerate(temas_orden)}
    fallback_rank = len(tema_rank)
    todas.sort(key=lambda r: (tema_rank.get(r["Materia"], fallback_rank), int(r["Id"])))

    # Reasignar IDs a todas las filas para mantener orden
    for i, f in enumerate(todas, start=1):
        f["Id"] = str(i)

    # Escribir
    guardar_filas_csv([], todas)

    # Estadísticas
    from collections import Counter
    conteo_final = Counter(f["Materia"] for f in todas)
    min_c = min(conteo_final.values())
    max_c = max(conteo_final.values())

    print(f"Balanceo completado.")
    print(f"  Eliminadas: {eliminadas} preguntas (de temas con exceso)")
    print(f"  Añadidas: {len(nuevas_filas) + extra_añadidas} preguntas (desde plantillas)")
    print(f"  Total final: {len(todas)} preguntas")
    print(f"  Distribución: min={min_c}, max={max_c}")
    print(f"\nConteo por tema:")
    for tema in temas_orden:
        if tema not in conteo_final:
            continue
        n = conteo_final[tema]
        diff = n - TARGET
        signo = "+" if diff > 0 else ""
        print(f"  {tema}: {n} ({signo}{diff})")

if __name__ == "__main__":
    try:
        main()
    finally:
        borrar_pycache_en_proyecto()
