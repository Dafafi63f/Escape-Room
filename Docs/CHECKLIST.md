# Checklist — MATCAD (proyecto personal)

Checklist de **hecho** (`[x]`) y **pendiente / futuro** (`[ ]`). El historial detallado está en [`CHANGELOG_PROYECTO.md`](CHANGELOG_PROYECTO.md).

**Última actualización:** 2026-08-08

## Versión entregable 1.0.0 (TFG cerrado)

- [x] **Juego v1.0.0** jugable de extremo a extremo (ver [`RELEASE_1.0.md`](RELEASE_1.0.md))
- [x] Continuación personal: **v1.1.0** (juego educativo independiente; ver `Juego/Comun/version.py`)
- [x] Etiqueta de versión en menú e Info del juego
- [x] Banco por defecto: 480 revisadas; ampliado opcional y etiquetado
- [x] 615 tests + `Files/health_check.py`
- [x] Arranque del juego con `python Juego/juego_grafico.py`
- [x] PDF memoria y presentación de defensa (entrega TFG; fuera de este repo)

*A partir de aquí: ideas futuras; no son requisito para jugar la v1.0.*

## Cómo mantenerlo

1. **Nueva idea** → `- [ ]` en la sección que toque.
2. **Completada** → pasa a `[x]` (no la borres; así se ve el progreso acumulado).
3. **Descartada** → muévela a §VIII o bórrala; una línea en [`CHANGELOG_PROYECTO.md`](CHANGELOG_PROYECTO.md) §4 si importa.
4. **No dupliques** aquí el feedback del tutor ni el estado narrativo del proyecto (eso va en el changelog).

### Resumen rápido

| Área | Hecho | Pendiente |
|------|-------|-----------|
| TFG / memoria | Memoria, PDF, presentación defensa | Piloto usuarios (opcional) |
| Banco y datos | 480 + plantillas + pool 1000 | Revisar banco ampliado, Moodle, prerrequisitos |
| Juego (5 modos) | Libre, historia, resistencia, escape, feedback | Mapas/UI visual, muchas ideas UX |
| Estadísticas locales | v1 (panel simplificado + JSON) | Gráficos, repaso, botones acción |
| Ingeniería | 615 tests, CI, zip jugable | Docker |

---

## Hecho — núcleo del entregable

*(Lo que ya forma parte del TFG funcional; referencia rápida antes de las listas por bloque.)*

### Documentación y pipeline

- [x] Memoria Markdown / LaTeX / Word (entrega TFG; fuera de este repo)
- [x] **9 figuras** de memoria + capturas pygame (fuera de este repo)
- [x] README raíz, `Data/`, `Juego/`, `Files/`, `Tests/`, `Docs/`
- [x] Changelogs proyecto y jugador (`CHANGELOG_PROYECTO.md`, `CHANGELOG_JUEGO.md`)
- [x] Esquemas JSON locales del jugador (`persistencia.py`)
- [x] Arranque documentado con Python (`juego_grafico.py`)

### Banco y mantenimiento

- [x] **480** preguntas revisadas en `Preguntas.csv` (balance, metadatos curriculares)
- [x] **960** plantillas JSON (480 dataset + 480 extras); pool jugable **1000** ítems
- [x] `mantenimiento.py validar` / `auditar-distractores` / deduplicación (`duplicados.py`)
- [x] Histórico qualificaciones MatCAD integrado (modo historia, §5.6 memoria) — **retirado del juego post-TFG (2026-08-07):** ponderación solo con stats locales
- [x] Simulación Monte Carlo (azar) y pity (escape/resistencia) — **scripts retirados del repo** post-TFG (figuras/memoria fuera de git)

### Juego pygame — modos y sistemas

