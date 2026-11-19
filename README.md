# kzp-lab06-bychyk — звіт про спортивні тренування (Python)

Python-застосунок з курсу «Кросплатформні засоби програмування» (Національний університет
«Львівська політехніка», КІ-304, Бичик Вадім, **варіант 2 — «Спортивні тренування»**): читає CSV,
перетворює рядки на типізовані записи, будує детермінований текстовий звіт.

## Структура

```text
├── pyproject.toml                 # пакет, dev-залежності, CLI-скрипт, pytest, ruff
├── src/kzp_lab06/
│   ├── __init__.py                # версія й DataError
│   ├── errors.py                  # DataError(ValueError)
│   ├── loader.py                  # csv.DictReader → типізовані записи (Record)
│   ├── analysis.py                # відбір, множина, словник, середнє, найдовше, make_summary
│   ├── reporting.py               # format_report і write_report
│   └── cli.py                     # аргументи, коди завершення, межа помилок
├── tests/                         # pytest
├── data/input.csv                 # контрольні дані (7 записів)
├── reports/example-summary.txt    # еталонний звіт
├── .github/workflows/ci.yml       # pytest, ruff, wheel на Ubuntu, Windows, macOS
├── ai/                            # ролі агента ШІ
└── REPORT.md                      # звіт; усі звіти — docs/reports/
```

Модулі не залежать від зайвого: `loader` не друкує й не аналізує, `analysis` не відкриває файлів,
`reporting` не читає CSV, імпорт жодного модуля не запускає CLI.

## Формат CSV

UTF-8, перший рядок — заголовок, кома — роздільник. Стовпці й типи:

| Стовпець | Тип | Правило |
| --- | --- | --- |
| `date` | `date` | ISO `РРРР-ММ-ДД` |
| `kind` | `str` | непорожнє (може містити кому в лапках: `"Силове, зал"`) |
| `duration` | `int` | `>= 0`, хвилини |
| `distance` | `float` | скінченне, `>= 0`, км |
| `pulse` | `int` | `>= 0` |

```text
date,kind,duration,distance,pulse
2026-09-01,Біг,45,7.50,148
2026-09-04,"Силове, зал",60,0.00,118
```

Файл лише із заголовком — порожній набір (коректно); файл без заголовка — `DataError`.
Однакові рядки не видаляються. Вхідний файл не змінюється.

## Умова варіанта 2

- відбір: `duration >= 45` (поріг можна змінити `--min-duration`);
- словник: сумарна `distance` за `kind` (за відібраними записами, ключі за алфавітом);
- множина: унікальні `kind` (за всіма записами);
- звіт: середній пульс (усі записи) і найдовше тренування (за рівної тривалості — раніша дата).

## Запуск

```text
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate        # macOS, Ubuntu
python -m pip install -e ".[dev]"

python -m kzp_lab06.cli data/input.csv reports/summary.txt
kzp-lab06 data/input.csv reports/summary.txt          # після встановлення пакета
```

Коди завершення: `0` — успіх; `2` — очікувана помилка даних (повідомлення в stderr) або хибні
аргументи; `1` — неочікувана помилка.

## Приклад звіту

```text
Звіт про тренування
Записів у файлі: 7
Відібрано (тривалість >= 45 хв): 4
Види тренувань: Біг; Велосипед; Плавання; Силове, зал; Ходьба
Сума за відібраними: Тривалість, хв = 245.00; Дистанція, км = 44.00
Дистанція за видом (відібрані):
  Біг: 15.60 км
  Велосипед: 28.40 км
  Силове, зал: 0.00 км
Середній пульс: 133.86
Найдовше тренування: 2026-09-02, Велосипед, 90 хв, 28.40 км, пульс 132
```

## Перевірки

```text
python -m pytest                 # 57 тестів
ruff check .
ruff format --check .
python -m build                  # dist/kzp_lab06_bychyk-0.1.0-py3-none-any.whl

python -m venv .venv-wheel
.venv-wheel/bin/python -m pip install --no-deps dist/kzp_lab06_bychyk-0.1.0-py3-none-any.whl
.venv-wheel/bin/python -m kzp_lab06.cli data/input.csv reports/wheel-summary.txt
```

Windows: `.venv-wheel\Scripts\python` замість `.venv-wheel/bin/python`. `.venv`, `dist`, `build` та
кеші не додаються до репозиторію.
