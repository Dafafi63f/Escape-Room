# Revisión manual del banco de preguntas

Trazabilidad de la revisión manual de `Data/Preguntas.csv`. Actualizar este único fichero al cerrar cada tramo.

**Última actualización:** 2026-06-01  
**Progreso:** 130 / 400 (~32,5 %)  
**Validación habitual:** `python -c "import sys; sys.path.insert(0,'Files'); from balance_lib import ejecutar_validar; ejecutar_validar(detalle=False)"` → **OK**

| Ids | Estado | Materias |
|-----|--------|----------|
| 1–30 | Revisado | Àlgebra Lineal, Càlcul en una Variable, Fonaments de Computadors |
| 31–130 | Revisado | Iniciació … Modelització i Inferència (13 materias) |
| 131–400 | Pendiente | Desde Tècniques de Disseny d'Algoritmes |

---

## Decisiones globales (todas las sesiones)

- `gradiente` restringido a `Càlcul en Diverses Variables` (eliminado de `Optimització` en criterios).
- `entropía` restringida a `Teoria de la Informació` (y eventualmente `Física, Abstracció i Computació` si se añade contenido).
- Menos preguntas genéricas de `bits` fuera de materias informacionales.
- No inyectar en `plantillas.json` enunciados con sufijo `"(variante N)"`.
- **Programari vs HPC / Fonaments:** terminal, shell, `pipe`, `git`, `gcc` en Programari; pipeline en Fonaments (no en Programari).
- **Grafs:** sin TSP/Floyd-Warshall ni NoSQL; teoría de grafos + conteos.
- **POO:** solo Python en cálculo; banco en `Files/fix_final_materias.py` (`_poo_banco`).
- **Probabilitat:** una sola Bayes (id 90); sin duplicados binomial/unión/varianza.
- **EDO:** sin Wronskiano; id 120 PVI (no paralelepípedo).
- **Modelització i Inferència:** sin RL; IC, error tipo I, inferencia coherente.

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

### 21–30 (Fonaments de Computadors)

- `21`–`24`, `26`, `28`–`30`: **OK**
- `24`: LRU/caché
- `25`: **Pendiente** — «¿Qué es la CPU?» muy básica para Difícil; subir complejidad o sustituir.
- `27`: **Resuelto** (2026-06-01) — pipeline 5 etapas, 100 instrucciones, 104 ciclos (antes latencia red).

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

### 31–40 (Iniciació a la Programació)

Python introductorio: `if`, `while`, `for`, scope, listas, `len`, `%`, índices.  
Fuera del bloque (Tècniques/POO): algoritmo genérico, LIFO, complejidad BST, Fibonacci.  
**OK**

### 41–50 (Programari de Sistema)

Teoría: shell, stdout, pipe, `git commit`, compilador. Cálculo: `cd ..`, `touch`, `ls -a`, `ls \| wc -l`, `gcc -o`.  
**OK** (sin semáforos/hilos → HPC)

### 51–60 (Grafs)

Teoría: \(K_n\), árbol, euleriano, circuito euleriano, matching bipartito.  
Cálculo: grado/aristas \(K_5\), componentes, caminos \(K_4\).  
**OK** (ajustes 54, 57 en sesión previa)

### 61–70 (Càlcul en Diverses Variables)

Diferenciabilidad, gradiente, coordenadas, integrales dobles, jacobiano. **OK**

### 71–80 (Càlcul Numèric)

Teoría: trapecio, redondeo, punto fijo, Newton-Raphson, orden convergencia.  
Cálculo: error relativo, Newton \(x_1\), bisección, Simpson, \(O(h^2)\) trapecio.  
**OK** (`fix_final_materias.py`)

### 81–90 (Probabilitat)

Teoría: \(E(X)\), independencia, condicional, unión, probabilidad total.  
Cálculo: varianza constante, binomial, Poisson, moneda, única Bayes (90 → 0,18).  
**OK**

### 91–100 (POO)

| Id | Tipo | Contenido |
|----|------|-----------|
| 91–95 | Teoría | Herencia, encapsulamiento, polimorfismo, acoplamiento, cohesión |
| 96–100 | Cálculo | Python: `C()`, `self`, `a is b`, `c.v`, `__init__` |

**OK** (sin Java)

### 101–110 (Bases de Dades Relacionals)

Teoría: `GROUP BY`, FK, `HAVING`, `DELETE`, normalización (105; antes 2PL).  
Cálculo: claves compuestas, producto cartesiano, candidatas, `COUNT(*)`.  
**OK** — opcional: id 104 `DELETE` en Difícil (contenido fácil)

### 111–120 (EDO)

| Id | Cambio |
|----|--------|
| 112 | Wronskiano → orden de una EDO |
| 120 | Paralelepípedo → PVI \(y''+y=0\), \(y(\pi)\) |

Resto: Runge-Kutta, autónoma, Euler, rigidez, CI, \(y'=y\), \(y''+y=0\). **OK**

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

## Pendientes

1. **Id 25** (Fonaments): reforzar dificultad o sustituir pregunta de CPU.
2. **Id 104** (BDR): valorar `DELETE` en Difícil vs JOIN / integridad referencial.
3. **Plantillas EDO:** comprobar plantilla «autovalores 2×2» en sección EDO (no en CSV 111–120).
4. **Siguiente tramo:** ids **131–160** (Tècniques de Disseny d'Algoritmes y siguientes).

---

## Alertas operativas

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
