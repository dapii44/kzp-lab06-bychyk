"""Обчислення над тренуваннями через протокол ``Workout`` (без файлів і без перевірки підтипів)."""

from collections.abc import Sequence
from typing import TypeVar

from .models import KindLoad, ReportSummary, Workout

#: Тип елемента: будь-який об'єкт, що відповідає протоколу ``Workout``.
W = TypeVar("W", bound=Workout)

#: Поріг відбору за умовою варіанта: тренування не коротші за 45 хв.
MIN_DURATION = 45


def select_long(workouts: Sequence[W], min_duration: int = MIN_DURATION) -> list[W]:
    """Відбирає тренування з ``duration >= min_duration`` у початковому порядку."""
    return [workout for workout in workouts if workout.duration >= min_duration]


def unique_kinds(workouts: Sequence[Workout]) -> set[str]:
    """Повертає множину унікальних видів (порядку не гарантує)."""
    return {workout.kind for workout in workouts}


def distance_by_kind(workouts: Sequence[Workout]) -> dict[str, float]:
    """Обчислює сумарну дистанцію за видом; ключі впорядковано за алфавітом."""
    return {
        kind: sum(workout.distance for workout in workouts if workout.kind == kind)
        for kind in sorted(unique_kinds(workouts))
    }


def average_pulse(workouts: Sequence[Workout]) -> float:
    """Повертає середній пульс; для порожнього списку — 0.0."""
    if not workouts:
        return 0.0
    return sum(workout.pulse for workout in workouts) / len(workouts)


def longest_workout(workouts: Sequence[W]) -> W | None:
    """Повертає найдовше тренування або ``None``; за рівної тривалості — раніша дата."""
    if not workouts:
        return None
    return max(workouts, key=lambda workout: (workout.duration, -workout.date.toordinal()))


def load_by_kind(workouts: Sequence[Workout]) -> tuple[KindLoad, ...]:
    """Рахує навантаження за видом через поліморфний ``load()`` (види за алфавітом).

    Формулу навантаження знає кожен підтип; тут вона лише викликається, тому нові підтипи не
    потребують змін.
    """
    return tuple(
        KindLoad(
            kind=kind,
            count=sum(1 for workout in workouts if workout.kind == kind),
            total_load=sum(workout.load() for workout in workouts if workout.kind == kind),
        )
        for kind in sorted(unique_kinds(workouts))
    )


def summarize(workouts: Sequence[Workout], min_duration: int = MIN_DURATION) -> ReportSummary:
    """Будує незмінний підсумок для звіту; вхідний список не змінюється."""
    selected = select_long(workouts, min_duration)
    return ReportSummary(
        total=len(workouts),
        selected=len(selected),
        kinds=tuple(sorted(unique_kinds(workouts))),
        selected_minutes=sum(workout.duration for workout in selected),
        selected_distance=float(sum(workout.distance for workout in selected)),
        distance_by_kind=tuple(distance_by_kind(selected).items()),
        average_pulse=average_pulse(workouts),
        longest=longest_workout(workouts),
        load_by_kind=load_by_kind(workouts),
    )
