#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Genera las figuras de la memoria TFG en Docs/Figuras/.

Solo gráficos con datos (Monte Carlo, pity), la captura de gameplay Inka Games y capturas pygame del escape room.
Arquitectura, pipeline historia y comparaciones tabulares viven en Memoria_TFG.md/.tex.

Uso (desde la raíz del proyecto):
  python Docs/generar_figuras_memoria.py
  python Docs/generar_figuras_memoria.py --forzar   # reconstruir aunque no haya cambios

También lo invoca ``Docs/utilidades_tfg.py`` con la misma lógica incremental.
"""

from __future__ import annotations

import math
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
from Comun.semillas import RngPartida, semilla_estable_texto  # noqa: E402

try:
    import matplotlib.pyplot as plt
except ImportError as exc:
    raise SystemExit(
        "Falta matplotlib. Instálalo con: pip install matplotlib"
    ) from exc

DPI = 160
SEMILLA = 42
N_ITER = 50_000
N_PREGUNTAS = 20

FIGURAS_SALIDA = (
    # 9 PNG insertados en Memoria_TFG (figuras 1–9). Ver Docs/Figuras/README.md.
    "monte_carlo_histograma_notas.png",
    "monte_carlo_convergencia.png",
    "pity_curva_probabilidad.png",
    "pity_comparacion_descanso.png",
    "pity_distribucion_primer_descanso.png",
    "inkagames_gameplay_referencia.png",
    "tfg_menu_principal.png",
    "tfg_escape_referencia.png",
    "tfg_escape_tienda.png",
)
FIGURAS_MEMORIA = len(FIGURAS_SALIDA)  # 9 PNG en Docs/Figuras/ e informes


def _mtime(ruta: Path) -> float:
    try:
        return ruta.stat().st_mtime
    except OSError:
        return 0.0


def entradas_generacion_figuras() -> list[Path]:
    """Ficheros que invalidan las figuras si cambian tras la última generación."""
    entradas: list[Path] = [
        Path(__file__).resolve(),
        DOCS / "capturar_pantallas_juego.py",
        _SCRIPTS / "simulacion_evaluacion_azar.py",
        _SCRIPTS / "simulacion_pity.py",
        _JUEGO / "Comun" / "semillas.py",
        _JUEGO / "Comun" / "datos.py",
        _JUEGO / "Comun" / "reglas_partida.py",
        _JUEGO / "Comun" / "eventos_partida.py",
        _JUEGO / "Comun" / "escape_room.py",
        _JUEGO / "Grafico" / "app.py",
        _JUEGO / "Grafico" / "pantallas_modos.py",
        _JUEGO / "Grafico" / "pantallas.py",
    ]
    for resolver in (resolver_dataset, resolver_listado_materias):
        try:
            ruta = resolver()
        except Exception:
            continue
        if ruta.is_file():
            entradas.append(ruta)
    return [p for p in entradas if p.is_file()]


def rutas_figuras_salida() -> list[Path]:
    return [FIGURAS / nombre for nombre in FIGURAS_SALIDA]


def figuras_necesitan_regeneracion() -> tuple[bool, str]:
    salidas = rutas_figuras_salida()
    faltan = [p.name for p in salidas if not p.is_file()]
    if faltan:
        return True, f"faltan {', '.join(faltan)}"
    mas_reciente_salida = max(_mtime(p) for p in salidas)
    for ruta in entradas_generacion_figuras():
        if _mtime(ruta) > mas_reciente_salida + 1e-6:
            try:
                motivo = str(ruta.relative_to(ROOT))
            except ValueError:
                motivo = str(ruta)
            return True, f"cambió {motivo}"
    return False, ""


def _rng_figura(etiqueta: str) -> RngPartida:
    """Stream reproducible alineado con ``RngPartida`` del juego."""
    return RngPartida.desde_semilla(semilla_estable_texto(f"memoria-{etiqueta}-{SEMILLA}"))


def _generar_figuras(preguntas) -> list[Path]:
    return [
        fig_monte_carlo_histograma(preguntas, _rng_figura("mc-hist")),
        fig_monte_carlo_convergencia(preguntas, _rng_figura("mc-conv")),
        fig_pity_curva_probabilidad(),
        fig_pity_comparacion_modelo(),
        fig_pity_distribucion_primer_descanso(),
        fig_inkagames_gameplay_referencia(),
        *_generar_capturas_pygame(),
    ]


def _generar_capturas_pygame() -> list[Path]:
    from capturar_pantallas_juego import generar_capturas_escape

    if str(DOCS) not in sys.path:
        sys.path.insert(0, str(DOCS))
    return generar_capturas_escape()


def generar_todas_figuras(*, force: bool = False, imprimir_stats: bool = True) -> tuple[int, list[Path]]:
    """Genera PNG en ``Docs/Figuras/`` si hace falta. Devuelve (código, rutas)."""
    motivo = ""
    if not force:
        necesita, motivo = figuras_necesitan_regeneracion()
        if not necesita:
            return 0, [p for p in rutas_figuras_salida() if p.is_file()]

    path_csv = resolver_dataset()
    path_materias = resolver_listado_materias()
    materias_meta = cargar_materias(path_materias)
    preguntas = cargar_preguntas(path_csv, materias_meta)
    if not preguntas:
        print("Error: banco vacío.", file=sys.stderr)
        return 1, []

    rutas = _generar_figuras(preguntas)

    if imprimir_stats:
        stats = ejecutar_simulacion(
            preguntas,
            iteraciones=N_ITER,
            n_preguntas=N_PREGUNTAS,
            semilla=SEMILLA,
        )
        print("=== FIGURAS GENERADAS ===")
        if force:
            print("  Modo: reconstrucción forzada")
        elif motivo:
            print(f"  Motivo: {motivo}")
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
    return 0, rutas


def _guardar(fig: plt.Figure, nombre: str) -> Path:
    FIGURAS.mkdir(parents=True, exist_ok=True)
    ruta = FIGURAS / nombre
    fig.savefig(ruta, dpi=DPI, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return ruta


def _binom_pmf(n: int, p: float, k: int) -> float:
    return math.comb(n, k) * (p**k) * ((1 - p) ** (n - k))


def fig_monte_carlo_histograma(preguntas, rng: RngPartida) -> Path:
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


def fig_monte_carlo_convergencia(preguntas, rng: RngPartida) -> Path:
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


def fig_pity_comparacion_modelo() -> Path:
    n = 10_000
    n_salas = 30
    rng_base = _rng_figura("pity-base")
    rng_pity = _rng_figura("pity-model")
    base = [
        simular_modelo_simplificado(
            rng_base,
            n_salas=n_salas,
            prob_base=PARAMS_DESCANSO["prob_base"],
            incremento=0.0,
            prob_max=PARAMS_DESCANSO["prob_base"],
            hard_umbral_sin=None,
            hard_sala=None,
        )
        for _ in range(n)
    ]
    pity = [
        simular_modelo_simplificado(
            rng_pity,
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


def fig_pity_distribucion_primer_descanso() -> Path:
    n = 10_000
    rng = _rng_figura("pity-dist")
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


INKAGAMES_GAMEPLAY_PNG = FIGURAS / "inkagames_gameplay_referencia.png"


def fig_inkagames_gameplay_referencia() -> Path:
    """Figura 1: PNG canónico (fotograma Inka Games; no se regenera desde JPG)."""
    if not INKAGAMES_GAMEPLAY_PNG.is_file():
        raise FileNotFoundError(
            f"Falta {INKAGAMES_GAMEPLAY_PNG.name} en Docs/Figuras/. "
            "Es la figura 1 de la memoria; sustitúyela manualmente si hace falta "
            "(walkthrough Kim Dotcom Prison Break, ~13:30)."
        )
    return INKAGAMES_GAMEPLAY_PNG


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Genera figuras PNG de la memoria TFG.")
    parser.add_argument(
        "--forzar",
        action="store_true",
        help="Reconstruir todas las figuras aunque no haya cambios en entradas",
    )
    args = parser.parse_args(argv)

    if not args.forzar:
        necesita, motivo = figuras_necesitan_regeneracion()
        if not necesita:
            print("=== FIGURAS DE MEMORIA ===")
            print(f"  Sin cambios relevantes; se reutilizan {len(FIGURAS_SALIDA)} PNG en Docs/Figuras/")
            print("  (usa --forzar para reconstruir desde cero)")
            return 0

    codigo, _ = generar_todas_figuras(force=args.forzar, imprimir_stats=True)
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
