# Juego — consola MATCAD

Todo lo necesario para **jugar** en terminal (y, opcionalmente, empaquetar un `.exe`).

| Elemento | Descripción |
|----------|-------------|
| [`juego_cuestionario.py`](juego_cuestionario.py) | Lanzador: menú principal y arranque de modos |
| [`Consola/`](Consola/README.md) | Paquete Python con la lógica del juego (`from Consola...`) |
| [`Informes/`](Informes/README.md) | Informes `.txt` de partidas (local, gitignored) |
| [`Feedback/`](Feedback/README.md) | Copias locales de avisos al creador (local, gitignored) |
| [`Tests/`](Tests/README.md) | Pruebas unitarias |
| [`build_exe_onefile.ps1`](build_exe_onefile.ps1) | Genera `juego_cuestionario.exe` con PyInstaller |

## Jugar

Desde la raíz del TFG:

```bash
python Juego/juego_cuestionario.py
```

Requisito: Python 3.10+, solo biblioteca estándar. Datos en [`../Data/README.md`](../Data/README.md).

Al arrancar, el lanzador muestra un **tutorial breve** de foco de teclado (hay que hacer clic en la línea `>>` de la terminal para que las teclas respondan). Detalle en [`Consola/entrada_menu.py`](Consola/entrada_menu.py).

### Modos

| Modo | Estado | Descripción |
|------|--------|-------------|
| **Libre** | Implementado | Partida configurable, filtros por curso/semestre/grupo/nivel, informes al cerrar |
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

Detalle completo: [`Consola/entrada_menu.py`](Consola/entrada_menu.py) y [`Consola/README.md`](Consola/README.md).

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

Genera `juego_cuestionario.exe` en esta carpeta. Incluye `Data/` del proyecto (preguntas, materias, plantillas, histórico CSV). Los informes se escriben en `Informes/` **junto al `.exe`** al ejecutarlo.

### Artefactos de build

Tras un build correcto, `build_exe_onefile.ps1` **borra** `build/`, `juego_cuestionario.spec` y `dist/` si existen. Solo queda `juego_cuestionario.exe` en `Juego/`.

| Elemento | En git |
|----------|--------|
| `juego_cuestionario.exe` | Ignorado en `.gitignore` |
| `build/`, `*.spec` | No se versionan; el script de build los elimina al terminar |

## Limpieza de temporales

Desde la raíz del TFG:

```bash
python borrar_temporales.py
```

Borra `__pycache__` y `.txt` (informes, feedback, etc.) en todo el proyecto.
