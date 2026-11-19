"""Об'єктна модель звіту про спортивні тренування (КЗП, лабораторна робота № 7)."""

from .errors import DataError
from .models import Cycling, KindLoad, ReportSummary, Running, Training, Workout

__version__ = "0.2.0"

__all__ = [
    "Cycling",
    "DataError",
    "KindLoad",
    "ReportSummary",
    "Running",
    "Training",
    "Workout",
    "__version__",
]
