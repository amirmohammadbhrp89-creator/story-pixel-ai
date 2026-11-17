from app.database.connection import get_connection


def create_episode(project_id, episode_number, title, description=""):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO episodes
            (project_id, episode_number, title, description)
            VALUES (?, ?, ?, ?)
            """,
            (project_id, episode_number, title, description)
        )
        conn.commit()
        return cursor.lastrowid


def get_episodes(project_id):
    with get_connection() as conn:
        return conn.execute(
            """
            SELECT * FROM episodes
            WHERE project_id = ?
            ORDER BY episode_number
            """,
            (project_id,)
        ).fetchall()


def get_episode(episode_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM episodes WHERE id = ?",
            (episode_id,)
        ).fetchone()