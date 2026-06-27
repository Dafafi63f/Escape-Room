# Novedades del juego

Cambios **visibles o relevantes para quien juega** en la interfaz gráfica pygame. El historial técnico del TFG está en [`CHANGELOG_PROYECTO.md`](CHANGELOG_PROYECTO.md).

**Última actualización:** 2026-06-27

---

## 2026-06-27 (escape room y economía)

- **Escape room:** cada partida es distinta (semilla aleatoria).
- **Tienda:** si no tienes puntos para lo más barato, la puerta tienda no aparece y el pity se pospone; hard pity no fuerza tienda inviable.
- **Cartas de puerta:** icono 🎁 arriba; en la descripción, emoji del premio concreto (💣, 🔮, ❤️…).
- **Código:** catálogo y economía unificados (`objetos_partida`, `economia_partida`); eliminados alias legacy de semillas y tienda.

## 2026-06-26 (modo escape room)

- **Escape room** jugable desde Modos especiales: 30 salas, 3 puertas por sala; eliges desafío y avanzas (fallar cuesta 1 vida).
- **Puertas especiales:** descanso (sin preguntas), **tienda** (compra con puntos arcade) y **botín** (vidas u objetos al superar la puerta).
- **Tienda:** hasta 3 artículos por visita; puedes comprar varios distintos (máx. 1 de cada); cartas compradas se marcan en gris.
- **Inventario** en la banda inferior (como en resistencia): bomba, 50/50, tiempo extra, escudo, salto, cambio, refuerzo vital, amuleto arcade.
- **Botín de objetos** en puertas normales y en descanso; icono 🎁 con el detalle del premio en la descripción.
- **Pity** suave y garantías: descanso (sala 5), tienda (sala 10), botín (cada 3 salas sin ver uno).

## 2026-06-19 (migración solo pygame)

- Eliminada la versión en terminal; **único lanzador:** `python Juego/juego_grafico.py`.
- Informes, feedback y generador de historia viven en `Juego/Comun/`.
- Suite de tests reorientada al backend gráfico (**424** tests: 416 en `Tests/` + 8 en `Files/`).

## 2026-06-19 (interfaz gráfica)

- **Modo feedback** integrado: formulario (tipo de aviso, zona, mensaje, contacto opcional); copia en `Data/Juego/` y envío por correo si hay SMTP configurado.
- **Info del juego** (icono ℹ️ en la barra): ranking local, contacto del creador en pantalla y **novedades del juego** (este fichero).
- **Barra superior fija:** pausa, retos del día, info, avisos (feedback) y opciones.
- Nombre del jugador tomado de **Opciones** (ya no hay campo nombre en feedback).
- Popup de **apuesta** en resistencia: botones ✅ / ❌.
- Power-up **Saltar** con icono 🦘.
- Ajustes de maquetación en pantallas feedback e info.

## 2026-06-18

- **Resistencia:** apuestas (doble o nada), maldiciones, bloques temáticos temporales, power-ups (bomba, escudo, 50/50, saltar…).
- **Barra de partida:** tiempo, número de pregunta, racha y estado de resistencia más claros (chips con emoji).
- Rankings locales de resistencia y examen del día.

## 2026-06-17

- **Modo historia** y **resistencia** en pygame.
- **Modo libre** gráfico: asistente en dos pasos (opciones y filtros).
- Tooltips configurables y emojis opcionales en menús.
- Reorganización de datos del jugador bajo `Data/Juego/`.

## 2026-06-16

- Primera versión de la **interfaz gráfica** (`juego_grafico.py`): menú principal y modo libre.
- Misma lógica de partida que el prototipo terminal gracias al paquete compartido `Comun/`.

## 2026-06-05

- **Modo feedback** (menú o atajo durante partida): avisos al creador con copia local.
- Controles de teclado ampliados en el prototipo terminal (retirado en junio 2026).

## 2026-06-03

- **Banco cerrado** con **480 preguntas** revisadas.
- Tres capas de preguntas en partida: revisadas → plantillas → exclusivas (modo resistencia).
- Catálogo de **presets historia** y modos **especiales**.

## 2026-05-12 — Inicio del juego (prototipo terminal)

- **Modo libre:** partida personalizable (filtros, vidas, tiempo, puntuación).
- **Modo historia:** simulacros de examen con datos históricos MatCAD.
- **Modo resistencia** (evolución posterior): partida continua con escalada de dificultad.
- Informes de partida en `.txt` al cerrar sesión.
- Banco inicial de preguntas y materias del grado MATCAD.

---

Al añadir algo que el jugador note, documenta aquí (fecha + viñeta breve). Cambios solo de desarrollo del TFG → `CHANGELOG_PROYECTO.md` §4.
