"""Ejercicio resuelto 2: búsqueda, inserción, eliminación, split y join."""

from splay_tree import SplayTree


def main() -> None:
    tree = SplayTree()
    for key in [40, 20, 60, 10, 30, 50, 70]:
        tree.insert(key)
    assert tree.root.key == 70
    assert tree.search(30).key == 30 and tree.root.key == 30
    assert tree.search(25) is None and tree.root.key in {20, 30}
    assert tree.delete(40) and not tree.delete(999)
    assert tree.validate()

    split_tree = SplayTree()
    for key in [40, 20, 60, 10, 30, 50, 70]:
        split_tree.insert(key)
    lower, upper = split_tree.split(40)
    assert lower.keys() == [10, 20, 30]
    assert upper.keys() == [40, 50, 60, 70]
    lower.join(upper)
    assert lower.keys() == [10, 20, 30, 40, 50, 60, 70] and lower.validate()
    print("[OK] search, insert, delete, split y join verificados.")


if __name__ == "__main__":
    main()
