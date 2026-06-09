# Memoria TFG

**Alumno:** Daniel Fageda Figueredo · **NIU:** 1601846 · **Tutor:** Víctor Navas Portella

**Título provisional:** Diseño y desarrollo de un videojuego educativo tipo escape room basado en contenidos del grado en Matemática Computacional y Análisis de Datos

El detalle técnico del repositorio (esquema del banco, scripts, arquitectura del juego) se documenta en los [`README.md`](README.md) del proyecto y se cita en los apéndices al final de esta memoria.

---

## 1. Introducción

### 1.1 Contexto

El grado en Matemática Computacional y Análisis de Datos (MatCAD) de la Universitat Autònoma de Barcelona articula un plan de estudios amplio en el que conviven contenidos de matemáticas, computación, estadística, optimización e inteligencia artificial. La evaluación continua y la autoevaluación son piezas habituales del aprendizaje universitario, pero los recursos disponibles para practicar de forma autónoma —cuestionarios genéricos, listas de ejercicios descontextualizadas o plataformas que no reflejan la estructura del grado— suelen ofrecer poca trazabilidad respecto al plan curricular.

Paralelamente, la gamificación y los videojuegos educativos han ganado relevancia como complemento a la enseñanza formal: permiten practicar con retroalimentación inmediata, reducir la ansiedad ante la evaluación en algunos contextos y favorecer la motivación mediante mecánicas de juego (vidas, puntuación, progresión). Los escape rooms educativos y las novelas gráficas interactivas representan un subconjunto de los *serious games* en el que la narrativa envuelve retos cognitivos; sin embargo, su desarrollo completo exige un esfuerzo considerable en diseño gráfico, guion y validación pedagógica.

### 1.2 Motivación

Este Trabajo de Fin de Grado surge de la necesidad de disponer de una herramienta de autoevaluación alineada con las asignaturas del grado, capaz de:

- gestionar un banco de preguntas estructurado y auditable,
- ofrecer una experiencia de juego que incentive la práctica repetida,
- analizar la calidad del contenido (distractores, duplicados, coherencia curricular),
- y sentar las bases para modelos pedagógicos más ricos (multiasignatura, prerrequisitos, narrativa).

La motivación principal es combinar programación, matemáticas y diseño interactivo en una aplicación práctica que consolide conocimientos del grado y que pueda ser extendida por el propio autor o por el profesorado.

### 1.3 Alcance del entregable

El documento de proyecto inicial planteaba un videojuego tipo escape room con interfaz gráfica. Durante el desarrollo se priorizó la **calidad y estructura del banco de preguntas** y un **prototipo jugable en consola**, decisión metodológica coherente con un enfoque incremental: primero validar el contenido y la lógica de evaluación; después añadir la capa narrativa y gráfica.

**Estado actual:** cuestionario en consola con tres modos operativos (libre, historia, feedback), banco de **480 preguntas** revisadas manualmente, herramientas de mantenimiento del dataset y empaquetado opcional en ejecutable Windows. La capa gráfica escape room / novela queda como evolución futura.

---

## 2. Objetivos

### 2.1 Objetivo general

Diseñar e implementar un videojuego educativo interactivo en el que la progresión del jugador dependa de la resolución de retos basados en contenidos del grado en Matemática Computacional y Análisis de Datos.

### 2.2 Objetivos específicos

| # | Objetivo | Indicador de logro | Estado |
|---|----------|-------------------|--------|
| OE1 | Diseñar una narrativa interactiva como marco de los retos | Guion de escenas/salas vinculadas a materias del grado | Pendiente (futuro) |
| OE2 | Crear distintos tipos de retos relacionados con las materias | Banco con preguntas de Teoría y Cálculo, tres niveles de dificultad, 40 materias | **Cumplido** |
| OE3 | Implementar algoritmos que validen las respuestas del jugador | Motor de partida con corrección A–D, puntuación, vidas, informes | **Cumplido** |
| OE4 | Desarrollar una interfaz gráfica sencilla e intuitiva | Interfaz gráfica de usuario (Pygame u otro motor) | Pendiente (futuro) |
| OE5 | Evaluar el funcionamiento y el valor formativo del sistema | Banco validado, pruebas unitarias, revisión manual, modo feedback | **Parcialmente cumplido** |

### 2.3 Objetivos derivados del desarrollo

