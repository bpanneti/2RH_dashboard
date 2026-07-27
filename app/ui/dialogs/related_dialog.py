from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QFormLayout, QLineEdit, QVBoxLayout


FIELDS = {
    "employments": [("Employeur *","employer"),("Poste *","job_title"),("Contrat","contract_type"),("Début (AAAA-MM-JJ)","start_date"),("Fin (AAAA-MM-JJ)","end_date"),("Salaire","salary")],
    "educations": [("École *","school"),("Diplôme","diploma"),("Spécialité","specialty"),("Année début","start_year"),("Année fin","end_year"),("Résultat","result")],
    "sport_results": [("Sport *","sport"),("Épreuve","event_name"),("Date (AAAA-MM-JJ)","event_date"),("Catégorie","category"),("Score","score"),("Classement","ranking"),("Lieu","location")],
}


class RelatedDialog(QDialog):
    def __init__(self, table: str, parent=None):
        super().__init__(parent); self.table = table; self.inputs = {}
        self.setWindowTitle("Ajouter un enregistrement")
        root = QVBoxLayout(self); form = QFormLayout()
        for label, key in FIELDS[table]:
            edit = QLineEdit(); self.inputs[key] = edit; form.addRow(label, edit)
        root.addLayout(form)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept); buttons.rejected.connect(self.reject); root.addWidget(buttons)

    def values(self):
        data = {k:v.text().strip() for k,v in self.inputs.items()}
        for key in ("salary",):
            if key in data and data[key]:
                try: data[key] = float(data[key].replace(",", "."))
                except ValueError: data[key] = None
        for key in ("start_year","end_year","ranking"):
            if key in data and data[key]:
                try: data[key] = int(data[key])
                except ValueError: data[key] = None
        return data
