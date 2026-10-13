#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Honeypot daemon placeholder for the Octet-Économe project.

Phase 2 - surveillance temps réel sécurisée.
Cette version de démonstration sert de point d'entrée à un démon de supervision,
avec logique de logging, écoute réseau et alertes minimalistes.
"""

import argparse
import logging
import os
import socket
import sys
from datetime import datetime


LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format=LOG_FORMAT)


def monitor_port(host: str = "127.0.0.1", port: int = 9000, timeout: float = 1.0) -> None:
    """Démonstre une écoute passive sur un port local."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(5)
    sock.settimeout(timeout)

    logging.info("Honeypot daemon lancé sur %s:%s", host, port)

    while True:
        try:
            conn, addr = sock.accept()
            now = datetime.utcnow().isoformat(timespec="seconds")
            logging.warning("Connexion détectée depuis %s à %s", addr, now)
            conn.sendall(b"Octet-Econome: monitor active\n")
            conn.close()
        except socket.timeout:
            continue
        except KeyboardInterrupt:
            logging.info("Arrêt du démon demandé.")
            break

    sock.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Honeypot daemon Octet-Économe")
    parser.add_argument("--host", default="127.0.0.1", help="Adresse d'écoute")
    parser.add_argument("--port", type=int, default=9000, help="Port TCP à surveiller")
    parser.add_argument("--timeout", type=float, default=1.0, help="Timeout d'écoute en secondes")
    parser.add_argument("-v", "--verbose", action="store_true", help="Mode verbeux")
    args = parser.parse_args()

    setup_logging(args.verbose)
    try:
        monitor_port(host=args.host, port=args.port, timeout=args.timeout)
    except OSError as exc:
        logging.error("Erreur réseau : %s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
