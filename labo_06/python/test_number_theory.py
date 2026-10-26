"""
test_number_theory.py
=====================

Pruebas automatizadas de propiedades y casos excepcionales (Guía 06).
Se usa unittest para que funcione en Google Colab sin instalar nada:
    import unittest, test_number_theory
    unittest.main(module=test_number_theory, argv=[""], exit=False, verbosity=2)
"""

import math
import unittest
from itertools import permutations

from number_theory import (crt, crt_with_trace, extended_gcd, gcd_trace,
                           modular_inverse, modular_pow,
                           solve_linear_congruence, validate_crt_solution)
from case_generator import (FIB_PAIRS, exponent_with_popcount, make_rng,
                            random_congruence, random_crt_system, random_pair)


def check_trace(a, b, d, trace):
    """Propiedad 1: cada fila cumple a_i = b_i q_i + r_i y 0 <= r_i < |b_i|."""
    for (ai, bi, qi, ri) in trace:
        assert ai == bi * qi + ri, (ai, bi, qi, ri)
        assert 0 <= ri < abs(bi), (ai, bi, qi, ri)
    if trace:
        assert trace[-1][3] == 0
        assert trace[-1][1] == d


class TestEuclides(unittest.TestCase):
    def test_caso_guia(self):
        d, trace = gcd_trace(252, 105)
        self.assertEqual(d, 21)
        self.assertEqual(trace, [(252, 105, 2, 42), (105, 42, 2, 21), (42, 21, 2, 0)])
        self.assertEqual(extended_gcd(252, 105), (21, -2, 5))

    def test_ceros(self):
        self.assertEqual(gcd_trace(17, 0), (17, []))
        self.assertEqual(gcd_trace(0, 17)[0], 17)
        self.assertEqual(gcd_trace(0, 0), (0, []))         # convención documentada
        self.assertEqual(extended_gcd(0, 0), (0, 0, 0))
        for a, b in [(17, 0), (0, 17), (-9, 0), (0, -9)]:
            d, x, y = extended_gcd(a, b)
            self.assertEqual(a * x + b * y, d)

    def test_signos_e_intercambio(self):
        for a, b in [(252, 105), (-252, 105), (252, -105), (-252, -105),
                     (105, 252), (-105, -252)]:
            d, trace = gcd_trace(a, b)
            self.assertEqual(d, math.gcd(a, b))
            check_trace(a, b, d, trace)
            d2, x, y = extended_gcd(a, b)
            self.assertEqual(d2, d)
            self.assertEqual(a * x + b * y, d)

    def test_coprimos_y_no_coprimos(self):
        self.assertEqual(gcd_trace(35, 64)[0], 1)
        self.assertEqual(gcd_trace(48, 180)[0], 12)

    def test_fibonacci_peor_caso(self):
        # Pares consecutivos de Fibonacci: máximo número de divisiones (Lamé)
        for a, b in FIB_PAIRS:
            d, trace = gcd_trace(a, b)
            self.assertEqual(d, 1)
            check_trace(a, b, d, trace)
        self.assertEqual(len(gcd_trace(89, 55)[1]), 9)

    def test_aleatorio_contra_math_gcd(self):
        rng = make_rng(1)
        for bits in (8, 16, 32, 64, 128, 256, 512):
            for _ in range(100):
                a, b = random_pair(rng, bits)
                d, trace = gcd_trace(a, b)
                self.assertEqual(d, math.gcd(a, b))
                check_trace(a, b, d, trace)
                d2, x, y = extended_gcd(a, b)
                self.assertEqual(a * x + b * y, d2)

    def test_tipo_invalido(self):
        with self.assertRaises(TypeError):
            gcd_trace(2.5, 3)


class TestInversoYCongruencias(unittest.TestCase):
    def test_inverso_existente(self):
        self.assertEqual(modular_inverse(7, 40), 23)
        self.assertEqual((7 * 23) % 40, 1)

    def test_inverso_residuo_negativo_y_grande(self):
        u = modular_inverse(-3, 11)
        self.assertEqual((-3 * u) % 11, 1)
        self.assertEqual(u, 7)
        self.assertEqual(modular_inverse(47, 40), modular_inverse(7, 40))

    def test_inverso_inexistente(self):
        for a, n in [(6, 9), (10, 25), (0, 7), (14, 100)]:
            with self.assertRaises(ValueError):
                modular_inverse(a, n)

    def test_modulo_invalido(self):
        for n in (1, 0, -5):
            with self.assertRaises(ValueError):
                modular_inverse(3, n)

    def test_inverso_existe_sii_mcd_1(self):
        for n in range(2, 60):
            for a in range(-n, 2 * n):
                if math.gcd(a, n) == 1:
                    u = modular_inverse(a, n)
                    self.assertEqual((a * u) % n, 1)
                    self.assertTrue(0 < u < n)
                    self.assertEqual(u, pow(a, -1, n))
                else:
                    with self.assertRaises(ValueError):
                        modular_inverse(a, n)

    def test_congruencia_guia(self):
        sol = solve_linear_congruence(14, 30, 100)
        self.assertEqual(sol, [45, 95])
        self.assertTrue(all((14 * x - 30) % 100 == 0 for x in sol))

    def test_congruencia_sin_solucion(self):
        self.assertEqual(solve_linear_congruence(6, 4, 9), [])

    def test_congruencia_una_solucion(self):
        self.assertEqual(solve_linear_congruence(7, 3, 40), [(23 * 3) % 40])

    def test_congruencia_varias_soluciones(self):
        sol = solve_linear_congruence(12, 18, 30)
        self.assertEqual(len(sol), 6)
        self.assertTrue(all((12 * x - 18) % 30 == 0 for x in sol))

    def test_congruencia_a_cero(self):
        self.assertEqual(solve_linear_congruence(0, 0, 4), [0, 1, 2, 3])
        self.assertEqual(solve_linear_congruence(10, 3, 5), [])

    def test_congruencia_modulo_invalido(self):
        with self.assertRaises(ValueError):
            solve_linear_congruence(3, 1, 0)

    def test_congruencias_exhaustivo(self):
        for n in range(1, 40):
            for a in range(-5, n + 5):
                for b in range(-3, n + 3):
                    brute = [x for x in range(n) if (a * x - b) % n == 0]
                    self.assertEqual(solve_linear_congruence(a, b, n), brute)

    def test_congruencias_aleatorias(self):
        rng = make_rng(2)
        for _ in range(500):
            a, b, n = random_congruence(rng)
            d = math.gcd(a, n)
            sol = solve_linear_congruence(a, b, n)
            if b % d == 0:
                self.assertEqual(len(sol), d)
                self.assertEqual(len(set(sol)), d)
                self.assertTrue(all(0 <= x < n and (a * x - b) % n == 0 for x in sol))
            else:
                self.assertEqual(sol, [])


