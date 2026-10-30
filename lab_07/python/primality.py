"""Pruebas de primalidad y generación de probables primos (Guía 07, UNSAAC).

Una ronda de Miller--Rabin devuelve (pasa, detalle). El detalle incluye n, a,
s, d y, si trace=True, todos los residuos examinados. ``pasa`` NO certifica
primalidad; ``False`` sí certifica composición para n impar >= 5.

La fuente por defecto es secrets.SystemRandom; inyectar random.Random solo sirve
para ensayos reproducibles, nunca para generar claves criptográficas.
"""

import secrets
from math import gcd, isqrt

__all__ = [
    "trial_division", "trial_division_with_count", "fermat_round", "fermat_test",
    "decompose", "miller_rabin_round", "primality_report", "is_probable_prime",
    "generate_candidate", "generate_probable_prime", "classify_bases",
]


def _integer(*values):
    for value in values:
        if type(value) is not int:
            raise TypeError("Se esperaba un entero, no bool ni otro tipo")


def _primes_up_to(limit):
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for p in range(2, isqrt(limit) + 1):
        if sieve[p]:
            sieve[p * p::p] = b"\x00" * len(sieve[p * p::p])
    return tuple(i for i in range(2, limit + 1) if sieve[i])


SMALL_PRIMES = _primes_up_to(997)


def trial_division_with_count(n):
    """Devuelve (es_primo, divisiones) con O(sqrt(n)) divisiones en el peor caso."""
    _integer(n)
    if n < 2:
        return False, 0
    if n in (2, 3):
        return True, 0
    if n % 2 == 0:
        return False, 1
    count = 1
    for divisor in range(3, isqrt(n) + 1, 2):
        count += 1
        if n % divisor == 0:
            return False, count
    return True, count


def trial_division(n):
    """Primalidad determinista por divisores impares hasta isqrt(n)."""
    return trial_division_with_count(n)[0]


def _mod_pow_counted(base, exponent, modulus):
    """Cuadrados sucesivos reales, no estimaciones de las operaciones de pow()."""
    result, base = 1 % modulus, base % modulus
    squares = products = 0
    while exponent:
        if exponent & 1:
            result = result * base % modulus
            products += 1
        exponent >>= 1
        if exponent:
            base = base * base % modulus
            squares += 1
    return result, squares, products


def _base(n, a):
    _integer(n, a)
    if n < 5 or n % 2 == 0:
        raise ValueError("La ronda requiere n impar >= 5")
    if not 2 <= a <= n - 2:
        raise ValueError("La base debe estar en [2, n-2]")


def fermat_round(n, a):
    """False demuestra composición; True solo dice que n pasa Fermat base a."""
    _base(n, a)
    if gcd(a, n) != 1:
        return False
    return _mod_pow_counted(a, n - 1, n)[0] == 1


def fermat_test(n, bases):
    """Fermat con bases configurables; ninguna cantidad de rondas da cota 4^-k."""
    _integer(n)
    bases = tuple(bases)
    if not bases:
        raise ValueError("Se requiere al menos una base")
    if n < 2:
        return {"resultado": "no_primo", "rondas_ejecutadas": 0,
                "bases_ejecutadas": [], "cuadrados_modulares": 0}
    if n in (2, 3):
        return {"resultado": "primo", "rondas_ejecutadas": 0,
                "bases_ejecutadas": [], "cuadrados_modulares": 0}
    if n % 2 == 0:
        return {"resultado": "compuesto", "rondas_ejecutadas": 0,
                "bases_ejecutadas": [], "cuadrados_modulares": 0}
    ran, squares, executed = 0, 0, []
    for a in bases:
        _base(n, a)
        executed.append(a)
        ran += 1
        if gcd(a, n) != 1:
            return {"resultado": "compuesto", "rondas_ejecutadas": ran,
                    "bases_ejecutadas": executed, "cuadrados_modulares": squares}
        residue, sq, _ = _mod_pow_counted(a, n - 1, n)
        squares += sq
        if residue != 1:
            return {"resultado": "compuesto", "rondas_ejecutadas": ran,
                    "bases_ejecutadas": executed, "cuadrados_modulares": squares}
    return {"resultado": "pasa_fermat", "rondas_ejecutadas": ran,
            "bases_ejecutadas": executed, "cuadrados_modulares": squares}


def decompose(n):
    """n impar >= 3: devuelve (s,d) con n-1 = 2**s * d y d impar."""
    _integer(n)
    if n < 3 or n % 2 == 0:
        raise ValueError("n debe ser impar y >= 3")
    s, d = 0, n - 1
    while d % 2 == 0:
        s, d = s + 1, d // 2
    return s, d


