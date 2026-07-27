import math
from collections import Counter
from statistics import mean, median, pstdev
from typing import Any


class StatisticsCalculator:
    @staticmethod
    def clean_values(values: list[Any]) -> list[Any]:
        return [
            value
            for value in values
            if value is not None and str(value).strip() != ""
        ]

    @staticmethod
    def numeric_values(values: list[Any]) -> list[float]:
        result: list[float] = []

        for value in values:
            if value is None:
                continue

            try:
                number = float(str(value).strip().replace(",", "."))
            except (TypeError, ValueError):
                continue

            if math.isfinite(number):
                result.append(number)

        return result

    @classmethod
    def calculate(cls, values: list[Any], operation: str) -> Any:
        if operation == "count":
            return len(cls.clean_values(values))

        if operation == "distinct_count":
            cleaned = cls.clean_values(values)
            return len({str(value).strip() for value in cleaned})

        if operation == "proportion":
            return cls.proportions(values)

        numeric = cls.numeric_values(values)

        if operation == "distribution":
            return numeric

        if not numeric:
            return None

        if operation == "mean":
            return mean(numeric)

        if operation == "median":
            return median(numeric)

        if operation == "std":
            return pstdev(numeric) if len(numeric) >= 2 else 0.0

        if operation == "min":
            return min(numeric)

        if operation == "max":
            return max(numeric)

        raise ValueError(f"Operation statistique inconnue : {operation}")

    @classmethod
    def proportions(cls, values: list[Any]) -> list[dict[str, Any]]:
        cleaned = [str(value).strip() for value in cls.clean_values(values)]
        total = len(cleaned)

        if total == 0:
            return []

        counts = Counter(cleaned)

        return [
            {
                "label": label,
                "count": count,
                "percentage": count * 100.0 / total,
            }
            for label, count in counts.most_common()
        ]
