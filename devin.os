#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Surveille un fichier système (HONEYPOT_PATH) en comparant périodiquement
son clone (HONEYPOT_CLONE). Si le clone est modifié, une alerte est émise.
Usage: python3 honeypot_monitor.py --path /etc/passwd --clone /tmp/passwd.clone
"""
import argparse
import hashlib
import logging
import os
import shutil
import signal
import sys
import time
from typing import Optional

# -- Utilities --------------------------------------------------------------
CHUNK_SIZE = 65536


def calculate_hash(path: str) -> Optional[str]:
    """Calcule le SHA256 du fichier. Retourne None si lecture impossible."""
    if not os.path.exists(path):
        return None
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        logging.exception("Erreur en calculant le hash pour %s: %s", path, e)
        return None


def create_clone(src: str, dst: str) -> bool:
    """Crée ou met à jour un clone (copie) du fichier src vers dst."""
    if not os.path.exists(src):
        logging.error("Le fichier source n'existe pas: %s", src)
        return False
    try:
        # copie métadonnées avec copy2
        shutil.copy2(src, dst)
        logging.info("Clone créé/mis à jour: %s -> %s", src, dst)
        return True
    except Exception:
        logging.exception("Échec création du clone %s -> %s", src, dst)
        return False


def send_alert(message: str, alert_cmd: Optional[str]) -> None:
    """Action d'alerte: log + exécution d'une commande optionnelle (ex: webhook, mail)."""
    logging.critical("ALERTE: %s", message)
    if alert_cmd:
        try:
            rc = os.system(alert_cmd)
            logging.info("Commande d'alerte exécutée (rc=%s): %s", rc, alert_cmd)
        except Exception:
            logging.exception("Échec exécution de la commande d'alerte: %s", alert_cmd)


# -- Monitor ---------------------------------------------------------------
stop_requested = False


def handle_signal(signum, frame):
    global stop_requested
    logging.info("Signal reçu %s, arrêt demandé.", signum)
    stop_requested = True


def monitor_system(honeypot_path: str, clone_path: str, interval: int, alert_cmd: Optional[str]) -> bool:
    """Boucle de surveillance; retourne False si arrêt forcé pour cause d'erreur critique."""
    clone_hash = calculate_hash(clone_path)
    if not clone_hash:
        logging.info("Clone initial absent ou illisible; tentative de création.")
        if not create_clone(honeypot_path, clone_path):
            logging.error("Initialisation impossible - Création du clone échouée")
            return False
        clone_hash = calculate_hash(clone_path)
        if not clone_hash:
            logging.error("Impossible de calculer le hash du clone après création")
            return False

    logging.info("Clone initial hash: %s... (OK)", clone_hash[:10])

    # installer handlers pour arrêt propre
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    while not stop_requested:
        time.sleep(interval)

        # Vérification de l'existence du fichier système original
        if not os.path.exists(honeypot_path):
            logging.error("Le fichier système original est introuvable: %s", honeypot_path)
            send_alert(f"Fichier original introuvable: {honeypot_path}", alert_cmd)
            return False

        # Calcul du hash du clone (recréer si absent)
        if not os.path.exists(clone_path):
            logging.warning("Le clone a disparu; tentative de recréation.")
            if not create_clone(honeypot_path, clone_path):
                logging.error("Impossible de recréer le clone")
                send_alert("Impossible de recréer le clone", alert_cmd)
                continue

        current_hash = calculate_hash(clone_path)
        if not current_hash:
            logging.error("Erreur calcul hash du clone")
            continue

        # Vérification de l'intégrité du clone
        if current_hash != clone_hash:
            msg = (
                "ALERTE: Le clone a été modifié! "
                f"ancien_hash={clone_hash[:10]}..., nouveau_hash={current_hash[:10]}..."
            )
            send_alert(msg, alert_cmd)
            # mettre à jour la baseline si c'est souhaité (ici on ne l'update pas automatiquement)
            # clone_hash = current_hash  # décommenter si on veut accepter la nouvelle version comme baseline
        else:
            logging.debug("Système en sécurité - hash inchangé")

    logging.info("Arrêt de la surveillance demandé proprement.")
    return True


# -- Entrypoint ------------------------------------------------------------
def parse_args():
    p = argparse.ArgumentParser(description="Surveille un fichier via son clone (honeypot).")
    p.add_argument("--path", "-p", required=True, help="Chemin du fichier système original (HONEYPOT_PATH)")
    p.add_argument("--clone", "-c", required=True, help="Chemin du clone local à surveiller (HONEYPOT_CLONE)")
    p.add_argument("--interval", "-i", type=int, default=10, help="Intervalle de scan en secondes")
    p.add_argument("--alert-cmd", "-a", default=None, help="Commande shell à exécuter en cas d'alerte (optionnel)")
    p.add_argument("--log-level", "-l", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    honeypot_path = args.path
    clone_path = args.clone
    interval = max(1, args.interval)

    # Si le clone n'existe pas, tenter de le créer maintenant
    if not os.path.exists(clone_path):
        logging.info("Clone %s absent: tentative de création.", clone_path)
        if not create_clone(honeypot_path, clone_path):
            logging.error("Échec de la création du clone. Sortie.")
            sys.exit(1)

    ok = monitor_system(honeypot_path, clone_path, interval, args.alert_cmd)
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
