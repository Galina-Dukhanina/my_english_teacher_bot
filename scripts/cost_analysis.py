"""Разовый расчёт себестоимости AI для планирования лимитов."""
import sqlite3
from pathlib import Path

DB = Path(__file__).resolve().parent.parent / "bot_database.db"

# OpenRouter: deepseek/deepseek-chat (DeepSeek V3)
PRICE_IN = 0.2002
PRICE_OUT = 0.8001


def cost_usd(tokens_in: int, tokens_out: int) -> float:
    return tokens_in / 1_000_000 * PRICE_IN + tokens_out / 1_000_000 * PRICE_OUT


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row

    row = conn.execute(
        """
        SELECT COUNT(*) AS n,
               AVG(tokens_in) AS ai,
               AVG(tokens_out) AS ao,
               SUM(cost_estimate) AS bot_est
        FROM ai_usage
        """
    ).fetchone()

    print("=== Факт из ai_usage (диалог и прочее) ===")
    if not row["n"]:
        print("Нет данных")
        avg_in, avg_out = 987, 192
        n = 0
    else:
        n = row["n"]
        avg_in, avg_out = int(row["ai"]), int(row["ao"])
        real = cost_usd(avg_in, avg_out)
        print(f"Запросов: {n}")
        print(f"Среднее: {avg_in} in / {avg_out} out")
        print(f"Реальная цена (OpenRouter V3): ${real:.6f}")
        print(f"Оценка бота в БД (завышена):   ${row['bot_est']/n:.6f}")

    # Типовые сценарии (из кода max_tokens + типичные объёмы)
    scenarios = {
        "dialog_msg_avg": (avg_in, avg_out),
        "dialog_msg_light": (600, 120),
        "dialog_msg_heavy": (2500, 400),
        "pronounce_meaning": (900, 150),
        "words_session": (450, 1400),
        "grammar_explain": (550, 900),
        "grammar_exercises": (500, 1200),
    }

    print("\n=== Себестоимость по типам запроса (USD) ===")
    costs = {}
    for name, (ti, to) in scenarios.items():
        c = cost_usd(ti, to)
        costs[name] = c
        print(f"  {name:22} {ti:5} in / {to:4} out -> ${c:.6f} (~{c*80:.3f} rub)")

    msg_cost = costs["dialog_msg_avg"]
    words_cost = costs["words_session"]
    grammar_block = costs["grammar_explain"] + costs["grammar_exercises"]

    print("\n=== Бесплатный пользователь / день (макс. лимиты) ===")
    free_day = 15 * msg_cost + 1 * words_cost + 1 * grammar_block
    print(f"  15 msg + 1 words + 1 grammar block: ${free_day:.4f} (~{free_day*80:.2f} rub)")

    print("\n=== Бесплатный пользователь / месяц (если каждый день на максимум) ===")
    free_month_max = free_day * 30
    print(f"  ${free_month_max:.3f} (~{free_month_max*80:.0f} rub)")

    print("\n=== Бесплатный / месяц (реалистично: 40% дней активен, 60% лимита) ===")
    free_month_real = free_day * 30 * 0.4 * 0.6
    print(f"  ${free_month_real:.3f} (~{free_month_real*80:.0f} rub)")

    # Premium economics
    premium_rub = 299
    usd_rub = 80
    premium_usd = premium_rub / usd_rub
    yookassa_fee = 0.035  # ~3.5%
    net_premium = premium_usd * (1 - yookassa_fee)

    print("\n=== Premium 299 rub/мес ===")
    print(f"  Выручка: ${premium_usd:.2f}")
    print(f"  После комиссии (~3.5%): ${net_premium:.2f} (~{net_premium*usd_rub:.0f} rub)")

    margins = [0.3, 0.4, 0.5]
    free_users_per_premium = [5, 10, 20]

    print("\n=== Сколько $ можно тратить на AI с одного Premium (после комиссии) ===")
    for margin in margins:
        ai_budget = net_premium * (1 - margin)
        print(f"  Маржа {margin*100:.0f}% -> бюджет на AI: ${ai_budget:.2f}/мес")

    print("\n=== Лимит AI-сообщений Premium / день (только диалог, без слов/грамматики) ===")
    print("  Формула: (бюджет_premium - субсидия_free) / 30 / cost_msg")
    print()

    for margin in margins:
        ai_budget = net_premium * (1 - margin)
        for n_free in free_users_per_premium:
            subsidize = free_month_real * n_free
            remaining = ai_budget - subsidize
            if remaining <= 0:
                print(
                    f"  margin={margin*100:.0f}%, {n_free} free/premium: "
                    f"НЕ ХВАТАЕТ (нужно ${subsidize:.2f}, бюджет ${ai_budget:.2f})"
                )
                continue
            msgs_per_day = remaining / 30 / msg_cost
            msgs_per_day_int = int(msgs_per_day)
            print(
                f"  margin={margin*100:.0f}%, {n_free} free/premium: "
                f"~{msgs_per_day_int} msg/день "
                f"(~{msgs_per_day_int*30} msg/мес, субсидия free ${subsidize:.2f})"
            )

    print("\n=== Рекомендуемый пакет лимитов Premium (консервативно) ===")
    # Target: 10 free per premium, 40% margin
    margin = 0.4
    n_free = 10
    ai_budget = net_premium * (1 - margin)
    subsidize = free_month_real * n_free
    remaining = ai_budget - subsidize
    if remaining > 0:
        # Allocate: 70% dialog, 20% words, 10% grammar blocks
        dialog_budget = remaining * 0.70
        words_budget = remaining * 0.20
        grammar_budget = remaining * 0.10
        msgs_day = int(dialog_budget / 30 / msg_cost)
        words_day = max(1, int(words_budget / 30 / words_cost))
        grammar_day = max(1, int(grammar_budget / 30 / grammar_block))
        print(f"  При {n_free} free на 1 premium, маржа {margin*100:.0f}%:")
        print(f"    PREMIUM_LIMIT_MESSAGES = {msgs_day}/день  (~{msgs_day*30}/мес)")
        print(f"    PREMIUM_LIMIT_WORDS_SESSIONS = {words_day}/день")
        print(f"    PREMIUM_LIMIT_GRAMMAR = {grammar_day}/день")
        print(f"    Остаток бюджета на AI: ${remaining:.2f}/мес на premium-user")

    conn.close()


if __name__ == "__main__":
    main()
