from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

import sqlite3


def initialize_database(db: sqlite3.Connection) -> None:
    db.execute("PRAGMA foreign_keys = ON")

    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS custom_field_category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            display_order INTEGER NOT NULL DEFAULT 0,
            enabled INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS custom_field_definition (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            field_type TEXT NOT NULL DEFAULT 'text',
            configuration TEXT,
            required INTEGER NOT NULL DEFAULT 0,
            display_order INTEGER NOT NULL DEFAULT 0,
            enabled INTEGER NOT NULL DEFAULT 1,

            FOREIGN KEY (category_id)
                REFERENCES custom_field_category(id)
                ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS custom_field_value (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            field_id INTEGER NOT NULL,
            value TEXT,

            FOREIGN KEY (person_id)
                REFERENCES person(id)
                ON DELETE CASCADE,

            FOREIGN KEY (field_id)
                REFERENCES custom_field_definition(id)
                ON DELETE CASCADE,

            UNIQUE(person_id, field_id)
        );
        """
    )

    db.commit()
class Database:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.connection()


    def connection(self):


        self._connection = sqlite3.connect(str(self.path))
        self._connection.row_factory = sqlite3.Row
        self.initialize()
        self.create_custom_table_schema()
        initialize_database(self._connection)

        #self.register_initial_custom_fields()
        self._connection.execute("PRAGMA foreign_keys = ON")
        '''
        try:
            yield self._connection
            self._connection.commit()
        except Exception:
            self._connection.rollback()
            raise
        finally:
            self._connection.close()
        '''

    def get_custom_table_fields(self, table_id: int):
        """
        Retourne tous les champs définis pour une table personnalisée.
        """

        return self.fetch_all(
            """
            SELECT
                id,
                table_id,
                name,
                label,
                field_type,
                required,
                display_order,
                enabled,
                configuration,
                csv_path,
                csv_column,
                csv_label_column,
                csv_separator,
                manual_choices
            FROM custom_table_field
            WHERE table_id = ?
            ORDER BY display_order, label
            """,
            (table_id,),
        )

    def register_initial_custom_fields(self) -> None:
        employment = self.fetch_one(
            """
            SELECT id
            FROM custom_table_definition
            WHERE name = ?
            """,
            ("employment",),
        )

        if employment is None:
            return

        table_id = employment["id"]

        fields = [
            {
                "name": "company",
                "label": "Entreprise",
                "field_type": "text",
                "display_order": 10,
            },
            {
                "name": "position",
                "label": "Poste",
                "field_type": "text",
                "display_order": 20,
            },
            {
                "name": "start_date",
                "label": "Date de début",
                "field_type": "date",
                "display_order": 30,
            },
            {
                "name": "end_date",
                "label": "Date de fin",
                "field_type": "date",
                "display_order": 40,
            },
        ]

        for field in fields:
            existing = self.fetch_one(
                """
                SELECT id
                FROM custom_table_field
                WHERE table_id = ?
                  AND name = ?
                """,
                (
                    table_id,
                    field["name"],
                ),
            )

            if existing is not None:
                continue

            self.execute(
                """
                INSERT INTO custom_table_field (
                    table_id,
                    name,
                    label,
                    field_type,
                    required,
                    display_order,
                    enabled
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    table_id,
                    field["name"],
                    field["label"],
                    field["field_type"],
                    0,
                    field["display_order"],
                    1,
                ),
            )


    def register_initial_custom_tables(self) -> None:
        """
        Enregistre les tables initiales dans la configuration
        sans créer de doublons.
        """

        initial_tables = [
            {
                "name": "employment",
                "label": "Emplois",
                "description": "Historique des emplois de la personne",
                "display_order": 10,
                "allow_multiple": 1,
                "enabled": 1,
            },
            {
                "name": "formation",
                "label": "Formations",
                "description": "Formations suivies par la personne",
                "display_order": 20,
                "allow_multiple": 1,
                "enabled": 1,
            },
            {
                "name": "sport",
                "label": "Sports",
                "description": "Activités sportives de la personne",
                "display_order": 30,
                "allow_multiple": 1,
                "enabled": 1,
            },
        ]

        for table in initial_tables:
            existing = self.fetch_one(
                """
                SELECT id
                FROM custom_table_definition
                WHERE name = ?
                """,
                (table["name"],),
            )

            if existing is not None:
                continue

            self.execute(
                """
                INSERT INTO custom_table_definition (
                    name,
                    label,
                    description,
                    display_order,
                    allow_multiple,
                    enabled
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    table["name"],
                    table["label"],
                    table["description"],
                    table["display_order"],
                    table["allow_multiple"],
                    table["enabled"],
                ),
            )


    def get_custom_tables(self):
        """
        Retourne la liste de toutes les tables configurées.
        """

        return self.fetch_all(
            """
            SELECT
                id,
                name,
                label,
                description,
                display_order,
                enabled,
                allow_multiple
            FROM custom_table_definition
            ORDER BY display_order, label
            """
        )
    def get_custom_table(self, table_id: int):
        return self.fetch_one(
            """
            SELECT
                id,
                name,
                label,
                description,
                display_order,
                enabled,
                allow_multiple
            FROM custom_table_definition
            WHERE id = ?
            """,
            (table_id,),
        )

    def update_custom_table(
            self,
            table_id: int,
            values: dict,
    ) -> None:
        self.execute(
            """
            UPDATE custom_table_definition
            SET
                name = ?,
                label = ?,
                description = ?,
                display_order = ?,
                enabled = ?,
                allow_multiple = ?
            WHERE id = ?
            """,
            (
                values["name"],
                values["label"],
                values.get("description", ""),
                int(values.get("display_order", 0)),
                int(values.get("enabled", True)),
                int(values.get("allow_multiple", True)),
                table_id,
            ),
        )


    def get_enabled_custom_tables(self):
        return self.fetch_all(
            """
            SELECT
                id,
                name,
                label,
                description,
                display_order,
                allow_multiple
            FROM custom_table_definition
            WHERE enabled = 1
            ORDER BY display_order, label
            """
        )

    def delete_custom_record(
            self,
            record_id: int,
            person_id: int,
            table_id: int,
    ) -> None:

           self.execute(
                """
                DELETE FROM custom_table_record
                WHERE id = ?
                  AND person_id = ?
                  AND table_id = ?
                """,
                (
                    record_id,
                    person_id,
                    table_id,
                ),
            )


    def get_custom_table_field(self, field_id: int):
        return self.fetch_one(
            """
            SELECT
                id,
                table_id,
                name,
                label,
                field_type,
                required,
                display_order,
                enabled,
                manual_choices,
                csv_path,
                csv_column,
                csv_label_column,
                csv_separator
            FROM custom_table_field
            WHERE id = ?
            """,
            (field_id,),
        )

    def update_custom_table_field(
            self,
            field_id: int,
            values: dict,
    ) -> None:
        self.execute(
            """
            UPDATE custom_table_field
            SET
                table_id = ?,
                name = ?,
                label = ?,
                field_type = ?,
                required = ?,
                display_order = ?,
                enabled = ?,
                manual_choices = ?,
                csv_path = ?,
                csv_column = ?,
                csv_label_column = ?,
                csv_separator = ?
            WHERE id = ?
            """,
            (
                values["table_id"],
                values["name"],
                values["label"],
                values["field_type"],
                int(values.get("required", False)),
                int(values.get("display_order", 0)),
                int(values.get("enabled", True)),
                values.get("manual_choices"),
                values.get("csv_path"),
                values.get("csv_column"),
                values.get("csv_label_column"),
                values.get("csv_separator", ","),
                field_id,
            ),
        )

        self.commit()
    def add_custom_table(self, values: dict) -> int:
        existing = self.fetch_one(
            """
            SELECT id
            FROM custom_table_definition
            WHERE name = ?
            """,
            (values["name"],),
        )

        if existing is not None:
            raise ValueError(
                f"La table '{values['name']}' existe déjà."
            )

        return self.execute(
            """
            INSERT INTO custom_table_definition (
                name,
                label,
                description,
                display_order,
                enabled,
                allow_multiple
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                values["name"],
                values["label"],
                values.get("description", ""),
                int(values.get("display_order", 0)),
                int(values.get("enabled", True)),
                int(values.get("allow_multiple", True)),
            ),
        )

    def add_custom_table_field(self, values: dict) -> int:

        print('in add_custom_table_field')
        print(values)
        return self.execute(
            """
            INSERT INTO custom_table_field (
                table_id,
                name,
                label,
                field_type,
                required,
                display_order,
                configuration,
                csv_path,
                csv_column,
                csv_label_column,
                csv_separator,
                enabled,
                manual_choices
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,?,?)
            """,
            (
                values["table_id"],
                values["name"],
                values["label"],
                values["field_type"],
                int(values.get("required", False)),
                values.get("display_order", 0),
                values.get("configuration"),
                values.get("csv_path"),
                values.get("csv_column"),
                values.get("csv_label_column"),
                values.get("csv_separator"),
                int(values.get("enabled", True)),
                values.get("manual_choices"),
            ),
        )
    def create_custom_table_schema(self) -> None:
        self._connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS custom_table_definition (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                label TEXT NOT NULL,
                description TEXT,
                display_order INTEGER NOT NULL DEFAULT 0,
                enabled INTEGER NOT NULL DEFAULT 1,
                allow_multiple INTEGER NOT NULL DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS custom_table_field (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                label TEXT NOT NULL,
                field_type TEXT NOT NULL,
                required INTEGER NOT NULL DEFAULT 0,
                display_order INTEGER NOT NULL DEFAULT 0,
                configuration TEXT,
                csv_path TEXT,
                csv_column TEXT,
                csv_label_column TEXT,
                csv_separator TEXT,
                manual_choices TEXT,
                enabled INTEGER NOT NULL DEFAULT 1,

                FOREIGN KEY (table_id)
                    REFERENCES custom_table_definition(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS custom_table_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_id INTEGER NOT NULL,
                person_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (table_id)
                    REFERENCES custom_table_definition(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (person_id)
                    REFERENCES persons(id)
                    ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS custom_table_value (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_id INTEGER NOT NULL,
                field_id INTEGER NOT NULL,
                value TEXT,

                FOREIGN KEY (record_id)
                    REFERENCES custom_table_record(id)
                    ON DELETE CASCADE,

                FOREIGN KEY (field_id)
                    REFERENCES custom_table_field(id)
                    ON DELETE CASCADE,

                UNIQUE(record_id, field_id)
            );
            """
        )

        self._connection.commit()
    def initialize(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricule INTEGER NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            birth_date TEXT,
            sex TEXT,
            nationality TEXT,
            social_category TEXT,
            profession TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            postal_code TEXT,
            notes TEXT,
            photo_path TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_person_name ON persons(last_name, first_name);
        """
        '''
        CREATE TABLE IF NOT EXISTS employments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            employer TEXT NOT NULL,
            job_title TEXT NOT NULL,
            contract_type TEXT,
            start_date TEXT,
            end_date TEXT,
            salary REAL,
            FOREIGN KEY(person_id) REFERENCES persons(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS educations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            school TEXT NOT NULL,
            diploma TEXT,
            specialty TEXT,
            start_year INTEGER,
            end_year INTEGER,
            result TEXT,
            FOREIGN KEY(person_id) REFERENCES persons(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS sport_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            sport TEXT NOT NULL,
            event_name TEXT,
            event_date TEXT,
            category TEXT,
            score TEXT,
            ranking INTEGER,
            location TEXT,
            FOREIGN KEY(person_id) REFERENCES persons(id) ON DELETE CASCADE
        );
        
        CREATE TABLE IF NOT EXISTS custom_fields (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            field_type TEXT NOT NULL,
            choices TEXT,
            required INTEGER NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS custom_values (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id INTEGER NOT NULL,
            field_id INTEGER NOT NULL,
            value TEXT,
            UNIQUE(person_id, field_id),
            FOREIGN KEY(person_id) REFERENCES persons(id) ON DELETE CASCADE,
            FOREIGN KEY(field_id) REFERENCES custom_fields(id) ON DELETE CASCADE
        );

        
        CREATE INDEX IF NOT EXISTS idx_person_profession ON persons(profession);
        CREATE INDEX IF NOT EXISTS idx_person_city ON persons(city);
        '''
        with self._connection as conn:
            conn.executescript(schema)

    def execute(self, sql: str, params: Iterable[Any] = ()) -> int:

       with self._connection as conn:
            cur = conn.execute(sql, params)
            conn.commit()
            return int(cur.lastrowid or 0)

    def query(self, sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
        with self._connection  as conn:
            return [dict(row) for row in conn.execute(sql, tuple(params)).fetchall()]

    def one(self, sql: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
        rows = self.query(sql, params)
        return rows[0] if rows else None

    def save_person(self, data: dict[str, Any], person_id: int | None = None) -> int:
        '''
        columns = [
            "first_name", "last_name", "birth_date", "sex", "nationality",
            "social_category", "profession", "email", "phone", "address",
            "city", "postal_code", "notes", "photo_path"
        ]
        values = [data.get(c) or None for c in columns]
        if person_id:
            assignments = ", ".join(f"{c} = ?" for c in columns)
            self.execute(
                f"UPDATE persons SET {assignments}, updated_at=CURRENT_TIMESTAMP WHERE id=?",
                values + [person_id],
            )
            return person_id
        marks = ",".join("?" for _ in columns)
        return self.execute(
            f"INSERT INTO persons ({','.join(columns)}) VALUES ({marks})", values
        )
        '''


        cursor = self.execute(
            """
            INSERT INTO persons (
                matricule,
                first_name,
                last_name,
                birth_date,
                sex,
                nationality,
                social_category,
                profession,
                email,
                phone,
                address,
                city,
                postal_code,
                notes,
                photo_path
            )
            VALUES (?,?, ?, ?, ?, ?, ?, ?,?, ?, ?, ?, ?, ?, ?)
            """,
            (
                data.get("matricule"),
                data.get("first_name"),
                data.get("last_name"),
                data.get("birth_date"),
                data.get("sex"),
                data.get("nationality"),
                data.get("social_category"),
                data.get("profession"),
                data.get("email"),
                data.get("phone"),
                data.get("address"),
                data.get("city"),
                data.get("postal_code"),
                data.get("notes"),
                data.get("photo_path"),
            ),
        )


        return cursor

    def delete_person(self, person_id: int) -> None:
        self.execute("DELETE FROM persons WHERE id=?", (person_id,))

    def search_persons(self, text: str = "") -> list[dict[str, Any]]:
        pattern = f"%{text.strip()}%"
        return self.query(
            """
            SELECT id, last_name, first_name, matricule, birth_date, sex, profession,
                   social_category, city, photo_path
            FROM persons
            WHERE ? = '%%' OR last_name LIKE ? OR first_name LIKE ?
                  OR profession LIKE ? OR social_category LIKE ? OR city LIKE ?
            ORDER BY last_name COLLATE NOCASE, first_name COLLATE NOCASE
            """,
            (pattern, pattern, pattern, pattern, pattern, pattern),
        )

    def person(self, person_id: int) -> dict[str, Any] | None:
        return self.one("SELECT * FROM persons WHERE id=?", (person_id,))

    def related(self, table: str, person_id: int) -> list[dict[str, Any]]:
        allowed = {"employments", "educations", "sport_results"}
        if table not in allowed:
            raise ValueError("Table non autorisée")
        return self.query(f"SELECT * FROM {table} WHERE person_id=? ORDER BY id DESC", (person_id,))

    def add_related(self, table: str, person_id: int, data: dict[str, Any]) -> int:
        allowed = {
            "employments": ["employer", "job_title", "contract_type", "start_date", "end_date", "salary"],
            "educations": ["school", "diploma", "specialty", "start_year", "end_year", "result"],
            "sport_results": ["sport", "event_name", "event_date", "category", "score", "ranking", "location"],
        }
        columns = allowed.get(table)
        if not columns:
            raise ValueError("Table non autorisée")
        vals = [data.get(c) or None for c in columns]
        marks = ",".join("?" for _ in range(len(columns) + 1))
        return self.execute(
            f"INSERT INTO {table} (person_id,{','.join(columns)}) VALUES ({marks})",
            [person_id] + vals,
        )

    def delete_related(self, table: str, row_id: int) -> None:
        if table not in {"employments", "educations", "sport_results"}:
            raise ValueError("Table non autorisée")
        self.execute(f"DELETE FROM {table} WHERE id=?", (row_id,))

    def dashboard_stats(self) -> dict[str, Any]:
        stats: dict[str, Any] = {}
        stats["total"] = self.one("SELECT COUNT(*) n FROM persons")["n"]

        #stats["employed"] = self.one("SELECT COUNT(DISTINCT person_id) n FROM employments")["n"]
        #stats["students"] = self.one("SELECT COUNT(DISTINCT person_id) n FROM educations")["n"]
        #stats["athletes"] = self.one("SELECT COUNT(DISTINCT person_id) n FROM sport_results")["n"]
        stats["sex"] = self.query("SELECT COALESCE(NULLIF(sex,''),'Non renseigné') label, COUNT(*) value FROM persons GROUP BY label ORDER BY value DESC")
        stats["profession"] = self.query("SELECT COALESCE(NULLIF(profession,''),'Non renseigné') label, COUNT(*) value FROM persons GROUP BY label ORDER BY value DESC LIMIT 8")
        stats["city"] = self.query("SELECT COALESCE(NULLIF(city,''),'Non renseignée') label, COUNT(*) value FROM persons GROUP BY label ORDER BY value DESC LIMIT 8")
        stats["ages"] = self.query("""
            SELECT CASE
                WHEN birth_date IS NULL OR birth_date='' THEN 'Inconnu'
                WHEN CAST(strftime('%Y','now') AS INTEGER)-CAST(substr(birth_date,1,4) AS INTEGER) < 18 THEN '< 18'
                WHEN CAST(strftime('%Y','now') AS INTEGER)-CAST(substr(birth_date,1,4) AS INTEGER) < 30 THEN '18-29'
                WHEN CAST(strftime('%Y','now') AS INTEGER)-CAST(substr(birth_date,1,4) AS INTEGER) < 45 THEN '30-44'
                WHEN CAST(strftime('%Y','now') AS INTEGER)-CAST(substr(birth_date,1,4) AS INTEGER) < 60 THEN '45-59'
                ELSE '60+'
            END label, COUNT(*) value FROM persons GROUP BY label
        """)
        return stats

    def custom_fields(self) -> list[dict[str, Any]]:
        return self.query("SELECT * FROM custom_fields ORDER BY name")

    def add_custom_field(self, name: str, field_type: str, choices: str = "", required: bool = False) -> int:
        return self.execute(
            "INSERT INTO custom_fields(name,field_type,choices,required) VALUES (?,?,?,?)",
            (name, field_type, choices, int(required)),
        )

    def delete_custom_field(self, field_id: int) -> None:

        self.execute("DELETE FROM custom_table_field WHERE id=?", (field_id,))

    def fetch_all(
        self,
        query: str,
        parameters: tuple = (),
    ) -> list[sqlite3.Row]:

        self.connection()

        cursor = self._connection.execute(query, parameters)
        return cursor.fetchall()

    def fetch_one(
        self,
        query: str,
        parameters: tuple = (),
    ) -> sqlite3.Row | None:


        cursor = self._connection.execute(query, parameters)
        return cursor.fetchone()

    def commit(self) -> None:

        self.connection()
        self._connection.commit()

    def rollback(self) -> None:

        self.connection()
        self._connection.rollback()

    def close(self) -> None:
        self._connection.close()

    def create_custom_record(
            self,
            person_id: int,
            table_id: int,
    ) -> int:

        cursor = self.execute(
            """
            INSERT INTO custom_table_record (
                person_id,
                table_id,
                created_at,
                updated_at
            )
            VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            """,
            (
                person_id,
                table_id,
            ),
        )

        return int(cursor)

    def save_custom_record_value(
            self,
            record_id: int,
            field_id: int,
            value,
    ) -> None:

        if isinstance(value, bool):
            stored_value = "1" if value else "0"
        elif value is None:
            stored_value = None
        else:
            stored_value = str(value)

        self.execute(
            """
            INSERT INTO custom_table_value (
                record_id,
                field_id,
                value
            )
            VALUES (?, ?, ?)
            ON CONFLICT(record_id, field_id)
            DO UPDATE SET
                value = excluded.value
            """,
            (
                record_id,
                field_id,
                stored_value,
            ),
        )

    def save_custom_record(
            self,
            person_id: int,
            table_id: int,
            values: dict[int, object],
            record_id: int | None = None,
    ) -> int:

        try:
            if record_id is None:
                record_id = self.create_custom_record(
                    person_id,
                    table_id,
                )
            else:
                self.execute(
                    """
                    UPDATE custom_table_record
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                      AND person_id = ?
                      AND table_id = ?
                    """,
                    (
                        record_id,
                        person_id,
                        table_id,
                    ),
                )

            for field_id, value in values.items():
                self.save_custom_record_value(
                    record_id,
                    field_id,
                    value,
                )

            #self.connection.commit()

            return record_id

        except Exception:
            self.rollback()
            raise
    def get_custom_field_values(
            self,
            field_id: int,
    ):
        return self.fetch_all(
            """
            SELECT
                record_id,
                value
            FROM custom_table_value
            WHERE field_id = ?
            """,
            (
                field_id,
            ),
        )
    def get_custom_record_values(
            self,
            record_id: int,
    ):
        return self.fetch_all(
            """
            SELECT
                field_id,
                value
            FROM custom_table_value
            WHERE record_id = ?
            """,
            (
                record_id,
            ),
        )

    def get_custom_fields_for_statistics(self) -> list[dict[str, Any]]:
        cursor = self.fetch_all(
            """
            SELECT
                f.id AS field_id,
                f.table_id AS table_id,
                f.name AS field_name,
                f.field_type AS field_type,
                t.name AS table_name
            FROM custom_table_field AS f
            INNER JOIN custom_table_definition AS t
                ON t.id = f.table_id
            ORDER BY
                t.name,
                f.id
            """
        )
        return cursor

    def get_custom_records(
            self,
            person_id: int,
            table_id: int,
    ):
        return self.fetch_all(
            """
            SELECT
                id,
                person_id,
                table_id,
                created_at,
                updated_at
            FROM custom_table_record
            WHERE person_id = ?
              AND table_id = ?
            ORDER BY id
            """,
            (
                person_id,
                table_id,
            ),
        )

    #==================================================================
    # Pour la carto
    #==================================================================


    def get_persons_for_map(self) -> list:
        return self.fetch_all(
            """
            SELECT
                id,
                first_name,
                last_name,
                address,
                postal_code,
                city
            FROM persons
            WHERE
                address IS NOT NULL
                AND TRIM(address) <> ''
            ORDER BY
                last_name,
                first_name
            """
        )

    def get_standard_field_values(self, database_field: str,ALLOWED_STANDARD_FIELDS:dict) -> list[Any]:
        if database_field not in ALLOWED_STANDARD_FIELDS:
            raise ValueError(f"Champ standard non autorise : {database_field}")

        cursor = self.fetch_all(
            f"SELECT {database_field} AS value FROM persons"
        )


        return cursor