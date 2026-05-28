# Revision manual 1-30 (2026-05-28)

Objetivo: dejar trazabilidad de la revision manual de las preguntas `Id 1..30` para continuar en la siguiente sesion.

## Estado general

- Revisadas manualmente las `Id 1..30` de `Data/Preguntas.csv`.
- Bloques tematicos:
  - `1..10`: Àlgebra Lineal.
  - `11..20`: Càlcul en una Variable.
  - `21..30`: Fonaments de Computadors.
- Balance de estructura en el tramo revisado: correcto (`5 Teoria + 5 Calculo` por materia en cada bloque de 10).

## Registro por IDs

### 1-10 (Àlgebra Lineal)

- `1`: OK
- `2`: OK
- `3`: OK
- `4`: OK
- `5`: OK
- `6`: OK
- `7`: OK
- `8`: OK
- `9`: OK
- `10`: OK

### 11-20 (Càlcul en una Variable)

- `11`: OK
- `12`: OK (serie geometrica, teoria)
- `13`: OK
- `14`: OK
- `15`: OK
- `16`: OK
- `17`: OK
- `18`: OK
- `19`: OK (limites, calculo)
- `20`: OK (series, calculo)

### 21-30 (Fonaments de Computadors)

- `21`: OK
- `22`: OK
- `23`: OK
- `24`: OK (LRU/cache)
- `25`: Revisar nivel de dificultad: posible candidato a subir complejidad (actualmente muy basica para "Dificil").
- `26`: OK
- `27`: Revisar formulacion: "Latencia tipica red local" puede depender del contexto/infraestructura.
- `28`: OK
- `29`: OK
- `30`: OK

## Pendientes para proximo dia

1. Ajustar `Id 25` para que sea claramente "Dificil" en Fonaments.
2. Decidir si `Id 27` se mantiene como aproximacion practica o se sustituye por una pregunta menos dependiente de entorno.
3. Continuar revision manual por lotes: siguiente tramo sugerido `Id 31..60`.

## Decisiones globales aplicadas hoy (importante)

- `gradiente` se ha restringido para clasificacion de materia a `Càlcul en Diverses Variables` (se elimino de `Optimització` en criterios).
- `entropía` se ha restringido para clasificacion/preguntas a `Teoria de la Informació` (y eventualmente `Física, Abstracció i Computació` si se añade contenido futuro).
- Se redujo ruido de preguntas de `bits` repetidas en materias no informacionales, sustituyendolas por enunciados mas especificos de cada materia.
- Se evitaron inyecciones de preguntas con sufijo `"(variante N)"` hacia `plantillas.json` desde el script de inyeccion del dataset.

## Alertas operativas para no romper nada

- Revisar `Files/recategorizar_lote_manual.py` antes de ejecutar:
  - el script puede quedar con `OPERACIONES` no vacia e `INPLACE=True`.
  - ejecutar solo tras confirmar que el Id y materia destino son los deseados.
- Si se vuelve a exportar criterios con `Files/exportar_criterios_clasificacion_materia.py`, validar que las notas de desambiguacion sigan alineadas con las keywords actuales.
- En `Data/plantillas.json` puede quedar alguna pregunta con sufijo `"(variante)"` historica; planificar limpieza puntual cuando toque mantenimiento de plantillas.

## Checklist rapido para retomar la proxima sesion

1. Abrir este archivo y confirmar pendientes `Id 25` y `Id 27`.
2. Validar dataset tras cualquier cambio:
   - `python -c "import sys; sys.path.insert(0, 'Files'); from balance_lib import ejecutar_validar; raise SystemExit(ejecutar_validar(detalle=False, estricto=False))"`
3. Si se tocan criterios, relanzar exportador y volver a comprobar solapes.
4. Continuar revision manual por tramos (`31..60`, `61..90`, etc.) y actualizar este mismo `md`.
