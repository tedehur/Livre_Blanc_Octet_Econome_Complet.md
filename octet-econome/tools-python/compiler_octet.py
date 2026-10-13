#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Octet-Économe - Compilateur Binaire Asymétrique (Référence PoC)

Améliorations et corrections :
- Vérification que le nombre de bits fourni dans l'en-tête est cohérent avec la taille du corps.
- Gestion robuste des accès aux octets lors de la lecture de bits (évite IndexError).
- Levée d'exceptions claires en cas de format invalide.
- Option de ligne de commande simple pour compresser/décompresser sans interface GUI (utile pour CI/tests).
"""

from __future__ import annotations

import argparse
import sys
import time
from typing import Tuple

try:
    # tkinter est optionnel (GUI de démonstration)
    import tkinter as tk
    from tkinter import filedialog, messagebox
except Exception:  # pragma: no cover - headless environments
    tk = None  # type: ignore
    filedialog = None  # type: ignore
    messagebox = None  # type: ignore


class OctetCompiler:
    """Moteur d'empaquetage binaire bas niveau (Bit-Packing)."""

    @staticmethod
    def compress_bytes(raw_data: bytes) -> Tuple[bytearray, int]:
        """
        Compresse un flux d'octets selon la règle du Bit Unique (Espace = 1).
        Retourne le tableau d'octets compressés et le nombre exact de bits utiles.
        """
        output = bytearray()
        bit_buffer = 0
        bit_count = 0
        total_bits = 0

        for byte in raw_data:
            if byte == 0x20:
                # Flag '1' pour espace
                bit_buffer = (bit_buffer << 1) | 1
                bit_count += 1
                total_bits += 1
            else:
                # Flag '0' suivi de l'octet (9 bits au total). Le bit de contrôle est 0
                bit_buffer = (bit_buffer << 9) | byte
                bit_count += 9
                total_bits += 9

            # Écrire des octets complets depuis le tampon de bits
            while bit_count >= 8:
                bit_count -= 8
                extracted_byte = (bit_buffer >> bit_count) & 0xFF
                output.append(extracted_byte)

            # Note : on ne masque pas explicitement bit_buffer car Python gère les grands entiers

        # Gestion du bourrage final (padding) s'il reste des bits en suspens
        if bit_count > 0:
            extracted_byte = (bit_buffer << (8 - bit_count)) & 0xFF
            output.append(extracted_byte)

        return output, total_bits

    @staticmethod
    def decompress_bytes(compressed_data: bytes, total_bits: int) -> bytearray:
        """
        Décompresse le flux binaire (vérification d'intégrité symétrique).

        Cette implémentation vérifie les bornes d'accès et l'intégrité des paramètres.
        """
        if total_bits < 0:
            raise ValueError("total_bits must be non-negative")

        body_len_bits = len(compressed_data) * 8
        if total_bits > body_len_bits:
            raise ValueError("total_bits is larger than available data (padding/inconsistent header)")

        output = bytearray()
        bit_index = 0
        mv = memoryview(compressed_data)

        def read_bit(idx: int) -> int:
            byte_pos = idx >> 3
            if byte_pos >= len(mv):
                raise ValueError("Attempted to read past end of compressed data")
            bit_offset = 7 - (idx & 7)
            return (mv[byte_pos] >> bit_offset) & 1

        while bit_index < total_bits:
            flag = read_bit(bit_index)
            if flag == 1:
                output.append(0x20)
                bit_index += 1
            else:
                if bit_index + 9 > total_bits:
                    # Header said there were more bits but pas assez pour un octet complet
                    raise ValueError("Incomplete 9-bit sequence at end of stream")
                char_val = 0
                for i in range(8):
                    char_val = (char_val << 1) | read_bit(bit_index + 1 + i)
                output.append(char_val)
                bit_index += 9

        return output


def pack_with_header(compressed_body: bytes | bytearray, total_bits: int) -> bytes:
    """
    Ajoute un en-tête binaire de 12 octets :
    - 4 octets : Magic Number b'OCTE'
    - 8 octets : Nombre exact de bits utiles (big-endian)
    """
    if total_bits < 0:
        raise ValueError("total_bits must be non-negative")
    return b"OCTE" + int(total_bits).to_bytes(8, byteorder="big") + bytes(compressed_body)


def unpack_with_header(file_bytes: bytes) -> Tuple[bytes, int]:
    """Lit et valide l'en-tête binaire d'un fichier .octet."""
    if len(file_bytes) < 12 or file_bytes[:4] != b"OCTE":
        raise ValueError("Format invalide : Signature binaire 'OCTE' introuvable.")
    total_bits = int.from_bytes(file_bytes[4:12], byteorder="big")
    body = file_bytes[12:]

    # Vérification simple : il ne peut y avoir plus de bits utiles que le corps disponible
    if total_bits > len(body) * 8:
        raise ValueError("Header inconsistant : total_bits > body_size_in_bits")

    return body, total_bits


