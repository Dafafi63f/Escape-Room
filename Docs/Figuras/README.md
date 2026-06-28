# Figuras de la memoria

Imágenes usadas en [`Memoria_TFG.md`](../Entrega/Memoria_TFG.md) y [`Memoria_TFG.tex`](../Entrega/Memoria_TFG.tex) (`Docs/Entrega/`).

Regenerar (desde la raíz del proyecto):

```bash
python Docs/generar_figuras_memoria.py
```

Capturas pygame (menú + escape room; también incluidas en el script anterior):

```bash
python Docs/capturar_pantallas_juego.py
```

Las capturas del juego incluyen la **barra fija superior** (pausa, diarios, ranking, feedback, opciones), igual que al ejecutar `juego_grafico.py`.

## Numeración global en la memoria

**9 figuras numeradas (1–9)** = **9 PNG** en esta carpeta (mismo conjunto en informes y regeneración).

| N.º | Fichero | Sección |
|-----|---------|---------|
| 1 | `inkagames_gameplay_referencia.png` | §1.3 Inka Games |
| 2 | `tfg_escape_referencia.png` | §1.3 Escape room (composición) |
| 3 | `tfg_menu_principal.png` | Metodología |
| 4–5 | `monte_carlo_*.png` | §5.7 Monte Carlo |
| 6 | `tfg_escape_tienda.png` | §5.8 Pity — tienda en juego |
| 7–9 | `pity_*.png` | §5.8 Pity — curva y simulación |

La **figura 1** (`inkagames_gameplay_referencia.png`) es un asset canónico: fotograma del walkthrough de Inka Games (~13:30). El script de figuras **no** la regenera; solo comprueba que exista. Sustitúyela a mano si necesitas actualizarla.

Capturas obsoletas (`tfg_menu_modos_especiales.png`, `tfg_escape_puertas.png`, `tfg_escape_pregunta_inventario.png`) ya no se generan: su contenido está en las figuras 2 y 3.

## Qué **no** es PNG (tablas en la memoria)

Arquitectura del sistema, pipeline del modo historia y comparación Inka Games ↔ TFG están como **tablas** en `Memoria_TFG.md` / `.tex`, no como figuras generadas.

Las simulaciones Monte Carlo y pity usan semilla 42 con `RngPartida` (mismo criterio que el juego). Requisitos: `matplotlib`, `Pillow` (capturas pygame) y `pygame` (`pip install -r requirements.txt` y `pip install -r Juego/requirements.txt`).
