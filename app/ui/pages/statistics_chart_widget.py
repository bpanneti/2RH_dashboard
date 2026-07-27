import math
from typing import Any

import numpy as np
import pyqtgraph as pg
from PyQt6.QtCore import QRectF, Qt
from PyQt6.QtGui import QBrush, QColor, QPainterPath, QPen,QPalette,QFont
from PyQt6.QtWidgets import QGraphicsPathItem, QLabel, QVBoxLayout, QWidget

class StatisticsChartWidget(QWidget):
    COLORS = [
        "#1de9b6",  # Teal principal
        "#6effe8",  # Teal clair
        "#00bfa5",  # Teal foncé
        "#26a69a",  # Teal moyen
        "#80cbc4",  # Teal pastel
        "#00897b",  # Teal profond
        "#4db6ac",  # Teal secondaire
        "#b2dfdb",  # Teal très clair
        "#00695c",  # Teal sombre
    ]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.result_label = QLabel()
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet(
            "QLabel { font-size: 26px; font-weight: bold; padding: 8px; }"
        )
        layout.addWidget(self.result_label)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground("w")
        self.plot_widget.showGrid(x=True, y=True, alpha=0.2)

        layout.addWidget(self.plot_widget, 1)


        self.apply_theme_colors()

        self.configure_plot_background()

    def configure_plot_background(self) -> None:
        background_color = QColor("#31363b")

        # Fond géré par PyQtGraph.
        self.plot_widget.setBackground(background_color)

        # Fond de la scène graphique.
        self.plot_widget.scene().setBackgroundBrush(
            QBrush(background_color)
        )

        # Fond du viewport interne de QGraphicsView.
        viewport = self.plot_widget.viewport()

        viewport.setAutoFillBackground(True)

        viewport_palette = viewport.palette()

        viewport_palette.setColor(
            QPalette.ColorRole.Window,
            background_color,
        )

        viewport_palette.setColor(
            QPalette.ColorRole.Base,
            background_color,
        )

        viewport.setPalette(viewport_palette)

        # Empêche une feuille de style de remettre le fond en blanc.
        self.plot_widget.setStyleSheet(
            """
            QGraphicsView {
                background-color: #232629;
                border: none;
            }

            QGraphicsView QWidget {
                background-color: #232629;
            }
            """
        )
    def apply_theme_colors(self) -> None:

        background_color = (
            self.plot_widget
            .palette()
            .color(
                QPalette.ColorRole.Window
            )
        )

        text_color = (
            self.plot_widget
            .palette()
            .color(
                QPalette.ColorRole.WindowText
            )
        )

        self.plot_widget.setBackground(
            background_color
        )

        self.text_color = QColor('white')
        self.background_color = background_color

        for axis_name in (
            "left",
            "bottom",
        ):
            axis = self.plot_widget.getAxis(
                axis_name
            )

            axis.setPen(
                pg.mkPen(
                    self.text_color
                )
            )

            axis.setTextPen(
                pg.mkPen(
                    self.text_color
                )
            )
            for axis_name in (
                    "left",
                    "bottom",
            ):
                axis = self.plot_widget.getAxis(
                    axis_name
                )

                axis.setPen(
                    pg.mkPen(
                        self.text_color
                    )
                )

                axis.setTextPen(
                    pg.mkPen(
                        self.text_color
                    )
                )

    def render(self, result: Any, display_type: str, title: str = "") -> None:
        self._reset_plot()

        if display_type == "number":
            self.show_number(result, title)
        elif display_type == "pie":
            self.show_pie_chart(result)
        elif display_type == "bar":
            self.show_bar_chart(result, title)
        elif display_type == "histogram":
            self.show_histogram(result, title)
        else:
            self.show_error(f"Affichage inconnu : {display_type}")

    def _reset_plot(self) -> None:
        self.result_label.clear()
        self.plot_widget.clear()
        self.plot_widget.show()
        self.plot_widget.showAxis("left")
        self.plot_widget.showAxis("bottom")
        self.plot_widget.setAspectLocked(False)
        self.plot_widget.setMouseEnabled(x=True, y=True)
        self._remove_legend()

    def _remove_legend(self) -> None:
        plot_item = self.plot_widget.getPlotItem()
        legend = plot_item.legend
        if legend is not None:
            legend.scene().removeItem(legend)
            plot_item.legend = None


    def show_pie_chart(
            self,
            result: list[dict],
    ) -> None:

        self.plot_widget.show()
        self.plot_widget.clear()

        plot_item = self.plot_widget.getPlotItem()

        # Suppression de l’ancienne légende PyQtGraph.
        if plot_item.legend is not None:
            legend = plot_item.legend
            legend.scene().removeItem(legend)
            plot_item.legend = None

        self.plot_widget.hideAxis("left")
        self.plot_widget.hideAxis("bottom")

        self.plot_widget.setAspectLocked(True)

        self.plot_widget.setMouseEnabled(
            x=False,
            y=False,
        )

        if not result:
            text_item = pg.TextItem(
                "Aucune donnée",
                anchor=(0.5, 0.5),
                color=self.text_color,
            )

            text_item.setPos(0, 0)

            self.plot_widget.addItem(text_item)

            self.plot_widget.setXRange(
                -1,
                1,
                padding=0,
            )

            self.plot_widget.setYRange(
                -1,
                1,
                padding=0,
            )

            return

        total = sum(
            item.get("count", 0)
            for item in result
        )

        if total <= 0:
            return

        colors = [
            QColor("#1de9b6"),  # Teal principal
            QColor("#6effe8"),  # Teal clair
            QColor("#00bfa5"),  # Teal foncé
            QColor("#26a69a"),  # Teal moyen
            QColor("#80cbc4"),  # Teal pastel
            QColor("#00897b"),  # Teal profond
            QColor("#4db6ac"),  # Teal secondaire
            QColor("#b2dfdb"),  # Teal très clair
            QColor("#00695c"),  # Teal sombre
        ]

        radius = 100.0

        pie_rectangle = QRectF(
            -radius,
            -radius,
            radius * 2,
            radius * 2,
        )

        start_angle = 0.0

        for index, item in enumerate(result):

            count = item.get("count", 0)

            if count <= 0:
                continue

            label = str(
                item.get(
                    "label",
                    "Non renseigné",
                )
            )

            percentage = (
                                 count / total
                         ) * 100.0

            span_angle = (
                                 count / total
                         ) * 360.0

            # ---------------------------------
            # Création du secteur
            # ---------------------------------

            path = QPainterPath()

            path.moveTo(0, 0)

            path.arcTo(
                pie_rectangle,
                start_angle,
                -span_angle,
            )

            path.closeSubpath()

            sector_item = QGraphicsPathItem(path)

            color = colors[
                index % len(colors)
                ]

            sector_item.setBrush(
                QBrush(color)
            )

            sector_item.setPen(
                QPen(
                    self.background_color,
                    1.5,
                )
            )

            sector_item.setToolTip(
                f"{label}\n"
                f"Effectif : {count}\n"
                f"Proportion : {percentage:.1f} %"
            )

            self.plot_widget.addItem(
                sector_item
            )

            # ---------------------------------
            # Angle situé au milieu du secteur
            # ---------------------------------

            middle_angle = (
                    (start_angle
                    + span_angle / 2.0)
            )


            if middle_angle < 0:
                middle_angle = -start_angle+span_angle / 2.0


            angle_radians = math.radians(
                middle_angle
            )

            cosine = math.cos( angle_radians)
            sine = math.sin(angle_radians)

            # ---------------------------------
            # Position de départ de la ligne
            # ---------------------------------
            # La ligne commence à environ 55 %
            # du rayon, donc à peu près au milieu
            # du secteur.

            line_start_radius = radius * 0.52

            line_start_x = (
                    line_start_radius * cosine
            )

            line_start_y = (
                    line_start_radius * sine
            )

            # ---------------------------------
            # Position de sortie du camembert
            # ---------------------------------

            line_edge_radius = radius * 1.03

            line_edge_x = (
                    line_edge_radius * cosine
            )

            line_edge_y = (
                    line_edge_radius * sine
            )

            # ---------------------------------
            # Position du texte
            # ---------------------------------

            text_radius = radius * 1.30

            print('label',label)
            print('start_angle', start_angle)
            print('span_angle', span_angle)
            print('middle_angle',middle_angle)

            text_x = text_radius * cosine
            text_y = text_radius * sine

            # Petit décalage horizontal pour
            # éviter que le texte touche la ligne.

            horizontal_offset = 8.0

            if cosine >= 0:
                text_x += horizontal_offset
                text_anchor = (0.0, 0.5)

            else:
                text_x -= horizontal_offset
                text_anchor = (1.0, 0.5)

            # ---------------------------------
            # Ligne radiale
            # ---------------------------------

            radial_line = pg.PlotDataItem(
                x=[
                    line_start_x,
                    line_edge_x,
                ],
                y=[
                    line_start_y,
                    line_edge_y,
                ],
                pen=pg.mkPen(
                    color=color,
                    width=2,
                ),
            )

            self.plot_widget.addItem(
                radial_line
            )

            # ---------------------------------
            # Ligne horizontale vers le texte
            # ---------------------------------

            horizontal_end_x = (
                text_x - horizontal_offset
                if cosine >= 0
                else text_x + horizontal_offset
            )

            horizontal_line = pg.PlotDataItem(
                x=[
                    line_edge_x,
                    horizontal_end_x,
                ],
                y=[
                    line_edge_y,
                    text_y,
                ],
                pen=pg.mkPen(
                    color=color,
                    width=2,
                ),
            )

            self.plot_widget.addItem(
                horizontal_line
            )

            # ---------------------------------
            # Texte de légende
            # ---------------------------------

            legend_text = (
                f"{label}\n"
                f"{percentage:.1f} % ({count})"
            )
            font = QFont("Arial", 10, QFont.Weight.Bold)

            text_item = pg.TextItem(
                text=legend_text,
                anchor=text_anchor,
                color=self.text_color,
            )

            text_item.setFont(font)
            text_item.setPos(
                text_x,
                text_y,
            )

            self.plot_widget.addItem(
                text_item
            )

            start_angle -= span_angle

        # Espace supplémentaire pour les textes.
        display_radius = radius * 1.85

        self.plot_widget.setXRange(
            -display_radius,
            display_radius,
            padding=0,
        )

        self.plot_widget.setYRange(
            -display_radius,
            display_radius,
            padding=0,
        )

    def show_number(self, result: Any, title: str = "") -> None:
        self.plot_widget.hide()

        if result is None:
            value_text = "Non disponible"
        elif isinstance(result, float):
            value_text = f"{result:.2f}"
        else:
            value_text = str(result)

        if title:
            self.result_label.setText(f"{title}\n{value_text}")
        else:
            self.result_label.setText(value_text)
    '''
    def show_pie_chart(self, result: list[dict[str, Any]], title: str = "") -> None:
        self.result_label.setText(title)
        self.plot_widget.hideAxis("left")
        self.plot_widget.hideAxis("bottom")
        self.plot_widget.setAspectLocked(True)
        self.plot_widget.setMouseEnabled(x=False, y=False)

        if not result:
            self.show_empty_plot("Aucune donnee")
            return

        total = sum(float(item.get("count", 0)) for item in result)
        if total <= 0:
            self.show_empty_plot("Aucune donnee")
            return

        radius = 100.0
        rectangle = QRectF(-radius, -radius, 2 * radius, 2 * radius)
        start_angle = 0.0

        legend = self.plot_widget.addLegend(offset=(10, 10))

        for index, item in enumerate(result):
            count = float(item.get("count", 0))
            percentage = count * 100.0 / total
            span_angle = count * 360.0 / total
            color = QColor(self.COLORS[index % len(self.COLORS)])

            path = QPainterPath()
            path.moveTo(0, 0)
            path.arcTo(rectangle, start_angle, span_angle)
            path.closeSubpath()

            sector = QGraphicsPathItem(path)
            sector.setBrush(QBrush(color))
            sector.setPen(QPen(QColor("white"), 1.5))
            sector.setToolTip(
                f"{item.get('label', '')}\n"
                f"Effectif : {int(count)}\n"
                f"Proportion : {percentage:.1f} %"
            )
            self.plot_widget.addItem(sector)

            if percentage >= 5.0:
                middle_angle = start_angle + span_angle / 2.0
                radians = math.radians(middle_angle)
                text_radius = radius * 0.62
                label = pg.TextItem(
                    f"{percentage:.1f} %",
                    anchor=(0.5, 0.5),
                    color=QColor("white"),
                )
                label.setPos(
                    text_radius * math.cos(radians),
                    text_radius * math.sin(radians),
                )
                self.plot_widget.addItem(label)

            sample = pg.PlotDataItem(
                [],
                [],
                pen=None,
                symbol="s",
                symbolSize=12,
                symbolBrush=color,
            )
            legend.addItem(sample, f"{item.get('label', '')} ({percentage:.1f} %)")
            start_angle += span_angle

        self.plot_widget.setXRange(-135, 135, padding=0)
        self.plot_widget.setYRange(-135, 135, padding=0)
    '''
    def show_bar_chart(self, result: list[dict[str, Any]], title: str = "") -> None:

        self.result_label.setText(title)

        if not result:
            self.show_empty_plot("Aucune donnee")
            return

        # Tri croissant de x


        labels = [str(item.get("label", "")) for item in result]
        values = [float(item.get("count", 0)) for item in result]
        x_values = np.arange(len(values), dtype=float)

        data = sorted(zip(labels, values), key=lambda t: t[1])

        x_values = [d[0] for d in data]
        values = [d[1] for d in data]
        labels = x_values
        x_values = list(range(len(x_values)))
        bars = pg.BarGraphItem(
            x=x_values,
            height=values,
            width=0.7,
            brush=QColor(self.COLORS[0]),
            pen=None#QPen(QColor(self.COLORS[1])),
        )
        self.plot_widget.addItem(bars)

        self.plot_widget.getAxis("bottom").setTicks(
            [[(index, label) for index, label in enumerate(labels)]]
        )
        self.plot_widget.setLabel("left", "Effectif")
        self.plot_widget.setLabel("bottom", "Categories")
        self.plot_widget.setXRange(-1, len(values), padding=0.03)

        maximum = max(values) if values else 0
        self.plot_widget.setYRange(0, maximum * 1.18 if maximum > 0 else 1)

        for index, value in enumerate(values):
            text_item = pg.TextItem(
                str(int(value) if value.is_integer() else value),
                anchor=(0.5, 1.0),
                color=self.text_color,
            )
            text_item.setPos(index, value)
            self.plot_widget.addItem(text_item)

    def show_histogram(self, result: list[float], title: str = "") -> None:


        self.result_label.setText(title)

        if not result:
            self.show_empty_plot("Aucune donnee")
            return

        values = np.asarray(result, dtype=float)
        counts, edges = np.histogram(values, bins="auto")
        widths = np.diff(edges)
        centers = (edges[:-1] + edges[1:]) / 2.0

        histogram = pg.BarGraphItem(
            x=centers,
            height=counts,
            width=widths * 0.90,
            brush=QColor(self.COLORS[0]),
            pen=QPen(QColor("#2F4F6F")),
        )
        self.plot_widget.addItem(histogram)
        self.plot_widget.setLabel("left", "Effectif")
        self.plot_widget.setLabel("bottom", "Valeur")

        maximum = int(counts.max()) if len(counts) else 0
        self.plot_widget.setYRange(0, maximum * 1.18 if maximum > 0 else 1)

    def show_empty_plot(self, message: str) -> None:
        self.plot_widget.clear()
        self.plot_widget.hideAxis("left")
        self.plot_widget.hideAxis("bottom")

        text_item = pg.TextItem(
            message,
            anchor=(0.5, 0.5),
            color=self.text_color,
        )
        text_item.setPos(0, 0)
        self.plot_widget.addItem(text_item)
        self.plot_widget.setXRange(-1, 1)
        self.plot_widget.setYRange(-1, 1)

    def show_error(self, message: str) -> None:
        self.plot_widget.hide()
        self.result_label.setText(message)

    def set_statistic(
            self,
            title: str,
            result,
            display_type: str,
    ) -> None:


        #self.title_label.setText(
        #     title
        #)

        self.clear_chart()

        if display_type == "number":
            self.show_number(
                result
            )

        elif display_type == "pie":
            self.show_pie_chart(
                result
            )

        elif display_type == "bar":
            self.show_bar_chart(
                result
            )

        elif display_type == "histogram":
            self.show_histogram(
                result
            )

        else:
            self.show_error(
                f"Affichage inconnu : "
                f"{display_type}"
            )

    def clear_chart(self) -> None:

        #self.value_label.clear()

        self.plot_widget.clear()

        self.plot_widget.show()

        plot_item = (
            self.plot_widget
            .getPlotItem()
        )

        if plot_item.legend is not None:
            legend = plot_item.legend

            legend.scene().removeItem(
                legend
            )

            plot_item.legend = None

        self.plot_widget.setAspectLocked(
            False
        )

        self.plot_widget.showAxis(
            "left"
        )

        self.plot_widget.showAxis(
            "bottom"
        )

        self.plot_widget.setMouseEnabled(
            x=True,
            y=True,
        )