Durante el proyecto surgieron objetivos técnicos no recogidos en el documento inicial pero necesarios para la calidad del entregable:

- Definir un **esquema canónico** del banco (480 preguntas, balance por dificultad, tipo y respuesta correcta).
- Enriquecer cada pregunta con **metadatos curriculares** (curso, semestre, grupo temático, nivel).
- Construir un **pipeline de mantenimiento** (validación, auditoría de distractores, deduplicación).
- Implementar un **modo historia** que genere exámenes balanceados según el histórico de qualificacions del grado.

---

## 3. Marco teórico y estado del arte

### 3.1 Aprendizaje activo y evaluación formativa

El aprendizaje universitario de calidad se asocia a estrategias que sitúan al estudiante en el centro del proceso: resolver problemas, recibir retroalimentación y reflexionar sobre los errores (Biggs y Tang, 2011). La **evaluación formativa** no tiene como única finalidad calificar, sino orientar el aprendizaje mediante información sobre el desempeño y sobre cómo mejorarlo (Nicol y Macfarlane-Dick, 2006).

Los cuestionarios de opción múltiple, cuando están bien diseñados, permiten cubrir un espectro amplio de contenidos con corrección automática. Su efectividad depende de la calidad del ítem: enunciados claros, distractores plausibles y alineación con los resultados de aprendizaje (Haladyna et al., 2002). Un banco estructurado facilita la revisión sistemática y la reutilización por parte del profesorado.

### 3.2 Gamificación y aprendizaje basado en juegos

La **gamificación** introduce elementos de diseño de juegos en contextos no lúdicos (puntos, niveles, retos) para aumentar la participación (Deterding et al., 2011). No debe confundirse con un juego completo: la gamificación puede aplicarse a un cuestionario sin narrativa gráfica, como ocurre en este TFG con vidas, puntuación diferenciada por dificultad y progresión de complejidad.

El **aprendizaje basado en juegos digitales** (*game-based learning*) apuesta por experiencias más inmersivas. Prensky (2001) subraya que los nativos digitales responden favorablemente a entornos interactivos con reglas claras y retroalimentación inmediata. Gee (2003) analiza cómo los buenos videojuegos enseñan mediante tutoriales integrados, dificultad creciente y sentido de competencia.

En el ámbito de la educación superior en STEM, los juegos serios han mostrado potencial para reforzar conceptos abstractos, aunque la evidencia exige estudios concretos por dominio y nivel (Michael y Chen, 2005; Kiili, 2005).

### 3.3 Serious games, escape rooms y narrativa

Los **serious games** son aplicaciones diseñadas con un propósito formativo principal, no meramente recreativo (Michael y Chen, 2005). Los **escape rooms educativos** trasladan la mecánica de salas y puzles encadenados al aula: fomentan el trabajo en equipo, el razonamiento bajo presión temporal y la aplicación de conocimientos en contexto (Veldkamp et al., 2020). Las **novelas gráficas interactivas** aportan narrativa ramificada con menor carga de desarrollo 3D que un motor de juego completo.

El estado del arte muestra que la narrativa incrementa la motivación cuando está alineada con los objetivos de aprendizaje; si no lo está, puede distraer (Habgood y Ainsworth, 2011). Por ello, este TFG separa explícitamente la capa de contenido evaluable (banco + motor de juego) de la capa narrativa aún no implementada.

### 3.4 Bancos de preguntas y sistemas de tutoría inteligente

En ingeniería y ciencias de la computación es habitual disponer de bancos de ejercicios para práctica autónoma. Plataformas como Moodle integran cuestionarios con categorías y estadísticas de uso. Los sistemas adaptativos avanzados modelan el conocimiento del alumno y seleccionan ítems según prerrequisitos (Brusilovsky y Peylo, 2003).

Este proyecto no implementa un modelo de usuario adaptativo completo, pero anticipa esa línea con la propuesta de campos `Materias_relacionadas` y `Prerequisitos` en el esquema de datos, y con el modo historia que pondera materias según el histórico de qualificacions del grado.

### 3.5 Trabajos relacionados y posicionamiento

Existen aplicaciones comerciales y académicas de cuestionarios (Kahoot, Quizlet, AulaWeb, etc.), pero pocas están **específicamente modeladas sobre el plan de estudios completo de un grado concreto** con metadatos curriculares explícitos y código abierto mantenible por el autor.

