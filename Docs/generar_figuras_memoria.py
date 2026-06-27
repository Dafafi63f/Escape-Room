#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera las figuras de la memoria TFG en Docs/Figuras/.

Uso (desde la raíz del proyecto):
  python Docs/generar_figuras_memoria.py
"""

from __future__ import annotations

import math
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DOCS = Path(__file__).resolve().parent
FIGURAS = DOCS / "Figuras"
_SCRIPTS = ROOT / "Files"
_JUEGO = ROOT / "Juego"

for p in (_SCRIPTS, _JUEGO):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from simulacion_evaluacion_azar import (  # noqa: E402
    _PROB_ACIERTO_TEORICA,
    ejecutar_simulacion,
    simular_examen,
)
from simulacion_pity import (  # noqa: E402
    PARAMS_DESCANSO,
    PARAMS_TIENDA,
    ejecutar_simulacion as ejecutar_simulacion_pity,
    prob_soft,
    simular_modelo_simplificado,
)
from Comun.datos import cargar_materias, cargar_preguntas  # noqa: E402
from Comun.rutas import resolver_dataset, resolver_listado_materias  # noqa: E402

try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
except ImportError as exc:
    raise SystemExit(
        "Falta matplotlib. Instálalo con: pip install matplotlib"
    ) from exc

DPI = 160
SEMILLA = 42
N_ITER = 50_000
N_PREGUNTAS = 20


def _guardar(fig: plt.Figure, nombre: str) -> Path:
    FIGURAS.mkdir(parents=True, exist_ok=True)
    ruta = FIGURAS / nombre
    fig.savefig(ruta, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ruta


def _binom_pmf(n: int, p: float, k: int) -> float:
    return math.comb(n, k) * (p**k) * ((1 - p) ** (n - k))


def fig_arquitectura_sistema() -> Path:
    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")

    capas = [
        (4.8, 5.0, "Lanzador", "juego_grafico.py"),
        (4.8, 3.85, "Modos de juego", "libre · historia · resistencia · feedback"),
        (4.8, 2.7, "Motor de partida", "Comun/ — reglas · vidas · puntuación"),
        (4.8, 1.55, "Capa de datos", "Preguntas.csv · listado_materias.csv · plantillas.json"),
        (4.8, 0.35, "Mantenimiento", "validación · auditoría · Monte Carlo"),
    ]
    colores = ["#2c5282", "#2b6cb0", "#3182ce", "#4299e1", "#63b3ed"]

    for (cx, cy, titulo, detalle), color in zip(capas, colores):
        box = FancyBboxPatch(
            (cx - 3.6, cy - 0.42),
            7.2,
            0.84,
            boxstyle="round,pad=0.03,rounding_size=0.08",
            linewidth=1.2,
            edgecolor="#1a365d",
            facecolor=color,
            alpha=0.92,
        )
        ax.add_patch(box)
        ax.text(cx, cy + 0.12, titulo, ha="center", va="center", color="white", fontsize=11, fontweight="bold")
        ax.text(cx, cy - 0.18, detalle, ha="center", va="center", color="#ebf8ff", fontsize=8.5)

    for y0, y1 in [(4.58, 4.27), (3.43, 3.12), (2.28, 1.97), (1.13, 0.82)]:
        ax.add_patch(
            FancyArrowPatch(
                (4.8, y0),
                (4.8, y1),
                arrowstyle="-|>",
                mutation_scale=14,
                linewidth=1.4,
                color="#2d3748",
            )
        )

    ax.set_title("Arquitectura en capas del cuestionario MATCAD", fontsize=13, fontweight="bold", pad=12)
    return _guardar(fig, "arquitectura_sistema.png")


def fig_flujo_modo_historia() -> Path:
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 4)
    ax.axis("off")

    pasos = [
        (1.0, 2.0, "Histórico\nde qualificacions\n(8818 registros)"),
        (3.2, 2.0, "Agregación\npor materia\n(media, % susp.)"),
        (5.4, 2.0, "Índice de\ndificultad\ny pesos"),
        (7.6, 2.0, "Selección de\nmaterias y slots\nT/C × F/M/D"),
        (9.2, 2.0, "Examen\nbalanceado"),
    ]

    for i, (x, y, texto) in enumerate(pasos):
        w, h = 1.55, 1.35
        color = "#edf2f7" if i % 2 == 0 else "#e6fffa"
        edge = "#2c5282"
        ax.add_patch(
            FancyBboxPatch(
                (x - w / 2, y - h / 2),
                w,
                h,
                boxstyle="round,pad=0.02,rounding_size=0.06",
                linewidth=1.2,
                edgecolor=edge,
                facecolor=color,
            )
        )
        ax.text(x, y, texto, ha="center", va="center", fontsize=8.3, color="#1a202c")
        if i < len(pasos) - 1:
            x_sig = pasos[i + 1][0]
            ax.add_patch(
                FancyArrowPatch(
                    (x + w / 2 + 0.05, y),
                    (x_sig - w / 2 - 0.05, y),
                    arrowstyle="-|>",
                    mutation_scale=12,
                    linewidth=1.2,
                    color="#4a5568",
                )
            )

    ax.text(
        5.0,
        3.45,
        "Flujo del modo historia (generador_examen_historia.py)",
        ha="center",
        fontsize=12,
        fontweight="bold",
    )
    ax.text(
        5.0,
        0.55,
        "Perfil refuerzo: mayor peso a materias con índice de dificultad alto en el histórico agregado",
        ha="center",
        fontsize=8.5,
        color="#4a5568",
        style="italic",
    )
    return _guardar(fig, "flujo_modo_historia.png")


def fig_monte_carlo_histograma(preguntas, rng: random.Random) -> Path:
    notas = [simular_examen(preguntas, N_PREGUNTAS, rng).nota for _ in range(N_ITER)]
    aciertos_vals = [round(n * N_PREGUNTAS / 10) for n in notas]

    teorica_x = list(range(N_PREGUNTAS + 1))
    teorica_y = [_binom_pmf(N_PREGUNTAS, _PROB_ACIERTO_TEORICA, k) for k in teorica_x]
    teorica_notas = [10 * k / N_PREGUNTAS for k in teorica_x]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10.5, 4.2))

    ax1.hist(
        notas,
        bins=[0.25 * i for i in range(41)],
        density=True,
        color="#4299e1",
        alpha=0.75,
        edgecolor="white",
        label="Simulación (50 000 réplicas)",
    )
    ax1.plot(
        teorica_notas,
        teorica_y,
        "o-",
        color="#c53030",
        linewidth=1.5,
        markersize=4,
        label=r"Binomial teórica ($p=1/4$)",
    )
    ax1.set_xlabel("Nota sobre 10")
    ax1.set_ylabel("Densidad")
    ax1.set_title("Distribución de la nota (modo examen)")
    ax1.legend(fontsize=8)
    ax1.grid(axis="y", alpha=0.3)

    ax2.hist(
        aciertos_vals,
        bins=range(N_PREGUNTAS + 2),
        density=True,
        align="left",
        color="#48bb78",
        alpha=0.75,
        edgecolor="white",
        label="Simulación",
    )
    ax2.plot(
        teorica_x,
        teorica_y,
        "o-",
        color="#c53030",
        linewidth=1.5,
        markersize=4,
        label=r"$\mathrm{Bin}(20,\,1/4)$",
    )
    ax2.set_xlabel("Número de aciertos")
    ax2.set_ylabel("Probabilidad")
    ax2.set_title("Distribución del número de aciertos")
    ax2.legend(fontsize=8)
    ax2.grid(axis="y", alpha=0.3)

    fig.suptitle("Simulación Monte Carlo — respuestas al azar (A–D uniforme)", fontsize=12, fontweight="bold")
    fig.tight_layout()
    return _guardar(fig, "monte_carlo_histograma_notas.png")


def fig_monte_carlo_convergencia(preguntas, rng: random.Random) -> Path:
    muestras = 5000
    fracs = []
    acum = 0
    for i in range(1, muestras + 1):
        r = simular_examen(preguntas, N_PREGUNTAS, rng)
        acum += r.aciertos / r.respondidas
        fracs.append(acum / i)

    p = _PROB_ACIERTO_TEORICA
    banda = [
        1.96 * math.sqrt(p * (1 - p) / (N_PREGUNTAS * i)) for i in range(1, muestras + 1)
    ]

    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    xs = list(range(1, muestras + 1))
    ax.plot(xs, fracs, color="#2b6cb0", linewidth=1.2, label=r"$\hat{p}_N$ (media acumulada)")
    ax.axhline(_PROB_ACIERTO_TEORICA, color="#c53030", linestyle="--", linewidth=1.5, label=r"$p = 1/4$ teórico")
    ax.fill_between(
        xs,
        [_PROB_ACIERTO_TEORICA - b for b in banda],
        [_PROB_ACIERTO_TEORICA + b for b in banda],
        color="#fed7d7",
        alpha=0.5,
        label="Banda aprox. ±1,96 SE",
    )
    ax.set_xlabel("Número de réplicas Monte Carlo")
    ax.set_ylabel("Fracción media de aciertos")
    ax.set_title("Convergencia del estimador Monte Carlo")
    ax.set_xlim(1, muestras)
    ax.set_ylim(0.22, 0.28)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    return _guardar(fig, "monte_carlo_convergencia.png")


def fig_pity_curva_probabilidad() -> Path:
    xs = list(range(0, 11))
    descanso = [
        prob_soft(
            s,
            prob_base=PARAMS_DESCANSO["prob_base"],
            incremento=PARAMS_DESCANSO["incremento"],
            prob_max=PARAMS_DESCANSO["prob_max"],
        )
        for s in xs
    ]
    tienda = [
        prob_soft(
            s,
            prob_base=PARAMS_TIENDA["prob_base"],
            incremento=PARAMS_TIENDA["incremento"],
            prob_max=PARAMS_TIENDA["prob_max"],
        )
        for s in xs
    ]

    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    ax.plot(xs, descanso, "o-", color="#2b6cb0", linewidth=1.8, label="Descanso")
    ax.plot(xs, tienda, "s-", color="#c05621", linewidth=1.8, label="Tienda")
    ax.axhline(PARAMS_DESCANSO["prob_base"], color="#2b6cb0", linestyle=":", alpha=0.5)
    ax.axhline(PARAMS_TIENDA["prob_base"], color="#c05621", linestyle=":", alpha=0.5)
    ax.set_xlabel("Salas consecutivas sin ver el evento ($s$)")
    ax.set_ylabel(r"Probabilidad por sala $p_s$")
    ax.set_title("Pity suave en escape room: $p_s = \\min(p_{\\max},\\, p_0 + s\\delta)$")
    ax.set_xticks(xs)
    ax.set_ylim(0, 0.52)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    return _guardar(fig, "pity_curva_probabilidad.png")


def fig_pity_comparacion_modelo(rng: random.Random) -> Path:
    n = 10_000
    n_salas = 30
    base = [
        simular_modelo_simplificado(
            rng,
            n_salas=n_salas,
            prob_base=PARAMS_DESCANSO["prob_base"],
            incremento=0.0,
            prob_max=PARAMS_DESCANSO["prob_base"],
            hard_umbral_sin=None,
            hard_sala=None,
        )
        for _ in range(n)
    ]
    rng2 = random.Random(SEMILLA + 99)
    pity = [
        simular_modelo_simplificado(
            rng2,
            n_salas=n_salas,
            prob_base=PARAMS_DESCANSO["prob_base"],
            incremento=PARAMS_DESCANSO["incremento"],
            prob_max=PARAMS_DESCANSO["prob_max"],
            hard_umbral_sin=PARAMS_DESCANSO["hard_umbral_sin"],
            hard_sala=PARAMS_DESCANSO["hard_sala"],
        )
        for _ in range(n)
    ]
    frac_sin_base = sum(1 for r in base if r.primera_sala is None) / n
    frac_sin_pity = sum(1 for r in pity if r.primera_sala is None) / n
    p95_base = sorted(r.max_racha_sin for r in base)[int(0.95 * (n - 1))]
    p95_pity = sorted(r.max_racha_sin for r in pity)[int(0.95 * (n - 1))]

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    etiquetas = ["Sin descanso\n(30 salas)", "Racha p95\nsin descanso"]
    x = [0, 1]
    w = 0.35
    ax.bar(
        [i - w / 2 for i in x],
        [frac_sin_base * 100, p95_base],
        width=w,
        color="#a0aec0",
        label="Prob. base fija (6 %)",
    )
    ax.bar(
        [i + w / 2 for i in x],
        [frac_sin_pity * 100, p95_pity],
        width=w,
        color="#2b6cb0",
        label="Pity suave + hard (sala 5)",
    )
    ax.set_xticks(x)
    ax.set_xticklabels(etiquetas)
    ax.set_ylabel("Porcentaje / nº salas")
    ax.set_title("Modelo simplificado — puerta descanso (10 000 réplicas)")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    return _guardar(fig, "pity_comparacion_descanso.png")


def fig_pity_distribucion_primer_descanso(rng: random.Random) -> Path:
    n = 10_000
    salas = [
        simular_modelo_simplificado(
            rng,
            n_salas=30,
            prob_base=PARAMS_DESCANSO["prob_base"],
            incremento=PARAMS_DESCANSO["incremento"],
            prob_max=PARAMS_DESCANSO["prob_max"],
            hard_umbral_sin=PARAMS_DESCANSO["hard_umbral_sin"],
            hard_sala=PARAMS_DESCANSO["hard_sala"],
        ).primera_sala
        for _ in range(n)
    ]
    salas_ok = [s for s in salas if s is not None]

    fig, ax = plt.subplots(figsize=(8.2, 4.2))
    ax.hist(
        salas_ok,
        bins=range(1, 8),
        align="left",
        color="#4299e1",
        edgecolor="white",
        density=True,
        label="Simulación",
    )
    ax.axvline(PARAMS_DESCANSO["hard_sala"], color="#c53030", linestyle="--", linewidth=1.5, label="Hard pity (sala 5)")
    ax.set_xlabel("Sala del primer descanso")
    ax.set_ylabel("Densidad")
    ax.set_title("Distribución del primer descanso con pity (modelo simplificado)")
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=0.3)
    return _guardar(fig, "pity_distribucion_primer_descanso.png")


def main() -> int:
    path_csv = resolver_dataset()
    path_materias = resolver_listado_materias()
    materias_meta = cargar_materias(path_materias)
    preguntas = cargar_preguntas(path_csv, materias_meta)
    if not preguntas:
        print("Error: banco vacío.", file=sys.stderr)
        return 1

    rng = random.Random(SEMILLA)
    rutas = [
        fig_arquitectura_sistema(),
        fig_flujo_modo_historia(),
        fig_monte_carlo_histograma(preguntas, rng),
        fig_monte_carlo_convergencia(preguntas, random.Random(SEMILLA)),
        fig_pity_curva_probabilidad(),
        fig_pity_comparacion_modelo(random.Random(SEMILLA + 7)),
        fig_pity_distribucion_primer_descanso(random.Random(SEMILLA + 11)),
    ]

    stats = ejecutar_simulacion(
        preguntas,
        iteraciones=N_ITER,
        n_preguntas=N_PREGUNTAS,
        semilla=SEMILLA,
    )
    print("=== FIGURAS GENERADAS ===")
    for r in rutas:
        print(f"  {r.relative_to(ROOT)}")
    print()
    print(f"Verificación numérica (semilla {SEMILLA}):")
    print(f"  Nota media examen: {stats['examen_nota_media']}/10")
    print(f"  Aciertos medios: {stats['examen_aciertos_frac_media']:.4f}")
    print(f"  Arcade agotan vidas: {stats['arcade_frac_agotado_vidas']:.1%}")
    stats_pity = ejecutar_simulacion_pity(
        iteraciones=N_ITER,
        iteraciones_escape=0,
        n_salas=30,
        semilla=SEMILLA,
    )
    print()
    print("Verificación pity (modelo descanso, semilla 42):")
    pity = stats_pity["modelo_pity_descanso"]
    base = stats_pity["modelo_base_descanso"]
    print(f"  Sin pity — partidas sin descanso: {base['frac_sin_evento']:.1%}")
    print(f"  Con pity — partidas sin descanso: {pity['frac_sin_evento']:.1%}")
    print(f"  Con pity — sala media 1.er descanso: {pity['sala_media_primer_evento']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
