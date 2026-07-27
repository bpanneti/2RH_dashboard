from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QListWidgetItem, QMainWindow

from app.ui.pages.dashboard_page import DashboardPage
from app.ui.pages.person_detail_page import PersonDetailPage
from app.ui.pages.persons_page import PersonsPage
from app.ui.pages.ImportDatabaseWindow import ImportDatabaseWindow
from app.ui.pages.settings_page import SettingsPage
from app.ui.ui_loader import load_ui
from app.ui.pages.map_window import PaxMapWindow
from app.ui.pages.statistics_window import StatisticsWindow

class MainWindow(QMainWindow):
    def __init__(self, db, data_dir: Path):
        super().__init__()
        self.db = db
        self.data_dir = data_dir
        load_ui("MainWindow.ui", self)

        for text in ["Tableau de bord", "Personnes", "Configuration","Carte","Statistiques","Import"]:
            self.nav.addItem(QListWidgetItem(text))
        self._load_logo()

        self.statistics = StatisticsWindow(db)
        self.dashboard = DashboardPage(db,_statisticsDataService=self.statistics.data_service)
        self.persons = PersonsPage(db, data_dir / "photos")
        self.map     = PaxMapWindow(db)
        self.settings = SettingsPage(db)
        self.detail = PersonDetailPage(db)
        self.importation = ImportDatabaseWindow(db)


        self.stack.addWidget(self.dashboard)
        self.stack.addWidget(self.persons)
        self.stack.addWidget(self.settings)
        self.stack.addWidget(self.map)
        self.stack.addWidget(self.statistics)
        self.stack.addWidget(self.importation)
        self.stack.addWidget(self.detail)

        self.nav.currentRowChanged.connect(self.navigate)
        self.persons.open_person.connect(self.open_person)
        self.persons.data_changed.connect(self.refresh_all)
        self.detail.back_requested.connect(lambda: self.nav.setCurrentRow(1))
        self.detail.person_changed.connect(self.refresh_all)
        self.nav.setCurrentRow(0)

    def _load_logo(self) -> None:
        # Path(__file__).resolve().parents[2] /
        logo_path = "data/icones/9ESC.png"
        print(logo_path)
        pixmap = QPixmap(str(logo_path))
        #if pixmap.isNull():
         #   self.from qt_material import apply_stylesheetfrom qt_material import apply_stylesheet.setText("LOGO")
          #  return
        self.logo_label.setPixmap(
            pixmap.scaled(
                340,
                152,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
        )

    def navigate(self, index):
        if index >= 0:
            self.stack.setCurrentIndex(index)
        if index == 0:
            self.dashboard.refresh()
        elif index == 1:
            self.persons.refresh()
        elif index == 2:
            self.settings.refresh()
        elif index == 3:
            self.map.refresh()

    def open_person(self, person_id):
        self.detail.load(person_id)
        self.stack.setCurrentWidget(self.detail)
        self.nav.clearSelection()

    def refresh_all(self):
        self.dashboard.refresh()
        self.persons.refresh()