La contribución distintiva de este TFG respecto a un cuestionario genérico es triple:

1. **Alineación curricular:** 40 materias del grado MatCAD con estructura 4×2×5 y 10 grupos temáticos.
2. **Trazabilidad de calidad:** revisión manual documentada, auditoría de distractores, detección de duplicados semánticos.
3. **Arquitectura extensible:** separación datos / motor de juego / modos, preparada para narrativa gráfica futura.

---

## 4. Hipótesis de trabajo

A partir del marco teórico y del diseño del sistema, se formulan las siguientes hipótesis:

**H1.** Un banco de preguntas estructurado según el plan curricular del grado (materia, dificultad, tipo Teoría/Cálculo) y enriquecido con metadatos académicos (curso, semestre, grupo, nivel) **permite una autoevaluación segmentada** más útil que un cuestionario homogéneo sin esa estructura.

**H2.** La incorporación de mecánicas de juego (vidas, puntuación variable, dificultad progresiva) en un cuestionario de consola **aumenta la motivación para practicar** respecto a un listado estático de preguntas, sin requerir inicialmente una interfaz gráfica compleja.

**H3.** Un pipeline automatizado de validación y auditoría del banco **detecta inconsistencias** (desequilibrios, distractores débiles, duplicados) que una revisión ad hoc no cubriría de forma sistemática.

**H4.** El uso del histórico de qualificacions del grado para balancear exámenes en el modo historia **aproxima la selección de contenidos** a la estructura real de evaluación del plan de estudios.

> **Nota metodológica:** H1 y H3 se apoyan en el diseño del banco y en los informes de auditoría generados. H2 y H4 requerirían un estudio con usuarios (cuestionario de usabilidad, comparación pre/post) que queda fuera del alcance de esta primera versión pero se señala como validación empírica futura.

---

## 5. Metodología

### 5.1 Enfoque general

El desarrollo siguió una **metodología incremental** en cuatro fases, alineada con el documento de proyecto:

1. **Análisis y diseño:** definición de materias, esquema del banco, metadatos y modos de juego.
2. **Implementación:** dataset, scripts de mantenimiento, motor de partida en consola.
3. **Pruebas:** validación estructural, pruebas unitarias, revisión manual del contenido.
4. **Evaluación:** análisis del resultado, identificación de limitaciones y líneas futuras.

El control de versiones con Git permitió iterar sobre el banco y el código de forma trazable. El repositorio público facilita la reproducibilidad del trabajo.

### 5.2 Diseño del banco de preguntas

**Población de ítems:** 40 materias del grado MatCAD × 12 preguntas = **480 ítems**.

**Esquema por materia:** 2FT 2MT 2DT 2FC 2MC 2DC (6 de Teoría + 6 de Cálculo, escalón Fácil → Media → Difícil en cada mitad).

**Reparto global:**

| Dimensión | Distribución |
|-----------|--------------|
| Dificultad | 160 Fácil / 160 Media / 160 Difícil |
| Tipo | 240 Teoría / 240 Cálculo |
| Respuesta correcta | 120 por letra A, B, C y D |

**Metadatos curriculares** en `listado_materias.csv`: `Grupo`, `Nivel`, `Curso`, `Semestre`, `Tematica` (10 grupos temáticos globales).

**Revisión de contenido:** revisión manual por bloques de Ids (1–480), con registro en `Data/revision_manual.md`. Criterios: redacción genérica, coherencia con el nivel de la materia, distractores plausibles, ausencia de referencias a temarios internos de asignatura.

**Validación automatizada:** comando `mantenimiento.py validar` comprueba balance, orden canónico e integridad de columnas. Auditoría de distractores y detección de duplicados semánticos mediante scripts dedicados.

Detalle técnico: [`Data/README.md`](Data/README.md).

### 5.3 Diseño e implementación del software

**Stack tecnológico:**

- Lenguaje: Python 3.10+ (biblioteca estándar en el juego; sin dependencias externas obligatorias).
- Persistencia: CSV y JSON para datos; informes y feedback en `.txt` locales.
- Empaquetado opcional: PyInstaller (Windows), script `build_exe_onefile.ps1`.

**Arquitectura en capas:**

```
Lanzador (juego_cuestionario.py)
    → Modos (libre / historia / feedback)
        → Motor de partida (reglas, puntuación, vidas)
            → Capa de datos (CSV, metadatos, plantillas)
```

