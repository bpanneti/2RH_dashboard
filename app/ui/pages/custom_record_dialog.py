from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class CustomRecordDialog(QDialog):
    def __init__(
        self,
        db,
        table_id: int,
        person_id: int,
        record_id: int | None = None,
        parent=None,
    ):
        super().__init__(parent)

        self.db = db
        self.table_id = table_id
        self.person_id = person_id
        self.record_id = record_id

        self.field_widgets: dict[int, QWidget] = {}
        self.field_definitions: dict[int, dict] = {}

        self.table_definition = self.db.get_custom_table(table_id)

        if self.table_definition is None:
            raise ValueError(
                f"Table personnalisée introuvable : {table_id}"
            )

        self.setWindowTitle(
            str(self.table_definition["label"])
        )

        self.resize(550, 450)

        self.main_layout = QVBoxLayout(self)
        self.form_layout = QFormLayout()

        self.main_layout.addLayout(self.form_layout)

        self.build_fields()

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )

        self.button_box.accepted.connect(self.validate_and_accept)
        self.button_box.rejected.connect(self.reject)

        self.main_layout.addWidget(self.button_box)

        if self.record_id is not None:
            self.load_record()


    def build_fields(self) -> None:
        fields = self.db.get_custom_table_fields(
            self.table_id
        )


        for field in fields:
            if not bool(field["enabled"]):
                continue

            field_id = int(field["id"])
            field_type = str(field["field_type"])

            widget = self.create_widget(field)

            self.field_widgets[field_id] = widget
            self.field_definitions[field_id] = dict(field)

            label = str(field["label"])



            if bool(field["required"]):
                label += " *"

            self.form_layout.addRow(
                QLabel(label),
                widget,
            )

    def create_widget(self, field) -> QWidget:
        field_type = str(field["field_type"]).lower()

        if field_type == "text":
            widget = QLineEdit()

        elif field_type == "multiline":
            widget = QTextEdit()
            widget.setMinimumHeight(100)

        elif field_type == "integer":
            widget = QSpinBox()
            widget.setRange(-1_000_000_000, 1_000_000_000)

        elif field_type == "decimal":
            widget = QDoubleSpinBox()
            widget.setRange(
                -1_000_000_000.0,
                1_000_000_000.0,
            )
            widget.setDecimals(4)

        elif field_type == "date":
            widget = QDateEdit()
            widget.setCalendarPopup(True)
            widget.setDisplayFormat("dd/MM/yyyy")
            widget.setDate(QDate.currentDate())

        elif field_type == "boolean":
            widget = QCheckBox()

        elif field_type == "choice":
            widget = QComboBox()

            choices = self.parse_choices(
                field["manual_choices"]
            )

            widget.addItems(choices)

        elif field_type == "csv_choice":
            widget = QComboBox()

            self.load_csv_choices(
                widget,
                field,
            )

        elif field_type == "file":
            widget = self.create_file_widget()

        else:
            widget = QLineEdit()


        self.apply_default_value(
            widget,
            field,
        )

        return widget
    def parse_choices(
        self,
        raw_choices: str | None,
    ) -> list[str]:

        if not raw_choices:
            return []

        return [
            value.strip()
            for value in raw_choices.split(";")
            if value.strip()
        ]
    def load_csv_choices(
        self,
        combo: QComboBox,
        field,
    ) -> None:

        csv_path = field["csv_path"]

        if not csv_path:
            return

        path = Path(str(csv_path))

        if not path.exists():
            combo.addItem(
                f"Fichier introuvable : {path.name}"
            )
            combo.setEnabled(False)
            return

        separator = field["csv_separator"] or ";"
        value_column = field["csv_value_column"]
        label_column = field["csv_label_column"]

        with path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:

            reader = csv.DictReader(
                file,
                delimiter=str(separator),
            )

            for row in reader:
                value = row.get(value_column, "")

                if label_column:
                    label = row.get(
                        label_column,
                        value,
                    )
                else:
                    label = value

                combo.addItem(
                    str(label),
                    str(value),
                )
    def create_file_widget(self) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)

        layout.setContentsMargins(0, 0, 0, 0)

        path_edit = QLineEdit()
        browse_button = QPushButton("Parcourir")

        layout.addWidget(path_edit, 1)
        layout.addWidget(browse_button)

        container.path_edit = path_edit

        browse_button.clicked.connect(
            lambda: self.choose_file(path_edit)
        )

        return container

    def choose_file(
        self,
        path_edit: QLineEdit,
    ) -> None:

        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Choisir un fichier",
        )

        if filename:
            path_edit.setText(filename)

    def apply_default_value(
        self,
        widget: QWidget,
        field,
    ) -> None:

        default_value = ''
        '''
        default_value = field["default_value"]

        if default_value is None:
            return
        '''
        field_type = str(field["field_type"]).lower()

        if field_type == "text":
            widget.setText(str(default_value))

        elif field_type == "multiline":
            widget.setPlainText(str(default_value))

        elif field_type == "integer":
            if default_value == '' :
                default_value = -1
            widget.setValue(int(default_value))

        elif field_type == "decimal":
            widget.setValue(float(default_value))

        elif field_type == "date":
            date = QDate.fromString(
                str(default_value),
                "yyyy-MM-dd",
            )

            if date.isValid():
                widget.setDate(date)

        elif field_type == "boolean":
            widget.setChecked(
                str(default_value).lower()
                in {"1", "true", "yes", "oui"}
            )

        elif field_type in {"choice", "csv_choice"}:
            index = widget.findData(default_value)

            if index < 0:
                index = widget.findText(
                    str(default_value)
                )

            if index >= 0:
                widget.setCurrentIndex(index)
    def values(self) -> dict[int, Any]:
        result: dict[int, Any] = {}

        for field_id, widget in self.field_widgets.items():
            field = self.field_definitions[field_id]
            field_type = str(field["field_type"]).lower()

            if field_type == "text":
                value = widget.text().strip()

            elif field_type == "multiline":
                value = widget.toPlainText().strip()

            elif field_type == "integer":
                value = widget.value()

            elif field_type == "decimal":
                value = widget.value()

            elif field_type == "date":
                value = widget.date().toString(
                    "yyyy-MM-dd"
                )

            elif field_type == "boolean":
                value = widget.isChecked()

            elif field_type == "choice":
                value = widget.currentText()

            elif field_type == "csv_choice":
                value = widget.currentData()

                if value is None:
                    value = widget.currentText()

            elif field_type == "file":
                value = widget.path_edit.text().strip()

            else:
                value = ""

            result[field_id] = value

        return result
    def validate_and_accept(self) -> None:
        values = self.values()

        for field_id, value in values.items():
            field = self.field_definitions[field_id]

            if not bool(field["required"]):
                continue

            field_type = str(field["field_type"]).lower()

            if field_type == "boolean":
                continue

            if value is None or str(value).strip() == "":
                QMessageBox.warning(
                    self,
                    "Champ obligatoire",
                    f"Le champ « {field['label']} » "
                    "doit être renseigné.",
                )
                return

        self.accept()
    def load_record(self) -> None:
        stored_values = self.db.get_custom_record_values(
            self.record_id
        )

        for row in stored_values:
            field_id = int(row["field_id"])

            widget = self.field_widgets.get(field_id)
            field = self.field_definitions.get(field_id)

            if widget is None or field is None:
                continue

            value = row["value"]
            field_type = str(field["field_type"]).lower()

            if field_type == "text":
                widget.setText(value or "")

            elif field_type == "multiline":
                widget.setPlainText(value or "")

            elif field_type == "integer":
                widget.setValue(
                    int(value or 0)
                )

            elif field_type == "decimal":
                widget.setValue(
                    float(value or 0.0)
                )

            elif field_type == "date":
                date = QDate.fromString(
                    value or "",
                    "yyyy-MM-dd",
                )

                if date.isValid():
                    widget.setDate(date)

            elif field_type == "boolean":
                widget.setChecked(
                    str(value).lower()
                    in {"1", "true", "yes", "oui"}
                )

            elif field_type == "choice":
                index = widget.findText(value or "")

                if index >= 0:
                    widget.setCurrentIndex(index)

            elif field_type == "csv_choice":
                index = widget.findData(value)

                if index < 0:
                    index = widget.findText(value or "")

                if index >= 0:
                    widget.setCurrentIndex(index)

            elif field_type == "file":
                widget.path_edit.setText(value or "")