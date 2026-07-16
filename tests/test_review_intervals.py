from bot.domain.review import (
    LearningItemStatus,
    ReviewResult,
    ReviewState,
    apply_review,
    initial_interval_days,
)


def test_initial_interval():
    assert initial_interval_days() == 1


def test_incorrect_resets_to_weak():
    state = ReviewState(
        status=LearningItemStatus.ACTIVE,
        interval_days=8,
        correct_streak=2,
        error_count=0,
    )
    next_state = apply_review(state, ReviewResult.INCORRECT)
    assert next_state.status == LearningItemStatus.WEAK
    assert next_state.interval_days == 1
    assert next_state.correct_streak == 0
    assert next_state.error_count == 1


def test_correct_doubles_interval():
    state = ReviewState(
        status=LearningItemStatus.LEARNING,
        interval_days=2,
        correct_streak=1,
        error_count=0,
    )
    next_state = apply_review(state, ReviewResult.CORRECT)
    assert next_state.correct_streak == 2
    assert next_state.interval_days >= 4


def test_mastered_after_streak():
    state = ReviewState(
        status=LearningItemStatus.ACTIVE,
        interval_days=4,
        correct_streak=2,
        error_count=0,
    )
    next_state = apply_review(state, ReviewResult.CORRECT)
    assert next_state.status == LearningItemStatus.MASTERED
    assert next_state.interval_days == 60
