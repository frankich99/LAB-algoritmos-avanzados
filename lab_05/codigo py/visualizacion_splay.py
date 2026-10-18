"""Punto de entrada de la visualización del Splay Tree."""

from pathlib import Path

from visualizations import generate_splay_visualizations


if __name__ == "__main__":
    base = Path(__file__).resolve().parent
    result = generate_splay_visualizations(base / "visualizaciones" / "splay", base / "figuras")
    print(f"[OK] {len(result['frames'])} imágenes de Splay generadas.")
