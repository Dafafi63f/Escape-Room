# Juego — cuestionario MATCAD

Cuestionario en **terminal** con tres modos (libre, historia, feedback). La lógica de dominio vive en [`Comun/`](Comun/README.md); la UI y orquestación en [`Consola/`](Consola/README.md).

Una versión gráfica en pygame se desarrolla en la rama `feature/juego-grafico-pygame`.

| Elemento | Descripción |
|----------|-------------|
| [`juego_consola.py`](juego_consola.py) | Lanzador: menú principal y arranque de modos |
| [`Comun/`](Comun/README.md) | Dominio compartido (`from Comun...`) |
| [`Consola/`](Consola/README.md) | UI terminal y orquestación de modos |
| [`Informes/`](Informes/README.md) | Informes `.txt` de partidas (local, gitignored) |
| [`Feedback/`](Feedback/README.md) | Copias locales de avisos al creador (local, gitignored) |
| [`Tests/`](../Tests/README.md) | Pruebas unitarias (suite unificada en la raíz) |
| [`build_exe_onefile.ps1`](build_exe_onefile.ps1) | Genera `juego_consola.exe` con PyInstaller |

## Ejecutar

```bash
python Juego/juego_consola.py
```

Requisito: Python 3.10+, solo biblioteca estándar. Datos en [`../Data/README.md`](../Data/README.md).

Al arrancar, el lanzador muestra un **tutorial breve** de foco de teclado (hay que hacer clic en la línea `>>` de la terminal para que las teclas respondan). Detalle en [`Consola/entrada_teclas.py`](Consola/entrada_teclas.py) y [`Consola/entrada_menu.py`](Consola/entrada_menu.py).

### Modos

| Modo | Estado | Descripción |
|------|--------|-------------|
| **Libre** | Implementado | Partida configurable, filtros por curso/semestre/grupo/nivel, informes al cerrar |
| **Historia** | Implementado (v1) | Examen balanceado según histórico de qualificacions |
| **Feedback** | Implementado (v1) | Asistente para enviar bug, sugerencia u otro aviso al creador |

Detalle de bancos de preguntas, puntuación, dificultad progresiva y arquitectura: [`Consola/README.md`](Consola/README.md) y [`Comun/README.md`](Comun/README.md).

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