def miller_rabin_round(n, a, trace=False):
    """Devuelve (pasa, detalle); el detalle registra n, a, s, d y residuos.

    ``cuadrados_modulares`` incluye exponentiación y cadena; ``cuadrados_cadena``
    cuenta solo la cadena. Se ejecuta el algoritmo binario instrumentado.
    """
    _base(n, a)
    s, d = decompose(n)
    x, squares, products = _mod_pow_counted(a, d, n)
    residues = [x] if trace else []
    chain_squares = 0
    passed = x in (1, n - 1)
    reason = "residuo_inicial" if passed else "sin_menos_uno"
    if not passed:
        for _ in range(s - 1):
            x = x * x % n
            chain_squares += 1
            if trace:
                residues.append(x)
            if x == n - 1:
                passed, reason = True, "aparece_menos_uno"
                break
            if x == 1:
                reason = "raiz_no_trivial_de_uno"
                break
    return passed, {
        "n": n, "a": a, "s": s, "d": d, "residuos": residues,
        "cuadrados_cadena": chain_squares,
        "cuadrados_modulares": squares + chain_squares,
        "productos_modulares": products, "motivo": reason,
    }


def _presieve_divisor(n):
    for p in SMALL_PRIMES:
        if n % p == 0:
            return p
    return None


def primality_report(n, rounds=20, rng=None, *, bases=None, presieve=True):
    """Resultado auditable. Cota 4^-r solo para probable primo tras r rondas.

    Las bases suministradas permiten comparar métodos sobre entradas idénticas.
    La cota asume bases uniformes independientes; con bases fijas es solo una
    referencia teórica, no una garantía para esa ejecución concreta.
    """
    _integer(n, rounds)
    if rounds < 1:
        raise ValueError("rounds debe ser >= 1")
    report = {"n": n, "resultado": "no_primo", "rondas_solicitadas": rounds,
              "rondas_ejecutadas": 0, "bases_ejecutadas": [],
              "cuadrados_modulares": 0, "cuadrados_cadena": 0,
              "descartado_precribado": False, "cota_error": 0.0}
    if n < 2:
        return report
    if n in (2, 3):
        report["resultado"] = "primo"
        return report
    if n % 2 == 0:
        report["resultado"] = "compuesto"
        report["descartado_precribado"] = True
        return report
    if presieve:
        if n in SMALL_PRIMES:
            report["resultado"] = "primo"
            return report
        if _presieve_divisor(n) is not None:
            report["resultado"] = "compuesto"
            report["descartado_precribado"] = True
            return report
    if bases is not None:
        bases = tuple(bases)
        if len(bases) < rounds:
            raise ValueError("Faltan bases para las rondas solicitadas")
        chosen = bases[:rounds]
    else:
        generator = rng if rng is not None else secrets.SystemRandom()
        chosen = (generator.randrange(2, n - 1) for _ in range(rounds))
    for a in chosen:
        passed, detail = miller_rabin_round(n, a)
        report["rondas_ejecutadas"] += 1
        report["bases_ejecutadas"].append(a)
        report["cuadrados_modulares"] += detail["cuadrados_modulares"]
        report["cuadrados_cadena"] += detail["cuadrados_cadena"]
        if not passed:
            report["resultado"] = "compuesto"
            return report
    report["resultado"] = "probable_primo"
    report["cota_error"] = 4.0 ** (-rounds)
    return report


def is_probable_prime(n, rounds=20, rng=None):
    """Interfaz booleana de la guía. Para rondas/cota use primality_report()."""
    return primality_report(n, rounds, rng)["resultado"] in ("primo", "probable_primo")


def generate_candidate(bits, rng=None):
    """Candidato impar de exactamente bits bits; RNG seguro si no se especifica."""
    _integer(bits)
    if bits < 2:
        raise ValueError("bits debe ser >= 2")
    generator = rng if rng is not None else secrets.SystemRandom()
    return generator.getrandbits(bits) | (1 << (bits - 1)) | 1


def generate_probable_prime(bits, rounds=20, rng=None, *, return_report=False):
    """Muestreo de candidatos hasta obtener un probable primo de bits bits.

    Devuelve n por defecto; con return_report=True devuelve n y conteos reales.
    random.Random es SOLO para experimentos; sin rng utiliza SystemRandom.
    """
    _integer(bits, rounds)
    if bits < 2 or rounds < 1:
        raise ValueError("bits >= 2 y rounds >= 1 son obligatorios")
    generator = rng if rng is not None else secrets.SystemRandom()
    attempts = discarded = executed = squares = 0
    while True:
        n = generate_candidate(bits, generator)
        attempts += 1
        result = primality_report(n, rounds, generator)
        discarded += int(result["descartado_precribado"])
        executed += result["rondas_ejecutadas"]
        squares += result["cuadrados_modulares"]
        if result["resultado"] in ("primo", "probable_primo"):
            if return_report:
                return {"n": n, "bits": bits, "candidatos": attempts,
                        "descartes_precribado": discarded, "rondas_ejecutadas": executed,
                        "cuadrados_modulares": squares, "rondas_finales": result["rondas_ejecutadas"],
                        "cota_error": result["cota_error"]}
            return n


def classify_bases(n):
    """Enumera todas las bases de un compuesto impar pequeño (costo O(n))."""
    _integer(n)
    if n < 5 or n % 2 == 0 or trial_division(n):
        raise ValueError("Se requiere un compuesto impar >= 5")
    liars, witnesses = [], []
    for a in range(2, n - 1):
        passed, _ = miller_rabin_round(n, a)
        (liars if passed else witnesses).append(a)
    return {"n": n, "mentirosos_fuertes": liars, "testigos": witnesses,
            "fraccion_mentirosos": len(liars) / (n - 3)}
