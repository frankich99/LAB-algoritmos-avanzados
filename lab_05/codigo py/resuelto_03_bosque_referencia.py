"""Ejercicio resuelto 3: bosque de referencia BFS/DFS."""

from reference_forest import ReferenceForest


def main() -> None:
    values = {1: 4, 2: 7, 3: 2, 4: 9, 5: 1, 6: 6, 7: 3}
    forest = ReferenceForest(values)
    for u, v in [(1, 2), (1, 3), (2, 4), (2, 5), (3, 6), (3, 7)]:
        forest.link(u, v)
    assert forest.path(4, 6) == [4, 2, 1, 3, 6]
    assert forest.path_sum(4, 6) == 28
    assert forest.connected(5, 7)
    forest.cut(1, 3)
    assert not forest.connected(4, 6)
    print("[OK] ReferenceForest validado con BFS y suma de camino.")


if __name__ == "__main__":
    main()
