# Livre Blanc Octet-Économe

Ce dépôt contient le Livre Blanc présentant l'architecture "Octet-Économe" et une preuve de concept Python pour l'encodage asymétrique (espace = '1').

Quick start

1. Installer Python 3.8+.
2. Exemple d'encodage :

```bash
python -m tools.octet_compressor --input examples/sample.txt --output examples/sample.txt.octet
```

3. Exemple de décodage :

```bash
python -m tools.octet_compressor --decode --input examples/sample.txt.octet --output examples/sample.decoded.txt
```

Tests

Un test minimal est fourni dans tests/ ; lancez :

```bash
python -m pytest -q
```
