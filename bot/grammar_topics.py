# Каталог тем грамматики по уровням.
# Ключ — код темы (для callback), значение — название для пользователя.
# Легко расширять: добавляй темы в нужный уровень.

GRAMMAR_TOPICS = {
    "beginner": {
        "to_be": "Глагол to be (am/is/are)",
        "present_simple": "Present Simple",
        "articles": "Артикли (a/an/the)",
        "plural": "Множественное число",
        "pronouns": "Местоимения",
        "present_continuous": "Present Continuous",
        "have_got": "Have got (иметь)",
        "numbers": "Числа, даты, время",
    },
    "intermediate": {
        "past_simple": "Past Simple",
        "future": "Future (will, going to)",
        "present_perfect": "Present Perfect",
        "modals": "Модальные глаголы",
        "comparison": "Степени сравнения",
        "conditionals_01": "Условные (0 и 1 тип)",
        "prepositions": "Предлоги",
    },
    "advanced": {
        "perfect_tenses": "Все Perfect времена",
        "passive": "Passive Voice (пассив)",
        "conditionals_23": "Условные (2, 3, смешанный)",
        "reported_speech": "Reported Speech",
        "gerund_infinitive": "Герундий и инфинитив",
        "articles_advanced": "Артикли (тонкости)",
        "inversion": "Инверсия",
    },
}


# Для уровня "unknown" показываем темы начинающего
def get_topics_for_level(level):
    """Вернуть темы грамматики для уровня пользователя."""
    if level in GRAMMAR_TOPICS:
        return GRAMMAR_TOPICS[level]
    return GRAMMAR_TOPICS["beginner"]  # по умолчанию — начинающий


def get_topic_name(level, topic_code):
    """Найти название темы по коду (ищем во всех уровнях)."""
    for lvl_topics in GRAMMAR_TOPICS.values():
        if topic_code in lvl_topics:
            return lvl_topics[topic_code]
    return topic_code
