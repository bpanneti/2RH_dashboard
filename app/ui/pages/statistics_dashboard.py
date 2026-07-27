from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from parameter_manager import ParameterManager
from statistics_calculator import StatisticsCalculator
from statistics_chart_widget import StatisticsChartWidget
from statistics_data_service import StatisticsDataService


class StatisticsDashboardWidget(QWidget):
    def __init__(
        self,
        repository,
        parameters_path: str = "parameters.txt",
        columns: int = 2,
        parent=None,
    ) -> None:
        super().__init__(parent)

        self.repository = repository
        self.data_service = StatisticsDataService(repository)
        self.parameter_manager = ParameterManager(parameters_path)
        self.columns = max(1, columns)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        root_layout.addWidget(self.scroll_area)

        self.content = QWidget()
        self.grid_layout = QGridLayout(self.content)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.content)

        self.refresh_statistics()

    def clear_grid(self) -> None:
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def refresh_statistics(self) -> None:
        self.clear_grid()

        definitions = [
            definition
            for definition in self.parameter_manager.get_statistics()
            if definition.get("show_on_dashboard", False)
        ]

        if not definitions:
            empty_label = QLabel("Aucune statistique selectionnee pour le dashboard.")
            empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.grid_layout.addWidget(empty_label, 0, 0)
            return

        for index, definition in enumerate(definitions):
            row = index // self.columns
            column = index % self.columns

            try:
                result = self.calculate_definition(definition)
                card = self.create_statistic_card(definition, result)
            except Exception as error:
                card = self.create_error_card(definition, str(error))

            self.grid_layout.addWidget(card, row, column)

    def calculate_definition(self, definition: dict[str, Any]) -> Any:
        field_definition: dict[str, Any] = {
            "source_type": definition["source_type"],
            "field_id": definition["field_id"],
            "label": definition.get("field_label", ""),
            "data_type": definition.get("field_data_type", "text"),
        }

        if definition.get("source_type") == "standard":
            field_definition["database_field"] = definition.get(
                "database_field", definition["field_id"]
            )
            field_definition["computed"] = definition.get("computed", False)
        else:
            field_definition["custom_table_id"] = definition.get(
                "custom_table_id"
            )
            field_definition["custom_table_name"] = definition.get(
                "custom_table_name"
            )

        values = self.data_service.get_values(field_definition)
        return StatisticsCalculator.calculate(values, definition["operation"])

    def create_statistic_card(
        self,
        definition: dict[str, Any],
        result: Any,
    ) -> QFrame:
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setMinimumHeight(280)
        card.setStyleSheet(
            "QFrame { border: 1px solid #cccccc; border-radius: 8px; "
            "background: white; } QLabel { border: none; }"
        )

        layout = QVBoxLayout(card)
        chart = StatisticsChartWidget()
        chart.render(
            result=result,
            display_type=definition["display_type"],
            title=definition.get("title", "Statistique"),
        )
        layout.addWidget(chart)
        return card

    def create_error_card(
        self,
        definition: dict[str, Any],
        message: str,
    ) -> QFrame:
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(card)

        title = QLabel(definition.get("title", "Statistique"))
        title.setStyleSheet("font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        error_label = QLabel(message)
        error_label.setWordWrap(True)
        error_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(error_label)
        return card