- [x] Lanzador único `juego_grafico.py` (migración «solo pygame»)
- [x] **Modo libre:** filtros curso/semestre/materia, banco revisado/ampliado, informe `.txt` al cerrar
- [x] **Modo historia:** carrusel presets, examen balanceado por práctica local (histórico MatCAD retirado post-TFG)
- [x] **Modo resistencia:** racha, apuestas, maldiciones, bloques temáticos, objetos, eventos sí/no + pity
- [x] **Modo escape room:** salas 5–50, 3 puertas, tienda/botín/descanso/jefe, inventario, pity, economía arcade
- [x] **Modo feedback:** formulario en pantalla + copia local + SMTP opcional
- [x] **Modos diarios / examen del día** (semilla fija diaria)
- [x] Barra superior: pausa, diarios, info (ℹ️), feedback (📣), opciones
- [x] Opciones: nombre jugador, tooltips, emojis, guardar informes `.txt`, restablecer preferencias/estadísticas, limpiar `.txt`
- [x] Informes `.txt` por partida en `Data/Juego/` (independientes por sesión)
- [x] **Estadísticas locales v1** (`estadisticas_jugador.json`, pantalla «Mis estadísticas»)
- [x] Esquemas JSON documentados (`persistencia.py`)

### Ingeniería

- [x] **615** tests unitarios (`Tests/`)
- [x] CI GitHub Actions: pre-commit, tests, integración, mypy, SonarCloud (opcional)
- [x] `pre-commit`, `mypy.ini`, `.python-version` (3.14 en CI)
- [x] Zip jugable vía Releases (`Docs/utilidades.py` → raíz del repo; CI `paquete-jugable.yml`)

---

## I. TFG — entrega y documentación

### Memoria

- [x] Regenerar figuras y Word (entrega TFG; fuera de este repo)
- [x] Limpieza de temporales del repo (`python Docs/utilidades.py --solo-limpieza`)
- [x] Merge migración «solo pygame» en `main`
- [x] Marco teórico, hipótesis H1–H3, cumplimiento objetivos en memoria (feedback tutor)
- [x] Editar maquetación en Word y exportar **PDF de entrega**
- [x] Releer el PDF final completo antes de entregar
- [x] Confirmar con el tutor estructura de memoria antes de pulir redacción
- [ ] Apéndice glosario términos MatCAD
- [ ] Diagrama de arquitectura (Comun / Grafico / Files / Data)
- [ ] Tabla comparativa Kahoot / Quizlet / Moodle vs MATCAD

### Defensa y difusión

- [x] Presentación de defensa (entrega TFG; fuera de este repo)
- [ ] Vídeo demo (~3 min): menú → libre → escape → informe
- [ ] Manual del profesor (1 pág.) en `Docs/`
- [ ] Badge «reproducible» en README (DOI Zenodo opcional)

### Piloto académico

- [ ] Piloto usabilidad con estudiantes (SUS, motivación, validez predictiva)
- [ ] Diseño pre/post: SUS + IMI + tiempo de práctica
- [ ] Grupo control: PDF estático vs gamificado
- [ ] Métricas automáticas: preguntas/partida, abandono, materias falladas
- [ ] Entrevista breve (n≈5)
- [ ] Informe piloto como apéndice o §6 ampliada
- [ ] Anonimización de logs (opt-in)

---

## II. Contenido y datos

### Banco de producción (480 ítems)

- [x] Pool cerrado y revisado manualmente
- [x] Validación estructural y auditoría distractores (scripts)
- [x] Deduplicación: 0 pares similares en producción (2026-06-15)
- [ ] Campos `Materias_relacionadas` y `Prerequisitos` en el CSV

### Pool ampliado (plantillas + resistencia)