**Modos implementados:**

| Modo | Función pedagógica |
|------|-------------------|
| **Libre** | Autoevaluación abierta con filtros por curso, semestre, temática, grupo, nivel, materia y dificultad |
| **Historia** | Simulación de examen balanceado según histórico de qualificacions del grado |
| **Feedback** | Canal de mejora continua (bugs, sugerencias) hacia el creador |

**Mecánicas de juego:** dificultad global progresiva (sube cada tres preguntas), puntuación +10/+20/+30 según dificultad, penalización por error, 3 vidas por partida, informe al cerrar en modo examen.

Detalle técnico: [`Juego/Consola/README.md`](Juego/Consola/README.md).

### 5.4 Validación y aseguramiento de la calidad

| Actividad | Herramienta / método |
|-----------|---------------------|
| Balance estructural del CSV | `mantenimiento.py validar` |
| Revisión manual del contenido | Bloques documentados en `revision_manual.md` |
| Auditoría de distractores | `mantenimiento.py auditar-distractores` |
| Duplicados semánticos | `duplicados.py revisar` |
| Pruebas de regresión del juego | `python -m unittest discover -s Juego/Tests -v` |
| Revisión con profesorado | Identificación de solapamiento temático y prerrequisitos (véase sección 8) |

El banco de producción (`Preguntas.csv`) se declaró **cerrado** en junio de 2026; las escrituras en el CSV requieren `TFG_PERMITIR_CSV=1` para evitar modificaciones accidentales.

### 5.5 Criterios de éxito

Se consideró exitoso el entregable si:

1. El banco cumplía el esquema 480 ítems con balance verificado.
2. Los tres modos de juego eran ejecutables sin errores en el flujo principal.
3. Existía documentación reproducible (README, memoria, scripts de mantenimiento).
4. El contenido había pasado revisión manual completa.

---

## 6. Resultados

### 6.1 Banco de preguntas

Se obtuvo un banco cerrado de **480 preguntas** con las siguientes propiedades verificadas:

- **40 materias** alineadas con el listado del grado.
- **12 preguntas por materia** siguiendo el patrón 2FT 2MT 2DT 2FC 2MC 2DC.
- **Revisión manual 480/480** completada en cinco tramos temporales.
- **Informes de calidad** generados: `auditoria_distractores.md`, detección de pares similares pendientes de sustitución (3 en CSV modo seguro, ~13 intra-materia en plantillas beta).

El banco distingue **modo seguro** (solo dataset revisado) y **modo beta** (pool ampliado con plantillas no revisadas, hasta 1440 ítems jugables), dejando clara la trazabilidad para evaluación formal del TFG.

### 6.2 Aplicación de juego

Se entregó un cuestionario en consola funcional:

| Componente | Resultado |
|------------|-----------|
| Lanzador | `Juego/juego_cuestionario.py` |
| Paquete de lógica | `Juego/Consola/` (18 módulos) |
| Modo libre | Filtros multidimensionales, informes `.txt` |
| Modo historia | Generador de examen según `Historic_qualificacions_MatCAD_completo.csv` |
| Modo feedback | Guardado local + envío SMTP opcional |
| Ejecutable | Build opcional con PyInstaller |
| Pruebas | Suite en `Juego/Tests/` (informes, entrada, feedback, configuración) |

### 6.3 Organización curricular modelada

Las 40 materias se distribuyen en:

- **4 cursos** × **2 semestres** × **5 materias**.
- **10 grupos temáticos** (álgebra, cálculo, sistemas, programación, algoritmia, métodos numéricos, probabilidad y datos, bases de datos, IA, modelización física).

Cada pregunta se enriquece al cargar con `curso`, `semestre`, `grupo`, `nivel` y `tematica`, lo que habilita filtros de partida alineados con la etapa formativa del estudiante.

Diagramas: [`Data/README.md`](Data/README.md).

### 6.4 Herramientas de mantenimiento

Se desarrolló un conjunto de scripts en `Files/Scripts/` con punto de entrada unificado (`mantenimiento.py`): validación, revisión, pipeline de plantillas, auditorías, deduplicación y estadísticas del histórico de qualificacions. Los scripts de regeneración masiva del CSV se aislaron en `Files/Archivo/` con protección de banco cerrado.

### 6.5 Síntesis cuantitativa

