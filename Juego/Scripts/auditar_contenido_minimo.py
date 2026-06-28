#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auditoría de módulos Comun/ y Grafico/ para el zip mínimo.

Uso (desde la raíz del repo):
  python Juego/Scripts/auditar_contenido_minimo.py
"""

from __future__ import annotations

import ast
import sys
from collections import defaultdict
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
_JUEGO = _RAIZ / "Juego"
if str(_JUEGO) not in sys.path:
    sys.path.insert(0, str(_JUEGO))

from Comun.contenido import MODULOS_EXCLUIDOS_MINIMO, RAICES_FLUJO_MINIMO  # noqa: E402

_CARPETAS = ("Comun", "Grafico")


def _modname(path: Path) -> str:
    return ".".join(path.relative_to(_JUEGO).with_suffix("").parts)


def _listar_modulos() -> dict[str, Path]:
    mods: dict[str, Path] = {}
    for sub in _CARPETAS:
        for p in (_JUEGO / sub).rglob("*.py"):
            if p.name == "__init__.py":
                continue
            mods[_modname(p)] = p
    return mods


def _resolver(target: str, mods: dict[str, Path]) -> str | None:
    if target in mods:
        return target
    parts = target.split(".")
    for i in range(len(parts), 0, -1):
        cand = ".".join(parts[:i])
        if cand in mods:
            return cand
    return None


def _grafo_imports(mods: dict[str, Path]) -> dict[str, set[str]]:
    g: dict[str, set[str]] = defaultdict(set)
    for mod, path in mods.items():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            targets: list[str] = []
            if isinstance(node, ast.Import):
                targets = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                targets = [node.module]
            for target in targets:
                resolved = _resolver(target, mods)
                if resolved and resolved != mod:
                    g[mod].add(resolved)
    return g


def _cierre(raices: set[str], grafo: dict[str, set[str]]) -> set[str]:
    visto = set(raices)
    cola = list(raices)
    while cola:
        mod = cola.pop()
        for dep in grafo.get(mod, ()):
            if dep not in visto:
                visto.add(dep)
                cola.append(dep)
    return visto


def auditar() -> tuple[set[str], set[str], set[str]]:
    mods = _listar_modulos()
    grafo = _grafo_imports(mods)
    excluidos = {_modname(_JUEGO / rel) for rel in MODULOS_EXCLUIDOS_MINIMO}
    faltan = excluidos - set(mods)
    if faltan:
        raise ValueError(f"Exclusiones inexistentes: {sorted(faltan)}")

    raices = set(RAICES_FLUJO_MINIMO)
    desconocidas = raices - set(mods)
    if desconocidas:
        raise ValueError(f"Raíces de flujo desconocidas: {sorted(desconocidas)}")

    necesarios = _cierre(raices, grafo) - excluidos
    todos = set(mods) - excluidos
    opcionales = todos - necesarios
    return necesarios, opcionales, excluidos


def main() -> int:
    mods = _listar_modulos()
    necesarios, opcionales, excluidos = auditar()

    print(f"Módulos Comun/ + Grafico/: {len(mods)}")
    print(f"  Excluidos del zip mínimo: {len(excluidos)}")
    print(f"  Necesarios (flujo mínimo): {len(necesarios)}")
    print(f"  Resto en zip (compartidos / arranque): {len(opcionales)}")

    if opcionales:
        print("\n--- Incluidos en zip pero fuera del cierre del flujo mínimo ---")
        print("(compartidos con paquete completo o solo metadata de build)\n")
        for mod in sorted(opcionales):
            rel = mod.replace(".", "/") + ".py"
            sz = mods[mod].stat().st_size
            print(f"  {sz:6d}  {rel}")

    print("\n--- Excluidos ---")
    for rel in sorted(MODULOS_EXCLUIDOS_MINIMO):
        p = _JUEGO / rel
        sz = p.stat().st_size if p.is_file() else 0
        print(f"  {sz:6d}  {rel}")

    ahorro = sum(mods[_modname(_JUEGO / rel)].stat().st_size for rel in MODULOS_EXCLUIDOS_MINIMO)
    print(f"\nAhorro aprox. por exclusiones: {ahorro / 1024:.1f} KiB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
