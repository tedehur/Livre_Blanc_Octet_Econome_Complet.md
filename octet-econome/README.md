# Octet-Économe

Projet de démonstration et d’outil de compression binaire asymétrique basé sur le codage :

- Bit `1` = espace (`0x20`) sur 1 bit
- Bit `0` + octet brut = tout autre caractère sur 9 bits

## Objectif

Ce dépôt contient une structure de travail organisée autour de trois axes :

- `specs/` : documentation théorique et architecture
- `core-rust/` : moteur bas niveau en Rust sans allocation
- `tools-python/` : outils de production et démonstration

## Structure

```text
octet-econome/
├── README.md
├── LICENSE
├── CONTRIBUTING.md
├── core-rust/
│   ├── Cargo.toml
│   └── src/
│       └── lib.rs
├── tools-python/
│   ├── compiler_octet.py
│   └── honeypot_daemon.py
└── specs/
    └── whitepaper_fr.md
```

## Phase 1 : compresseur binaire réel

Le script `tools-python/compiler_octet.py` implémente un encodeur et un décodeur de flux binaire avec en-tête `OCTE` et vérification d’intégrité immédiate.

## Phase 2 : surveillance sécurisée

Le fichier `tools-python/honeypot_daemon.py` sert de base pour un démon de surveillance temps réel, en préparation de la couche de détection et d’analyse.

## Licence

Ce projet est distribué sous licence MIT.
