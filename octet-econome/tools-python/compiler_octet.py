#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Octet-Économe - Compilateur Binaire Asymétrique (Référence PoC)
Implémente le codage matériel :
- Bit '1' (1 bit) = Espace (0x20)
- Bit '0' + 8 bits (9 bits) = Octet brut standard
"""

import os
import sys
import time
import tkinter as tk
from tkinter import filedialog, messagebox


class OctetCompiler:
    """Moteur d'empaquetage binaire bas niveau (Bit-Packing)."""

    @staticmethod
    def compress_bytes(raw_data: bytes) -> tuple[bytearray, int]:
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
                bit_buffer = (bit_buffer << 1) | 1
                bit_count += 1
                total_bits += 1
            else:
                bit_buffer = (bit_buffer << 9) | byte
                bit_count += 9
                total_bits += 9

            while bit_count >= 8:
                bit_count -= 8
                extracted_byte = (bit_buffer >> bit_count) & 0xFF
                output.append(extracted_byte)

        if bit_count > 0:
            extracted_byte = (bit_buffer << (8 - bit_count)) & 0xFF
            output.append(extracted_byte)

        return output, total_bits

    @staticmethod
    def decompress_bytes(compressed_data: bytes, total_bits: int) -> bytearray:
        """Décompresse le flux binaire (vérification d'intégrité symétrique)."""
        output = bytearray()
        bit_index = 0

        def read_bit(idx: int) -> int:
            byte_pos = idx >> 3
            bit_offset = 7 - (idx & 7)
            return (compressed_data[byte_pos] >> bit_offset) & 1

        while bit_index < total_bits:
            flag = read_bit(bit_index)
            if flag == 1:
                output.append(0x20)
                bit_index += 1
            else:
                if bit_index + 9 > total_bits:
                    break
                char_val = 0
                for i in range(8):
                    char_val = (char_val << 1) | read_bit(bit_index + 1 + i)
                output.append(char_val)
                bit_index += 9

        return output


def pack_with_header(compressed_body: bytearray, total_bits: int) -> bytes:
    """
    Ajoute un en-tête binaire de 12 octets :
    - 4 octets : Magic Number b'OCTE'
    - 8 octets : Nombre exact de bits utiles
    """
    header = b"OCTE" + total_bits.to_bytes(8, byteorder="big")
    return header + bytes(compressed_body)


def unpack_with_header(file_bytes: bytes) -> tuple[bytes, int]:
    """Lit et valide l'en-tête binaire d'un fichier .octet."""
    if len(file_bytes) < 12 or file_bytes[:4] != b"OCTE":
        raise ValueError("Format invalide : Signature binaire 'OCTE' introuvable.")
    total_bits = int.from_bytes(file_bytes[4:12], byteorder="big")
    return file_bytes[12:], total_bits


def run_gui():
    def process_compression():
        filepath = filedialog.askopenfilename(
            title="Sélectionner un fichier à compiler (HTML, JSON, Code)",
            filetypes=[("Fichiers Web & Données", "*.html *.htm *.json *.xml *.txt *.css *.js"), ("Tous", "*.*")]
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
            space_ratio = (space_count / orig_size) * 100
            gain = (1 - (comp_size / orig_size)) * 100

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
                f"Fichier binaire généré :\n{output_path}"
            )

        except Exception as e:
            messagebox.showerror("Erreur système", str(e))

    root = tk.Tk()
    root.title("Octet-Économe - Compilateur Binaire Asymétrique")
    root.geometry("580x320")
    tk.Label(root, text="Compilateur Binaire Octet-Économe", font=("Arial", 15, "bold")).pack(pady=15)
    tk.Label(root, text="Encodage matériel : Espace = 1 bit | Autres = 9 bits (0 + Octet)", font=("Arial", 10)).pack(pady=5)

    btn = tk.Button(
        root, text="Compiler et Vérifier un Fichier (HTML / JSON)",
        command=process_compression, bg="#1976D2", fg="white", font=("Arial", 11, "bold"), height=2, padx=15
    )
    btn.pack(pady=35)
    tk.Label(root, text="Vérification symétrique intégrée - Zéro perte de données (UTF-8 / Binaire pur)", fg="gray").pack(side="bottom", pady=15)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