- [x] `plantillas.json`: 960 filas equilibradas
- [x] Pool juego: 1000 preguntas reales; sin `variaciones`
- [x] 40 exclusivas resistencia embebidas en `preguntas_resistencia_exclusivas_datos.py`
- [x] Revisar enunciado y distractores del **banco ampliado** (`auditar-distractores`) — 2026-06-29: 98 incidencias en 960 instancias (sin opciones_duplicadas; corregidas CDV#16 y ProgSist#19)
- [ ] Conmutador global «solo banco producción» (ocultar banco ampliado en todos los modos)

### Integración y mantenimiento

- [x] Modo feedback con copia local de reportes
- [x] Plantilla `creador_privado.json` para SMTP/GitHub
- [ ] Panel agregado de feedback para profesorado (CSV/HTML)
- [ ] Etiquetas en reportes (typo, enunciado, distractor…)
- [ ] Exportación Moodle (GIFT/QTI)

---

## III. Juego — experiencia común

### Completado

- [x] Cinco modos jugables (libre, historia, resistencia, escape, feedback)
- [x] Pantalla bienvenida + nombre en opciones (salta bienvenida si ya hay nombre)
- [x] Menú pausa con volver a menú / continuar
- [x] Tooltips configurables (on/off)
- [x] Emojis configurables (on/off)
- [x] Changelog del juego visible en Info (ℹ️)

### Onboarding y accesibilidad

- [ ] Tutorial interactivo primera vez
- [ ] Tamaño de fuente y alto contraste
- [ ] Indicadores daltonismo en A–D
- [x] Atajos de teclado en partida (1–4, Esc, Enter, Supr, H, F)

### Informes y compartición

- [x] Informe `.txt` detallado al cerrar partida (configurable en opciones)
- [x] Estadísticas por materia en informe `.txt`
- [ ] Exportar informe a PDF/CSV desde pantalla de cierre
- [ ] Código de partida (semilla + filtros exportables)
- [ ] Presets libre guardados por el jugador

---

## Estadísticas locales del usuario

*v1 — 2026-06-28*

### Completado

- [x] Pantalla «Mis estadísticas» (Info → 📊)
- [x] `estadisticas_jugador.json` (creado al arrancar si falta)
- [x] Registro al cerrar partida (todos los modos, vía `ResumenPartida`)
- [x] Restablecer estadísticas desde Opciones (⚙️)
- [x] Totales globales, evolución semanal, desglose por modo
- [x] Récords resistencia (máx. pregunta y puntos) y escape; mejor sesión %
- [x] Ranking materias débiles y fuertes (mín. 3 intentos); Teoría vs Cálculo
- [x] Panel siempre visible (ceros si no hay datos); sin historial partida a partida ni ranking JSON

### Pendiente

- [x] Tarjeta «Sigue por aquí»
- [ ] Gráficos semanales (% y volumen) + filtro por modo
- [ ] Tendencia por materia (↑ ↓ →)
- [ ] Mejor nota historia/libre por preset; hitos desbloqueados
- [ ] Botón «ver informe» `.txt`; export stats CSV
- [ ] Opt-out «no registrar estadísticas»
- [ ] Preguntas repetidas mal; botón «Practica {materia}»
- [ ] Pestañas detalle por modo; repaso espaciado / solo mis fallos

---

## IV. Por modo

### Modo libre

**Completado**

- [x] Asistente filtros (curso, semestre, materia, tipo, dificultad)
- [x] Banco revisado (480) y ampliado opcional (plantillas)
- [x] Partida finita e infinita
- [x] Informe al cerrar con desglose

**Pendiente**

- [ ] Tercer panel de configuración en modo libre: eventos y powerups de modos especiales (resistencia / escape) activables en partida libre
- [x] Registrar duración de partida (tiempo global ya configurable) en informes `.txt` y en `estadisticas_jugador.json` / panel «Mis estadísticas»

### Modo historia

**Completado**

- [x] Presets configurables (`Juego/presets.json`)
- [x] Ponderación por histórico qualificacions — **retirado (2026-08-07);** sustituido por práctica local
- [x] Informe examen con nota y materias a reforzar

**Pendiente**

- [x] Tras cerrar un simulacro/examen (historia o examen fijo): botón «Otro examen dirigido» que genera un nuevo test usando los **aciertos y fallos de esa sesión** (materias/temas débiles del jugador)

### Modo resistencia

**Completado**

- [x] Partida continua con vidas y puntos arcade
- [x] Hitos de racha, apuestas, maldiciones, bloques temáticos
- [x] Objetos (bomba, 50/50, escudo, salto, cambio, amuleto…)
- [x] Eventos sobre pregunta (niebla, relámpago, doble puntos…)
- [x] Eventos sí/no (Apuesta/Oferta) + pity + exclusión mutua
- [x] Barra de estado con chips emoji
- [x] Preguntas exclusivas por tier/racha

**Pendiente**

- [ ] Checkpoints cada 25 preguntas
- [ ] Jefes de materia
- [ ] Mutadores al empezar
- [ ] Logros persistentes
- [ ] Duelo hot-seat
- [ ] Adaptativa según qualificacions; informe por materia al cerrar
- [ ] Rotación curricular; sets rotativos; más tiers
- [ ] Mapa escalada (ver §V mapas); cooldown objetos; intensidad visual/audio

### Modo escape room

**Completado**

- [x] Salas configurables 5–50, tres puertas por sala
- [x] Escalada dificultad, cronómetros, niebla
- [x] Puertas descanso / tienda / botín / jefe
- [x] Pity suave + hard pity por tipo
- [x] Economía arcade y tienda (precio mínimo viable)
- [x] Inventario compartido con resistencia
- [x] Semilla aleatoria por partida
- [x] Informe `.txt` al terminar

**Pendiente**

- [ ] Checkpoints y reanudar
- [ ] Mutadores; logros; sala final / resumen de run
- [ ] Filtros curriculares; informe materias débiles; modo examen escape
- [ ] Mapa progreso (ver §V mapas); iconografía por tipo puerta; transiciones; pity visible
- [ ] Artículos tienda exclusivos; eventos sala global; puertas encadenadas
- [ ] Bonificación racha puertas; puertas más largas en fases finales

---

## V. Dirección artística (UI visual)

*(Sin capa narrativa prevista: no guion, personajes ni bocadillos. Objetivo a medio plazo: **mapas y arte** para orientar por imagen y reducir texto/tooltips.)*

- [ ] **Mapas de juego** (menú, escape, resistencia, etc.): progreso y elecciones en pantalla en lugar de listas largas; menos texto explicativo y tooltips de por medio
- [ ] Fondos o escenas por sala/modo (arte estático + hotspots; **sin** diálogos ni historia)
- [ ] Inventario con sprites propios (sustituir emojis)
- [ ] Música/FX opcionales + toggle

---

## VI. Experiencia de juego

*(Ideas lúdicas sin lente académico — todo pendiente.)*

### Sensación («juice»), audio, modos alternativos, metajuego, social, anti-frustración, curiosidades

- [ ] Ver listado completo en historial git / notas anteriores; ningún ítem de §VI implementado aún
- [ ] Candidatos prioritarios: combo visual racha, SFX acierto/fallo, barra pity visible resistencia, récord personal al superar marca

---

## VII. Ingeniería y mantenimiento

### Completado

- [x] Suite tests unitarios (615 tests)
- [x] CI: tests.yml (pre-commit, unit, integration, mypy, summary)
- [x] CI: sonarcloud.yml, pr_agent.yml (opcionales)
- [x] mypy en `Juego/Comun` y `Files/`
- [x] `Docs/utilidades.py` (limpieza + zip) y `mantenimiento.py temporales`
- [x] Tests dominio: libre, historia, resistencia, escape, semillas, eventos, informes
- [x] Tests UI gráfica parciales (menús, preferencias, estadísticas, lanzador)

### Pendiente

- [x] Tests UI ampliados (flujos escape/resistencia con semilla fija en navegación)
- [x] mypy extendido a todo `Juego/Grafico/`
- [x] CI: release `juego` con zip jugable (`paquete-jugable.yml`)
- [x] Script «health check» único (datos + tests + validar banco)
- [ ] Docker desarrollo
- [ ] Benchmark arranque pool 1000 preguntas

---

## VIII. Descartado por diseño

- **Reto del día escape o resistencia** — solo **Examen del día** usa semilla diaria fija.
- **Avisos sobre preguntas futuras** — solo efectos sobre pregunta actual o bloques en curso.
- **Eventos que cambian selección del pool** — segmentación vía bloques temáticos.
- **Ranking JSON / pantalla dedicada** — sustituido por récords en `estadisticas_jugador.json` (2026-06-28).
- **Ranking online obligatorio** — no previsto.
- **Microtransacciones** — economía 100 % in-game.
- **Narrativa / historia / texto de ambientación** — no previsto (guion por salas, personaje guía, bocadillos, transiciones narrativas, estilo Inka Games). Sí se contempla UI visual (mapas, fondos, sprites) sin relato.
