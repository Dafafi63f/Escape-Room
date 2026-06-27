# Checklist — TFG MATCAD

Checklist **único** de trabajo pendiente e ideas futuras. El historial y el estado del proyecto están en [`CHANGELOG_PROYECTO.md`](CHANGELOG_PROYECTO.md).

**Última actualización:** 2026-06-27

## Cómo mantenerlo

1. **Nueva idea o tarea** → añádela con `- [ ]` en la sección que toque.
2. **Hecha o descartada** → bórrala de aquí; si importa, una línea en el changelog de [`CHANGELOG_PROYECTO.md`](CHANGELOG_PROYECTO.md) §4.
3. **No dupliques** aquí el estado del proyecto ni el feedback del tutor (eso va en `CHANGELOG_PROYECTO.md`).

---

## Memoria y entrega

- [x] Regenerar figuras (`Docs/generar_figuras_memoria.py`) y Word (`Docs/utilidades_tfg.py --solo-memoria`)
- [x] Limpieza de temporales del repo (`Docs/utilidades_tfg.py --solo-limpieza`)
- [x] Merge de la migración «solo pygame» en `main`
- [ ] Editar maquetación en Word y exportar PDF de entrega
- [ ] Releer el PDF final completo antes de entregar
- [ ] Confirmar con el tutor si la estructura actual de la memoria es aceptable antes de pulir redacción

---

## Banco de preguntas y datos

- [x] `plantillas.json` cerrado: **960** filas (480 `dataset_480` + 480 extra reales, 12/materia)
- [x] Metadatos del pool beta equilibrados (materia, tipo, dificultad)
- [x] Pool del juego cerrado: **1000** preguntas reales (480 + 480 JSON + 40 resistencia); sin `variaciones`
- [ ] Revisar **enunciado y distractores** del pool beta jugable (`auditar-distractores`)
- [ ] Campos `Materias_relacionadas` y `Prerequisitos` en el esquema del banco (evolución futura del CSV)

---

## Juego (general)

- [x] Modo escape room jugable (salas, puertas, tienda, botín, inventario, pity)
- [ ] Piloto de usabilidad con estudiantes del grado (SUS, motivación, validez predictiva)
- [x] Retirar consola — migración «solo pygame» integrada en `main`

---

## Modo escape room — ideas futuras

Implementado en 2026-06-26 y **ya no listado aquí:** salas configurables (5–50), tres puertas por sala, escalada de dificultad, cronómetros y niebla, puertas descanso/tienda/botín, pity de especiales, economía en puntos arcade, inventario reutilizando objetos de resistencia, puertas jefe.

### Progresión y metajuego

- [ ] Checkpoints (guardar sala y estado; reanudar partida a medias)
- [ ] Ranking local escape (mejor run: salas superadas, puntos arcade, tiempo total)
- [ ] Mutadores al empezar («sin tienda», «solo dataset», «1 vida», «doble precio en tienda»…)
- [ ] Logros persistentes (primera victoria 30 salas, comprar los 3 artículos en una visita, superar puerta jefe sin objetos…)
- [ ] Sala final / cierre de run (pantalla de resumen al completar el guion)

### Valor pedagógico

- [ ] Filtros de partida por curso, semestre o grupo temático (como en historia/libre)
- [ ] Informe al cerrar: materias y tipos (Teoría/Cálculo) con más fallos en la run
- [ ] Puertas de repaso adaptativo (priorizar materias débiles según histórico de qualificacions)
- [ ] Modo «examen escape»: solo banco revisado, sin objetos ni tienda

### UX y presentación

- [ ] Mapa de progreso visual (salas 1→N con iconos de puertas superadas)
- [ ] Diferenciación gráfica por tipo de puerta (jefe, tienda, descanso, desafío normal)
- [ ] Transiciones entre salas (animación o panel de «siguiente planta»)
- [ ] Feedback más claro del pity (cuándo toca descanso/tienda/botín garantizado)

### Contenido y mecánicas

- [ ] Más artículos exclusivos de tienda (no reexportados de resistencia)
- [ ] Eventos de sala completos (afectan las tres puertas a la vez: niebla global, bonus puntos…)
- [ ] Puertas encadenadas o excluyentes (elegir una ruta cierra otras en la misma sala)
- [ ] Bonificación por racha de puertas limpias (multiplicador arcade o botín extra)
- [ ] Variantes de tamaño de puerta según fase (más bloques de 10 en salas finales)

---

## Modo resistencia — ideas futuras

Implementado en 2026-06-18 y **ya no listado aquí:** hitos de racha, apuestas, maldiciones, bloques temáticos, objeto Cambio, eventos sobre la pregunta actual, barra de estado gráfica con chips emoji.

### Progresión y metajuego

- [ ] Checkpoints cada 25 preguntas (guardar progreso y reanudar)
- [ ] Jefes de materia (bloques 3–5 preguntas de una asignatura con multiplicador alto)
- [ ] Mutadores al empezar («solo Cálculo», «sin objetos ×1,5 puntos», etc.)
- [ ] Logros locales persistentes (medallas: exclusiva Legendario, 50 preguntas sin objetos…)
- [ ] Ranking filtrado (p. ej. por mutador o curso)
- [ ] Duelo hot-seat (dos jugadores alternando en la misma pantalla)

### Valor pedagógico

- [ ] Resistencia adaptativa (ponderar materias según histórico `Historic_qualificacions_MatCAD_completo.csv`)
- [ ] Informe por materia al final de partida (desglose Teoría/Cálculo y grupos)
- [ ] Rotación curricular obligatoria (penalizar misma materia dos veces seguidas)

### UX y presentación

- [ ] Mapa de escalada (barra visual umbrales 10 → 25 → 50 → … → 700)
- [ ] Cooldown de objetos (limitar 50/50 o bomba cada X preguntas)
- [ ] Intensidad visual (fondo o música según nivel)

### Economía y eventos sí/no

- [x] **Eventos sí/no** (mismo popup ✅/❌): el título indica «Apuesta» (riesgo al responder) u «Oferta» (gasto en pts); No → no pasa nada; Sí deshabilitado sin puntos suficientes
- [x] Pity suave si llevas varias preguntas sin evento sí/no
- [x] Exclusión mutua: un solo evento sí/no por turno

### Contenido

- [ ] Sets rotativos de exclusivas («Semana de Probabilidad», «Maratón de Programación»)
- [ ] Más tiers de exclusivas (más allá de Élite → Imposible)

---

## Descartado por diseño (no implementar)

- **Reto del día escape o resistencia** — semilla fija diaria comparable entre jugadores; solo el **Examen del día** (`examen_fijo`) usa semilla diaria.
- **Avisos sobre preguntas futuras** — solo efectos sobre la pregunta actual o bloques en curso.
- **Eventos que cambian la selección del pool** — los eventos modifican la pregunta ya elegida; la segmentación va en bloques temáticos.
