from PyQt6.QtCore import pyqtSignal, Qt,QDate
from PyQt6.QtWidgets import QFileDialog, QDialog, QMessageBox, QTableWidget, QTableWidgetItem, QWidget,QHeaderView,QAbstractScrollArea

from app.services.exporter import export_csv
from app.ui.dialogs.person_dialog import PersonDialog
from app.ui.ui_loader import load_ui


class PersonsPage(QWidget):
    open_person = pyqtSignal(int)
    data_changed = pyqtSignal()

    def __init__(self, db, photo_dir):
        super().__init__()
        self.db = db
        self.photo_dir = photo_dir
        load_ui("PersonsPage.ui", self)
        self.addButton.setProperty("primary", True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.search.textChanged.connect(self.refresh)
        self.addButton.clicked.connect(self.add_person)
        self.editButton.clicked.connect(self.edit_person)
        self.deleteButton.clicked.connect(self.delete_person)
        self.exportButton.clicked.connect(self.export)
        self.table.doubleClicked.connect(self.show_selected)
        self.refresh()

    def selected_id(self):
        row = self.table.currentRow()
        return int(self.table.item(row, 0).text()) if row >= 0 else None

    def refresh(self):
        rows = self.db.search_persons(self.search.text())
        self.rows = rows
        self.table.setRowCount(len(rows))
        keys = ["id", "matricule","last_name", "first_name", "birth_date", "sex", "profession", "social_category", "city"]
        for r, item in enumerate(rows):
            for c, key in enumerate(keys):
                self.table.setItem(r, c, QTableWidgetItem(str(item.get(key) or "")))
        self.table.resizeColumnsToContents()

        header = self.table.horizontalHeader()

        # Les colonnes occupent toute la largeur disponible
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        # Ascenseur horizontal si nécessaire
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Ascenseur vertical si nécessaire
        self.table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Le tableau s'agrandit avec la fenêtre
        self.table.setSizeAdjustPolicy(
            QAbstractScrollArea.SizeAdjustPolicy.AdjustToContentsOnFirstShow
        )
    def add_person(self):
        dialog = PersonDialog(self.db, str(self.photo_dir), parent=self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        try:
            values = dialog.values()

            # Première insertion sans nouvelle photo.
            #values["photo_path"] = None

            person_id = self.db.save_person(values)

            if person_id is None:
                raise RuntimeError(
                    "La base n'a pas retourné l'identifiant "
                    "de la nouvelle personne."
                )
            '''
            photo_path = dialog.save_photo_for_person(
                int(person_id)
            )
            
            if photo_path:
                self.db.update_person_photo(
                    int(person_id),
                    photo_path,
                )
            '''

            self.refresh()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erreur",
                "Impossible d'enregistrer la personne :\n"
                f"{error}",
            )

    def edit_person(self):
        person_id = self.selected_id()
        if not person_id:
            return
        dialog =  PersonDialog(   db=self.db,    person_id=person_id,    parent=self,
)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            #self.db.get_custom_table_fields(dialog.values(), person_id)
            self.refresh()
            self.data_changed.emit()

    def delete_person(self):
        person_id = self.selected_id()
        if person_id and QMessageBox.question(self, "Confirmation", "Supprimer cette personne et toutes ses données liées ?") == QMessageBox.StandardButton.Yes:
            self.db.delete_person(person_id)
            self.refresh()
            self.data_changed.emit()

    def show_selected(self):
        person_id = self.selected_id()
        if person_id:
            self.open_person.emit(person_id)

    def export(self):
        path, _ = QFileDialog.getSaveFileName(self, "Exporter", "personnes.csv", "CSV (*.csv)")
        if path:
            try:
                export_csv(path, self.db.search_persons(self.search.text()))
                QMessageBox.information(self, "Export", "Export terminé.")
            except ValueError as exc:
                QMessageBox.warning(self, "Export", str(exc))
