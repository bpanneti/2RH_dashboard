import sys
from pathlib import Path
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QIcon,QPixmap
from PyQt6.QtWidgets import QApplication,QSplashScreen
import time
import qt_modern_style

from app.db.database import Database
from app.ui.main_window import MainWindow
from qt_material import apply_stylesheet


def main() -> int:





    root = Path(__file__).resolve().parent
    data_dir = root / "data"
    data_dir.mkdir(exist_ok=True)

    app = QApplication(sys.argv)


    splash = QSplashScreen(QPixmap("data/icones/montereau.png"))
    splash.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    time.sleep(2)
    splash.showMessage(
        "Chargement réseau...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
        Qt.GlobalColor.white
    )

    app.processEvents()

    time.sleep(3.0)

    splash.showMessage(
        "Chargement interface...",
        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter,
        Qt.GlobalColor.white
    )

    app.processEvents()
    time.sleep(3.0)

    app.setApplicationName("9 esc Dashboard")
    app.setOrganizationName("2 RH")
    apply_stylesheet(app, theme="dark_teal.xml")

    db = Database(data_dir / "population.db")


    window = MainWindow(db, data_dir)
    window.show()
    splash.finish(window)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
