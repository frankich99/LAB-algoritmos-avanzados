"""Tres ejercicios resueltos de la sección 8 de la Guía 08."""

from transforms import (convolution_fft_raw, fft, ifft, multiply_fft,
                        naive_convolution)


def ntt_direct(values, root, modulus):
    """Oráculo cuadrático: evaluación de la definición de NTT, no benchmark."""
    n = len(values)
    return [sum(value * pow(root, j * k, modulus)
                for j, value in enumerate(values)) % modulus for k in range(n)]


def intt_direct(values, root, modulus):
    """NTT directa con raíz inversa y escala N^{-1} (oráculo)."""
    n = len(values)
    transformed = ntt_direct(values, pow(root, -1, modulus), modulus)
    return [x * pow(n, -1, modulus) % modulus for x in transformed]


def resuelto_1():
    a, b = [1, 2, 3], [4, 5]
    result = naive_convolution(a, b)
    assert result == [4, 13, 22, 15]
    return {"a": a, "b": b, "c": result}


def resuelto_2():
    a, b = [1, 2, 3], [4, 5]
    padded = a + [0]
    roundtrip = ifft(fft(padded))
    result = multiply_fft(a, b)
    assert result == [4, 13, 22, 15]
    assert max(abs(x - y) for x, y in zip(padded, roundtrip)) < 1e-7
    return {"fft": fft(padded), "ifft_fft": roundtrip,
            "producto": result, "error_imaginario": max(abs(z.imag) for z in
             convolution_fft_raw(a, b))}


def resuelto_3():
    a = [1, 2, 3, 4]
    transformed = ntt_direct(a, 4, 17)
    recovered = intt_direct(transformed, 4, 17)
    assert transformed == [10, 7, 15, 6] and recovered == a
    return {"entrada": a, "raiz": 4, "modulo": 17,
            "ntt": transformed, "intt": recovered}


if __name__ == "__main__":
    for number, function in enumerate((resuelto_1, resuelto_2, resuelto_3), 1):
        print(f"Resuelto {number}: {function()}")
