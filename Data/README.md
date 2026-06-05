# Data — banco de preguntas y datasets

Ficheros que usa el juego y las herramientas de mantenimiento.

| Fichero | Uso |
|---------|-----|
| `Preguntas.csv` | Banco principal (480 preguntas cerradas en producción) |
| `listado_materias.csv` | Metadatos de materias (curso, nombre, etc.) |
| `plantillas.json` | Plantillas / pool extra (modos beta del juego) |
| `criterios_clasificacion_materia.csv` | Criterios de clasificación por materia (mantenimiento) |
| `Historic_qualificacions_MatCAD_completo.csv` | Histórico de qualificacions — **modo historia** |
| `Històric_qualificacions_MatCAD.xlsx` | Fuente original del histórico; el juego usa el **CSV** |
| `revision_manual.md` | Notas de revisión manual del banco |
| `creador_privado.json` | Datos personales y secretos del creador (local, no se versiona) |

El juego resuelve rutas con [`Juego/Consola/rutas.py`](../Juego/Consola/rutas.py): busca una carpeta `Data/` en la raíz del proyecto, en el directorio de trabajo o junto al `.exe` (PyInstaller extrae `Data/` dentro del bundle).

## Fichero privado del creador (no se sube a git)

`Data/creador_privado.json` guarda en un solo sitio:

- Datos personales (`creador`: nombre, correo, tutor, notas).
- Secretos de GitHub (`github`: usuario, repo, token).
- SMTP del modo feedback (`feedback_smtp`).

La plantilla por defecto está en código: [`Juego/Consola/config_creador.py`](../Juego/Consola/config_creador.py).

```bash
cd Juego
python -m Consola.config_creador
```

Rellena tus datos reales en el fichero generado. En Gmail, `smtp_password` es una contraseña de aplicación de 16 caracteres.

## Validar el banco

```bash
python Files/Scripts/mantenimiento.py validar
```

## Empaquetado en el `.exe`

Al ejecutar `Juego/build_exe_onefile.ps1`, se incluye esta carpeta (salvo que copies datos solo en `Juego/Data/`). Conviene tener aquí al menos los CSV/JSON que uses en todos los modos.

`creador_privado.json` **no** se empaqueta en el `.exe`; configúralo en la máquina donde generes o distribuyas el ejecutable si necesitas SMTP.
