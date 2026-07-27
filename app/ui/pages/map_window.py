import html
import json
import time
from typing import Optional

import requests

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView

class GeocodingWorker(QThread):

    progress = pyqtSignal(int, int, str)
    finished_successfully = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, persons: list[dict], parent=None):
        super().__init__(parent)

        self.persons = persons
        self._running = True

        self.session = requests.Session()

        # Obligatoire pour le service public Nominatim
        self.session.headers.update(
            {
                "User-Agent": (
                    "PaxManagementApplication/1.0 "
                    "(contact: votre-email@example.com)"
                )
            }
        )

    def stop(self) -> None:
        self._running = False

    def run(self) -> None:
        results = []

        total = len(self.persons)

        try:
            for index, person in enumerate(
                self.persons,
                start=1,
            ):
                if not self._running:
                    break

                name = person.get("name", "PAX")
                address = person.get("address", "")

                self.progress.emit(
                    index,
                    total,
                    name,
                )

                # Si les coordonnées sont déjà en base,
                # aucun géocodage n'est nécessaire.
                latitude = person.get("latitude")
                longitude = person.get("longitude")

                if (
                    latitude is not None
                    and longitude is not None
                ):
                    person["latitude"] = float(latitude)
                    person["longitude"] = float(longitude)

                    results.append(person)
                    continue

                coordinates = self.geocode_address(
                    address
                )

                if coordinates is not None:
                    latitude, longitude, display_name = (
                        coordinates
                    )

                    person["latitude"] = latitude
                    person["longitude"] = longitude
                    person["display_address"] = display_name

                    results.append(person)

                # Limitation du service public Nominatim :
                # une requête par seconde au maximum.
                time.sleep(1)

            self.finished_successfully.emit(results)

        except Exception as error:
            self.error.emit(str(error))

    def geocode_address(
            self,
            address: str,
    ) -> Optional[tuple[float, float, str]]:

        address = address.strip()

        if not address:
            print("Adresse vide")
            return None

        url = "https://nominatim.openstreetmap.org/search"

        params = {
            "q": address,
            "format": "jsonv2",
            "limit": 1,
            "countrycodes": "fr",
            "addressdetails": 1,
        }

        headers = {
            "User-Agent": (
                "PaxManagement/1.0 "
                "(contact: ton-adresse-email@domaine.fr)"
            ),
            "Accept-Language": "fr",
            "Accept": "application/json",
        }

        try:
            print(f"Géocodage de : {address}")

            response = requests.get(
                url,
                params=params,
                headers=headers,
                timeout=20,
            )

            print("URL appelée :", response.url)
            print("Code HTTP :", response.status_code)
            print("Réponse :", response.text[:500])

            response.raise_for_status()

            data = response.json()

            if not data:
                print(
                    f"Aucun résultat trouvé pour : {address}"
                )
                return None

            result = data[0]

            return (
                float(result["lat"]),
                float(result["lon"]),
                result.get(
                    "display_name",
                    address,
                ),
            )

        except requests.exceptions.SSLError as error:
            print("Erreur SSL :", error)
            raise RuntimeError(
                "Erreur SSL lors de la connexion à OpenStreetMap.\n"
                "Vérifie les certificats Python et la connexion réseau."
            ) from error

        except requests.exceptions.ConnectionError as error:
            print("Erreur de connexion :", error)
            raise RuntimeError(
                "Impossible de joindre Nominatim.\n"
                "Vérifie la connexion Internet, le proxy ou le pare-feu."
            ) from error

        except requests.exceptions.Timeout as error:
            print("Délai dépassé :", error)
            raise RuntimeError(
                "Le serveur Nominatim ne répond pas dans le délai imparti."
            ) from error

        except requests.exceptions.HTTPError as error:
            status_code = response.status_code

            raise RuntimeError(
                f"Erreur HTTP Nominatim : {status_code}\n"
                f"{response.text[:300]}"
            ) from error

        except ValueError as error:
            print("Réponse JSON invalide :", response.text[:500])

            raise RuntimeError(
                "La réponse de Nominatim n'est pas un JSON valide."
            ) from error
