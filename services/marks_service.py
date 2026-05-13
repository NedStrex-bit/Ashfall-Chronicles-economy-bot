from datetime import datetime, time, timedelta
from typing import Any

from database import get_connection
from ranks import BRANCHES


DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


def ensure_user_exists(user_id: int) -> None:
    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            INSERT OR IGNORE INTO users (user_id)
            VALUES (?)
            """,
            (user_id,),
        )

        for branch in BRANCHES:
            cursor.execute(
                """
                INSERT OR IGNORE INTO branch_progress (user_id, branch)
                VALUES (?, ?)
                """,
                (user_id, branch),
            )

        connection.commit()


def get_user_progress(user_id: int) -> dict[str, Any]:
    ensure_user_exists(user_id)

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT total_marks
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        )
        user_row = cursor.fetchone()

        cursor.execute(
            """
            SELECT branch, marks
            FROM branch_progress
            WHERE user_id = ?
            """,
            (user_id,),
        )
        branch_rows = cursor.fetchall()

    branches = {branch: 0 for branch in BRANCHES}
    branches.update({branch: marks for branch, marks in branch_rows})

    return {
        "user_id": user_id,
        "total_marks": user_row[0],
        "branches": branches,
    }


def add_marks(
    user_id: int,
    admin_id: int,
    branch: str,
    action_type: str,
    base_marks: int,
    bonus_marks: int = 0,
    proof_url: str | None = None,
    comment: str | None = None,
) -> dict[str, Any]:
    if branch not in BRANCHES:
        raise ValueError(f"Unknown branch: {branch}")

    if base_marks < 0:
        raise ValueError("base_marks must not be negative.")

    if bonus_marks < 0:
        raise ValueError("bonus_marks must not be negative.")

    total_to_add = base_marks + bonus_marks
    ensure_user_exists(user_id)

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            UPDATE users
            SET total_marks = total_marks + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (total_to_add, user_id),
        )

        cursor.execute(
            """
            UPDATE branch_progress
            SET marks = marks + ?
            WHERE user_id = ? AND branch = ?
            """,
            (total_to_add, user_id, branch),
        )

        cursor.execute(
            """
            INSERT INTO transactions (
                user_id,
                admin_id,
                branch,
                action_type,
                base_marks,
                bonus_marks,
                total_marks,
                proof_url,
                comment
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                admin_id,
                branch,
                action_type,
                base_marks,
                bonus_marks,
                total_to_add,
                proof_url,
                comment,
            ),
        )

        connection.commit()

    return get_user_progress(user_id)


def adjust_marks(
    user_id: int,
    admin_id: int,
    branch: str,
    amount: int,
    reason: str,
) -> dict[str, Any]:
    if branch not in BRANCHES:
        raise ValueError(f"Unknown branch: {branch}")

    ensure_user_exists(user_id)

    with get_connection() as connection:
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT total_marks
            FROM users
            WHERE user_id = ?
            """,
            (user_id,),
        )
        total_marks = cursor.fetchone()[0]

        cursor.execute(
            """
            SELECT marks
            FROM branch_progress
            WHERE user_id = ? AND branch = ?
            """,
            (user_id, branch),
        )
        branch_marks = cursor.fetchone()[0]

        if amount < 0:
            actual_change = -min(abs(amount), total_marks, branch_marks)
        else:
            actual_change = amount

        cursor.execute(
            """
            UPDATE users
            SET total_marks = total_marks + ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (actual_change, user_id),
        )

        cursor.execute(
            """
            UPDATE branch_progress
            SET marks = marks + ?
            WHERE user_id = ? AND branch = ?
            """,
            (actual_change, user_id, branch),
        )

        cursor.execute(
            """
            INSERT INTO transactions (
                user_id,
                admin_id,
                branch,
                action_type,
                base_marks,
                bonus_marks,
                total_marks,
                comment
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                admin_id,
                branch,
                "manual_adjustment",
                actual_change,
                0,
                actual_change,
                reason,
            ),
        )

        connection.commit()

    return get_user_progress(user_id)


def _format_datetime(value: datetime) -> str:
    return value.strftime(DATETIME_FORMAT)


def get_transactions_count(
    user_id: int,
    branch: str,
    action_type: str | None = None,
    since_datetime: datetime | None = None,
) -> int:
    query = """
        SELECT COUNT(*)
        FROM transactions
        WHERE user_id = ? AND branch = ?
    """
    params: list[Any] = [user_id, branch]

    if action_type is not None:
        query += " AND action_type = ?"
        params.append(action_type)

    if since_datetime is not None:
        query += " AND created_at >= ?"
        params.append(_format_datetime(since_datetime))

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()[0]


def _get_approve_transactions_count(
    user_id: int,
    branch: str,
    since_datetime: datetime,
) -> int:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM transactions
            WHERE user_id = ?
                AND branch = ?
                AND action_type != ?
                AND created_at >= ?
            """,
            (user_id, branch, "manual_adjustment", _format_datetime(since_datetime)),
        )
        return cursor.fetchone()[0]


