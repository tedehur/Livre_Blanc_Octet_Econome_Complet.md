"""Octet-Économe - Preuve de concept

Format de fichier .octet (simple PoC):
- Première ligne: JSON header (utf-8) avec champs:
    - codes: mapping caractère -> bitstring
    - bit_length: nombre total de bits valides dans le payload
- Reste du fichier: payload binaire (bits empilés, MSB first dans chaque octet)

Ce script fournit des fonctions d'encodage/décodage et une interface CLI minimale.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
import heapq
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

@dataclass(order=True)
class Node:
    freq: int
    char: Optional[str] = None
    left: Optional['Node'] = None
    right: Optional['Node'] = None


def build_asymmetric_codes(text: str) -> Dict[str, str]:
    """Construit un dictionnaire de codes Huffman pour les caractères non-espace
    et assigne le code '1' à l'espace.
    """
    # Compter les caractères non-espace
    freq = Counter(c for c in text if c != ' ')

    heap = [Node(freq=count, char=ch) for ch, count in freq.items()]
    heapq.heapify(heap)

    if not heap:
        # Cas: texte vide ou ne contient que des espaces
        codes = {" ": "1"}
        return codes

    while len(heap) > 1:
        left = heapq.heappop(heap)
        right = heapq.heappop(heap)
        merged = Node(freq=left.freq + right.freq, left=left, right=right)
        heapq.heappush(heap, merged)

    root = heap[0]

    codes: Dict[str, str] = {}

    def generate_codes(node: Optional[Node], prefix: str) -> None:
        if node is None:
            return
        if node.char is not None:
            # Forcer le préfixe '0' pour tous les codes non-espace
            codes[node.char] = '0' + (prefix or '')
            return
        generate_codes(node.left, prefix + '0')
        generate_codes(node.right, prefix + '1')

    # Si la racine est une feuille (un seul caractère non-espace)
    if root.char is not None:
        codes[root.char] = '0'
    else:
        generate_codes(root, '')

    # Code réservé pour l'espace
    codes[' '] = '1'

    return codes


def encode_bits_from_text(text: str, codes: Dict[str, str]) -> Tuple[bytearray, int]:
    """Encode le texte en une séquence de bits puis les empile en octets.
    Retourne (bytes_payload, bit_length)
    """
    bit_str_parts = []
    for ch in text:
        bit = codes.get(ch)
        if bit is None:
            # Caractère inconnu: on peut choisir de l'ignorer ou lever une erreur
            raise ValueError(f"Caractère sans code: {repr(ch)}")
        bit_str_parts.append(bit)

    bit_str = ''.join(bit_str_parts)
    bit_len = len(bit_str)

    # Empaquetage MSB-first dans chaque octet
    b = bytearray()
    current = 0
    filled = 0  # bits currently in current (0..7)
    for bit_char in bit_str:
        current = (current << 1) | (1 if bit_char == '1' else 0)
        filled += 1
        if filled == 8:
            b.append(current & 0xFF)
            current = 0
            filled = 0
    if filled > 0:
        # Pad the remaining bits on the right (least significant bits)
        current = current << (8 - filled)
        b.append(current & 0xFF)

    return b, bit_len


def write_octet_file(output_path: str, text: str, codes: Optional[Dict[str, str]] = None) -> None:
    if codes is None:
        codes = build_asymmetric_codes(text)
    payload, bit_len = encode_bits_from_text(text, codes)

    header = {
        'codes': codes,
        'bit_length': bit_len,
    }
    with open(output_path, 'wb') as f:
        header_line = json.dumps(header, ensure_ascii=False).encode('utf-8') + b"\n"
        f.write(header_line)
        f.write(payload)


def read_octet_file(input_path: str) -> Tuple[Dict[str, str], int, bytearray]:
    with open(input_path, 'rb') as f:
        header_line = f.readline()
        header = json.loads(header_line.decode('utf-8'))
        payload = bytearray(f.read())
    codes = header['codes']
    bit_length = int(header['bit_length'])
    return codes, bit_length, payload


def decode_text_from_bits(codes: Dict[str, str], bit_length: int, payload: bytearray) -> str:
    # Construire la table inverse
    inv = {v: k for k, v in codes.items()}

    # Extraire les bits en MSB-first
    bits = []
    total_bits = 0
    for byte in payload:
        for i in range(7, -1, -1):
            if total_bits >= bit_length:
                break
            bits.append('1' if ((byte >> i) & 1) else '0')
            total_bits += 1
        if total_bits >= bit_length:
            break
    bit_str = ''.join(bits)

    # Parcourir et décoder
    out_chars = []
    buffer = ''
    for b in bit_str:
        buffer += b
        if buffer in inv:
            out_chars.append(inv[buffer])
            buffer = ''
    if buffer:
        # Bits restants non décodables
        raise ValueError('Payload ended with incomplete code sequence')
    return ''.join(out_chars)


def decode_from_file(input_path: str) -> str:
    codes, bit_length, payload = read_octet_file(input_path)
    return decode_text_from_bits(codes, bit_length, payload)


def main() -> None:
    parser = argparse.ArgumentParser(description='Octet-Économe - PoC encoder/decoder')
    parser.add_argument('--input', '-i', required=True, help='Chemin du fichier d\'entrée (texte ou .octet selon --decode)')
    parser.add_argument('--output', '-o', required=False, help='Chemin du fichier de sortie')
    parser.add_argument('--decode', action='store_true', help='Décoder un fichier .octet en texte')
    args = parser.parse_args()

    if args.decode:
        out = args.output or (args.input + '.decoded')
        text = decode_from_file(args.input)
        with open(out, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f'Décodé -> {out}')
    else:
        # Lire le texte d'entrée
        with open(args.input, 'r', encoding='utf-8') as f:
            text = f.read()
        out = args.output or (args.input + '.octet')
        write_octet_file(out, text)
        print(f'Encodé -> {out}')


if __name__ == '__main__':
    main()
