from __future__ import annotations

import re
from pathlib import Path
from typing import Any
from PyQt6.QtWidgets import QAbstractItemView
from PyQt6 import uic
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)


UI_FILE = Path(__file__).resolve().parent.parent / "forms" / "SettingsPage.ui"


class CustomTableDialog(QDialog):
    def __init__(self, parent=None, values: dict[str, Any] | None = None):
        super().__init__(parent)
        self.setWindowTitle("Table liée")
        self.resize(520, 340)

        self.labelEdit = QLineEdit()
        self.nameEdit = QLineEdit()
        self.descriptionEdit = QPlainTextEdit()
        self.descriptionEdit.setMaximumHeight(100)
        self.allowMultipleCheckBox = QCheckBox("Autoriser plusieurs lignes par personne")
        self.orderSpinBox = QSpinBox()
        self.orderSpinBox.setRange(0, 9999)
        self.enabledCheckBox = QCheckBox("Table active")
        self.enabledCheckBox.setChecked(True)

        form = QFormLayout()
        form.addRow("Libellé :", self.labelEdit)
        form.addRow("Nom technique :", self.nameEdit)
        form.addRow("Description :", self.descriptionEdit)
        form.addRow("", self.allowMultipleCheckBox)
        form.addRow("Ordre :", self.orderSpinBox)
        form.addRow("", self.enabledCheckBox)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self.labelEdit.textChanged.connect(self._suggest_name)
        self._name_manually_edited = False
        self.nameEdit.textEdited.connect(self._mark_name_as_manual)

        if values:
            self.set_values(values)

    def _mark_name_as_manual(self) -> None:
        self._name_manually_edited = True

    def _suggest_name(self, text: str) -> None:
        if self._name_manually_edited:
            return
        name = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
        self.nameEdit.setText(name)

    def _validate_and_accept(self) -> None:
        if not self.labelEdit.text().strip():
            QMessageBox.warning(self, "Validation", "Le libellé est obligatoire.")
            return
        if not re.fullmatch(r"[a-z][a-z0-9_]*", self.nameEdit.text().strip()):
            QMessageBox.warning(
                self,
                "Validation",
                "Le nom technique doit commencer par une lettre et ne contenir que "
                "des lettres minuscules, chiffres et caractères soulignés.",
            )
            return
        self.accept()

    def set_values(self, values: dict[str, Any]) -> None:
        self.labelEdit.setText(str(values.get("label", "")))
        self.nameEdit.setText(str(values.get("name", "")))
        self.descriptionEdit.setPlainText(str(values.get("description") or ""))
        self.allowMultipleCheckBox.setChecked(bool(values.get("allow_multiple", True)))
        self.orderSpinBox.setValue(int(values.get("display_order", 0)))
        self.enabledCheckBox.setChecked(bool(values.get("enabled", True)))
        self._name_manually_edited = True

    def values(self) -> dict[str, Any]:
        return {
            "label": self.labelEdit.text().strip(),
            "name": self.nameEdit.text().strip(),
            "description": self.descriptionEdit.toPlainText().strip(),
            "allow_multiple": self.allowMultipleCheckBox.isChecked(),
            "display_order": self.orderSpinBox.value(),
            "enabled": self.enabledCheckBox.isChecked(),
        }


