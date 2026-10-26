"""Pruebas diferenciales automatizadas: LinkCutForest vs ReferenceForest."""

import unittest
import random
import sys
from pathlib import Path

# Agregar directorio padre al path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from link_cut_tree import LinkCutForest
from reference_forest import ReferenceForest


class TestDifferential(unittest.TestCase):
    def test_differential_random_500_ops(self):
        """Ejecuta 500 operaciones mixtas aleatorias y compara 100% con ReferenceForest."""
        rng = random.Random(2026)
        n = 20
        values = {i: rng.randint(-50, 150) for i in range(1, n + 1)}

        lct = LinkCutForest()
        lct_nodes = {i: lct.create_node(i, values[i]) for i in range(1, n + 1)}
        ref = ReferenceForest(values)

        existing_edges = set()

        for step in range(500):
            op = rng.choice(["connected", "path_sum", "link", "cut", "make_root"])
            u_id = rng.randint(1, n)
            v_id = rng.randint(1, n)

            if op == "connected":
                res_lct = lct.connected(lct_nodes[u_id], lct_nodes[v_id])
                res_ref = ref.connected(u_id, v_id)
                self.assertEqual(res_lct, res_ref, f"Discrepancia en connected({u_id}, {v_id}) paso {step}")

            elif op == "path_sum":
                if ref.connected(u_id, v_id):
                    sum_lct = lct.path_sum(lct_nodes[u_id], lct_nodes[v_id])
                    sum_ref = ref.path_sum(u_id, v_id)
                    self.assertEqual(sum_lct, sum_ref, f"Discrepancia en path_sum({u_id}, {v_id}) paso {step}")

            elif op == "link":
                if not ref.connected(u_id, v_id):
                    lct.link(lct_nodes[u_id], lct_nodes[v_id])
                    ref.link(u_id, v_id)
                    edge = tuple(sorted((u_id, v_id)))
                    existing_edges.add(edge)
                    self.assertTrue(lct.validate())

            elif op == "cut":
                if existing_edges and rng.random() < 0.6:
                    edge = rng.choice(list(existing_edges))
                    u_c, v_c = edge
                    lct.cut(lct_nodes[u_c], lct_nodes[v_c])
                    ref.cut(u_c, v_c)
                    existing_edges.remove(edge)
                    self.assertTrue(lct.validate())

            elif op == "make_root":
                lct.make_root(lct_nodes[u_id])
                self.assertIs(lct.find_root(lct_nodes[u_id]), lct_nodes[u_id])
                self.assertTrue(lct.validate())


if __name__ == "__main__":
    unittest.main()
