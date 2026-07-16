"""Генерация MVP curriculum JSON (неделя 1) для review и seed."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "content" / "curriculum"


def _lesson(day: int, title: str, phrase_en: str, phrase_ru: str, explain_title: str,
            explain_body: str, question: str, options: list, correct: int, apply_ru: str):
    return {
        "day_number": day,
        "title": title,
        "estimated_minutes": 15,
        "steps": [
            {"sort_order": 1, "step_type": "phrase", "payload": {
                "phrase_en": phrase_en, "phrase_ru": phrase_ru,
                "phrase_id": f"phrase_d{day}",
            }},
            {"sort_order": 2, "step_type": "explain", "payload": {
                "title_ru": explain_title, "body_ru": explain_body,
            }},
            {"sort_order": 3, "step_type": "exercise", "payload": {
                "format": "mcq", "question": question,
                "options": options, "correct": correct,
            }},
            {"sort_order": 4, "step_type": "listen", "payload": {
                "asset_slug": f"{phrase_en[:20].replace(' ', '_').lower()}_listen",
                "note": "deferred — этап 13",
            }},
            {"sort_order": 5, "step_type": "apply", "payload": {
                "prompt_ru": apply_ru, "min_words": 5,
            }},
            {"sort_order": 6, "step_type": "voice", "payload": {
                "prompt_ru": "Запиши голосом ответ из предыдущего шага.",
                "note": "deferred — этап 14",
            }},
        ],
    }


def _module(goal: str, cefr: str, title: str, outcome: str, lessons: list, core=0.7, target=0.3):
    return {
        "module": {
            "goal": goal,
            "cefr_level": cefr,
            "stage": 1,
            "week_number": 1,
            "sort_order": 0,
            "title": title,
            "outcome_ru": outcome,
            "core_ratio": core,
            "target_ratio": target,
        },
        "lessons": lessons,
    }


WORK_A1 = _module(
    "work", "A1", "Introduce yourself at work",
    "Представиться, назвать должность, понять простую инструкцию",
    [
        _lesson(1, "Day 1: Name and job",
                "My name is … and I work as a …",
                "Меня зовут …, я работаю …",
                "work as + профессия",
                "I work as a designer. Артикль a/an перед профессией.",
                "I work ___ a teacher.", ["as", "is", "at", "on"], 0,
                "Представься: имя и работа (1–2 предложения)."),
        _lesson(2, "Day 2: Where I work",
                "I work at a small company in Moscow.",
                "Я работаю в небольшой компании в Москве.",
                "work at + место",
                "at — компания/офис: I work at Google.",
                "She works ___ a hospital.", ["in", "at", "on", "to"], 1,
                "Где ты работаешь? Напиши одно предложение."),
        _lesson(3, "Day 3: Simple instruction",
                "Please send the file today.",
                "Пожалуйста, отправь файл сегодня.",
                "Please + глагол",
                "Вежливая просьба: Please open the document.",
                "___ close the door, please.", ["Close", "Closing", "Closed", "Closes"], 0,
                "Напиши вежливую просьбу коллеге (1 предложение)."),
        _lesson(4, "Day 4: Schedule a meeting",
                "Can we meet on Monday at 10?",
                "Мы можем встретиться в понедельник в 10?",
                "Can we…? — предложение встречи",
                "Can we meet tomorrow? — мягкое предложение.",
                "Can we ___ on Friday?", ["meet", "meeting", "met", "meets"], 0,
                "Предложи время короткой встречи (1–2 предложения)."),
        _lesson(5, "Day 5: Ask to repeat",
                "Sorry, could you repeat that, please?",
                "Извините, не могли бы вы повторить?",
                "Could you…? — уточнение",
                "Could you repeat that? — если не расслышали.",
                "Sorry, could you ___ that?", ["repeat", "repeating", "repeats", "repeated"], 0,
                "Напиши фразу, если не понял(а) задачу на созвоне."),
    ],
)

TRAVEL_A1 = _module(
    "travel", "A1", "Travel basics",
    "Аэропорт, транспорт, отель, ресторан, просьба о помощи",
    [
        _lesson(1, "Day 1: At the airport",
                "Where is gate B12?",
                "Где выход B12?",
                "Where is…?",
                "Спросить место: Where is the restroom?",
                "Where ___ the exit?", ["is", "are", "am", "be"], 0,
                "Спроси, где выход или gate (1 предложение)."),
        _lesson(2, "Day 2: Transport",
                "One ticket to the city center, please.",
                "Один билет до центра, пожалуйста.",
                "One ticket to…",
                "to + место назначения.",
                "Two tickets ___ the airport.", ["to", "at", "in", "on"], 0,
                "Купи билет — напиши фразу кассиру."),
        _lesson(3, "Day 3: Hotel check-in",
                "I have a reservation under Ivanov.",
                "У меня бронь на имя Ivanov.",
                "reservation under + фамилия",
                "I have a reservation. My name is…",
                "I ___ a reservation.", ["have", "has", "having", "had"], 0,
                "Напиши фразу при регистрации в отеле."),
        _lesson(4, "Day 4: Restaurant",
                "Can I have the menu, please?",
                "Можно меню, пожалуйста?",
                "Can I have…?",
                "Заказать вежливо: Can I have a coffee?",
                "Can I ___ the bill?", ["have", "has", "having", "had"], 0,
                "Закажи еду или напиток (1–2 предложения)."),
        _lesson(5, "Day 5: Ask for help",
                "Excuse me, I'm lost. Can you help me?",
                "Извините, я заблудился. Можете помочь?",
                "Excuse me + просьба",
                "I'm lost. — если потерялся.",
                "Excuse me, can you ___ me?", ["help", "helping", "helps", "helped"], 0,
                "Напиши просьбу о помощи в незнакомом месте."),
    ],
)

EXAMS_A1 = _module(
    "exams", "A1", "Exam foundations",
    "Базовые задания: reading, grammar, vocabulary (TOEFL/DET стиль)",
    [
        _lesson(1, "Day 1: Reading main idea",
                "The main idea is what the text is mostly about.",
                "Главная мысль — о чём в основном текст.",
                "Main idea",
                "Ищи повторяющуюся тему абзаца.",
                "What is the text mostly about? → Main ___.", ["idea", "word", "sound", "letter"], 0,
                "Прочитай: «Tom studies English every day.» — напиши main idea одним предложением."),
        _lesson(2, "Day 2: Present simple",
                "She works five days a week.",
                "Она работает пять дней в неделю.",
                "Present Simple",
                "he/she/it + глагол-s: works, studies.",
                "He ___ English.", ["study", "studies", "studying", "studied"], 1,
                "Напиши 2 предложения о своём расписании (Present Simple)."),
        _lesson(3, "Day 3: Vocabulary in context",
                "The word «deadline» means the last day to finish.",
                "Deadline — последний день, когда нужно сдать.",
                "Context clues",
                "Смотри на слова вокруг незнакомого слова.",
                "A ___ is the last day to finish work.", ["deadline", "holiday", "breakfast", "window"], 0,
                "Напиши предложение со словом deadline."),
        _lesson(4, "Day 4: Listening script",
                "🎧 A: Your test starts at 9. B: Should I bring my ID?",
                "Текст диалога перед экзаменом.",
                "Listening: details",
                "Выписывай числа, время, имена.",
                "When does the test start?", ["At 8", "At 9", "At 10", "At 12"], 1,
                "Напиши 1 вопрос, который ты задашь в день экзамена."),
        _lesson(5, "Day 5: Short written response",
                "In my opinion, practice every day helps.",
                "По моему мнению, практика каждый день помогает.",
                "In my opinion…",
                "Короткое written response: 2–3 предложения.",
                "Which is a good opinion phrase?",
                ["In my opinion,", "In my table,", "In my kitchen,", "In my Monday,"], 0,
                "Напиши 2–3 предложения: зачем тебе английский (exam goal)."),
    ],
    core=0.6,
    target=0.4,
)

SPEAKING_A1 = _module(
    "speaking", "A1", "Start speaking",
    "О себе, простые вопросы, семья, интересы",
    [
        _lesson(1, "Day 1: About me",
                "I'm from Russia and I live in …",
                "Я из России, живу в …",
                "I'm from / I live in",
                "from — страна/город рождения; live in — где живёшь.",
                "I ___ from Italy.", ["am", "is", "are", "be"], 0,
                "Расскажи, откуда ты и где живёшь (2 предложения)."),
        _lesson(2, "Day 2: Simple questions",
                "What do you do in your free time?",
                "Чем занимаешься в свободное время?",
                "What do you…?",
                "What do you do? — о работе или хобби по контексту.",
                "What ___ you do?", ["do", "does", "did", "doing"], 0,
                "Задай собеседнику 2 простых вопроса с What do you…?"),
        _lesson(3, "Day 3: Family",
                "I have one brother and two sisters.",
                "У меня один брат и две сестры.",
                "I have…",
                "have — члены семьи, без артикля во множественном.",
                "She ___ two cats.", ["have", "has", "having", "had"], 1,
                "Опиши семью в 2–3 предложениях."),
        _lesson(4, "Day 4: Interests",
                "I enjoy reading and hiking.",
                "Мне нравится читать и ходить в походы.",
                "I enjoy + -ing",
                "enjoy/like/love + gerund: I enjoy cooking.",
                "I enjoy ___.", ["swim", "swimming", "swims", "swam"], 1,
                "Напиши о 2–3 хобби."),
        _lesson(5, "Day 5: Plans",
                "This weekend I'm going to visit my friends.",
                "В эти выходные я собираюсь навестить друзей.",
                "be going to",
                "Планы: I'm going to + глагол.",
                "We ___ going to watch a movie.", ["am", "is", "are", "be"], 2,
                "Напиши планы на выходные (2 предложения)."),
    ],
)

SELF_A1 = _module(
    "self", "A1", "Everyday English",
    "Быт, интересы, предпочтения, повседневная жизнь",
    [
        _lesson(1, "Day 1: Daily routine",
                "I usually wake up at seven.",
                "Обычно я просыпаюсь в семь.",
                "Usually + Present Simple",
                "usually/often/sometimes — перед глаголом.",
                "I usually ___ coffee in the morning.", ["drink", "drinks", "drinking", "drank"], 0,
                "Опиши утро в 2–3 предложениях."),
        _lesson(2, "Day 2: Likes and dislikes",
                "I like podcasts, but I don't like loud music.",
                "Мне нравятся подкасты, но не нравится громкая музыка.",
                "like / don't like",
                "don't + глагол для dislike.",
                "She ___ like horror movies.", ["don't", "doesn't", "isn't", "aren't"], 1,
                "Что нравится и не нравится — 2–3 предложения."),
        _lesson(3, "Day 3: Movies and series",
                "My favorite series is about detectives.",
                "Мой любимый сериал про детективов.",
                "favorite + singular",
                "My favorite book is…",
                "My favorite ___ is very funny.", ["movie", "movies", "watch", "watching"], 0,
                "Напиши о любимом фильме или сериале."),
        _lesson(4, "Day 4: Feelings",
                "I feel tired after a long day.",
                "Я чувствую усталость после долгого дня.",
                "I feel + adjective",
                "feel tired/happy/excited.",
                "They feel ___.", ["happy", "happily", "happiness", "happierly"], 0,
                "Как ты себя чувствуешь сегодня? 1–2 предложения."),
        _lesson(5, "Day 5: Small talk",
                "Nice weather today, isn't it?",
                "Хорошая погода сегодня, правда?",
                "Small talk starters",
                "Комментарий о погоде — лёгкий старт разговора.",
                "___ weather today!", ["Nice", "Nicely", "Niceful", "Nicing"], 0,
                "Напиши 2 фразы для small talk."),
    ],
)

# A2 / B1 — по 1 уроку (день 1) на цель для routing по уровню
def _single_lesson_module(goal: str, cefr: str, title: str, outcome: str, lesson):
    ratios = {"A2": (0.5, 0.5), "B1": (0.3, 0.7)}
    core, target = ratios.get(cefr, (0.5, 0.5))
    return _module(goal, cefr, title, outcome, [lesson], core=core, target=target)


A2_DAY1 = {
    "work": _single_lesson_module(
        "work", "A2", "Work updates", "Рассказать о статусе задачи",
        _lesson(1, "Day 1: Task status",
                "I'm working on the report and it will be ready tomorrow.",
                "Я работаю над отчётом, будет готов завтра.",
                "Present Continuous для процесса",
                "I'm working on… — задача в процессе.",
                "I ___ working on the slides.", ["am", "is", "are", "be"], 0,
                "Напиши статус одной задачи (2 предложения)."),
    ),
    "travel": _single_lesson_module(
        "travel", "A2", "Travel problems", "Объяснить проблему в поездке",
        _lesson(1, "Day 1: Booking issue",
                "I'd like to change my reservation, please.",
                "Я хотел(а) бы изменить бронь.",
                "I'd like to…",
                "I'd like to + глагол — вежливая просьба.",
                "I'd like to ___ my flight.", ["change", "changing", "changed", "changes"], 0,
                "Напиши просьбу изменить бронь."),
    ),
    "exams": _single_lesson_module(
        "exams", "A2", "Exam strategies", "Стратегии reading/listening",
        _lesson(1, "Day 1: Skimming",
                "Skim the text first, then read the questions.",
                "Сначала пробегись по тексту, потом читай вопросы.",
                "Skimming",
                "Skim — быстро найти общую идею.",
                "Skimming helps find the ___ idea quickly.", ["main", "tiny", "secret", "no"], 0,
                "Напиши, как ты готовишься к reading section."),
    ),
    "speaking": _single_lesson_module(
        "speaking", "A2", "Tell a story", "Рассказать короткую историю",
        _lesson(1, "Day 1: Past event",
                "Last year I visited Prague and loved it.",
                "В прошлом году я был в Праге — понравилось.",
                "Past Simple narrative",
                "Last year I visited… — начало истории.",
                "Last summer we ___ to the sea.", ["went", "go", "going", "goes"], 0,
                "Расскажи о поездке в 3–4 предложениях (Past Simple)."),
    ),
    "self": _single_lesson_module(
        "self", "A2", "Opinions", "Выразить мнение",
        _lesson(1, "Day 1: I think…",
                "I think learning English opens new opportunities.",
                "Думаю, английский открывает новые возможности.",
                "I think (that)…",
                "I think + clause — своё мнение.",
                "I think it ___ useful.", ["is", "are", "am", "be"], 0,
                "Напиши своё мнение на любую тему (2 предложения)."),
    ),
}

B1_DAY1 = {
    "work": _single_lesson_module(
        "work", "B1", "Work communication", "Объяснить проблему на работе",
        _lesson(1, "Day 1: Explain an issue",
                "We've run into a delay because the supplier hasn't confirmed the date.",
                "Возникла задержка: поставщик не подтвердил дату.",
                "Present Perfect + reason",
                "We've run into… — описать проблему.",
                "We've ___ into a problem with the timeline.",
                ["run", "ran", "running", "runs"], 0,
                "Опиши рабочую проблему и причину (2–3 предложения)."),
    ),
    "travel": _single_lesson_module(
        "travel", "B1", "Travel stories", "Подробно описать ситуацию",
        _lesson(1, "Day 1: Unexpected situation",
                "The flight was cancelled, so we had to rebook for the next morning.",
                "Рейс отменили, пришлось перебронировать на утро.",
                "so + result clause",
                "so — следствие: …, so we had to…",
                "The train was late, ___ we missed the connection.",
                ["so", "but", "because", "although"], 0,
                "Опиши нестандартную ситуацию в поездке."),
    ),
    "exams": _single_lesson_module(
        "exams", "B1", "Integrated skills", "Связать reading и writing",
        _lesson(1, "Day 1: Summarize",
                "The author argues that practice beats talent when goals are clear.",
                "Автор считает: практика важнее таланта при ясных целях.",
                "Summarizing",
                "The author argues/suggests that…",
                "The author ___ that regular practice helps.",
                ["argues", "argue", "arguing", "argued"], 0,
                "Напиши краткое summary (2–3 предложения) по любой знакомой теме."),
    ),
    "speaking": _single_lesson_module(
        "speaking", "B1", "Debate basics", "Аргументировать позицию",
        _lesson(1, "Day 1: On the other hand",
                "On the other hand, remote work saves commuting time.",
                "С другой стороны, удалёнка экономит время на дорогу.",
                "On the other hand",
                "Контраст: On the other hand, …",
                "Which phrase shows contrast?",
                ["On the other hand,", "On the same hand,", "On the happy,", "On the quickly,"], 0,
                "Напиши 2 аргумента за и 1 против любой темы."),
    ),
    "self": _single_lesson_module(
        "self", "B1", "Culture and news", "Обсудить новость или тренд",
        _lesson(1, "Day 1: Discuss a trend",
                "More people are learning languages through short daily sessions.",
                "Всё больше людей учат языки короткими ежедневными сессиями.",
                "Present Continuous trend",
                "More people are + -ing — тренд.",
                "More people are ___ online courses.",
                ["taking", "take", "took", "takes"], 0,
                "Напиши о тренде, который тебе интересен."),
    ),
}


def write_all():
    mapping = {
        ("work", "A1"): WORK_A1,
        ("travel", "A1"): TRAVEL_A1,
        ("exams", "A1"): EXAMS_A1,
        ("speaking", "A1"): SPEAKING_A1,
        ("self", "A1"): SELF_A1,
    }
    for goal, data in A2_DAY1.items():
        mapping[(goal, "A2")] = data
    for goal, data in B1_DAY1.items():
        mapping[(goal, "B1")] = data

    for (goal, cefr), payload in mapping.items():
        dest = OUT / goal / cefr / "module_1.json"
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Wrote {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    write_all()
