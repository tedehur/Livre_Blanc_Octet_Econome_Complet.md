# Octet-Économe — Whitepaper (français)

## 1. Problème visé

Le projet cherche à démontrer qu’un codage binaire asymétrique peut fortement réduire la taille de données contenant beaucoup d’espaces, tout en restant lisible, vérifiable et compatible avec des flux binaires réels.

## 2. Codage de référence

Le schéma choisi est le suivant :

- `1` bit = espace ASCII (`0x20`)
- `0` + 8 bits = octet brut standard

Cette convention est particulièrement efficace lorsque les fichiers contiennent de nombreuses séquences vides ou de grands blocs d’espaces, comme certains contenus HTML, JSON ou textes structurés.

## 3. Avantages techniques

- Compression native sur octets bruts
- Vérification d’intégrité par décompression immédiate
- En-tête binaire structuré (`OCTE` + longueur en bits)
- Capacité de rester compatible avec des fichiers binaires standards

## 4. Limites

Le système est très efficace sur les données très denses en espace, mais n’est pas toujours optimal sur les données aléatoires ou fortement compressées déjà. Il convient avant tout à des flux textuels structurés et à des démonstrations de codage bas niveau.

## 5. Architecture du dépôt

- `specs/` : documentation et points de design
- `core-rust/` : noyau bas niveau sans allocation
- `tools-python/` : outils, démonstration et contrôle de qualité

## 6. Objectif de la phase 1

Livrer un compilateur binaire réel, réversible et vérifié, capable de produire des fichiers `.octet` ayant une signature claire et un mécanisme d’audit intégré.

## 7. Objectif de la phase 2

Ajouter un démon de surveillance, de collecte de traces et de détection de comportements suspects dans des flux d’entrée. Cette couche prépare la sécurisation du système et l’analyse de trafic en temps réel.
