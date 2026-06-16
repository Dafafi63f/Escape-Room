# Figuras de la memoria TFG

Imágenes usadas en `Memoria_TFG.md` y `Entrega/Memoria/Memoria_TFG.tex`.

## Regenerar

Desde la raíz del proyecto:

```bash
python Entrega/generar_figuras_memoria.py
```

Requisito: `matplotlib` (`pip install matplotlib`).

| Fichero | Contenido |
|---------|-----------|
| `arquitectura_sistema.png` | Capas del software (lanzadores → Comun → datos) |
| `flujo_modo_historia.png` | Pipeline del generador de examen balanceado |
| `monte_carlo_histograma_notas.png` | Distribución simulada de notas vs. binomial teórica |
| `monte_carlo_convergencia.png` | Convergencia del estimador Monte Carlo de la fracción de aciertos |