class CustomFieldDialog(QDialog):
    FIELD_TYPES = [
        ("Texte", "text"),
        ("Texte multiligne", "multiline"),
        ("Entier", "integer"),
        ("Décimal", "decimal"),
        ("Date", "date"),
        ("Oui / Non", "boolean"),
        ("Liste manuelle", "choice"),
        ("Liste depuis CSV", "csv_choice"),
        ("Fichier", "file"),
    ]

    def __init__(
        self,
        tables: list[Any],
        parent=None,
        values: dict[str, Any] | None = None,
        selected_table_id: int | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle("Champ personnalisé")
        self.resize(600, 520)

        self.tableComboBox = QComboBox()
        for table in tables:
            self.tableComboBox.addItem(
                str(_value(table, "label")), int(_value(table, "id"))
            )

        self.labelEdit = QLineEdit()
        self.nameEdit = QLineEdit()
        self.typeComboBox = QComboBox()
        for label, code in self.FIELD_TYPES:
            self.typeComboBox.addItem(label, code)

        self.requiredCheckBox = QCheckBox("Champ obligatoire")
        self.orderSpinBox = QSpinBox()
        self.orderSpinBox.setRange(0, 9999)
        self.enabledCheckBox = QCheckBox("Champ actif")
        self.enabledCheckBox.setChecked(True)

        self.manualChoicesEdit = QPlainTextEdit()
        self.manualChoicesEdit.setPlaceholderText("Une valeur par ligne")
        self.manualChoicesEdit.setMaximumHeight(90)

        self.csvPathEdit = QLineEdit()
        self.chooseCsvButton = QPushButton("Parcourir…")
        csv_path_layout = QHBoxLayout()
        csv_path_layout.addWidget(self.csvPathEdit)
        csv_path_layout.addWidget(self.chooseCsvButton)

        self.csvValueColumnEdit = QLineEdit()
        self.csvValueColumnEdit.setPlaceholderText("ex. code")
        self.csvLabelColumnEdit = QLineEdit()
        self.csvLabelColumnEdit.setPlaceholderText("ex. label")
        self.csvSeparatorEdit = QLineEdit(",")
        self.csvSeparatorEdit.setMaxLength(1)

        form = QFormLayout()
        form.addRow("Table :", self.tableComboBox)
        form.addRow("Libellé :", self.labelEdit)
        form.addRow("Nom technique :", self.nameEdit)
        form.addRow("Type :", self.typeComboBox)
        form.addRow("", self.requiredCheckBox)
        form.addRow("Ordre :", self.orderSpinBox)
        form.addRow("", self.enabledCheckBox)
        form.addRow("Valeurs manuelles :", self.manualChoicesEdit)
        form.addRow("Fichier CSV :", csv_path_layout)
        form.addRow("Colonne valeur :", self.csvValueColumnEdit)
        form.addRow("Colonne libellé :", self.csvLabelColumnEdit)
        form.addRow("Séparateur CSV :", self.csvSeparatorEdit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

        self.chooseCsvButton.clicked.connect(self.choose_csv)
        self.typeComboBox.currentIndexChanged.connect(self.update_source_widgets)
        self.labelEdit.textChanged.connect(self._suggest_name)
        self._name_manually_edited = False
        self.nameEdit.textEdited.connect(self._mark_name_as_manual)

        if selected_table_id is not None:
            index = self.tableComboBox.findData(selected_table_id)
            if index >= 0:
                self.tableComboBox.setCurrentIndex(index)

        if values:
            self.set_values(values)

        self.update_source_widgets()

    def _mark_name_as_manual(self) -> None:
        self._name_manually_edited = True

    def _suggest_name(self, text: str) -> None:
        if self._name_manually_edited:
            return
        name = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
        self.nameEdit.setText(name)

    def choose_csv(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir un fichier CSV",
            "",
            "Fichiers CSV (*.csv);;Tous les fichiers (*)",
        )
        if path:
            self.csvPathEdit.setText(path)

    def update_source_widgets(self) -> None:
        field_type = self.typeComboBox.currentData()
        manual = field_type == "choice"
        csv_mode = field_type == "csv_choice"

        self.manualChoicesEdit.setEnabled(manual)
        self.csvPathEdit.setEnabled(csv_mode)
        self.chooseCsvButton.setEnabled(csv_mode)
        self.csvValueColumnEdit.setEnabled(csv_mode)
        self.csvLabelColumnEdit.setEnabled(csv_mode)
        self.csvSeparatorEdit.setEnabled(csv_mode)

    def _validate_and_accept(self) -> None:
        if self.tableComboBox.currentData() is None:
            QMessageBox.warning(self, "Validation", "Sélectionnez une table.")
            return
        if not self.labelEdit.text().strip():
            QMessageBox.warning(self, "Validation", "Le libellé est obligatoire.")
            return
        if not re.fullmatch(r"[a-z][a-z0-9_]*", self.nameEdit.text().strip()):
            QMessageBox.warning(self, "Validation", "Nom technique invalide.")
            return

        field_type = self.typeComboBox.currentData()
        if field_type == "choice" and not self.manualChoicesEdit.toPlainText().strip():
            QMessageBox.warning(self, "Validation", "Saisissez au moins une valeur.")
            return
        if field_type == "csv_choice":
            csv_path = self.csvPathEdit.text().strip()
            if not csv_path:
                QMessageBox.warning(self, "Validation", "Sélectionnez un fichier CSV.")
                return
            if not Path(csv_path).exists():
                QMessageBox.warning(self, "Validation", "Le fichier CSV n'existe pas.")
                return
            if not self.csvValueColumnEdit.text().strip():
                QMessageBox.warning(self, "Validation", "Indiquez la colonne de valeur.")
                return

        self.accept()

    def set_values(self, values: dict[str, Any]) -> None:
        table_index = self.tableComboBox.findData(int(values.get("table_id")))
        if table_index >= 0:
            self.tableComboBox.setCurrentIndex(table_index)
        self.labelEdit.setText(str(values.get("label", "")))
        self.nameEdit.setText(str(values.get("name", "")))
        type_index = self.typeComboBox.findData(values.get("field_type", "text"))
        if type_index >= 0:
            self.typeComboBox.setCurrentIndex(type_index)
        self.requiredCheckBox.setChecked(bool(values.get("required", False)))
        self.orderSpinBox.setValue(int(values.get("display_order", 0)))
        self.enabledCheckBox.setChecked(bool(values.get("enabled", True)))
        self.manualChoicesEdit.setPlainText(str(values.get("manual_choices") or ""))
        self.csvPathEdit.setText(str(values.get("csv_path") or ""))
        self.csvValueColumnEdit.setText(str(values.get("csv_column") or ""))
        self.csvLabelColumnEdit.setText(str(values.get("csv_label_column") or ""))
        self.csvSeparatorEdit.setText(str(values.get("csv_separator") or ","))
        self._name_manually_edited = True

    def values(self) -> dict[str, Any]:

        #avant--> self.manualChoicesEdit.toPlainText().strip()
        result = ";".join(self.manualChoicesEdit.toPlainText().splitlines())
        return {
            "table_id": int(self.tableComboBox.currentData()),
            "label": self.labelEdit.text().strip(),
            "name": self.nameEdit.text().strip(),
            "field_type": self.typeComboBox.currentData(),
            "required": self.requiredCheckBox.isChecked(),
            "display_order": self.orderSpinBox.value(),
            "enabled": self.enabledCheckBox.isChecked(),
            "manual_choices": result or None,
            "csv_path": self.csvPathEdit.text().strip() or None,
            "csv_column": self.csvValueColumnEdit.text().strip() or None,
            "csv_label_column": self.csvLabelColumnEdit.text().strip() or None,
            "csv_separator": self.csvSeparatorEdit.text() or ",",
        }


def _value(row: Any, key: str, default: Any = None) -> Any:
    try:
        return row[key]
    except (KeyError, TypeError, IndexError):
        return getattr(row, key, default)


class SettingsPage(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        uic.loadUi(str(UI_FILE), self)

        self.customTablesTable.horizontalHeader().setStretchLastSection(True)
        self.customFieldsTable.horizontalHeader().setStretchLastSection(True)

        self.addCustomTableButton.clicked.connect(self.add_custom_table)
        self.editCustomTableButton.clicked.connect(self.edit_custom_table)
        self.deleteCustomTableButton.clicked.connect(self.delete_custom_table)
        self.addCustomFieldButton.clicked.connect(self.add_custom_field)
        self.editCustomFieldButton.clicked.connect(self.edit_custom_field)
        self.deleteCustomFieldButton.clicked.connect(self.delete_custom_field)
        self.fieldTableComboBox.currentIndexChanged.connect(self.load_custom_fields)
        self.customTablesTable.itemSelectionChanged.connect(self._sync_table_selection)
        self.customTablesTable.doubleClicked.connect(self.edit_custom_table)
        self.customFieldsTable.doubleClicked.connect(self.edit_custom_field)

        self.customTablesTable.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.customTablesTable.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.customFieldsTable.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )

        self.customFieldsTable.setSelectionMode(
            QAbstractItemView.SelectionMode.SingleSelection
        )

        self.load_custom_tables()

    def refresh(self) -> None:
        selected_table_id = self.fieldTableComboBox.currentData()

        self.load_custom_tables()

        if selected_table_id is not None:
            index = self.fieldTableComboBox.findData(
                selected_table_id
            )

            if index >= 0:
                self.fieldTableComboBox.setCurrentIndex(index)

    def load_custom_tables(self) -> None:
        rows = list(self.db.get_custom_tables())
        selected_id = self.fieldTableComboBox.currentData()

        self.customTablesTable.setRowCount(len(rows))
        self.fieldTableComboBox.blockSignals(True)
        self.fieldTableComboBox.clear()

        for row_index, row in enumerate(rows):
            table_id = int(_value(row, "id"))
            values = [
                _value(row, "label", ""),
                _value(row, "name", ""),
                "Oui" if bool(_value(row, "allow_multiple", 0)) else "Non",
                str(_value(row, "display_order", 0)),
                "Oui" if bool(_value(row, "enabled", 0)) else "Non",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, table_id)
                self.customTablesTable.setItem(row_index, column, item)

            self.fieldTableComboBox.addItem(str(_value(row, "label", "")), table_id)

        if selected_id is not None:
            index = self.fieldTableComboBox.findData(selected_id)
            if index >= 0:
                self.fieldTableComboBox.setCurrentIndex(index)

        self.fieldTableComboBox.blockSignals(False)
        self.load_custom_fields()

    def load_custom_fields(self) -> None:
        table_id = self.fieldTableComboBox.currentData()
        if table_id is None:
            self.customFieldsTable.setRowCount(0)
            return

        rows = list(self.db.get_custom_table_fields(int(table_id)))
        self.customFieldsTable.setRowCount(len(rows))

        for row_index, row in enumerate(rows):
            field_id = int(_value(row, "id"))
            values = [
                _value(row, "label", ""),
                _value(row, "name", ""),
                _value(row, "field_type", ""),
                "Oui" if bool(_value(row, "required", 0)) else "Non",
                str(_value(row, "display_order", 0)),
                _value(row, "csv_path", "") or "",
            ]
            for column, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                if column == 0:
                    item.setData(Qt.ItemDataRole.UserRole, field_id)
                self.customFieldsTable.setItem(row_index, column, item)

    def _selected_table_id(self) -> int | None:
        selected_rows = (
            self.customTablesTable
            .selectionModel()
            .selectedRows()
        )

        if not selected_rows:
            return None

        row_index = selected_rows[0].row()
        item = self.customTablesTable.item(row_index, 0)

        if item is None:
            return None

        table_id = item.data(Qt.ItemDataRole.UserRole)

        if table_id is None:
            return None

        return int(table_id)

    def _selected_field_id(self) -> int | None:
        row = self.customFieldsTable.currentRow()
        if row < 0:
            return None
        item = self.customFieldsTable.item(row, 0)
        return int(item.data(Qt.ItemDataRole.UserRole)) if item else None

    def _sync_table_selection(self) -> None:
        table_id = self._selected_table_id()
        if table_id is None:
            return
        index = self.fieldTableComboBox.findData(table_id)
        if index >= 0:
            self.fieldTableComboBox.setCurrentIndex(index)

    def add_custom_table(self) -> None:
        dialog = CustomTableDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        try:
            self.db.add_custom_table(dialog.values())
            self.load_custom_tables()
        except Exception as error:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ajouter la table :\n{error}")

    def edit_custom_table(self, *_args) -> None:
        table_id = self._selected_table_id()

        if table_id is None:
            QMessageBox.information(
                self,
                "Modifier une table",
                "Sélectionnez une table dans la liste.",
            )
            return

        try:
            table = self.db.get_custom_table(table_id)

            if table is None:
                QMessageBox.warning(
                    self,
                    "Modifier une table",
                    "La table sélectionnée n'existe plus.",
                )
                self.refresh()
                return

            values = {
                "id": _value(table, "id"),
                "name": _value(table, "name", ""),
                "label": _value(table, "label", ""),
                "description": _value(table, "description", ""),
                "display_order": _value(table, "display_order", 0),
                "enabled": bool(_value(table, "enabled", 1)),
                "allow_multiple": bool(
                    _value(table, "allow_multiple", 1)
                ),
            }

            dialog = CustomTableDialog(
                parent=self,
                values=values,
            )

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            self.db.update_custom_table(
                table_id,
                dialog.values(),
            )

            self.refresh()

            index = self.fieldTableComboBox.findData(table_id)

            if index >= 0:
                self.fieldTableComboBox.setCurrentIndex(index)

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erreur",
                "Impossible de modifier la table :\n"
                f"{error}",
            )
    def delete_custom_table(self) -> None:
        table_id = self._selected_table_id()
        if table_id is None:
            QMessageBox.information(self, "Table", "Sélectionnez une table.")
            return

        answer = QMessageBox.question(
            self,
            "Suppression",
            "Supprimer cette table, ses champs et toutes les valeurs associées ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.db.delete_custom_table(table_id)
            self.load_custom_tables()
        except Exception as error:
            QMessageBox.critical(self, "Erreur", f"Impossible de supprimer la table :\n{error}")

    def add_custom_field(self) -> None:
        tables = list(self.db.get_custom_tables())
        if not tables:
            QMessageBox.information(self, "Champ", "Créez d'abord une table liée.")
            return

        dialog = CustomFieldDialog(
            tables=tables,
            parent=self,
            selected_table_id=self.fieldTableComboBox.currentData(),
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            self.db.add_custom_table_field(dialog.values())
            selected_table_id = dialog.values()["table_id"]
            index = self.fieldTableComboBox.findData(selected_table_id)
            if index >= 0:
                self.fieldTableComboBox.setCurrentIndex(index)
            self.load_custom_fields()
        except Exception as error:
            QMessageBox.critical(self, "Erreur", f"Impossible d'ajouter le champ :\n{error}")

    def edit_custom_field(self, *_args) -> None:
        field_id = self._selected_field_id()

        if field_id is None:
            QMessageBox.information(
                self,
                "Modifier un champ",
                "Sélectionnez un champ dans la liste.",
            )
            return

        try:
            field = self.db.get_custom_table_field(field_id)

            if field is None:
                QMessageBox.warning(
                    self,
                    "Modifier un champ",
                    "Le champ sélectionné n'existe plus.",
                )
                self.load_custom_fields()
                return

            values = {
                "id": _value(field, "id"),
                "table_id": _value(field, "table_id"),
                "name": _value(field, "name", ""),
                "label": _value(field, "label", ""),
                "field_type": _value(
                    field,
                    "field_type",
                    "text",
                ),
                "required": bool(
                    _value(field, "required", 0)
                ),
                "display_order": _value(
                    field,
                    "display_order",
                    0,
                ),
                "enabled": bool(
                    _value(field, "enabled", 1)
                ),
                "manual_choices": _value(
                    field,
                    "manual_choices",
                    "",
                ),
                "csv_path": _value(
                    field,
                    "csv_path",
                    "",
                ),
                "csv_column": _value(
                    field,
                    "csv_column",
                    "",
                ),
                "csv_label_column": _value(
                    field,
                    "csv_label_column",
                    "",
                ),
                "csv_separator": _value(
                    field,
                    "csv_separator",
                    ",",
                ),
            }

            tables = list(self.db.get_custom_tables())

            dialog = CustomFieldDialog(
                tables=tables,
                parent=self,
                values=values,
            )

            if dialog.exec() != QDialog.DialogCode.Accepted:
                return

            new_values = dialog.values()

            self.db.update_custom_table_field(
                field_id,
                new_values,
            )

            table_index = self.fieldTableComboBox.findData(
                new_values["table_id"]
            )

            if table_index >= 0:
                self.fieldTableComboBox.setCurrentIndex(
                    table_index
                )

            self.load_custom_fields()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erreur",
                "Impossible de modifier le champ :\n"
                f"{error}",
            )

    def delete_custom_field(self) -> None:
        field_id = self._selected_field_id()
        if field_id is None:
            QMessageBox.information(self, "Champ", "Sélectionnez un champ.")
            return

        answer = QMessageBox.question(
            self,
            "Suppression",
            "Supprimer ce champ et toutes ses valeurs ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer != QMessageBox.StandardButton.Yes:
            return

        try:
            self.db.delete_custom_field(field_id)
            self.load_custom_fields()
        except Exception as error:
            QMessageBox.critical(self, "Erreur", f"Impossible de supprimer le champ :\n{error}")
