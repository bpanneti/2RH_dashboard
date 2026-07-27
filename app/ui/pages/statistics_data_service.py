from datetime import date, datetime
from typing import Any


class StatisticsDataService:
    def __init__(self, repository,ALLOWED_FIELDS) -> None:
        self.repository     = repository
        self.ALLOWED_FIELDS = ALLOWED_FIELDS
    def get_values(self, field_definition: dict[str, Any]) -> list[Any]:
        source_type = field_definition.get("source_type")

        if source_type == "standard":
            return self.get_standard_values(field_definition)

        if source_type == "custom":


            _data   = self.repository.get_custom_field_values(int(field_definition["field_id"]))

            _values = [row['value'] for row in _data]

            return _values;
        raise ValueError(f"Source de champ inconnue : {source_type}")

    def get_standard_values(self, field_definition: dict[str, Any]) -> list[Any]:


        if field_definition.get("field_id") == "birth_date":
            return [
                self.calculate_age(value['value'])
                for value in self.repository.get_standard_field_values(field_definition.get("field_id") ,self.ALLOWED_FIELDS)
            ]

        database_field = field_definition.get(
            "database_field", field_definition.get("field_id")
        )

        rows = self.repository.get_standard_field_values(str(database_field),self.ALLOWED_FIELDS)
        _values = [dict(row) for row in rows]

        _names = [row.get('value') for row in _values]


        return _names


    @staticmethod
    def parse_date(value: str) -> date | None:
        for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
            try:
                return datetime.strptime(value, date_format).date()
            except ValueError:
                continue
        return None

    @classmethod
    def calculate_age(cls, birth_date: Any) -> int | None:

        if not birth_date:
            return None

        if isinstance(birth_date, datetime):
            birth_date = birth_date.date()
        elif isinstance(birth_date, str):
            birth_date = cls.parse_date(birth_date.strip())

        if not isinstance(birth_date, date):
            return None

        today = date.today()
        age = today.year - birth_date.year

        if (today.month, today.day) < (birth_date.month, birth_date.day):
            age -= 1

        return age
