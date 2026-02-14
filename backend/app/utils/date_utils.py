from datetime import date, timedelta

PLAN_START_DATE = date(2026, 2, 2)  # Monday of the first week of Feb 2026
PLAN_TOTAL_WEEKS = 252


def get_current_plan_week() -> int:
    today = date.today()
    if today < PLAN_START_DATE:
        return 0
    days_elapsed = (today - PLAN_START_DATE).days
    week = days_elapsed // 7 + 1
    return min(week, PLAN_TOTAL_WEEKS)


def get_week_dates(week_number: int) -> tuple[date, date]:
    start = PLAN_START_DATE + timedelta(weeks=week_number - 1)
    end = start + timedelta(days=6)
    return start, end


def get_phase_for_week(week: int) -> int:
    if week <= 26:
        return 1
    elif week <= 104:
        return 2
    elif week <= 182:
        return 3
    else:
        return 4


def week_to_month(week: int) -> int:
    """Convert week number (1-252) to month number (1-58)."""
    return min((week - 1) // 4 + 1, 58)
