# Revisión manual del banco de preguntas

> Trazabilidad **por Ids** del banco `Data/Preguntas.csv` (redacción genérica). Estado global del TFG: [`ESTADO.md`](ESTADO.md). No duplicar el resumen aquí: actualizar [`ESTADO.md`](ESTADO.md) al cerrar cada bloque.

Trazabilidad de la revisión manual del banco. Actualizar este fichero (detalle) y [`ESTADO.md`](ESTADO.md) (resumen) al cerrar cada tramo.

**Última actualización:** 2026-06-03  
**Progreso:** **480 / 480 (100 %)** — banco **12 preguntas/materia** (40 materias), redacción genérica para el juego  
**Aprobación usuario:** ids **1–480** — **cerrado** (contenido validado por bloques; ver tablas por tramo)  
**Validación habitual:** `python -c "import sys; sys.path.insert(0,'Files'); from balance_lib import ejecutar_validar; ejecutar_validar(detalle=False)"` — avisos menores de orden canónico en algunas materias (no bloquean el juego)  
**Mantenimiento 2026-06-03:** `python Files/Scripts/mantenimiento.py plantillas pipeline` → `criterios` → `auditar-distractores` (comandos: [`Files/Scripts/README.md`](../Files/Scripts/README.md))

| Ids | Estado | Materias (listado `Data/listado_materias.csv`) |
|-----|--------|------------------------------------------------|
| **1–240** | **Aprobado** | Àlgebra Lineal … **Optimització** (20 materias; §1–240) |
| **241–480** | **Aprobado** | Aprenentatge Computacional … **Visió per Computador** (20 materias; §241–480) |

---

## Ids 1–240 — aprobación usuario (2026-06-02)

Contenido validado por el autor del TFG para las **20 primeras materias** (12 preguntas cada una). Incluye los ajustes recientes de Visualització 3D (169–180), Tècniques (157–168), Fonaments (25–36), Grafs, IA, etc. **No retocar** salvo petición explícita.

| Ids | Materia |
|-----|---------|
| 1–12 | Àlgebra Lineal |
| 13–24 | Càlcul en una Variable |
| 25–36 | Fonaments de Computadors |
| 37–48 | Iniciació a la Programació |
| 49–60 | Programari de Sistema |
| 61–72 | Algorítmia i Combinatòria en Grafs |
| 73–84 | Càlcul en Diverses Variables |
| 85–96 | Càlcul Numèric |
| 97–108 | Probabilitat |
| 109–120 | Programació Orientada als Objectes |
| 121–132 | Bases de Dades Relacionals |
| 133–144 | Equacions Diferencials Ordinàries |
| 145–156 | Modelització i Inferència |
| 157–168 | Tècniques de Disseny d'Algoritmes |
| 169–180 | Visualització 3D |
| 181–192 | Anàlisi Complexa i de Fourier |
| 193–204 | Anàlisi de Dades Complexes |
| 205–216 | Intel·ligència Artificial |
| 217–228 | Mètodes Numèrics i Probabilístics |
| 229–240 | Optimització |

---

## Decisiones globales (todas las sesiones)

