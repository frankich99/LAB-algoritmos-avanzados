"""Suite unittest de la Guía 07; sin dependencias externas."""

import math
import unittest
from random import Random
from unittest.mock import patch

from case_generator import KNOWN_CASES, SIZES, make_rng, random_composite
from primality import (classify_bases, decompose, fermat_round, fermat_test,
                       generate_candidate, generate_probable_prime,
                       is_probable_prime, miller_rabin_round, primality_report,
                       trial_division, trial_division_with_count)


class TestDivision(unittest.TestCase):
    def test_casos_conocidos(self):
        for n, expected in KNOWN_CASES:
            with self.subTest(n=n):
                self.assertEqual(trial_division(n), expected)

    def test_oraculo_independiente(self):
        # Criba independiente de la función bajo prueba.
        sieve = bytearray(b"\x01") * 10_001
        sieve[:2] = b"\x00\x00"
        for p in range(2, math.isqrt(10_000) + 1):
            if sieve[p]:
                sieve[p * p::p] = b"\x00" * len(sieve[p * p::p])
        for n in range(10_001):
            self.assertEqual(trial_division(n), bool(sieve[n]))

    def test_cuadrados_de_primos(self):
        for p in (3, 5, 7, 11, 97, 997):
            self.assertFalse(trial_division(p * p))

    def test_cuenta_divisiones(self):
        self.assertEqual(trial_division_with_count(2), (True, 0))
        self.assertEqual(trial_division_with_count(9), (False, 2))
        self.assertEqual(trial_division_with_count(97)[0], True)

    def test_tipos_invalidos(self):
        for n in (True, 2.5, "7"):
            with self.assertRaises(TypeError):
                trial_division(n)


class TestFermat(unittest.TestCase):
    def test_aserciones_guia(self):
        self.assertFalse(fermat_round(15, 2))
        self.assertTrue(fermat_round(341, 2))

    def test_carmichael_y_base_no_coprima(self):
        for n in (561, 1105, 1729):
            self.assertTrue(fermat_round(n, 2))
        self.assertFalse(fermat_round(561, 3))

    def test_fallo_implica_compuesto(self):
        for n in range(5, 201, 2):
            for a in range(2, n - 1):
                if not fermat_round(n, a):
                    self.assertFalse(trial_division(n))

    def test_bases_configurables(self):
        self.assertEqual(fermat_test(341, [2])["resultado"], "pasa_fermat")
        self.assertEqual(fermat_test(561, [2, 3])["resultado"], "compuesto")
        self.assertEqual(fermat_test(1, [2])["resultado"], "no_primo")
        self.assertEqual(fermat_test(3, [2])["resultado"], "primo")

    def test_bases_invalidas(self):
        for n, a in ((3, 2), (9, 1), (9, 8), (10, 2)):
            with self.assertRaises(ValueError):
                fermat_round(n, a)
        with self.assertRaises(ValueError):
            fermat_test(341, [])


class TestMillerRabin(unittest.TestCase):
    def test_descomposicion_y_precondiciones(self):
        for n in range(3, 301, 2):
            s, d = decompose(n)
            self.assertGreaterEqual(s, 1)
            self.assertEqual(d % 2, 1)
            self.assertEqual(n - 1, 2**s * d)
        for n in (0, 1, 2, 4, -1):
            with self.assertRaises(ValueError):
                decompose(n)

    def test_trazas_obligatorias(self):
        traces = {
            221: (2, 55, [128, 30]),
            341: (2, 85, [32, 1]),
            561: (4, 35, [263, 166, 67, 1]),
        }
        for n, (s, d, residues) in traces.items():
            passed, detail = miller_rabin_round(n, 2, trace=True)
            self.assertFalse(passed)
            self.assertEqual((detail["n"], detail["a"], detail["s"], detail["d"]),
                             (n, 2, s, d))
            self.assertEqual(detail["residuos"], residues)

    def test_mr_detecta_carmichael_base_dos(self):
        for n in (561, 1105, 1729):
            self.assertFalse(miller_rabin_round(n, 2)[0])

    def test_raiz_no_trivial(self):
        _, detail = miller_rabin_round(341, 2, True)
        self.assertEqual(detail["motivo"], "raiz_no_trivial_de_uno")
        self.assertEqual(math.gcd(32 - 1, 341), 31)
        self.assertEqual(math.gcd(32 + 1, 341), 11)

    def test_conteo_real_de_cuadrados(self):
        _, detail = miller_rabin_round(221, 2, True)
        self.assertEqual(detail["cuadrados_modulares"], 6)
        self.assertEqual(detail["cuadrados_cadena"], 1)
        self.assertEqual(detail["productos_modulares"], (55).bit_count())

    def test_todos_los_primos_pequenos_y_bases(self):
        for n in range(5, 151, 2):
            if trial_division(n):
                for a in range(2, n - 1):
                    self.assertTrue(miller_rabin_round(n, a)[0], (n, a))

    def test_fallo_implica_compuesto(self):
        for n in range(5, 151, 2):
            for a in range(2, n - 1):
                if not miller_rabin_round(n, a)[0]:
                    self.assertFalse(trial_division(n))

    def test_testigo_y_mentiroso_fuerte(self):
        result = classify_bases(25)
        self.assertIn(7, result["mentirosos_fuertes"])
        self.assertIn(2, result["testigos"])
        self.assertEqual(len(result["mentirosos_fuertes"]) + len(result["testigos"]), 22)
        self.assertLessEqual(result["fraccion_mentirosos"], 0.25)

    def test_clasificacion_invalida(self):
        for n in (1, 2, 4, 7):
            with self.assertRaises(ValueError):
                classify_bases(n)

    def test_bases_extremas(self):
        self.assertTrue(miller_rabin_round(97, 2)[0])
        self.assertTrue(miller_rabin_round(97, 95)[0])
        for a in (1, 96):
            with self.assertRaises(ValueError):
                miller_rabin_round(97, a)

    def test_sin_traza(self):
        passed, detail = miller_rabin_round(97, 2)
        self.assertTrue(passed)
        self.assertEqual(detail["residuos"], [])
        self.assertEqual((detail["n"], detail["a"]), (97, 2))