# --- Interface minimale en ligne de commande pour tests/CI ---

def cli_compress(in_path: str, out_path: str) -> None:
    with open(in_path, "rb") as f:
        raw = f.read()
    compressed, bits = OctetCompiler.compress_bytes(raw)
    payload = pack_with_header(compressed, bits)
    with open(out_path, "wb") as f:
        f.write(payload)


def cli_decompress(in_path: str, out_path: str) -> None:
    with open(in_path, "rb") as f:
        file_bytes = f.read()
    body, bits = unpack_with_header(file_bytes)
    restored = OctetCompiler.decompress_bytes(body, bits)
    with open(out_path, "wb") as f:
        f.write(restored)


def run_gui():
    if tk is None:
        raise RuntimeError("Tkinter n'est pas disponible dans cet environnement")

    def process_compression():
        filepath = filedialog.askopenfilename(
            title="Sélectionner un fichier à compiler (HTML, JSON, Code)",
            filetypes=[
                ("Fichiers Web & Données", "*.html *.htm *.json *.xml *.txt *.css *.js"),
                ("Tous", "*.*"),
            ],
        )
        if not filepath:
            return

        try:
            start_time = time.perf_counter()
            with open(filepath, "rb") as f:
                raw_bytes = f.read()

            if not raw_bytes:
                messagebox.showwarning("Fichier vide", "Le fichier sélectionné est vide.")
                return

            compressed_body, total_bits = OctetCompiler.compress_bytes(raw_bytes)
            final_payload = pack_with_header(compressed_body, total_bits)

            output_path = filepath + ".octet"
            with open(output_path, "wb") as f:
                f.write(final_payload)

            body_check, bits_check = unpack_with_header(final_payload)
            restored_bytes = OctetCompiler.decompress_bytes(body_check, bits_check)
            integrity_ok = (restored_bytes == raw_bytes)

            elapsed_ms = (time.perf_counter() - start_time) * 1000

            orig_size = len(raw_bytes)
            comp_size = len(final_payload)
            space_count = raw_bytes.count(0x20)
            space_ratio = (space_count / orig_size) * 100 if orig_size else 0.0
            gain = (1 - (comp_size / orig_size)) * 100 if orig_size else 0.0

            status_integrity = "VALIDÉE (100% Bit-Exact)" if integrity_ok else "ÉCHEC CRITIQUE"

            messagebox.showinfo(
                "Audit de Compilation Octet-Économe",
                f"Statut d'intégrité : {status_integrity}\n"
                f"Temps de traitement : {elapsed_ms:.2f} ms\n\n"
                f"--- Métriques Physiques sur Disque ---\n"
                f"Taille originale : {orig_size:,} octets\n"
                f"Taille compilée (.octet) : {comp_size:,} octets (en-tête 12o inclus)\n"
                f"Densité d'espaces : {space_ratio:.1f}% ({space_count:,} espaces)\n"
                f"Gain net sur disque : {gain:+.2f} %\n\n"
                f"Fichier binaire généré :\n{output_path}",
            )

        except Exception as e:
            messagebox.showerror("Erreur système", str(e))

    root = tk.Tk()
    root.title("Octet-Économe - Compilateur Binaire Asymétrique")
    root.geometry("580x320")
    tk.Label(root, text="Compilateur Binaire Octet-Économe", font=("Arial", 15, "bold")).pack(pady=15)
    tk.Label(
        root,
        text="Encodage matériel : Espace = 1 bit | Autres = 9 bits (0 + Octet)",
        font=("Arial", 10),
    ).pack(pady=5)

    btn = tk.Button(
        root,
        text="Compiler et Vérifier un Fichier (HTML / JSON)",
        command=process_compression,
        bg="#1976D2",
        fg="white",
        font=("Arial", 11, "bold"),
        height=2,
        padx=15,
    )
    btn.pack(pady=35)
    tk.Label(
        root,
        text="Vérification symétrique intégrée - Zéro perte de données (UTF-8 / Binaire pur)",
        fg="gray",
    ).pack(side="bottom", pady=15)
    root.mainloop()


def main() -> int:
    parser = argparse.ArgumentParser(description="Octet-Économe : compresseur/décompresseur")
    sub = parser.add_subparsers(dest="cmd")

    p_comp = sub.add_parser("compress", help="Compresse un fichier en .octet")
    p_comp.add_argument("input")
    p_comp.add_argument("output")

    p_decomp = sub.add_parser("decompress", help="Décompresse un fichier .octet")
    p_decomp.add_argument("input")
    p_decomp.add_argument("output")

    p_gui = sub.add_parser("gui", help="Lancer l'interface graphique (si disponible)")

    args = parser.parse_args()

    try:
        if args.cmd == "compress":
            cli_compress(args.input, args.output)
        elif args.cmd == "decompress":
            cli_decompress(args.input, args.output)
        elif args.cmd == "gui":
            run_gui()
        else:
            parser.print_help()
            return 2
    except Exception as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
