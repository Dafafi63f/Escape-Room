# Tests — pruebas unitarias

Comprueban reglas, informes, entrada de consola y configuración del modo libre. No son necesarias para jugar.

## Ejecutar

Desde la raíz del TFG:

```bash
python -m unittest discover -s Juego/Tests -v
```

Los tests añaden `Juego/` al `sys.path` e importan el paquete `Consola` (misma convención que el lanzador).

## Ficheros

| Test | Enfoque |
|------|---------|
| `test_informe_examen.py` | Informes y corrección al final |
| `test_configuracion_libre.py` | Reglas personalizadas y política |
| `test_robustez_entrada.py` | Menús, teclas, `motor_partida` |