- `gradiente` restringido a `Càlcul en Diverses Variables` (eliminado de `Optimització` en criterios).
- `entropía` restringida a `Teoria de la Informació` (y eventualmente `Física, Abstracció i Computació` si se añade contenido).
- Menos preguntas genéricas de `bits` fuera de materias informacionales.
- No inyectar en `plantillas.json` enunciados con sufijo `"(variante N)"`.
- **Programari vs HPC / Fonaments:** terminal, shell, `pipe`, `git`, `gcc` en Programari; pipeline en Fonaments (no en Programari).
- **Grafs:** **única materia** con A*, Dijkstra, f(n)=g+h y h(n) en A* (ids 51, 53, 59, 60); sin TSP/Floyd; teoría de grafos + conteos.
- **Dades Complexes (161–170):** modelo lineal (regresión): modelo lineal, L2/MCO, R², homocedasticidad, test F, residuo/predicción, **bootstrap** (remuestreo con reemplazo), SSE, GLM logística. Reserva: devianza, ML=MCO, extrapolación, R²=0. Sin train/test.
- **POO:** solo Python en cálculo; banco en `Files/fix_final_materias.py` (`_poo_banco`).
- **Probabilitat:** una sola Bayes (id 90); sin duplicados binomial/unión/varianza.
- **EDO:** sin Wronskiano; id 120 PVI (no paralelepípedo).
- **Modelització i Inferència:** sin RL; IC, error tipo I, inferencia coherente.
- **Intel·ligència Artificial (171–180):** sin duplicar A*/Dijkstra (eso va en Grafs). Teoría: Turing, búsqueda informada (heurística admisible, sin nombrar A*), no informada, local, minimax. **Cálculo:** recall, hojas árbol, precisión, minimax, P∧Q.
- **Optimització (191–200):** lineal y no lineal. **Lineal:** simplex, dual, holguras, KKT. **No lineal:** Newton (f', f''), Hessiano, convexidad; métodos golden/brent, BFGS, Nelder-Mead. Sin gradiente descendente genérico como eje del bloque.

---

## Ids 1–30

Bloques: `1..10` Àlgebra Lineal · `11..20` Càlcul en una Variable · `21..30` Fonaments de Computadors.  
Estructura: `5 Teoría + 5 Cálculo` por materia.

### 1–10 (Àlgebra Lineal)

`1`–`10`: **OK**

### 11–20 (Càlcul en una Variable)

- `11`–`18`, `13`–`15`: **OK**
- `12`: OK (serie geométrica, teoría)
- `19`: OK (límites, cálculo)
- `20`: OK (series, cálculo)

### 25–36 (Fonaments de Computadors) — 12 preguntas

**Teoría (25–30):** ancho de banda, latencia, journaling, **memoria virtual** (28), ciclo de instrucción, LRU. Sin fog computing ni entropía (van en otros bloques).

**Cálculo (31–36):** CPI→IPC (10⁹ inst/s), pipeline 104 ciclos, tiempo 2 ns (3 GHz×6 ciclos), AMAT caché 5 ns, TFLOPS, **bus 64 bits×4 ciclos = 32 B**.

**OK** (revisado 2026-06-02). Ids antiguos 21–30 → ahora **25–36**.

---

## Ids 31–130

| Ids | Materia |
|-----|---------|
| 31–40 | Iniciació a la Programació |
| 41–50 | Programari de Sistema |
| 51–60 | Algorítmia i Combinatòria en Grafs. Mètodes Heurístics |
| 61–70 | Càlcul en Diverses Variables |
| 71–80 | Càlcul Numèric |
| 81–90 | Probabilitat |
| 91–100 | Programació Orientada als Objectes |
| 101–110 | Bases de Dades Relacionals |
| 111–120 | Equacions Diferencials Ordinàries |
| 121–130 | Modelització i Inferència |

### 37–48 (Iniciació a la Programació)

**Teoría:** FT `while`, `if` · MT `for`, listas · DT **scope local en funciones**, **efectos secundarios** en funciones.  
**Cálculo:** `type([])`, `bool`, `range`, `len`, `%`, `//`. **OK** (2026-06-02).

### 49–60 (Programari de Sistema)

Teoría: shell, stdout, pipe, contexto proceso, `git commit`, compilador. Cálculo: `cd ..`, `touch`, `ls -a`, `ls \| wc -l`, `gcc -o`, redirección `>`.  
Sin Python (solo en Iniciació/POO). **OK** (2026-06-02).

### 61–72 (Algorítmia i Combinatòria en Grafs)

Teoría: heurística, árbol, **A\*** (h admisible), **MDP**, euleriano, matching bipartito.  
Cálculo: spanning trees \(K_3\), aristas \(K_4\), componentes, **f=g+h**, **Dijkstra**. **OK** (2026-06-02).

### 61–70 (Càlcul en Diverses Variables)

Diferenciabilidad, gradiente, coordenadas, integrales dobles, jacobiano. **OK**

### 71–80 (Càlcul Numèric)

Teoría: trapecio, redondeo, truncamiento, Newton-Raphson, **Romberg**.  
Cálculo (76–80): error relativo 0,1; Newton \(x_1=1{,}5\); bisección \(n=10\) (mitad < 0,001); Simpson \(1/3\); trapecio \(O(h^2)\). **OK**

### 81–90 (Probabilitat)

Teoría: \(E(X)\), independencia, condicional, unión, probabilidad total.  
Cálculo: varianza constante, binomial, Poisson, moneda, única Bayes (90 → 0,18).  
**OK**

### 109–120 (Programació Orientada als Objectes)

| Id | Tipo | Contenido |
|----|------|-----------|
| 109–114 | Teoría | Herencia, encapsulamiento, polimorfismo, **@staticmethod**, acoplamiento, cohesión |
| 115–120 | Cálculo | Python: `C()`, `self`, `a is b`, `c.v`, `__init__`, constructores |

Sin decoherencia cuántica (112 corregido). Solo Python en cálculo. **OK** (2026-06-02).

### 101–110 (Bases de Dades Relacionals)

Teoría: `GROUP BY`, FK, `HAVING`, `DELETE`, normalización (105; antes 2PL).  
Cálculo: claves compuestas, producto cartesiano, candidatas, `COUNT(*)`.  
**OK** — opcional: id 104 `DELETE` en Difícil (contenido fácil)

### 111–120 (EDO)

| Id | Cambio |
|----|--------|
| 112 | Wronskiano → orden de una EDO |
| 120 | Paralelepípedo → PVI \(y''+y=0\), \(y(\pi)\) |

Resto: Runge-Kutta (1 intro), Euler (1 cálculo numérico), Picard-Lindelöf, autónoma, rigidez, CI, \(y'=y\), \(y''-4y=0\), \(y''+y=0\). **OK**

### 121–130 (Modelització i Inferència)

| Id | Contenido |
|----|-----------|
| 121 | Modelo estadístico (antes ley científica) |
| 122–123 | p-valor, potencia |
| 124–125 | IC, error tipo I (antes EDA + RL) |
| 126–127 | OR con IC, rechazo p y α |
| 128 | Desviación típica 2,4,6,8 |
| 129–130 | Margen IC (SE y \(\sigma/\sqrt{n}\)) |

**OK**

---

## Ids 157–240 (detalle; bloque ya aprobado)

| Ids | Materia |
|-----|---------|
| 157–168 | Tècniques de Disseny d'Algoritmes |
| 169–180 | Visualització 3D |
| 181–192 | Anàlisi Complexa i de Fourier |
| 193–204 | Anàlisi de Dades Complexes |
| 205–216 | Intel·ligència Artificial |
| 217–228 | Mètodes Numèrics i Probabilístics |
| 229–240 | Optimització |

### 157–168 (Tècniques de Disseny d'Algoritmes)

Teoría: algoritmo, LIFO/pila, subestructura óptima, memoización top-down, subproblemas superpuestos (DP), **greedy**.  
Cálculo: quicksort, búsqueda binaria, merge sort, comparaciones binaria (1024→10), \(O(2^n)\) Fib recursivo, búsqueda lineal. Sin duplicar 161/162. **OK** (2026-06-02).

### 169–180 (Visualització 3D)

**Teoría (169–174):** afín 3D (169), ortográfica paralela vs perspectiva (170), cuaterniones/gimbal (171), intersección planos→recta (172), homogéneas P² (173), proyección cilíndrica (174). **Cálculo (175–180):** distancia 3D (175), escala 1:5 (176), puntos→recta (177), volumen paralelepípedo (178), producto vectorial (179), norma cuaternión (180). **OK** (2026-06-02: corregido duplicado 169/170 y 175).

### 151–160 (Anàlisi Complexa i de Fourier)

Más **Fourier** y **Cauchy**; una holomorfa (153). Sin reales/anualidades fuera de lugar. **OK**

### 161–170 (Anàlisi de Dades Complexes)

Alineado a regresión L2/MCO, residuos, test F, GLM logit, **bootstrap**; sin train/test. **OK**

### 171–180 (Intel·ligència Artificial)

Temario: Turing, búsquedas (informada/no informada/local), patrones estadístico/estructural, minimax, lógica proposicional. **Sin A*/Dijkstra** (van en Grafs 51–60). F/M/D **3/4/3** (id 172 Difícil; id 178 accuracy). Ladder: `python Files/balance.py ordenar-ladder`. **OK**

### 217–228 (Mètodes Numèrics i Probabilístics)

**Teoría:** integración (01–04), Monte Carlo (05–06), EDO Euler/Taylor/RK (09–12), multipaso (14–15). **Sin Metropolis ni PBC.**

| Bloque | Ámbito | Banco (ids) |
|-----|------|-------------|
| 01–02, 04 | Trapecio, Romberg, Simpson | **71–80** (+ **75** Romberg) |
| 05–06 | Monte Carlo | **217–218, 223–224, 226** |
| 09–11 | Euler, Taylor, RK4 | **219–220, 222, 225, 227–228** |
| 14–15 | Multipaso lineal | **222** |
| 16–19 | Estabilidad, stiff, PVF | reserva |

Cálculo revisado: escalado \(1/\sqrt{N}\), paso Euler (Practica 3), RK4 con 4 evaluaciones de \(f\). **OK**

### 229–240 (Optimització)

Alineado a programación lineal (Simplex, dual, holguras, KKT) y no lineal (Newton, Hessiano, convexidad).

Cálculo: mínimos cuadráticos, holguras, Hessiano \(2I\), complementariedad KKT. **OK**

**Cambios destacados en 157–240:** Complexa/Fourier; ADC + bootstrap; IA sin duplicar A*; MN (integración, ecuaciones); Optimització Newton/Simplex/KKT. **Bloque 1–240 aprobado por usuario.**

---

## Pendientes

### Estado cerrado para uso (2026-06)

**Datos listos:** `Preguntas.csv` (480/480 revisadas), `plantillas.json` (480 filas reflejadas como `dataset_480`, pool extra 24×40, sin duplicados exactos globales), `listado_materias.csv`. Juego modo libre: banco 1 = **MODO SEGURO**; bancos 2–3 = beta. Comprobación: `python Files/Scripts/mantenimiento.py auditar-plantillas`, `python Files/Scripts/mantenimiento.py duplicados revisar`.

### Calidad / unicidad semántica (futuro — no bloquea el TFG actual)

1. **CSV:** 3 pares *similares* (no exactos): Id 14↔21, 298↔322, 69↔72 — `duplicados.py revisar`.
2. **Plantillas:** ~13 pares similares **dentro** de la misma materia; ~129 **entre** materias (catálogo por temática + sufijo `[materia]`).
3. **Catálogo:** ampliar `Files/catalogo_internet_plantillas.py` con preguntas propias por materia.
4. **Repuesto:** opcional alinear/eliminar repuestos con enunciado parecido pero opciones distintas al CSV (LSTM, Sharpe, …).
5. **Modo beta:** dedup semántica al cargar las 960 extra si se exige cero solapamiento entre materias.

### Otros pendientes de contenido

1. **Id 25** (Fonaments): reforzar dificultad o sustituir pregunta de CPU.
2. **Id 104** (BDR): valorar `DELETE` en Difícil vs JOIN / integridad referencial.
3. **Plantillas EDO:** comprobar plantilla «autovalores 2×2» en sección EDO (no en CSV 111–120).
4. **Producto:** **modos historia y feedback** operativos en consola; evolución CSV (`Materias_relacionadas` / prerrequisitos) y capa gráfica pendientes. Bloques **289–480** documentados en secciones abajo.

### 301–312 (Bases de Dades No Relacionals)

**Alcance:** **MongoDB** (documental, BSON, colecciones, `$match`/`$eq`/`$project`) y **Neo4j** (grafos, nodos/relaciones, **Cypher**, `MATCH`, `count(r)`). Sin Cassandra/Redis como eje del bloque.

| Id | Tipo | Ámbito | Estado |
|----|------|------|--------|
| 301 | FT | MongoDB: BD documental | OK |
| 302 | FT | Cuándo usar Neo4j (relaciones explícitas) | OK |
| 303 | MT | MongoDB: colecciones de documentos | OK |
| 304 | MT | Neo4j: lenguaje Cypher | OK |
| 305 | DT | Neo4j: nodos y relaciones | OK |
| 306 | DT | MongoDB: documento JSON/BSON | OK |
| 307 | FC | MongoDB: operador `$match` | OK |
| 308 | FC | Neo4j: `count(r)` con 5 relaciones | OK |
| 309 | MC | MongoDB: operador `$eq` | OK |
| 310 | MC | Cypher: vecinos `MATCH (n)-[r]->(m)` | OK |
| 311 | DC | MongoDB: formato JSON/BSON | OK |
| 312 | DC | MongoDB: tamaño 500×2 KB ≈ 1000 KB | OK |

**Nota:** Repuesto en catálogo: CAP, `$group`, patrones Cypher adicionales (no en las 12 del CSV).

### 289–300 (Teoria de la Informació)

**Alcance:** Shannon — entropía, condicional, **codificación de fuente/canal**, **compresión (límite H, Huffman)**, teoremas I y II, cálculos básicos.

| Id | Tipo | Ámbito | Estado |
|----|------|------|--------|
| 289 | FT | H(X): entropía de X | OK |
| 290 | FT | Codificación de fuente / compresión (Huffman) | OK |
| 291 | MT | Entropía condicional H(X\|Y) | OK |
| 292 | MT | Codificación de canal vs fuente | OK |
| 293 | DT | Compresión sin pérdida: límite H(X) | OK |
| 294 | DT | 1.er teorema (codificación fuente) | OK |
| 295 | FC | Cálculo H(X\|Y)=H(X,Y)−H(Y) | OK |
| 296 | FC | Redundancia de canal: 10% sobre 1000 bits → 900 útiles | OK |
| 297 | MC | Bernoulli: máximo en p=0,5 | OK |
| 298 | MC | Auto-información −log₂(1/8)=3 bits | OK |
| 299 | DC | 2.º teorema (canal con ruido) | OK |
| 300 | DC | Huffman (1/2, 1/4, 1/4) → L̄=1,5 bits/símbolo | OK |

**Codificación/compresión en el banco:** 290 fuente, 292 canal, 293 límite de compresión, 294 teorema fuente, 296 redundancia, 300 Huffman. Información mutua y capacidad quedan en plantillas `general`/`repuesto` si hace falta ampliar.

### 313–324 (Informació Quàntica)

**Alcance:** qubit, superposición, puertas (H, unitarias), medida, teleportación, entrelazamiento, no-clonación, estados de Bell, dimensiones del espacio de estados (amplitudes / Hilbert).

| Id | Tipo | Ámbito | Estado |
|----|------|------|--------|
| 313 | FT | Puerta Hadamard → superposición | OK |
| 314 | FT | Medida en base computacional | OK |
| 315 | MT | Puertas unitarias (conservan norma) | OK |
| 316 | MT | Teleportación cuántica (entrelazamiento + clásico) | OK |
| 317 | DT | Entrelazamiento (correlaciones no clásicas) | OK |
| 318 | DT | Grados de libertad del qubit (2 reales) | OK |
| 319 | FC | Cuatro estados de Bell | OK |
| 320 | FC | Teorema de no-clonación | OK |
| 321 | MC | n qubits → 2^n amplitudes en base computacional | OK |
| 322 | MC | Parámetros reales estado puro (sin fase global) | OK |
| 323 | DC | Dimensión espacio de Hilbert = 2^n | OK (antes duplicaba 321) |
| 324 | DC | P(\|1⟩) tras H en \|0⟩ = 1/2 | OK (antes duplicaba 319) |

**Cambios:** eliminados duplicados 319/324 (Bell) y 321/323 (2^n); corregidas letras de respuesta en plantillas (teleportación D, entrelazamiento A, no-clonación D, amplitudes A); retiradas plantillas obsoletas «qubits para N estados». Repuesto: puerta unitaria genérica, Hadamard/entrelazamiento alternativos (`web_seed`).

### 325–336 (Modelització i Simulació)

**Alcance:** anàlisi dimensional, sistemes dinàmics discrets 1D, Markov/Leslie, mapes logístics i teranyina. Núcleo: equacions en diferències x_{n+1}=f(x_n).

| Id | Tipo | Ámbito | Estado |
|----|------|------------------|--------|
| 325 | FT | L1: homogeneidad dimensional | OK |
| 326 | FT | L1: dimensión de G (gravetat) | OK |
| 327 | MT | L2: solución afín x_{n+1}=αx_n+β | OK |
| 328 | MT | L2: punt fix f(x*)=x | OK |
| 329 | DT | L2: estabilitat \|f'(x*)\|<1 | OK |
| 330 | DT | L2: mapa logístic (punt fix 1−1/μ) | OK |
| 331 | FC | L2: x_{n+1}=x_n/3+2^n → x_2=22/9 | OK |
| 332 | FC | Mapa teranyina p_n=(c−a)−p_{n−1} | OK |
| 333 | MC | L3: Markov fila-estocàstica | OK |
| 334 | MC | L3: distribució estacionària π=πP | OK |
| 335 | DC | L3: Leslie / radi de Perron | OK |
| 336 | DC | Recurrencia afín: x_{n+1}=0,5x_n+3, x_0=2 → x_3=5,5 | OK (antes Euler/EDO → repuesto) |

**Repuesto:** f(x)=r·x−x³ (bifurcacions, Parcial 2). **Fora del banco:** validació de simuladors, llistes d’esdeveniments, Monte Carlo (→ MN 217–218).

### 337–348 (Sistemes Distribuïts i el Núvol)

**Alcance:** sistemes distribuïts i núvol — replicación, IaaS/PaaS/SaaS, VPC, S3/EBS, RDS/DynamoDB, Redis, auto scaling, ELB, Lambda, Docker/Kubernetes.

| Id | Tipo | Ámbito | Estado |
|----|------|----------------------|--------|
| 337 | FT | Replicación / disponibilidad | OK |
| 338 | FT | Modelo **IaaS** | OK |
| 339 | MT | CAP — trade-off con partición | OK |
| 340 | MT | Consistencia eventual | OK |
| 341 | DT | Teorema CAP | OK |
| 342 | DT | Tríada **CIA** | OK |
| 343 | FC | Objetos en **S3** (buckets) | OK |
| 344 | FC | Disponibilidad MTBF/MTTR ≈ 99,6% | OK |
| 345 | MC | **AOF** vs RDB (durabilidad) | OK |
| 346 | MC | **EC2** vCPU totales | OK |
| 347 | DC | **multi-AZ** / HA | OK |
| 348 | DC | **ALB** capa 7 | OK |

**Repuesto:** VPC, pod Kubernetes, Lambda serverless.

### 349–360 (Xarxes Neuronals i Aprenentatge Profond)

**Alcance:** redes profundas (CNN, atención, dropout, batch norm, LSTM, residual, softmax, parámetros de capas). **Sin ML genérico** (epoch, validación cruzada, GD → Aprenentatge Computacional 241–252). **Sin meta-análisis** (→ Ciències de la Salut 409–420).

| Id | Tipo | Ámbito | Estado |
|----|------|------|--------|
| 349 | FT | Batch normalization | OK |
| 350 | FT | Mecanismo de atención | OK |
| 351 | MT | Conexión residual (skip connection) | OK (antes «Ambas») |
| 352 | MT | Self-attention | OK |
| 353 | DT | LSTM (secuencias con memoria) | OK (antes meta-análisis) |
| 354 | DT | Dropout en entrenamiento | OK |
| 355 | FC | Softmax (logits → probabilidades) | OK |
| 356 | FC | Max-pooling 2×2, stride 2 → salida 2×2 | OK |
| 357 | MC | ReLU(0)=0 | OK |
| 358 | MC | Kernel 3×3, 1 canal → 9 parámetros | OK (antes min x+y) |
| 359 | DC | Capa densa 10→5 con sesgo → 55 | OK |
| 360 | DC | softmax([0,0]) → [0.5, 0.5] | OK |

**Cambios:** eliminadas preguntas fuera de materia (meta-análisis, optimización lineal); plantillas `dataset_480` reducidas a 12 coherentes con CSV; repuesto: conv/stride, Transformer, capa densa 64→32.

### 361–372 (Anàlisi de Dades Financeres)

**Alcance:** ingeniería financiera — opciones, carteras, modelos continuos, gestión de riesgo, securitización; árbol binomial, frontera media-varianza, GBM, VaR/TVaR, payoffs call/put/collar.

**Alcance (IEF):** ingeniería financiera, **opciones** (payoff call/put), **carteras** (Sharpe, beta, CAPM, covarianzas), tipos de interés y **valor presente**, varianza, **VaR** (percentil 1%). **Fuera del banco:** macro (PIB, deflactor, Keynes, Gini, consumidor) → no aparecen en el curso; series ARIMA/GARCH en profundidad → **373+** Anàlisi de Dades Temporals.

| Id | Tipo | Ámbito | Estado |
|----|------|------------------------|--------|
| 361 | FT | Introducción — qué es la ingeniería financiera | OK (antes PIB real) |
| 362 | FT | Opciones — payoff **call** max(S−K,0) | OK (antes teoría consumidor) |
| 363 | MT | Portfolio — ratio de **Sharpe** | OK |
| 364 | MT | Portfolio — matriz de **covarianzas**  | OK (antes Gini) |
| 365 | DT | Beta / sensibilidad al mercado | OK |
| 366 | DT | **CAPM** — interpretación de beta | OK |
| 367 | FC | Tipo de interés simple (r en modelos) | OK |
| 368 | FC | Volatilidad σ → varianza σ² | OK |
| 369 | MC | Beta × movimiento del mercado | OK |
| 370 | MC | **VaR 99%** — percentil 1%  | OK (antes multiplicador keynesiano) |
| 371 | DC | **Valor presente** 110€ al 10% → 100€ | OK (antes precio real/inflación) |
| 372 | DC | Opciones — payoff **put** max(K−S,0) | OK (antes deflactor PIB) |

**Repuesto:** Sortino, CVaR/TVaR, árbol binomial, covered call/collar (GARCH → repuesto en 373+).

### 373–384 (Anàlisi de Dades Temporals)

**Alcance:** series temporales financieras — ADF, diferenciación, ACF, ARIMA, GARCH.

**Alcance:** autocorrelación, **raíz unitaria** / ADF, estacionariedad AR(1), horizonte de predicción, **media móvil**, **diferenciación** (d=1), tendencia lineal, órdenes AR. **Sin** EDO (∫cos x), SQL (`MAX`), ni beta/CAPM (→ Financeres 361–372).

| Id | Tipo | Ámbito | Estado |
|----|------|------|--------|
| 373 | FT | Autocorrelación (retardo) | OK |
| 374 | FT | Raíz unitaria / no estacionariedad | OK (enunciado aclarado) |
| 375 | MT | Ventana de predicción (horizonte) | OK |
| 376 | MT | AR(1) estacionario: \|φ\| < 1 | OK |
| 377 | DT | Test de Dickey-Fuller | OK |
| 378 | DT | Media móvil (ventana deslizante) | OK |
| 379 | FC | Diferenciar serie n=100 → 99 obs | OK (antes ARIMA vago) |
| 380 | FC | Media [10,20,30] → 20 | OK |
| 381 | MC | Primera diferencia [5,8,12] → 4 | OK (antes dy/dx=cos x) |
| 382 | MC | Tendencia lineal en t=3 → 7 | OK |
| 383 | DC | AR(2): 2 coeficientes AR | OK |
| 384 | DC | MA orden 2 en t=5 → 9 | OK |

**Repuesto:** SARIMA, estacionariedad (definición), descomposición tendencia+estacional+ruido, GARCH, retardo estacional 12.

### 385–396 (Anàlisi Topològica de Dades)

**Alcance (TDA):** homología persistente, diagrama birth–death, filtración **Vietoris-Rips**, números de **Betti** (β₀ componentes, β₁ ciclos), **símplices** (0/1/2), persistencia death−birth, complejo de **Čech**. Sin PCA/regresión como definición central ni ML (matriz de confusión).

| Id | Tipo | Ámbito | Estado |
|----|------|------|--------|
| 385 | FT | Diagrama de persistencia | OK |
| 386 | FT | β₁ → ciclos/agujeros 1D | OK |
| 387 | MT | Coordenada **birth** | OK |
| 388 | MT | Filtración Rips al aumentar ε | OK |
| 389 | DT | Homología persistente (multiescala) | OK |
| 390 | DT | Barra: death−birth = persistencia | OK (antes β₁ duplicado) |
| 391 | FC | 2-símplice → 3 vértices | OK (antes 3-símplice Teoria) |
| 392 | FC | 1-símplice → 2 vértices | OK (antes 0-símplice duplicado) |
| 393 | MC | Persistencia 4−1 = 3 | OK |
| 394 | MC | β₀ = 2 componentes | OK |
| 395 | DC | Complejo de Čech | OK |
| 396 | DC | 2-símplice = triángulo | OK (antes β₀ duplicado) |

**Repuesto:** 0-símplice, 1-símplice (definición), 3-símplice, β₀ interpretación.

### 397–408 (Internet de les Coses)

**Alcance:** arquitectura IoT (gateway, escalabilidad, conectividad), **MQTT** (pub/sub, QoS, vs HTTP), actuador, redes (/24), cálculos de telemetría (mensajes, lecturas, caudal, latencia). **Sin** duplicar SDN/AWS en profundidad (→ 337–348).

| Id | Tipo | Ámbito | Estado |
|----|------|------|--------|
| 397 | FT | Gateway sensores ↔ nube | OK |
| 398 | FT | Escalabilidad (muchos dispositivos) | OK |
| 399 | MT | Protocolo **MQTT** | OK |
| 400 | MT | Conectividad en IoT | OK |
| 401 | DT | MQTT ligero vs HTTP en telemetría | OK |
| 402 | DT | **Actuador** (acciones físicas) | OK (antes sensor duplicado) |
| 403 | FC | Hosts útiles en red **/24** → 254 | OK |
| 404 | FC | MQTT: **3** niveles QoS | OK |
| 405 | MC | 2 msg/s × 5 min → **600** mensajes | OK |
| 406 | MC | 1 lectura/s × 5 min → **300** lecturas | OK |
| 407 | DC | 200 B × 50 msg/s → **10 KB/s** | OK |
| 408 | DC | Latencia 10 ms + 5 ms → **15 ms** | OK |

**Repuesto:** CoAP (UDP), seguridad en dispositivos limitados, LoRaWAN, sensor (definición).

### 409–420 (Mètodes d'Anàlisi en Ciències de la Salut)

**Alcance:** epidemiología clínica — **VPP**, sensibilidad/especificidad, **meta-análisis** (heterogeneidad), mediación, **ECA** (aleatorización), **NNT**, **odds ratio**, cálculos (especificidad, VPP con Bayes, verdaderos positivos). **Sin** reutilizar OR/riesgo relativo de Financeres/IoT.

| Id | Tipo | Ámbito | Estado |
|----|------|------|--------|
| 409 | FT | Valor predictivo positivo (VPP) | OK |
| 410 | FT | VPP bajo con prevalencia baja | OK |
| 411 | MT | Heterogeneidad en meta-análisis | OK |
| 412 | MT | Análisis de mediación | OK |
| 413 | DT | Definición de sensibilidad | OK |
| 414 | DT | Aleatorización en ECA | OK |
| 415 | FC | Meta-análisis: 5 estudios | OK |
| 416 | FC | Especificidad 190/200 sanos → 0,95 | OK |
| 417 | MC | NNT = 5 | OK |
| 418 | MC | Odds ratio | OK |
| 419 | DC | VPP con prev 50%, Se/Sp 0,9 → ≈0,90 | OK |
| 420 | DC | Sensibilidad 0,9 × 100 enfermos → 90 VP | OK |

**Repuesto:** IC 95%, especificidad (definición), NNT=10, variantes VPP.

### 421–432 (Anàlisi de Dades en Astrofísica)

**Alcance:** astronomía gamma VHE (Li & Ma, on/off), cosmología H(z), ondas gravitacionales (blanqueamiento, Nyquist, ASD), Poisson. **Fuera del banco fijo:** fotometría clásica (paralaje, magnitudes, Stefan-Boltzmann).

| Id | Tipo | Ámbito | Estado |
|----|------|--------------|--------|
| 421 | FT | VHE E > 100 GeV (T3) | OK (reorientado) |
| 422 | FT | Bibliotecas de astronomía gamma | OK |
| 423 | MT | α on/off (Li & Ma) | OK |
| 424 | MT | Significancia Li & Ma | OK |
| 425 | DT | Blanqueamiento GW (T5) | OK |
| 426 | DT | Nyquist f_N = fs/2 (T5) | OK |
| 427 | FC | Poisson P(X=0), λ=4 | OK |
| 428 | FC | α = 1/3 (3 regiones off) | OK |
| 429 | MC | H(z=0) = H₀ (ΛCDM, T2) | OK |
| 430 | MC | v ≈ zc, z=0,02 (T2) | OK |
| 431 | DC | Mejora ASD O3/O1 ≈ 1,7 a 100 Hz (T5) | OK |
| 432 | DC | Poisson P(X=2), λ=4 | OK |

**Repuesto:** matched filter/SNR, neutrinos supernova; en plantillas.json: Hubble, Wien, HR, corrección K, redshift cosmológico (general/repuesto).

### 433–444 (Bioinformàtica)

**Alcance:** secuencias y genómica básica — **Hamming**, **k-mers** (n−k+1), **ADN** (4 bases), **BLAST**, **UPGMA**/filogenia, **alineamiento múltiple**, **codones** (64), **identidad**, **aminoácidos** (20). **Sin** PLN (resumen automático) ni **sistemas distribuidos** (nodos replicación).

| Id | Tipo | Ámbito | Estado |
|----|------|------|--------|
| 433 | FT | Distancia de Hamming | OK |
| 434 | FT | k-mer (subcadena contigua) | OK (antes «subsecuencia») |
| 435 | MT | 4 bases nitrogenadas (A,T,C,G) | OK |
| 436 | MT | BLAST (similitud local) | OK (antes resumen automático / PLN) |
| 437 | DT | UPGMA: distancias ultramétricas | OK |
| 438 | DT | Alineamiento múltiple (3+ secuencias) | OK |
| 439 | FC | 4³ = 64 codones | OK |
| 440 | FC | Hamming ATCG vs ATTG → 1 | OK |
| 441 | MC | % identidad en alineamiento | OK |
| 442 | MC | k=3, n=10 → 8 k-mers | OK |
| 443 | DC | 20 aminoácidos estándar | OK (antes duplicado 64 codones) |
| 444 | DC | n=100, k=3 → 98 k-mers solapados | OK |

**Repuesto:** transcripción, Levenshtein, k-mers n=1000 k=5, resumen automático (fuera de alcance), codón (teoría).

### 445–456 (Informació i Seguretat)

**Alcance (variedad):** cifrados clásicos (Vigenère, César), Bloom, RSA/firma sobre hash, esteganografía, hash, aritmética modular, fuerza bruta 2^n, salt, Diffie-Hellman, SHA-256. **Repuesto / ampliación:** AES (SubBytes, rondas), LFSR, CIA, Kerckhoffs, Hill, mínimo privilegio.

| Id | Tipo | Ámbito | Estado |
|----|------|--------|--------|
| 445 | FT | Vigenère: suma módulo alfabeto | OK (sustituye AES SubBytes) |
| 446 | FT | César: desplazamiento k mod 26 | OK |
| 447 | MT | Bloom: más k → menos FP teóricos | OK |
| 448 | MT | RSA: firma sobre hash | OK |
| 449 | DT | Esteganografía: ocultar existencia | OK (sustituye LFSR) |
| 450 | DT | Hash criptográfico unidireccional | OK |
| 451 | FC | (7·8) mod 13 = 4 | OK (sustituye rondas AES-128) |
| 452 | FC | 8 bits → 256 claves | OK |
| 453 | MC | Salt en almacenamiento de contraseñas | OK (sustituye bytes AES-128) |
| 454 | MC | Contraseña 8×26 → 26^8 | OK |
| 455 | DC | Diffie-Hellman: g^(ab) mod p | OK (sustituye duplicado hash/AES) |
| 456 | DC | SHA-256 → 256 bits salida | OK |

**Repuesto:** AES, LFSR, CIA, Kerckhoffs (`plantillas_repuesto_catalogo.py`).

### 241–252 (Aprenentatge Computacional)

**Alcance:** ML / pipeline de datos (batch, epoch, validación, sesgo-varianza, GD, entropía cruzada, partición train-test). **Sin redes neuronales** (capas, dropout, batch norm → Xarxes Neuronals 349–360).

| Id | Tipo | Ámbito | Estado |
|----|------|------|--------|
| 241 | FT | batch | OK |
| 242 | FT | overfitting (antes learning rate decay) | OK |
| 243 | MT | validación cruzada | OK |
| 244 | MT | bias-variance (opciones reescritas) | OK |
| 245 | DT | modelo predictivo | OK |
| 246 | DT | early stopping (sin distractores NN) | OK |
| 247 | FC | paso GD (w←w−η∂L/∂w) | OK |
| 248 | FC | actualizaciones = epochs × batches (2×8=16) | OK |
| 249 | MC | tamaño fold validación k=5, n=500 → 100 | OK |
| 250 | MC | precisión TP/(TP+FP) con TP=18, FP=2 → 0,9 | OK |
| 251 | DC | F1 desde P=0,6 y R=0,75 → 2/3 ≈ 0,667 | OK |
| 252 | DC | cross-entropy p=q=[1,0]→0 | OK |

**Cálculo (247–252):** GD · entrenamiento por batches · k-fold · precisión · F1 · entropía cruzada (sin regresión β ni partición 70/30 duplicada).

**Huecos opcionales (futuro):** aprendizaje supervisado vs no supervisado, regularización L1/L2, árboles/SVM/k-means, matriz de confusión (IA 211–213 ya cubre métricas de clasificación).

### 253–264 (Computació i Simulació d'Altes Prestacions)

**Alcance:** **OpenMP** (shared CPU), **OpenACC** (directivas offload), **CUDA** (GPU NVIDIA), **OpenMPI** (MPI en clúster); más Amdahl, speedup y eficiencia. Sin semáforo/mutex (sincronización OS → Fonaments/HPC genérico si se añade aparte).

| Id | Tipo | Ámbito | Estado |
|----|------|------|--------|
| 253 | FT | OpenMP (memoria compartida, pragma) | OK |
| 254 | FT | CUDA (kernels, GPU) | OK |
| 255 | MT | OpenACC (offload acelerador) | OK |
| 256 | MT | Open MPI / OpenMPI | OK |
| 257 | DT | pareja OpenMP↔shared, OpenMPI↔distributed | OK |
| 258 | DT | ley de Amdahl | OK |
| 259 | FC | speedup T₁/Tₚ (80 s → 20 s) | OK |
| 260 | FC | eficiencia E=S/p | OK |
| 261 | MC | CUDA warps (128 threads → 4 warps) | OK |
| 262 | MC | `mpirun -np 4` → 4 procesos MPI | OK |
| 263 | DC | speedup 16 nodos (64 s / 8 s → 8) | OK |
| 264 | DC | Amdahl s=0,1 → S_max=10 | OK |

**Huecos opcionales:** escalabilidad fuerte/débil explícita, cuello de botella, comparativa OpenACC vs CUDA a bajo nivel.

### 265–276 (Equacions en Derivades Parcials)

**Alcance:** notación (u_t, u_xx), tipos (parabólica/hipérbola/elíptica), CFL, condiciones iniciales, discriminante B²−4AC. Sin solapar EDO (133–144).

| Id | Tipo | Ámbito | Estado |
|----|------|------|--------|
| 265 | FT | ecuación de Burgers u_t+u·u_x=ν·u_xx | OK |
| 266 | FT | u_t temporal (calor) | OK |
| 267 | MT | tránsito u_t+c·u_x → hiperbólica | OK |
| 268 | MT | condición CFL (estabilidad DF) | OK |
| 269 | DT | elíptica (Laplace) | OK |
| 270 | DT | u_tt=c²u_xx → hiperbólica | OK |
| 271 | FC | Δx en [0,1] con 11 nodos → 0,1 | OK |
| 272 | FC | calor parabólica → 1 CI en t=0 | OK |
| 273 | MC | tránsito f(x−ct): desplazamiento c·Δt=2 | OK |
| 274 | MC | Courant onda σ=cΔt/Δx → 0,5 | OK |
| 275 | DC | B²−4AC>0 → hiperbólica | OK |
| 276 | DC | CFL calor r=αΔt/Δx² → 0,5 (sustituye duplicado 275) | OK |

**Corregido:** 275 y 276 eran la misma pregunta con respuestas distintas (C vs D). **Huecos:** formulación débil / H¹₀, Laplaciano 2D, B²−4AC<0 elíptica, 2 CI ondas u_tt (solo en 270 teórica).

### 277–288 (Física, Abstracció i Computació)

**Alcance:** **solo física**. Temas del bloque: **cinemática · dinámica · energía · óptica · ondas · electricidad · termodinámica · campos · reacciones** (pares acción-reacción).

| Id | Tipo | Ámbito | Estado |
|----|------|------|--------|
| 277 | FT | cinemática: velocidad media | OK |
| 278 | FT | reacciones: 3ª ley Newton | OK |
| 279 | MT | dinámica: 2ª ley F=m·a | OK |
| 280 | MT | electricidad: Ohm V=I·R | OK |
| 281 | DT | campos: definición de E | OK |
| 282 | DT | energía: conservación mecánica | OK |
| 283 | FC | electricidad: V=20 V | OK |
| 284 | FC | ondas: v=λ·f → 10 m/s | OK |
| 285 | MC | termodinámica: pV=nRT ≈ 2493 J | OK |
| 286 | MC | energía: E_c=9 J | OK |
| 287 | DC | cinemática: a=3 m/s² | OK |
| 288 | DC | óptica: reflexión 35° | OK |

**Huecos opcionales:** 1ª ley Newton (inercia), refracción Snell, campo magnético B, potencia P=VI.

### 457–468 (Teoria de Jocs)

**Alcance:** estrategias dominantes y maximin, Nash, equilibrio correlacionado, juegos repetidos (SPE), suma cero, conteo de perfiles 2×2 y 3×4. Redacción genérica (sin temas/prácticas de curso).

| Id | Tipo | Ámbito | Estado |
|----|------|--------|--------|
| 457 | FT | estrategia estrictamente dominante | OK |
| 458 | FT | maximin (Wald) | OK |
| 459 | MT | equilibrio correlacionado | OK |
| 460 | MT | equilibrio de Nash | OK |
| 461 | DT | juego repetido horizonte infinito / δ | OK |
| 462 | DT | repetido finito: Nash estático vs SPE | **Corregido** (antes «siempre SPE») |
| 463 | FC | estrategias puras por jugador en 2×2 | OK (sustituye «¿cuántos jugadores?») |
| 464 | FC | máximo de Nash puros en 2×2 (=4) | OK |
| 465 | MC | perfiles puros en 2×2 (=4) | OK |
| 466 | MC | suma cero: pago columna | OK |
| 467 | DC | perfiles 3×4 (=12) | OK (sustituye duplicado 2×2) |
| 468 | DC | maximin: max de mínimos por fila | OK |

**Corregido crítico:** id **462** — repetir el Nash del stage-game en un juego **finito** no es siempre SPE (p. ej. dilema del prisionero con backward induction).

**Repuesto útil en catálogo:** SPE formal, Nash en puras (ya cubiertos en 460/462).

### 469–480 (Visió per Computador)

**Alcance:** CNN (convolución, ReLU, pooling), IoU, padding, descriptores, RGB, tamaño de imagen, salidas conv (8×8, 32×32, stride 2). Sin duplicar ML genérico (→ Aprenentatge Computacional) ni arquitecturas profundas avanzadas (→ Xarxes Neuronals).

| Id | Tipo | Ámbito | Estado |
|----|------|--------|--------|
| 469 | FT | Kernel convolución: patrones locales | OK |
| 470 | FT | ReLU: max(0,·) | OK |
| 471 | MT | Max pooling: menos resolución, invarianza | OK |
| 472 | MT | IoU en detección/segmentación | OK |
| 473 | DT | Padding: bordes y tamaño de salida | OK |
| 474 | DT | Descriptor SIFT/ORB | OK |
| 475 | FC | RGB → 3 canales | OK |
| 476 | FC | 640×480 → 307200 píxeles | OK |
| 477 | MC | 8×8, k=3, s=1 → 6×6 | OK |
| 478 | MC | IoU: inter=50, unión=150 → 1/3 | OK |
| 479 | DC | 32×32, k=3 → 30×30 | OK |
| 480 | DC | 10×10, k=3, s=2 → 4×4 | OK |

**Repuesto:** píxel, histograma (`plantillas_repuesto_catalogo.py`).

---

## Cierre banco 480/480 (2026-06-03)

- **Juego:** partida en **modo libre** (`Juego/juego_cuestionario.py`): banco **1 = dataset revisado (MODO FINAL)**; bancos **2–3 = plantillas (MODO BETA)**. **Historia** y **feedback** (menú o tecla **F**) operativos en consola.
- **Artefactos sincronizados:** `plantillas.json`, `criterios_clasificacion_materia.csv`, `plantillas_repuesto_catalogo.py`, `Memoria_TFG.md` §5.1 y §6.1; Word en `Entrega/Memoria/`.
- **Opcional futuro:** id **83** (vanishing gradient en Càlcul DV) podría moverse a Xarxes Neuronals; pulido distractores según auditoría.

---

## Alertas operativas

- Tras revisar un bloque, **ladder** (F→M→D en teoría y cálculo): `python Files/balance.py ordenar-ladder` (no renumerar Id ni tocar A-D). Ampliar banco: `python Files/ampliar_dataset_480.py`.
- `Files/dataset_plantillas_cli.py` / `recategorizar_y_equilibrar.py`: confirmar `Id` y materia antes de `--inplace`.
- Tras `exportar_criterios_clasificacion_materia.py`, revisar desambiguación en criterios.
- `plantillas.json` puede tener entradas históricas `"(variante)"`; limpieza puntual si molesta.
- **Plantillas repuesto:** subtemas que **no** aparecen en las 12 preguntas del CSV → `uso: repuesto` en `plantillas.json` (antes `reserva` en Visualització 3D). Catálogo editable: `Files/plantillas_repuesto_catalogo.py`. Sincronizar tras revisar una materia: `python Files/sincronizar_plantillas_repuesto.py --inplace` (o `--dry-run`). El pool de regeneración (`dataset_pipeline`, `crear_borrar_preguntas`) usa `general` + `repuesto`.
- **Distractores (A–D):** `python Files/Scripts/mantenimiento.py auditar-distractores` (salida en consola; `--json` opcional). Revisa opciones vacías/duplicadas, «Ninguna de las anteriores», filtración de la correcta y desbalance de longitud.
- **Scripts:** [`Files/Scripts/README.md`](../Files/Scripts/README.md) — comandos seguros vs `Files/Archivo/`. El CSV está protegido por `utils_banco_cerrado.py` (override: `TFG_PERMITIR_CSV=1`).
- **Mantenimiento plantillas** (banco cerrado): `limpiar_plantillas.py` → `inyectar_dataset_en_plantillas.py` → `sincronizar_plantillas_repuesto.py`. **No** `balance.py conservador` ni regeneradores.

---

## Comandos útiles

```powershell
$env:PYTHONIOENCODING="utf-8"
python Files/fix_final_materias.py
python Files/sync_plantillas_materias.py --inyectar
python -c "import sys;sys.path.insert(0,'Files');from balance_lib import ejecutar_validar;ejecutar_validar(detalle=False)"
```

### Scripts de mantenimiento (cuándo usar cada uno)

| Script | Uso |
|--------|-----|
| `fix_final_materias.py` | **Principal:** reclasificación por contenido, bancos fijos (POO, PROB, CN, Grafs…), fillers, guardado y validación. |
| `sync_plantillas_materias.py` | Alinea `plantillas.json` con las mismas reglas; `--inyectar` vuelca el CSV. |
| `balance.py validar` / `reordenar` | Solo metadatos y orden canónico (sin regenerar enunciados). |
| `limpiar_duplicados_csv.py` | Solo quita duplicados exactos (materia+enunciado); falla si ≠480 filas. |
| `reparar_materia_algoritmes.py` | Legacy: movimientos por Id (ya aplicados si el CSV está al día). |
| `revisar_castellano_csv.py` | Ortografía y parches por Id **fuera** de bloques ya cerrados; no usar en 42–50 ni 91–100. |

**No ejecutar** `balance.py conservador` / `aplicar_clasificacion_optima.py --inplace` sobre el banco ya revisado (regeneran desde plantillas y pueden deshacer cambios).

## Ficheros habituales al revisar

- `Data/Preguntas.csv`
- `Data/plantillas.json`
- `Data/criterios_clasificacion_materia.csv`
- `Files/fix_final_materias.py`

---

## Checklist al retomar

1. Revisar sección **Pendientes** arriba.
2. Tras cambios, validar con `ejecutar_validar`.
3. Actualizar **`revision_manual_banco.md`** (detalle) y [`ESTADO.md`](ESTADO.md) (resumen + bitácora).
4. Si aplica: `fix_final_materias.py` + `sync_plantillas_materias.py --inyectar`.
