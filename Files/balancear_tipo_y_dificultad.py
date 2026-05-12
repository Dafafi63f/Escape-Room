# -*- coding: utf-8 -*-
"""
Balancea el dataset para repartir tipo y dificultad dentro de cada materia.
Objetivos derivados de `objetivos_balanceo` (10 preguntas/materia → 5 Teoria y 5 Calculo).
"""

import csv
import json
import re
from collections import defaultdict
from objetivos_balanceo import preguntas_por_materia
from utils_orden_temas import cargar_orden_temas
from utils_dataset_csv import guardar_filas_csv
from borrar_pycache import borrar_pycache_en_proyecto

PATH_PREGUNTAS = "Data/Preguntas.csv"
PATH_PLANTILLAS = "Data/plantillas.json"
TARGET_POR_TEMA = preguntas_por_materia()
TARGET_POR_TIPO = TARGET_POR_TEMA // 2  # mitad Teoria, mitad Calculo por materia


def puntuar_como_calculo(pregunta, a, b, c, d):
    """Mayor score = más parecida a cálculo."""
    texto = f"{pregunta} {a} {b} {c} {d}"
    score = 0
    if re.search(r'\d+', texto):
        score += 2
    if re.search(r'[=+\-*/^∫∑∏√π]', texto):
        score += 2
    if re.search(r'\b(cuánto|cuántos|cuál es|valor|calcular)\b', texto.lower()):
        score += 1
    return score


def cargar_plantillas():
    with open(PATH_PLANTILLAS, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {
        "teoria": {t: [x for x in items if x.get("tipo") == "Teoria"] for t, items in raw.items()},
        "calculo": {t: [x for x in items if x.get("tipo") == "Calculo"] for t, items in raw.items()},
    }


def expandir_plantilla(t):
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
        for n in expandir_plantilla(t):
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


def main():
    temas_ordenados, tema_rank = cargar_orden_temas()
    fallback_rank = len(tema_rank)
    plantillas = cargar_plantillas()

    with open(PATH_PREGUNTAS, "r", encoding="utf-8") as f:
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
            candidatos = [(i, puntuar_como_calculo(rows[i]["Pregunta"], rows[i]["A"], rows[i]["B"], rows[i]["C"], rows[i]["D"]))
                         for i in calculo_idx]
            candidatos.sort(key=lambda x: x[1])  # Menor = más tipo teoría (candidatos a eliminar)
            for j in range(a_eliminar):
                indices_eliminar.add(candidatos[j][0])
            generadas = generar_preguntas(tema, "teoria", a_eliminar, plantillas, claves_existentes)
            for g in generadas:
                max_id += 1
                claves_existentes.add((g["Pregunta"], g["A"], g["B"], g["C"], g["D"]))
                nuevas_filas.append({"Id": str(max_id), "Pregunta": g["Pregunta"], "Materia": tema, "Dificultad": g["Dificultad"],
                                    "Tipo": "Teoria", "A": g["A"], "B": g["B"], "C": g["C"], "D": g["D"], "Correcta": g["Correcta"]})

        # ¿Necesitamos más Calculo? Eliminar Teoria, añadir Calculo
        elif n_c < TARGET_POR_TIPO and n_t > TARGET_POR_TIPO:
            a_eliminar = min(n_t - TARGET_POR_TIPO, TARGET_POR_TIPO - n_c)
            candidatos = [(i, puntuar_como_calculo(rows[i]["Pregunta"], rows[i]["A"], rows[i]["B"], rows[i]["C"], rows[i]["D"]))
                         for i in teoria_idx]
            candidatos.sort(key=lambda x: -x[1])  # Mayor = más tipo cálculo (eliminar estas)
            for j in range(a_eliminar):
                indices_eliminar.add(candidatos[j][0])
            generadas = generar_preguntas(tema, "calculo", a_eliminar, plantillas, claves_existentes)
            for g in generadas:
                max_id += 1
                claves_existentes.add((g["Pregunta"], g["A"], g["B"], g["C"], g["D"]))
                nuevas_filas.append({"Id": str(max_id), "Pregunta": g["Pregunta"], "Materia": tema, "Dificultad": g["Dificultad"],
                                    "Tipo": "Calculo", "A": g["A"], "B": g["B"], "C": g["C"], "D": g["D"], "Correcta": g["Correcta"]})

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


if __name__ == "__main__":
    try:
        main()
    finally:
        borrar_pycache_en_proyecto()
