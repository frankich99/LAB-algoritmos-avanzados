"""Ejercicio resuelto 1: rotaciones e instrumentación de splay."""

from splay_tree import SplayNode, SplayTree


def construir_caso_zig_zig() -> tuple[SplayTree, SplayNode]:
    tree = SplayTree()
    root, parent, target = SplayNode(100), SplayNode(50), SplayNode(20)
    tree.root = root
    root.left, parent.parent = parent, root
    parent.left, target.parent = target, parent
    return tree, target


def main() -> None:
    tree, target = construir_caso_zig_zig()
    before = tree.keys()
    tree.splay(target)
    assert tree.root is target
    assert tree.keys() == before == [20, 50, 100]
    assert tree.stats.zig_zig == 1 and tree.stats.rotations == 2
    print("[OK] splay(20): raíz=20, in-order conservado y zig-zig instrumentado.")
    print(tree.stats.snapshot())


if __name__ == "__main__":
    main()
