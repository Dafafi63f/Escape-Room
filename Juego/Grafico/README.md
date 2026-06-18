# Grafico — interfaz pygame del cuestionario MATCAD

Versión gráfica del juego. Reutiliza [`Comun/`](../Comun/README.md) (datos, reglas, motor) y añade la capa pygame en este directorio.

| Elemento | Descripción |
|----------|-------------|
| [`juego_grafico.py`](../juego_grafico.py) | Lanzador pygame |
| [`app.py`](app.py) | Bucle principal, pausa global, iconos fijos (pausa, feedback, opciones) |
| [`pantallas.py`](pantallas.py) | Menú principal, partida libre, resumen, placeholder feedback |
| [`pantallas_libre.py`](pantallas_libre.py) | Wizard modo libre (paso 1: reglas; paso 2: filtros) |
| [`pantallas_historia.py`](pantallas_historia.py) | Historia (carrusel de presets), opciones, partida y ranking |
| [`pantallas_especiales.py`](pantallas_especiales.py) | Modos especiales (menú por botones) |
| [`modo_libre.py`](modo_libre.py) | Utilidades del modo libre gráfico |
| [`modo_historia.py`](modo_historia.py) | Arranque de presets historia/resistencia |
| [`ui.py`](ui.py) | Botones, campos de texto, tooltips, texto multilínea |
| [`tooltips_ui.py`](tooltips_ui.py) | Textos de ayuda al pasar el ratón |
| [`texto.py`](texto.py) | Renderizado mixto (texto, matemáticas, emojis) |
| [`textos_grafico.py`](textos_grafico.py) | Atajos de etiquetas sin emoji decorativo |
| [`tema.py`](tema.py) | Colores, tamaño de ventana (960×720) |
| [`fuentes.py`](fuentes.py) | Fuentes por familia (texto, símbolos, emoji) |
| [`barra_estado.py`](barra_estado.py) | Barra superior en partida (chips emoji: pregunta, racha, vidas, tiempos, puntos) |
| [`menu_opciones.py`](menu_opciones.py) | Panel superpuesto de opciones globales |
| [`feedback_partida.py`](feedback_partida.py) | Panel de feedback tras cada respuesta |
| [`aviso_resistencia.py`](aviso_resistencia.py) | Popups de eventos y recompensas (resistencia) |
| [`informe_partida.py`](informe_partida.py) | Resumen breve y guardado de informes `.txt` |

## Estrategia de migración

| Fase | Qué ocurre |
|------|------------|
| **Actual** | Terminal y gráfico **coexisten**. La consola sigue siendo referencia completa; el gráfico amplía paridad (libre, historia, resistencia). |
| **Futura** | Cuando el gráfico sea **estable y completo**, se elimina la UI terminal y solo queda `juego_grafico.py` + `Grafico/`. |

**Se conservará:** dominio en [`Comun/`](../Comun/README.md) (modelos, reglas, motor, pool, resistencia, ranking).

**Se eliminará:** `juego_consola.py`, menús por teclado, `build_exe_onefile.ps1` orientado a consola, etc.

Mientras dure la coexistencia, **no romper la terminal** al tocar código compartido.

## Principio de controles

| Entrada | Uso |
|---------|-----|
| **Ratón** | Navegación, menús, opciones A–D, confirmar, volver, pausa, ayuda, feedback |
| **Teclado** | Solo donde haga falta **escribir texto** (nombre del jugador, mensajes de feedback, etc.) |

La consola usa teclas (H, F, Esc, Supr, dígitos…). En gráfico esas acciones se traducen a **clics en botones, tarjetas o iconos** visibles en pantalla.

## Ejecutar

```bash
pip install -r requirements.txt
python Juego/juego_grafico.py
```

(La terminal sigue en `python Juego/juego_consola.py` hasta la migración.)

## Estado por modo

| Modo | Gráfico | Notas |
|------|---------|-------|
| **Libre** | Implementado | Wizard en dos pasos: banco, preguntas/infinito, vidas, tiempo, sistema, dificultad progresiva; filtros por temática/semestre/tipo |
| **Historia** | Implementado (v1) | Carrusel de presets (`presets_historia.json`); exámenes balanceados |
| **Resistencia** | Implementado (v1) | Partida infinita, eventos, objetos (50/50, bomba, escudo…), ranking local |
| **Feedback** | Placeholder | Pantalla informativa; envío completo sigue en consola (icono 📣 en barra fija) |

## Tooltips (ayuda al pasar el ratón)

Textos en [`tooltips_ui.py`](tooltips_ui.py). Implementados en:

- Iconos fijos de pausa, feedback y opciones
- Menú de pausa (3 botones)
- Menú principal (4 opciones)
- Navegación Atrás / Siguiente / Empezar / Continuar (libre e historia)
- Modo libre: valor central de selectores ◀ valor ▶, dificultad progresiva, filtros paso 2
- Modo historia: valor central de selectores en configuración de preset
- Abandonar (libre, historia, resistencia)
- Guardar informe y ver ranking (resumen resistencia)
- Objetos del inventario en partida resistencia

## Diferencias respecto a consola

- Interfaz visual con barra de estado, progreso y feedback por colores.
- Configuración libre con ratón (sin menús numéricos).
- Resistencia con popups visuales y emojis centralizados en [`Comun/iconos_resistencia.py`](../Comun/iconos_resistencia.py).
- Títulos largos del resumen se parten en varias líneas (`dibujar_texto_centro` con `ancho_max`).
