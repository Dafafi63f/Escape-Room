# -*- coding: utf-8 -*-
"""Regeneracion del dataset desde plantillas (invocado por balance.py)."""

from __future__ import annotations

import csv
import json
import random
from collections import defaultdict
from pathlib import Path

import pandas as pd

BASE = Path(__file__).resolve().parent.parent
PATH_CSV = BASE / "Data" / "Preguntas.csv"
PATH_PLANTILLAS = BASE / "Data" / "plantillas.json"

from objetivos_balanceo import (
    TARGET_TOTAL_PREGUNTAS,
    lista_objetivos_correcta,
    objetivos_correcta_por_letra,
    objetivos_dificultad_por_totales,
    preguntas_por_materia,
    preguntas_por_tipo_global,
)
from utils_clasificacion_pregunta import clasificar_fila, prioridad_eliminacion, puntuar_como_calculo, puntuar_tipo
from utils_dataset_csv import COLUMNAS_PREGUNTAS, fila_pregunta, guardar_filas_csv
from utils_orden_temas import cargar_orden_temas
from utils_puntuacion_materia import MATERIAS

TARGET_MATERIA = preguntas_por_materia()
TARGET_TIPO_GLOBAL = preguntas_por_tipo_global()
TARGET_POR_TIPO = TARGET_MATERIA // 2

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




