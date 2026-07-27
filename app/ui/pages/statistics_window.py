import uuid
from typing import Any, Callable

from PyQt6 import QtCore
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.ui.pages.parameter_manager import ParameterManager
from app.ui.pages.statistics_calculator import StatisticsCalculator
from app.ui.pages.statistics_chart_widget import StatisticsChartWidget
from app.ui.pages.statistics_data_service import StatisticsDataService
from app.ui.pages.statistics_definitions import (
    CATEGORICAL_OPERATIONS,
    DISPLAY_TYPES,
    NUMERIC_OPERATIONS,
    STANDARD_FIELDS,
    allowed_displays,
    allowed_operations,
    normalize_custom_type,
)


class StatisticsWindow(QWidget):

    update_dashboard = QtCore.pyqtSignal()

    def __init__(
        self,
        repository,
        parameters_path: str = "parameters.txt",
        dashboard_refresh_callback: Callable[[], None] | None = None,
        parent=None,
    ) -> None:
        super().__init__(parent)

        ALLOWED_STANDARD_FIELDS = {
            "grade",
            "sex",
            "incorporation_dans_l_esacdron",
            "dipl_mes",
            "social_category",
            "birth_date",
        }

        self.repository = repository
        self.data_service = StatisticsDataService(repository,ALLOWED_STANDARD_FIELDS)
        self.parameter_manager = ParameterManager(parameters_path)
        self.dashboard_refresh_callback = dashboard_refresh_callback

        self.fields: list[dict[str, Any]] = []
        self.statistics: list[dict[str, Any]] = []

        self.setWindowTitle("Configuration des statistiques")
        self.resize(1200, 780)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)

        self.build_ui()
        self.load_fields()
        self.load_statistics()

    def build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        title = QLabel("Creation des statistiques")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        main_layout.addWidget(title)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        configuration_widget = QWidget()
        configuration_layout = QVBoxLayout(configuration_widget)
        form_layout = QFormLayout()

        self.field_combo = QComboBox()
        self.field_combo.currentIndexChanged.connect(self.on_field_changed)
        form_layout.addRow("Champ :", self.field_combo)

        self.operation_combo = QComboBox()
        self.operation_combo.currentIndexChanged.connect(self.on_operation_changed)
        form_layout.addRow("Calcul :", self.operation_combo)

        self.display_combo = QComboBox()
        self.display_combo.currentIndexChanged.connect(self.update_preview)
        form_layout.addRow("Affichage :", self.display_combo)

        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Titre de la statistique")
        form_layout.addRow("Titre :", self.title_edit)

        self.dashboard_checkbox = QCheckBox("Afficher sur le dashboard")
        form_layout.addRow("", self.dashboard_checkbox)

        configuration_layout.addLayout(form_layout)

        buttons_layout = QHBoxLayout()
        preview_button = QPushButton("Previsualiser")
        preview_button.clicked.connect(self.update_preview)
        buttons_layout.addWidget(preview_button)

        add_button = QPushButton("Ajouter")
        add_button.clicked.connect(self.add_statistic)
        buttons_layout.addWidget(add_button)
        configuration_layout.addLayout(buttons_layout)
        configuration_layout.addStretch()

        splitter.addWidget(configuration_widget)

        self.preview_widget = StatisticsChartWidget()
        splitter.addWidget(self.preview_widget)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        main_layout.addWidget(splitter, 1)

        self.statistics_table = QTableWidget()
        self.statistics_table.setColumnCount(7)
        self.statistics_table.setHorizontalHeaderLabels(
            [
                "Titre",
                "Source",
                "Champ",
                "Calcul",
                "Affichage",
                "Dashboard",
                "Supprimer",
            ]
        )
        self.statistics_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.statistics_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        main_layout.addWidget(self.statistics_table)

        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()


    def load_fields(self) -> None:
        self.fields = [dict(field) for field in STANDARD_FIELDS]


        try:
            custom_rows = self.repository.get_custom_fields_for_statistics()
        except Exception as error:
            QMessageBox.warning(
                self,
                "Champs personnalises",
                f"Impossible de charger les champs personnalises :\n{error}",
            )
            custom_rows = []

        for row in custom_rows:

            self.fields.append(
                {
                    "source_type": "custom",
                    "custom_table_id": row["table_id"],
                    "custom_table_name": row["table_name"],
                    "field_id": row["field_id"],
                    "label": row["field_name"],
                    "data_type": normalize_custom_type(row["field_type"]),
                }
            )

        self.field_combo.blockSignals(True)
        self.field_combo.clear()

        for field in self.fields:
            if field["source_type"] == "standard":
                display_name = f"Standard - {field['label']}"
            else:
                display_name = (
                    f"{field.get('custom_table_name', 'Personnalise')} - "
                    f"{field['label']}"
                )

            self.field_combo.addItem(display_name, field)

        self.field_combo.blockSignals(False)
        self.on_field_changed()

    def on_field_changed(self) -> None:
        field = self.field_combo.currentData()
        if not field:
            return

        operations = allowed_operations(field.get("data_type", "text"))

        self.operation_combo.blockSignals(True)
        self.operation_combo.clear()
        for operation_id, label in operations.items():
            self.operation_combo.addItem(label, operation_id)
        self.operation_combo.blockSignals(False)

        self.on_operation_changed()

    def on_operation_changed(self) -> None:
        operation = self.operation_combo.currentData()
        displays = allowed_displays(operation) if operation else {}

        self.display_combo.blockSignals(True)
        self.display_combo.clear()
        for display_id, label in displays.items():
            self.display_combo.addItem(label, display_id)
        self.display_combo.blockSignals(False)

        field = self.field_combo.currentData()
        if field and operation:
            operation_label = self.operation_combo.currentText()
            self.title_edit.setText(f"{operation_label} - {field['label']}")

        self.update_preview()

    def update_preview(self) -> None:
        field = self.field_combo.currentData()
        operation = self.operation_combo.currentData()
        display_type = self.display_combo.currentData()

        if not field or not operation or not display_type:
            return

        try:
            values = self.data_service.get_values(field)

            print('in statistics windows :',values)
            result = StatisticsCalculator.calculate(values, operation)
            self.preview_widget.render(
                result=result,
                display_type=display_type,
                title=self.title_edit.text().strip(),
            )
        except Exception as error:
            self.preview_widget.show_error(str(error))
            QMessageBox.critical(
                self,
                "Statistiques",
                f"Impossible de calculer la statistique :\n{error}",
            )

    def add_statistic(self) -> None:
        field = self.field_combo.currentData()
        operation = self.operation_combo.currentData()
        display_type = self.display_combo.currentData()
        title = self.title_edit.text().strip()

        if not field or not operation or not display_type:
            QMessageBox.warning(self, "Statistiques", "Configuration incomplete.")
            return

        if not title:
            QMessageBox.warning(self, "Statistiques", "Le titre est obligatoire.")
            return

        definition: dict[str, Any] = {
            "id": uuid.uuid4().hex,
            "title": title,
            "source_type": field["source_type"],
            "field_id": field["field_id"],
            "field_label": field["label"],
            "field_data_type": field["data_type"],
            "operation": operation,
            "display_type": display_type,
            "show_on_dashboard": self.dashboard_checkbox.isChecked(),
        }

        if field["source_type"] == "standard":
            definition["database_field"] = field.get(
                "database_field", field["field_id"]
            )
            definition["computed"] = field.get("computed", False)
        else:
            definition["custom_table_id"] = field.get("custom_table_id")
            definition["custom_table_name"] = field.get("custom_table_name")

        self.statistics.append(definition)
        self.refresh_statistics_table()
        self.save_statistics()
    def refresh_statistics_table(self) -> None:
        self.statistics_table.setRowCount(len(self.statistics))
        operation_labels = {**NUMERIC_OPERATIONS, **CATEGORICAL_OPERATIONS}

        for row_index, statistic in enumerate(self.statistics):
            source_label = (
                "Standard"
                if statistic.get("source_type") == "standard"
                else statistic.get("custom_table_name", "Personnalise")
            )

            textual_values = [
                statistic.get("title", ""),
                source_label,
                statistic.get("field_label", ""),
                operation_labels.get(
                    statistic.get("operation"), statistic.get("operation", "")
                ),
                DISPLAY_TYPES.get(
                    statistic.get("display_type"),
                    statistic.get("display_type", ""),
                ),
            ]

            for column, value in enumerate(textual_values):
                item = QTableWidgetItem(str(value))
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.statistics_table.setItem(row_index, column, item)

            dashboard_checkbox = QCheckBox()
            dashboard_checkbox.setChecked(
                bool(statistic.get("show_on_dashboard", False))
            )
            dashboard_checkbox.stateChanged.connect(
                lambda state, index=row_index: self.set_dashboard_state(index, state)
            )
            self.statistics_table.setCellWidget(
                row_index, 5, dashboard_checkbox
            )

            delete_button = QPushButton("Supprimer")
            delete_button.clicked.connect(
                lambda checked=False, index=row_index: self.delete_statistic(index)
            )
            self.statistics_table.setCellWidget(row_index, 6, delete_button)

    def set_dashboard_state(self, index: int, state: int) -> None:
        if 0 <= index < len(self.statistics):
            self.statistics[index]["show_on_dashboard"] = (
                state == Qt.CheckState.Checked.value
            )

    def delete_statistic(self, index: int) -> None:
        if not 0 <= index < len(self.statistics):
            return

        del self.statistics[index]
        self.refresh_statistics_table()
        self.save_statistics()
    def load_statistics(self) -> None:
        self.statistics = self.parameter_manager.get_statistics()
        self.refresh_statistics_table()



    def save_statistics(self) -> None:
        try:
            self.parameter_manager.save_statistics(self.statistics)
        except OSError as error:
            QMessageBox.critical(
                self,
                "Statistiques",
                f"Impossible d'enregistrer parameters.txt :\n{error}",
            )
            return

        if self.dashboard_refresh_callback is not None:
            self.dashboard_refresh_callback()

        QMessageBox.information(
            self,
            "Statistiques",
            "Configuration enregistree dans parameters.txt.",
        )
