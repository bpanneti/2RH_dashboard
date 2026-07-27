from typing import Any


STANDARD_FIELDS: list[dict[str, Any]] = [
    {
        "source_type": "standard",
        "field_id": "birth_date",
        "label": "Age",
        "data_type": "date",
        "database_field": "birth_date",
        "computed": True,
    },
    {
        "source_type": "standard",
        "field_id": "sex",
        "label": "Genre",
        "data_type": "choice",
        "database_field": "sex",
    },
    {
        "source_type": "standard",
        "field_id": "social_category",
        "label": "Catégorie",
        "data_type": "choice",
        "database_field": "social_category",
    }
]

NUMERIC_OPERATIONS = {
    "count": "Nombre de valeurs",
    "distinct_count": "Nombre de valeurs differentes",
    "mean": "Moyenne",
    "median": "Mediane",
    "std": "Ecart-type",
    "min": "Minimum",
    "max": "Maximum",
    "distribution": "Distribution",
}

CATEGORICAL_OPERATIONS = {
    "count": "Nombre de valeurs",
    "distinct_count": "Nombre de valeurs differentes",
    "proportion": "Proportions",
    "fonction": "Fonctions",
    "histogram": "Histogrammes"

}

DISPLAY_TYPES = {
    "number": "Nombre",
    "pie": "Camembert",
    "bar": "Diagramme en barres",
    "histogram": "Histogramme",
    "function": "Funtions"
}


def normalize_custom_type(field_type: str | None) -> str:
    normalized = (field_type or "text").strip().lower()

    if normalized in {"integer", "decimal", "float", "number"}:
        return "number"

    if normalized in {"choice", "csv_choice", "boolean"}:
        return "choice"

    if normalized == "date":
        return "date"

    return "text"


def allowed_operations(data_type: str) -> dict[str, str]:
    if data_type == "number":
        return NUMERIC_OPERATIONS
    return CATEGORICAL_OPERATIONS


def allowed_displays(operation: str) -> dict[str, str]:
    if operation in {
        "count",
        "distinct_count",
        "mean",
        "median",
        "std",
        "min",
        "max",
    }:
        return {"number": DISPLAY_TYPES["number"]}

    if operation == "proportion":
        return {
            "pie": DISPLAY_TYPES["pie"],
            "bar": DISPLAY_TYPES["bar"],
        }

    if operation == "distribution":
        return {"histogram": DISPLAY_TYPES["histogram"]}

    return {}
