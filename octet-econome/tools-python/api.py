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

import logging
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
    # Attempt a local import when installed as a module package
    from .compiler_octet import (
        OctetCompiler,
        pack_with_header,
        unpack_with_header,
    )
except Exception:
    # Fallback to module file import in the same directory (file-based)
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
