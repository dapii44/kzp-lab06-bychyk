"""Предметна модель: базовий клас ``Training``, підтипи й незмінні підсумки (без файлів і CLI)."""

import datetime as dt
import math
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@runtime_checkable
class Workout(Protocol):
    """Протокол (качина типізація): усе, що потрібно аналізу від тренування.

    Функції ``analysis`` знають лише про цей протокол, а не про конкретні класи, тому новий
    підтип або сторонній клас із такими членами працює без змін аналізу.
    """

    @property
    def date(self) -> dt.date:
        """Дата тренування."""
        ...

    @property
    def kind(self) -> str:
        """Вид тренування."""
        ...

    @property
    def duration(self) -> int:
        """Тривалість, хв."""
        ...

    @property
    def distance(self) -> float:
        """Дистанція, км."""
        ...

    @property
    def pulse(self) -> int:
        """Пульс."""
        ...

    def load(self) -> float:
        """Повертає навантаження тренування."""
        ...


def _check_count(name: str, value: object) -> int:
    """Перевіряє невід'ємне ціле число (``bool`` не вважається числом)."""
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"поле {name} має бути цілим числом")
    if value < 0:
        raise ValueError(f"поле {name} не може бути від'ємним")
    return value


class Training(ABC):
    """Базове тренування: спільний стан, перевірки та контракт ``load()``.

    Стан перевіряють властивості: ``__init__`` призначає значення через setter-и, тому правило
    існує в одному місці. ``date`` доступна лише для читання. Об'єкт змінюваний (є setter-и), тому
    не хешується.
    """

    def __init__(self, date: dt.date, kind: str, duration: int, distance: float, pulse: int):
        """Створює тренування й перевіряє всі поля.

        Raises:
            TypeError: якщо тип значення хибний.
            ValueError: якщо значення від'ємне, нескінченне або текст порожній.
        """
        if isinstance(date, dt.datetime) or not isinstance(date, dt.date):
            raise TypeError("поле date має бути датою")
        self._date = date
        self.kind = kind
        self.duration = duration
        self.distance = distance
        self.pulse = pulse

    @property
    def date(self) -> dt.date:
        """Дата тренування (лише читання)."""
        return self._date

    @property
    def kind(self) -> str:
        """Вид тренування."""
        return self._kind

    @kind.setter
    def kind(self, value: str) -> None:
        """Встановлює непорожній вид; крайні пробіли відкидаються."""
        if not isinstance(value, str):
            raise TypeError("поле kind має бути текстом")
        text = value.strip()
        if not text:
            raise ValueError("поле kind порожнє")
        # Записуємо у внутрішнє поле, а не у властивість: інакше setter викликав би сам себе.
        self._kind = text

    @property
    def duration(self) -> int:
        """Тривалість, хв."""
        return self._duration

    @duration.setter
    def duration(self, value: int) -> None:
        """Встановлює невід'ємну тривалість (нуль допустимий)."""
        self._duration = _check_count("duration", value)

    @property
    def distance(self) -> float:
        """Дистанція, км."""
        return self._distance

    @distance.setter
    def distance(self, value: float) -> None:
        """Встановлює скінченну невід'ємну дистанцію (нуль допустимий)."""
        if isinstance(value, bool) or not isinstance(value, int | float):
            raise TypeError("поле distance має бути числом")
        number = float(value)
        if not math.isfinite(number):
            raise ValueError("поле distance має бути скінченним числом")
        if number < 0:
            raise ValueError("поле distance не може бути від'ємним")
        self._distance = number

    @property
    def pulse(self) -> int:
        """Пульс."""
        return self._pulse

    @pulse.setter
    def pulse(self, value: int) -> None:
        """Встановлює невід'ємний пульс (нуль допустимий)."""
        self._pulse = _check_count("pulse", value)

    @abstractmethod
    def load(self) -> float:
        """Повертає навантаження; формулу визначає підтип."""

    def _fields(self) -> tuple[object, ...]:
        """Повертає кортеж полів для порівняння й подання."""
        return (self._date, self._kind, self._duration, self._distance, self._pulse)

    def __str__(self) -> str:
        """Повертає короткий текст для читача."""
        return (
            f"{self._date.isoformat()}, {self._kind}: {self._duration} хв, "
            f"{self._distance:.2f} км, пульс {self._pulse}"
        )

    def __repr__(self) -> str:
        """Повертає діагностичне подання з назвою класу."""
        return (
            f"{type(self).__name__}(date={self._date!r}, kind={self._kind!r}, "
            f"duration={self._duration!r}, distance={self._distance!r}, pulse={self._pulse!r})"
        )

    def __eq__(self, other: object) -> bool:
        """Порівнює тренування за точним класом і всіма полями."""
        if not isinstance(other, Training):
            return NotImplemented
        return type(self) is type(other) and self._fields() == other._fields()

    # Змінюваний об'єкт з __eq__ не повинен хешуватися (інакше ключ у set/dict «загубиться»).
    __hash__ = None  # type: ignore[assignment]

    def __lt__(self, other: object) -> bool:
        """Упорядковує за датою, потім за видом (хронологічний порядок)."""
        if not isinstance(other, Training):
            return NotImplemented
        return (self._date, self._kind) < (other._date, other._kind)


class Running(Training):
    """Тренування, навантаження якого оцінюється за пульсом (біг та подібні види)."""

    def load(self) -> float:
        """Обчислює навантаження: ``тривалість × пульс / 100``."""
        return self.duration * self.pulse / 100


class Cycling(Training):
    """Тренування, навантаження якого оцінюється за дистанцією (велосипед)."""

    def load(self) -> float:
        """Обчислює навантаження: ``дистанція × 3 + тривалість / 10``."""
        return self.distance * 3 + self.duration / 10


@dataclass(frozen=True)
class KindLoad:
    """Навантаження за видом: кількість тренувань і сума ``load()``."""

    kind: str
    count: int
    total_load: float


@dataclass(frozen=True)
class ReportSummary:
    """Незмінний підсумок для звіту.

    Атрибути, що є колекціями, подано кортежами (незмінними), тому весь об'єкт не можна змінити.
    """

    total: int
    selected: int
    kinds: tuple[str, ...]
    selected_minutes: int
    selected_distance: float
    distance_by_kind: tuple[tuple[str, float], ...]
    average_pulse: float
    longest: Workout | None
    load_by_kind: tuple[KindLoad, ...]
