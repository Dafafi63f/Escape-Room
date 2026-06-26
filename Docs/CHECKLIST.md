# Checklist — TFG MATCAD

Checklist **único** de trabajo pendiente e ideas futuras. El historial y el estado del proyecto están en [`CHANGELOG_PROYECTO.md`](CHANGELOG_PROYECTO.md).

**Última actualización:** 2026-06-26

## Cómo mantenerlo

1. **Nueva idea o tarea** → añádela con `- [ ]` en la sección que toque.
2. **Hecha o descartada** → bórrala de aquí; si importa, una línea en el changelog de [`CHANGELOG_PROYECTO.md`](CHANGELOG_PROYECTO.md) §4.
3. **No dupliques** aquí el estado del proyecto ni el feedback del tutor (eso va en `CHANGELOG_PROYECTO.md`).

---

## Memoria y entrega

- [x] Regenerar figuras (`Docs/generar_figuras_memoria.py`) y Word (`utilidades_tfg.py --solo-memoria`)
- [x] Limpieza de temporales del repo (`utilidades_tfg.py --solo-limpieza`)
- [x] Merge de la migración «solo pygame» en `main`
- [ ] Editar maquetación en Word y exportar PDF de entrega
- [ ] Releer el PDF final completo antes de entregar
- [ ] Confirmar con el tutor si la estructura actual de la memoria es aceptable antes de pulir redacción

---

## Banco de preguntas y datos

- [ ] Revisar plantillas de `plantillas.json` que no están en el dataset de producción (pool beta; opcional)
- [ ] Campos `Materias_relacionadas` y `Prerequisitos` en el esquema del banco (evolución futura del CSV)

---

## Juego (general)

- [x] Modo escape room jugable (salas, puertas, tienda, botín, inventario, pity)
- [ ] Narrativa gráfica escape room completa (guion, arte de escenas; OE1)
- [ ] Piloto de usabilidad con estudiantes del grado (SUS, motivación, validez predictiva)
- [x] Retirar consola — migración «solo pygame» integrada en `main`

---

## Modo resistencia — ideas futuras

Implementado en 2026-06-18 y **ya no listado aquí:** reto del día, hitos de racha, apuestas, maldiciones, bloques temáticos, objeto Cambio, eventos sobre la pregunta actual, barra de estado gráfica con chips emoji.

### Progresión y metajuego

- [ ] Checkpoints cada 25 preguntas (guardar progreso y reanudar)
- [ ] Jefes de materia (bloques 3–5 preguntas de una asignatura con multiplicador alto)
- [ ] Mutadores al empezar («solo Cálculo», «sin objetos ×1,5 puntos», etc.)
- [ ] Logros locales persistentes (medallas: exclusiva Legendario, 50 preguntas sin objetos…)
- [ ] Ranking filtrado (solo reto del día vs resistencia libre; o por mutador/curso)
- [ ] Duelo hot-seat (dos jugadores alternando en la misma pantalla)

### Valor pedagógico

- [ ] Resistencia adaptativa (ponderar materias según histórico `Historic_qualificacions_MatCAD_completo.csv`)
- [ ] Informe por materia al final de partida (desglose Teoría/Cálculo y grupos)
- [ ] Rotación curricular obligatoria (penalizar misma materia dos veces seguidas)

### UX y presentación

- [ ] Mapa de escalada (barra visual umbrales 10 → 25 → 50 → … → 700)
- [ ] Cooldown de objetos (limitar 50/50 o bomba cada X preguntas)
- [ ] Intensidad visual (fondo o música según nivel)

### Contenido

- [ ] Sets rotativos de exclusivas («Semana de Probabilidad», «Maratón de Programación»)
- [ ] Más tiers de exclusivas (más allá de Élite → Imposible)

---

## Descartado por diseño (no implementar)

- **Avisos sobre preguntas futuras** — solo efectos sobre la pregunta actual o bloques en curso.
- **Eventos que cambian la selección del pool** — los eventos modifican la pregunta ya elegida; la segmentación va en bloques temáticos.
