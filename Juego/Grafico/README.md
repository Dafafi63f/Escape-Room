# Grafico — interfaz pygame del cuestionario MATCAD

Versión gráfica del juego. Reutiliza [`Comun/`](../Comun/README.md) (datos, reglas, motor) y añade la capa pygame en este directorio.

| Elemento | Descripción |
|----------|-------------|
| [`juego_grafico.py`](../juego_grafico.py) | Lanzador pygame |
| [`app.py`](app.py) | Bucle principal y enrutador de pantallas |
| [`pantallas.py`](pantallas.py) | Menú, configuración, partida, resumen |
| [`ui.py`](ui.py) | Botones, campos de texto y widgets (ratón) |
| [`modo_libre.py`](modo_libre.py) | Utilidades del modo libre gráfico |
| [`tema.py`](tema.py) | Colores, fuentes y constantes de ventana |

## Estrategia de migración

| Fase | Qué ocurre |
|------|------------|
| **Actual** | Terminal y gráfico **coexisten**. La terminal es la referencia funcional completa; el gráfico se amplía hasta igualarla. |
| **Futura** | Cuando el gráfico sea **estable y completo**, se borra todo lo específico de terminal y solo queda `juego_grafico.py` + `Grafico/`. |

**Se conservará** (motor de dominio): modelos, datos, reglas, motor de partida — en [`Comun/`](../Comun/README.md). Informes y generador de historia siguen en `Consola/` de momento.

**Se eliminará** (solo UI terminal): `juego_consola.py`, `consola.py`, `entrada_teclas.py`, `entrada_menu.py`, `navegacion.py` (contexto consola), `build_exe_onefile.ps1` orientado a consola, documentación de atajos de teclado, etc.

Mientras dure la coexistencia, **no romper la terminal** al tocar código compartido.

## Principio de controles

| Entrada | Uso |
|---------|-----|
| **Ratón** | Navegación, menús, elegir opciones A–D, confirmar, volver, pausa, ayuda, feedback |
| **Teclado** | Solo donde haga falta **escribir texto** (nombre del jugador, mensajes de feedback, etc.) |

La consola usa teclas (H, F, Esc, Supr, dígitos…). En gráfico esas acciones se traducen a **clics en botones, tarjetas o iconos** visibles en pantalla. No se replican atajos de teclado salvo en campos de texto.

## Ejecutar

```bash
pip install -r requirements.txt
python Juego/juego_grafico.py
```

(La terminal sigue en `python Juego/juego_consola.py` hasta la migración.)

## Estado

| Modo | Gráfico |
|------|---------|
| **Libre** | v1 — bloque 5/10/15 preguntas, arcade con vidas, opciones clicables |
| **Historia** | Pendiente |
| **Feedback** | Pendiente |

Diferencias respecto a consola en modo libre v1:

- Configuración reducida (nombre + tamaño del bloque; sin filtros ni menús de reglas).
- Respuestas A–D como botones en pantalla (no teclas).
- Feedback visual inmediato (colores en opciones + mensaje).
- Barra de progreso y botón «Abandonar» siempre visible.
