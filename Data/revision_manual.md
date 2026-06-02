# Revisión manual del banco de preguntas

Trazabilidad de la revisión manual de `Data/Preguntas.csv`. Actualizar este único fichero al cerrar cada tramo.

**Última actualización:** 2026-06-02  
**Progreso:** **240 / 480 (50 %)** — banco **12 preguntas/materia**, estructura 2FT 2MT 2DT 2FC 2MC 2DC  
**Aprobación usuario:** ids **1–240** (materias 1–20 del listado) — **cerrado**; siguiente tramo **241+**  
**Validación habitual:** `python -c "import sys; sys.path.insert(0,'Files'); from balance_lib import ejecutar_validar; ejecutar_validar(detalle=False)"` → **OK**

| Ids | Estado | Materias (listado `Data/listado_materias.csv`) |
|-----|--------|------------------------------------------------|
| **1–240** | **Aprobado (usuario)** | Àlgebra Lineal … **Optimització** (20 materias; detalle en §1–240) |
| 241–480 | Pendiente | Aprenentatge Computacional … Visió per Computador (20 materias) |

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
- **Dades Complexes (161–170):** apuntes Puig: modelo lineal, L2/MCO, R², homocedasticidad, test F, residuo/predicción, **bootstrap** (remuestreo con reemplazo), SSE, GLM logística. Reserva: devianza, ML=MCO, extrapolación, R²=0. Sin train/test.
- **POO:** solo Python en cálculo; banco en `Files/fix_final_materias.py` (`_poo_banco`).
- **Probabilitat:** una sola Bayes (id 90); sin duplicados binomial/unión/varianza.
- **EDO:** sin Wronskiano; id 120 PVI (no paralelepípedo).
- **Modelització i Inferència:** sin RL; IC, error tipo I, inferencia coherente.
- **Intel·ligència Artificial (171–180):** temario UAB sin duplicar A*/Dijkstra (eso va en Grafs). Teoría: Turing, búsqueda informada (heurística admisible, sin nombrar A*), no informada, local, minimax. **Cálculo:** recall, hojas árbol, precisión, minimax, P∧Q.
- **Optimització (191–200):** alineado con UAB (`Optimitzacio/Lineal` + `No Lineal`). **Lineal:** simplex, dual, holguras, KKT. **No lineal:** Newton (f', f''), Hessiano, convexidad. **Prácticas:** glpk/Simplex, Newton, golden/brent, BFGS, Nelder-Mead. Sin gradiente descendente genérico (no en prácticas).

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

Teoría: trapecio, redondeo, truncamiento, Newton-Raphson, **Romberg** (PDF 02).  
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

Alineado con apuntes **Pere Puig**: regresión L2/MCO, residuos, test F, GLM logit, **bootstrap**; sin train/test. **OK**

### 171–180 (Intel·ligència Artificial)

Temario UAB: Turing, búsquedas (informada/no informada/local), patrones estadístico/estructural, minimax, lógica proposicional. **Sin A*/Dijkstra** (van en Grafs 51–60). F/M/D **3/4/3** (id 172 Difícil; id 178 accuracy). Ladder: `python Files/balance.py ordenar-ladder`. **OK**

### 217–228 (Mètodes Numèrics i Probabilístics)

**Teoría UAB (PDF 01–19):** integración (01–04), Monte Carlo (05–06), EDO Euler/Taylor/RK (09–12), multipaso (14–15). **Sin Metropolis ni PBC.**

| PDF | Tema | Banco (ids) |
|-----|------|-------------|
| 01–02, 04 | Trapecio, Romberg, Simpson | **71–80** (+ **75** Romberg) |
| 05–06 | Monte Carlo | **217–218, 223–224, 226** |
| 09–11 | Euler, Taylor, RK4 | **219–220, 222, 225, 227–228** |
| 14–15 | Multipaso lineal | **222** |
| 16–19 | Estabilidad, stiff, PVF | reserva |

Cálculo revisado: escalado \(1/\sqrt{N}\), paso Euler (Practica 3), RK4 con 4 evaluaciones de \(f\). **OK**

### 229–240 (Optimització)

Alineado con carpeta UAB `Optimitzacio/` (**Lineal:** Simplex, dual, holguras, KKT; **No lineal:** Newton, Hessiano, convexidad). Sin gradiente descendente genérico (no en prácticas del curso).

Cálculo: mínimos cuadráticos, holguras, Hessiano \(2I\), complementariedad KKT. **OK**

**Cambios destacados en 157–240:** Complexa/Fourier; ADC Puig + bootstrap; IA sin duplicar A*; MN según PDF UAB; Optimització Newton/Simplex/KKT. **Bloque 1–240 aprobado por usuario.**

---

## Pendientes

1. **Id 25** (Fonaments): reforzar dificultad o sustituir pregunta de CPU.
2. **Id 104** (BDR): valorar `DELETE` en Difícil vs JOIN / integridad referencial.
3. **Plantillas EDO:** comprobar plantilla «autovalores 2×2» en sección EDO (no en CSV 111–120).
4. **Siguiente tramo:** ids **241–252** (Aprenentatge Computacional).

---

## Alertas operativas

- Tras revisar un bloque, **ladder** (F→M→D en teoría y cálculo): `python Files/balance.py ordenar-ladder` (no renumerar Id ni tocar A-D). Ampliar banco: `python Files/ampliar_dataset_480.py`.
- `Files/dataset_plantillas_cli.py` / `recategorizar_y_equilibrar.py`: confirmar `Id` y materia antes de `--inplace`.
- Tras `exportar_criterios_clasificacion_materia.py`, revisar desambiguación en criterios.
- `plantillas.json` puede tener entradas históricas `"(variante)"`; limpieza puntual si molesta.

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
| `limpiar_duplicados_csv.py` | Solo quita duplicados exactos (materia+enunciado); falla si ≠400 filas. |
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
3. Actualizar **este** `revision_manual.md` (tabla de progreso + bloque nuevo).
4. Si aplica: `fix_final_materias.py` + `sync_plantillas_materias.py --inyectar`.
