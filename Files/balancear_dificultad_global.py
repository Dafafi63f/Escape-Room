# -*- coding: utf-8 -*-
"""
Balancea las dificultades a nivel global (reparto ~1/3 Facil, Media, Dificil del total actual).
Elimina excesos y genera desde plantillas para acercarse a los objetivos.
El total de filas no cambia (pensado para dataset de 400 preguntas).
"""

import csv
import json
from collections import defaultdict
from objetivos_balanceo import objetivos_dificultad_por_totales
from utils_orden_temas import cargar_orden_temas
from utils_dataset_csv import fila_pregunta, guardar_filas_csv
from borrar_pycache import borrar_pycache_en_proyecto

PATH_PREGUNTAS = "Data/Preguntas.csv"
PATH_PLANTILLAS = "Data/plantillas.json"
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


def main():
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

    with open(PATH_PREGUNTAS, "r", encoding="utf-8") as f:
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


if __name__ == "__main__":
    try:
        main()
    finally:
        borrar_pycache_en_proyecto()
