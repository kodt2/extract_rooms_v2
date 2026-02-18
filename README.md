# extract_rooms_v2

Сервис для подбора свободных аудиторий по расписанию RUZ и генерации печатного отчёта (второй режим).

## Что делает
- Загружает расписание по `BASE_URL = https://portal.unn.ru/ruzapi/schedule/building/{building_oid}`.
- Отфильтровывает только разрешённые аудитории (из конфига).
- Загружает данные в диапазоне: от (сегодня - N дней) до (сегодня + M месяцев), значения берутся из конфига.
- Обрабатывает партию запросов и не допускает пересечения по одной аудитории внутри этой партии.
- Для отсутствующего дня возвращает `no day in shulde`.
- При отсутствии свободной аудитории возвращает `no free room`.
- Поддерживает второй режим: формирование текстового payload для будущего PDF.

## Входной формат запроса
Одна строка на запрос:

```text
[Имя Фамилия Цель дд.мм чч:мм чч:мм тип_аудитории]
```

Поддерживаемые типы аудиторий:
- `any`, `any2`, `any6`
- `big`, `big2`, `big6`
- конкретный номер аудитории (например `305`)

## Конфиг
Скопируйте `config.example.json` в `config.json` и настройте:
- `buildings` — соответствие номер корпуса -> oid
- `schedule_window_days_before` — сколько дней вычесть от текущей даты для начала диапазона
- `schedule_window_months_after` — сколько месяцев добавить к текущей дате для конца диапазона
- `schedule_range_from_param` / `schedule_range_to_param` — имена query-параметров диапазона дат для API
- `schedule_range_date_format` — формат даты для query-параметров (например `%Y-%m-%d`)
- `allowed_rooms` — аудитории, в которых разрешён поиск
- `big_rooms` — аудитории большого типа
- `contact_fields` — поля для режима генерации отчёта (телефон, ФИО и т.д.)

## Запуск
```bash
python -m app.main --config config.json --input requests.txt --mode allocate
```

Режим генерации отчёта:

```bash
python -m app.main --config config.json --input requests.txt --mode pdf --output output/report.txt
```

## Обновление расписания
В `app.service.should_refresh` реализована проверка временных точек обновления (04:00 и 16:00 по Москве). Её можно использовать во внешнем планировщике (cron/systemd timer).


## Новый режим: генерация конечного PDF по шаблону

Поддерживается режим `render-pdf`, который полностью управляется шаблонным JSON-конфигом и входными данными JSON.

Возможности:
- выравнивание текста: `left`, `center`, `right`;
- отступы: `margin_left`, `margin_right`, `bottom`/`top`;
- печать массивов (`array_text`) по строкам;
- подстановка переменных `{{path.to.value}}`;
- генерация нескольких страниц через `repeat_for`.

Пример запуска:

```bash
python -m app.main --mode render-pdf --template my_template.json --data my_data.json --output output/report.pdf
```

Подробная инструкция по созданию кастомных шаблонов: `PDF_TEMPLATE_GUIDE.md`.
