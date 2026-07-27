from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
    QGroupBox,
    QCheckBox,
    QComboBox,
    QProgressBar,
)


class ImportDatabaseWindow(QWidget):

    def __init__(
        self,
        db,
        parent=None,
    ):
        super().__init__(parent)

        self.db = db
        self.source_database_path = None

        self.setWindowTitle(
            "Importation d'une base"
        )

        self.resize(700, 500)

        self.build_ui()

    def build_ui(self) -> None:

        main_layout = QVBoxLayout(self)

        title = QLabel(
            "Importation et fusion d'une base de données"
        )

        title.setStyleSheet(
            """
            QLabel {
                font-size: 20px;
                font-weight: bold;
            }
            """
        )

        main_layout.addWidget(title)

        description = QLabel(
            "Sélectionnez une base SQLite à importer. "
            "Les personnes existantes pourront être mises à jour "
            "et les nouvelles personnes seront ajoutées."
        )

        description.setWordWrap(True)

        main_layout.addWidget(description)

        self.build_file_section(main_layout)
        self.build_matching_section(main_layout)
        self.build_options_section(main_layout)
        self.build_progress_section(main_layout)
        self.build_buttons(main_layout)

        main_layout.addStretch()

    def build_file_section(
        self,
        parent_layout: QVBoxLayout,
    ) -> None:

        group = QGroupBox(
            "Base source"
        )

        layout = QHBoxLayout(group)

        self.path_edit = QLineEdit()
        self.path_edit.setReadOnly(True)
        self.path_edit.setPlaceholderText(
            "Sélectionner une base SQLite"
        )

        browse_button = QPushButton(
            "Parcourir"
        )

        browse_button.clicked.connect(
            self.select_database
        )

        layout.addWidget(
            self.path_edit,
            1,
        )
        layout.addWidget(
            browse_button
        )

        parent_layout.addWidget(group)

    def build_matching_section(
        self,
        parent_layout: QVBoxLayout,
    ) -> None:

        group = QGroupBox(
            "Correspondance des personnes"
        )

        layout = QFormLayout(group)

        self.match_field_combo = QComboBox()

        self.match_field_combo.addItem(
            "Matricule",
            "employee_number",
        )

        self.match_field_combo.addItem(
            "Adresse e-mail",
            "email",
        )

        self.match_field_combo.addItem(
            "Nom et prénom",
            "name",
        )

        layout.addRow(
            "Identifier les personnes avec :",
            self.match_field_combo,
        )

        parent_layout.addWidget(group)

    def build_options_section(
        self,
        parent_layout: QVBoxLayout,
    ) -> None:

        group = QGroupBox(
            "Options d'importation"
        )

        layout = QVBoxLayout(group)

        self.update_existing_checkbox = QCheckBox(
            "Mettre à jour les personnes existantes"
        )

        self.update_existing_checkbox.setChecked(
            True
        )

        self.import_custom_tables_checkbox = QCheckBox(
            "Importer les tables personnalisées"
        )

        self.import_custom_tables_checkbox.setChecked(
            True
        )

        self.import_custom_values_checkbox = QCheckBox(
            "Importer les valeurs personnalisées"
        )

        self.import_custom_values_checkbox.setChecked(
            True
        )

        self.create_missing_tables_checkbox = QCheckBox(
            "Créer les tables personnalisées manquantes"
        )

        self.create_missing_tables_checkbox.setChecked(
            True
        )

        layout.addWidget(
            self.update_existing_checkbox
        )

        layout.addWidget(
            self.import_custom_tables_checkbox
        )

        layout.addWidget(
            self.import_custom_values_checkbox
        )

        layout.addWidget(
            self.create_missing_tables_checkbox
        )

        parent_layout.addWidget(group)

    def build_progress_section(
        self,
        parent_layout: QVBoxLayout,
    ) -> None:

        self.progress_bar = QProgressBar()

        self.progress_bar.setRange(
            0,
            100,
        )

        self.progress_bar.setValue(0)

        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)

        parent_layout.addWidget(
            self.progress_bar
        )

        parent_layout.addWidget(
            self.result_label
        )

    def build_buttons(
        self,
        parent_layout: QVBoxLayout,
    ) -> None:

        layout = QHBoxLayout()

        layout.addStretch()

        self.import_button = QPushButton(
            "Importer et fusionner"
        )

        self.import_button.setEnabled(
            False
        )

        self.import_button.clicked.connect(
            self.start_import
        )

        close_button = QPushButton(
            "Fermer"
        )

        close_button.clicked.connect(
            self.close
        )

        layout.addWidget(
            self.import_button
        )

        layout.addWidget(
            close_button
        )

        parent_layout.addLayout(layout)

    def select_database(self) -> None:

        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner une base SQLite",
            "",
            "Bases SQLite (*.db *.sqlite *.sqlite3);;"
            "Tous les fichiers (*)",
        )

        if not filepath:
            return

        source_path = Path(filepath)

        try:
            current_path = Path(
                self.db.database_path
            ).resolve()

            if source_path.resolve() == current_path:
                QMessageBox.warning(
                    self,
                    "Importation",
                    "La base sélectionnée est déjà la base active.",
                )
                return

        except AttributeError:
            pass

        self.source_database_path = str(
            source_path
        )

        self.path_edit.setText(
            self.source_database_path
        )

        self.import_button.setEnabled(
            True
        )

        self.result_label.setText(
            "Base sélectionnée."
        )

    def start_import(self) -> None:

        if not self.source_database_path:
            QMessageBox.warning(
                self,
                "Importation",
                "Sélectionnez une base à importer.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Confirmer l'importation",
            "Voulez-vous fusionner cette base avec "
            "la base actuellement ouverte ?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        self.import_button.setEnabled(
            False
        )

        self.progress_bar.setValue(
            10
        )

        self.result_label.setText(
            "Importation en cours..."
        )

        try:
            result = self.db.import_database(
                source_path=self.source_database_path,
                match_field=(
                    self.match_field_combo.currentData()
                ),
                update_existing=(
                    self.update_existing_checkbox.isChecked()
                ),
                import_custom_tables=(
                    self.import_custom_tables_checkbox.isChecked()
                ),
                import_custom_values=(
                    self.import_custom_values_checkbox.isChecked()
                ),
                create_missing_tables=(
                    self.create_missing_tables_checkbox.isChecked()
                ),
            )

            self.progress_bar.setValue(
                100
            )

            created = result.get(
                "persons_created",
                result.get("created", 0),
            )

            updated = result.get(
                "persons_updated",
                result.get("updated", 0),
            )

            ignored = result.get(
                "persons_ignored",
                result.get("ignored", 0),
            )

            custom_records = result.get(
                "custom_records_created",
                0,
            )

            message = (
                f"Importation terminée.\n"
                f"Personnes ajoutées : {created}\n"
                f"Personnes mises à jour : {updated}\n"
                f"Personnes ignorées : {ignored}\n"
                f"Enregistrements personnalisés : "
                f"{custom_records}"
            )

            self.result_label.setText(
                message
            )

            QMessageBox.information(
                self,
                "Importation terminée",
                message,
            )

        except Exception as error:

            self.progress_bar.setValue(
                0
            )

            self.result_label.setText(
                "L'importation a échoué."
            )

            QMessageBox.critical(
                self,
                "Erreur d'importation",
                f"Impossible d'importer la base :\n{error}",
            )

        finally:
            self.import_button.setEnabled(
                True
            )