class TestPruebasRepetidas(unittest.TestCase):
    def test_mil_aleatorios_menores_de_un_millon(self):
        rng = make_rng(707)
        bases_rng = make_rng(1707)
        for _ in range(1000):
            n = rng.randrange(1_000_000)
            self.assertEqual(is_probable_prime(n, 20, bases_rng), trial_division(n), n)

    def test_bordes_y_cota(self):
        for n, expected in KNOWN_CASES:
            report = primality_report(n, 20, make_rng(7))
            self.assertEqual(report["resultado"] in ("primo", "probable_primo"), expected, n)
        report = primality_report(1009, 20, bases=[2] * 20)
        self.assertEqual(report["resultado"], "probable_primo")
        self.assertEqual(report["rondas_ejecutadas"], 20)
        self.assertEqual(report["cota_error"], 4.0**-20)

    def test_base_testigo_y_rechazo_temprano(self):
        report = primality_report(341, 20, bases=[2] * 20, presieve=False)
        self.assertEqual(report["resultado"], "compuesto")
        self.assertEqual(report["rondas_ejecutadas"], 1)
        self.assertEqual(report["cota_error"], 0)

    def test_cotas_para_cuatro_configuraciones(self):
        for rounds in (1, 5, 10, 20):
            result = primality_report(1009, rounds, bases=[2] * rounds)
            self.assertEqual(result["cota_error"], 4.0**-rounds)

    def test_reproducibilidad_y_precribado(self):
        r1 = primality_report(1009, 20, make_rng(26))
        r2 = primality_report(1009, 20, make_rng(26))
        self.assertEqual(r1, r2)
        discarded = primality_report(561, 20, make_rng(26))
        self.assertTrue(discarded["descartado_precribado"])
        self.assertEqual(discarded["rondas_ejecutadas"], 0)

    def test_rondas_y_bases_invalidas(self):
        for rounds in (0, -1):
            with self.assertRaises(ValueError):
                is_probable_prime(97, rounds)
        with self.assertRaises(ValueError):
            primality_report(1009, 5, bases=[2, 3])
        with self.assertRaises(ValueError):
            primality_report(1009, 1, bases=[1])


class TestGeneracion(unittest.TestCase):
    def test_candidatos_16_a_1024_bits(self):
        rng = make_rng(2026)
        for bits in SIZES:
            for _ in range(50):
                n = generate_candidate(bits, rng)
                self.assertEqual(n.bit_length(), bits)
                self.assertEqual(n % 2, 1)

    def test_minimo_y_tipos(self):
        self.assertEqual(generate_candidate(2, make_rng(1)), 3)
        for bits in (0, 1, -1):
            with self.assertRaises(ValueError):
                generate_candidate(bits)
        with self.assertRaises(TypeError):
            generate_candidate(True)

    def test_generacion_reproducible(self):
        for bits in (16, 64, 128):
            a = generate_probable_prime(bits, 10, make_rng(123), return_report=True)
            b = generate_probable_prime(bits, 10, make_rng(123), return_report=True)
            self.assertEqual(a, b)
            self.assertEqual(a["n"].bit_length(), bits)
            self.assertEqual(a["n"] % 2, 1)
            self.assertTrue(is_probable_prime(a["n"], 20, make_rng(8)))
            self.assertLessEqual(a["descartes_precribado"], a["candidatos"] - 1)

    def test_generacion_segura_por_defecto(self):
        with patch("primality.secrets.SystemRandom", return_value=make_rng(7)) as secure:
            n = generate_probable_prime(16, rounds=5)
            self.assertEqual(n.bit_length(), 16)
            secure.assert_called_once()
        with patch("primality.secrets.SystemRandom", return_value=make_rng(8)) as secure:
            n = generate_candidate(32)
            self.assertEqual(n.bit_length(), 32)
            secure.assert_called_once()

    def test_compuestos_garantizados(self):
        rng = make_rng(12345)
        for bits in SIZES:
            n = random_composite(bits, rng)
            self.assertEqual(n.bit_length(), bits)
            self.assertFalse(is_probable_prime(n, 20, make_rng(5)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
