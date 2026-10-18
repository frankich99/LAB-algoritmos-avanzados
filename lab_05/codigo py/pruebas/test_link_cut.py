"""Pruebas unitarias completas para LinkCutForest (Laboratorio 05)."""

import unittest
import sys
from pathlib import Path

# Agregar directorio padre al path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from link_cut_tree import LinkCutForest


class TestLinkCutForest(unittest.TestCase):
    def test_isolated_nodes(self):
        """1. Nodos aislados y consultas de raíz."""
        forest = LinkCutForest()
        nodes = [forest.create_node(i, value=i * 10) for i in range(1, 6)]
        for node in nodes:
            self.assertIs(forest.find_root(node), node)
            self.assertTrue(forest.connected(node, node))
            self.assertEqual(forest.path_sum(node, node), node.value)
            self.assertTrue(forest.validate())

    def test_topologies_chain_star_balanced(self):
        """2. Cadenas, estrellas y árboles balanceados."""
        # Cadena
        forest = LinkCutForest()
        n = 8
        nodes = [forest.create_node(i, 1) for i in range(n)]
        for i in range(n - 1):
            forest.link(nodes[i], nodes[i + 1])
            self.assertTrue(forest.validate())
        self.assertEqual(forest.path_sum(nodes[0], nodes[n - 1]), n)

        # Estrella
        forest_star = LinkCutForest()
        hub = forest_star.create_node("hub", 100)
        spokes = [forest_star.create_node(f"s{i}", i) for i in range(5)]
        for s in spokes:
            forest_star.link(s, hub)
            self.assertTrue(forest_star.validate())
        for s in spokes:
            self.assertEqual(forest_star.path_sum(s, hub), s.value + 100)

    def test_make_root_and_exposes(self):
        """3 y 4. Cambio de raíz mediante make_root y varios expose consecutivos."""
        forest = LinkCutForest()
        u = forest.create_node("U", 10)
        v = forest.create_node("V", 20)
        w = forest.create_node("W", 30)

        forest.link(u, v)
        forest.link(v, w)
        self.assertTrue(forest.validate())

        # make_root cambia la raíz representada
        forest.make_root(w)
        self.assertIs(forest.find_root(u), w)
        self.assertIs(forest.find_root(v), w)
        self.assertIs(forest.find_root(w), w)
        self.assertTrue(forest.validate())

        # Expose consecutivos sobre diferentes nodos
        forest.expose(u)
        self.assertTrue(forest.validate())
        forest.expose(w)
        self.assertTrue(forest.validate())
        forest.expose(v)
        self.assertTrue(forest.validate())

    def test_cycle_rejection(self):
        """5. Rechazo estricto de enlaces que forman ciclos."""
        forest = LinkCutForest()
        n1 = forest.create_node(1)
        n2 = forest.create_node(2)
        n3 = forest.create_node(3)

        forest.link(n1, n2)
        forest.link(n2, n3)
        self.assertTrue(forest.connected(n1, n3))

        # Intentar crear ciclo 1-3 debe lanzar ValueError
        with self.assertRaises(ValueError):
            forest.link(n1, n3)
        self.assertTrue(forest.validate())

    def test_cut_near_root_and_internal(self):
        """6 y 7. Cortes válidos e intento de cortar aristas inexistentes."""
        forest = LinkCutForest()
        a = forest.create_node("A", 1)
        b = forest.create_node("B", 2)
        c = forest.create_node("C", 3)
        d = forest.create_node("D", 4)

        forest.link(a, b)
        forest.link(b, c)
        forest.link(c, d)

        # Corte inválido: A y C están en la misma componente pero no forman arista directa
        with self.assertRaises(ValueError):
            forest.cut(a, c)

        # Corte válido interno B-C
        forest.cut(b, c)
        self.assertFalse(forest.connected(a, d))
        self.assertTrue(forest.connected(a, b))
        self.assertTrue(forest.connected(c, d))
        self.assertTrue(forest.validate())

        # Corte de arista inexistente
        with self.assertRaises(ValueError):
            forest.cut(a, d)

    def test_path_sum_signed_values(self):
        """8. Consulta de suma con valores positivos, cero y negativos."""
        forest = LinkCutForest()
        n_pos = forest.create_node("P", 15)
        n_zero = forest.create_node("Z", 0)
        n_neg = forest.create_node("N", -10)

        forest.link(n_pos, n_zero)
        forest.link(n_zero, n_neg)

        self.assertEqual(forest.path_sum(n_pos, n_neg), 15 + 0 + (-10))
        self.assertEqual(forest.path_sum(n_zero, n_neg), -10)
        self.assertEqual(forest.path_sum(n_pos, n_zero), 15)
        self.assertTrue(forest.validate())

    def test_scenario_a_guide_official(self):
        """Prueba del Escenario A oficial de la Guía 05."""
        values = {1: 4, 2: 7, 3: 2, 4: 9, 5: 1, 6: 6, 7: 3}
        forest = LinkCutForest()
        nodes = {v: forest.create_node(v, val) for v, val in values.items()}

        edges = [(1, 2), (1, 3), (2, 4), (2, 5), (3, 6), (3, 7)]
        for u, v in edges:
            forest.link(nodes[u], nodes[v])
            self.assertTrue(forest.validate())

        self.assertEqual(forest.path_sum(nodes[4], nodes[5]), 17)
        self.assertEqual(forest.path_sum(nodes[4], nodes[6]), 28)
        self.assertEqual(forest.path_sum(nodes[6], nodes[7]), 11)

        forest.cut(nodes[1], nodes[3])
        self.assertFalse(forest.connected(nodes[4], nodes[6]))
        self.assertTrue(forest.validate())

        forest.link(nodes[1], nodes[3])
        self.assertTrue(forest.connected(nodes[4], nodes[6]))
        self.assertEqual(forest.path_sum(nodes[4], nodes[6]), 28)
        self.assertTrue(forest.validate())


if __name__ == "__main__":
    unittest.main()
