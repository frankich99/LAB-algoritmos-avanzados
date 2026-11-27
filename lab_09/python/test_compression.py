"""Suite de pruebas automatizadas para la Guía 09 (algoritmos de compresión)."""

from __future__ import annotations

import hashlib
from pathlib import Path
from random import Random
import tempfile
import unittest

import cli
from case_generator import build_benchmark_corpus, make_synthetic_png
from compression import (
    ALG_HUFFMAN,
    ALG_LZ77,
    ALG_RLE,
    CanonicalHuffmanCompressor,
    Compressor,
    LZ77Compressor,
    RLECompressor,
    average_code_length,
    build_code_lengths,
    build_huffman_tree,
    canonical_codes,
    decode_bits,
    encode_bits,
    entropy,
    frequencies,
    get_compressor,
    inspect_payload,
    lz77_decode,
    lz77_encode,
    lz77_tokenize,
    rle_decode,
    rle_encode,
    validate_prefix_codes,
)


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class TestEntropiaYCanonicidad(unittest.TestCase):
    def test_frecuencias_y_entropia(self):
        data = b"AAAABBCD"
        freq = frequencies(data)
        self.assertEqual(sum(freq.values()), len(data))
        self.assertAlmostEqual(entropy(freq), 1.75, places=12)
        self.assertEqual(entropy({}), 0.0)
        self.assertEqual(entropy({ord("A"): 10}), 0.0)
        self.assertAlmostEqual(entropy(frequencies(bytes(range(256)))), 8.0, places=12)

    def test_rechaza_tipo_str(self):
        with self.assertRaises(TypeError):
            frequencies("hola")  # type: ignore[arg-type]
        for comp in (CanonicalHuffmanCompressor(), RLECompressor(), LZ77Compressor()):
            with self.assertRaises(TypeError):
                comp.compress("hola")  # type: ignore[arg-type]

    def test_codigos_canonicos_guia(self):
        lengths = {ord("A"): 2, ord("B"): 2, ord("C"): 2, ord("D"): 3, ord("E"): 3}
        codes = canonical_codes(lengths)
        self.assertEqual(
            {chr(k): v for k, v in codes.items()},
            {"A": "00", "B": "01", "C": "10", "D": "110", "E": "111"},
        )
        self.assertTrue(validate_prefix_codes(codes))

    def test_propiedad_prefijo_y_desigualdad_huffman(self):
        data = b"En un lugar de la Mancha, de cuyo nombre no quiero acordarme..."
        freq = frequencies(data)
        tree = build_huffman_tree(freq)
        lengths = build_code_lengths(tree)
        codes = canonical_codes(lengths)
        self.assertTrue(validate_prefix_codes(codes))
        self.assertTrue(all(length >= 1 for length in lengths.values()))
        h_val = entropy(freq)
        l_val = average_code_length(freq, lengths)
        self.assertLessEqual(h_val, l_val + 1e-12)
        self.assertLess(l_val, h_val + 1.0)

    def test_frecuencias_iguales_huffman(self):
        # Con frecuencias iguales no se comparan palabras exactas por empates,
        # sino reconstrucción, propiedad prefijo y longitud promedio esperada.
        data = b"AABBCCDD" * 5
        freq = frequencies(data)
        tree = build_huffman_tree(freq)
        lengths = build_code_lengths(tree)
        codes = canonical_codes(lengths)
        self.assertTrue(validate_prefix_codes(codes))
        self.assertEqual(set(lengths.values()), {2})
        bits = encode_bits(data, codes)
        self.assertEqual(len(bits), 2 * len(data))
        self.assertEqual(decode_bits(bits, codes, len(data)), data)

    def test_canonicidad_consecutiva(self):
        lengths = {10: 2, 20: 2, 30: 3, 40: 3, 50: 3}
        codes = canonical_codes(lengths)
        self.assertEqual(int(codes[20], 2), int(codes[10], 2) + 1)
        self.assertEqual(int(codes[40], 2), int(codes[30], 2) + 1)
        self.assertEqual(int(codes[50], 2), int(codes[40], 2) + 1)


