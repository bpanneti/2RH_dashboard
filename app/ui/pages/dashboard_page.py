from PyQt6.QtWidgets import QFrame,QGridLayout, QPushButton, QSizePolicy,QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget
from PyQt6.QtCore import Qt
from app.widgets.bar_chart import BarChart
from app.widgets.stat_card import StatCard
from app.ui.pages.parameter_manager import ParameterManager
from app.ui.pages.statistics_calculator import StatisticsCalculator
from app.ui.pages.statistics_chart_widget import StatisticsChartWidget
from app.ui.pages.map_window import PaxMapWindow

class DashboardPage(QWidget):
    def __init__(self, db, _map=None,open_statistics_callback=None,_statisticsDataService=None,parent=None ):
        super().__init__(parent)
        self.db = db
        #root = QVBoxLayout(self)
        #title = QLabel("Tableau de bord de la population")
        #f = title.font(); f.setPointSize(20); f.setBold(True); title.setFont(f)
        #root.addWidget(title)

        self.open_statistics_callback = (
            open_statistics_callback
        )




        self.parameter_manager = ParameterManager(
            "parameters.txt"
        )
        self.data_service = _statisticsDataService

        self.cards = {}

        self.statistic_widgets = []

        self.build_ui()

        #self.refresh_statistics()

    def build_ui(self):

            main_layout = QVBoxLayout(self)

            main_layout.setContentsMargins(
                15,
                15,
                15,
                15,
            )

            main_layout.setSpacing(12)

            header_layout = QGridLayout()

            title_label = QLabel(
                "Tableau de bord"
            )

            title_label.setStyleSheet(
                """
                QLabel {
                    font-size: 22px;
                    font-weight: bold;
                }
                """
            )

            self.cardsLayout = QHBoxLayout()


            header_layout.addWidget(
                title_label,
                0,
                0,
            )

            header_layout.setColumnStretch(
                0,
                1,
            )

            self.refresh_button = QPushButton(
                "Actualiser"
            )

            self.refresh_button.clicked.connect(
                self.refresh_statistics
            )

            header_layout.addWidget(
                self.refresh_button,
                0,
                1,
            )

            if (
                    self.open_statistics_callback
                    is not None
            ):
                configure_button = QPushButton(
                    "Configurer les statistiques"
                )

                configure_button.clicked.connect(
                    self.open_statistics_callback
                )

                header_layout.addWidget(
                    configure_button,
                    0,
                    2,
                )

            main_layout.addLayout(
                header_layout
            )


            self.status_label = QLabel()

            main_layout.addLayout(self.cardsLayout)

            self.status_label.setStyleSheet(
                """
                QLabel {
                    color: #666666;
                }
                """
            )

            main_layout.addWidget(
                self.status_label
            )

            self.scroll_area = QScrollArea()

            self.scroll_area.setWidgetResizable(
                True
            )

            self.scroll_area.setFrameShape(
                QFrame.Shape.NoFrame
            )

            self.statistics_container = QWidget()

            self.statistics_grid = QGridLayout(
                self.statistics_container
            )

            self.statistics_grid.setContentsMargins(
                0,
                0,
                0,
                0,
            )

            self.statistics_grid.setHorizontalSpacing(
                15
            )

            self.statistics_grid.setVerticalSpacing(
                15
            )

            self.statistics_grid.setAlignment(
                Qt.AlignmentFlag.AlignTop
            )

            self.scroll_area.setWidget(
                self.statistics_container
            )

            main_layout.addWidget(
                self.scroll_area,
                1,
            )

    def create_statistic_widget(
        self,
        definition: dict,
    ) -> QWidget:

        values = self.data_service.get_values(
            definition
        )

        operation = definition.get(
            "operation"
        )


        result = StatisticsCalculator.calculate(
            values=values,
            operation=operation,
        )


        chart_widget =None
        if operation == "count":
            if definition.get("title") not in  self.cards:
                chart_widget = StatCard(definition.get("title"))
                chart_widget.set_value(result)
                self.cards[definition.get("title")] = chart_widget
            else :
                self.cards[definition.get("title")].set_value(result)
        else :

            chart_widget = StatisticsChartWidget(
                parent=self
            )

            chart_widget.setMinimumHeight(
                280
            )

            chart_widget.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Expanding,
            )

            chart_widget.set_statistic(
                title=definition.get("title"),
                result=result,
                display_type=definition.get("display_type"),
            )


        return chart_widget

    def clear_layout(
        self,
        layout,
    ) -> None:

        while layout.count():

            item = layout.takeAt(0)

            widget = item.widget()

            if widget is not None:
                widget.deleteLater()

            child_layout = item.layout()

            if child_layout is not None:
                self.clear_layout(
                    child_layout
                )
    def clear_statistics_grid(self) -> None:

        self.statistic_widgets.clear()

        while self.statistics_grid.count():

            item = (
                self.statistics_grid
                .takeAt(0)
            )

            widget = item.widget()

            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()

            child_layout = item.layout()

            if child_layout is not None:
                self.clear_layout(
                    child_layout
                )
    def refresh_statistics(self) -> None:

        self.refresh_button.setEnabled(
            False
        )

        self.status_label.setText(
            "Mise à jour des statistiques..."
        )

        try:
            self.clear_statistics_grid()

            definitions = (
                self.parameter_manager
                .get_statistics()
            )


            definitions = [
                definition
                for definition in definitions
                if definition.get(
                    "show_on_dashboard",
                    False,
                )
            ]

            if not definitions:
                self.show_empty_dashboard()

                self.status_label.setText(
                    "Aucune statistique sélectionnée "
                    "pour le dashboard."
                )

                return

            self.map = PaxMapWindow(self.db)
            self.statistics_grid.addWidget(
                self.map,
                0,0
            )

            for index, definition in enumerate(
                definitions
            ):


                widget = self.create_statistic_widget( definition)


                if definition.get('operation','')=='count':
                    if widget is not None:
                      self.cardsLayout.addWidget(widget)

                else:
                    print(index)
                    row = index // 2
                    column = index % 2
                    print('----> 1')
                    self.statistics_grid.addWidget(
                        widget,
                        row,
                        column,
                    )
                    print('----> 2')
                    self.statistic_widgets.append(
                        widget
                    )
                    print('----> 3')

            self.set_equal_column_stretch()

            self.status_label.setText(
                f"{len(definitions)} statistique(s) "
                f"mise(s) à jour."
            )

        except Exception as error:
            self.status_label.setText(
                "Erreur pendant la mise à jour."
            )

            self.show_error_dashboard(
                str(error)
            )

        finally:
            self.refresh_button.setEnabled(
                True
            )
    def refresh(self):
        pass
        #stats = self.db.dashboard_stats()
        #for key, card in self.cards.items(): card.set_value(stats[key])
        #for key, chart in self.charts.items(): chart.set_data(stats[key])
    def show_empty_dashboard(self) -> None:

        empty_label = QLabel(
            "Aucune statistique n’est configurée "
            "pour le tableau de bord.\n\n"
            "Ouvrez la page Statistiques, créez "
            "une statistique et cochez "
            "« Afficher sur le dashboard »."
        )

        empty_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        empty_label.setWordWrap(
            True
        )

        empty_label.setMinimumHeight(
            250
        )

        empty_label.setStyleSheet(
            """
            QLabel {
                color: #777777;
                font-size: 15px;
                border: 1px dashed #aaaaaa;
                border-radius: 8px;
                padding: 20px;
            }
            """
        )

        self.statistics_grid.addWidget(
            empty_label,
            0,
            0,
            1,
            2,
        )

    def show_error_dashboard(
        self,
        message: str,
    ) -> None:

        error_label = QLabel(
            "Impossible d’afficher les statistiques.\n\n"
            f"{message}"
        )

        error_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        error_label.setWordWrap(
            True
        )

        error_label.setStyleSheet(
            """
            QLabel {
                color: #a00000;
                border: 1px solid #a00000;
                border-radius: 8px;
                padding: 20px;
            }
            """
        )

        self.statistics_grid.addWidget(
            error_label,
            0,
            0,
            1,
            2,
        )
    def set_equal_column_stretch(
        self,
    ) -> None:

        self.statistics_grid.setColumnStretch(
            0,
            1,
        )

        self.statistics_grid.setColumnStretch(
            1,
            1,
        )