

from __future__ import annotations

import json
import shutil
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from PyQt6 import uic
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHeaderView,
    QCalendarWidget,
    QAbstractScrollArea,
    QDateEdit,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidgetItem,
    QWidget,
    QPushButton,
    QTableWidget,
)

from app.ui.pages.custom_record_dialog import CustomRecordDialog

class PersonDialog(QDialog):
    """
    Dialogue de création et de modification d'une personne.

    Widgets attendus dans PersonDialog.ui :

    - personTabWidget       : QTabWidget
    - firsMatriculeEdit     : QLineEdit
    - firstNameEdit         : QLineEdit
    - lastNameEdit          : QLineEdit
    - birthDateEdit         : QDateEdit
    - sexComboBox           : QComboBox
    - professionEdit        : QLineEdit
    - socialCategoryEdit    : QLineEdit
    - cityEdit              : QLineEdit
    - notesEdit             : QPlainTextEdit ou QTextEdit
    - photoLabel            : QLabel
    - selectPhotoButton     : QPushButton
    - removePhotoButton     : QPushButton, facultatif
    - saveButton            : QPushButton
    - cancelButton          : QPushButton
    """

    UI_FILE = (
        Path(__file__).resolve().parent.parent
        / "forms"
        / "PersonDialog.ui"
    )

    PROJECT_ROOT = Path(__file__).resolve().parents[3]
    PHOTO_DIRECTORY = PROJECT_ROOT / "data" / "photos"

    def __init__(
        self,
        db: sqlite3.Connection,
        person_id: int | None = None,
        photo_dir: str='',
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self.db = db
        self.db.row_factory = sqlite3.Row

        self.person_id = person_id
        self.selected_photo_source: Path | None = None
        self.current_photo_path: str | None = None
        self.custom_table_widgets = {}
        self.photo_dir = Path(photo_dir)
        self.photo_dir.mkdir(parents=True, exist_ok=True)


        self.custom_field_widgets: dict[int, dict[str, Any]] = {}
        self.dynamic_category_pages: list[QWidget] = []

        uic.loadUi(str(self.UI_FILE), self)



        self.socialCategoryComboBox.addItem("Sélectionner...", None)

        self.socialCategoryComboBox.addItem("Agriculteurs exploitants", "1")
        self.socialCategoryComboBox.addItem("Artisans, commerçants et chefs d'entreprise", "2")
        self.socialCategoryComboBox.addItem("Cadres et professions intellectuelles supérieures", "3")
        self.socialCategoryComboBox.addItem("Professions intermédiaires", "4")
        self.socialCategoryComboBox.addItem("Employés", "5")
        self.socialCategoryComboBox.addItem("Ouvriers", "6")
        self.socialCategoryComboBox.addItem("Retraités", "7")
        self.socialCategoryComboBox.addItem("Autres personnes sans activité professionnelle", "8")

        self.birthDateEdit.setMinimumWidth(200)
        calendar = self.birthDateEdit.calendarWidget()
        calendar.setMinimumSize(350, 300)
        calendar.setNavigationBarVisible(True)
        calendar.setGridVisible(True)
        calendar.setStyleSheet("""
            QCalendarWidget {
                background-color: black;
                color: black;
            }

            QCalendarWidget QWidget#qt_calendar_navigationbar {
                background-color: #e9ecef;
                min-height: 40px;
            }

            QCalendarWidget QToolButton {
                color: black;
                background-color: transparent;
                min-width: 80px;
                min-height: 32px;
                font-size: 14px;
                font-weight: bold;
                border: none;
            }

            QCalendarWidget QToolButton:hover {
                background-color: #d5d8dc;
            }

            QCalendarWidget QToolButton#qt_calendar_prevmonth {
                min-width: 32px;
                max-width: 32px;
            }

            QCalendarWidget QToolButton#qt_calendar_nextmonth {
                min-width: 32px;
                max-width: 32px;
            }

            QCalendarWidget QSpinBox {
                color: black;
                background-color: white;
                min-width: 90px;
                min-height: 30px;
                font-size: 14px;
            }

            QCalendarWidget QAbstractItemView {
                color: black;
                background-color: black;
                selection-background-color: #4a90e2;
                selection-color: white;
            }
        """)

        self.birthDateEdit.setCalendarPopup(True)
        self.birthDateEdit.setDisplayFormat("dd/MM/yyyy")
        self.birthDateEdit.setDate(QDate.currentDate())

        calendar.setVerticalHeaderFormat(
            QCalendarWidget.VerticalHeaderFormat.NoVerticalHeader
        )
        self.fixed_tab_count = self.personTabWidget.count()
        self.build_custom_table_tabs()

        self._configure_interface()
        self._connect_signals()

        self.build_custom_category_tabs()

        if self.person_id is not None:
            self.load_person()
            self.load_custom_field_values()
            self.load_all_custom_tables()

    #-----------------------------------------------------------------
    # chargement des valeurs custom des pax sélectioné
    #-----------------------------------------------------------------
    def load_all_custom_tables(self) -> None:
        for table_id, table_widget in self.custom_table_widgets.items():

            fields = table_widget.property("custom_table_fields") or []

            self.load_custom_table_records(
                table_id=table_id,
                table_widget=table_widget,
                fields=fields,
            )

    def load_custom_table_records(
            self,
            table_id: int,
            table_widget,
            fields: list,
    ) -> None:
        table_widget.setRowCount(0)

        if self.person_id is None:
            return

        records = self.db.get_custom_records(
            person_id=self.person_id,
            table_id=table_id,
        )

        for record in records:
            record_id = int(record["id"])

            value_rows = self.db.get_custom_record_values(
                record_id
            )

            values_by_field = {
                int(row["field_id"]): row["value"]
                for row in value_rows
            }

            row_index = table_widget.rowCount()
            table_widget.insertRow(row_index)

            for column_index, field in enumerate(fields):
                field_id = int(field["id"])
                field_type = str(field["field_type"]).lower()

                raw_value = values_by_field.get(field_id)

                displayed_value = self.format_custom_value(
                    raw_value,
                    field_type,
                    field,
                )

                item = QTableWidgetItem(displayed_value)

                item.setData(
                    Qt.ItemDataRole.UserRole,
                    record_id,
                )

                table_widget.setItem(
                    row_index,
                    column_index,
                    item,
                )



    def format_custom_value(
            self,
            value,
            field_type: str,
            field: dict,
    ) -> str:
        """
        Transforme une valeur stockée en base en texte affichable
        dans le QTableWidget.
        """

        if value is None:
            return ""

        field_type = field_type.lower()

        if field_type in ("text", "multiline"):
            return str(value)

        elif field_type == "integer":
            try:
                return str(int(value))
            except Exception:
                return str(value)

        elif field_type == "decimal":
            try:
                return f"{float(value):.2f}"
            except Exception:
                return str(value)

        elif field_type == "boolean":
            return "Oui" if str(value).lower() in (
                "1",
                "true",
                "yes",
                "oui",
            ) else "Non"

        elif field_type == "date":
            try:
                yyyy, mm, dd = str(value).split("-")
                return f"{dd}/{mm}/{yyyy}"
            except Exception:
                return str(value)

        elif field_type == "choice":
            return str(value)

        elif field_type == "csv_choice":
            # Ici la base contient la valeur, on affiche le libellé
            return self.db.get_csv_choice_label(
                field,
                value,
            )

        elif field_type == "file":
            return Path(str(value)).name

        return str(value)

    def refresh_custom_table(
            self,
            table_id: int,
    ) -> None:
        """
        Recharge le contenu d'une table personnalisée.
        """

        table_widget = self.custom_table_widgets.get(table_id)

        if table_widget is None:
            return

        fields = table_widget.property("custom_fields")

        if fields is None:
            fields = [
                dict(row)
                for row in self.db.get_custom_table_fields(table_id)
            ]
            table_widget.setProperty("custom_fields", fields)

        self.load_custom_table_records(
            table_id=table_id,
            table_widget=table_widget,
            fields=fields,
        )

    def edit_custom_record(
            self,
            table_id: int,
            table_widget,
    ):
        row = table_widget.currentRow()

        if row < 0:
            return

        item = table_widget.item(row, 0)

        if item is None:
            return

        record_id = item.data(Qt.ItemDataRole.UserRole)

        if record_id is None:
            QMessageBox.warning(
                self,
                "Modification",
                "Impossible de retrouver l'enregistrement."
            )
            return

        dialog = CustomRecordDialog(
            db=self.db,
            table_id=table_id,
            person_id=self.person_id,
            record_id=record_id,
            parent=self,
        )

        if not dialog.exec():
            return

        self.db.save_custom_record(
            person_id=self.person_id,
            table_id=table_id,
            record_id=record_id,
            values=dialog.values(),
        )

        self.refresh_custom_table(table_id)
    # ------------------------------------------------------------------
    # Initialisation de l'interface
    # ------------------------------------------------------------------
    def build_custom_table_tabs(self) -> None:
        """
        Supprime les anciens onglets dynamiques puis les recrée
        depuis la configuration.
        """

        # Suppression des anciens onglets dynamiques.
        while self.personTabWidget.count() > self.fixed_tab_count:
            index = self.personTabWidget.count() - 1

            widget = self.personTabWidget.widget(index)

            self.personTabWidget.removeTab(index)

            if widget is not None:
                widget.deleteLater()

        tables = self.db.get_enabled_custom_tables()


        existing_names: set[str] = set()

        for table in tables:
            table_id = int(table["id"])
            table_name = str(table["name"])
            table_label = str(table["label"])


            # Protection supplémentaire contre les doublons venant de la base.
            if table_name in existing_names:
                continue

            existing_names.add(table_name)


            page = QWidget()

            # Permet d'identifier précisément l'onglet dynamique.
            page.setProperty("custom_table_id", table_id)
            page.setProperty("custom_table_name", table_name)


            layout = QVBoxLayout(page)

            #if bool(table["allow_multiple"]):
            self.build_multiple_record_table(
                    page=page,
                    layout=layout,
                    table_definition=table,
                )
            '''
            else:
                self.build_single_record_form(
                    page=page,
                    layout=layout,
                    table_definition=table,
                )
            '''

            self.personTabWidget.addTab(
                page,
                table_label,
            )

    def delete_custom_record(
            self,
            table_id: int,
            table_widget,
    ) -> None:
        row = table_widget.currentRow()

        if row < 0:
            QMessageBox.information(
                self,
                "Suppression",
                "Sélectionnez une ligne à supprimer.",
            )
            return

        first_item = table_widget.item(row, 0)

        if first_item is None:
            QMessageBox.warning(
                self,
                "Suppression",
                "Impossible de retrouver l'enregistrement.",
            )
            return

        record_id = first_item.data(
            Qt.ItemDataRole.UserRole
        )

        if record_id is None:
            QMessageBox.warning(
                self,
                "Suppression",
                "L'identifiant de l'enregistrement est introuvable.",
            )
            return

        answer = QMessageBox.question(
            self,
            "Confirmer la suppression",
            "Voulez-vous supprimer cet enregistrement ?",
            QMessageBox.StandardButton.Yes
            | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.db.delete_custom_record(
                record_id=int(record_id),
                person_id=self.person_id,
                table_id=table_id,
            )

            self.refresh_custom_table(table_id)

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erreur",
                "Impossible de supprimer l'enregistrement :\n"
                f"{error}",
            )

    def build_single_record_form(
            self,
            page: QWidget,
            layout: QVBoxLayout,
            table_definition: dict,
    ) -> None:

        table_id = int(table_definition["id"])

        form = QFormLayout()

        fields = [
            dict(row)
            for row in self.db.get_custom_table_fields(table_id)
            if bool(row["enabled"])
        ]

        # Dictionnaire des widgets de saisie
        widgets = {}

        for field in fields:

            widget = self.create_widget(field)

            widgets[int(field["id"])] = widget

            label = field["label"]

            if field["required"]:
                label += " *"

            form.addRow(label, widget)

        layout.addLayout(form)

        # Boutons
        buttons = QHBoxLayout()

        save_button = QPushButton("Enregistrer")
        buttons.addStretch()
        buttons.addWidget(save_button)

        layout.addLayout(buttons)

        # Sauvegarde des métadonnées dans la page
        page.setProperty("table_id", table_id)
        page.setProperty("custom_fields", fields)
        page.setProperty("custom_widgets", widgets)

        # Chargement des valeurs existantes
        if self.person_id is not None:
            self.load_single_record(page)

        save_button.clicked.connect(
            lambda checked=False, p=page:
            self.save_single_record(p)
        )
    def build_multiple_record_table(
            self,
            page,
            layout,
            table_definition,
    ) -> None:


        table_id = table_definition["id"]
        fields = self.db.get_custom_table_fields(table_id)

        toolbar = QHBoxLayout()

        add_button = QPushButton("Ajouter")
        edit_button = QPushButton("Modifier")
        delete_button = QPushButton("Supprimer")


        toolbar.addWidget(add_button)
        toolbar.addWidget(edit_button)
        toolbar.addWidget(delete_button)
        toolbar.addStretch()

        layout.addLayout(toolbar)

        custom_fields = [
            dict(row)
            for row in self.db.get_custom_table_fields(table_id)
        ]


        table_widget = QTableWidget()
        table_widget.setColumnCount(len(fields))
        table_widget.setHorizontalHeaderLabels(
            [field["label"] for field in fields]
        )

        add_button.clicked.connect(
            lambda checked=False, current_table_id=table_id:
            self.add_custom_record(current_table_id)
        )

        edit_button.clicked.connect(
            lambda checked=False,
                   table_id=table_id,
                   table_widget=table_widget:
            self.edit_custom_record(table_id, table_widget)
        )

        delete_button.clicked.connect(
            lambda checked=False,
                   current_table_id=table_id,
                   current_table=table_widget:
            self.delete_custom_record(
                current_table_id,
                current_table,
            )
        )
        self.configure_table_widget(table_widget)
        table_widget.setProperty("custom_table_fields", custom_fields)

        self.custom_table_widgets[page.property("custom_table_id")]=table_widget


        layout.addWidget(table_widget)


    def add_custom_record(
            self,
            table_id: int,
    ) -> None:

        if self.person_id is None:
            QMessageBox.warning(
                self,
                "Personne non enregistrée",
                "Vous devez d'abord enregistrer la personne "
                "avant d'ajouter un élément personnalisé.",
            )
            return

        dialog = CustomRecordDialog(
            db=self.db,
            table_id=table_id,
            person_id=self.person_id,
            parent=self,
        )

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            self.db.save_custom_record(
                person_id=self.person_id,
                table_id=table_id,
                values=dialog.values(),
            )

            self.refresh_custom_table(
                table_id
            )

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erreur",
                "Impossible d'enregistrer les données :\n"
                f"{error}",
            )
    def configure_table_widget(self, table):
        header = table.horizontalHeader()

        # Les colonnes occupent toute la largeur disponible
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Ascenseur horizontal si nécessaire
        table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Ascenseur vertical si nécessaire
        table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Le tableau s'agrandit avec la fenêtre
        table.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContentsOnFirstShow
        )
    def _configure_interface(self) -> None:
        self.PHOTO_DIRECTORY.mkdir(parents=True, exist_ok=True)

        self.birthDateEdit.setCalendarPopup(True)
        self.birthDateEdit.setDisplayFormat("dd/MM/yyyy")

        # Une date minimale peut représenter une valeur vide.
        self.birthDateEdit.setMinimumDate(QDate(1900, 1, 1))
        self.birthDateEdit.setSpecialValueText("Non renseignée")
        self.birthDateEdit.setDate(self.birthDateEdit.minimumDate())

        if self.sexComboBox.count() == 0:
            self.sexComboBox.addItems(
                [
                    "",
                    "Femme",
                    "Homme",
                    "Autre",
                    "Non renseigné",
                ]
            )

        self.photoLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.photoLabel.setText("Aucune photo")
        self.photoLabel.setMinimumSize(180, 180)
        self.photoLabel.setScaledContents(False)

        if self.person_id is None:
            self.setWindowTitle("Ajouter une personne")
        else:
            self.setWindowTitle("Modifier une personne")

    def _connect_signals(self) -> None:
        self.saveButton.clicked.connect(self.save)
        self.cancelButton.clicked.connect(self.reject)
        self.selectPhotoButton.clicked.connect(self.select_photo)

        if hasattr(self, "removePhotoButton"):
            self.removePhotoButton.clicked.connect(self.remove_photo)

    # ------------------------------------------------------------------
    # Catégories et champs personnalisés
    # ------------------------------------------------------------------

    def clear_custom_category_tabs(self) -> None:
        """
        Supprime uniquement les onglets dynamiques déjà créés.
        Les onglets fixes du fichier .ui sont conservés.
        """
        for page in self.dynamic_category_pages:
            index = self.personTabWidget.indexOf(page)

            if index >= 0:
                self.personTabWidget.removeTab(index)

            page.deleteLater()

        self.dynamic_category_pages.clear()
        self.custom_field_widgets.clear()

    def get_custom_field_categories(self) -> list[sqlite3.Row]:
        return self.db.fetch_all(
            """
            SELECT
                id,
                name,
                description,
                display_order
            FROM custom_field_category
            WHERE enabled = 1
            ORDER BY display_order, name
            """
        )

    def get_fields_for_category(
            self,
            category_id: int,
    ) -> list[sqlite3.Row]:
        return self.db.fetch_all(
            """
            SELECT
                id,
                name,
                field_type,
                configuration,
                required,
                display_order
            FROM custom_field_definition
            WHERE category_id = ?
              AND enabled = 1
            ORDER BY display_order, name
            """,
            (category_id,),
        )

    def build_custom_category_tabs(self) -> None:
        self.clear_custom_category_tabs()

        categories = self.get_custom_field_categories()

        for category in categories:
            category_id = int(category["id"])
            category_name = str(category["name"])
            description = category["description"]

            page = QWidget()
            page.setObjectName(f"customCategoryPage_{category_id}")

            page_layout = QVBoxLayout(page)
            page_layout.setContentsMargins(0, 0, 0, 0)

            scroll_area = QScrollArea(page)
            scroll_area.setWidgetResizable(True)
            scroll_area.setFrameShape(QScrollArea.Shape.NoFrame)

            form_container = QWidget()
            form_layout = QFormLayout(form_container)

            form_layout.setContentsMargins(20, 20, 20, 20)
            form_layout.setHorizontalSpacing(20)
            form_layout.setVerticalSpacing(12)
            form_layout.setFieldGrowthPolicy(
                QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow
            )

            if description:
                description_label = QLabel(str(description))
                description_label.setWordWrap(True)
                description_label.setObjectName("categoryDescriptionLabel")

                form_layout.addRow(description_label)

            fields = self.get_fields_for_category(category_id)

            if not fields:
                empty_label = QLabel(
                    "Aucun champ n'est défini dans cette catégorie."
                )
                empty_label.setWordWrap(True)
                form_layout.addRow(empty_label)

            for field in fields:
                field_id = int(field["id"])
                field_name = str(field["name"])
                field_type = str(field["field_type"])
                required = bool(field["required"])

                configuration = self.parse_configuration(
                    field["configuration"]
                )

                widget = self.create_custom_field_widget(
                    field_type=field_type,
                    config=configuration,
                )

                widget.setObjectName(f"customField_{field_id}")

                label_text = field_name

                if required:
                    label_text += " *"

                label = QLabel(label_text)
                label.setBuddy(widget)

                form_layout.addRow(label, widget)

                self.custom_field_widgets[field_id] = {
                    "widget": widget,
                    "type": field_type,
                    "required": required,
                    "name": field_name,
                    "configuration": configuration,
                    "category_id": category_id,
                }

            scroll_area.setWidget(form_container)
            page_layout.addWidget(scroll_area)

            self.personTabWidget.addTab(page, category_name)
            self.dynamic_category_pages.append(page)

    @staticmethod
    def parse_configuration(configuration: Any) -> dict[str, Any]:
        if configuration is None:
            return {}

        if isinstance(configuration, dict):
            return configuration

        try:
            parsed = json.loads(str(configuration))

            if isinstance(parsed, dict):
                return parsed

        except (json.JSONDecodeError, TypeError):
            pass

        return {}

    def create_custom_field_widget(
        self,
        field_type: str,
        config: dict[str, Any],
    ) -> QWidget:
        field_type = field_type.strip().lower()

        if field_type == "text":
            widget = QLineEdit()
            widget.setPlaceholderText(
                str(config.get("placeholder", ""))
            )

            max_length = config.get("max_length")

            if max_length is not None:
                widget.setMaxLength(int(max_length))

            return widget

        if field_type == "multiline":
            widget = QPlainTextEdit()
            widget.setPlaceholderText(
                str(config.get("placeholder", ""))
            )

            height = int(config.get("height", 100))
            widget.setMinimumHeight(height)

            return widget

        if field_type == "integer":
            widget = QSpinBox()

            minimum = int(config.get("min", -999_999))
            maximum = int(config.get("max", 999_999))
            step = int(config.get("step", 1))

            widget.setRange(minimum, maximum)
            widget.setSingleStep(step)

            suffix = config.get("suffix")

            if suffix:
                widget.setSuffix(str(suffix))

            return widget

        if field_type == "decimal":
            widget = QDoubleSpinBox()

            minimum = float(config.get("min", -999_999.0))
            maximum = float(config.get("max", 999_999.0))
            step = float(config.get("step", 0.1))
            decimals = int(config.get("decimals", 2))

            widget.setRange(minimum, maximum)
            widget.setSingleStep(step)
            widget.setDecimals(decimals)

            suffix = config.get("suffix")

            if suffix:
                widget.setSuffix(str(suffix))

            return widget

        if field_type == "date":
            widget = QDateEdit()
            widget.setCalendarPopup(True)
            widget.setDisplayFormat(
                str(config.get("format", "dd/MM/yyyy"))
            )

            widget.setMinimumDate(QDate(1900, 1, 1))

            if bool(config.get("allow_empty", True)):
                widget.setSpecialValueText("Non renseignée")
                widget.setDate(widget.minimumDate())
            else:
                widget.setDate(QDate.currentDate())

            return widget

        if field_type == "boolean":
            widget = QCheckBox()

            label = config.get("label")

            if label:
                widget.setText(str(label))

            return widget

        if field_type == "choice":
            widget = QComboBox()

            allow_empty = bool(config.get("allow_empty", True))

            if allow_empty:
                widget.addItem("")

            choices = config.get("choices", [])

            if isinstance(choices, list):
                widget.addItems([str(choice) for choice in choices])

            return widget

        # Type inconnu : repli vers un champ texte.
        return QLineEdit()

    def values(self) -> dict:
        """Retourne les données saisies dans le formulaire."""

        birth_date = None

        if self.birthDateEdit.date() != self.birthDateEdit.minimumDate():
            birth_date = self.birthDateEdit.date().toString("yyyy-MM-dd")

        return {
            "matricule": self.firsMatriculeEdit.text().strip(),
            "first_name": self.firstNameEdit.text().strip(),
            "last_name": self.lastNameEdit.text().strip(),
            "birth_date": birth_date,
            "sex": self.sexComboBox.currentText().strip(),
            "nationality": self.nationalityEdit.text().strip(),
            "social_category": self.socialCategoryComboBox.currentText().strip(),
            "profession": self.professionEdit.text().strip(),
            "email": self.emailEdit.text().strip(),
            "phone": self.phoneEdit.text().strip(),
            "address": self.addressEdit.text().strip(),
            "city": self.cityEdit.text().strip(),
            "postal_code": self.postalCodeEdit.text().strip(),
            "notes": self.notesEdit.toPlainText().strip(),
            "photo_path": self.current_photo_path,
        }
    # ------------------------------------------------------------------
    # Chargement de la personne
    # ------------------------------------------------------------------

    def load_person(self) -> None:
        if self.person_id is None:
            return


        person = self.db.fetch_one(
            """
            SELECT *
            FROM persons
            WHERE id = ?
            """,
            (self.person_id,),
        )

        if person is None:
            QMessageBox.critical(
                self,
                "Personne introuvable",
                "Cette personne n'existe plus dans la base de données.",
            )
            self.reject()
            return

 
        self.firsMatriculeEdit.setText(str(person["matricule"]))
        self.firstNameEdit.setText(person["first_name"] or "")
        self.lastNameEdit.setText(person["last_name"] or "")
        self.professionEdit.setText(person["profession"] or "")
        self.socialCategoryComboBox.setCurrentText(
            person["social_category"] or ""
        )
        self.cityEdit.setText(person["city"] or "")


        self.addressEdit.setText(person["address"] or "")
        self.phoneEdit.setText(person["phone"] or "")
        self.emailEdit.setText(person["email"] or "")
        self.postalCodeEdit.setText(person["postal_code"] or "")




        if hasattr(self.notesEdit, "setPlainText"):
            self.notesEdit.setPlainText(person["notes"] or "")
        else:
            self.notesEdit.setText(person["notes"] or "")

        birth_date_value = person["birth_date"]

        if birth_date_value:
            birth_date = QDate.fromString(
                str(birth_date_value),
                "yyyy-MM-dd",
            )

            if birth_date.isValid():
                self.birthDateEdit.setDate(birth_date)
        else:
            self.birthDateEdit.setDate(
                self.birthDateEdit.minimumDate()
            )

        sex = person["sex"] or ""
        sex_index = self.sexComboBox.findText(str(sex))

        if sex_index >= 0:
            self.sexComboBox.setCurrentIndex(sex_index)
        else:
            self.sexComboBox.addItem(str(sex))
            self.sexComboBox.setCurrentText(str(sex))



        if person["photo_path"]:
            self.current_photo_path = person["photo_path"]
            self.display_photo(
                self.resolve_photo_path(str(self.PHOTO_DIRECTORY) + '/' + self.current_photo_path)
            )
        else:
            self.clear_photo_preview()

    # ------------------------------------------------------------------
    # Chargement des champs personnalisés
    # ------------------------------------------------------------------

    def load_custom_field_values(self) -> None:
        if self.person_id is None:
            return

        rows = self.db.fetch_all(
            """
            SELECT field_id, value
            FROM custom_field_value
            WHERE person_id = ?
            """,
            (self.person_id,),
        )

        for row in rows:
            field_id = int(row["field_id"])
            value = row["value"]

            field_data = self.custom_field_widgets.get(field_id)

            if field_data is None:
                continue

            self.set_widget_value(
                widget=field_data["widget"],
                field_type=field_data["type"],
                value=value,
            )

    def set_widget_value(
        self,
        widget: QWidget,
        field_type: str,
        value: Any,
    ) -> None:
        if value is None:
            return

        field_type = field_type.lower()

        try:
            if field_type == "text" and isinstance(
                widget,
                QLineEdit,
            ):
                widget.setText(str(value))

            elif field_type == "multiline" and isinstance(
                widget,
                QPlainTextEdit,
            ):
                widget.setPlainText(str(value))

            elif field_type == "integer" and isinstance(
                widget,
                QSpinBox,
            ):
                widget.setValue(int(value))

            elif field_type == "decimal" and isinstance(
                widget,
                QDoubleSpinBox,
            ):
                widget.setValue(float(value))

            elif field_type == "boolean" and isinstance(
                widget,
                QCheckBox,
            ):
                normalized = str(value).strip().lower()
                widget.setChecked(
                    normalized in {"1", "true", "yes", "oui"}
                )

            elif field_type == "choice" and isinstance(
                widget,
                QComboBox,
            ):
                value_text = str(value)
                index = widget.findText(value_text)

                if index < 0 and value_text:
                    widget.addItem(value_text)
                    index = widget.findText(value_text)

                if index >= 0:
                    widget.setCurrentIndex(index)

            elif field_type == "date" and isinstance(
                widget,
                QDateEdit,
            ):
                date = QDate.fromString(
                    str(value),
                    "yyyy-MM-dd",
                )

                if date.isValid():
                    widget.setDate(date)

        except (TypeError, ValueError):
            # Une ancienne valeur invalide ne doit pas empêcher
            # l'ouverture de la fiche.
            return

    # ------------------------------------------------------------------
    # Photo
    # ------------------------------------------------------------------

    def select_photo(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner une photo",
            "",
            (
                "Images (*.png *.jpg *.jpeg *.bmp *.webp);;"
                "Tous les fichiers (*)"
            ),
        )

        if not file_path:
            return

        source = Path(file_path)

        pixmap = QPixmap(str(source))

        if pixmap.isNull():
            QMessageBox.warning(
                self,
                "Image invalide",
                "Le fichier sélectionné ne peut pas être affiché.",
            )
            return

        self.selected_photo_source = source
        self.display_photo(source)

    def remove_photo(self) -> None:
        self.selected_photo_source = None
        self.current_photo_path = None
        self.clear_photo_preview()

    import shutil



    def display_photo(self, path: Path) -> None:


        if not path.exists():
            self.clear_photo_preview()
            return

        pixmap = QPixmap(str(path))

        if pixmap.isNull():
            self.clear_photo_preview()
            return

        scaled = pixmap.scaled(
            self.photoLabel.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        self.photoLabel.setPixmap(scaled)
        self.photoLabel.setText("")

    def clear_photo_preview(self) -> None:
        self.photoLabel.clear()
        self.photoLabel.setText("Aucune photo")

    def resolve_photo_path(self, stored_path: str) -> Path:
        path = Path(stored_path)

        if path.is_absolute():
            return path

        return self.PROJECT_ROOT / path

    def copy_selected_photo(self) -> str | None:
        """
        Copie la nouvelle photo dans data/photos et retourne un chemin
        relatif au projet.

        Si aucune nouvelle photo n'a été sélectionnée, conserve le chemin
        existant.
        """
        if self.selected_photo_source is None:
            return self.current_photo_path

        extension = self.selected_photo_source.suffix.lower()

        if extension not in {
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".webp",
        }:
            extension = ".jpg"

        filename = f"{uuid.uuid4().hex}{extension}"
        destination = self.PHOTO_DIRECTORY / filename
        shutil.copy2(self.selected_photo_source, destination)

        relative_path = destination.relative_to(self.PROJECT_ROOT)
        self.current_photo_path = str(filename)

        #print('in copy_selected_photo',self.current_photo_path)
        return self.current_photo_path

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_person(self) -> bool:
        if not self.lastNameEdit.text().strip():
            QMessageBox.warning(
                self,
                "Champ obligatoire",
                "Le nom de la personne est obligatoire.",
            )
            self.personTabWidget.setCurrentIndex(0)
            self.lastNameEdit.setFocus()
            return False

        for field_id, field_data in self.custom_field_widgets.items():
            if not field_data["required"]:
                continue

            value = self.get_widget_value(
                field_data["widget"],
                field_data["type"],
            )

            if self.is_empty_custom_value(
                value=value,
                field_type=field_data["type"],
            ):
                QMessageBox.warning(
                    self,
                    "Champ obligatoire",
                    (
                        f'Le champ « {field_data["name"]} » '
                        "est obligatoire."
                    ),
                )

                widget = field_data["widget"]

                for index in range(self.personTabWidget.count()):
                    page = self.personTabWidget.widget(index)

                    if page.isAncestorOf(widget):
                        self.personTabWidget.setCurrentIndex(index)
                        break

                widget.setFocus()
                return False

        return True

    @staticmethod
    def is_empty_custom_value(
        value: Any,
        field_type: str,
    ) -> bool:
        if field_type == "boolean":
            # Une case décochée constitue une valeur valide.
            return False

        return value is None or str(value).strip() == ""

    # ------------------------------------------------------------------
    # Enregistrement
    # ------------------------------------------------------------------

    def save(self) -> None:
        if not self.validate_person():
            return

        try:

            photo_path  = self.copy_selected_photo()
            person_data = self.collect_person_data(photo_path)


            try:
                if self.person_id is None:

                    self.person_id = self.insert_person(person_data)
                    self.save_custom_field_values(self.person_id)
                else:

                    self.update_person(person_data)
                    #self.update_custom_field_values(self.person_id)


                self.db.commit()

            except Exception:
                self.db.rollback()
                raise

        except sqlite3.Error as error:
            QMessageBox.critical(
                self,
                "Erreur de base de données",
                f"Impossible d'enregistrer la personne.\n\n{error}",
            )
            return

        except (OSError, ValueError) as error:
            QMessageBox.critical(
                self,
                "Erreur d'enregistrement",
                str(error),
            )
            return

        self.accept()

    def collect_person_data(
        self,
        photo_path: str | None,
    ) -> dict[str, Any]:
        birth_date: str | None

        if (
            self.birthDateEdit.date()
            == self.birthDateEdit.minimumDate()
        ):
            birth_date = None
        else:
            birth_date = self.birthDateEdit.date().toString(
                "yyyy-MM-dd"
            )

        if hasattr(self.notesEdit, "toPlainText"):
            notes = self.notesEdit.toPlainText().strip()
        else:
            notes = self.notesEdit.text().strip()

        return {
            "matricule" : self.firsMatriculeEdit.text().strip(),
            "first_name": self.firstNameEdit.text().strip(),
            "last_name": self.lastNameEdit.text().strip(),
            "birth_date": birth_date,
            "sex": self.sexComboBox.currentText().strip(),
            "profession": self.professionEdit.text().strip(),
            "social_category":                 self.socialCategoryComboBox.currentText().strip(),
            "city": self.cityEdit.text().strip(),
            "notes": notes,
            "photo_path": photo_path,
            "email":self.emailEdit.text().strip(),
            "phone": self.phoneEdit.text().strip(),
            "address": self.addressEdit.text().strip(),
            "postal_code": self.postalCodeEdit.text().strip(),
            "nationality": self.nationalityEdit.text().strip()
        }

    def insert_person(
        self,
        person_data: dict[str, Any],
    ) -> int:
        cursor = self.db.execute(
            """
            INSERT INTO persons (
                first_name,
                last_name,
                matricule,
                birth_date,
                sex,
                profession,
                social_category,
                city,
                notes,
                photo_path,
                email,
                phone,
                address,
                postal_code,
                nationality,
                created_at,
                updated_at
            )
            VALUES (
                :first_name,
                :last_name,
                :birth_date,
                :sex,
                :matricule,
                :profession,
                :social_category,
                :city,
                :notes,
                :photo_path,
                :email,
                :phone,
                :address,
                :postal_code,
                :nationality,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            )
            """,
            person_data,
        )

        if cursor.lastrowid is None:
            raise sqlite3.DatabaseError(
                "La base n'a pas retourné l'identifiant de la personne."
            )

        return int(cursor.lastrowid)

    def update_person(
        self,
        person_data: dict[str, Any],
    ) -> None:


        if self.person_id is None:
            raise ValueError(
                "Identifiant de personne absent lors de la modification."
            )

        person_data_with_id = {
            **person_data,
            "person_id": self.person_id,
        }

        self.db.execute(
            """
            UPDATE persons
            SET
                first_name = :first_name,
                last_name = :last_name,
                birth_date = :birth_date,
                sex = :sex,
                matricule=:matricule,
                profession = :profession,
                social_category = :social_category,
                city = :city,
                notes = :notes,
                photo_path = :photo_path,
                email = :email,
                phone = :phone,
                address = :address,
                postal_code = :postal_code,
                nationality = :nationality,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = :person_id
            """,
            person_data_with_id,
        )

    def save_custom_field_values(
        self,
        person_id: int,
    ) -> None:


        for field_id, field_data in self.custom_field_widgets.items():
            value = self.get_widget_value(
                widget=field_data["widget"],
                field_type=field_data["type"],
            )

            if value is None or (
                isinstance(value, str) and not value.strip()
            ):
                self.db.execute(
                    """
                    DELETE FROM custom_field_value
                    WHERE person_id = ?
                      AND field_id = ?
                    """,
                    (person_id, field_id),
                )

                continue

            self.db.execute(
                """
                INSERT INTO custom_field_value (
                    person_id,
                    field_id,
                    value
                )
                VALUES (?, ?, ?)
                ON CONFLICT(person_id, field_id)
                DO UPDATE SET
                    value = excluded.value
                """,
                (
                    person_id,
                    field_id,
                    str(value),
                ),
            )

    def get_widget_value(
        self,
        widget: QWidget,
        field_type: str,
    ) -> Any:
        field_type = field_type.lower()

        if field_type == "text" and isinstance(
            widget,
            QLineEdit,
        ):
            return widget.text().strip()

        if field_type == "multiline" and isinstance(
            widget,
            QPlainTextEdit,
        ):
            return widget.toPlainText().strip()

        if field_type == "integer" and isinstance(
            widget,
            QSpinBox,
        ):
            return widget.value()

        if field_type == "decimal" and isinstance(
            widget,
            QDoubleSpinBox,
        ):
            return widget.value()

        if field_type == "boolean" and isinstance(
            widget,
            QCheckBox,
        ):
            return "1" if widget.isChecked() else "0"

        if field_type == "choice" and isinstance(
            widget,
            QComboBox,
        ):
            return widget.currentText().strip()

        if field_type == "date" and isinstance(
            widget,
            QDateEdit,
        ):
            if widget.date() == widget.minimumDate():
                return None

            return widget.date().toString("yyyy-MM-dd")

        return None