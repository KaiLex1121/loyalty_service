def format_custom_frequency_to_russian(data: dict) -> str:

    units = [
        ("years", ("год", "года", "лет")),
        ("months", ("месяц", "месяца", "месяцев")),
        ("weeks", ("неделя", "недели", "недель")),
        ("days", ("день", "дня", "дней")),
        ("hours", ("час", "часа", "часов")),
        ("minutes", ("минута", "минуты", "минут")),
    ]

    parts = []
    for key, forms in units:
        n = data.get(key, 0) or 0
        if not isinstance(n, int) or n <= 0:
            continue
        if n % 10 == 1 and n % 100 != 11:
            form = forms[0]
        elif 2 <= n % 10 <= 4 and not (12 <= n % 100 <= 14):
            form = forms[1]
        else:
            form = forms[2]
        parts.append(f"{n} {form}")

    return " ".join(parts)


def format_reminder_enum_value_to_russian(value: str) -> str:
    mapping = {
        "daily": "ежедневно",
        "weekly": "еженедельно",
        "monthly": "ежемесячно",
        "yearly": "ежегодно",
    }
    return mapping.get(value)
