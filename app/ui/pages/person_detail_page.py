from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem, QTabWidget, QVBoxLayout, QWidget
from app.ui.dialogs.related_dialog import RelatedDialog, FIELDS


class PersonDetailPage(QWidget):
    back_requested = pyqtSignal()
    person_changed = pyqtSignal()
    PROJECT_ROOT = Path(__file__).resolve().parents[3]
    PHOTO_DIRECTORY = PROJECT_ROOT / "data" / "photos"
    def __init__(self, db):
        super().__init__(); self.db = db; self.person_id = None
        root = QVBoxLayout(self)
        top = QHBoxLayout(); self.back = QPushButton("Retour"); self.back.clicked.connect(self.back_requested); top.addWidget(self.back)
        self.title = QLabel(); f=self.title.font(); f.setPointSize(18); f.setBold(True); self.title.setFont(f); top.addWidget(self.title); top.addStretch(); root.addLayout(top)
        header = QHBoxLayout(); self.photo = QLabel(); self.photo.setFixedSize(160,160); header.addWidget(self.photo)
        self.info = QLabel(); self.info.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse); header.addWidget(self.info); header.addStretch(); root.addLayout(header)
        self.tabs = QTabWidget(); root.addWidget(self.tabs)
        self.tables = {}

    def load(self, person_id: int):
        self.person_id=person_id; p=self.db.person(person_id)
        if not p: return
        self.title.setText(f"{p['first_name']} {p['last_name']}")
        self.info.setText(f"<b>Naissance :</b> {p.get('birth_date') or '-'}<br><b>Sexe :</b> {p.get('sex') or '-'}<br><b>Profession :</b> {p.get('profession') or '-'}<br><b>Catégorie :</b> {p.get('social_category') or '-'}<br><b>Ville :</b> {p.get('city') or '-'}<br><b>Contact :</b> {p.get('email') or '-'} / {p.get('phone') or '-'}<br><br>{p.get('notes') or ''}")

        path=p.get('photo_path')


        if path and Path(str(self.PHOTO_DIRECTORY )+'/' +path).exists(): self.photo.setPixmap(QPixmap(str(self.PHOTO_DIRECTORY )+'/' +path).scaled(160,160,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation))
        else: self.photo.setText("Aucune photo")
        for table in self.tables: self.refresh_table(table)

    def refresh_table(self, table):
        rows=self.db.related(table,self.person_id); cols=[k for _,k in FIELDS[table]]; widget=self.tables[table]; widget.setColumnCount(len(cols)+1); widget.setHorizontalHeaderLabels(["ID"]+[label.replace(" *","") for label,_ in FIELDS[table]]); widget.setRowCount(len(rows))
        for r,row in enumerate(rows):
            for c,key in enumerate(["id"]+cols): widget.setItem(r,c,QTableWidgetItem(str(row.get(key) or "")))
        widget.resizeColumnsToContents()

    def add_row(self, table):
        dialog=RelatedDialog(table,self)
        if dialog.exec()==QDialog.DialogCode.Accepted:
            self.db.add_related(table,self.person_id,dialog.values()); self.refresh_table(table); self.person_changed.emit()

    def delete_row(self, table):
        widget=self.tables[table]; row=widget.currentRow()
        if row<0: return
        row_id=int(widget.item(row,0).text())
        if QMessageBox.question(self,"Confirmation","Supprimer cet enregistrement ?")==QMessageBox.StandardButton.Yes:
            self.db.delete_related(table,row_id); self.refresh_table(table); self.person_changed.emit()
