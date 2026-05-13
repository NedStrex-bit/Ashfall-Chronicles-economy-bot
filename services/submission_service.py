from typing import Any

from database import get_connection
from ranks import BRANCHES


def _row_to_submission(row: tuple[Any, ...] | None) -> dict[str, Any] | None:
    if row is None:
        return None

    return {
        "id": row[0],
        "user_id": row[1],
        "branch": row[2],
        "action_type": row[3],
        "proof_url": row[4],
        "description": row[5],
        "metrics": row[6],
        "status": row[7],
        "reviewer_id": row[8],
        "created_at": row[9],
        "reviewed_at": row[10],
    }


def create_submission(
    user_id: int,
    branch: str,
    action_type: str,
    proof_url: str,
    description: str,
    metrics: str = "",
) -> int:
    if branch not in BRANCHES:
        raise ValueError(f"Unknown branch: {branch}")

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            INSERT INTO submissions (
                user_id,
                branch,
                action_type,
                proof_url,
                description,
                metrics
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                branch,
                action_type,
                proof_url,
                description or None,
                metrics or None,
            ),
        )
        connection.commit()
        return cursor.lastrowid


def get_submission(id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                id,
                user_id,
                branch,
                action_type,
                proof_url,
                description,
                metrics,
                status,
                reviewer_id,
                created_at,
                reviewed_at
            FROM submissions
            WHERE id = ?
            """,
            (id,),
        )
        row = cursor.fetchone()

    return _row_to_submission(row)


def mark_submission_approved(id: int, reviewer_id: int) -> dict[str, Any] | None:
    return _mark_submission_reviewed(id, reviewer_id, "approved")


def mark_submission_rejected(id: int, reviewer_id: int) -> dict[str, Any] | None:
    return _mark_submission_reviewed(id, reviewer_id, "rejected")


def _mark_submission_reviewed(
    id: int,
    reviewer_id: int,
    status: str,
) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            UPDATE submissions
            SET status = ?,
                reviewer_id = ?,
                reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (status, reviewer_id, id),
        )
        connection.commit()

    return get_submission(id)
