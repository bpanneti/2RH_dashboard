from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QFrame, QLabel, QVBoxLayout


class StatCard(QFrame):
    def __init__(self, title: str, value: str = "0"):
        super().__init__()
        self.setObjectName("statCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(self)
        self.value_label = QLabel(value)
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = self.value_label.font()
        font.setPointSize(24)
        font.setBold(True)
        self.value_label.setFont(font)
        title_label = QLabel(title)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setProperty("muted", True)
        layout.addWidget(self.value_label)
        layout.addWidget(title_label)

    def set_value(self, value: object) -> None:
        self.value_label.setText(str(value))