| Métrica | Valor |
|---------|-------|
| Preguntas en banco de producción | 480 |
| Materias cubiertas | 40 |
| Módulos Python del juego (Consola) | 18 |
| Modos de juego operativos | 3 |
| Pruebas unitarias | 4 módulos de test |
| Grupos temáticos modelados | 10 |

---

## 7. Discusión

### 7.1 Cumplimiento de los objetivos

El **objetivo general** se cumple de forma parcial: existe un juego educativo interactivo basado en contenidos del grado, pero la progresión narrativa tipo escape room no está implementada. La progresión actual es ludificada (vidas, puntos, dificultad creciente) y curricular (filtros por etapa del grado).

Los **objetivos específicos** OE2, OE3 y OE5 están cubiertos en su versión de consola. OE1 y OE4 (narrativa gráfica e interfaz visual) quedan explícitamente como trabajo futuro. Esta decisión es defendible: el prototipo valida el núcleo evaluable sin el coste de desarrollo gráfico, en línea con el principio de prototipado incremental en ingeniería del software.

### 7.2 Validez del banco de preguntas

La **validez de contenido** se abordó mediante revisión manual exhaustiva y criterios de redacción acordados. La **validez estructural** se garantiza con reglas de balance automatizadas. Quedan abiertas:

- la **validez semántica** fina (algunos pares de ítems muy similares),
- y la **validez predictiva** (relación entre desempeño en el juego y desempeño académico real), no medida en este TFG.

La revisión con profesorado puso de manifiesto limitaciones del modelo de una sola etiqueta `Materia`:

1. **Solapamiento temático:** preguntas que encajan en varias asignaturas (p. ej. inferencia en Probabilidad y en Modelización e Inferencia).
2. **Prerrequisitos:** preguntas de cursos avanzados que asumen conceptos de materias previas (p. ej. optimización y cálculo multivariable).

Estas observaciones motivan la propuesta de campos `Materias_relacionadas` y `Prerequisitos` en futuras versiones del esquema.

### 7.3 Utilidad para autoevaluación y apoyo docente

El sistema permite al estudiante:

- practicar por **semestre o temática**, acorde a su momento del grado;
- simular un **examen balanceado** (modo historia);
- recibir **informe detallado** al finalizar una partida en modo examen.

Para el profesorado, el banco estructurado y los scripts de auditoría facilitan revisión por materia y detección de ítems problemáticos. El modo feedback cierra un ciclo de mejora continua.

La interfaz en consola limita la accesibilidad para usuarios no familiarizados con terminal; el tutorial de foco de teclado al inicio mitiga parte de esa barrera, pero una GUI sería deseable para despliegue masivo.

### 7.4 Relación con las hipótesis

| Hipótesis | Valoración |
|-----------|------------|
| **H1** | Apoyada por diseño: filtros curriculares operativos; falta estudio comparativo con usuarios |
| **H2** | Plausible por diseño; no contrastada empíricamente en este TFG |
| **H3** | Apoyada: auditorías detectan desequilibrios y distractores débiles de forma reproducible |
| **H4** | Apoyada por implementación del modo historia; no validada con cohorte de estudiantes |

### 7.5 Limitaciones del estudio

1. **Sin estudio de usuarios:** no se recogieron datos de usabilidad ni de aprendizaje con una muestra de estudiantes.
2. **Interfaz en consola:** reduce el atractivo visual respecto al escape room planteado inicialmente.
3. **Modelo de datos simplificado:** una materia por pregunta; sin prerrequisitos explícitos aún.
4. **Idioma del banco:** preguntas en castellano/catalán según materia; coherencia terminológica revisada pero mejorable.
5. **Modo beta:** pool ampliado con plantillas no revisadas; debe distinguirse del banco de producción en cualquier evaluación formal.

### 7.6 Trabajo futuro

- Implementar `Materias_relacionadas` y `Prerequisitos` en el CSV y en los filtros del juego.
- Desarrollar la capa gráfica escape room / novela gráfica del documento de proyecto.
- Realizar un **piloto con estudiantes** del grado (cuestionario SUS, entrevistas, comparación de rendimiento).
- Sustituir los pares de ítems semánticamente similares detectados por la auditoría.
- Explorar integración con plataformas institucionales (Moodle, AulaWeb).

---

## 8. Conclusiones

Este Trabajo de Fin de Grado ha diseñado e implementado un **sistema de cuestionarios académicos** alineado con el plan de estudios del grado en Matemática Computacional y Análisis de Datos, integrando:

