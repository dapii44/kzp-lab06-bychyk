"""Формування тексту звіту й запис його у файл (без читання CSV й без обчислень)."""

from pathlib import Path

from .errors import DataError
from .models import ReportSummary


def format_report(summary: ReportSummary, min_duration: int, with_load: bool = False) -> str:
    """Формує детермінований текстовий звіт із підсумку.

    Базовий текст збігається з лабораторною № 6 (той самий формат). Блок навантаження додається
    лише за ``with_load=True``.
    """
    lines = [
        "Звіт про тренування",
        f"Записів у файлі: {summary.total}",
        f"Відібрано (тривалість >= {min_duration} хв): {summary.selected}",
        "Види тренувань: " + ("; ".join(summary.kinds) or "немає"),
        f"Сума за відібраними: Тривалість, хв = {float(summary.selected_minutes):.2f}; "
        f"Дистанція, км = {summary.selected_distance:.2f}",
        "Дистанція за видом (відібрані):",
    ]
    lines += [f"  {kind}: {distance:.2f} км" for kind, distance in summary.distance_by_kind]
    if not summary.distance_by_kind:
        lines.append("  немає записів")
    lines.append(f"Середній пульс: {summary.average_pulse:.2f}")
    longest = summary.longest
    if longest is None:
        lines.append("Найдовше тренування: немає даних")
    else:
        lines.append(
            f"Найдовше тренування: {longest.date.isoformat()}, {longest.kind}, "
            f"{longest.duration} хв, {longest.distance:.2f} км, пульс {longest.pulse}"
        )
    if with_load:
        lines.append("Навантаження за видом (load):")
        lines += [
            f"  {item.kind}: {item.total_load:.2f} ({item.count} трен.)"
            for item in summary.load_by_kind
        ]
        if not summary.load_by_kind:
            lines.append("  немає записів")
    return "\n".join(lines) + "\n"


def write_report(path: Path, text: str) -> None:
    """Записує звіт у файл UTF-8 (``\\n`` на всіх ОС), створюючи каталог за потреби.

    Raises:
        DataError: якщо файл неможливо записати.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        # with гарантує закриття файла навіть у разі помилки запису.
        with path.open("w", encoding="utf-8", newline="\n") as target:
            target.write(text)
    except OSError as error:
        raise DataError(f"Не вдалося записати звіт: {path}") from error
