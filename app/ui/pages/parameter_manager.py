import json
from pathlib import Path
from typing import Any


class ParameterManager:
    """Lecture et écriture de la configuration du dashboard."""

    def __init__(self, filename: str = "parameters.txt") -> None:
        self.filepath = Path(filename)

    @staticmethod
    def default_parameters() -> dict[str, Any]:
        return {"dashboard_statistics": []}

    def load(self) -> dict[str, Any]:
        if not self.filepath.exists():
            return self.default_parameters()

        try:
            with self.filepath.open("r", encoding="utf-8") as file:
                data = json.load(file)
        except (OSError, json.JSONDecodeError):
            return self.default_parameters()

        if not isinstance(data, dict):
            return self.default_parameters()

        if not isinstance(data.get("dashboard_statistics"), list):
            data["dashboard_statistics"] = []

        return data

    def save(self, parameters: dict[str, Any]) -> None:
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        temporary_file = self.filepath.with_suffix(self.filepath.suffix + ".tmp")

        with temporary_file.open("w", encoding="utf-8") as file:
            json.dump(parameters, file, ensure_ascii=False, indent=4)

        temporary_file.replace(self.filepath)

    def get_statistics(self) -> list[dict[str, Any]]:
        return list(self.load().get("dashboard_statistics", []))

    def save_statistics(self, statistics: list[dict[str, Any]]) -> None:
        parameters = self.load()
        parameters["dashboard_statistics"] = statistics
        self.save(parameters)
