# Cómo jugar

## Requisitos

| Requisito | Detalle |
|-----------|---------|
| **Python** | 3.10 o superior (3.12+ recomendado). [python.org/downloads](https://www.python.org/downloads/) |
| **pip** | Suele venir con Python (`python -m pip --version`) |
| **pygame-ce** | `pip install -r Juego/requirements.txt` |
| **Sistema** | Windows 10/11; también Linux/macOS |

## Descargar solo lo necesario

Si no quieres clonar el repo entero (tests, docs, scripts de mantenimiento):

1. Descarga [MATCAD_juego_portable.zip](https://github.com/Dafafi63f/Escape-Room/releases/download/juego/MATCAD_juego_portable.zip)
2. Descomprime la carpeta
3. En Windows puedes usar [`Jugar.bat`](../Jugar.bat) en la raíz del repo (o del zip); o en cualquier sistema:

```bash
pip install -r Juego/requirements.txt
python Juego/juego_grafico.py
```

Detalle del paquete: descarga desde [Releases / juego](https://github.com/Dafafi63f/Escape-Room/releases/tag/juego).

## Arrancar (repositorio completo)

```bash
git clone https://github.com/Dafafi63f/Escape-Room.git
cd Escape-Room
pip install -r Juego/requirements.txt
python Juego/juego_grafico.py
```

Para desarrollo (tests y mantenimiento del banco): `pip install -r requirements.txt` en la raíz del repo.

## Más información

- [`README.md`](README.md) — estructura del juego
- [`Data/README.md`](../Data/README.md) — archivos de datos
- [`Data/Plantillas/README.md`](../Data/Plantillas/README.md) — plantilla CSV para datos propios
