# MATCAD — Versión 1.0.0 (entrega TFG)

**Fecha:** 2026-06-29
**Estado:** entrega académica cerrada. Continuación del juego: **v1.1.0+** como proyecto personal (ver `Juego/Comun/version.py` y [`CHANGELOG_JUEGO.md`](CHANGELOG_JUEGO.md)).

## Qué incluye esta versión

| Área | Estado |
|------|--------|
| **Modo libre** | Configuración en dos pasos, filtros, banco 480 o ampliado, informe `.txt` |
| **Modo historia** | Presets, examen balanceado, examen dirigido tras cerrar |
| **Modos diarios** | Examen del día (semilla de fecha) y examen aleatorio (barra superior) |
| **Resistencia** | Partida infinita: vidas, racha, apuestas, maldiciones, bloques, objetos, eventos |
| **Escape room** | Salas 5–50, puertas, tienda, botín, jefe, inventario, informe |
| **Feedback** | Formulario + copia local; SMTP opcional (`Data/Privado/`) |
| **Estadísticas** | Panel «Mis estadísticas», JSON local, récords por modo |
| **Opciones** | Nombre, tooltips, emojis, informes, restablecer datos |
| **Banco** | 480 preguntas revisadas + 480 extras en plantillas (opcional) + 40 exclusivas resistencia |
| **Tests / CI** | 578 tests unitarios en la entrega; health check *(suite actual en `main`: ~615)* |

## Cómo jugar

```bash
pip install -r Juego/requirements.txt
python Juego/juego_grafico.py
python Files/health_check.py          # datos + tests + validar banco
```

## Qué queda para el futuro (no bloquea jugar)

Ideas y mejoras **no incluidas** en 1.0.0; ver [`CHECKLIST.md`](CHECKLIST.md) §I–VIII:

- PDF final de memoria, piloto con usuarios, vídeo demo.
- Tutorial interactivo, mapas visuales, música, más «juice».
- Checkpoints / reanudar en resistencia y escape.
- Gráficos avanzados en estadísticas, export CSV, repaso espaciado.
- Conmutador global «solo 480» en todos los modos (hoy: por defecto en libre/escape; resistencia usa pool ampliado del autor).
- Integración Moodle, panel agregado de feedback para profesorado.

## Notas de contenido

- El **banco ampliado** (960) mezcla preguntas revisadas con extras JSON; úsalo si quieres más variedad, sabiendo que los extras no tienen la misma revisión manual que las 480.
- El **paquete mínimo** (solo CSV) limita modos especiales y filtros; el examen del día sigue disponible desde la barra superior.
- En v1.1+ el zip jugable se descarga desde [Releases / juego](https://github.com/Dafafi63f/Escape-Room/releases/tag/juego) (no hay carpeta `Distribucion/` en el repo).
