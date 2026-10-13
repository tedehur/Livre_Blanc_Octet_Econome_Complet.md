# Contribuer à Octet-Économe

Merci de votre intérêt pour le projet.

## Règles générales

- Garder la structure de dépôt cohérente : `specs/`, `core-rust/`, `tools-python/`.
- Privilégier les données binaires et les flux octets plutôt que les chaînes de caractères Python.
- Conserver l’architecture de codage : `espace = 1 bit`, `autre octet = 9 bits`.
- Documenter chaque changement sur un point de conception ou de compression.

## Workflow recommandé

1. Créer une branche dédiée.
2. Travailler sur un sous-domaine précis.
3. Vérifier le comportement avec un test de round-trip.
4. Ouvrir une pull request avec un résumé clair.

## Bonnes pratiques

- Éviter les dépendances inutiles.
- Préférer la clarté du protocole au code opaque.
- Rester compatible avec les fichiers binaires `.octet`.
- Conserver une vérification intégrité pour chaque enregistrement.

## Code de conduite

- Respecter les membres de la communauté.
- Favoriser des discussions techniques basées sur des faits.
- Ne pas introduire de dépendances non justifiées ni de code non vérifié.

## Questions

Pour toute question technique ou blocage, ouvrir une issue ou contacter le mainteneur du dépôt.