class TestCasosMinimosDeLaGuia(unittest.TestCase):
    ALL_FACTORIES = (CanonicalHuffmanCompressor, RLECompressor, LZ77Compressor)

    def _check_all_roundtrip(self, data: bytes) -> None:
        h_orig = _sha256(data)
        for factory in self.ALL_FACTORIES:
            comp = factory()
            self.assertIsInstance(comp, Compressor)
            payload = comp.compress(data)
            restored = comp.decompress(payload)
            self.assertEqual(restored, data)
            self.assertEqual(_sha256(restored), h_orig)
            st = comp.stats()
            self.assertEqual(
                st["header_bytes"] + st["metadata_bytes"] + st["data_bytes"],
                st["total_bytes"],
            )
            self.assertEqual(st["total_bytes"], len(payload))
            self.assertEqual(st["original_bytes"], len(data))

    def test_01_entrada_vacia(self):
        self._check_all_roundtrip(b"")

    def test_02_un_solo_byte(self):
        for val in (b"\x00", b"A", b"\xff"):
            with self.subTest(val=val):
                self._check_all_roundtrip(val)

    def test_03_unico_simbolo_repetido(self):
        self._check_all_roundtrip(b"K" * 500)
        self._check_all_roundtrip(b"\x00" * 5000)

    def test_04_todos_los_256_valores_de_byte(self):
        self._check_all_roundtrip(bytes(range(256)))
        self._check_all_roundtrip(bytes(range(255, -1, -1)) * 3)

    def test_05_bits_de_relleno_no_nulos_y_descarte(self):
        # Caso A: cantidad de bits de relleno != 0 y código '0' válido.
        # Sin conocer original_size, los ceros de relleno producirían símbolos extra.
        data = b"AAAB"
        comp = CanonicalHuffmanCompressor()
        payload = comp.compress(data)
        st = comp.stats()
        self.assertGreater(st["padding_bits"], 0)
        self.assertEqual(comp.decompress(payload), data)

        # Caso B: decode_bits descarta correctamente relleno de 0s o 1s al completar original_size.
        codes = {ord("A"): "0", ord("B"): "10"}
        bits = encode_bits(data, codes)
        self.assertEqual(decode_bits(bits + "000", codes, len(data)), data)
        self.assertEqual(decode_bits(bits + "111", codes, len(data)), data)

        # Caso C: si se altera un bit de relleno a 1 en el contenedor CMP9, se detecta corrupción.
        tampered = bytearray(payload)
        tampered[-1] |= 1
        with self.assertRaises(ValueError):
            comp.decompress(bytes(tampered))

    def test_06_corrida_mayor_que_65535_rle(self):
        data = b"\xab" * 70000 + b"\xcd" * 10
        payload = rle_encode(data)
        self.assertEqual(rle_decode(payload), data)
        info = inspect_payload(payload)
        # 70000 requiere 2 corridas (65535 + 4465) + 1 corrida para 0xCD = 3 corridas
        self.assertEqual(info["corridas"], 3)

    def test_07_patrones_repetidos_y_sin_repeticion_lz77(self):
        repetitive = b"UNSAAC_ALGORITMOS_" * 30
        non_repeating = bytes(range(256))
        overlapping = b"ABABABABABABABAB"
        self._check_all_roundtrip(repetitive)
        self._check_all_roundtrip(non_repeating)
        self._check_all_roundtrip(overlapping)
        self.assertLess(len(lz77_encode(repetitive)), len(repetitive))
        tokens, _ = lz77_tokenize(overlapping, trace=False)
        self.assertTrue(any(tok[0] == "M" and tok[1] < tok[2] for tok in tokens))

    def test_08_datos_pseudoaleatorios_semilla_fija(self):
        data = Random(202609).randbytes(4096)
        self._check_all_roundtrip(data)

    def test_09_texto_utf8_como_bytes(self):
        texto = "Algoritmos Avanzados — UNSAAC 2026: ñ, á, é, í, ó, ú, ü, ¡compresión!".encode("utf-8")
        self._check_all_roundtrip(texto)

    def test_10_multiples_llamadas_consecutivas_mismo_compresor(self):
        samples = [b"", b"X", b"AAAABBCD", bytes(range(256)), b"UNSAAC" * 50, b"X"]
        for factory in self.ALL_FACTORIES:
            comp = factory()
            first_seen: dict[bytes, bytes] = {}
            for sample in samples:
                payload = comp.compress(sample)
                st_c = comp.stats()
                if sample in first_seen:
                    self.assertEqual(payload, first_seen[sample])
                else:
                    first_seen[sample] = payload
                restored = comp.decompress(payload)
                st_d = comp.stats()
                self.assertEqual(restored, sample)
                self.assertEqual(st_c["total_bytes"], st_d["total_bytes"])
                self.assertEqual(st_c["original_bytes"], len(sample))

    def test_11_archivo_pequeno_metadatos_superan_ahorro(self):
        small = b"UNSAAC-2026-L09!"
        for factory in self.ALL_FACTORIES:
            comp = factory()
            payload = comp.compress(small)
            self.assertGreater(len(payload), len(small))
            self.assertGreater(comp.stats()["metadata_bytes"] + comp.stats()["header_bytes"], len(small))

    def test_12_corpus_completo_y_png(self):
        corpus = build_benchmark_corpus()
        self.assertEqual(len(corpus), 9)
        png_bytes = make_synthetic_png()
        self.assertTrue(png_bytes.startswith(b"\x89PNG\r\n\x1a\n"))
        for item in corpus:
            if len(item["data"]) <= 2048:
                self._check_all_roundtrip(item["data"])


