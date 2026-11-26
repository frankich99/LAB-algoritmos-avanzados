"""Interfaz de línea de comandos para compresión, descompresión y verificación CMP9."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

from compression import ALG_NAMES, _unpack_header, get_compressor, inspect_payload


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def cmd_compress(args: argparse.Namespace) -> int:
    source = Path(args.input)
    data = source.read_bytes()
    comp = get_compressor(args.alg)
    payload = comp.compress(data)
    stats = comp.stats()

    verified = False
    if not args.no_verify:
        restored = comp.decompress(payload)
        if restored != data or _sha256(restored) != _sha256(data):
            raise RuntimeError("Fallo de verificación automática ida y vuelta")
        verified = True

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(payload)
    stats["verificado_roundtrip"] = verified
    stats["sha256_original"] = _sha256(data)
    stats["archivo_salida"] = str(output)

    if args.json:
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    else:
        print(
            f"[{stats['algoritmo']}] {source.name}: {stats['original_bytes']} B -> "
            f"{stats['total_bytes']} B (encabezado={stats['header_bytes']} B, "
            f"metadatos={stats['metadata_bytes']} B, datos={stats['data_bytes']} B, "
            f"ahorro={stats['savings_pct']:.2f}%, ida_y_vuelta={'OK' if verified else 'omitida'})"
        )
    return 0


def cmd_decompress(args: argparse.Namespace) -> int:
    payload = Path(args.input).read_bytes()
    alg_id, _ = _unpack_header(payload)
    alg_name = ALG_NAMES[alg_id]
    if args.alg != "auto":
        expected = get_compressor(args.alg)
        restored = expected.decompress(payload)
        stats = expected.stats()
    else:
        comp = get_compressor(alg_name)
        restored = comp.decompress(payload)
        stats = comp.stats()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(restored)
    stats["sha256_reconstruido"] = _sha256(restored)
    stats["archivo_salida"] = str(output)

    if args.json:
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    else:
        print(
            f"[{stats['algoritmo']}] Reconstruido {output}: {len(restored)} B "
            f"(sha256={stats['sha256_reconstruido'][:16]}...)"
        )
    return 0


def cmd_roundtrip(args: argparse.Namespace) -> int:
    data = Path(args.input).read_bytes()
    comp = get_compressor(args.alg)
    payload = comp.compress(data)
    stats = comp.stats()
    restored = comp.decompress(payload)
    h_orig = _sha256(data)
    h_rest = _sha256(restored)
    exact = restored == data and h_orig == h_rest
    stats["exact_match"] = exact
    stats["sha256_original"] = h_orig
    stats["sha256_reconstruido"] = h_rest
    if args.json:
        print(json.dumps(stats, indent=2, ensure_ascii=False))
    else:
        print(
            f"[{stats['algoritmo']}] Ida y vuelta {'EXITOSA' if exact else 'FALLIDA'}: "
            f"{stats['original_bytes']} B -> {stats['total_bytes']} B "
            f"(R={stats['compression_ratio']:.3f}, ahorro={stats['savings_pct']:.2f}%)"
        )
    return 0 if exact else 1


def cmd_inspect(args: argparse.Namespace) -> int:
    payload = Path(args.input).read_bytes()
    info = inspect_payload(payload)
    print(json.dumps(info, indent=2, ensure_ascii=False))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="CLI de compresión sin pérdida (Guía 09, UNSAAC - Grupo 5)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_comp = sub.add_parser("compress", help="Comprime un archivo en formato CMP9")
    p_comp.add_argument("--alg", required=True, choices=("huffman", "rle", "lz77"))
    p_comp.add_argument("-i", "--input", required=True, help="Archivo de entrada")
    p_comp.add_argument("-o", "--output", required=True, help="Archivo comprimido (.cmp9)")
    p_comp.add_argument("--no-verify", action="store_true", help="Omite verificación automática")
    p_comp.add_argument("--json", action="store_true", help="Salida JSON")
    p_comp.set_defaults(func=cmd_compress)

    p_dec = sub.add_parser("decompress", help="Descomprime un flujo CMP9")
    p_dec.add_argument("-i", "--input", required=True, help="Archivo .cmp9")
    p_dec.add_argument("-o", "--output", required=True, help="Archivo reconstruido")
    p_dec.add_argument("--alg", default="auto", choices=("auto", "huffman", "rle", "lz77"))
    p_dec.add_argument("--json", action="store_true", help="Salida JSON")
    p_dec.set_defaults(func=cmd_decompress)

    p_rt = sub.add_parser("roundtrip", help="Comprime, descomprime y verifica hash en memoria")
    p_rt.add_argument("--alg", required=True, choices=("huffman", "rle", "lz77"))
    p_rt.add_argument("-i", "--input", required=True, help="Archivo de entrada")
    p_rt.add_argument("--json", action="store_true", help="Salida JSON")
    p_rt.set_defaults(func=cmd_roundtrip)

    p_ins = sub.add_parser("inspect", help="Muestra encabezado y metadatos de un archivo CMP9")
    p_ins.add_argument("-i", "--input", required=True, help="Archivo .cmp9")
    p_ins.set_defaults(func=cmd_inspect)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
