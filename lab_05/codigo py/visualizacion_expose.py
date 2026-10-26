"""Punto de entrada de la visualización obligatoria de EXPOSE."""

from pathlib import Path

from visualizations import generate_expose_visualization


if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    result = generate_expose_visualization(base / "visualizaciones" / "expose", base / "figuras")
    print(f"[OK] {len(result['frames'])} imágenes de EXPOSE generadas.")
