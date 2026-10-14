#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Octet-Économe - Compilateur Binaire Asymétrique (Public API)

Ce module expose une API simple et réutilisable pour compresser et décompresser
des données selon le schéma "Espace = 1 bit / Autre octet = 9 bits".

API principale
- compress(raw: bytes) -> bytes       : renvoie le payload .octet (avec en-tête)
- decompress(payload: bytes) -> bytes : renvoie les octets restaurés
- compress_file(in_path, out_path)
- decompress_file(in_path, out_path)

Exemples:
    from compiler_octet import compress, decompress
    payload = compress(b"Hello   world")
    original = decompress(payload)

Design notes:
- Les fonctions basses (OctetCompiler.compress_bytes / decompress_bytes)
  manipulent des buffers en mémoire ; les wrappers gèrent l'en-tête.
- Le format produit commence par b"OCTE" + 8-octets big-endian décrivant
  le nombre exact de bits utiles (pour éviter les ambiguïtés de padding).
"""

from __future__ import annotations

import argparse
import logging
import sys
from typing import Tuple

# Ré-export des symboles principaux (compatibilité)
__all__ = [
    "OctetCompiler",
    "compress",
    "decompress",
    "compress_file",
    "decompress_file",
    "pack_with_header",
    "unpack_with_header",
]

logger = logging.getLogger(__name__)

# On importe l'implémentation interne (déjà présente dans ce repo)
# Si ce fichier est exécuté depuis le répertoire tests, l'import relatif
# à partir du même répertoire fonctionnera.
try:
    from .compiler_octet import (
        OctetCompiler,
        pack_with_header,
        unpack_with_header,
    )
except Exception:
    import importlib.util
    import pathlib

    mod_path = pathlib.Path(__file__).resolve().parent / "compiler_octet.py"
    spec = importlib.util.spec_from_file_location("compiler_octet_impl", str(mod_path))
    _impl = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_impl)  # type: ignore

    OctetCompiler = _impl.OctetCompiler
    pack_with_header = _impl.pack_with_header
    unpack_with_header = _impl.unpack_with_header


def compress(raw: bytes) -> bytes:
    """Compress bytes and return a .octet payload including the header.

    Raises ValueError on invalid input types.
    """
    if not isinstance(raw, (bytes, bytearray)):
        raise ValueError("raw data must be bytes or bytearray")
    compressed_body, total_bits = OctetCompiler.compress_bytes(bytes(raw))
    payload = pack_with_header(compressed_body, total_bits)
    logger.debug("Compressed %d -> %d bytes (bits=%d)", len(raw), len(payload), total_bits)
    return payload


def decompress(payload: bytes) -> bytes:
    """Decompress a .octet payload (bytes) and return the original bytes.

    Raises ValueError if payload format is invalid.
    """
    if not isinstance(payload, (bytes, bytearray)):
        raise ValueError("payload must be bytes or bytearray")
    body, total_bits = unpack_with_header(bytes(payload))
    restored = OctetCompiler.decompress_bytes(body, total_bits)
    logger.debug("Decompressed payload -> %d bytes (bits=%d)", len(restored), total_bits)
    return bytes(restored)


def compress_file(in_path: str, out_path: str) -> None:
    """Compress a file on disk and write the .octet result to out_path."""
    with open(in_path, "rb") as f:
        raw = f.read()
    payload = compress(raw)
    with open(out_path, "wb") as f:
        f.write(payload)


def decompress_file(in_path: str, out_path: str) -> None:
    """Decompress a .octet file on disk and write the restored bytes to out_path."""
    with open(in_path, "rb") as f:
        payload = f.read()
    original = decompress(payload)
    with open(out_path, "wb") as f:
        f.write(original)


# --- CLI helpers -----------------------------------------------------------


def _read_bytes(path: str) -> bytes:
    if path == "-":
        return sys.stdin.buffer.read()
    with open(path, "rb") as f:
        return f.read()


def _write_bytes(path: str, data: bytes) -> None:
    if path == "-":
        sys.stdout.buffer.write(data)
        return
    with open(path, "wb") as f:
        f.write(data)


def _print_stats(orig_bytes: bytes, payload: bytes) -> None:
    orig_size = len(orig_bytes)
    comp_size = len(payload)
    space_count = orig_bytes.count(0x20)
    space_ratio = (space_count / orig_size) * 100 if orig_size else 0.0
    gain = (1 - (comp_size / orig_size)) * 100 if orig_size else 0.0
    print(
        f"Orig: {orig_size} bytes, Compiled: {comp_size} bytes, "
        f"spaces: {space_count} ({space_ratio:.1f}%), gain: {gain:+.2f}%",
        file=sys.stderr,
    )


# --- CLI entrypoint -------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="octet-econome",
        description="Octet-Économe CLI: compress/decompress files or stdin/stdout",
    )
    parser.add_argument("--version", action="version", version="Octet-Économe 0.1")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_comp = sub.add_parser("compress", help="Compress a file to .octet format")
    p_comp.add_argument("input", help="Input file path (use - for stdin)")
    p_comp.add_argument("output", help="Output file path (use - for stdout)")
    p_comp.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    p_decomp = sub.add_parser("decompress", help="Decompress a .octet file")
    p_decomp.add_argument("input", help="Input .octet path (use - for stdin)")
    p_decomp.add_argument("output", help="Output path (use - for stdout)")
    p_decomp.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.DEBUG if getattr(args, "verbose", False) else logging.INFO)

    try:
        if args.cmd == "compress":
            raw = _read_bytes(args.input)
            payload = compress(raw)
            _write_bytes(args.output, payload)
            _print_stats(raw, payload)

        elif args.cmd == "decompress":
            payload = _read_bytes(args.input)
            original = decompress(payload)
            _write_bytes(args.output, original)
            print(f"Decompressed: {len(original)} bytes", file=sys.stderr)

        else:
            parser.print_help()
            return 2

    except Exception as exc:  # pragma: no cover - surface errors to caller
        print(f"Error: {exc}", file=sys.stderr)
        logging.exception("CLI operation failed")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
""",
{"content":"import importlib.util
import io
import pathlib
import sys
import types

import pytest


def load_api_module():
    test_dir = pathlib.Path(__file__).resolve().parent
    mod_path = test_dir.parent / "api.py"
    spec = importlib.util.spec_from_file_location("api_module", str(mod_path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    return module


def test_cli_requires_subcommand(capsys):
    api = load_api_module()

    with pytest.raises(SystemExit) as exc:
        api.main([])

    assert exc.value.code == 2
    captured = capsys.readouterr()
    assert "usage:" in captured.err.lower()


def test_cli_version_flag(capsys):
    api = load_api_module()

    with pytest.raises(SystemExit) as exc:
        api.main(["--version"])

    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "Octet-Économe" in captured.out
    assert "0.1" in captured.out


def test_compress_stdin_stdout_binary_no_stats_on_stdout(monkeypatch):
    api = load_api_module()
    raw = b"Hello   world"

    stdin_obj = types.SimpleNamespace(buffer=io.BytesIO(raw))
    stdout_obj = types.SimpleNamespace(buffer=io.BytesIO())
    stderr_obj = io.StringIO()

    monkeypatch.setattr(sys, "stdin", stdin_obj)
    monkeypatch.setattr(sys, "stdout", stdout_obj)
    monkeypatch.setattr(sys, "stderr", stderr_obj)

    rc = api.main(["compress", "-", "-"])
    assert rc == 0

    payload = stdout_obj.buffer.getvalue()
    assert payload.startswith(b"OCTE")
    assert "Orig:" not in payload.decode("latin1", errors="ignore")
    assert "Orig:" in stderr_obj.getvalue()