class PaxMapWindow(QWidget):

    def __init__(
        self,
        db,
        parent=None,
    ):
        super().__init__(parent)

        self.db = db
        self.geocoding_worker = None

        self.setWindowTitle(
            "Localisation des PAX"
        )

        self.resize(1200, 800)

        self.setAttribute(
            Qt.WidgetAttribute.WA_DeleteOnClose,
            True,
        )

        self.build_ui()
        self.load_persons()

    def build_ui(self) -> None:
        main_layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()

        title_label = QLabel(
            "Localisation géographique des PAX"
        )

        title_label.setStyleSheet(
            """
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
            """
        )

        top_layout.addWidget(title_label)
        top_layout.addStretch()

        self.status_label = QLabel(
            "Chargement..."
        )

        top_layout.addWidget(
            self.status_label
        )

        self.refresh_button = QPushButton(
            "Actualiser"
        )

        self.refresh_button.clicked.connect(
            self.load_persons
        )

        top_layout.addWidget(
            self.refresh_button
        )



        main_layout.addLayout(top_layout)

        self.progress_bar = QProgressBar()

        self.progress_bar.setVisible(False)

        main_layout.addWidget(
            self.progress_bar
        )

        self.web_view = QWebEngineView()

        main_layout.addWidget(
            self.web_view,
            1,
        )
    def load_persons(self) -> None:
        if (
            self.geocoding_worker is not None
            and self.geocoding_worker.isRunning()
        ):
            return

        try:
            rows = self.db.get_persons_for_map()

        except Exception as error:
            QMessageBox.critical(
                self,
                "Erreur",
                "Impossible de charger les PAX :\n"
                f"{error}",
            )
            return

        persons = []

        for row in rows:
            person = dict(row)

            address = self.build_person_address(
                person
            )

            if not address:
                continue

            first_name = (
                person.get("first_name")
                or person.get("firstname")
                or person.get("prenom")
                or ""
            )

            last_name = (
                person.get("last_name")
                or person.get("lastname")
                or person.get("nom")
                or ""
            )

            full_name = (
                f"{first_name} {last_name}"
            ).strip()

            persons.append(
                {
                    "id": person.get("id"),
                    "name": full_name or "PAX",
                    "grade": person.get("grade") or "",
                    "unit": (
                        person.get("unit")
                        or person.get("unite")
                        or ""
                    ),
                    "address": address,
                    "display_address": address,
                    "latitude": person.get("latitude"),
                    "longitude": person.get("longitude"),
                }
            )

        if not persons:
            self.status_label.setText(
                "Aucun PAX avec une adresse"
            )

            self.web_view.setHtml(
                self.create_empty_page()
            )

            return

        self.start_geocoding(persons)

    @staticmethod
    def build_person_address(
        person: dict,
    ) -> str:

        street = (
            person.get("address")
            or person.get("street")
            or person.get("adresse")
            or ""
        )

        address_extra = (
            person.get("address_extra")
            or person.get("complement_adresse")
            or ""
        )

        postal_code = (
            person.get("postal_code")
            or person.get("zip_code")
            or person.get("code_postal")
            or ""
        )

        city = (
            person.get("city")
            or person.get("ville")
            or ""
        )

        country = (
            person.get("country")
            or person.get("pays")
            or "France"
        )

        parts = [
            str(value).strip()
            for value in (
                street,
                address_extra,
                postal_code,
                city,
                country,
            )
            if value is not None
            and str(value).strip()
        ]

        return ", ".join(parts)


    def start_geocoding(
        self,
        persons: list[dict],
    ) -> None:

        self.refresh_button.setEnabled(False)

        self.progress_bar.setVisible(True)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(len(persons))
        self.progress_bar.setValue(0)

        self.status_label.setText(
            "Localisation des PAX..."
        )

        self.geocoding_worker = GeocodingWorker(
            persons,
            self,
        )

        self.geocoding_worker.progress.connect(
            self.update_geocoding_progress
        )

        self.geocoding_worker.finished_successfully.connect(
            self.display_map
        )

        self.geocoding_worker.error.connect(
            self.handle_geocoding_error
        )

        self.geocoding_worker.start()


    def update_geocoding_progress(
        self,
        current: int,
        total: int,
        name: str,
    ) -> None:

        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

        self.status_label.setText(
            f"Localisation {current}/{total} : {name}"
        )

    def handle_geocoding_error(
        self,
        message: str,
    ) -> None:

        self.refresh_button.setEnabled(True)
        self.progress_bar.setVisible(False)

        self.status_label.setText(
            "Erreur de géocodage"
        )

        QMessageBox.critical(
            self,
            "Erreur de géocodage",
            message,
        )

    def display_map(
        self,
        persons: list[dict],
    ) -> None:

        self.refresh_button.setEnabled(True)
        self.progress_bar.setVisible(False)

        self.status_label.setText(
            f"{len(persons)} PAX localisé(s)"
        )

        if not persons:
            QMessageBox.warning(
                self,
                "Localisation",
                "Aucune adresse n'a pu être localisée.",
            )

            self.web_view.setHtml(
                self.create_empty_page()
            )

            return

        page = self.create_leaflet_page(
            persons
        )

        self.web_view.setHtml(
            page,
            # Nécessaire pour autoriser le chargement
            # des ressources Leaflet et des tuiles OSM.
            # PyQt6 accepte une QUrl comme baseUrl.
        )

    def create_leaflet_page(
                self,
                persons: list[dict],
        ) -> str:
            persons_json = json.dumps(
                persons,
                ensure_ascii=False,
            )

            persons_json = persons_json.replace(
                "</",
                "<\\/",
            )

            return f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="width=device-width, initial-scale=1.0"
        >

        <link
            rel="stylesheet"
            href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
            crossorigin=""
        >

        <script
            src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
            crossorigin=""
        ></script>

        <style>
            html,
            body {{
                width: 100%;
                height: 100%;
                margin: 0;
                padding: 0;
                overflow: hidden;
                font-family: Arial, sans-serif;
            }}

            #map {{
                width: 100%;
                height: 100%;
            }}

            #map-status {{
                position: absolute;
                z-index: 1000;
                top: 10px;
                left: 50%;
                transform: translateX(-50%);

                padding: 8px 14px;

                background: rgba(255, 255, 255, 0.95);
                border: 1px solid #cccccc;
                border-radius: 6px;

                color: #202124;
                font-size: 13px;
            }}

            .pax-popup {{
                min-width: 230px;
                line-height: 1.5;
            }}

            .pax-name {{
                font-size: 15px;
                font-weight: bold;
                margin-bottom: 6px;
            }}

            .pax-address {{
                color: #555555;
                margin-top: 6px;
            }}

            .pax-id {{
                color: #777777;
                font-size: 11px;
                margin-top: 6px;
            }}
        </style>
    </head>

    <body>
        <div id="map-status">
            Chargement de la carte...
        </div>

        <div id="map"></div>

        <script>
            const persons = {persons_json};

            const map = L.map("map", {{
                zoomControl: true
            }}).setView(
                [46.603354, 1.888334],
                6
            );

            L.tileLayer(
                "https://tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png",
                {{
                    maxZoom: 19,
                    attribution:
                        '&copy; <a href="https://www.openstreetmap.org/copyright">'
                        + 'OpenStreetMap</a> contributors'
                }}
            ).addTo(map);

            const bounds = L.latLngBounds([]);

            persons.forEach(function (person) {{
                if (
                    person.latitude === null
                    || person.longitude === null
                    || person.latitude === undefined
                    || person.longitude === undefined
                ) {{
                    return;
                }}

                const latitude =
                    Number(person.latitude);

                const longitude =
                    Number(person.longitude);

                if (
                    Number.isNaN(latitude)
                    || Number.isNaN(longitude)
                ) {{
                    return;
                }}

                const marker = L.marker(
                    [latitude, longitude],
                    {{
                        title: person.name
                    }}
                ).addTo(map);

                const popup = document.createElement("div");
                popup.className = "pax-popup";

                const name = document.createElement("div");
                name.className = "pax-name";
                name.textContent = person.name;

                popup.appendChild(name);

                if (person.grade) {{
                    const grade = document.createElement("div");
                    grade.textContent =
                        "Grade : " + person.grade;

                    popup.appendChild(grade);
                }}

                if (person.unit) {{
                    const unit = document.createElement("div");
                    unit.textContent =
                        "Unité : " + person.unit;

                    popup.appendChild(unit);
                }}

                const address = document.createElement("div");
                address.className = "pax-address";
                address.textContent =
                    person.display_address
                    || person.address;

                popup.appendChild(address);

                if (person.id !== null) {{
                    const identifier =
                        document.createElement("div");

                    identifier.className = "pax-id";
                    identifier.textContent =
                        "Identifiant : " + person.id;

                    popup.appendChild(identifier);
                }}

                marker.bindPopup(popup);

                bounds.extend(
                    [latitude, longitude]
                );
            }});

            if (bounds.isValid()) {{
                map.fitBounds(
                    bounds,
                    {{
                        padding: [40, 40],
                        maxZoom: 16
                    }}
                );
            }}

            document.getElementById(
                "map-status"
            ).textContent =
                persons.length + " PAX localisé(s)";

            setTimeout(
                function () {{
                    document.getElementById(
                        "map-status"
                    ).style.display = "none";
                }},
                3000
            );
        </script>
    </body>
    </html>
    """

    @staticmethod
    def create_empty_page() -> str:
            return """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">

        <style>
            html,
            body {
                height: 100%;
                margin: 0;

                display: flex;
                align-items: center;
                justify-content: center;

                font-family: Arial, sans-serif;
                color: #555555;
                background-color: #f4f4f4;
            }
        </style>
    </head>

    <body>
        <div>
            Aucun PAX ne peut être affiché sur la carte.
        </div>
    </body>
    </html>
    """

    def refresh(self):
        pass
