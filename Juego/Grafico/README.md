# Grafico — interfaz pygame del cuestionario MATCAD

Versión gráfica del juego. Reutiliza [`Comun/`](../Comun/README.md) (datos, reglas, motor) y añade la capa pygame en este directorio.

| Elemento | Descripción |
|----------|-------------|
| [`juego_grafico.py`](../juego_grafico.py) | Lanzador pygame |
| [`app.py`](app.py) | Bucle principal, pausa global, barra fija (pausa · diarios · info · feedback · opciones) |
| [`pantallas.py`](pantallas.py) | Núcleo: clase `Pantalla`, menú principal, partida libre, resumen |
| [`pantallas_inicio.py`](pantallas_inicio.py) | Bienvenida y nombre del jugador |
| [`pantallas_libre.py`](pantallas_libre.py) | Wizard modo libre (paso 1: reglas; paso 2: filtros) y helpers de etiquetas |
| [`pantallas_historia.py`](pantallas_historia.py) | Carrusel modo historia (solo paquete completo) |
| [`pantallas_examen_fijo.py`](pantallas_examen_fijo.py) | Examen fijo: opciones, partida y resumen |
| [`pantallas_resistencia_partida.py`](pantallas_resistencia_partida.py) | Partida y resumen del modo resistencia |
| [`pantallas_modos.py`](pantallas_modos.py) | Modos diarios, modos especiales y escape room |
| [`pantallas_sistema.py`](pantallas_sistema.py) | Info del juego (ℹ️), estadísticas y formulario de feedback (📣) |
| [`modo_historia.py`](modo_historia.py) | Catálogo y preparación de exámenes del carrusel historia |
| [`arranque_partida.py`](arranque_partida.py) | Arranque por preset y navegación al fin de partida |
| [`ui.py`](ui.py) | Botones, campos de texto, tooltips, texto multilínea |
| [`tooltips_ui.py`](tooltips_ui.py) | Textos de ayuda al pasar el ratón |
| [`texto.py`](texto.py) | Renderizado mixto (texto, matemáticas, emojis) |
| [`textos_grafico.py`](textos_grafico.py) | Atajos de etiquetas sin emoji decorativo |
| [`tema.py`](tema.py) | Colores, tamaño de ventana (960×720) |
| [`fuentes.py`](fuentes.py) | Fuentes por familia (texto, símbolos, emoji) |
| [`barra_estado.py`](barra_estado.py) | Barra superior en partida (chips emoji) |
| [`menu_opciones.py`](menu_opciones.py) | Panel superpuesto de opciones globales |
| [`feedback_partida.py`](feedback_partida.py) | Panel de feedback tras cada respuesta |
| [`aviso_resistencia.py`](aviso_resistencia.py) | Popups de eventos y recompensas (resistencia) |
| [`informe_partida.py`](informe_partida.py) | Resumen breve y guardado de informes `.txt` en `Data/Juego/` |

## Convención `pantallas_<área>.py`

Todos los módulos de pantalla usan el prefijo **`pantallas_`** más un área (`inicio`, `libre`, `historia`, `modos`, `sistema`). El plural no indica cuántas clases hay dentro; indica el **rol** del módulo. El núcleo compartido sigue en [`pantallas.py`](pantallas.py).

## Estado

La interfaz gráfica es la única interfaz de juego: dominio en [`Comun/`](../Comun/README.md), UI en `Grafico/` y lanzador [`juego_grafico.py`](../juego_grafico.py) (**v1.1.0**).

## Principio de controles

| Entrada | Uso |
|---------|-----|
| **Ratón** | Navegación, menús, opciones A–D, confirmar, volver, pausa, ayuda, feedback, info |
| **Teclado** | Solo donde haga falta **escribir texto** (mensaje de feedback, contacto opcional, etc.) |

El nombre del jugador se configura en **Opciones** (icono ⚙️), no en el formulario de feedback.

## Ejecutar

```bash
pip install -r Juego/requirements.txt
python Juego/juego_grafico.py
```

## Estado por modo

| Modo | Gráfico | Notas |
|------|---------|-------|
| **Libre** | Implementado | Wizard dos pasos; filtros; tooltips |
| **Historia** | Implementado | Carrusel de 5 presets (`Juego/presets.json`) |
| **Resistencia** | Implementado | Eventos, objetos, récords en estadísticas; `RngPartida` por sesión |
| **Escape room** | Implementado | 30 salas, tienda, botín, inventario; `RngPartida` por sesión |
| **Feedback** | Implementado | Icono 📣 en barra; envío SMTP si hay config en `Data/Privado/creador_privado.json` |
| **Info** | Implementado | Icono ℹ️: estadísticas, contacto del creador, changelog del juego |

## Barra superior fija (fuera de partida y en pausa)

| Icono | Función |
|-------|---------|
| ⏸ | Pausa global |
| 📅 | Modos diarios |
| ℹ️ | Info del juego (estadísticas, contacto, novedades) |
| 📣 | Enviar aviso al creador |
| ⚙️ | Opciones (nombre, tooltips, emojis) |

## Tooltips

Textos en [`tooltips_ui.py`](tooltips_ui.py). Cobertura: iconos de barra, menús, wizard libre/historia, inventario resistencia y escape, etc.

## Pruebas

[`Tests/test_grafico_menus.py`](../../Tests/test_grafico_menus.py), [`Tests/test_grafico_ui.py`](../../Tests/test_grafico_ui.py), [`Tests/test_escape_room.py`](../../Tests/test_escape_room.py), dominio en [`Tests/test_dominio_juego.py`](../../Tests/test_dominio_juego.py).
