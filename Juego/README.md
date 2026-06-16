# Juego — cuestionario MATCAD

Dos interfaces del mismo juego, **en paralelo** hasta que la versión gráfica sea estable:

| Lanzador | Interfaz | Requisitos |
|----------|----------|------------|
| [`juego_consola.py`](juego_consola.py) | Terminal (completa) | Python 3.10+, solo stdlib |
| [`juego_grafico.py`](juego_grafico.py) | Pygame (en desarrollo) | `pip install -r requirements.txt` |

La lógica compartida (datos, reglas, motor de partida) vive en [`Comun/`](Comun/README.md). Cada interfaz añade su capa: [`Consola/`](Consola/README.md) (terminal) y [`Grafico/`](Grafico/README.md) (pygame).

## Estrategia de migración

**Ahora:** mantener **ambas versiones operativas**. Cualquier cambio en reglas, datos o motor debe seguir funcionando en terminal y gráfico.

**Más adelante:** cuando `Grafico/` alcance paridad funcional y estabilidad, se eliminará la interfaz terminal (`juego_consola.py`, `entrada_teclas.py`, `entrada_menu.py`, `consola.py`, menús por teclado, build `.exe` de consola, etc.) y solo quedará la versión gráfica. El paquete [`Comun/`](Comun/README.md) se conservará; lo específico de terminal no.

Detalle: [`Grafico/README.md`](Grafico/README.md#estrategia-de-migración).

| Elemento | Descripción |
|----------|-------------|
| [`juego_consola.py`](juego_consola.py) | Lanzador terminal: menú principal y arranque de modos |
| [`juego_grafico.py`](juego_grafico.py) | Lanzador pygame (prototipo; ver [`Grafico/README.md`](Grafico/README.md)) |
| [`Comun/`](Comun/README.md) | Dominio compartido (`from Comun...`) |
| [`Consola/`](Consola/README.md) | UI terminal y orquestación de modos en consola |
| [`Grafico/`](Grafico/README.md) | Interfaz pygame (ratón; teclado solo para texto) |
| [`Informes/`](Informes/README.md) | Informes `.txt` de partidas (local, gitignored) |
| [`Feedback/`](Feedback/README.md) | Copias locales de avisos al creador (local, gitignored) |
| [`Tests/`](../Tests/README.md) | Pruebas unitarias (suite unificada en la raíz) |
| [`build_exe_onefile.ps1`](build_exe_onefile.ps1) | Genera `juego_consola.exe` con PyInstaller |

## Ejecutar

**Terminal (versión completa):**

```bash
python Juego/juego_consola.py
```

**Gráfico:**

```bash
pip install -r requirements.txt
python Juego/juego_grafico.py
```

Datos en [`../Data/README.md`](../Data/README.md).

## Terminal — jugar

Al arrancar, el lanzador muestra un **tutorial breve** de foco de teclado (hay que hacer clic en la línea `>>` de la terminal para que las teclas respondan). Detalle en [`Consola/entrada_teclas.py`](Consola/entrada_teclas.py) y [`Consola/entrada_menu.py`](Consola/entrada_menu.py).

### Modos

| Modo | Estado | Descripción |
|------|--------|-------------|
| **Libre** | Implementado | Partida configurable, filtros por curso/semestre/grupo/nivel, informes al cerrar |
| **Libre (gráfico)** | v1 | Bloque 5/10/15, arcade, opciones clicables — [`Grafico/README.md`](Grafico/README.md) |
| **Historia** | Implementado (v1) | Examen balanceado según histórico de qualificacions |
| **Feedback** | Implementado (v1) | Asistente para enviar bug, sugerencia u otro aviso al creador |

Detalle de bancos de preguntas, puntuación, dificultad progresiva y arquitectura: [`Consola/README.md`](Consola/README.md).

### Controles (resumen)

| Tecla | Acción |
|-------|--------|
| **H** | Ayuda contextual del momento |
| **F** | Feedback rápido (sin borrar la pantalla; mantiene el contexto) |
| **Esc** | Pausa; en campos de texto con «atrás», volver |
| **Supr** | Atrás en menús; en texto, borrar caracteres |
| **Ctrl+C** | Cerrar el programa |

Detalle completo: [`Consola/entrada_teclas.py`](Consola/entrada_teclas.py), [`Consola/entrada_menu.py`](Consola/entrada_menu.py) y [`Consola/README.md`](Consola/README.md).

### Portabilidad del teclado

| Entorno | Comportamiento |
|---------|----------------|
| **Windows** (recomendado) | Tecla a tecla con `msvcrt`: H, F, Esc, Supr, dígitos y A–D responden al instante sin pulsar Enter |
| **Linux / macOS** | Fallback por línea (`input()`): hay que escribir la opción y pulsar **Enter**; H/F/Esc no funcionan igual |

El `.exe` y la terminal de Windows son el entorno previsto para jugar y para la defensa del TFG. En otros SO el juego arranca, pero la UX de menús es limitada. Implementación: [`Consola/entrada_teclas.py`](Consola/entrada_teclas.py).

## Ejecutable (opcional)

### Requisitos

| Requisito | Notas |
|-----------|--------|
| Windows | El build usa PowerShell |
| Python 3.10+ | Comando `python` en el PATH |
| pip | Instala PyInstaller si falta |
| PyInstaller | Lo instala el script: `pip install pyinstaller` |
| `../Data/` | Se empaqueta entero si no hay `Juego/Data/` ni CSV sueltos en `Juego/` |

### Comando

```powershell
cd Juego
.\build_exe_onefile.ps1
```

Genera `juego_consola.exe` en esta carpeta. Incluye `Data/` del proyecto (preguntas, materias, plantillas, histórico CSV). Los informes se escriben en `Informes/` **junto al `.exe`** al ejecutarlo.

### Artefactos de build

Tras un build correcto, `build_exe_onefile.ps1` **borra** `build/`, `juego_consola.spec` y `dist/` si existen. Solo queda `juego_consola.exe` en `Juego/`.

| Elemento | En git |
|----------|--------|
| `juego_consola.exe` | Ignorado en `.gitignore` |
| `build/`, `*.spec` | No se versionan; el script de build los elimina al terminar |

## Limpieza de temporales

Desde la raíz del TFG:

```bash
python borrar_temporales.py
```

Borra `__pycache__` en todo el proyecto y `.txt` solo en `Juego/Informes/` y `Juego/Feedback/`.