class TestIntegridadYFlujosCorruptos(unittest.TestCase):
    def test_flujo_truncado_en_todas_las_posiciones(self):
        sample = b"ABABABCABABABAAABBBBCCCC"
        for factory in (CanonicalHuffmanCompressor, RLECompressor, LZ77Compressor):
            comp = factory()
            payload = comp.compress(sample)
            for cut in range(len(payload)):
                with self.subTest(alg=factory.__name__, cut=cut):
                    with self.assertRaises(ValueError):
                        comp.decompress(payload[:cut])

    def test_encabezados_y_algoritmo_inconsistente(self):
        h_payload = CanonicalHuffmanCompressor().compress(b"ABCD")
        r_payload = RLECompressor().compress(b"ABCD")
        l_payload = LZ77Compressor().compress(b"ABCD")

        self.assertEqual(inspect_payload(h_payload)["alg_id"], ALG_HUFFMAN)
        self.assertEqual(inspect_payload(r_payload)["alg_id"], ALG_RLE)
        self.assertEqual(inspect_payload(l_payload)["alg_id"], ALG_LZ77)

        # Magic inválido y versión inválida
        with self.assertRaises(ValueError):
            CanonicalHuffmanCompressor().decompress(b"XXXX" + h_payload[4:])
        bad_ver = bytearray(h_payload)
        bad_ver[4] = 99
        with self.assertRaises(ValueError):
            CanonicalHuffmanCompressor().decompress(bytes(bad_ver))

        # Mezcla de algoritmo con payload ajeno
        with self.assertRaises(ValueError):
            CanonicalHuffmanCompressor().decompress(r_payload)
        with self.assertRaises(ValueError):
            RLECompressor().decompress(l_payload)
        with self.assertRaises(ValueError):
            LZ77Compressor().decompress(h_payload)

        # Bytes sobrantes
        with self.assertRaises(ValueError):
            CanonicalHuffmanCompressor().decompress(h_payload + b"\x00")
        with self.assertRaises(ValueError):
            RLECompressor().decompress(r_payload + b"\x00")
        with self.assertRaises(ValueError):
            LZ77Compressor().decompress(l_payload + b"\x00")

    def test_rle_corrida_cero_invalida(self):
        payload = bytearray(rle_encode(b"AAA"))
        # En el último par >BH, poner count = 0
        payload[-2:] = b"\x00\x00"
        with self.assertRaises(ValueError):
            rle_decode(bytes(payload))

    def test_lz77_offset_invalido(self):
        # Construimos un payload con coincidencia en la posición 0 (offset imposible)
        comp = LZ77Compressor()
        payload = bytearray(comp.compress(b"ABCDEF"))
        # Primer byte del cuerpo (después de 6B header + 16B meta = 22) es flags=0x00
        payload[22] = 0x01  # marcar primer token como coincidencia
        with self.assertRaises(ValueError):
            lz77_decode(bytes(payload))

    def test_get_compressor(self):
        self.assertIsInstance(get_compressor("huffman"), CanonicalHuffmanCompressor)
        self.assertIsInstance(get_compressor("rle"), RLECompressor)
        self.assertIsInstance(get_compressor("lz77"), LZ77Compressor)
        with self.assertRaises(ValueError):
            get_compressor("desconocido")


class TestCLI(unittest.TestCase):
    def test_cli_compress_decompress_roundtrip_inspect(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_dir = Path(tmp)
            src = tmp_dir / "entrada.bin"
            cmp_file = tmp_dir / "salida.cmp9"
            dec_file = tmp_dir / "reconstruido.bin"
            data = "Prueba CLI UNSAAC 2026 ñ áéíóú — ".encode("utf-8") * 25
            src.write_bytes(data)

            for alg in ("huffman", "rle", "lz77"):
                self.assertEqual(
                    cli.main(["compress", "--alg", alg, "-i", str(src), "-o", str(cmp_file)]),
                    0,
                )
                self.assertEqual(cli.main(["inspect", "-i", str(cmp_file)]), 0)
                self.assertEqual(
                    cli.main(["decompress", "-i", str(cmp_file), "-o", str(dec_file)]),
                    0,
                )
                self.assertEqual(dec_file.read_bytes(), data)
                self.assertEqual(cli.main(["roundtrip", "--alg", alg, "-i", str(src)]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
