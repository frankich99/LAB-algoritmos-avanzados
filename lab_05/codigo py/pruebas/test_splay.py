"""Pruebas unitarias para SplayTree (Laboratorio 05)."""

import unittest
import sys
from pathlib import Path

# Agregar directorio padre al path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from splay_tree import SplayTree, SplayNode


class TestSplayTree(unittest.TestCase):
    def test_resuelto_1_zig_zig(self):
        """Valida el caso resuelto 1: 100 <- 50 <- 20 y splay(20)."""
        tree = SplayTree()
        n100 = SplayNode(100)
        n50 = SplayNode(50)
        n20 = SplayNode(20)

        n100.left = n50
        n50.parent = n100
        n50.left = n20
        n20.parent = n50
        tree.root = n100

        self.assertTrue(tree.validate())
        tree.splay(n20)

        self.assertEqual(tree.root.key, 20)
        self.assertEqual(tree.stats.zig_zig, 1)
        self.assertEqual(tree.stats.rotations, 2)
        self.assertEqual(tree.keys(), [20, 50, 100])
        self.assertTrue(tree.validate())

    def test_resuelto_2_operaciones_diccionario(self):
        """Valida inserción, búsqueda exitosa, fallida y eliminación."""
        tree = SplayTree()
        claves = [40, 20, 60, 10, 30, 50, 70]
        for k in claves:
            tree.insert(k)
            self.assertTrue(tree.validate())

        # Inserción deja la última clave en la raíz
        self.assertEqual(tree.root.key, 70)

        # Búsqueda exitosa
        node30 = tree.search(30)
        self.assertIsNotNone(node30)
        self.assertEqual(node30.key, 30)
        self.assertEqual(tree.root.key, 30)
        self.assertTrue(tree.validate())

        # Búsqueda fallida
        self.assertIsNone(tree.search(25))
        self.assertIn(tree.root.key, {20, 30})
        self.assertTrue(tree.validate())

        # Eliminación
        self.assertTrue(tree.delete(40))
        self.assertTrue(tree.validate())
        self.assertIsNone(tree.search(40))
        self.assertFalse(tree.delete(999))
        self.assertTrue(tree.validate())

    def test_zig_case(self):
        """Valida caso zig simple cuando el padre es la raíz."""
        tree = SplayTree()
        r = SplayNode(10)
        c = SplayNode(5)
        r.left = c
        c.parent = r
        tree.root = r

        tree.splay(c)
        self.assertEqual(tree.root.key, 5)
        self.assertEqual(tree.stats.zig, 1)
        self.assertEqual(tree.stats.rotations, 1)
        self.assertTrue(tree.validate())

    def test_zig_zag_case(self):
        """Valida caso zig-zag cuando nodo y padre están en lados opuestos."""
        tree = SplayTree()
        n30 = SplayNode(30)
        n10 = SplayNode(10)
        n20 = SplayNode(20)

        n30.left = n10
        n10.parent = n30
        n10.right = n20
        n20.parent = n10
        tree.root = n30

        tree.splay(n20)
        self.assertEqual(tree.root.key, 20)
        self.assertEqual(tree.stats.zig_zag, 1)
        self.assertEqual(tree.stats.rotations, 2)
        self.assertEqual(tree.keys(), [10, 20, 30])
        self.assertTrue(tree.validate())

    def test_split_and_join(self):
        """Valida split por clave y join de árboles independientes."""
        tree = SplayTree()
        for k in [10, 20, 30, 40, 50, 60, 70]:
            tree.insert(k)

        lower, upper = tree.split(40)
        self.assertTrue(lower.validate())
        self.assertTrue(upper.validate())
        self.assertEqual(lower.keys(), [10, 20, 30])
        self.assertEqual(upper.keys(), [40, 50, 60, 70])

        lower.join(upper)
        self.assertTrue(lower.validate())
        self.assertEqual(lower.keys(), [10, 20, 30, 40, 50, 60, 70])


if __name__ == "__main__":
    unittest.main()
