# Population Dashboard PyQt6

Application de bureau de gestion et d'analyse de profils individuels.

## Fonctions incluses

- Dashboard avec indicateurs et graphiques simples
- Gestion des personnes et photo de profil
- Emplois, formations et résultats sportifs liés à une personne
- Champs personnalisés administrables
- Recherche multicritère et export CSV
- Base SQLite créée automatiquement
- Thème moderne via `qt-modern-style`

## Installation

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

La base est créée dans `data/population.db` et les photos copiées dans `data/photos/`.

## Structure

- `app/db/database.py` : schéma et accès SQLite
- `app/ui/main_window.py` : fenêtre principale
- `app/ui/pages/` : dashboard, personnes, configuration
- `app/ui/dialogs/` : formulaires
- `app/services/` : stockage des photos et export

## Limites de cette première version

Cette base est un socle exécutable. Pour un déploiement multiutilisateur ou de grande ampleur, migrer vers PostgreSQL, ajouter authentification, rôles, journal d'audit, chiffrement et règles de conservation.

## Logo permanent dans la fenêtre principale

Le logo affiché en bas à gauche est chargé depuis :

```text
assets/logo.png
```

Pour utiliser votre propre logo, remplacez simplement ce fichier en conservant le même nom. L'image est redimensionnée automatiquement en conservant ses proportions.

## Modification avec Qt Designer

Les interfaces modifiables se trouvent dans `app/ui/forms/` :

- `MainWindow.ui` : menu latéral, zone centrale et logo permanent en bas à gauche ;
- `PersonsPage.ui` : recherche, boutons et tableau des personnes ;
- `SettingsPage.ui` : gestion des champs personnalisés ;
- `PersonDialog.ui` : formulaire d'identité, coordonnées et photo.

Ouvrez un fichier avec Qt Designer, modifiez les widgets, puis enregistrez-le. Aucune conversion `pyuic6` n'est nécessaire : l'application charge les fichiers `.ui` directement avec `PyQt6.uic.loadUi`.

Pour changer le logo, remplacez `assets/logo.png`. Dans `MainWindow.ui`, conservez le nom d'objet `logo_label` si vous souhaitez garder le chargement automatique de l'image.


##Génération de l'exécutable sous linux

pyinstaller --windowed --onefile --clean --name "MONTEREAU_DASHBOARD" --icon "data/icones/montereau.ico" --add-data="data/icones:data/icones" --add-data="app/ui/forms:app/ui/forms" --collect-all PyQt6 --collect-all qt_material --collect-all pyqtgraph  main.py

