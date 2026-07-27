from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPen
from PyQt6.QtWidgets import QWidget


class BarChart(QWidget):
    def __init__(self, title: str):
        super().__init__()
        self.title = title
        self.data: list[dict] = []
        self.setMinimumHeight(230)

    def set_data(self, data: list[dict]) -> None:
        self.data = data
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        rect = self.rect().adjusted(15, 15, -15, -15)
        painter.setPen(self.palette().text().color())
        font = painter.font()
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter, self.title)
        if not self.data:
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "Aucune donnée")
            return
        top = rect.top() + 35
        row_h = max(22, (rect.height() - 45) // len(self.data))
        max_value = max(int(item["value"]) for item in self.data) or 1
        painter.setPen(QPen(self.palette().mid().color(), 1))
        for i, item in enumerate(self.data):
            y = top + i * row_h
            label = str(item["label"])[:24]
            value = int(item["value"])
            painter.setPen(self.palette().text().color())
            painter.drawText(rect.left(), y, 145, row_h - 4, Qt.AlignmentFlag.AlignVCenter, label)
            bar_x = rect.left() + 150
            bar_w = int((rect.width() - 195) * value / max_value)
            painter.fillRect(bar_x, y + 5, max(2, bar_w), row_h - 10, self.palette().highlight())
            painter.drawText(rect.right() - 38, y, 38, row_h - 4, Qt.AlignmentFlag.AlignCenter, str(value))
