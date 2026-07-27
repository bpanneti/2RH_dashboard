from typing import Any


class StatisticsRepository:
    """Requetes SQLite necessaires aux statistiques.

    La connexion doit utiliser sqlite3.Row comme row_factory.
    Adaptez PERSON_TABLE et les noms des colonnes si necessaire.
    """

    PERSON_TABLE = "persons"

    ALLOWED_STANDARD_FIELDS =     {
    "grade",
    "sex",
    "incorporation_dans_l_esacdron",
    "dipl_mes",
    "social_category",
    "birth_date",
    }

    def __init__(self, connection) -> None:
        self.connection = connection


    def get_person_fields(self) -> list[Any]:
        cursor = self.connection.execute(
            f"SELECT *   FROM  {self.PERSON_TABLE}   "
        )
        return [dict(row) for row in cursor.fetchall()]


    def get_standard_field_values(self, database_field: str) -> list[Any]:
        if database_field not in self.ALLOWED_STANDARD_FIELDS:
            raise ValueError(f"Champ standard non autorise : {database_field}")

        cursor = self.connection.execute(
            f"SELECT {database_field} AS value FROM {self.PERSON_TABLE}"
        )
        return [dict(row).get("value") for row in cursor.fetchall()]

    def get_person_birth_dates(self) -> list[Any]:
        cursor = self.connection.execute(
            f"""
            SELECT birth_date AS value
            FROM {self.PERSON_TABLE}
            WHERE birth_date IS NOT NULL
              AND TRIM(birth_date) <> ''
            """
        )
        return [dict(row).get("value") for row in cursor.fetchall()]

    def get_custom_fields_for_statistics(self) -> list[dict[str, Any]]:
        cursor = self.connection.execute(
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
        return [dict(row) for row in cursor.fetchall()]

    def get_custom_field_values(self, custom_field_id: int) -> list[Any]:
        cursor = self.connection.execute(
            """
            SELECT value
            FROM custom_table_value
            WHERE field_id = ?
            """,
            (custom_field_id,),
        )
        return [dict(row).get("value") for row in cursor.fetchall()]