def ejecutar_balancear_materias() -> None:
    plantillas = cargar_plantillas()

    with open(PATH_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = reader.fieldnames
        filas = list(reader)

    # Índice: tema -> lista de (idx_fila, score para ese tema)
    por_tema = defaultdict(list)
    for idx, fila in enumerate(filas):
        tema = fila["Materia"]
        score_tema = prioridad_eliminacion(fila, tema)
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

    total_deficit = sum(max(0, TARGET_MATERIA - conteo[t]) for t in temas_a_procesar)
    total_exceso = sum(max(0, conteo[t] - TARGET_MATERIA) for t in temas_a_procesar)
    total_generable = 0
    for tema in temas_a_procesar:
        deficit = max(0, TARGET_MATERIA - conteo[tema])
        generables = len(generar_preguntas_desde_plantillas(tema, deficit, plantillas))
        total_generable += generables

    # Eliminar todo el exceso (también cuando no hay déficit y total > TARGET_TOTAL_PREGUNTAS)
    total_a_eliminar = total_exceso

    # 1) ELIMINAR exceso: marcar índices a eliminar (priorizar peor encaje semántico)
    indices_eliminar = set()
    eliminadas_por_tema = {t: 0 for t in temas_a_procesar}
    for tema in temas_a_procesar:
        n = conteo[tema]
        exceso = max(0, n - TARGET_MATERIA)
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
        temas_con_exceso = [(t, conteo[t] - TARGET_MATERIA - eliminadas_por_tema[t]) for t in temas_a_procesar
                           if conteo[t] - TARGET_MATERIA - eliminadas_por_tema[t] > 0]
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
        deficit = max(0, TARGET_MATERIA - n_actual)
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

    # 3) Si total < TARGET_TOTAL_PREGUNTAS, añadir más preguntas a temas con déficit hasta llegar
    faltan_total = max(0, TARGET_TOTAL_PREGUNTAS - len(todas))
    extra_añadidas = 0
    if faltan_total > 0:
        max_id = max(int(f.get("Id", 0)) for f in todas)
        claves_existentes = {(f["Pregunta"], f["A"], f["B"], f["C"], f["D"]) for f in todas}
        temas_con_deficit = [(t, TARGET_MATERIA - sum(1 for f in todas if f["Materia"] == t))
                             for t in temas_a_procesar
                             if sum(1 for f in todas if f["Materia"] == t) < TARGET_MATERIA]
        temas_con_deficit.sort(key=lambda x: -x[1])  # Mayor déficit primero
        idx_tema = 0
        while extra_añadidas < faltan_total and temas_con_deficit:
            tema = temas_con_deficit[idx_tema % len(temas_con_deficit)][0]
            n_actual = sum(1 for f in todas if f["Materia"] == tema)
            deficit_restante = TARGET_MATERIA - n_actual
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

    # Ordenar por tema siguiendo listado_materias, luego por Id (orden ligero).
    # Para el orden canónico del TFG (ladder TF..TD/CF..CD, bloques F/M/D, ciclo ABCD), ejecutar
    # `python Files/balance.py reordenar` al final del pipeline agresivo.
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
        diff = n - TARGET_MATERIA
        signo = "+" if diff > 0 else ""
        print(f"  {tema}: {n} ({signo}{diff})")



def cargar_plantillas_por_tipo() -> dict:
    with open(PATH_PLANTILLAS, encoding="utf-8") as f:
        raw = json.load(f)
    return {
        "teoria": {t: [x for x in items if x.get("tipo") == "Teoria"] for t, items in raw.items()},
        "calculo": {t: [x for x in items if x.get("tipo") == "Calculo"] for t, items in raw.items()},
    }


def expandir_plantilla_tipo(t):
    """Convierte plantilla en preguntas (con variaciones)."""
    preguntas = []
    variaciones = t.get("variaciones", [{}])
    for var in variaciones:
        p, a, b, c, d = t["pregunta"], t["A"], t["B"], t["C"], t["D"]
        for k, v in var.items():
            ph = "{" + str(k) + "}"
            p, a, b, c, d = p.replace(ph, str(v)), a.replace(ph, str(v)), b.replace(ph, str(v)), c.replace(ph, str(v)), d.replace(ph, str(v))
        preguntas.append({"Pregunta": p, "A": a, "B": b, "C": c, "D": d, "Correcta": t["correcta"],
                         "Dificultad": t.get("dificultad", "Media"), "Tipo": t.get("tipo", "Teoria")})
    return preguntas


def generar_preguntas(tema, tipo, cantidad, plantillas, claves_existentes):
    """Genera preguntas del tipo indicado para el tema."""
    templates = plantillas[tipo].get(tema, [])
    if not templates:
        return []
    resultado = []
    vistos = set(claves_existentes)
    idx = 0
    while len(resultado) < cantidad and idx < len(templates) * 10:
        t = templates[idx % len(templates)]
        for n in expandir_plantilla_tipo(t):
            if len(resultado) >= cantidad:
                break
            clave = (n["Pregunta"], n["A"], n["B"], n["C"], n["D"])
            if clave in vistos:
                continue
            vistos.add(clave)
            resultado.append({**n, "Materia": tema})
        idx += 1
    return resultado


def ordenar_para_downgrade(rows, indices):
    """Indices ordenados: más fáciles primero (para bajar dificultad)."""
    def score(i):
        r = rows[i]
        p = r["Pregunta"].strip().lower()
        es_conceptual = 1 if p.startswith("¿qué es") else 0
        return (-es_conceptual, len(r["Pregunta"]))
    return sorted(indices, key=score)


def ordenar_para_upgrade(rows, indices):
    """Indices ordenados: más difíciles primero (para subir dificultad)."""
    def score(i):
        r = rows[i]
        p = r["Pregunta"].strip().lower()
        es_conceptual = 1 if p.startswith("¿qué es") else 0
        return (es_conceptual, -len(r["Pregunta"]))
    return sorted(indices, key=score)




def ejecutar_balancear_tipo_dificultad() -> None:
    temas_ordenados, tema_rank = cargar_orden_temas()
    fallback_rank = len(tema_rank)
    plantillas = cargar_plantillas_por_tipo()

    with open(PATH_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = reader.fieldnames
        rows = list(reader)

    # Paso 1: Balancear Tipo por tema (36 Teoria, 36 Calculo)
    por_tema_tipo = defaultdict(lambda: defaultdict(list))
    for i, r in enumerate(rows):
        por_tema_tipo[r["Materia"]][r["Tipo"]].append(i)

    indices_eliminar = set()
    nuevas_filas = []
    claves_existentes = {(r["Pregunta"], r["A"], r["B"], r["C"], r["D"]) for r in rows}
    max_id = max(int(r["Id"]) for r in rows)

    for tema in list(por_tema_tipo.keys()):
        teoria_idx = por_tema_tipo[tema]["Teoria"]
        calculo_idx = por_tema_tipo[tema]["Calculo"]
        n_t, n_c = len(teoria_idx), len(calculo_idx)

        # ¿Necesitamos más Teoria? Eliminar Calculo, añadir Teoria
        if n_t < TARGET_POR_TIPO and n_c > TARGET_POR_TIPO:
            a_eliminar = min(n_c - TARGET_POR_TIPO, TARGET_POR_TIPO - n_t)
            candidatos = [
                (
                    i,
                    puntuar_tipo(
                        rows[i]["Pregunta"],
                        rows[i]["A"],
                        rows[i]["B"],
                        rows[i]["C"],
                        rows[i]["D"],
                        rows[i].get("Correcta", "A"),
                    )["Teoria"],
                )
                for i in calculo_idx
            ]
            candidatos.sort(key=lambda x: x[1])  # Mayor Teoria = menos cálculo (eliminar primero)
            for j in range(a_eliminar):
                indices_eliminar.add(candidatos[j][0])
            generadas = generar_preguntas(tema, "teoria", a_eliminar, plantillas, claves_existentes)
            for g in generadas:
                max_id += 1
                claves_existentes.add((g["Pregunta"], g["A"], g["B"], g["C"], g["D"]))
                nuevas_filas.append(
                    fila_pregunta(
                        id_=max_id,
                        materia=tema,
                        dificultad=g["Dificultad"],
                        tipo="Teoria",
                        pregunta=g["Pregunta"],
                        a=g["A"],
                        b=g["B"],
                        c=g["C"],
                        d=g["D"],
                        correcta=g["Correcta"],
                    )
                )

        # ¿Necesitamos más Calculo? Eliminar Teoria, añadir Calculo
        elif n_c < TARGET_POR_TIPO and n_t > TARGET_POR_TIPO:
            a_eliminar = min(n_t - TARGET_POR_TIPO, TARGET_POR_TIPO - n_c)
            candidatos = [
                (
                    i,
                    puntuar_como_calculo(
                        rows[i]["Pregunta"],
                        rows[i]["A"],
                        rows[i]["B"],
                        rows[i]["C"],
                        rows[i]["D"],
                    ),
                )
                for i in teoria_idx
            ]
            candidatos.sort(key=lambda x: -x[1])  # Mayor = más cálculo (eliminar estas)
            for j in range(a_eliminar):
                indices_eliminar.add(candidatos[j][0])
            generadas = generar_preguntas(tema, "calculo", a_eliminar, plantillas, claves_existentes)
            for g in generadas:
                max_id += 1
                claves_existentes.add((g["Pregunta"], g["A"], g["B"], g["C"], g["D"]))
                nuevas_filas.append(
                    fila_pregunta(
                        id_=max_id,
                        materia=tema,
                        dificultad=g["Dificultad"],
                        tipo="Calculo",
                        pregunta=g["Pregunta"],
                        a=g["A"],
                        b=g["B"],
                        c=g["C"],
                        d=g["D"],
                        correcta=g["Correcta"],
                    )
                )

    filas = [r for i, r in enumerate(rows) if i not in indices_eliminar] + nuevas_filas

    # Recalcular índices por (Tema, Tipo, Dificultad)
    por_tema_tipo_diff = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
    for i, r in enumerate(filas):
        por_tema_tipo_diff[r["Materia"]][r["Tipo"]][r["Dificultad"]].append(i)

    # Paso 2: Balancear Dificultad dentro de cada (Tema, Tipo) a 12 cada una
    for tema in list(por_tema_tipo_diff.keys()):
        for tipo in ["Teoria", "Calculo"]:
            diff_counts = por_tema_tipo_diff[tema][tipo]
            total = sum(len(diff_counts[d]) for d in ["Facil", "Media", "Dificil"])
            if total == 0:
                continue
            base = total // 3
            resto = total % 3
            t_f = base + (1 if resto >= 1 else 0)
            t_m = base + (1 if resto >= 2 else 0)
            t_d = total - t_f - t_m

            idx_f = diff_counts["Facil"]
            idx_m = diff_counts["Media"]
            idx_d = diff_counts["Dificil"]
            n_f, n_m, n_d = len(idx_f), len(idx_m), len(idx_d)

            need_f, need_m, need_d = t_f - n_f, t_m - n_m, t_d - n_d

            # Ajustar Facil
            if need_f > 0:
                for i in ordenar_para_downgrade(filas, idx_m)[:need_f]:
                    filas[i]["Dificultad"] = "Facil"
                    need_f -= 1
                    if need_f == 0:
                        break
                if need_f > 0:
                    for i in ordenar_para_downgrade(filas, idx_d)[:need_f]:
                        filas[i]["Dificultad"] = "Facil"
                        need_f -= 1
                        if need_f == 0:
                            break
            elif need_f < 0:
                for i in ordenar_para_upgrade(filas, idx_f)[:-need_f]:
                    filas[i]["Dificultad"] = "Media"
                    need_f += 1
                    if need_f == 0:
                        break

            # Recalcular
            idx_f = [i for i, r in enumerate(filas) if r["Materia"] == tema and r["Tipo"] == tipo and r["Dificultad"] == "Facil"]
            idx_m = [i for i, r in enumerate(filas) if r["Materia"] == tema and r["Tipo"] == tipo and r["Dificultad"] == "Media"]
            idx_d = [i for i, r in enumerate(filas) if r["Materia"] == tema and r["Tipo"] == tipo and r["Dificultad"] == "Dificil"]
            n_m, n_d = len(idx_m), len(idx_d)
            need_m = t_m - n_m

            # Ajustar Media
            if need_m > 0:
                for i in ordenar_para_downgrade(filas, idx_d)[:need_m]:
                    filas[i]["Dificultad"] = "Media"
                    need_m -= 1
                    if need_m == 0:
                        break
                if need_m > 0:
                    idx_f = [i for i, r in enumerate(filas) if r["Materia"] == tema and r["Tipo"] == tipo and r["Dificultad"] == "Facil"]
                    for i in ordenar_para_upgrade(filas, idx_f)[:need_m]:
                        filas[i]["Dificultad"] = "Media"
                        need_m -= 1
                        if need_m == 0:
                            break
            elif need_m < 0:
                for i in ordenar_para_upgrade(filas, idx_m)[:-need_m]:
                    filas[i]["Dificultad"] = "Dificil"
                    need_m += 1
                    if need_m == 0:
                        break

    # Reordenar: Tema, Tipo (Teoria primero), Dificultad (Facil, Media, Dificil)
    orden_tipo = {"Teoria": 0, "Calculo": 1}
    orden_diff = {"Facil": 0, "Media": 1, "Dificil": 2}
    filas.sort(
        key=lambda r: (
            tema_rank.get(r["Materia"], fallback_rank),
            orden_tipo[r["Tipo"]],
            orden_diff[r["Dificultad"]],
        )
    )

    for i, r in enumerate(filas, start=1):
        r["Id"] = str(i)

    guardar_filas_csv(list(fieldnames or []), filas)

    print("Balanceo completado. Objetivo: reparto de tipo y dificultad por materia.")
    print(f"  Eliminadas: {len(indices_eliminar)}, Añadidas: {len(nuevas_filas)}")
    print("\nVerificación - primeras 3 materias:")
    from collections import Counter
    temas_presentes = [t for t in temas_ordenados if any(r["Materia"] == t for r in filas)]
    for tema in temas_presentes[:3]:
        print(f"\n  {tema}:")
        for (tipo, diff), count in sorted(Counter((r["Tipo"], r["Dificultad"]) for r in filas if r["Materia"] == tema).items()):
            print(f"    {tipo} {diff}: {count}")




def ejecutar_balancear_tipos() -> None:
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

    with open(PATH_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = reader.fieldnames
        rows = list(reader)

    conteos = defaultdict(int)
    for r in rows:
        conteos[r["Tipo"]] += 1

    print("Estado actual:")
    print(f"  Teoria: {conteos['Teoria']}")
    print(f"  Calculo: {conteos['Calculo']}")

    exceso_teoria = max(0, conteos["Teoria"] - TARGET_TIPO_GLOBAL)
    exceso_calculo = max(0, conteos["Calculo"] - TARGET_TIPO_GLOBAL)
    deficit_teoria = max(0, TARGET_TIPO_GLOBAL - conteos["Teoria"])
    deficit_calculo = max(0, TARGET_TIPO_GLOBAL - conteos["Calculo"])

    indices_eliminar = set()
    eliminadas_por_tema = defaultdict(int)
    tipo_a_añadir = None  # "Calculo" o "Teoria"
    plantillas_a_usar = None

    if exceso_teoria > 0:
        # Eliminar Teoria, añadir Calculo
        temas_con_plantillas = {t for t, items in plantillas_calculo.items() if items}
        candidatos = [
            (
                i,
                puntuar_como_calculo(r["Pregunta"], r["A"], r["B"], r["C"], r["D"]),
            )
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
            (
                i,
                puntuar_tipo(
                    r["Pregunta"], r["A"], r["B"], r["C"], r["D"], r.get("Correcta", "A")
                )["Teoria"],
            )
            for i, r in enumerate(rows)
            if r["Tipo"] == "Calculo" and r["Materia"] in temas_con_plantillas
        ]
        candidatos.sort(key=lambda x: -x[1])  # Mayor Teoria = menos cálculo
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
    print(f"  Teoria: {conteos_final['Teoria']} {'[OK]' if conteos_final['Teoria'] == TARGET_TIPO_GLOBAL else f'(obj:{TARGET_TIPO_GLOBAL})'}")
    print(f"  Calculo: {conteos_final['Calculo']} {'[OK]' if conteos_final['Calculo'] == TARGET_TIPO_GLOBAL else f'(obj:{TARGET_TIPO_GLOBAL})'}")
    print(f"\nTotal: {len(todas)} preguntas")

    por_tema = defaultdict(int)
    for r in todas:
        por_tema[r["Materia"]] += 1
    min_t, max_t = min(por_tema.values()), max(por_tema.values())
    print(f"Por tema: min={min_t}, max={max_t}")




def puntuar_facilidad(pregunta, a, b, c, d, tipo):
    """Menor score = más fácil (candidata a eliminar)."""
    texto = f"{pregunta} {a} {b} {c} {d}".lower()
    score = 0
    score += len(pregunta) / 50
    terminos = ["integral", "derivada", "teorema", "probabilidad", "matriz",
                "autovalor", "gradiente", "ecuación", "algoritmo", "complejidad",
                "bayes", "hipótesis", "contraste", "entropía", "kernel"]
    for t in terminos:
        if t in texto:
            score += 1
    if tipo == "Calculo":
        score += 2
    return score




def ejecutar_balancear_dificultad_global() -> None:
    temas_ordenados, _ = cargar_orden_temas()
    tema_rank = {t: i for i, t in enumerate(temas_ordenados)}
    fallback_rank = len(tema_rank)

    with open(PATH_PLANTILLAS, "r", encoding="utf-8") as f:
        raw = json.load(f)
    plantillas_dificil = {
        tema: [t for t in items if t.get("uso") == "dificil"]
        for tema, items in raw.items()
    }
    plantillas_facil = {
        tema: [t for t in items if t.get("uso") == "general" and t.get("dificultad") == "Facil"]
        for tema, items in raw.items()
    }
    plantillas_media = {
        tema: [t for t in items if t.get("uso") == "general" and t.get("dificultad") == "Media"]
        for tema, items in raw.items()
    }

    with open(PATH_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f, delimiter=";")
        fieldnames = reader.fieldnames
        rows = list(reader)

    targets = objetivos_dificultad_por_totales(len(rows))

    conteos = defaultdict(int)
    for r in rows:
        conteos[r["Dificultad"]] += 1

    print("Estado actual:")
    for d in ["Facil", "Media", "Dificil"]:
        print(f"  {d}: {conteos[d]}")

    exceso_facil = max(0, conteos["Facil"] - targets["Facil"])
    exceso_media = max(0, conteos["Media"] - targets["Media"])
    exceso_dificil = max(0, conteos["Dificil"] - targets["Dificil"])
    deficit_facil = max(0, targets["Facil"] - conteos["Facil"])
    deficit_media = max(0, targets["Media"] - conteos["Media"])
    deficit_dificil = max(0, targets["Dificil"] - conteos["Dificil"])

    # Candidatos a eliminar por dificultad
    candidatos_facil = [
        (i, puntuar_facilidad(r["Pregunta"], r["A"], r["B"], r["C"], r["D"], r["Tipo"]))
        for i, r in enumerate(rows) if r["Dificultad"] == "Facil"
    ]
    candidatos_media = [
        (i, puntuar_facilidad(r["Pregunta"], r["A"], r["B"], r["C"], r["D"], r["Tipo"]))
        for i, r in enumerate(rows) if r["Dificultad"] == "Media"
    ]
    candidatos_dificil = [
        (i, puntuar_facilidad(r["Pregunta"], r["A"], r["B"], r["C"], r["D"], r["Tipo"]))
        for i, r in enumerate(rows) if r["Dificultad"] == "Dificil"
    ]
    candidatos_facil.sort(key=lambda x: x[1])  # Más fáciles primero
    candidatos_media.sort(key=lambda x: x[1])
    candidatos_dificil.sort(key=lambda x: x[1])  # Dificil más "fáciles" primero (menos score)

    indices_eliminar = set()
    for i in range(exceso_facil):
        indices_eliminar.add(candidatos_facil[i][0])
    for i in range(exceso_media):
        indices_eliminar.add(candidatos_media[i][0])
    for i in range(exceso_dificil):
        indices_eliminar.add(candidatos_dificil[i][0])

    eliminadas_por_tema = defaultdict(int)
    for i in indices_eliminar:
        eliminadas_por_tema[rows[i]["Materia"]] += 1

    filas_filtradas = [r for i, r in enumerate(rows) if i not in indices_eliminar]
    eliminadas = len(rows) - len(filas_filtradas)

    # Crear preguntas nuevas: repartir por dificultad según déficit
    nuevas_filas = []
    max_id = max(int(r["Id"]) for r in filas_filtradas)
    claves_existentes = {(r["Pregunta"], r["A"], r["B"], r["C"], r["D"]) for r in filas_filtradas}

    def añadir_desde_plantillas(dificultad, cantidad, plantillas_por_tema):
        nonlocal max_id, nuevas_filas, claves_existentes
        temas_con_plantillas = [t for t, items in plantillas_por_tema.items() if items]
        if not temas_con_plantillas:
            return 0
        template_idx = defaultdict(int)
        añadidas = 0
        idx_tema = 0
        while añadidas < cantidad:
            tema = temas_con_plantillas[idx_tema % len(temas_con_plantillas)]
            templates = plantillas_por_tema.get(tema, [])
            if not templates:
                idx_tema += 1
                continue
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
                    dificultad=dificultad,
                    tipo=t.get("tipo", "Teoria"),
                    pregunta=pregunta,
                    a=a,
                    b=b,
                    c=c,
                    d=d,
                    correcta=t["correcta"],
                )
            )
            añadidas += 1
            idx_tema += 1
            if idx_tema > len(temas_con_plantillas) * 20:
                break
        return añadidas

    # Añadir según déficit, priorizando temas que perdieron preguntas
    def añadir_priorizando_temas(dificultad, cantidad, plantillas_por_tema):
        nonlocal max_id, nuevas_filas, claves_existentes
        temas_que_perdieron = list(eliminadas_por_tema.keys())
        temas_con_plantillas = {t: items for t, items in plantillas_por_tema.items() if items}
        if not temas_con_plantillas:
            return
        template_idx = defaultdict(int)
        añadidas = 0
        # Primero a temas que perdieron
        for tema in temas_que_perdieron:
            if añadidas >= cantidad:
                break
            templates = temas_con_plantillas.get(tema, [])
            if not templates:
                continue
            n_añadir = min(cantidad - añadidas, eliminadas_por_tema[tema])
            for _ in range(n_añadir):
                t = templates[template_idx[tema] % len(templates)]
                template_idx[tema] += 1
                pregunta, a, b, c, d = t["pregunta"], t["A"], t["B"], t["C"], t["D"]
                clave = (pregunta, a, b, c, d)
                if clave in claves_existentes:
                    pregunta = pregunta.rstrip() + " (variante)"
                claves_existentes.add((pregunta, a, b, c, d))
                max_id += 1
                nuevas_filas.append(
                    fila_pregunta(
                        id_=max_id,
                        materia=tema,
                        dificultad=dificultad,
                        tipo=t.get("tipo", "Teoria"),
                        pregunta=pregunta,
                        a=a,
                        b=b,
                        c=c,
                        d=d,
                        correcta=t["correcta"],
                    )
                )
                añadidas += 1
        # Si faltan, añadir a cualquier tema con plantillas
        if añadidas < cantidad:
            añadir_desde_plantillas(dificultad, cantidad - añadidas, plantillas_por_tema)

    if deficit_facil > 0:
        añadir_priorizando_temas("Facil", deficit_facil, plantillas_facil)
    if deficit_media > 0:
        añadir_priorizando_temas("Media", deficit_media, plantillas_media)
    if deficit_dificil > 0:
        añadir_priorizando_temas("Dificil", deficit_dificil, plantillas_dificil)

    todas = filas_filtradas + nuevas_filas
    todas.sort(key=lambda r: (tema_rank.get(r["Materia"], fallback_rank), int(r["Id"])))

    for i, r in enumerate(todas, start=1):
        r["Id"] = str(i)

    guardar_filas_csv(list(fieldnames or []), todas)

    conteos_final = defaultdict(int)
    for r in todas:
        conteos_final[r["Dificultad"]] += 1

    tipos_elim = []
    if exceso_facil: tipos_elim.append("Facil")
    if exceso_media: tipos_elim.append("Media")
    if exceso_dificil: tipos_elim.append("Dificil")
    print(f"\nEliminadas: {eliminadas} preguntas ({'+'.join(tipos_elim) or 'ninguna'})")
    print(f"Añadidas: {len(nuevas_filas)} preguntas nuevas")
    print("\nResultado final:")
    for d in ["Facil", "Media", "Dificil"]:
        n = conteos_final[d]
        t = targets[d]
        ok = "[OK]" if n == t else f"(obj:{t})"
        print(f"  {d}: {n} {ok}")
    print(f"\nTotal: {len(todas)} preguntas")

    por_tema = defaultdict(int)
    for r in todas:
        por_tema[r["Materia"]] += 1
    min_t, max_t = min(por_tema.values()), max(por_tema.values())
    print(f"Por tema: min={min_t}, max={max_t}")




# -*- coding: utf-8 -*-
"""
Balancea la distribución de respuestas correctas (A/B/C/D) repartiendo lo más igual posible.
Estrategia: permutar el orden de las opciones (sin cambiar el contenido)
para que la respuesta correcta quede en distintas posiciones.
"""

import random

import pandas as pd
from pathlib import Path

from objetivos_balanceo import lista_objetivos_correcta, objetivos_correcta_por_letra
from utils_dataset_csv import COLUMNAS_PREGUNTAS

BASE = Path(__file__).resolve().parent.parent
PATH_CSV = BASE / "Data" / "Preguntas.csv"


def permutar_opciones(row, objetivo):
    """Reordena A,B,C,D para que la respuesta correcta quede en posicion objetivo."""
    opciones = {"A": row["A"], "B": row["B"], "C": row["C"], "D": row["D"]}
    correcta_actual = row["Correcta"]
    valor_correcto = opciones[correcta_actual]

    letras = ["A", "B", "C", "D"]
    otras = [opciones[l] for l in letras if l != correcta_actual]
    random.shuffle(otras)

    nuevo = {}
    idx = 0
    for _, l in enumerate(letras):
        if l == objetivo:
            nuevo[l] = valor_correcto
        else:
            nuevo[l] = otras[idx]
            idx += 1

    return nuevo["A"], nuevo["B"], nuevo["C"], nuevo["D"], objetivo




def ejecutar_balancear_correctas() -> None:
    random.seed(42)

    df = pd.read_csv(PATH_CSV, sep=";", encoding="utf-8")
    n = len(df)
    objetivos_por_letra = objetivos_correcta_por_letra(n)

    conteos = df["Correcta"].value_counts()
    print("Antes:")
    for letra in ["A", "B", "C", "D"]:
        print(f"  {letra}: {conteos.get(letra, 0)}")

    objetivos = lista_objetivos_correcta(n)
    random.shuffle(objetivos)

    nuevas_A, nuevas_B, nuevas_C, nuevas_D, nuevas_Correcta = [], [], [], [], []
    for i, (_, row) in enumerate(df.iterrows()):
        obj = objetivos[i]
        a, b, c, d, corr = permutar_opciones(row, obj)
        nuevas_A.append(a)
        nuevas_B.append(b)
        nuevas_C.append(c)
        nuevas_D.append(d)
        nuevas_Correcta.append(corr)

    df["A"] = nuevas_A
    df["B"] = nuevas_B
    df["C"] = nuevas_C
    df["D"] = nuevas_D
    df["Correcta"] = nuevas_Correcta

    conteos_final = df["Correcta"].value_counts()
    print("\nDespues:")
    for letra in ["A", "B", "C", "D"]:
        n_fin = conteos_final.get(letra, 0)
        obj = objetivos_por_letra[letra]
        ok = "[OK]" if n_fin == obj else f"(obj:{obj})"
        print(f"  {letra}: {n_fin} {ok}")

    df = df[[c for c in COLUMNAS_PREGUNTAS if c in df.columns]]
    df.to_csv(PATH_CSV, sep=";", index=False, encoding="utf-8")
    print(f"\n[OK] Opciones permutadas para balancear respuestas correctas ({n} filas).")



def _plantillas_filtradas(plantillas, tema, *, tipo=None, dificultad=None):
    items = list(plantillas.get(tema, []))
    if tipo:
        items = [t for t in items if t.get("tipo", "Teoria") == tipo]
    if dificultad:
        items = [t for t in items if t.get("dificultad", "Media") == dificultad]
    if not items:
        items = list(plantillas.get(tema, []))
    return {tema: items}


def generar_pregunta_para_slot(tema, claves_existentes, plantillas=None, *, tipo=None, dificultad=None):
    pl = plantillas or cargar_plantillas()
    for filtrado in (
        _plantillas_filtradas(pl, tema, tipo=tipo, dificultad=dificultad),
        _plantillas_filtradas(pl, tema, tipo=tipo, dificultad=None),
        _plantillas_filtradas(pl, tema, tipo=None, dificultad=dificultad),
        {tema: pl.get(tema, [])},
    ):
        if not filtrado.get(tema):
            continue
        generadas = generar_preguntas_desde_plantillas(tema, 1, filtrado, claves_existentes)
        if generadas:
            g = generadas[0]
            if tipo:
                g["Tipo"] = tipo
            if dificultad:
                g["Dificultad"] = dificultad
            return g
    return None


def sustituir_filas_incoherentes(filas, correcciones):
    if not correcciones:
        return filas, 0, set()
    ids_ok_eliminar = set()
    claves = {(r["Pregunta"], r["A"], r["B"], r["C"], r["D"]) for r in filas}
    plantillas = cargar_plantillas()
    nuevas: list = []
    max_id = max((int(r["Id"]) for r in filas), default=0)
    generadas = 0
    for c in correcciones:
        row = next((r for r in filas if r["Id"] == c["id"]), None)
        if not row:
            continue
        tema = c.get("materia") or c.get("de") or row["Materia"]
        campos = c.get("campos") or []
        opt = c.get("optimo") or {}
        inf = c.get("inferido")
        if opt:
            tipo_slot = opt.get("Tipo", row["Tipo"]) if "Tipo" in campos else row["Tipo"]
            diff_slot = (
                opt.get("Dificultad", row["Dificultad"])
                if "Dificultad" in campos
                else row["Dificultad"]
            )
        elif inf is not None:
            tipo_slot = getattr(inf, "tipo", row["Tipo"]) if "Tipo" in campos else row["Tipo"]
            diff_slot = (
                getattr(inf, "dificultad", row["Dificultad"])
                if "Dificultad" in campos
                else row["Dificultad"]
            )
        else:
            cl = clasificar_fila(row)
            tipo_slot = cl.tipo if "Tipo" in campos else row["Tipo"]
            diff_slot = cl.dificultad if "Dificultad" in campos else row["Dificultad"]
        g = generar_pregunta_para_slot(tema, claves, plantillas, tipo=tipo_slot, dificultad=diff_slot)
        if not g:
            print(f"  AVISO: sin plantilla para {tema!r} T={tipo_slot} D={diff_slot} (Id {c['id']}) — se conserva la fila")
            continue
        ids_ok_eliminar.add(c["id"])
        max_id += 1
        claves.add((g["Pregunta"], g["A"], g["B"], g["C"], g["D"]))
        nuevas.append(
            fila_pregunta(
                id_=max_id,
                materia=tema,
                dificultad=g.get("Dificultad", diff_slot),
                tipo=g.get("Tipo", tipo_slot),
                pregunta=g["Pregunta"],
                a=g["A"],
                b=g["B"],
                c=g["C"],
                d=g["D"],
                correcta=g["Correcta"],
            )
        )
        generadas += 1
    filas_ok = [r for r in filas if r["Id"] not in ids_ok_eliminar]
    return filas_ok + nuevas, generadas, ids_ok_eliminar

sustituir_incoherencias_materia = sustituir_filas_incoherentes

PASOS_PIPELINE = [
    ("materias", ejecutar_balancear_materias),
    ("tipo+dificultad por materia", ejecutar_balancear_tipo_dificultad),
    ("tipos globales", ejecutar_balancear_tipos),
    ("dificultad global", ejecutar_balancear_dificultad_global),
    ("correctas ABCD", ejecutar_balancear_correctas),
]


def ejecutar_pipeline_regenerar(pasos=None, *, dry_run: bool = False, sin_dificultad: bool = False) -> int:
    lista = list(pasos or PASOS_PIPELINE)
    if sin_dificultad:
        lista = [(n, f) for n, f in lista if "dificultad" not in n.lower()]
    if dry_run:
        print("Dry-run: pasos de regeneracion:")
        for nombre, _ in lista:
            print(f"  - {nombre}")
        return 0
    print("Pipeline regeneracion (borrar + plantillas):")
    for nombre, fn in lista:
        print(f"\n>>> {nombre}")
        fn()
    return 0
