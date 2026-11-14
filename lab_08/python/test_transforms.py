"""Pruebas unitarias y diferenciales de la Guía 08; solo biblioteca estándar."""

import unittest
from random import Random

from case_generator import MANUAL_CASES
from ejercicios_resueltos import intt_direct, ntt_direct, resuelto_1, resuelto_2, resuelto_3
from transforms import (MODULUS, PRIMITIVE_ROOT, OperationCounts,
                        convolution_fft_raw, fft, fft_iterative, ifft,
                        modular_inverse, multiply_fft, multiply_ntt,
                        naive_convolution, next_power_of_two, ntt, validate_root)


class TestConvolution(unittest.TestCase):
    def test_casos_manuales(self):
        for a, b, expected in MANUAL_CASES:
            with self.subTest(a=a, b=b):
                self.assertEqual(naive_convolution(a, b), expected)
                self.assertEqual(multiply_fft(a, b), expected)
                self.assertEqual(multiply_fft(a, b, method="iterative"), expected)
                self.assertEqual(multiply_ntt(a, b, 17, 3), [x % 17 for x in expected])

    def test_vacios_y_cero_conservan_longitud(self):
        self.assertEqual(naive_convolution([], [0]), [])
        self.assertEqual(multiply_fft([], [0]), [])
        self.assertEqual(multiply_ntt([], [0], 17, 3), [])
        self.assertEqual(multiply_fft([0, 0], [0, 0, 0]), [0] * 4)

    def test_potencia_minima(self):
        self.assertEqual([next_power_of_two(i) for i in (1, 2, 3, 4, 5, 8, 9)],
                         [1, 2, 4, 4, 8, 8, 16])

    def test_potencias_invalidas(self):
        for v in (0, -1):
            with self.assertRaises(ValueError):
                next_power_of_two(v)
        with self.assertRaises(TypeError):
            next_power_of_two(True)

    def test_contadores_directa(self):
        counts = OperationCounts()
        naive_convolution([1, 2, 3], [4, 5], stats=counts)
        self.assertEqual((counts.multiplications, counts.additions), (6, 6))


class TestFFT(unittest.TestCase):
    def test_roundtrip_2_4_8_16(self):
        for n in (1, 2, 4, 8, 16):
            a = [x * x - 3 for x in range(n)]
            with self.subTest(n=n):
                self.assertTrue(all(abs(x - y) < 1e-8
                                    for x, y in zip(a, ifft(fft(a)))))

    def test_iterativa_inplace_y_orden(self):
        a = [1, 2, 3, 4, 0, -2, 1, 0]
        expected = fft(a)
        b = a.copy()
        self.assertIs(fft_iterative(b), b)
        self.assertTrue(all(abs(x - y) < 1e-8 for x, y in zip(b, expected)))
        fft_iterative(b, invert=True)
        self.assertTrue(all(abs(x - y) < 1e-8 for x, y in zip(b, a)))

    def test_rechazo_longitudes(self):
        for a in ([], [1, 2, 3]):
            with self.assertRaises(ValueError):
                fft(a)
            with self.assertRaises(ValueError):
                ifft(a)
            with self.assertRaises(ValueError):
                fft_iterative(a)
        with self.assertRaises(TypeError):
            fft_iterative((1, 2))

    def test_padding_evitar_circularidad(self):
        self.assertEqual(multiply_fft([1, 0, 0, 1], [1, 1]), [1, 1, 0, 1, 1])
        self.assertEqual(len(convolution_fft_raw([1] * 5, [1] * 6)), 10)

    def test_tolerancia_real_e_imaginaria(self):
        with self.assertRaises(ValueError):
            multiply_fft([1], [1], tolerance=-1)
        with self.assertRaises(ValueError):
            multiply_fft([1], [1], method="noexiste")
        with self.assertRaises(ArithmeticError):
            multiply_fft([1, 0, 1], [0, 1, 1], tolerance=0)
        for tolerance in (float("nan"), float("inf"), "0"):
            with self.assertRaises(ValueError):
                multiply_fft([1], [1], tolerance=tolerance)
        with self.assertRaises(TypeError):
            multiply_fft([1.5], [2])

    def test_conteos_mariposas(self):
        counts = OperationCounts()
        fft(list(range(8)), stats=counts)
        self.assertEqual((counts.stages, counts.butterflies,
                          counts.additions, counts.multiplications), (3, 12, 24, 24))
        counts2 = OperationCounts()
        fft_iterative(list(range(8)), stats=counts2)
        self.assertEqual(counts, counts2)


