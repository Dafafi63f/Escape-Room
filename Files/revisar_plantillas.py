# -*- coding: utf-8 -*-
"""
Revisa que haya plantillas suficientes y no duplicadas para cada tema.
Genera un informe detallado.
"""

import json
from collections import defaultdict
from objetivos_balanceo import plantillas_minimas_por_materia, preguntas_por_materia
from utils_orden_temas import cargar_orden_temas
from borrar_pycache import borrar_pycache_en_proyecto

PATH_PLANTILLAS = "Data/plantillas.json"
TARGET_POR_TEMA = plantillas_minimas_por_materia()
PREGUNTAS_DATASET_POR_TEMA = preguntas_por_materia()


def expandir_variaciones(template):
    """Cuántas preguntas únicas puede generar una plantilla."""
    variaciones = template.get("variaciones")
    if variaciones:
        return len(variaciones)
    return 1


def main():
    with open(PATH_PLANTILLAS, "r", encoding="utf-8") as f:
        plantillas = json.load(f)

    materias, _ = cargar_orden_temas()

    # Temas en plantillas vs materias
    temas_plantillas = set(plantillas.keys())
    temas_materias = set(materias)

    faltan_materias = temas_materias - temas_plantillas
    sobrantes = temas_plantillas - temas_materias

    print("=" * 70)
    print("INFORME DE PLANTILLAS")
    print("=" * 70)

    # 1. Cobertura de temas
    print("\n1. COBERTURA DE TEMAS (40 materias)")
    if faltan_materias:
        print(f"   [FALTA] Temas sin plantillas: {faltan_materias}")
    else:
        print("   [OK] Todas las materias tienen plantillas")
    if sobrantes:
        print(f"   [INFO] Temas en plantillas no en listado: {sobrantes}")

    # 2. Por tema: conteo y capacidad generable
    print("\n2. PLANTILLAS POR TEMA (capacidad para generar preguntas únicas)")
    print("-" * 70)

    total_general = 0
    total_dificil = 0
    total_calculo = 0
    duplicados_por_tema = defaultdict(int)
    temas_cortos = []
    temas_sin_general = []
    temas_sin_dificil = []
    temas_sin_calculo = []

    temas_en_orden = [t for t in materias if t in plantillas] + [
        t for t in plantillas.keys() if t not in set(materias)
    ]
    for tema in temas_en_orden:
        items = plantillas[tema]
        por_uso = defaultdict(list)
        claves_vistas = set()
        duplicados = 0
        generables = 0

        for t in items:
            uso = t.get("uso", "general")
            por_uso[uso].append(t)
            # Contar generables (con variaciones)
            generables += expandir_variaciones(t)
            # Detectar duplicados (misma pregunta + opciones)
            clave = (t["pregunta"], t["A"], t["B"], t["C"], t["D"])
            if clave in claves_vistas:
                duplicados += 1
            claves_vistas.add(clave)

        n_general = len(por_uso["general"])
        n_dificil = len(por_uso["dificil"])
        n_calculo = len(por_uso["calculo"])
        n_unicos = len(claves_vistas)

        total_general += n_general
        total_dificil += n_dificil
        total_calculo += n_calculo

        if duplicados > 0:
            duplicados_por_tema[tema] = duplicados
        if generables < TARGET_POR_TEMA and tema in temas_materias:
            temas_cortos.append((tema, generables))
        if n_general == 0 and tema in temas_materias:
            temas_sin_general.append(tema)
        if n_dificil == 0 and tema in temas_materias:
            temas_sin_dificil.append(tema)
        if n_calculo == 0 and tema in temas_materias:
            temas_sin_calculo.append(tema)

        n_items = len(items)
        ratio_ds = n_items / PREGUNTAS_DATASET_POR_TEMA if tema in temas_materias else 0
        estado = "OK" if generables >= TARGET_POR_TEMA else f"BAJO ({generables})"
        dup_str = f" [DUP:{duplicados}]" if duplicados else ""
        ratio_str = f" | plant:{n_items:2} ({ratio_ds:.1f}×ds)" if tema in temas_materias else ""
        print(f"   {tema[:50]:<50} | gen:{n_general:2} dif:{n_dificil:2} calc:{n_calculo:2} | "
              f"generables:~{generables:3} {estado}{ratio_str}{dup_str}")

    # 3. Resumen
    print("\n3. RESUMEN")
    print("-" * 70)
    print(f"   Total plantillas: {sum(len(v) for v in plantillas.values())}")
    print(f"   Uso general: {total_general} | dificil: {total_dificil} | calculo: {total_calculo}")

    if duplicados_por_tema:
        print(f"\n   [DUPLICADOS] {sum(duplicados_por_tema.values())} plantillas duplicadas en {len(duplicados_por_tema)} temas")
        for t, n in sorted(duplicados_por_tema.items(), key=lambda x: -x[1])[:5]:
            print(f"      - {t}: {n}")

    if temas_cortos:
        print(f"\n   [CAPACIDAD BAJA] Temas con <{TARGET_POR_TEMA} preguntas generables:")
        for tema, n in sorted(temas_cortos, key=lambda x: x[1]):
            print(f"      - {tema}: ~{n}")

    if temas_sin_general:
        print(f"\n   [SIN GENERAL] {len(temas_sin_general)} temas usan solo dificil/calculo para balanceo temas")

    if temas_sin_dificil:
        print(f"\n   [SIN DIFICIL] {len(temas_sin_dificil)} temas no pueden añadir preguntas Difíciles")

    if temas_sin_calculo:
        print(f"\n   [SIN CALCULO] {len(temas_sin_calculo)} temas no pueden añadir preguntas Cálculo")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        main()
    finally:
        borrar_pycache_en_proyecto()