def _get_transactions_marks_sum(
    user_id: int,
    branch: str,
    action_type: str,
    since_datetime: datetime,
) -> int:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT COALESCE(SUM(total_marks), 0)
            FROM transactions
            WHERE user_id = ?
                AND branch = ?
                AND action_type = ?
                AND created_at >= ?
            """,
            (user_id, branch, action_type, _format_datetime(since_datetime)),
        )
        return cursor.fetchone()[0]


def _get_week_start() -> datetime:
    today = datetime.now().date()
    week_start_date = today - timedelta(days=today.weekday())
    return datetime.combine(week_start_date, time.min)


def validate_limits(
    user_id: int,
    branch: str,
    action_type: str,
    base_marks: int,
) -> tuple[bool, str]:
    if branch not in BRANCHES:
        return False, f"Unknown branch: {branch}"

    today_start = datetime.combine(datetime.now().date(), time.min)

    if branch == "voice":
        daily_count = _get_approve_transactions_count(user_id, branch, today_start)
        if daily_count >= 2:
            return False, "The Voice of Ashfall limit reached: max 2 approvals per day."

    if branch == "atelier":
        daily_count = _get_approve_transactions_count(user_id, branch, today_start)
        if daily_count >= 1:
            return False, "The Atelier of Ash limit reached: max 1 approval per day."

    if branch == "wardens" and action_type == "poll_participation":
        week_start = _get_week_start()
        awarded_marks_this_week = _get_transactions_marks_sum(
            user_id,
            branch,
            action_type,
            week_start,
        )

        if awarded_marks_this_week >= 2:
            return False, "Chronicle Wardens poll_participation limit reached: max 2 Ash Marks per week."

    return True, ""


def get_user_history(user_id: int, limit: int = 10) -> list[dict[str, Any]]:
    with get_connection() as connection:
        connection.row_factory = None
        cursor = connection.cursor()

        cursor.execute(
            """
            SELECT
                id,
                user_id,
                admin_id,
                branch,
                action_type,
                base_marks,
                bonus_marks,
                total_marks,
                proof_url,
                comment,
                created_at
            FROM transactions
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = cursor.fetchall()

    return [
        {
            "id": row[0],
            "user_id": row[1],
            "admin_id": row[2],
            "branch": row[3],
            "action_type": row[4],
            "base_marks": row[5],
            "bonus_marks": row[6],
            "total_marks": row[7],
            "proof_url": row[8],
            "comment": row[9],
            "created_at": row[10],
        }
        for row in rows
    ]


def get_leaderboard(branch: str = "total", limit: int = 10) -> list[dict[str, int]]:
    limit = max(1, min(limit, 20))

    with get_connection() as connection:
        cursor = connection.cursor()

        if branch == "total":
            cursor.execute(
                """
                SELECT user_id, total_marks
                FROM users
                WHERE total_marks > 0
                ORDER BY total_marks DESC, user_id ASC
                LIMIT ?
                """,
                (limit,),
            )
        elif branch in BRANCHES:
            cursor.execute(
                """
                SELECT user_id, marks
                FROM branch_progress
                WHERE branch = ? AND marks > 0
                ORDER BY marks DESC, user_id ASC
                LIMIT ?
                """,
                (branch, limit),
            )
        else:
            raise ValueError(f"Unknown leaderboard branch: {branch}")

        rows = cursor.fetchall()

    return [{"user_id": row[0], "marks": row[1]} for row in rows]