- un **banco de 480 preguntas** estructurado, balanceado y revisado manualmente;
- un **juego en consola** con tres modos (libre, historia, feedback) que gamifica la autoevaluación;
- un **conjunto de herramientas** de validación y mantenimiento del dataset;
- y una **arquitectura extensible** preparada para narrativa gráfica y modelos pedagógicos más ricos.

La principal contribución académica es pasar de un cuestionario genérico a una herramienta con **criterio didáctico explícito**: trazabilidad curricular, calidad auditable del banco y mecánicas de juego orientadas a la práctica repetida. El desvío respecto al título inicial (escape room gráfico) se compensa con un entregable técnicamente sólido y documentado, que constituye la base sobre la que construir la experiencia narrativa.

En el plano personal, el proyecto ha consolidado competencias de programación en Python, diseño de datos, ingeniería de software incremental y reflexión pedagógica sobre la evaluación en grados STEM interdisciplinares.

Las líneas futuras más inmediatas son la validación con usuarios reales, el enriquecimiento del modelo de datos con multiasignatura y prerrequisitos, y el desarrollo de la interfaz gráfica prevista en el documento de proyecto.

---

## 9. Bibliografía

Biggs, J., y Tang, C. (2011). *Teaching for Quality Learning at University* (4.ª ed.). Open University Press.

Brusilovsky, P., y Peylo, C. (2003). Adaptive and intelligent web-based educational systems. *International Journal of Artificial Intelligence in Education*, *13*(2–4), 159–172.

Deterding, S., Dixon, D., Khaled, R., y Nacke, L. (2011). From game design elements to gamefulness: Defining "gamification". En *Proceedings of the 15th International Academic MindTrek Conference* (pp. 9–15). ACM. https://doi.org/10.1145/2181037.2181040

Gee, J. P. (2003). *What Video Games Have to Teach Us About Learning and Literacy*. Palgrave Macmillan.

Habgood, M. P. J., y Ainsworth, S. E. (2011). Motivating children to learn effectively: Exploring the use of intrinsic and extrinsic motivation in educational games. *British Journal of Educational Technology*, *42*(2), 183–200. https://doi.org/10.1111/j.1467-8535.2009.01034.x

Haladyna, T. M., Downing, S. M., y Rodriguez, M. C. (2002). A review of multiple-choice item-writing guidelines for classroom assessment. *Applied Measurement in Education*, *15*(3), 309–333. https://doi.org/10.1207/S15324818AME1503_5

Kiili, K. (2005). Digital game-based learning: Towards an experiential gaming model. *The Internet and Higher Education*, *8*(1), 13–24. https://doi.org/10.1016/j.iheduc.2004.12.001

Michael, D. R., y Chen, S. L. (2005). *Serious Games: Games That Educate, Train, and Inform*. Thomson Course Technology.

Nicol, D. J., y Macfarlane-Dick, D. (2006). Formative assessment and self-regulated learning: A model and seven principles of good feedback practice. *Studies in Higher Education*, *31*(2), 199–218. https://doi.org/10.1080/03075070600572090

Prensky, M. (2001). *Digital Game-Based Learning*. McGraw-Hill.

Veldkamp, A., van de Grint, L., Knippels, M. C. P. J., y van Joolingen, W. R. (2020). Escape education: A systematic review on escape rooms in education. *Educational Research Review*, *31*, 100364. https://doi.org/10.1016/j.edurev.2020.100364

---

## Apéndices — documentación técnica del repositorio

| Apéndice | Contenido | Enlace |
|----------|-----------|--------|
| A | Esquema del banco, revisión manual, diagramas curriculares | [`Data/README.md`](Data/README.md) |
| B | Arquitectura del juego, modos, puntuación, bancos beta | [`Juego/Consola/README.md`](Juego/Consola/README.md) |
| C | Scripts de mantenimiento, balanceo, auditorías | [`Files/Scripts/README.md`](Files/Scripts/README.md) |
| D | Scripts legado de regeneración CSV | [`Files/Archivo/README.md`](Files/Archivo/README.md) |
| E | Pruebas unitarias | [`Juego/Tests/README.md`](Juego/Tests/README.md) |
| F | Repositorio y guía rápida | [`README.md`](README.md) |

**Repositorio:** https://github.com/Dafafi63f/Escape-Room.git