class TestNTT(unittest.TestCase):
    def test_ejemplo_f17_y_oraculo(self):
        a = [1, 2, 3, 4]
        self.assertEqual(ntt_direct(a, 4, 17), [10, 7, 15, 6])
        self.assertEqual(intt_direct([10, 7, 15, 6], 4, 17), a)
        self.assertEqual(ntt(a, False, 17, 4), ntt_direct(a, 4, 17))
        self.assertEqual(ntt([10, 7, 15, 6], True, 17, 4), a)

    def test_raices_f17(self):
        for n, root in ((1, 1), (2, 16), (4, 4), (8, 9), (16, 3)):
            self.assertTrue(validate_root(root, n, 17))
        for root, n, p in ((4, 8, 17), (1, 4, 17), (0, 2, 17),
                           (3, 32, 17), (4, 4, 15), (3, 3, 17), (1, 0, 17)):
            with self.subTest(root=root, n=n, p=p), self.assertRaises(ValueError):
                validate_root(root, n, p)

    def test_inversos(self):
        self.assertEqual(modular_inverse(4, 17), 13)
        self.assertEqual(modular_inverse(-1, 17), 16)
        for a, mod in ((0, 17), (2, 4), (1, 1)):
            with self.assertRaises(ValueError):
                modular_inverse(a, mod)

    def test_negativos_y_cercanos_modulo(self):
        a, b = [-1, 16, 0, 1], [16, -3]
        expected = [x % 17 for x in naive_convolution(a, b)]
        self.assertEqual(multiply_ntt(a, b, 17, 3), expected)

    def test_modulo_incompatible_y_raiz_incorrecta(self):
        with self.assertRaises(ValueError):
            multiply_ntt([1] * 9, [1] * 9, 17, 3)
        with self.assertRaises(ValueError):
            multiply_ntt([1], [1], 17, 4)
        with self.assertRaises(ValueError):
            ntt([1, 2, 3], False, 17, 4)
        with self.assertRaises(TypeError):
            ntt([1.5, 2, 3, 4], False, 17, 4)

    def test_oraculo_directo_varias_longitudes(self):
        rng = Random(1808)
        for n in (1, 2, 4, 8, 16):
            root = pow(3, 16 // n, 17)
            a = [rng.randrange(-20, 20) for _ in range(n)]
            self.assertEqual(ntt(a, False, 17, root), ntt_direct(a, root, 17))
            self.assertEqual(ntt(ntt(a, False, 17, root), True, 17, root),
                             [x % 17 for x in a])

    def test_modular_no_es_entero(self):
        self.assertEqual(multiply_ntt([10], [10], 17, 3), [15])
        self.assertEqual(naive_convolution([10], [10]), [100])

    def test_conteos_y_entrada_no_mutada(self):
        a = [1, 2, 3, 4]
        counts = OperationCounts()
        ntt(a, False, 17, 4, stats=counts)
        self.assertEqual(a, [1, 2, 3, 4])
        self.assertEqual((counts.stages, counts.butterflies, counts.additions), (2, 4, 8))


class TestDifferential(unittest.TestCase):
    def test_semillas_rangos_y_longitudes_desiguales(self):
        rng = Random(202608)
        for _ in range(120):
            a = [rng.randint(-1000, 1000) for _ in range(rng.randint(1, 12))]
            b = [rng.randint(-1000, 1000) for _ in range(rng.randint(1, 12))]
            direct = naive_convolution(a, b)
            self.assertEqual(multiply_fft(a, b, tolerance=1e-5), direct)
            self.assertEqual(multiply_fft(a, b, tolerance=1e-5, method="iterative"), direct)
            self.assertEqual(multiply_ntt(a, b, MODULUS, PRIMITIVE_ROOT),
                             [x % MODULUS for x in direct])

    def test_resueltos(self):
        self.assertEqual(resuelto_1()["c"], [4, 13, 22, 15])
        self.assertEqual(resuelto_2()["producto"], [4, 13, 22, 15])
        self.assertEqual(resuelto_3()["ntt"], [10, 7, 15, 6])


if __name__ == "__main__":
    unittest.main(verbosity=2)
