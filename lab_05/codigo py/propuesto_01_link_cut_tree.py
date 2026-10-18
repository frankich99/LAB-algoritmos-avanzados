"""Ejercicio propuesto 1: interfaz y prueba dirigida del Link-Cut Tree."""

from link_cut_tree import LinkCutForest, LinkCutNode, LinkCutStats
from lab05_pipeline import run_lct_deterministic

__all__ = ["LinkCutForest", "LinkCutNode", "LinkCutStats"]


def main() -> None:
    cases, rejections = run_lct_deterministic()
    assert all(row["estado"] == "OK" for row in rejections)
    print(f"[OK] Link-Cut Tree: {len(cases)} casos dirigidos y {len(rejections)} rechazos válidos.")


if __name__ == "__main__":
    main()