class TestPotenciaModular(unittest.TestCase):
    def test_caso_guia(self):
        self.assertEqual(modular_pow(7, 13, 20), (7, 3, 3))

    def test_bordes(self):
        self.assertEqual(modular_pow(5, 0, 7)[0], 1)     # exponente cero
        self.assertEqual(modular_pow(0, 5, 7)[0], 0)     # base cero
        self.assertEqual(modular_pow(0, 0, 7)[0], 1)     # convención 0^0 = 1, igual que pow
        self.assertEqual(modular_pow(5, 3, 1)[0], 0)     # módulo uno
        self.assertEqual(modular_pow(5, 0, 1)[0], 0)
        self.assertEqual(modular_pow(-2, 3, 7)[0], pow(-2, 3, 7))

    def test_errores(self):
        with self.assertRaises(ValueError):
            modular_pow(2, -1, 7)
        with self.assertRaises(ValueError):
            modular_pow(2, 3, 0)

    def test_conteo_operaciones(self):
        rng = make_rng(3)
        for bits in (8, 64, 1024):
            for ones in (1, bits // 2, bits):
                e = exponent_with_popcount(rng, bits, ones)
                _, sq, pr = modular_pow(3, e, 1_000_000_007)
                self.assertEqual(sq, bits - 1)
                self.assertEqual(pr, ones)
                self.assertEqual(pr, bin(e).count("1"))

    def test_muchos_bits_contra_pow(self):
        rng = make_rng(4)
        for bits in (8, 16, 32, 64, 128, 256, 512, 1024, 2048):
            for _ in range(20):
                base = rng.getrandbits(bits)
                e = rng.getrandbits(bits)
                m = rng.getrandbits(bits) | 1
                self.assertEqual(modular_pow(base, e, m)[0], pow(base, e, m))


class TestTCR(unittest.TestCase):
    def test_caso_obligatorio(self):
        x, N, trace = crt_with_trace([2, 3, 2], [3, 5, 7])
        self.assertEqual((x, N), (23, 105))
        self.assertEqual([(r["N_i"], r["M_i"]) for r in trace], [(35, 2), (21, 1), (15, 1)])
        self.assertTrue(validate_crt_solution(x, [2, 3, 2], [3, 5, 7]))

    def test_una_congruencia(self):
        self.assertEqual(crt([4], [9]), (4, 9))
        self.assertEqual(crt([-1], [9]), (8, 9))

    def test_residuos_no_normalizados(self):
        self.assertEqual(crt([-1, 13, 9], [3, 5, 7]), (23, 105))

    def test_orden_de_modulos(self):
        res, mod = [2, 3, 2], [3, 5, 7]
        for perm in permutations(range(3)):
            r = [res[i] for i in perm]
            m = [mod[i] for i in perm]
            self.assertEqual(crt(r, m), (23, 105))

    def test_listas_invalidas(self):
        with self.assertRaises(ValueError):
            crt([], [])
        with self.assertRaises(ValueError):
            crt([1, 2], [3])
        with self.assertRaises(ValueError):
            crt([1], [1])
        with self.assertRaises(ValueError):
            crt([1, 2], [0, 5])

    def test_modulos_no_coprimos(self):
        with self.assertRaises(ValueError):
            crt([1, 2], [6, 6])     # repetidos
        with self.assertRaises(ValueError):
            crt([1, 2], [4, 6])     # mcd = 2

    def test_contra_busqueda_exhaustiva(self):
        rng = make_rng(5)
        for _ in range(200):
            _, r, m = random_crt_system(rng, rng.randint(1, 3), 2, 30)
            x, N = crt(r, m)
            brute = next(t for t in range(N) if validate_crt_solution(t, r, m))
            self.assertEqual(x, brute)

    def test_sistemas_con_solucion_conocida(self):
        rng = make_rng(6)
        for _ in range(500):
            x_known, r, m = random_crt_system(rng, rng.randint(1, 6))
            x, N = crt(r, m)
            self.assertEqual(x, x_known % N)
            self.assertTrue(0 <= x < N)
            self.assertTrue(validate_crt_solution(x, r, m))

    def test_validador(self):
        self.assertTrue(validate_crt_solution(128, [2, 3, 2], [3, 5, 7]))
        self.assertFalse(validate_crt_solution(24, [2, 3, 2], [3, 5, 7]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
